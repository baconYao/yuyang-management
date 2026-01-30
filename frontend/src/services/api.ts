import axios from 'axios';
import type { Customer, Contract } from '../types';

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
