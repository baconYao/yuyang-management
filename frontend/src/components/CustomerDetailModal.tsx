import { useState, useCallback, useEffect } from 'react';
import { customerApi } from '../services/api';
import type { Customer, Contract } from '../types';
import { CustomerType } from '../types';
import type { CustomerStatus } from '../types';
import { getCustomerTypeLabel } from '../utils/customerTypeLabels';
import { getContractStatusDisplay } from '../utils/contractStatusDisplay';

const CUSTOMER_TYPE_OPTIONS = [
  { value: '', label: '請選擇' },
  ...Object.values(CustomerType).map((t) => ({ value: t, label: getCustomerTypeLabel(t) })),
];

const STATUS_OPTIONS: { value: CustomerStatus; label: string }[] = [
  { value: 'ACTIVE', label: '合作中' },
  { value: 'TERMINATED', label: '無合作' },
];

const REQUIRED_FIELDS: { key: string; label: string }[] = [
  { key: 'customer_name', label: '客戶名稱' },
  { key: 'primary_contact', label: '聯絡人' },
  { key: 'contact_phone', label: '聯絡電話' },
  { key: 'address', label: '地址' },
  { key: 'customer_type', label: '客戶類型' },
];

type FormState = {
  customer_name: string;
  invoice_title: string;
  invoice_number: string;
  primary_contact: string;
  contact_phone: string;
  messaging_app_line: string;
  address: string;
  customer_type: CustomerType | '';
  status: CustomerStatus;
};

function customerToForm(c: Customer): FormState {
  return {
    customer_name: c.customer_name ?? '',
    invoice_title: c.invoice_title ?? '',
    invoice_number: c.invoice_number ?? '',
    primary_contact: c.primary_contact ?? '',
    contact_phone: c.contact_phone ?? '',
    messaging_app_line: c.messaging_app_line ?? '',
    address: c.address ?? '',
    customer_type: (c.customer_type as CustomerType) ?? '',
    status: (c.status as CustomerStatus) ?? 'ACTIVE',
  };
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' });
  } catch {
    return iso;
  }
}

function getStatusLabel(status: Customer['status']): string {
  if (status === 'TERMINATED') return '無合作';
  return '合作中';
}

function EditIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
      />
    </svg>
  );
}

export interface CustomerDetailModalProps {
  customer: Customer | null;
  onClose: () => void;
  onCustomerUpdated: (customer: Customer) => void;
  contracts: Contract[];
  contractsLoading: boolean;
  onContractRowClick: (e: React.MouseEvent, contract: Contract) => void;
}

export default function CustomerDetailModal({
  customer,
  onClose,
  onCustomerUpdated,
  contracts,
  contractsLoading,
  onContractRowClick,
}: CustomerDetailModalProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState<FormState>(customerToForm(customer ?? ({} as Customer)));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof FormState, string>>>({});

  useEffect(() => {
    if (customer) {
      setForm(customerToForm(customer));
      setIsEditing(false);
      setError(null);
      setFieldErrors({});
    }
  }, [customer]);

  const update = useCallback((field: keyof FormState, value: string | CustomerStatus) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setError(null);
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }, []);

  const handleCancelEdit = useCallback(() => {
    if (customer) setForm(customerToForm(customer));
    setIsEditing(false);
    setError(null);
    setFieldErrors({});
  }, [customer]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!customer) return;
      setError(null);
      const errors: Partial<Record<keyof FormState, string>> = {};
      for (const { key, label } of REQUIRED_FIELDS) {
        const value = form[key as keyof FormState];
        const trimmed = typeof value === 'string' ? value.trim() : value;
        if (trimmed === '' || trimmed == null) {
          errors[key as keyof FormState] = `請填寫${label}`;
        }
      }
      if (Object.keys(errors).length > 0) {
        setFieldErrors(errors);
        setError('請填寫必填欄位後再儲存。');
        return;
      }
      setFieldErrors({});
      setSubmitting(true);
      try {
        const payload = {
          customer_name: form.customer_name || null,
          invoice_title: form.invoice_title || null,
          invoice_number: form.invoice_number || null,
          primary_contact: form.primary_contact || null,
          contact_phone: form.contact_phone || null,
          messaging_app_line: form.messaging_app_line || null,
          address: form.address || null,
          customer_type: (form.customer_type || null) as CustomerType | null,
          status: form.status,
        };
        const updated = await customerApi.update(customer.id, payload);
        setIsEditing(false);
        onCustomerUpdated(updated);
      } catch (err: unknown) {
        const message =
          err && typeof err === 'object' && 'response' in err
            ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
            : null;
        setError(typeof message === 'string' ? message : '更新客戶失敗，請稍後再試。');
      } finally {
        setSubmitting(false);
      }
    },
    [customer, form, onCustomerUpdated]
  );

  if (!customer) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="customer-modal-title"
    >
      <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 id="customer-modal-title" className="text-xl font-bold text-gray-800">
            {isEditing ? '編輯客戶' : '客戶詳情'}
          </h2>
          <div className="flex items-center gap-2">
            {!isEditing && (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
                aria-label="編輯"
                title="編輯"
              >
                <EditIcon className="w-5 h-5" />
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
              aria-label="關閉"
            >
              <span className="text-2xl leading-none">&times;</span>
            </button>
          </div>
        </div>

        {isEditing ? (
          <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
            <div className="px-6 py-4 overflow-y-auto flex-1">
              {error && (
                <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    客戶名稱 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={form.customer_name}
                    onChange={(e) => update('customer_name', e.target.value)}
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      fieldErrors.customer_name ? 'border-red-500 focus:ring-red-500' : 'border-gray-300'
                    }`}
                    placeholder="請輸入客戶名稱"
                  />
                  {fieldErrors.customer_name && (
                    <p className="mt-1 text-sm text-red-600">{fieldErrors.customer_name}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">發票抬頭</label>
                  <input
                    type="text"
                    value={form.invoice_title}
                    onChange={(e) => update('invoice_title', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="請輸入發票抬頭"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">統一編號</label>
                  <input
                    type="text"
                    value={form.invoice_number}
                    onChange={(e) => update('invoice_number', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="請輸入統一編號"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    聯絡人 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={form.primary_contact}
                    onChange={(e) => update('primary_contact', e.target.value)}
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      fieldErrors.primary_contact ? 'border-red-500 focus:ring-red-500' : 'border-gray-300'
                    }`}
                    placeholder="請輸入聯絡人"
                  />
                  {fieldErrors.primary_contact && (
                    <p className="mt-1 text-sm text-red-600">{fieldErrors.primary_contact}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    聯絡電話 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={form.contact_phone}
                    onChange={(e) => update('contact_phone', e.target.value)}
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      fieldErrors.contact_phone ? 'border-red-500 focus:ring-red-500' : 'border-gray-300'
                    }`}
                    placeholder="請輸入聯絡電話"
                  />
                  {fieldErrors.contact_phone && (
                    <p className="mt-1 text-sm text-red-600">{fieldErrors.contact_phone}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">LINE</label>
                  <input
                    type="text"
                    value={form.messaging_app_line}
                    onChange={(e) => update('messaging_app_line', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="請輸入 LINE ID"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    地址 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={form.address}
                    onChange={(e) => update('address', e.target.value)}
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      fieldErrors.address ? 'border-red-500 focus:ring-red-500' : 'border-gray-300'
                    }`}
                    placeholder="請輸入地址"
                  />
                  {fieldErrors.address && (
                    <p className="mt-1 text-sm text-red-600">{fieldErrors.address}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    客戶類型 <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={form.customer_type}
                    onChange={(e) => update('customer_type', e.target.value as CustomerType | '')}
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      fieldErrors.customer_type ? 'border-red-500 focus:ring-red-500' : 'border-gray-300'
                    }`}
                  >
                    {CUSTOMER_TYPE_OPTIONS.map((opt) => (
                      <option key={opt.value || 'empty'} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                  {fieldErrors.customer_type && (
                    <p className="mt-1 text-sm text-red-600">{fieldErrors.customer_type}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">合作狀態</label>
                  <select
                    value={form.status}
                    onChange={(e) => update('status', e.target.value as CustomerStatus)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {STATUS_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                type="button"
                onClick={handleCancelEdit}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? '儲存中...' : '儲存'}
              </button>
            </div>
          </form>
        ) : (
          <div className="px-6 py-4 overflow-y-auto flex-1">
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-gray-500 font-medium">客戶名稱</dt>
                <dd className="text-gray-900">{customer.customer_name || '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">發票抬頭</dt>
                <dd className="text-gray-900">{customer.invoice_title || '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">統一編號</dt>
                <dd className="text-gray-900">{customer.invoice_number || '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">聯絡人</dt>
                <dd className="text-gray-900">{customer.primary_contact || '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">聯絡電話</dt>
                <dd className="text-gray-900">{customer.contact_phone || '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">LINE</dt>
                <dd className="text-gray-900">{customer.messaging_app_line || '—'}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-gray-500 font-medium">地址</dt>
                <dd className="text-gray-900">{customer.address || '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">客戶類型</dt>
                <dd className="text-gray-900">
                  {getCustomerTypeLabel(customer.customer_type)}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">合作狀態</dt>
                <dd>
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded ${
                      (customer.status ?? 'ACTIVE') === 'TERMINATED'
                        ? 'bg-gray-200 text-gray-700'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {getStatusLabel(customer.status)}
                  </span>
                </dd>
              </div>
            </dl>

            <h3 className="text-lg font-semibold text-gray-800 mt-6 mb-3">合約列表</h3>
            {contractsLoading ? (
              <div className="text-gray-500 py-4">載入合約中...</div>
            ) : contracts.length === 0 ? (
              <div className="text-gray-500 py-4">此客戶尚無合約</div>
            ) : (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        合約編號
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        產品名稱
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        開始日期
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        結束日期
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        月租
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        狀態
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {contracts.map((contract) => {
                      const statusDisplay = getContractStatusDisplay(contract);
                      return (
                        <tr
                          key={contract.id}
                          onClick={(e) => onContractRowClick(e, contract)}
                          className="hover:bg-gray-100 cursor-pointer transition-colors"
                        >
                          <td className="px-4 py-2 text-sm text-gray-900">
                            {contract.contract_number || '—'}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900">
                            {contract.product_name}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-700 whitespace-nowrap">
                            {formatDate(contract.start_date)}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-700 whitespace-nowrap">
                            {formatDate(contract.end_date)}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-700">
                            {contract.monthly_rent != null ? `$${contract.monthly_rent}` : '—'}
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <span
                              className={`px-2 py-0.5 text-xs font-medium rounded ${statusDisplay.className}`}
                            >
                              {statusDisplay.label}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
