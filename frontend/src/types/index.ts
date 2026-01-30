export enum CustomerType {
  REAL_ESTATE = "REAL_ESTATE",
  EDUCATION = "EDUCATION",
  ELEMENTARY_ATTACHED_KINDERGARTEN = "ELEMENTARY_ATTACHED_KINDERGARTEN",
  COMPANY = "COMPANY",
  INSURANCE = "INSURANCE",
  OTHER = "OTHER",
}

export type CustomerStatus = 'ACTIVE' | 'TERMINATED';

export interface Customer {
  id: string;
  customer_name: string | null;
  invoice_title: string | null;
  invoice_number: string | null;
  contact_phone: string | null;
  messaging_app_line: string | null;
  address: string | null;
  primary_contact: string | null;
  customer_type: CustomerType | null;
  status?: CustomerStatus | null;
}

export interface Contract {
  id: string;
  customer_id: string;
  product_name: string;
  start_date: string;
  end_date: string;
  monthly_rent: number;
  billing_interval: string;
  notes: string | null;
  status: string;
  contract_number: string | null;
  signed_date: string | null;
  payment_method: string | null;
  next_billing_date: string | null;
  terminated_at: string | null;
  termination_reason: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ContractWithCustomer extends Contract {
  customer_name?: string | null;
}
