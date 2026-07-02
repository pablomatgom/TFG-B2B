import { render, screen } from '@testing-library/react'
import TemporalSection from '@/components/dashboard/TemporalSection'

jest.mock('@/components/charts/TemporalAreaChart', () => ({
  __esModule: true,
  default: () => <div data-testid="temporal-chart" />,
}))

const ROWS = [
  { date: '2024-01', documents: 120, flagged: 10 },
  { date: '2024-02', documents: 200, flagged: 30 },
  { date: '2024-03', documents: 80,  flagged: 5  },
]

describe('TemporalSection — with data', () => {
  it('renders the section header title', () => {
    render(<TemporalSection data={ROWS} />)
    expect(screen.getByText(/evolución de transacciones/i)).toBeInTheDocument()
  })

  it('renders total documents', () => {
    render(<TemporalSection data={ROWS} />)
    // 120 + 200 + 80 = 400
    expect(screen.getByText('400')).toBeInTheDocument()
  })

  it('shows the correct number of active months', () => {
    render(<TemporalSection data={ROWS} />)
    expect(screen.getByText('3 meses')).toBeInTheDocument()
  })

  it('shows the peak month value', () => {
    render(<TemporalSection data={ROWS} />)
    // peak is 200 in 2024-02
    expect(screen.getByText('200')).toBeInTheDocument()
  })

  it('renders the chart component', () => {
    render(<TemporalSection data={ROWS} />)
    expect(screen.getByTestId('temporal-chart')).toBeInTheDocument()
  })
})

describe('TemporalSection — empty data', () => {
  it('shows the empty state message', () => {
    render(<TemporalSection data={[]} />)
    expect(screen.getByText(/sin datos temporales/i)).toBeInTheDocument()
  })

  it('does not render the chart', () => {
    render(<TemporalSection data={[]} />)
    expect(screen.queryByTestId('temporal-chart')).not.toBeInTheDocument()
  })
})
