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
  invoice_type: string | null;
  terminated_at: string | null;
  termination_reason: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ContractWithCustomer extends Contract {
  customer_name?: string | null;
}

export type BillStatus =
  | 'DRAFT'
  | 'SENT'
  | 'PROCESSING'
  | 'PAID'
  | 'OVERDUE'
  | 'CANCELLED';

/** One line item returned with a bill (GET /bills, GET /bills/{id}). */
export interface BillItem {
  id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  amount: number;
  sort_order: number;
}

export interface Bill {
  bill_number: string;
  customer_id: string;
  contract_id: string;
  amount: number;
  tax_amount: number;
  monthly_rent: number;
  invoice_type: string | null;
  status: BillStatus;
  notes: string;
  previous_bill_number: string | null;
  created_at: string | null;
  updated_at: string | null;
  due_date: string | null;
  sent_at: string | null;
  paid_at: string | null;
  items?: BillItem[];
}

/** One line item in PATCH /bills/{bill_number} (items array). */
export interface BillItemUpdatePayload {
  id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  amount: number;
  sort_order: number;
}

/** Payload for PATCH /bills/{bill_number}. status is required. */
export interface BillUpdatePayload {
  status: BillStatus;
  notes?: string | null;
  tax_amount?: number | null;
  monthly_rent?: number | null;
  invoice_type?: string | null;
  due_date?: string | null;
  sent_at?: string | null;
  paid_at?: string | null;
  items?: BillItemUpdatePayload[];
}
