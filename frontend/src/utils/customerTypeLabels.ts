import { CustomerType } from '../types';

export const customerTypeLabels: Record<CustomerType, string> = {
  [CustomerType.REAL_ESTATE]: '不動產',
  [CustomerType.EDUCATION]: '教育',
  [CustomerType.ELEMENTARY_ATTACHED_KINDERGARTEN]: '國小附設幼兒園',
  [CustomerType.COMPANY]: '公司',
  [CustomerType.INSURANCE]: '保險',
  [CustomerType.OTHER]: '其他',
};

export const getCustomerTypeLabel = (type: CustomerType | null): string => {
  if (!type) return '未分類';
  return customerTypeLabels[type] || type;
};
