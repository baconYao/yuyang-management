import axios from 'axios';
import type { Bill, BillStatus, BillUpdatePayload, Customer, Contract } from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Future: Add auth token interceptor here
// api.interceptors.request.use((config) => {
//   const token = localStorage.getItem('authToken');
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

export const customerApi = {
  getAll: async (): Promise<Customer[]> => {
    const response = await api.get<Customer[]>('/customers/');
    return response.data;
  },

  getById: async (id: string): Promise<Customer> => {
    const response = await api.get<Customer>(`/customers/${id}`);
    return response.data;
  },

  create: async (customer: Partial<Customer>): Promise<Customer> => {
    const response = await api.post<Customer>('/customers/', customer);
    return response.data;
  },

  update: async (id: string, customer: Partial<Customer>): Promise<Customer> => {
    const response = await api.patch<Customer>(`/customers/${id}`, customer);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/customers/${id}`);
  },
};

export const contractApi = {
  getAll: async (customerId?: string): Promise<Contract[]> => {
    const params = customerId ? { customer_id: customerId } : {};
    const response = await api.get<Contract[]>('/contracts/', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Contract> => {
    const response = await api.get<Contract>(`/contracts/${id}`);
    return response.data;
  },

  create: async (contract: Partial<Contract>): Promise<Contract> => {
    const response = await api.post<Contract>('/contracts/', contract);
    return response.data;
  },

  update: async (id: string, contract: Partial<Contract>): Promise<Contract> => {
    const response = await api.patch<Contract>(`/contracts/${id}`, contract);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/contracts/${id}`);
  },
};

export const billApi = {
  getAll: async (filters?: {
    contract_id?: string;
    customer_id?: string;
    status?: BillStatus | BillStatus[];
  }): Promise<Bill[]> => {
    // Build query string explicitly so backend receives ?status=DRAFT (or status=SENT&status=PROCESSING)
    const searchParams = new URLSearchParams();
    if (filters?.contract_id) searchParams.set('contract_id', filters.contract_id);
    if (filters?.customer_id) searchParams.set('customer_id', filters.customer_id);
    if (filters?.status != null) {
      const statusList = Array.isArray(filters.status) ? filters.status : [filters.status];
      statusList.forEach((s) => searchParams.append('status', s));
    }
    const queryString = searchParams.toString();
    const url = queryString ? `/bills/?${queryString}` : '/bills/';
    const response = await api.get<Bill[]>(url);
    return response.data;
  },

  getByBillNumber: async (billNumber: string): Promise<Bill> => {
    const response = await api.get<Bill>(`/bills/${encodeURIComponent(billNumber)}`);
    return response.data;
  },

  getByContractId: async (contractId: string): Promise<Bill[]> => {
    const response = await api.get<Bill[]>('/bills/', {
      params: { contract_id: contractId },
    });
    return response.data;
  },

  update: async (billNumber: string, payload: BillUpdatePayload): Promise<Bill> => {
    const response = await api.patch<Bill>(
      `/bills/${encodeURIComponent(billNumber)}`,
      payload
    );
    return response.data;
  },
};
