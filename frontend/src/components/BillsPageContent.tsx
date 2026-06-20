import { useCallback, useEffect, useMemo, useState } from 'react';
import { billApi, customerApi } from '../services/api';
import type { Bill, BillStatus } from '../types';
import BillDetailModal from './BillDetailModal';
import { getBillStatusDisplay } from '../utils/billStatusDisplay';

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

export interface BillsPageContentProps {
  statusFilter: BillStatus | BillStatus[];
  title: string;
  enableUpcomingDaysFilter?: boolean;
}

const UPCOMING_DAYS_OPTIONS = [7, 14, 21, 30, 45, 60, 90, 120] as const;

export default function BillsPageContent({
  statusFilter,
  title,
  enableUpcomingDaysFilter = false,
}: BillsPageContentProps) {
  const [bills, setBills] = useState<Bill[]>([]);
  const [customerNameMap, setCustomerNameMap] = useState<Map<string, string | null>>(new Map());
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [upcomingDays, setUpcomingDays] = useState<number>(45);
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);

  const statusList = useMemo(
    () => (Array.isArray(statusFilter) ? statusFilter : [statusFilter]),
    [statusFilter]
  );

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [billsData, customersData] = await Promise.all([
        billApi.getAll({
          status: statusList,
          within_days: enableUpcomingDaysFilter ? upcomingDays : undefined,
        }),
        customerApi.getAll(),
      ]);
      setBills(billsData);
      const map = new Map<string, string | null>();
      customersData.forEach((c) => map.set(c.id, c.customer_name));
      setCustomerNameMap(map);
    } catch (e) {
      console.error('Failed to fetch bills:', e);
      setBills([]);
    } finally {
      setLoading(false);
    }
  }, [enableUpcomingDaysFilter, statusList, upcomingDays]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredBills = useMemo(() => {
    if (!searchTerm.trim()) return bills;
    const q = searchTerm.toLowerCase();
    return bills.filter((bill) => {
      const name = customerNameMap.get(bill.customer_id) ?? '';
      return (
        (typeof name === 'string' && name.toLowerCase().includes(q)) ||
        bill.bill_number.toLowerCase().includes(q)
      );
    });
  }, [bills, searchTerm, customerNameMap]);

  const getCustomerName = (customerId: string) => customerNameMap.get(customerId) ?? '—';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">{title}</h1>

      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col gap-3 md:flex-row">
          <input
            type="text"
            placeholder="搜尋客戶名稱或帳單編號..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {enableUpcomingDaysFilter && (
            <div className="w-full md:w-56">
              <label className="sr-only" htmlFor="bill-date-range-filter">
                帳單日期範圍
              </label>
              <select
                id="bill-date-range-filter"
                value={upcomingDays}
                onChange={(e) => setUpcomingDays(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="帳單日期範圍"
              >
                {UPCOMING_DAYS_OPTIONS.map((day) => (
                  <option key={day} value={day}>
                    {`${day} 天內`}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  帳單編號
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  客戶名稱
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  帳單起始日期
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  總金額
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  帳單狀態
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredBills.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    沒有找到帳單資料
                  </td>
                </tr>
              ) : (
                filteredBills.map((bill) => {
                  const statusDisplay = getBillStatusDisplay(bill);
                  return (
                    <tr
                      key={bill.bill_number}
                      onClick={() => setSelectedBill(bill)}
                      className="hover:bg-gray-100 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {bill.bill_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {getCustomerName(bill.customer_id)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {formatDate(bill.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        ${bill.amount}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 text-xs font-medium rounded ${statusDisplay.className}`}
                        >
                          {statusDisplay.label}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <BillDetailModal
        bill={selectedBill}
        customerName={selectedBill ? getCustomerName(selectedBill.customer_id) : null}
        onClose={() => setSelectedBill(null)}
        onBillUpdated={(updated) => {
          setBills((prev) =>
            prev.map((b) => (b.bill_number === updated.bill_number ? updated : b))
          );
          setSelectedBill(updated);
        }}
      />
    </div>
  );
}
