import { render, screen } from '@testing-library/react'
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/LoadingState'

describe('LoadingState', () => {
  it('renders the default text', () => {
    render(<LoadingState />)
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('renders a custom text prop', () => {
    render(<LoadingState text="Procesando datos..." />)
    expect(screen.getByText('Procesando datos...')).toBeInTheDocument()
  })
})

describe('ErrorState', () => {
  it('renders default title and message', () => {
    render(<ErrorState />)
    expect(screen.getByText('Sin datos')).toBeInTheDocument()
    expect(screen.getByText(/ejecuta primero el pipeline/i)).toBeInTheDocument()
  })

  it('renders custom title and message', () => {
    render(<ErrorState title="Error personalizado" message="Algo salió mal." />)
    expect(screen.getByText('Error personalizado')).toBeInTheDocument()
    expect(screen.getByText('Algo salió mal.')).toBeInTheDocument()
  })

  it('contains a link to /pipeline', () => {
    render(<ErrorState />)
    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '/pipeline')
  })
})

describe('EmptyState', () => {
  it('renders the "Base de datos vacía" heading', () => {
    render(<EmptyState />)
    expect(screen.getByText(/base de datos vacía/i)).toBeInTheDocument()
  })

  it('shows the admin pipeline CTA when isAdmin=true', () => {
    render(<EmptyState isAdmin />)
    expect(screen.getByRole('link', { name: /ejecutar pipeline/i })).toBeInTheDocument()
  })

  it('hides the admin CTA when isAdmin=false', () => {
    render(<EmptyState isAdmin={false} />)
    expect(screen.queryByRole('link', { name: /ejecutar pipeline/i })).not.toBeInTheDocument()
  })

  it('shows different message for non-admin', () => {
    render(<EmptyState isAdmin={false} />)
    expect(screen.getByText(/contacta con el administrador/i)).toBeInTheDocument()
  })
})
