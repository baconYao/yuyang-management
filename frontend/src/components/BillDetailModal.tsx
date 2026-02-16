import type { Bill } from '../types';
import { getBillStatusDisplay } from '../utils/billStatusDisplay';

const INVOICE_TYPE_LABELS: Record<string, string> = {
  NO_INVOICE: '不開立發票',
  DUPLICATE_UNIFORM_INVOICE: '二聯式發票',
  TRIPLE_UNIFORM_INVOICE: '三聯式發票',
};

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

function getInvoiceTypeLabel(value: string | null | undefined): string {
  if (!value) return '—';
  return INVOICE_TYPE_LABELS[value] ?? value;
}

export interface BillDetailModalProps {
  bill: Bill | null;
  customerName: string | null;
  onClose: () => void;
}

export default function BillDetailModal({
  bill,
  customerName,
  onClose,
}: BillDetailModalProps) {
  if (!bill) return null;

  const statusDisplay = getBillStatusDisplay(bill);

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
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
            aria-label="關閉"
          >
            <span className="text-2xl leading-none">&times;</span>
          </button>
        </div>

        <div className="px-6 py-4 overflow-y-auto flex-1">
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
        </div>
      </div>
    </div>
  );
}
