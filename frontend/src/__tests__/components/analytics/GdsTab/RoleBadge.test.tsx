import { render, screen } from '@testing-library/react'
import { RoleBadge } from '@/components/analytics/GdsTab/RoleBadge'

describe('RoleBadge', () => {
  it('renders SUPPLIER text', () => {
    render(<RoleBadge role="SUPPLIER" />)
    expect(screen.getByText('SUPPLIER')).toBeInTheDocument()
  })

  it('renders BUYER text', () => {
    render(<RoleBadge role="BUYER" />)
    expect(screen.getByText('BUYER')).toBeInTheDocument()
  })

  it('renders HYBRID text', () => {
    render(<RoleBadge role="HYBRID" />)
    expect(screen.getByText('HYBRID')).toBeInTheDocument()
  })

  it('applies teal classes for SUPPLIER', () => {
    const { container } = render(<RoleBadge role="SUPPLIER" />)
    expect(container.firstChild).toHaveClass('bg-teal-50')
  })

  it('applies violet classes for BUYER', () => {
    const { container } = render(<RoleBadge role="BUYER" />)
    expect(container.firstChild).toHaveClass('bg-violet-50')
  })

  it('applies blue classes for unknown role', () => {
    const { container } = render(<RoleBadge role="UNKNOWN" />)
    expect(container.firstChild).toHaveClass('bg-blue-50')
  })
})
