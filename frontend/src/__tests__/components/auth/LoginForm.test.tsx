import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginForm from '@/components/auth/LoginForm'

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}))
jest.mock('sonner', () => ({
  toast: { error: jest.fn(), success: jest.fn() },
}))

import { useAuth } from '@/contexts/AuthContext'
import { toast } from 'sonner'

const mockLogin = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
  ;(useAuth as jest.Mock).mockReturnValue({
    login:   mockLogin,
    logout:  jest.fn(),
    user:    null,
    loading: false,
  })
})

// Helpers: avoid /contraseña/i which also matches aria-label="Mostrar contraseña"
const emailInput    = () => screen.getByLabelText('Correo electrónico')
const passwordInput = () => screen.getByLabelText('Contraseña')

describe('LoginForm — rendering', () => {
  it('renders the email and password inputs', () => {
    render(<LoginForm />)
    expect(emailInput()).toBeInTheDocument()
    expect(passwordInput()).toBeInTheDocument()
  })

  it('renders the submit button', () => {
    render(<LoginForm />)
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it('renders demo account cards', () => {
    render(<LoginForm />)
    // Use exact strings to avoid matching "empresa" inside longer sentences
    expect(screen.getByText('Empresa')).toBeInTheDocument()
    expect(screen.getByText('Administrador')).toBeInTheDocument()
  })
})

describe('LoginForm — validation', () => {
  it('shows error when email is empty', async () => {
    render(<LoginForm />)
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
    expect(toast.error).toHaveBeenCalledWith('Correo requerido', expect.any(Object))
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('shows error when email format is invalid', async () => {
    render(<LoginForm />)
    await userEvent.type(emailInput(), 'notanemail')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
    expect(toast.error).toHaveBeenCalledWith('Correo no válido', expect.any(Object))
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('shows error when password is empty', async () => {
    render(<LoginForm />)
    await userEvent.type(emailInput(), 'user@test.com')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
    expect(toast.error).toHaveBeenCalledWith('Contraseña requerida', expect.any(Object))
    expect(mockLogin).not.toHaveBeenCalled()
  })

  it('calls login() with correct credentials on valid submit', async () => {
    mockLogin.mockResolvedValue(undefined)
    render(<LoginForm />)
    await userEvent.type(emailInput(), 'user@test.com')
    await userEvent.type(passwordInput(), 'mypassword')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
    expect(mockLogin).toHaveBeenCalledWith('user@test.com', 'mypassword')
  })

  it('shows error toast when login() throws', async () => {
    mockLogin.mockRejectedValue(new Error('Credenciales incorrectas'))
    render(<LoginForm />)
    await userEvent.type(emailInput(), 'user@test.com')
    await userEvent.type(passwordInput(), 'wrongpass')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
    expect(toast.error).toHaveBeenCalledWith('Credenciales incorrectas', expect.any(Object))
  })
})

describe('LoginForm — password toggle', () => {
  it('password input starts as type="password"', () => {
    render(<LoginForm />)
    expect(passwordInput()).toHaveAttribute('type', 'password')
  })

  it('clicking the eye icon switches to type="text"', async () => {
    render(<LoginForm />)
    await userEvent.click(screen.getByRole('button', { name: /mostrar contraseña/i }))
    expect(passwordInput()).toHaveAttribute('type', 'text')
  })

  it('clicking the eye icon again hides the password', async () => {
    render(<LoginForm />)
    await userEvent.click(screen.getByRole('button', { name: /mostrar contraseña/i }))
    await userEvent.click(screen.getByRole('button', { name: /ocultar contraseña/i }))
    expect(passwordInput()).toHaveAttribute('type', 'password')
  })
})

describe('LoginForm — demo accounts', () => {
  it('clicking a demo card fills the email field', async () => {
    render(<LoginForm />)
    // Click the email span inside the Empresa card — bubbles to parent onClick
    await userEvent.click(screen.getByText('company0@demo.com'))
    expect(emailInput()).toHaveValue('company0@demo.com')
  })

  it('clicking the Usar button fills the email field', async () => {
    render(<LoginForm />)
    const usarButtons = screen.getAllByRole('button', { name: /usar/i })
    await userEvent.click(usarButtons[0])
    expect(emailInput()).toHaveValue('company0@demo.com')
  })
})
