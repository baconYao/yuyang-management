# Kubernetes / k3s deployment (Yuyang Management)

This directory contains **Kustomize** bases and **overlays** for running PostgreSQL, Backend, and Frontend on Kubernetes / k3s.

## 1. Verify the cluster (before deploying apps)

Run these with your kubeconfig (replace path as needed):

```bash
export KUBECONFIG=~/.kube/config   # or path to your cluster kubeconfig

kubectl get nodes
# Expect: at least one node in Ready state

kubectl get pods -A
# Expect: system pods (e.g. local-path, coredns) running

kubectl get storageclass
# Expect: local-path (or adjust postgres PVC storageClassName in base)
```

Back up your kubeconfig file somewhere safe outside the cluster.

## 2. Prerequisites: secrets (required before apply)

Secrets are **not** committed to git. Create them once per cluster/namespace.

### Namespace

The overlay sets namespace `yuyang`. You can create it explicitly:

```bash
kubectl create namespace yuyang
```

(Applying the overlay also includes a `Namespace` resource; skip duplicate create if you use only `kubectl apply -k`.)

### GHCR pull secret (private images)

Use a GitHub PAT with `read:packages` (or classic token with package read):

```bash
kubectl -n yuyang create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_PAT \
  --docker-email=unused@example.com
```

### PostgreSQL password

Must match what the backend uses (`POSTGRES_PASSWORD`):

```bash
kubectl -n yuyang create secret generic postgres-secret \
  --from-literal=password='CHANGE_ME_STRONG_PASSWORD'
```

Default manifests use user `postgres`, database `yuyang_db` (same as [docker-compose.prod.yml](../docker-compose.prod.yml)).

## 3. Apply order

1. Complete **section 1** (cluster + StorageClass).
2. Create **section 2** secrets (`ghcr-pull`, `postgres-secret`).
3. Set image tags in [overlays/production/kustomization.yaml](overlays/production/kustomization.yaml) (`images[].newTag` to your GHCR tag, e.g. `sha-...` or `main`).
4. Apply the default production overlay (Postgres uses **dynamic PVC** + `local-path` StorageClass):

```bash
kubectl apply -k deploy/overlays/production
```

### PostgreSQL on bind-mounted storage (hostPath)

Example: **QNAP Container Station** Docker volume `yuyang-management` (host path like `.../volumes/yuyang-management/_data`).

The durable path on the **physical host** is not the same as paths **inside** the Kubernetes node (e.g. k3s running in a container). You cannot put the NAS absolute path into a Pod spec; the node must expose storage at a path the kubelet sees.

1. **Bind-mount** your volume into the **node** at a stable path (example on QNAP Container Station: Docker volume `yuyang-management` → mount inside the k3s container as **`/mnt/yuyang-management`**). The same idea applies on a bare-metal node: mount disk at e.g. `/var/lib/yuyang/postgres`.

2. **Enable the optional Kustomize component** so Postgres uses `hostPath` instead of a `local-path` PVC:

   - Edit [components/postgres-hostpath/postgres-hostpath.patch.yaml](components/postgres-hostpath/postgres-hostpath.patch.yaml) if your node mount path is not `/mnt/yuyang-management/postgres`.
   - In [overlays/production/kustomization.yaml](overlays/production/kustomization.yaml), uncomment:

   ```yaml
   components:
     - ../../components/postgres-hostpath
   ```

3. Apply the same overlay as usual:

```bash
kubectl apply -k deploy/overlays/production
```

**If you already deployed Postgres without the component** (`local-path` PVC), turning the component on is a **storage migration**: back up data, remove the old StatefulSet/PVC (or use a new cluster), then apply on a clean hostPath directory.

**After apply (PVC or hostPath):** wait for workloads and open the UI:

```bash
kubectl -n yuyang get pods,svc,pvc
kubectl -n yuyang logs deploy/api --tail=100
kubectl -n yuyang logs deploy/frontend --tail=50
```

The `frontend` Service is **NodePort** with fixed **`nodePort: 61080`** (fits NodePort ranges such as 61000–62000). Open `http://<node-ip>:61080`. If your cluster uses another range, change [base/frontend/service.yaml](base/frontend/service.yaml). The frontend nginx image proxies `/api` to the backend Service **`api`** (port 8000), matching [frontend/nginx.conf](../frontend/nginx.conf).

## 4. Database migrations

On startup the API runs **Alembic `upgrade head`** (with retries until PostgreSQL is ready). The backend Deployment also has an **initContainer** that waits for `postgres` via `pg_isready` before the API container starts.

Requirements:

- The backend image must include `alembic.ini` and `migrations/` (see [backend/Dockerfile](../backend/Dockerfile)).
- Rebuild and push a new backend image after pulling these changes.

If the API pod is in **CrashLoopBackOff**, check logs:

```bash
kubectl -n yuyang logs deploy/api --tail=100
kubectl -n yuyang logs deploy/api -c wait-for-postgres   # init container
```

### Recover from a broken / partial schema

If a previous deploy used `create_all()` and left tables without Alembic version tracking, or migrations fail with "relation already exists":

**Option A — fresh database (simplest for first deploy):**

```bash
# Stop workloads, remove postgres pod + data on the volume, then re-apply
kubectl -n yuyang delete statefulset postgres
# Clear hostPath dir on the node (e.g. /mnt/yuyang-management/postgres) or delete PVC
kubectl apply -k deploy/overlays/production
```

**Option B — DB already matches current models:**

```bash
kubectl -n yuyang exec -it deploy/api -- alembic stamp head
kubectl -n yuyang rollout restart deploy/api
```

**Option C — manual migration:**

```bash
kubectl -n yuyang exec -it deploy/api -- alembic upgrade head
```

## 5. Troubleshooting

- **ImagePullBackOff**: Check `ghcr-pull` secret and image name/tag (lowercase `ghcr.io/baconyao/...`).
- **Postgres pending**: Without the hostPath component, check PVC + `local-path`. With [components/postgres-hostpath](components/postgres-hostpath) enabled in [overlays/production/kustomization.yaml](overlays/production/kustomization.yaml), there is no PVC; ensure the node has the directory bind-mounted and `hostPath` matches the patch file.
- **Backend CrashLoop**: Check `kubectl -n yuyang logs deploy/api` and DB connectivity (`POSTGRES_SERVER=postgres`).
