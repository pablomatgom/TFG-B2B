import { render, screen } from '@testing-library/react'
import StatCard from '@/components/ui/StatCard'

// Avoid pulling in Recharts (ResizeObserver not available in jsdom)
jest.mock('@/components/ui/MiniSparkline', () => ({
  __esModule: true,
  default: () => <div data-testid="sparkline" />,
}))

const baseProps = {
  icon:        <span>icon</span>,
  label:       'Empresas',
  value:       '300',
  sub:         'total activas',
  sparkId:     'test-spark',
  formatHover: (v: number) => String(v),
}

describe('StatCard', () => {
  it('renders the label', () => {
    render(<StatCard {...baseProps} />)
    expect(screen.getByText('Empresas')).toBeInTheDocument()
  })

  it('renders the value', () => {
    render(<StatCard {...baseProps} />)
    expect(screen.getByText('300')).toBeInTheDocument()
  })

  it('renders the sub-text', () => {
    render(<StatCard {...baseProps} />)
    expect(screen.getByText('total activas')).toBeInTheDocument()
  })

  it('renders the sparkline when sparkData is provided', () => {
    render(<StatCard {...baseProps} sparkData={[10, 20, 30]} />)
    expect(screen.getByTestId('sparkline')).toBeInTheDocument()
  })

  it('does not render sparkline when sparkData is absent', () => {
    render(<StatCard {...baseProps} />)
    expect(screen.queryByTestId('sparkline')).not.toBeInTheDocument()
  })

  it('shows a positive trend badge when last value > previous', () => {
    render(<StatCard {...baseProps} sparkData={[10, 20]} />)
    expect(screen.getByText(/↑/)).toBeInTheDocument()
  })

  it('shows a negative trend badge when last value < previous', () => {
    render(<StatCard {...baseProps} sparkData={[20, 10]} />)
    expect(screen.getByText(/↓/)).toBeInTheDocument()
  })

  it('shows no trend badge with a single-point sparkData', () => {
    render(<StatCard {...baseProps} sparkData={[10]} />)
    expect(screen.queryByText(/[↑↓]/)).not.toBeInTheDocument()
  })
})
