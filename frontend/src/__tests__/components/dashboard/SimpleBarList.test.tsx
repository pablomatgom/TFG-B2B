import { render, screen } from '@testing-library/react'
import SimpleBarList from '@/components/dashboard/SimpleBarList'

const DATA = [
  { name: 'Acme Corp',   value: 42 },
  { name: 'Globex Ltd',  value: 18 },
  { name: 'Initech Inc', value: 7  },
]

describe('SimpleBarList', () => {
  it('renders all item names', () => {
    render(<SimpleBarList data={DATA} suffix="clientes" />)
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Globex Ltd')).toBeInTheDocument()
    expect(screen.getByText('Initech Inc')).toBeInTheDocument()
  })

  it('renders formatted values with the suffix', () => {
    render(<SimpleBarList data={DATA} suffix="clientes" />)
    expect(screen.getByText('42 clientes')).toBeInTheDocument()
    expect(screen.getByText('18 clientes')).toBeInTheDocument()
  })

  it('renders nothing when data is empty', () => {
    const { container } = render(<SimpleBarList data={[]} suffix="items" />)
    expect(container.querySelector('ul')!.children).toHaveLength(0)
  })
})
