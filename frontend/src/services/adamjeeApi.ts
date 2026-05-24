import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1/uae-buy', headers: { 'Content-Type': 'application/json' } })

export interface UAEMemberInput {
  first_name: string
  last_name: string
  date_of_birth: string
  relationship: 'self' | 'spouse' | 'child' | 'parent' | 'sibling' | 'dependent'
  gender: 'M' | 'F' | 'O' | 'U'
  nationality?: string
  passport_number?: string
  emirates_id?: string
  document_expiry?: string
  visa_type?: string
  place_of_birth?: string
}

export interface ApplyRequest {
  plan_id: string
  members: UAEMemberInput[]
  email: string
  phone: string
  pre_existing_conditions: boolean
  pre_existing_details?: string
  agreed_to_terms: boolean
  agreed_to_regulations: boolean
}

export interface PaymentRequest {
  method: 'card' | 'apple_pay' | 'google_pay' | 'bank_transfer'
  card_last4?: string
  card_brand?: string
  cardholder_name?: string
}

export const adamjeeApi = {
  getInfo: () => api.get('/info'),
  getPlans: () => api.get('/plans'),
  getRegulations: () => api.get('/regulations'),
  ocrDocument: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/ocr', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  getQuote: (plan_id: string, members: UAEMemberInput[]) =>
    api.post('/quote', { plan_id, members }),
  apply: (data: ApplyRequest) => api.post('/apply', data),
  pay: (application_id: string, data: PaymentRequest) =>
    api.post(`/payment/${application_id}`, data),
  getPaymentStatus: (application_id: string) =>
    api.get(`/payment/${application_id}/status`),
}
