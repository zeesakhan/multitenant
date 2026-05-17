export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  user_type: string
  status: string
  tenant_id: string
}

export interface Tenant {
  id: string
  code: string
  name: string
  status: string
  currency: string
  timezone: string
  config: Record<string, unknown>
  created_at: string
}

export interface Coverage {
  id: string
  name: string
  coverage_type: string
  limit_amount: string | null
  copay: string | null
  coinsurance_percent: string | null
}

export interface Plan {
  id: string
  product_id: string
  name: string
  code: string
  plan_type: string
  base_premium: string
  description?: string
  is_active: boolean
  coverages: Coverage[]
  created_at: string
  updated_at: string
}

export interface Product {
  id: string
  name: string
  code: string
  status: string
  description?: string
  plans: Plan[]
  created_at: string
  updated_at: string
}

export interface Application {
  id: string
  status: string
  customer_name: string
  customer_email: string
  product_id: string
  plan_id: string
  member_count: number
  tenant_id: string
  created_at: string
}

export interface Member {
  id: string
  application_id: string
  first_name: string
  last_name: string
  date_of_birth: string
  relationship: string
  gender: string
  status: string
  email?: string | null
  phone?: string | null
  national_id?: string | null
  created_at: string
  updated_at: string
}

export interface ApplicationItem {
  id: string
  coverage_id: string
  coverage?: { id: string; name: string; coverage_type: string } | null
  premium: string
  status: string
  notes?: string | null
}

export interface Policy {
  id: string
  policy_number: string
  application_id: string
  product_id: string
  plan_id: string
  customer_name: string
  customer_email: string
  member_count: number
  total_premium: string
  status: string
  effective_date: string
  expiry_date: string
  issued_at?: string | null
  created_at: string
}

export interface Quote {
  id: string
  quote_number: string
  product_id: string
  plan_id: string
  customer_name: string
  customer_email: string
  total_premium: string
  status: string
  valid_until: string
  breakdown?: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface Payment {
  id: string
  payment_number: string
  policy_id: string
  amount: string
  status: string
  method: string
  reference?: string | null
  notes?: string | null
  paid_at: string
  created_at: string
}

export interface Claim {
  id: string
  claim_number: string
  policy_id: string
  member_id?: string | null
  claim_type: string
  status: string
  incident_date: string
  description: string
  claimed_amount: string
  approved_amount?: string | null
  rejection_reason?: string | null
  reviewed_at?: string | null
  paid_at?: string | null
  created_at: string
  updated_at: string
}

export interface ReportSummary {
  active_policies: number
  expiring_soon_30d: number
  pending_applications: number
  open_claims: number
  monthly_premium_due: number
  collected_this_month: number
  claims_paid_this_month: number
}

export interface DashboardStats {
  policies: {
    total: number
    active: number
    monthly_premium: number
  }
  applications: {
    total: number
    by_status: Record<string, number>
  }
  payments: {
    total: number
    total_collected: number
  }
  users: {
    total: number
  }
  recent_applications: {
    id: string
    application_number: string
    customer_name: string
    status: string
    created_at: string
  }[]
  recent_payments: {
    id: string
    payment_number: string
    policy_id: string
    amount: number
    method: string
    paid_at: string
  }[]
}

export interface AuthState {
  user: User | null
  token: string | null
  tenantId: string | null
  isAuthenticated: boolean
}

export interface APIResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}
