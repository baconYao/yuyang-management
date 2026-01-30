import { useEffect, useState, useMemo } from 'react';
import { contractApi, customerApi } from '../services/api';
import type { ContractWithCustomer } from '../types';
import ContractDetailModal from '../components/ContractDetailModal';
import { getContractStatusDisplay } from '../utils/contractStatusDisplay';

const ITEMS_PER_PAGE = 15;
const DAYS_NEAR_END = 60;

type ContractStatusFilter = 'ACTIVE' | 'OTHER' | 'ALL';

function getDaysUntilEnd(contract: ContractWithCustomer): number | null {
  if (!contract.end_date) return null;
  const end = new Date(contract.end_date);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);
  return Math.ceil((end.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

function isExpiringSoon(contract: ContractWithCustomer): boolean {
  if (contract.status !== 'ACTIVE') return false;
  const days = getDaysUntilEnd(contract);
  return days !== null && days >= 0 && days <= DAYS_NEAR_END;
}

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

export default function Contracts() {
  const [contracts, setContracts] = useState<ContractWithCustomer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<ContractStatusFilter>('ACTIVE');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedContract, setSelectedContract] = useState<ContractWithCustomer | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [contractsData, customersData] = await Promise.all([
          contractApi.getAll(),
          customerApi.getAll(),
        ]);

        const customerMap = new Map<string, string | null>();
        customersData.forEach((customer) => {
          customerMap.set(customer.id, customer.customer_name);
        });

        const contractsWithCustomers: ContractWithCustomer[] = contractsData.map((contract) => ({
          ...contract,
          customer_name: customerMap.get(contract.customer_id) || null,
        }));

        setContracts(contractsWithCustomers);
      } catch (error) {
        console.error('Failed to fetch contracts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredContracts = useMemo(() => {
    let result = contracts;

    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      result = result.filter(
        (contract) =>
          contract.customer_name?.toLowerCase().includes(searchLower) ||
          contract.contract_number?.toLowerCase().includes(searchLower) ||
          contract.product_name?.toLowerCase().includes(searchLower)
      );
    }

    if (statusFilter === 'ACTIVE') {
      result = result.filter((c) => c.status === 'ACTIVE');
      result = [...result].sort((a, b) => {
        const aSoon = isExpiringSoon(a) ? 0 : 1;
        const bSoon = isExpiringSoon(b) ? 0 : 1;
        if (aSoon !== bSoon) return aSoon - bSoon;
        const aEnd = a.end_date ? new Date(a.end_date).getTime() : Infinity;
        const bEnd = b.end_date ? new Date(b.end_date).getTime() : Infinity;
        return aEnd - bEnd;
      });
    } else if (statusFilter === 'OTHER') {
      result = result.filter((c) => c.status !== 'ACTIVE');
    }

    return result;
  }, [contracts, searchTerm, statusFilter]);

  const totalPages = Math.ceil(filteredContracts.length / ITEMS_PER_PAGE);
  const paginatedContracts = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredContracts.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredContracts, currentPage]);

  const handlePageChange = (page: number) => setCurrentPage(page);

  const handleRowClick = (contract: ContractWithCustomer) => {
    setSelectedContract(contract);
  };

  const handleContractUpdated = (updated: ContractWithCustomer) => {
    setContracts((prev) =>
      prev.map((c) => (c.id === updated.id ? updated : c))
    );
    setSelectedContract(updated);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">合約管理</h1>

      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="搜尋客戶名稱、合約編號或產品名稱..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as ContractStatusFilter);
                setCurrentPage(1);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ACTIVE">生效</option>
              <option value="OTHER">其他</option>
              <option value="ALL">全部</option>
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  合約 ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  客戶名稱
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  起始日期
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  結束日期
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  合約狀態
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedContracts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    沒有找到合約資料
                  </td>
                </tr>
              ) : (
                paginatedContracts.map((contract) => {
                  const statusDisplay = getContractStatusDisplay(contract);
                  return (
                    <tr
                      key={contract.id}
                      onClick={() => handleRowClick(contract)}
                      className="hover:bg-gray-100 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {contract.contract_number || contract.id.substring(0, 8)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {contract.customer_name || '未知客戶'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {formatDate(contract.start_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {formatDate(contract.end_date)}
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

        {totalPages > 1 && (
          <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-t border-gray-200">
            <div className="text-sm text-gray-700">
              顯示第 {(currentPage - 1) * ITEMS_PER_PAGE + 1} 到{' '}
              {Math.min(currentPage * ITEMS_PER_PAGE, filteredContracts.length)} 筆，共{' '}
              {filteredContracts.length} 筆
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                上一頁
              </button>
              <span className="px-4 py-2 text-gray-700">
                第 {currentPage} / {totalPages} 頁
              </span>
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                下一頁
              </button>
            </div>
          </div>
        )}
      </div>

      <ContractDetailModal
        contract={selectedContract}
        onClose={() => setSelectedContract(null)}
        onContractUpdated={handleContractUpdated}
      />
    </div>
  );
}
