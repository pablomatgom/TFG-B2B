import { BRAND } from '@/lib/brand'

describe('BRAND', () => {
  it('has a non-empty name', () => expect(BRAND.name.length).toBeGreaterThan(0))
  it('has a subtitle',      () => expect(BRAND.subtitle.length).toBeGreaterThan(0))
  it('has a description',   () => expect(BRAND.description.length).toBeGreaterThan(0))
  it('has capabilities array with at least one entry', () => expect(BRAND.capabilities.length).toBeGreaterThan(0))
  it('name is B2B Graph Intel', () => expect(BRAND.name).toBe('B2B Graph Intel'))
})
