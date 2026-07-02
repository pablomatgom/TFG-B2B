import { render, screen } from '@testing-library/react'
import Capability from '@/components/auth/Capability'

describe('Capability', () => {
  it('renders the stat value', () => {
    render(<Capability stat="1.2k" label="Empresas" detail="Generadas con LFR" />)
    expect(screen.getByText('1.2k')).toBeInTheDocument()
  })

  it('renders the label', () => {
    render(<Capability stat="42" label="Algoritmos" detail="Detalle del algoritmo" />)
    expect(screen.getByText('Algoritmos')).toBeInTheDocument()
  })

  it('renders the detail text', () => {
    render(<Capability stat="x" label="y" detail="Texto descriptivo extenso" />)
    expect(screen.getByText('Texto descriptivo extenso')).toBeInTheDocument()
  })
})
