import { useEffect, useState } from 'react';
import { customerApi, contractApi } from '../services/api';
import { getCustomerTypeLabel } from '../utils/customerTypeLabels';

export default function Dashboard() {
  const [totalCustomers, setTotalCustomers] = useState(0);
  const [totalContracts, setTotalContracts] = useState(0);
  const [customersByType, setCustomersByType] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [customers, contracts] = await Promise.all([
          customerApi.getAll(),
          contractApi.getAll(),
        ]);

        setTotalCustomers(customers.length);
        setTotalContracts(contracts.length);

        // Count customers by type
        const typeCount: Record<string, number> = {};
        customers.forEach((customer) => {
          const label = customer.customer_type
            ? getCustomerTypeLabel(customer.customer_type)
            : '未分類';
          typeCount[label] = (typeCount[label] || 0) + 1;
        });
        setCustomersByType(typeCount);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-8">儀表板</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {/* Total Customers */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">客戶總數量</p>
              <p className="text-3xl font-bold text-gray-800 mt-2">{totalCustomers}</p>
            </div>
            <div className="bg-blue-100 rounded-full p-3">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Total Contracts */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm font-medium">合約總數量</p>
              <p className="text-3xl font-bold text-gray-800 mt-2">{totalContracts}</p>
            </div>
            <div className="bg-green-100 rounded-full p-3">
              <svg
                className="w-8 h-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Customer Type Statistics */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">客戶類型統計</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Object.entries(customersByType).map(([type, count]) => (
            <div key={type} className="border rounded-lg p-4">
              <p className="text-gray-600 text-sm font-medium">{type}</p>
              <p className="text-2xl font-bold text-gray-800 mt-2">{count}</p>
            </div>
          ))}
          {Object.keys(customersByType).length === 0 && (
            <p className="text-gray-500 col-span-full text-center py-4">暫無數據</p>
          )}
        </div>
      </div>
    </div>
  );
}
