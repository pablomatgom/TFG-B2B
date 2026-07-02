import { render, screen } from '@testing-library/react'
import KpiGrid, { HealthStrip } from '@/components/dashboard/KpiGrid'

// StatCard uses MiniSparkline (Recharts) — mock it
jest.mock('@/components/ui/StatCard', () => ({
  __esModule: true,
  default: ({ label, value }: { label: string; value: string }) => (
    <div data-testid="stat-card">
      <span>{label}</span>
      <span>{value}</span>
    </div>
  ),
}))

describe('KpiGrid', () => {
  it('renders all four KPI labels', () => {
    render(<KpiGrid values={{}} />)
    expect(screen.getByText('Empresas Activas')).toBeInTheDocument()
    expect(screen.getByText('Catálogo Productos')).toBeInTheDocument()
    expect(screen.getByText('Documentos EDI')).toBeInTheDocument()
    expect(screen.getByText('Total Conexiones')).toBeInTheDocument()
  })

  it('displays provided values', () => {
    // Use values that don't need thousands separators (locale-independent)
    render(<KpiGrid values={{ Company: 300, Product: 45 }} />)
    expect(screen.getByText('300')).toBeInTheDocument()
    expect(screen.getByText('45')).toBeInTheDocument()
  })

  it('shows 0 for missing values', () => {
    render(<KpiGrid values={{}} />)
    const zeros = screen.getAllByText('0')
    expect(zeros.length).toBeGreaterThanOrEqual(4)
  })

  it('renders a positive trend badge when trends provided', () => {
    render(<KpiGrid values={{ Company: 300 }} trends={{ Company: 5.25 }} />)
    expect(screen.getByText('+5.25%')).toBeInTheDocument()
  })

  it('renders a negative trend badge', () => {
    render(<KpiGrid values={{ Company: 300 }} trends={{ Company: -2.1 }} />)
    expect(screen.getByText('-2.10%')).toBeInTheDocument()
  })
})

describe('HealthStrip', () => {
  const econVol = { total_gross_eur: 1_000_000, invoice_count: 250 } as any
  const docHealth = { flagged_documents: 12, total_documents: 400, overall_discrepancy_rate_pct: 3 } as any

  it('renders three StatCard mocks', () => {
    render(<HealthStrip econVol={econVol} docHealth={docHealth} />)
    expect(screen.getAllByTestId('stat-card')).toHaveLength(3)
  })

  it('shows the discrepancy count', () => {
    render(<HealthStrip econVol={econVol} docHealth={docHealth} />)
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('shows the discrepancy rate', () => {
    render(<HealthStrip econVol={econVol} docHealth={docHealth} />)
    expect(screen.getByText('3%')).toBeInTheDocument()
  })
})
