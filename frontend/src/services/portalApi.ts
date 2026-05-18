import axios from 'axios'

const portalApi = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

portalApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('portal_token')
  const tenantId = localStorage.getItem('portal_tenantId')
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (tenantId) config.headers['X-Tenant-ID'] = tenantId
  return config
})

portalApi.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('portal_token')
      localStorage.removeItem('portal_tenantId')
      localStorage.removeItem('portal_user')
      window.location.href = '/portal/login'
    }
    return Promise.reject(err)
  },
)

export const portalAuthApi = {
  resolveTenant: (code: string) =>
    portalApi.get(`/auth/tenant/${code}`),
  login: (email: string, password: string, tenantId: string) =>
    portalApi.post('/auth/login', { email, password }, {
      headers: { 'X-Tenant-ID': tenantId },
    }),
  register: (data: {
    email: string; password: string; first_name: string; last_name: string
    policy_number: string; date_of_birth: string
  }, tenantId: string) =>
    portalApi.post('/customer/register', data, {
      headers: { 'X-Tenant-ID': tenantId },
    }),
  me: () => portalApi.get('/customer/me'),
}

export const portalCustomerApi = {
  me: () => portalApi.get('/customer/me'),
  updateProfile: (data: { first_name?: string; last_name?: string; phone?: string }) =>
    portalApi.put('/customer/me', data),
  changePassword: (current_password: string, new_password: string) =>
    portalApi.put('/customer/me/password', { current_password, new_password }),
  getPolicy: () => portalApi.get('/customer/policy'),
  getCoverage: () => portalApi.get('/customer/coverage'),
  getMembers: () => portalApi.get('/customer/members'),
  getPayments: () => portalApi.get('/customer/payments'),
  getClaims: () => portalApi.get('/customer/claims'),
  fileClaim: (data: {
    claim_type: string; incident_date: string; description: string
    claimed_amount: number; member_id?: string
  }) => portalApi.post('/customer/claims', data),
  getDocuments: () => portalApi.get('/customer/documents'),
}

export default portalApi
