import { render, screen } from '@testing-library/react'
import SectionHeader from '@/components/ui/SectionHeader'

function StubIcon(props: React.SVGProps<SVGSVGElement>) {
  return <svg data-testid="stub-icon" {...props} />
}

describe('SectionHeader', () => {
  it('renders the title', () => {
    render(<SectionHeader icon={StubIcon} title="Mi Título" subtitle="Mi subtítulo" />)
    expect(screen.getByText('Mi Título')).toBeInTheDocument()
  })

  it('renders the subtitle', () => {
    render(<SectionHeader icon={StubIcon} title="T" subtitle="Descripción detallada" />)
    expect(screen.getByText('Descripción detallada')).toBeInTheDocument()
  })

  it('renders the icon', () => {
    render(<SectionHeader icon={StubIcon} title="T" subtitle="S" />)
    expect(screen.getByTestId('stub-icon')).toBeInTheDocument()
  })
})
