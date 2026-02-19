import { useEffect, useState, useMemo } from 'react';
import { customerApi, contractApi } from '../services/api';
import type { Customer, Contract, ContractWithCustomer } from '../types';
import type { CustomerStatus } from '../types';
import { CustomerType } from '../types';
import ContractDetailModal from '../components/ContractDetailModal';
import AddCustomerModal from '../components/AddCustomerModal';
import { getContractStatusDisplay } from '../utils/contractStatusDisplay';
import { getCustomerTypeLabel } from '../utils/customerTypeLabels';

const ITEMS_PER_PAGE = 15;

function formatContactInfo(customer: Customer): string {
  const parts: string[] = [];
  if (customer.contact_phone) parts.push(`電話：${customer.contact_phone}`);
  if (customer.messaging_app_line) parts.push(`LINE：${customer.messaging_app_line}`);
  return parts.length ? parts.join(' / ') : '—';
}

function getStatusLabel(status: Customer['status']): string {
  if (status === 'TERMINATED') return '無合作';
  return '合作中';
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' });
  } catch {
    return iso;
  }
}

export default function Customers() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortType, setSortType] = useState<CustomerType | 'ALL'>('ALL');
  const [statusFilter, setStatusFilter] = useState<CustomerStatus>('ACTIVE');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [modalContracts, setModalContracts] = useState<Contract[]>([]);
  const [modalContractsLoading, setModalContractsLoading] = useState(false);
  const [selectedContractInModal, setSelectedContractInModal] =
    useState<ContractWithCustomer | null>(null);
  const [addCustomerModalOpen, setAddCustomerModalOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const customersData = await customerApi.getAll();
        setCustomers(customersData);
      } catch (error) {
        console.error('Failed to fetch customers:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (!selectedCustomer) {
      setModalContracts([]);
      return;
    }
    let cancelled = false;
    setModalContractsLoading(true);
    contractApi
      .getAll(selectedCustomer.id)
      .then((data) => {
        if (!cancelled) setModalContracts(data);
      })
      .finally(() => {
        if (!cancelled) setModalContractsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedCustomer]);

  const filteredAndSortedCustomers = useMemo(() => {
    let filtered = customers;

    if (searchTerm) {
      filtered = filtered.filter(
        (customer) =>
          customer.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          customer.invoice_title?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (sortType !== 'ALL') {
      filtered = filtered.filter((customer) => customer.customer_type === sortType);
    }

    filtered = filtered.filter(
      (customer) => (customer.status ?? 'ACTIVE') === statusFilter
    );

    return filtered;
  }, [customers, searchTerm, sortType, statusFilter]);

  const totalPages = Math.ceil(filteredAndSortedCustomers.length / ITEMS_PER_PAGE);
  const paginatedCustomers = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredAndSortedCustomers.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredAndSortedCustomers, currentPage]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleRowClick = (customer: Customer) => {
    setSelectedCustomer(customer);
  };

  const closeModal = () => {
    setSelectedCustomer(null);
    setSelectedContractInModal(null);
  };

  const handleContractRowClick = (e: React.MouseEvent, contract: Contract) => {
    e.stopPropagation();
    setSelectedContractInModal({
      ...contract,
      customer_name: selectedCustomer?.customer_name ?? null,
    });
  };

  const handleContractUpdated = (updated: ContractWithCustomer) => {
    setModalContracts((prev) =>
      prev.map((c) => (c.id === updated.id ? updated : c))
    );
    setSelectedContractInModal(updated);
  };

  const handleCustomerCreated = (customer: Customer) => {
    setCustomers((prev) => [customer, ...prev]);
    setAddCustomerModalOpen(false);
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
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-800">客戶管理</h1>
        <button
          type="button"
          onClick={() => setAddCustomerModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          新增客戶
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="搜尋客戶名稱或發票抬頭..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="md:w-64">
            <select
              value={sortType}
              onChange={(e) => {
                setSortType(e.target.value as CustomerType | 'ALL');
                setCurrentPage(1);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">所有類型</option>
              {Object.values(CustomerType).map((type) => (
                <option key={type} value={type}>
                  {getCustomerTypeLabel(type)}
                </option>
              ))}
            </select>
          </div>
          <div className="md:w-64">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as CustomerStatus);
                setCurrentPage(1);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ACTIVE">合作中</option>
              <option value="TERMINATED">無合作</option>
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
                  客戶名稱
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  聯絡人
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  聯絡資訊
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  合作狀態
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedCustomers.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                    沒有找到客戶資料
                  </td>
                </tr>
              ) : (
                paginatedCustomers.map((customer) => {
                  const status = customer.status ?? 'ACTIVE';
                  const isTerminated = status === 'TERMINATED';
                  return (
                    <tr
                      key={customer.id}
                      onClick={() => handleRowClick(customer)}
                      className="hover:bg-gray-100 cursor-pointer transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {customer.customer_name || '未命名'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {customer.primary_contact || '—'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700 max-w-xs truncate">
                        {formatContactInfo(customer)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded ${
                            isTerminated
                              ? 'bg-gray-200 text-gray-700'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {getStatusLabel(status)}
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
              {Math.min(currentPage * ITEMS_PER_PAGE, filteredAndSortedCustomers.length)} 筆，共{' '}
              {filteredAndSortedCustomers.length} 筆
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

      {/* Customer detail modal */}
      {selectedCustomer && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="customer-modal-title"
        >
          <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 id="customer-modal-title" className="text-xl font-bold text-gray-800">
                客戶詳情
              </h2>
              <button
                type="button"
                onClick={closeModal}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
                aria-label="關閉"
              >
                <span className="text-2xl leading-none">&times;</span>
              </button>
            </div>

            <div className="px-6 py-4 overflow-y-auto flex-1">
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-gray-500 font-medium">客戶名稱</dt>
                  <dd className="text-gray-900">{selectedCustomer.customer_name || '—'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 font-medium">發票抬頭</dt>
                  <dd className="text-gray-900">{selectedCustomer.invoice_title || '—'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 font-medium">統一編號</dt>
                  <dd className="text-gray-900">{selectedCustomer.invoice_number || '—'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 font-medium">聯絡人</dt>
                  <dd className="text-gray-900">{selectedCustomer.primary_contact || '—'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 font-medium">聯絡電話</dt>
                  <dd className="text-gray-900">{selectedCustomer.contact_phone || '—'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 font-medium">LINE</dt>
                  <dd className="text-gray-900">{selectedCustomer.messaging_app_line || '—'}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-gray-500 font-medium">地址</dt>
                  <dd className="text-gray-900">{selectedCustomer.address || '—'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 font-medium">客戶類型</dt>
                  <dd className="text-gray-900">
                    {getCustomerTypeLabel(selectedCustomer.customer_type)}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 font-medium">合作狀態</dt>
                  <dd>
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded ${
                        (selectedCustomer.status ?? 'ACTIVE') === 'TERMINATED'
                          ? 'bg-gray-200 text-gray-700'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {getStatusLabel(selectedCustomer.status)}
                    </span>
                  </dd>
                </div>
              </dl>

              <h3 className="text-lg font-semibold text-gray-800 mt-6 mb-3">合約列表</h3>
              {modalContractsLoading ? (
                <div className="text-gray-500 py-4">載入合約中...</div>
              ) : modalContracts.length === 0 ? (
                <div className="text-gray-500 py-4">此客戶尚無合約</div>
              ) : (
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          合約編號
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          產品名稱
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          開始日期
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          結束日期
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          月租
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          狀態
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {modalContracts.map((contract) => {
                        const statusDisplay = getContractStatusDisplay(contract);
                        return (
                          <tr
                            key={contract.id}
                            onClick={(e) => handleContractRowClick(e, contract)}
                            className="hover:bg-gray-100 cursor-pointer transition-colors"
                          >
                            <td className="px-4 py-2 text-sm text-gray-900">
                              {contract.contract_number || '—'}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-900">
                              {contract.product_name}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-700 whitespace-nowrap">
                              {formatDate(contract.start_date)}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-700 whitespace-nowrap">
                              {formatDate(contract.end_date)}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-700">
                              {contract.monthly_rent != null ? `$${contract.monthly_rent}` : '—'}
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
            </div>
          </div>
        </div>
      )}

      <ContractDetailModal
        contract={selectedContractInModal}
        onClose={() => setSelectedContractInModal(null)}
        onContractUpdated={handleContractUpdated}
      />

      <AddCustomerModal
        open={addCustomerModalOpen}
        onClose={() => setAddCustomerModalOpen(false)}
        onSuccess={handleCustomerCreated}
      />
    </div>
  );
}
