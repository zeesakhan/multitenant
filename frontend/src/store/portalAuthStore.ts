import { useEffect, useState } from 'react'

export interface PortalUser {
  id: string
  email: string
  first_name: string
  last_name: string
  phone?: string
  user_type: string
  policy_id?: string
}

let _user: PortalUser | null = (() => {
  try { return JSON.parse(localStorage.getItem('portal_user') ?? 'null') } catch { return null }
})()
let _token: string | null = localStorage.getItem('portal_token')
let _tenantId: string | null = localStorage.getItem('portal_tenantId')
const listeners = new Set<() => void>()

function notify() {
  listeners.forEach((fn) => fn())
}

export function getPortalAuthState() {
  return { user: _user, token: _token, tenantId: _tenantId, isAuthenticated: !!_token }
}

export function setPortalAuth(token: string, tenantId: string, user: PortalUser) {
  _token = token
  _tenantId = tenantId
  _user = user
  localStorage.setItem('portal_token', token)
  localStorage.setItem('portal_tenantId', tenantId)
  localStorage.setItem('portal_user', JSON.stringify(user))
  notify()
}

export function clearPortalAuth() {
  _token = null
  _tenantId = null
  _user = null
  localStorage.removeItem('portal_token')
  localStorage.removeItem('portal_tenantId')
  localStorage.removeItem('portal_user')
  notify()
}

export function usePortalAuth() {
  const [state, setState] = useState(getPortalAuthState)

  useEffect(() => {
    const fn = () => setState(getPortalAuthState())
    listeners.add(fn)
    return () => { listeners.delete(fn) }
  }, [])

  return state
}
