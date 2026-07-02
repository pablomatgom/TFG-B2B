import { getToken, setToken, clearToken, decodeToken, isTokenExpired } from '@/lib/auth'
import type { TokenPayload } from '@/types/auth'

// Helper: build a base64url-encoded JWT with arbitrary payload
function makeToken(payload: object): string {
  const json  = JSON.stringify(payload)
  const b64   = Buffer.from(json).toString('base64')
  const b64url = b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
  return `eyJhbGciOiJIUzI1NiJ9.${b64url}.fakesig`
}

function clearAllCookies() {
  document.cookie.split(';').forEach((c) => {
    const key = c.trim().split('=')[0]
    document.cookie = `${key}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/`
  })
}

beforeEach(clearAllCookies)

describe('setToken / getToken / clearToken', () => {
  it('getToken returns null when no cookie is set', () => {
    expect(getToken()).toBeNull()
  })

  it('setToken writes a cookie that getToken can read back', () => {
    setToken('my-token')
    expect(getToken()).toBe('my-token')
  })

  it('setToken URL-encodes the token value', () => {
    setToken('a+b/c=d')
    expect(getToken()).toBe('a+b/c=d')
  })

  it('clearToken removes the cookie', () => {
    setToken('to-clear')
    clearToken()
    expect(getToken()).toBeNull()
  })

  it('getToken returns the latest value when overwritten', () => {
    setToken('first')
    setToken('second')
    expect(getToken()).toBe('second')
  })
})

describe('decodeToken', () => {
  it('decodes a valid JWT payload', () => {
    const payload = { sub: 'user@test.com', exp: 9999999999, role: 'admin', company_id: 'C-001', full_name: null }
    const result  = decodeToken(makeToken(payload))
    expect(result).not.toBeNull()
    expect(result!.sub).toBe('user@test.com')
    expect(result!.role).toBe('admin')
    expect(result!.company_id).toBe('C-001')
  })

  it('returns null for a malformed token', () => {
    expect(decodeToken('not.a.jwt')).toBeNull()
  })

  it('returns null for completely invalid input', () => {
    expect(decodeToken('garbage')).toBeNull()
  })

  it('returns null for a token with invalid base64 in payload', () => {
    expect(decodeToken('header.!!!.sig')).toBeNull()
  })
})

describe('isTokenExpired', () => {
  it('returns false for a future expiry', () => {
    const payload: TokenPayload = { sub: 'u', exp: Math.floor(Date.now() / 1000) + 3600, role: 'admin', company_id: 'C', full_name: null }
    expect(isTokenExpired(payload)).toBe(false)
  })

  it('returns true for a past expiry', () => {
    const payload: TokenPayload = { sub: 'u', exp: Math.floor(Date.now() / 1000) - 1, role: 'admin', company_id: 'C', full_name: null }
    expect(isTokenExpired(payload)).toBe(true)
  })
})
