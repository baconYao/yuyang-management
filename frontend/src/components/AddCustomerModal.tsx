import { useState, useCallback } from 'react';
import { customerApi } from '../services/api';
import type { Customer } from '../types';
import { CustomerType } from '../types';
import type { CustomerStatus } from '../types';
import { getCustomerTypeLabel } from '../utils/customerTypeLabels';

const CUSTOMER_TYPE_OPTIONS = [
  { value: '', label: '請選擇' },
  ...Object.values(CustomerType).map((t) => ({ value: t, label: getCustomerTypeLabel(t) })),
];

const STATUS_OPTIONS: { value: CustomerStatus; label: string }[] = [
  { value: 'ACTIVE', label: '合作中' },
  { value: 'TERMINATED', label: '無合作' },
];

export interface AddCustomerModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (customer: Customer) => void;
}

const initialForm = {
  customer_name: '',
  invoice_title: '',
  invoice_number: '',
  primary_contact: '',
  contact_phone: '',
  messaging_app_line: '',
  address: '',
  customer_type: '' as CustomerType | '',
  status: 'ACTIVE' as CustomerStatus,
};

const REQUIRED_FIELDS: { key: keyof typeof initialForm; label: string }[] = [
  { key: 'customer_name', label: '客戶名稱' },
  { key: 'primary_contact', label: '聯絡人' },
  { key: 'contact_phone', label: '聯絡電話' },
  { key: 'address', label: '地址' },
  { key: 'customer_type', label: '客戶類型' },
];

export default function AddCustomerModal({
  open,
  onClose,
  onSuccess,
}: AddCustomerModalProps) {
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof typeof form, string>>>({});

  const update = useCallback(
    (field: keyof typeof form, value: string | CustomerStatus) => {
      setForm((prev) => ({ ...prev, [field]: value }));
      setError(null);
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    },
    []
  );

  const reset = useCallback(() => {
    setForm(initialForm);
    setError(null);
    setFieldErrors({});
    setSubmitting(false);
  }, []);

  const handleClose = useCallback(() => {
    reset();
    onClose();
  }, [onClose, reset]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);
      const errors: Partial<Record<keyof typeof form, string>> = {};
      for (const { key, label } of REQUIRED_FIELDS) {
        const value = form[key];
        const trimmed = typeof value === 'string' ? value.trim() : value;
        if (trimmed === '' || trimmed == null) {
          errors[key] = `請填寫${label}`;
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
        const created = await customerApi.create(payload);
        reset();
        onClose();
        onSuccess(created);
      } catch (err: unknown) {
        const message =
          err && typeof err === 'object' && 'response' in err
            ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
            : null;
        setError(
          typeof message === 'string' ? message : '新增客戶失敗，請稍後再試。'
        );
      } finally {
        setSubmitting(false);
      }
    },
    [form, onClose, onSuccess, reset]
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-customer-modal-title"
    >
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 id="add-customer-modal-title" className="text-xl font-bold text-gray-800">
            新增客戶
          </h2>
          <button
            type="button"
            onClick={handleClose}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
            aria-label="關閉"
          >
            <span className="text-2xl leading-none">&times;</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="px-6 py-4 overflow-y-auto flex-1">
            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm">
                {error}
              </div>
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
                    fieldErrors.customer_name
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300'
                  }`}
                  placeholder="請輸入客戶名稱"
                  aria-invalid={!!fieldErrors.customer_name}
                  aria-describedby={fieldErrors.customer_name ? 'customer_name-error' : undefined}
                />
                {fieldErrors.customer_name && (
                  <p id="customer_name-error" className="mt-1 text-sm text-red-600">
                    {fieldErrors.customer_name}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  發票抬頭
                </label>
                <input
                  type="text"
                  value={form.invoice_title}
                  onChange={(e) => update('invoice_title', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="請輸入發票抬頭"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  統一編號
                </label>
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
                    fieldErrors.primary_contact
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300'
                  }`}
                  placeholder="請輸入聯絡人"
                  aria-invalid={!!fieldErrors.primary_contact}
                  aria-describedby={fieldErrors.primary_contact ? 'primary_contact-error' : undefined}
                />
                {fieldErrors.primary_contact && (
                  <p id="primary_contact-error" className="mt-1 text-sm text-red-600">
                    {fieldErrors.primary_contact}
                  </p>
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
                    fieldErrors.contact_phone
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300'
                  }`}
                  placeholder="請輸入聯絡電話"
                  aria-invalid={!!fieldErrors.contact_phone}
                  aria-describedby={fieldErrors.contact_phone ? 'contact_phone-error' : undefined}
                />
                {fieldErrors.contact_phone && (
                  <p id="contact_phone-error" className="mt-1 text-sm text-red-600">
                    {fieldErrors.contact_phone}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  LINE
                </label>
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
                    fieldErrors.address
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300'
                  }`}
                  placeholder="請輸入地址"
                  aria-invalid={!!fieldErrors.address}
                  aria-describedby={fieldErrors.address ? 'address-error' : undefined}
                />
                {fieldErrors.address && (
                  <p id="address-error" className="mt-1 text-sm text-red-600">
                    {fieldErrors.address}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  客戶類型 <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.customer_type}
                  onChange={(e) =>
                    update('customer_type', e.target.value as CustomerType | '')
                  }
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.customer_type
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300'
                  }`}
                  aria-invalid={!!fieldErrors.customer_type}
                  aria-describedby={fieldErrors.customer_type ? 'customer_type-error' : undefined}
                >
                  {CUSTOMER_TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value || 'empty'} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                {fieldErrors.customer_type && (
                  <p id="customer_type-error" className="mt-1 text-sm text-red-600">
                    {fieldErrors.customer_type}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  合作狀態
                </label>
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
              onClick={handleClose}
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
      </div>
    </div>
  );
}
