import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RankingsGrid from '@/components/dashboard/RankingsGrid'

jest.mock('@/components/charts/RingChart', () => ({
  __esModule: true,
  default: ({ centerLabel, centerSub }: { centerLabel: string; centerSub: string }) => (
    <div data-testid="ring-chart">{centerLabel} {centerSub}</div>
  ),
}))

jest.mock('@/components/dashboard/RankingModal', () => ({
  __esModule: true,
  default: ({ modal, onClose }: { modal: unknown; onClose: () => void }) =>
    modal ? (
      <div data-testid="ranking-modal">
        <button onClick={onClose}>Cerrar</button>
      </div>
    ) : null,
}))

const SUPPLIERS = Array.from({ length: 6 }, (_, i) => ({ name: `Proveedor ${i + 1}`, value: 10 - i }))
const BUYERS    = [{ name: 'Comprador 1', value: 5 }]
const DOC_TYPES = [{ name: 'INVOICE', value: 100 }, { name: 'ORDER', value: 80 }]

describe('RankingsGrid', () => {
  it('renders the doc-type ring chart', () => {
    render(<RankingsGrid docTypes={DOC_TYPES} suppliers={SUPPLIERS} buyers={BUYERS} />)
    expect(screen.getByTestId('ring-chart')).toBeInTheDocument()
  })

  it('renders the supplier section title', () => {
    render(<RankingsGrid docTypes={DOC_TYPES} suppliers={SUPPLIERS} buyers={BUYERS} />)
    expect(screen.getByText('Top Proveedores')).toBeInTheDocument()
  })

  it('renders the buyer section title', () => {
    render(<RankingsGrid docTypes={DOC_TYPES} suppliers={SUPPLIERS} buyers={BUYERS} />)
    expect(screen.getByText('Top Compradores')).toBeInTheDocument()
  })

  it('shows the "Ver todos" button when suppliers exceed 5', () => {
    render(<RankingsGrid docTypes={DOC_TYPES} suppliers={SUPPLIERS} buyers={BUYERS} />)
    expect(screen.getByText(/ver todos \(6\)/i)).toBeInTheDocument()
  })

  it('does not show modal initially', () => {
    render(<RankingsGrid docTypes={DOC_TYPES} suppliers={SUPPLIERS} buyers={BUYERS} />)
    expect(screen.queryByTestId('ranking-modal')).not.toBeInTheDocument()
  })

  it('opens modal when "Ver todos" is clicked', async () => {
    render(<RankingsGrid docTypes={DOC_TYPES} suppliers={SUPPLIERS} buyers={BUYERS} />)
    await userEvent.click(screen.getByText(/ver todos \(6\)/i))
    expect(screen.getByTestId('ranking-modal')).toBeInTheDocument()
  })

  it('closes modal when onClose is triggered', async () => {
    render(<RankingsGrid docTypes={DOC_TYPES} suppliers={SUPPLIERS} buyers={BUYERS} />)
    await userEvent.click(screen.getByText(/ver todos \(6\)/i))
    await userEvent.click(screen.getByText('Cerrar'))
    expect(screen.queryByTestId('ranking-modal')).not.toBeInTheDocument()
  })

  it('shows empty state when no suppliers', () => {
    render(<RankingsGrid docTypes={[]} suppliers={[]} buyers={[]} />)
    expect(screen.getAllByText(/sin datos/i).length).toBeGreaterThan(0)
  })
})
