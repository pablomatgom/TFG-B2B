import { render, screen } from '@testing-library/react'
import DbStatusBadge from '@/components/ui/DbStatusBadge'

describe('DbStatusBadge', () => {
  it('shows "Online / Activa" when connected', () => {
    render(<DbStatusBadge status="connected" />)
    expect(screen.getByText('Online / Activa')).toBeInTheDocument()
  })

  it('shows "Offline / Inactiva" when disconnected', () => {
    render(<DbStatusBadge status="disconnected" />)
    expect(screen.getByText('Offline / Inactiva')).toBeInTheDocument()
  })

  it('shows "Conectando..." when checking', () => {
    render(<DbStatusBadge status="checking" />)
    expect(screen.getByText('Conectando...')).toBeInTheDocument()
  })

  it('always shows the Neo4j Status label', () => {
    render(<DbStatusBadge status="connected" />)
    expect(screen.getByText(/neo4j status/i)).toBeInTheDocument()
  })
})
