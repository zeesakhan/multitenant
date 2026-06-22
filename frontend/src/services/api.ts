import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  const tenantId = localStorage.getItem('tenantId')
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (tenantId) config.headers['X-Tenant-ID'] = tenantId
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('tenantId')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export default api

export const authApi = {
  login: (email: string, password: string) => {
    const tenantId = localStorage.getItem('tenantId')
    return api.post('/auth/login', { email, password }, {
      headers: tenantId ? { 'X-Tenant-ID': tenantId } : {},
    })
  },
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
  forgotPassword: (email: string) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token: string, new_password: string) =>
    api.post('/auth/reset-password', { token, new_password }),
}

export const tenantsApi = {
  list: (page = 1) => api.get(`/tenants?page=${page}`),
  get: (id: string) => api.get(`/tenants/${id}`),
  create: (data: unknown) => api.post('/tenants', data),
  update: (id: string, data: unknown) => api.put(`/tenants/${id}`, data),
}

export const usersApi = {
  list: (page = 1) => api.get(`/users?page=${page}`),
  get: (id: string) => api.get(`/users/${id}`),
  create: (data: unknown) => api.post('/users', data),
  update: (id: string, data: unknown) => api.put(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
}

export const productsApi = {
  list: (page = 1) => api.get(`/products?page=${page}`),
  get: (id: string) => api.get(`/products/${id}`),
  create: (data: unknown) => api.post('/products', data),
  update: (id: string, data: unknown) => api.put(`/products/${id}`, data),
}

export const plansApi = {
  list: (productId: string, page = 1) => api.get(`/products/${productId}/plans?page=${page}`),
  create: (productId: string, data: unknown) => api.post(`/products/${productId}/plans`, data),
  update: (productId: string, planId: string, data: unknown) => api.put(`/products/${productId}/plans/${planId}`, data),
  addCoverage: (productId: string, planId: string, data: unknown) =>
    api.post(`/products/${productId}/plans/${planId}/coverages`, data),
}

export const quotationsApi = {
  list: (page = 1) => api.get(`/quotations?page=${page}`),
  get: (id: string) => api.get(`/quotations/${id}`),
  create: (data: unknown) => api.post('/quotations', data),
  send: (id: string, recipientEmail?: string) =>
    api.post(`/quotations/${id}/send`, { recipient_email: recipientEmail ?? null }),
}

export const applicationsApi = {
  list: (page = 1, params?: { status?: string; aml_status?: string; govt_check_status?: string }) => {
    const q = new URLSearchParams({ page: String(page) })
    if (params?.status) q.set('status_filter', params.status)
    if (params?.aml_status) q.set('aml_status', params.aml_status)
    if (params?.govt_check_status) q.set('govt_check_status', params.govt_check_status)
    return api.get(`/applications?${q}`)
  },
  get: (id: string) => api.get(`/applications/${id}`),
  create: (data: unknown) => api.post('/applications', data),
  update: (id: string, data: unknown) => api.put(`/applications/${id}`, data),
  submit: (id: string) => api.post(`/applications/${id}/submit`, {}),
  approve: (id: string) => api.post(`/applications/${id}/approve`, {}),
  reject: (id: string, reason: string) =>
    api.post(`/applications/${id}/reject`, null, { params: { reason } }),
  recalculate: (id: string) => api.post(`/applications/${id}/recalculate`, {}),
  listItems: (id: string) => api.get(`/applications/${id}/items`),
  addItem: (id: string, data: unknown) => api.post(`/applications/${id}/items`, data),
  removeItem: (appId: string, itemId: string) => api.delete(`/applications/${appId}/items/${itemId}`),
  issue: (id: string) => api.post(`/applications/${id}/issue`, {}),
  // Loadings
  listLoadings: (id: string) => api.get(`/applications/${id}/loadings`),
  addLoading: (id: string, data: unknown) => api.post(`/applications/${id}/loadings`, data),
  removeLoading: (id: string, loadingId: string) => api.delete(`/applications/${id}/loadings/${loadingId}`),
  // Remarks
  listRemarks: (id: string) => api.get(`/applications/${id}/remarks`),
  addRemark: (id: string, text: string) => api.post(`/applications/${id}/remarks`, { text }),
}

export const membersApi = {
  listAll: (page = 1) => api.get(`/members?page=${page}`),
  list: (applicationId: string) => api.get(`/applications/${applicationId}/members`),
  add: (applicationId: string, data: unknown) => api.post(`/applications/${applicationId}/members`, data),
  update: (applicationId: string, memberId: string, data: unknown) =>
    api.put(`/applications/${applicationId}/members/${memberId}`, data),
  remove: (applicationId: string, memberId: string) =>
    api.delete(`/applications/${applicationId}/members/${memberId}`),
}

export const policiesApi = {
  list: (page = 1, params?: { status?: string; aml_status?: string }) => {
    const q = new URLSearchParams({ page: String(page) })
    if (params?.status) q.set('status', params.status)
    if (params?.aml_status) q.set('aml_status', params.aml_status)
    return api.get(`/policies?${q}`)
  },
  get: (id: string) => api.get(`/policies/${id}`),
  renew: (id: string) => api.post(`/policies/${id}/renew`, {}),
  generateDocument: (id: string) => api.post(`/policies/${id}/generate-document`, {}),
  listDocuments: (id: string) => api.get(`/policies/${id}/documents`),
  downloadDocumentUrl: (policyId: string, docId: string) => `/api/v1/policies/${policyId}/documents/${docId}/download`,
  // PDF generation
  generateSchedule: (id: string) => api.post(`/documents/policies/${id}/generate-schedule`, {}, { responseType: 'blob' }),
  generateCreditNote: (id: string) => api.post(`/documents/policies/${id}/generate-credit-note`, {}, { responseType: 'blob' }),
  generateTaxInvoice: (id: string) => api.post(`/documents/policies/${id}/generate-tax-invoice`, {}, { responseType: 'blob' }),
  generateReceipt: (id: string) => api.post(`/documents/policies/${id}/generate-receipt`, {}, { responseType: 'blob' }),
}

export const documentsApi = {
  generateMaf: (applicationId: string) => api.post(`/documents/applications/${applicationId}/generate-maf`, {}, { responseType: 'blob' }),
  generateKyc: (applicationId: string) => api.post(`/documents/applications/${applicationId}/generate-kyc`, {}, { responseType: 'blob' }),
  generateTob: (applicationId: string) => api.post(`/documents/applications/${applicationId}/generate-tob`, {}, { responseType: 'blob' }),
}

export const paymentsApi = {
  listByPolicy: (policyId: string) => api.get(`/policies/${policyId}/payments`),
  record: (policyId: string, data: unknown) => api.post(`/policies/${policyId}/payments`, data),
  listAll: (page = 1) => api.get(`/payments?page=${page}`),
}

export const dashboardApi = {
  stats: () => api.get('/dashboard/stats'),
}

export const claimsApi = {
  list: (page = 1) => api.get(`/claims?page=${page}`),
  get: (id: string) => api.get(`/claims/${id}`),
  create: (data: unknown) => api.post('/claims', data),
  update: (id: string, data: unknown) => api.put(`/claims/${id}`, data),
  startReview: (id: string) => api.post(`/claims/${id}/review`, {}),
  approve: (id: string, data: unknown) => api.post(`/claims/${id}/approve`, data),
  reject: (id: string, reason: string) => api.post(`/claims/${id}/reject`, { reason }),
  pay: (id: string) => api.post(`/claims/${id}/pay`, {}),
}

export const reportsApi = {
  summary: () => api.get('/reports/summary'),
  applications: (months = 6) => api.get(`/reports/applications?months=${months}`),
  premium: (months = 6) => api.get(`/reports/premium?months=${months}`),
  claims: (months = 6) => api.get(`/reports/claims?months=${months}`),
}

export const amlApi = {
  listAlerts: () => api.get('/aml/alerts'),
  listRecords: (applicationId: string) => api.get(`/aml/records/${applicationId}`),
  clearHold: (applicationId: string, notes: string) => api.post(`/aml/${applicationId}/clear`, { notes }),
  placeHold: (applicationId: string, notes: string) => api.post(`/aml/${applicationId}/hold`, { notes }),
  // STR
  listStr: () => api.get('/aml/str'),
  createStr: (data: unknown) => api.post('/aml/str', data),
  approveStr: (strId: string, notes: string) => api.post(`/aml/str/${strId}/approve`, { notes }),
  fileStr: (strId: string) => api.post(`/aml/str/${strId}/file`, {}),
}

export const govtChecksApi = {
  list: (params?: { status_filter?: string; check_type?: string }) =>
    api.get('/govt-checks', { params }),
  listForApplication: (applicationId: string) =>
    api.get(`/govt-checks/applications/${applicationId}`),
  verifyIcp: (applicationId: string, data: unknown) =>
    api.post(`/govt-checks/applications/${applicationId}/verify-icp`, data),
  verifySanctions: (applicationId: string, data: unknown) =>
    api.post(`/govt-checks/applications/${applicationId}/verify-sanctions`, data),
  override: (recordId: string, justification: string) =>
    api.post(`/govt-checks/${recordId}/override`, { justification }),
  bulkRetry: (recordIds: string[]) => api.post('/govt-checks/bulk-retry', recordIds),
}

export const notificationsApi = {
  list: (unreadOnly = false) => api.get(`/notifications?unread_only=${unreadOnly}`),
  markRead: (id: string) => api.post(`/notifications/${id}/read`, {}),
  markAllRead: () => api.post('/notifications/read-all', {}),
}

export const healthApi = {
  check: () => axios.get('/health'),
}
