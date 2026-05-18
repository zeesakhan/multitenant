import axios from 'axios'

const buyApi = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

function withTenant(tenantId: string) {
  return { headers: { 'X-Tenant-ID': tenantId } }
}

export interface MemberInput {
  first_name: string
  last_name: string
  date_of_birth: string
  relationship: 'self' | 'spouse' | 'child' | 'parent' | 'sibling' | 'dependent'
  gender: 'M' | 'F' | 'O' | 'U'
}

export const buyApiService = {
  getProducts: (tenantId: string) =>
    buyApi.get('/buy/products', withTenant(tenantId)),

  getQuote: (tenantId: string, plan_id: string, members: MemberInput[]) =>
    buyApi.post('/buy/quote', { plan_id, members }, withTenant(tenantId)),

  submitApplication: (tenantId: string, data: {
    plan_id: string
    members: MemberInput[]
    email: string
    phone?: string
  }) => buyApi.post('/buy/apply', data, withTenant(tenantId)),

  getApplicationStatus: (tenantId: string, applicationId: string) =>
    buyApi.get(`/buy/apply/${applicationId}`, withTenant(tenantId)),
}
