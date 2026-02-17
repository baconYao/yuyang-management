import { useCallback, useEffect, useState } from 'react';
import { billApi, contractApi } from '../services/api';
import type { Bill, BillStatus } from '../types';
import { getBillStatusDisplay } from '../utils/billStatusDisplay';

const INVOICE_TYPE_OPTIONS = [
  { value: 'NO_INVOICE', label: '不開立發票' },
  { value: 'DUPLICATE_UNIFORM_INVOICE', label: '二聯式發票' },
  { value: 'TRIPLE_UNIFORM_INVOICE', label: '三聯式發票' },
];

const BILL_STATUS_OPTIONS = [
  { value: 'DRAFT', label: '草稿' },
  { value: 'SENT', label: '已寄出' },
  { value: 'PROCESSING', label: '對帳中' },
  { value: 'PAID', label: '已結案' },
  { value: 'OVERDUE', label: '已逾期' },
  { value: 'CANCELLED', label: '已作廢' },
];

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  } catch {
    return iso;
  }
}

function toDateInputValue(iso: string | null | undefined): string {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toISOString().slice(0, 16); // for datetime-local we need to slice to 16 for YYYY-MM-DDTHH:mm
  } catch {
    return '';
  }
}

function getInvoiceTypeLabel(value: string | null | undefined): string {
  if (!value) return '—';
  return INVOICE_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

function getBillingIntervalDisplay(value: string | null | undefined): string {
  if (!value) return '—';
  return `${value} 月`;
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

export interface BillDetailModalProps {
  bill: Bill | null;
  customerName: string | null;
  onClose: () => void;
  onBillUpdated?: (bill: Bill) => void;
}

export default function BillDetailModal({
  bill,
  customerName,
  onClose,
  onBillUpdated,
}: BillDetailModalProps) {
  const [billingIntervalDisplay, setBillingIntervalDisplay] = useState<string>('—');
  const [isEditing, setIsEditing] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    status: 'DRAFT' as BillStatus,
    notes: '',
    tax_amount: '',
    monthly_rent: '',
    invoice_type: '',
    due_date: '',
    sent_at: '',
    paid_at: '',
  });

  const fetchContractForBillingInterval = useCallback(async (contractId: string) => {
    try {
      const contract = await contractApi.getById(contractId);
      setBillingIntervalDisplay(getBillingIntervalDisplay(contract.billing_interval ?? null));
    } catch {
      setBillingIntervalDisplay('—');
    }
  }, []);

  useEffect(() => {
    if (!bill) return;
    setEditForm({
      status: bill.status,
      notes: bill.notes ?? '',
      tax_amount: bill.tax_amount.toString(),
      monthly_rent: bill.monthly_rent.toString(),
      invoice_type: bill.invoice_type ?? '',
      due_date: toDateInputValue(bill.due_date).slice(0, 10),
      sent_at: toDateInputValue(bill.sent_at).slice(0, 10),
      paid_at: toDateInputValue(bill.paid_at).slice(0, 10),
    });
    setIsEditing(false);
    setSaveError(null);
    fetchContractForBillingInterval(bill.contract_id);
  }, [bill, fetchContractForBillingInterval]);

  if (!bill) return null;

  const statusDisplay = getBillStatusDisplay(bill);

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveError(null);
    setSaveLoading(true);
    try {
      const payload = {
        status: editForm.status,
        notes: editForm.notes || null,
        tax_amount: editForm.tax_amount ? parseFloat(editForm.tax_amount) : null,
        monthly_rent: editForm.monthly_rent ? parseFloat(editForm.monthly_rent) : null,
        invoice_type: editForm.invoice_type || null,
        due_date: editForm.due_date ? `${editForm.due_date}T00:00:00.000Z` : null,
        sent_at: editForm.sent_at ? `${editForm.sent_at}T00:00:00.000Z` : null,
        paid_at: editForm.paid_at ? `${editForm.paid_at}T00:00:00.000Z` : null,
      };
      const updated = await billApi.update(bill.bill_number, payload);
      onBillUpdated?.(updated);
      setIsEditing(false);
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : '儲存失敗');
    } finally {
      setSaveLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditForm({
      status: bill.status,
      notes: bill.notes ?? '',
      tax_amount: bill.tax_amount.toString(),
      monthly_rent: bill.monthly_rent.toString(),
      invoice_type: bill.invoice_type ?? '',
      due_date: toDateInputValue(bill.due_date).slice(0, 10),
      sent_at: toDateInputValue(bill.sent_at).slice(0, 10),
      paid_at: toDateInputValue(bill.paid_at).slice(0, 10),
    });
    setIsEditing(false);
    setSaveError(null);
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="bill-modal-title"
    >
      <div
        className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 id="bill-modal-title" className="text-xl font-bold text-gray-800">
            帳單詳情
          </h2>
          <div className="flex items-center gap-2">
            {!isEditing ? (
              <button
                type="button"
                onClick={handleStartEdit}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
                aria-label="編輯"
                title="編輯"
              >
                <EditIcon className="w-5 h-5" />
              </button>
            ) : null}
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

        <div className="px-6 py-4 overflow-y-auto flex-1">
          {isEditing ? (
            <form onSubmit={handleSaveEdit} className="space-y-4">
              {saveError && (
                <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">
                  {saveError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">狀態</label>
                <select
                  value={editForm.status}
                  onChange={(e) =>
                    setEditForm((f) => ({ ...f, status: e.target.value as BillStatus }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {BILL_STATUS_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">備註</label>
                <textarea
                  value={editForm.notes}
                  onChange={(e) => setEditForm((f) => ({ ...f, notes: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">月租金額</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={editForm.monthly_rent}
                  onChange={(e) => setEditForm((f) => ({ ...f, monthly_rent: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">稅額</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={editForm.tax_amount}
                  onChange={(e) => setEditForm((f) => ({ ...f, tax_amount: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">發票類型</label>
                <select
                  value={editForm.invoice_type}
                  onChange={(e) => setEditForm((f) => ({ ...f, invoice_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">—</option>
                  {INVOICE_TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">繳費期限</label>
                <input
                  type="date"
                  value={editForm.due_date}
                  onChange={(e) => setEditForm((f) => ({ ...f, due_date: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">寄出時間</label>
                <input
                  type="date"
                  value={editForm.sent_at}
                  onChange={(e) => setEditForm((f) => ({ ...f, sent_at: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">付款時間</label>
                <input
                  type="date"
                  value={editForm.paid_at}
                  onChange={(e) => setEditForm((f) => ({ ...f, paid_at: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={saveLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saveLoading ? '儲存中...' : '儲存'}
                </button>
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
              </div>
            </form>
          ) : (
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-gray-500 font-medium">帳單編號</dt>
                <dd className="text-gray-900">{bill.bill_number}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">客戶名稱</dt>
                <dd className="text-gray-900">{customerName ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">帳單起始日期</dt>
                <dd className="text-gray-900">{formatDate(bill.created_at)}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">帳單週期</dt>
                <dd className="text-gray-900">{billingIntervalDisplay}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">發票類型</dt>
                <dd className="text-gray-900">{getInvoiceTypeLabel(bill.invoice_type)}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">月租金額</dt>
                <dd className="text-gray-900">${bill.monthly_rent}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">稅額</dt>
                <dd className="text-gray-900">${bill.tax_amount}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">總金額</dt>
                <dd className="text-gray-900 font-medium">${bill.amount}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">狀態</dt>
                <dd>
                  <span
                    className={`px-2 py-0.5 text-xs font-medium rounded ${statusDisplay.className}`}
                  >
                    {statusDisplay.label}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">繳費期限</dt>
                <dd className="text-gray-900">{formatDate(bill.due_date)}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">寄出時間</dt>
                <dd className="text-gray-900">{formatDate(bill.sent_at)}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">付款時間</dt>
                <dd className="text-gray-900">{formatDate(bill.paid_at)}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-gray-500 font-medium">備註</dt>
                <dd className="text-gray-900">{bill.notes || '—'}</dd>
              </div>
            </dl>
          )}
        </div>
      </div>
    </div>
  );
}
