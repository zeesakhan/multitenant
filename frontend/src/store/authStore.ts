import { useEffect, useState } from 'react'
import { User } from '../types'

let _user: User | null = (() => {
  try { return JSON.parse(localStorage.getItem('user') ?? 'null') } catch { return null }
})()
let _token: string | null = localStorage.getItem('token')
let _tenantId: string | null = localStorage.getItem('tenantId')
const listeners = new Set<() => void>()

function notify() {
  listeners.forEach((fn) => fn())
}

export function getAuthState() {
  return { user: _user, token: _token, tenantId: _tenantId, isAuthenticated: !!_token }
}

export function setAuth(token: string, tenantId: string, user: User) {
  _token = token
  _tenantId = tenantId
  _user = user
  localStorage.setItem('token', token)
  localStorage.setItem('tenantId', tenantId)
  localStorage.setItem('user', JSON.stringify(user))
  notify()
}

export function clearAuth() {
  _token = null
  _tenantId = null
  _user = null
  localStorage.removeItem('token')
  localStorage.removeItem('tenantId')
  localStorage.removeItem('user')
  notify()
}

export function useAuth() {
  const [state, setState] = useState(getAuthState)

  useEffect(() => {
    const fn = () => setState(getAuthState())
    listeners.add(fn)
    return () => { listeners.delete(fn) }
  }, [])

  return state
}
