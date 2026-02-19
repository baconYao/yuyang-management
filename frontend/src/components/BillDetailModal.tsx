import { useCallback, useEffect, useState } from 'react';
import { billApi, contractApi } from '../services/api';
import type { Bill, BillStatus } from '../types';
import { getBillStatusDisplay } from '../utils/billStatusDisplay';

export interface BillItemRow {
  id: string;
  productName: string;
  quantity: number;
  unitPrice: number;
  amount: number;
}

function createRow(
  productName: string,
  quantity: number,
  unitPrice: number,
  id?: string
): BillItemRow {
  return {
    id: id ?? crypto.randomUUID(),
    productName,
    quantity,
    unitPrice,
    amount: Math.round(quantity * unitPrice * 100) / 100,
  };
}

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
  const [tableRows, setTableRows] = useState<BillItemRow[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
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

  const fetchContractAndInitTable = useCallback(async (contractId: string, billData: Bill) => {
    try {
      const contract = await contractApi.getById(contractId);
      setBillingIntervalDisplay(getBillingIntervalDisplay(contract.billing_interval ?? null));
      if (billData.items && billData.items.length > 0) {
        const sorted = [...billData.items].sort((a, b) => a.sort_order - b.sort_order);
        setTableRows(
          sorted.map((it) =>
            createRow(it.product_name, it.quantity, it.unit_price)
          )
        );
      } else {
        const intervalNum = parseInt(contract.billing_interval ?? '1', 10) || 1;
        const productName = contract.product_name ?? '';
        setTableRows([
          createRow(productName, intervalNum, billData.monthly_rent),
        ]);
      }
    } catch {
      setBillingIntervalDisplay('—');
      setTableRows([]);
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
    setPdfError(null);
    fetchContractAndInitTable(bill.contract_id, bill);
  }, [bill, fetchContractAndInitTable]);

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
        items: tableRows.map((row, index) => ({
          product_name: row.productName,
          quantity: row.quantity,
          unit_price: row.unitPrice,
          amount: row.amount,
          sort_order: index,
        })),
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
    fetchContractAndInitTable(bill.contract_id, bill);
  };

  const updateTableRow = (index: number, field: keyof BillItemRow, value: string | number) => {
    if (field === 'id') return;
    setTableRows((prev) => {
      const next = [...prev];
      const row = { ...next[index] };
      if (field === 'productName') row.productName = String(value);
      else if (field === 'quantity') row.quantity = Number(value) || 0;
      else if (field === 'unitPrice') row.unitPrice = Number(value) || 0;
      row.amount = Math.round(row.quantity * row.unitPrice * 100) / 100;
      next[index] = row;
      return next;
    });
  };

  const addTableRow = () => {
    setTableRows((prev) => [...prev, createRow('', 1, 0)]);
  };

  const removeTableRow = (index: number) => {
    if (index <= 0) return;
    setTableRows((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDownloadPdf = async () => {
    if (!bill) return;
    setPdfError(null);
    setPdfLoading(true);
    try {
      const blob = await billApi.downloadPdf(bill.bill_number);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${bill.bill_number}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setPdfError(err instanceof Error ? err.message : '下載失敗');
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50"
      onClick={() => { if (!isEditing) onClose(); }}
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
              <>
                <button
                  type="button"
                  onClick={handleDownloadPdf}
                  disabled={pdfLoading}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 disabled:opacity-50"
                  aria-label="下載帳單"
                  title="下載帳單"
                >
                  {pdfLoading ? '下載中…' : '下載帳單'}
                </button>
                <button
                  type="button"
                  onClick={handleStartEdit}
                  className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
                  aria-label="編輯"
                  title="編輯"
                >
                  <EditIcon className="w-5 h-5" />
                </button>
              </>
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
          {pdfError && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm">
              {pdfError}
            </div>
          )}
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
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">明細</label>
                  <button
                    type="button"
                    onClick={addTableRow}
                    className="text-sm px-2 py-1 border border-gray-300 rounded hover:bg-gray-50 text-gray-700"
                  >
                    新增一列
                  </button>
                </div>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-200">
                        <th className="text-left py-2 px-3 font-medium text-gray-700">品名</th>
                        <th className="text-right py-2 px-3 font-medium text-gray-700">數量</th>
                        <th className="text-right py-2 px-3 font-medium text-gray-700">單價</th>
                        <th className="text-right py-2 px-3 font-medium text-gray-700">金額</th>
                        <th className="w-12" aria-label="操作" />
                      </tr>
                    </thead>
                    <tbody>
                      {tableRows.map((row, index) => (
                        <tr key={row.id} className="border-b border-gray-100 last:border-0">
                          <td className="py-1.5 px-3">
                            <input
                              type="text"
                              value={row.productName}
                              onChange={(e) => updateTableRow(index, 'productName', e.target.value)}
                              className="w-full px-2 py-1 border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                              placeholder="品名"
                            />
                          </td>
                          <td className="py-1.5 px-3 text-right">
                            <input
                              type="number"
                              min="0"
                              step="1"
                              value={row.quantity}
                              onChange={(e) =>
                                updateTableRow(index, 'quantity', parseFloat(e.target.value) || 0)
                              }
                              className="w-20 px-2 py-1 border border-gray-200 rounded text-right focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                          </td>
                          <td className="py-1.5 px-3 text-right">
                            <input
                              type="number"
                              min="0"
                              step="0.01"
                              value={row.unitPrice}
                              onChange={(e) =>
                                updateTableRow(index, 'unitPrice', parseFloat(e.target.value) || 0)
                              }
                              className="w-24 px-2 py-1 border border-gray-200 rounded text-right focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                          </td>
                          <td className="py-1.5 px-3 text-right text-gray-900 tabular-nums">
                            {row.amount.toFixed(2)}
                          </td>
                          <td className="py-1.5 px-2 text-center">
                            {index > 0 ? (
                              <button
                                type="button"
                                onClick={() => removeTableRow(index)}
                                className="p-1 text-red-600 hover:bg-red-50 rounded"
                                aria-label="移除"
                                title="移除"
                              >
                                移除
                              </button>
                            ) : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {(() => {
                  const subtotal = tableRows.reduce((s, r) => s + r.amount, 0);
                  const invType = editForm.invoice_type || '';
                  const vatLabel =
                    invType === 'NO_INVOICE'
                      ? '未'
                      : invType === 'DUPLICATE_UNIFORM_INVOICE'
                        ? '已內含'
                        : invType === 'TRIPLE_UNIFORM_INVOICE'
                          ? (subtotal * 0.05).toFixed(2)
                          : '—';
                  const vatDisplay =
                    invType === 'TRIPLE_UNIFORM_INVOICE' ? `$${vatLabel}` : vatLabel;
                  const total =
                    invType === 'TRIPLE_UNIFORM_INVOICE'
                      ? subtotal + subtotal * 0.05
                      : subtotal;
                  return (
                    <div className="mt-4 pt-4 border-t border-gray-200 text-sm">
                      <div className="flex justify-between text-gray-700">
                        <span>合計</span>
                        <span className="tabular-nums">${subtotal.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-gray-700 mt-1">
                        <span>營業稅 5%</span>
                        <span className="tabular-nums">{vatDisplay}</span>
                      </div>
                      <div className="flex justify-between font-medium text-gray-900 mt-2">
                        <span>總計</span>
                        <span className="tabular-nums">${total.toFixed(2)}</span>
                      </div>
                    </div>
                  );
                })()}
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
            <div className="space-y-6">
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

            <div className="mt-6">
              <span className="text-sm font-medium text-gray-700">明細</span>
              <div className="border border-gray-200 rounded-lg overflow-hidden mt-2">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="text-left py-2 px-3 font-medium text-gray-700">品名</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-700">數量</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-700">單價</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-700">金額</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row) => (
                      <tr key={row.id} className="border-b border-gray-100 last:border-0">
                        <td className="py-1.5 px-3 text-gray-900">{row.productName || '—'}</td>
                        <td className="py-1.5 px-3 text-right text-gray-900 tabular-nums">
                          {row.quantity}
                        </td>
                        <td className="py-1.5 px-3 text-right text-gray-900 tabular-nums">
                          {row.unitPrice.toFixed(2)}
                        </td>
                        <td className="py-1.5 px-3 text-right text-gray-900 tabular-nums">
                          {row.amount.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {(() => {
                const subtotal = tableRows.reduce((s, r) => s + r.amount, 0);
                const invType = bill.invoice_type ?? '';
                const vatLabel =
                  invType === 'NO_INVOICE'
                    ? '未'
                    : invType === 'DUPLICATE_UNIFORM_INVOICE'
                      ? '已內含'
                      : invType === 'TRIPLE_UNIFORM_INVOICE'
                        ? (subtotal * 0.05).toFixed(2)
                        : '—';
                const vatDisplay =
                  invType === 'TRIPLE_UNIFORM_INVOICE' ? `$${vatLabel}` : vatLabel;
                const total =
                  invType === 'TRIPLE_UNIFORM_INVOICE'
                    ? subtotal + subtotal * 0.05
                    : subtotal;
                return (
                  <div className="mt-4 pt-4 border-t border-gray-200 text-sm">
                    <div className="flex justify-between text-gray-700">
                      <span>合計</span>
                      <span className="tabular-nums">${subtotal.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-gray-700 mt-1">
                      <span>營業稅 5%</span>
                      <span className="tabular-nums">{vatDisplay}</span>
                    </div>
                    <div className="flex justify-between font-medium text-gray-900 mt-2">
                      <span>總計</span>
                      <span className="tabular-nums">${total.toFixed(2)}</span>
                    </div>
                  </div>
                );
              })()}
            </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
