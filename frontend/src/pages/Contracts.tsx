import { useEffect, useState, useMemo } from 'react';
import { contractApi, customerApi } from '../services/api';
import type { ContractWithCustomer } from '../types';

const ITEMS_PER_PAGE = 15;

export default function Contracts() {
  const [contracts, setContracts] = useState<ContractWithCustomer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [contractsData, customersData] = await Promise.all([
          contractApi.getAll(),
          customerApi.getAll(),
        ]);

        // Create mapping from customer ID to customer name
        const customerMap = new Map<string, string | null>();
        customersData.forEach((customer) => {
          customerMap.set(customer.id, customer.customer_name);
        });

        // Merge contract and customer information
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

  // Search filter logic
  const filteredContracts = useMemo(() => {
    if (!searchTerm) {
      return contracts;
    }

    const searchLower = searchTerm.toLowerCase();
    return contracts.filter(
      (contract) =>
        contract.customer_name?.toLowerCase().includes(searchLower) ||
        contract.contract_number?.toLowerCase().includes(searchLower) ||
        contract.product_name?.toLowerCase().includes(searchLower)
    );
  }, [contracts, searchTerm]);

  // Pagination
  const totalPages = Math.ceil(filteredContracts.length / ITEMS_PER_PAGE);
  const paginatedContracts = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredContracts.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredContracts, currentPage]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
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

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
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

      {/* Table */}
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
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedContracts.length === 0 ? (
                <tr>
                  <td colSpan={2} className="px-6 py-4 text-center text-gray-500">
                    沒有找到合約資料
                  </td>
                </tr>
              ) : (
                paginatedContracts.map((contract) => (
                  <tr key={contract.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {contract.contract_number || contract.id.substring(0, 8)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {contract.customer_name || '未知客戶'}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
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
    </div>
  );
}
