import { useState, useCallback, useRef, useEffect } from 'react';
import { contractApi } from '../services/api';
import type { Contract, ContractWithCustomer } from '../types';
import type { Customer } from '../types';

const CONTRACT_STATUS_OPTIONS = [
  { value: 'PENDING', label: '待簽署' },
  { value: 'ACTIVE', label: '生效' }
];

const BILLING_INTERVAL_OPTIONS = [
  { value: '1', label: '1 個月' },
  { value: '2', label: '2 個月' },
  { value: '3', label: '3 個月' },
  { value: '6', label: '6 個月' },
  { value: '12', label: '12 個月' },
  { value: '24', label: '24 個月' },
  { value: '36', label: '36 個月' },
];

const PAYMENT_METHOD_OPTIONS = [
  { value: '', label: '請選擇' },
  { value: 'BANK_TRANSFER', label: '銀行轉帳' },
  { value: 'CASH', label: '現金' },
  { value: 'CHECK', label: '支票' },
  { value: 'OTHER', label: '其他' },
];

const INVOICE_TYPE_OPTIONS = [
  { value: '', label: '請選擇' },
  { value: 'NO_INVOICE', label: '不開立發票' },
  { value: 'DUPLICATE_UNIFORM_INVOICE', label: '二聯式發票' },
  { value: 'TRIPLE_UNIFORM_INVOICE', label: '三聯式發票' },
];

const CUSTOMER_LIST_MAX_HEIGHT = 240;

function filterCustomers(customers: Customer[], searchTerm: string): Customer[] {
  const q = searchTerm.trim().toLowerCase();
  if (!q) return customers;
  return customers.filter(
    (c) =>
      c.customer_name?.toLowerCase().includes(q) ||
      c.invoice_title?.toLowerCase().includes(q) ||
      c.invoice_number?.toLowerCase().includes(q)
  );
}

export interface AddContractModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (contract: ContractWithCustomer) => void;
  customers: Customer[];
}

const initialForm = {
  product_name: '',
  start_date: '',
  end_date: '',
  monthly_rent: '',
  billing_interval: '',
  status: 'PENDING' as Contract['status'],
  next_billing_date: '',
  notes: '',
  payment_method: '',
  invoice_type: '',
};

export default function AddContractModal({
  open,
  onClose,
  onSuccess,
  customers,
}: AddContractModalProps) {
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [customerSearchTerm, setCustomerSearchTerm] = useState('');
  const [customerDropdownOpen, setCustomerDropdownOpen] = useState(false);
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const customerDropdownRef = useRef<HTMLDivElement>(null);

  const filteredCustomers = filterCustomers(customers, customerSearchTerm);

  useEffect(() => {
    if (!open) {
      setSelectedCustomer(null);
      setCustomerSearchTerm('');
      setCustomerDropdownOpen(false);
      setForm(initialForm);
      setError(null);
      setFieldErrors({});
    }
  }, [open]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        customerDropdownRef.current &&
        !customerDropdownRef.current.contains(e.target as Node)
      ) {
        setCustomerDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const update = useCallback((field: string, value: string | number) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setError(null);
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      if (field === 'status' && value !== 'ACTIVE') delete next.next_billing_date;
      return next;
    });
  }, []);

  const handleClose = useCallback(() => {
    onClose();
  }, [onClose]);

  const handleSelectCustomer = useCallback((customer: Customer) => {
    setSelectedCustomer(customer);
    setCustomerSearchTerm('');
    setCustomerDropdownOpen(false);
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next.customer_id;
      return next;
    });
  }, []);

  const handleClearCustomer = useCallback(() => {
    setSelectedCustomer(null);
    setCustomerSearchTerm('');
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);
      const errors: Record<string, string> = {};

      if (!selectedCustomer) {
        errors.customer_id = '請選擇客戶';
      }
      if (!form.product_name.trim()) {
        errors.product_name = '請填寫產品名稱';
      }
      if (!form.start_date) {
        errors.start_date = '請選擇開始日期';
      }
      if (!form.end_date) {
        errors.end_date = '請選擇結束日期';
      }
      if (form.monthly_rent === '' || Number(form.monthly_rent) < 0) {
        errors.monthly_rent = '請填寫月租（0 或以上）';
      }
      if (!form.billing_interval) {
        errors.billing_interval = '請選擇帳單週期';
      }
      if (!form.invoice_type) {
        errors.invoice_type = '請選擇發票類型';
      }
      if (form.status === 'ACTIVE' && !form.next_billing_date) {
        errors.next_billing_date = '請選擇下次帳單日';
      }

      if (Object.keys(errors).length > 0) {
        setFieldErrors(errors);
        setError('請填寫必填欄位後再儲存。');
        return;
      }

      setFieldErrors({});
      setSubmitting(true);
      try {
        const monthlyRent = Number(form.monthly_rent);
        const payload = {
          customer_id: selectedCustomer!.id,
          product_name: form.product_name.trim(),
          start_date: `${form.start_date}T00:00:00`,
          end_date: `${form.end_date}T00:00:00`,
          monthly_rent: monthlyRent,
          billing_interval: form.billing_interval,
          status: form.status,
          next_billing_date:
            form.status === 'ACTIVE' && form.next_billing_date
              ? `${form.next_billing_date}T00:00:00`
              : null,
          notes: form.notes.trim() || null,
          payment_method: form.payment_method || null,
          invoice_type: form.invoice_type || null,
        };
        const created = await contractApi.create(payload);
        onClose();
        onSuccess({
          ...created,
          customer_name: selectedCustomer!.customer_name ?? null,
        });
      } catch (err: unknown) {
        const message =
          err && typeof err === 'object' && 'response' in err
            ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
            : null;
        setError(
          typeof message === 'string' ? message : '新增合約失敗，請稍後再試。'
        );
      } finally {
        setSubmitting(false);
      }
    },
    [selectedCustomer, form, onClose, onSuccess]
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-contract-modal-title"
    >
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 id="add-contract-modal-title" className="text-xl font-bold text-gray-800">
            新增合約
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

            {/* Customer selector */}
            <div className="mb-4" ref={customerDropdownRef}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                客戶 <span className="text-red-500">*</span>
              </label>
              {selectedCustomer ? (
                <div className="flex items-center gap-2">
                  <span className="flex-1 px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-800">
                    {selectedCustomer.customer_name || selectedCustomer.invoice_title || '—'}
                  </span>
                  <button
                    type="button"
                    onClick={handleClearCustomer}
                    className="px-3 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
                  >
                    變更
                  </button>
                </div>
              ) : (
                <>
                  <input
                    type="text"
                    value={customerSearchTerm}
                    onChange={(e) => {
                      setCustomerSearchTerm(e.target.value);
                      setCustomerDropdownOpen(true);
                    }}
                    onFocus={() => setCustomerDropdownOpen(true)}
                    placeholder="搜尋客戶名稱、發票抬頭或統一編號..."
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      fieldErrors.customer_id ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {fieldErrors.customer_id && (
                    <p className="mt-1 text-sm text-red-600">{fieldErrors.customer_id}</p>
                  )}
                  {customerDropdownOpen && (
                    <ul
                      className="mt-1 border border-gray-200 rounded-lg bg-white shadow-lg overflow-y-auto"
                      style={{ maxHeight: CUSTOMER_LIST_MAX_HEIGHT }}
                    >
                      {filteredCustomers.length === 0 ? (
                        <li className="px-4 py-3 text-sm text-gray-500">
                          找不到符合的客戶
                        </li>
                      ) : (
                        filteredCustomers.map((c) => (
                          <li
                            key={c.id}
                            role="option"
                            onClick={() => handleSelectCustomer(c)}
                            className="px-4 py-2 hover:bg-gray-100 cursor-pointer text-sm text-gray-900 border-b border-gray-100 last:border-b-0"
                          >
                            <span className="font-medium">
                              {c.customer_name || '未命名'}
                            </span>
                            {c.invoice_title && (
                              <span className="text-gray-500 ml-2">
                                （{c.invoice_title}）
                              </span>
                            )}
                          </li>
                        ))
                      )}
                    </ul>
                  )}
                </>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  產品名稱 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  maxLength={30}
                  value={form.product_name}
                  onChange={(e) => update('product_name', e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.product_name ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="請輸入產品名稱（最多 30 字）"
                />
                {fieldErrors.product_name && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.product_name}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  開始日期 <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={form.start_date}
                  onChange={(e) => update('start_date', e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.start_date ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {fieldErrors.start_date && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.start_date}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  結束日期 <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={form.end_date}
                  onChange={(e) => update('end_date', e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.end_date ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {fieldErrors.end_date && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.end_date}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  月租 (台幣)<span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  min={0}
                  value={form.monthly_rent}
                  onChange={(e) => update('monthly_rent', e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.monthly_rent ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="0"
                />
                {fieldErrors.monthly_rent && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.monthly_rent}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  帳單週期 <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.billing_interval}
                  onChange={(e) => update('billing_interval', e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.billing_interval ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">請選擇</option>
                  {BILLING_INTERVAL_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                {fieldErrors.billing_interval && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.billing_interval}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  合約狀態 <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.status}
                  onChange={(e) => update('status', e.target.value as Contract['status'])}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {CONTRACT_STATUS_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              {form.status === 'ACTIVE' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    下次帳單日 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={form.next_billing_date}
                    onChange={(e) => update('next_billing_date', e.target.value)}
                    className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      fieldErrors.next_billing_date
                        ? 'border-red-500 focus:ring-red-500'
                        : 'border-gray-300'
                    }`}
                  />
                  {fieldErrors.next_billing_date && (
                    <p className="mt-1 text-sm text-red-600">
                      {fieldErrors.next_billing_date}
                    </p>
                  )}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  付款方式
                </label>
                <select
                  value={form.payment_method}
                  onChange={(e) => update('payment_method', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {PAYMENT_METHOD_OPTIONS.map((opt) => (
                    <option key={opt.value || 'empty'} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  發票類型 <span className="text-red-500">*</span>
                </label>
                <select
                  value={form.invoice_type}
                  onChange={(e) => update('invoice_type', e.target.value)}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    fieldErrors.invoice_type ? 'border-red-500 focus:ring-red-500' : 'border-gray-300'
                  }`}
                >
                  {INVOICE_TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value || 'empty'} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                {fieldErrors.invoice_type && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.invoice_type}</p>
                )}
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  備註
                </label>
                <textarea
                  rows={2}
                  maxLength={300}
                  value={form.notes}
                  onChange={(e) => update('notes', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="選填，最多 300 字"
                />
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
