# Kubernetes / k3s deployment (Yuyang Management)

This directory contains **Kustomize** bases and a **qnap** overlay for running PostgreSQL, Backend, and Frontend on k3s.

## 1. Verify the cluster (before deploying apps)

Run these with your kubeconfig (replace path as needed):

```bash
export KUBECONFIG=~/.kube/qnap-k3s.yaml   # example

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
3. Set image tags in [overlays/qnap/kustomization.yaml](overlays/qnap/kustomization.yaml) (`images[].newTag` to your GHCR tag, e.g. `sha-...` or `main`).
4. Apply the overlay:

```bash
kubectl apply -k deploy/overlays/qnap
```

5. Wait for workloads:

```bash
kubectl -n yuyang get pods,svc,pvc
kubectl -n yuyang logs deploy/api --tail=100
kubectl -n yuyang logs deploy/frontend --tail=50
```

6. Open the UI: use the **NodePort** printed for service `frontend` (default node port **30080** if not changed), e.g. `http://<node-ip>:30080`.  
   The frontend nginx image proxies `/api` to the backend Service named **`api`** (port 8000), matching [frontend/nginx.conf](../frontend/nginx.conf).

## 4. Migrations

The API runs `create_db_tables()` on startup ([backend/app/main.py](../backend/app/main.py)). For production you may still want Alembic migrations; run a one-off Job or exec into the API pod if needed.

## 5. Troubleshooting

- **ImagePullBackOff**: Check `ghcr-pull` secret and image name/tag (lowercase `ghcr.io/baconyao/...`).
- **Postgres pending**: Check PVC + `local-path`; ensure k3s data paths are persisted on the NAS if using Container Station.
- **Backend CrashLoop**: Check `kubectl -n yuyang logs deploy/api` and DB connectivity (`POSTGRES_SERVER=postgres`).
