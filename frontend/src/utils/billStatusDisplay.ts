import type { Bill, BillStatus } from '../types';

export const BILL_STATUS_OPTIONS: { value: BillStatus; label: string; className: string }[] = [
  { value: 'DRAFT', label: '草稿', className: 'bg-gray-100 text-gray-800' },
  { value: 'SENT', label: '已寄出', className: 'bg-blue-100 text-blue-800' },
  { value: 'PROCESSING', label: '對帳中', className: 'bg-amber-100 text-amber-800' },
  { value: 'PAID', label: '已結案', className: 'bg-green-100 text-green-800' },
  { value: 'OVERDUE', label: '已逾期', className: 'bg-red-100 text-red-800' },
  { value: 'CANCELLED', label: '已作廢', className: 'bg-gray-100 text-gray-500' },
];

export function getBillStatusDisplay(bill: Pick<Bill, 'status'>): { label: string; className: string } {
  const opt = BILL_STATUS_OPTIONS.find((o) => o.value === bill.status);
  return opt ?? { label: bill.status, className: 'bg-gray-100 text-gray-800' };
}
