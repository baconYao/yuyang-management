import { useCallback, useEffect, useState } from 'react';
import { billApi, contractApi } from '../services/api';
import type { Bill, Contract, ContractWithCustomer } from '../types';
import { getBillStatusDisplay } from '../utils/billStatusDisplay';
import { getContractStatusDisplay } from '../utils/contractStatusDisplay';
import BillDetailModal from './BillDetailModal';

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
    return d.toISOString().slice(0, 10);
  } catch {
    return '';
  }
}

const CONTRACT_STATUS_OPTIONS = [
  { value: 'ACTIVE', label: '生效' },
  { value: 'TERMINATED', label: '終止' },
  { value: 'PENDING', label: '待簽署' },
  { value: 'ENDED', label: '結束' },
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
  { value: 'BANK_TRANSFER', label: '銀行轉帳' },
  { value: 'CASH', label: '現金' },
  { value: 'CHECK', label: '支票' },
  { value: 'OTHER', label: '其他' },
];

const INVOICE_TYPE_OPTIONS = [
  { value: 'NO_INVOICE', label: '不開立發票' },
  { value: 'DUPLICATE_UNIFORM_INVOICE', label: '二聯式發票' },
  { value: 'TRIPLE_UNIFORM_INVOICE', label: '三聯式發票' },
];

function getPaymentMethodLabel(value: string | null | undefined): string {
  if (!value) return '—';
  const opt = PAYMENT_METHOD_OPTIONS.find((o) => o.value === value);
  return opt?.label ?? value;
}

function getBillingIntervalDisplay(value: string | null | undefined): string {
  if (!value) return '—';
  return `${value} 月`;
}

function getInvoiceTypeLabel(value: string | null | undefined): string {
  if (!value) return '—';
  const opt = INVOICE_TYPE_OPTIONS.find((o) => o.value === value);
  return opt?.label ?? value;
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

const initialEditForm = {
  notes: '',
  status: 'ACTIVE',
  payment_method: '',
  next_billing_date: '',
  terminated_at: '',
  termination_reason: '',
  billing_interval: '',
  invoice_type: '',
};

export interface ContractDetailModalProps {
  contract: ContractWithCustomer | null;
  onClose: () => void;
  onContractUpdated?: (contract: ContractWithCustomer) => void;
}

export default function ContractDetailModal({
  contract,
  onClose,
  onContractUpdated,
}: ContractDetailModalProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState(initialEditForm);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [bills, setBills] = useState<Bill[]>([]);
  const [billsLoading, setBillsLoading] = useState(false);
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);

  const fetchBills = useCallback(async (contractId: string) => {
    setBillsLoading(true);
    try {
      const list = await billApi.getByContractId(contractId);
      const sorted = [...list].sort((a, b) => {
        const at = a.created_at ? new Date(a.created_at).getTime() : 0;
        const bt = b.created_at ? new Date(b.created_at).getTime() : 0;
        return bt - at;
      });
      setBills(sorted);
    } catch {
      setBills([]);
    } finally {
      setBillsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!contract) return;
    setEditForm({
      notes: contract.notes ?? '',
      status: contract.status ?? 'ACTIVE',
      payment_method: contract.payment_method ?? '',
      next_billing_date: toDateInputValue(contract.next_billing_date),
      terminated_at: toDateInputValue(contract.terminated_at),
      termination_reason: contract.termination_reason ?? '',
      billing_interval: contract.billing_interval ?? '',
      invoice_type: contract.invoice_type ?? '',
    });
    setIsEditing(false);
    setSaveError(null);
    fetchBills(contract.id);
  }, [contract, fetchBills]);

  if (!contract) return null;

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveError(null);
    setSaveLoading(true);
    try {
      const payload: Partial<Contract> = {
        notes: editForm.notes || null,
        status: editForm.status as Contract['status'],
        payment_method: editForm.payment_method || null,
        next_billing_date: editForm.next_billing_date
          ? `${editForm.next_billing_date}T00:00:00.000Z`
          : null,
        terminated_at: editForm.terminated_at
          ? `${editForm.terminated_at}T00:00:00.000Z`
          : null,
        termination_reason: editForm.termination_reason || null,
        billing_interval: editForm.billing_interval || undefined,
        invoice_type: editForm.invoice_type || null,
      };
      const updated = await contractApi.update(contract.id, payload);
      const withCustomer: ContractWithCustomer = {
        ...updated,
        customer_name: contract.customer_name,
      };
      onContractUpdated?.(withCustomer);
      setIsEditing(false);
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : '儲存失敗');
    } finally {
      setSaveLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditForm({
      notes: contract.notes ?? '',
      status: contract.status ?? 'ACTIVE',
      payment_method: contract.payment_method ?? '',
      next_billing_date: toDateInputValue(contract.next_billing_date),
      terminated_at: toDateInputValue(contract.terminated_at),
      termination_reason: contract.termination_reason ?? '',
      billing_interval: contract.billing_interval ?? '',
      invoice_type: contract.invoice_type ?? '',
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
      aria-labelledby="contract-modal-title"
    >
      <div
        className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 id="contract-modal-title" className="text-xl font-bold text-gray-800">
            合約詳情
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
            <form onSubmit={handleSaveEdit} className="flex flex-col flex-1 overflow-hidden">
              <div className="overflow-y-auto flex-1">
                {saveError && (
                  <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm">
                    {saveError}
                  </div>
                )}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      合約編號
                    </label>
                    <div className="w-full px-4 py-2 rounded-lg border border-gray-200 bg-gray-50 text-gray-900 text-sm">
                      {contract.contract_number || contract.id?.slice(0, 8) || '—'}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      客戶名稱
                    </label>
                    <div className="w-full px-4 py-2 rounded-lg border border-gray-200 bg-gray-50 text-gray-900 text-sm">
                      {contract.customer_name || '—'}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      產品名稱
                    </label>
                    <div className="w-full px-4 py-2 rounded-lg border border-gray-200 bg-gray-50 text-gray-900 text-sm">
                      {contract.product_name || '—'}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      起始日期
                    </label>
                    <div className="w-full px-4 py-2 rounded-lg border border-gray-200 bg-gray-50 text-gray-900 text-sm">
                      {formatDate(contract.start_date)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      結束日期
                    </label>
                    <div className="w-full px-4 py-2 rounded-lg border border-gray-200 bg-gray-50 text-gray-900 text-sm">
                      {formatDate(contract.end_date)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      月租
                    </label>
                    <div className="w-full px-4 py-2 rounded-lg border border-gray-200 bg-gray-50 text-gray-900 text-sm">
                      {contract.monthly_rent != null ? `$${contract.monthly_rent}` : '—'}
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      合約狀態
                    </label>
                    <select
                      value={editForm.status}
                      onChange={(e) => setEditForm((f) => ({ ...f, status: e.target.value }))}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {CONTRACT_STATUS_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {editForm.status === 'ACTIVE' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        下次帳單日
                      </label>
                      <input
                        type="date"
                        value={editForm.next_billing_date}
                        onChange={(e) =>
                          setEditForm((f) => ({ ...f, next_billing_date: e.target.value }))
                        }
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      付款方式
                    </label>
                    <select
                      value={editForm.payment_method}
                      onChange={(e) =>
                        setEditForm((f) => ({ ...f, payment_method: e.target.value }))
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">請選擇</option>
                      {PAYMENT_METHOD_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      發票類型
                    </label>
                    <select
                      value={editForm.invoice_type}
                      onChange={(e) =>
                        setEditForm((f) => ({ ...f, invoice_type: e.target.value }))
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">請選擇</option>
                      {INVOICE_TYPE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      帳單週期
                    </label>
                    <select
                      value={editForm.billing_interval}
                      onChange={(e) =>
                        setEditForm((f) => ({ ...f, billing_interval: e.target.value }))
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">請選擇</option>
                      {BILLING_INTERVAL_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {editForm.status === 'TERMINATED' && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          終止日期
                        </label>
                        <input
                          type="date"
                          value={editForm.terminated_at}
                          onChange={(e) =>
                            setEditForm((f) => ({ ...f, terminated_at: e.target.value }))
                          }
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          終止原因
                        </label>
                        <input
                          type="text"
                          value={editForm.termination_reason}
                          onChange={(e) =>
                            setEditForm((f) => ({ ...f, termination_reason: e.target.value }))
                          }
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="選填"
                        />
                      </div>
                    </>
                  )}
                  <div className="sm:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      備註
                    </label>
                    <textarea
                      value={editForm.notes}
                      onChange={(e) => setEditForm((f) => ({ ...f, notes: e.target.value }))}
                      rows={2}
                      maxLength={300}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="選填，最多 300 字"
                    />
                  </div>
                </div>
              </div>
              <div className="pt-4 mt-4 border-t border-gray-200 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={saveLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saveLoading ? '儲存中...' : '儲存'}
                </button>
              </div>
            </form>
          ) : (
            <>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-gray-500 font-medium">合約編號</dt>
                <dd className="text-gray-900">{contract.contract_number || '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">客戶名稱</dt>
                <dd className="text-gray-900">{contract.customer_name || '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">產品名稱</dt>
                <dd className="text-gray-900">{contract.product_name}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">起始日期</dt>
                <dd className="text-gray-900">{formatDate(contract.start_date)}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">結束日期</dt>
                <dd className="text-gray-900">{formatDate(contract.end_date)}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">月租</dt>
                <dd className="text-gray-900">
                  {contract.monthly_rent != null ? `$${contract.monthly_rent}` : '—'}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">狀態</dt>
                <dd>
                  <span
                    className={`px-2 py-0.5 text-xs font-medium rounded ${
                      getContractStatusDisplay(contract).className
                    }`}
                  >
                    {getContractStatusDisplay(contract).label}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">帳單週期</dt>
                <dd className="text-gray-900">
                  {getBillingIntervalDisplay(contract.billing_interval)}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">付款方式</dt>
                <dd className="text-gray-900">
                  {getPaymentMethodLabel(contract.payment_method)}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">發票類型</dt>
                <dd className="text-gray-900">
                  {getInvoiceTypeLabel(contract.invoice_type)}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">下次帳單日</dt>
                <dd className="text-gray-900">{formatDate(contract.next_billing_date)}</dd>
              </div>
              <div>
                <dt className="text-gray-500 font-medium">終止日期</dt>
                <dd className="text-gray-900">{formatDate(contract.terminated_at)}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-gray-500 font-medium">終止原因</dt>
                <dd className="text-gray-900">{contract.termination_reason || '—'}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-gray-500 font-medium">備註</dt>
                <dd className="text-gray-900">{contract.notes || '—'}</dd>
              </div>
            </dl>

            <h3 className="text-lg font-semibold text-gray-800 mt-6 mb-3">帳單列表</h3>
            {billsLoading ? (
              <div className="text-gray-500 py-4">載入帳單中...</div>
            ) : bills.length === 0 ? (
              <div className="text-gray-500 py-4">此合約尚無帳單</div>
            ) : (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        帳單編號
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        起始日期
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        總金額
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        狀態
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {bills.map((bill) => {
                      const statusDisplay = getBillStatusDisplay(bill);
                      return (
                        <tr
                          key={bill.bill_number}
                          role="button"
                          tabIndex={0}
                          onClick={() => setSelectedBill(bill)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              setSelectedBill(bill);
                            }
                          }}
                          className="hover:bg-gray-50 transition-colors cursor-pointer"
                        >
                          <td className="px-4 py-2 text-sm text-gray-900">
                            {bill.bill_number}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-700 whitespace-nowrap">
                            {formatDate(bill.created_at)}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-700">
                            ${bill.amount}
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
            </>
          )}
        </div>
      </div>

      {selectedBill && contract && (
        <BillDetailModal
          bill={selectedBill}
          customerName={contract.customer_name ?? null}
          onClose={() => setSelectedBill(null)}
          onBillUpdated={(updated) => {
            fetchBills(contract.id);
            setSelectedBill(updated);
          }}
        />
      )}
    </div>
  );
}
