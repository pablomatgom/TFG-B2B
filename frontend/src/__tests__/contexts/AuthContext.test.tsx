import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'

// Mock next/navigation before imports
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({ push: jest.fn() })),
}))

// Mock lib/auth so we control every function
jest.mock('@/lib/auth', () => ({
  getToken:       jest.fn(),
  setToken:       jest.fn(),
  clearToken:     jest.fn(),
  decodeToken:    jest.fn(),
  isTokenExpired: jest.fn(),
}))

import * as authLib from '@/lib/auth'
import { useRouter } from 'next/navigation'

const mockGetToken       = authLib.getToken       as jest.Mock
const mockSetToken       = authLib.setToken       as jest.Mock
const mockClearToken     = authLib.clearToken     as jest.Mock
const mockDecodeToken    = authLib.decodeToken    as jest.Mock
const mockIsTokenExpired = authLib.isTokenExpired as jest.Mock

const FAKE_PAYLOAD = {
  sub:        'user@test.com',
  exp:        9999999999,
  role:       'admin' as const,
  company_id: 'C-001',
  full_name:  null,
}

function UserDisplay() {
  const { user, loading } = useAuth()
  if (loading) return <span>loading</span>
  return <span>{user ? user.email : 'no-user'}</span>
}

beforeEach(() => {
  jest.clearAllMocks()
  mockGetToken.mockReturnValue(null)
  mockDecodeToken.mockReturnValue(null)
  mockIsTokenExpired.mockReturnValue(false)
  ;(useRouter as jest.Mock).mockReturnValue({ push: jest.fn() })
})

describe('AuthContext — mount', () => {
  it('shows no user when there is no cookie', async () => {
    render(<AuthProvider><UserDisplay /></AuthProvider>)
    await waitFor(() => expect(screen.getByText('no-user')).toBeInTheDocument())
  })

  it('populates user from a valid cookie on mount', async () => {
    mockGetToken.mockReturnValue('fake-token')
    mockDecodeToken.mockReturnValue(FAKE_PAYLOAD)
    mockIsTokenExpired.mockReturnValue(false)

    render(<AuthProvider><UserDisplay /></AuthProvider>)
    await waitFor(() => expect(screen.getByText('user@test.com')).toBeInTheDocument())
  })

  it('clears an expired cookie on mount', async () => {
    mockGetToken.mockReturnValue('expired-token')
    mockDecodeToken.mockReturnValue(FAKE_PAYLOAD)
    mockIsTokenExpired.mockReturnValue(true)

    render(<AuthProvider><UserDisplay /></AuthProvider>)
    await waitFor(() => expect(screen.getByText('no-user')).toBeInTheDocument())
    expect(mockClearToken).toHaveBeenCalled()
  })
})

describe('AuthContext — login', () => {
  it('calls setToken and populates user on success', async () => {
    mockDecodeToken.mockReturnValue(FAKE_PAYLOAD)
    global.fetch = jest.fn().mockResolvedValue({
      ok:   true,
      json: () => Promise.resolve({ access_token: 'new-token' }),
    })

    function LoginButton() {
      const { user, login } = useAuth()
      return (
        <div>
          <span>{user ? user.email : 'no-user'}</span>
          <button onClick={() => login('user@test.com', 'pass')}>login</button>
        </div>
      )
    }
    render(<AuthProvider><LoginButton /></AuthProvider>)

    await act(async () => userEvent.click(screen.getByText('login')))
    await waitFor(() => expect(screen.getByText('user@test.com')).toBeInTheDocument())
    expect(mockSetToken).toHaveBeenCalledWith('new-token')
  })

  it('throws when credentials are wrong', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok:   false,
      json: () => Promise.resolve({ detail: 'Credenciales incorrectas' }),
    })

    function LoginButton() {
      const { login } = useAuth()
      const [err, setErr] = React.useState<string | null>(null)
      return (
        <div>
          {err && <span data-testid="err">{err}</span>}
          <button onClick={() => login('u', 'w').catch((e: Error) => setErr(e.message))}>login</button>
        </div>
      )
    }
    render(<AuthProvider><LoginButton /></AuthProvider>)

    await act(async () => userEvent.click(screen.getByText('login')))
    await waitFor(() => expect(screen.getByTestId('err')).toBeInTheDocument())
    expect(screen.getByTestId('err').textContent).toContain('Credenciales')
  })
})

describe('AuthContext — logout', () => {
  it('clears user and calls clearToken', async () => {
    mockGetToken.mockReturnValue('token')
    mockDecodeToken.mockReturnValue(FAKE_PAYLOAD)

    function LogoutButton() {
      const { user, logout } = useAuth()
      return (
        <div>
          <span>{user ? user.email : 'no-user'}</span>
          <button onClick={logout}>logout</button>
        </div>
      )
    }
    render(<AuthProvider><LogoutButton /></AuthProvider>)

    await waitFor(() => expect(screen.getByText('user@test.com')).toBeInTheDocument())
    await act(async () => userEvent.click(screen.getByText('logout')))
    await waitFor(() => expect(screen.getByText('no-user')).toBeInTheDocument())
    expect(mockClearToken).toHaveBeenCalled()
  })
})
