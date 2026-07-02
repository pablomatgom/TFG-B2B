import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DocChip, EstadoPill, ProgressBar, KpiStrip, ForwardRowItem } from '@/components/analytics/shared'
import type { ForwardRow } from '@/types/analytics'

// ── DocChip ──────────────────────────────────────────────────────────────────

describe('DocChip', () => {
  it('renders the document type', () => {
    render(<DocChip tipo="INVOICE" discrepancy={false} />)
    expect(screen.getByText('INVOICE')).toBeInTheDocument()
  })

  it('shows warning icon when discrepancy=true', () => {
    render(<DocChip tipo="ORDER" discrepancy={true} />)
    expect(screen.getByText('⚠')).toBeInTheDocument()
  })

  it('does not show warning icon when discrepancy=false', () => {
    render(<DocChip tipo="ORDER" discrepancy={false} />)
    expect(screen.queryByText('⚠')).not.toBeInTheDocument()
  })

  it('applies fallback style for unknown doc type', () => {
    const { container } = render(<DocChip tipo="UNKNOWN" discrepancy={false} />)
    expect(container.firstChild).toHaveClass('bg-gray-100')
  })
})

// ── EstadoPill ────────────────────────────────────────────────────────────────

describe('EstadoPill', () => {
  it('renders the estado text', () => {
    render(<EstadoPill estado="CONFORME" />)
    expect(screen.getByText('CONFORME')).toBeInTheDocument()
  })

  it('applies emerald style for CONFORME', () => {
    const { container } = render(<EstadoPill estado="CONFORME" />)
    expect(container.firstChild).toHaveClass('bg-emerald-50')
  })

  it('applies red style for SOBREFACTURADO', () => {
    const { container } = render(<EstadoPill estado="SOBREFACTURADO" />)
    expect(container.firstChild).toHaveClass('bg-red-50')
  })

  it('applies amber style for SUBFACTURADO', () => {
    const { container } = render(<EstadoPill estado="SUBFACTURADO" />)
    expect(container.firstChild).toHaveClass('bg-amber-50')
  })
})

// ── ProgressBar ───────────────────────────────────────────────────────────────

describe('ProgressBar', () => {
  it('renders with the given percentage as inline width', () => {
    const { container } = render(<ProgressBar pct={65} />)
    const inner = container.querySelector('[style]') as HTMLElement
    expect(inner.style.width).toBe('65%')
  })

  it('renders with zero percent', () => {
    const { container } = render(<ProgressBar pct={0} />)
    const inner = container.querySelector('[style]') as HTMLElement
    expect(inner.style.width).toBe('0%')
  })
})

// ── KpiStrip ─────────────────────────────────────────────────────────────────

describe('KpiStrip', () => {
  const ITEMS = [
    { label: 'Total', value: '42', sub: 'registros' },
    { label: 'Activos', value: '30' },
  ]

  it('renders all item labels', () => {
    render(<KpiStrip items={ITEMS} />)
    expect(screen.getByText('Total')).toBeInTheDocument()
    expect(screen.getByText('Activos')).toBeInTheDocument()
  })

  it('renders all item values', () => {
    render(<KpiStrip items={ITEMS} />)
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('30')).toBeInTheDocument()
  })

  it('renders sub-text when provided', () => {
    render(<KpiStrip items={ITEMS} />)
    expect(screen.getByText('registros')).toBeInTheDocument()
  })

  it('renders in strip variant without crashing', () => {
    render(<KpiStrip items={ITEMS} variant="strip" />)
    expect(screen.getByText('Total')).toBeInTheDocument()
  })
})

// ── ForwardRowItem ────────────────────────────────────────────────────────────

const MOCK_ROW: ForwardRow = {
  pedido_id:              'ORD-001',
  proveedor:              'ACME Corp',
  comprador:              'GLOBEX Corp',
  total_docs_cumplimiento: 3,
  docs_con_discrepancia:   1,
  importe_pedido_eur:      5000,
  documentos_cumplimiento: [
    { id: 'DOC-001', tipo: 'INVOICE', discrepancy: true  },
    { id: 'DOC-002', tipo: 'ORDER',   discrepancy: false },
  ],
}

describe('ForwardRowItem', () => {
  it('shows the order ID and parties', () => {
    render(<ForwardRowItem row={MOCK_ROW} />)
    expect(screen.getByText('ORD-001')).toBeInTheDocument()
    expect(screen.getByText('ACME Corp')).toBeInTheDocument()
    expect(screen.getByText(/GLOBEX Corp/)).toBeInTheDocument()
  })

  it('is collapsed by default — documents not visible', () => {
    render(<ForwardRowItem row={MOCK_ROW} />)
    expect(screen.queryByText('INVOICE')).not.toBeInTheDocument()
  })

  it('expands when header is clicked', async () => {
    render(<ForwardRowItem row={MOCK_ROW} />)
    await userEvent.click(screen.getByRole('button'))
    expect(screen.getByText('INVOICE')).toBeInTheDocument()
    expect(screen.getByText('ORDER')).toBeInTheDocument()
  })

  it('collapses again on second click', async () => {
    render(<ForwardRowItem row={MOCK_ROW} />)
    await userEvent.click(screen.getByRole('button'))
    await userEvent.click(screen.getByRole('button'))
    expect(screen.queryByText('INVOICE')).not.toBeInTheDocument()
  })

  it('shows conflict count when docs_con_discrepancia > 0', () => {
    render(<ForwardRowItem row={MOCK_ROW} />)
    expect(screen.getByText(/1 conflicto/i)).toBeInTheDocument()
  })

  it('shows "Sin conflictos" when no discrepancies', () => {
    const cleanRow = { ...MOCK_ROW, docs_con_discrepancia: 0 }
    render(<ForwardRowItem row={cleanRow} />)
    expect(screen.getByText(/sin conflictos/i)).toBeInTheDocument()
  })

  it('shows plural form for multiple conflicts', () => {
    const multiRow = { ...MOCK_ROW, docs_con_discrepancia: 3 }
    render(<ForwardRowItem row={multiRow} />)
    expect(screen.getByText(/3 conflictos/i)).toBeInTheDocument()
  })
})
