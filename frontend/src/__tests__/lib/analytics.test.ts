import {
  EUR, SIGN, rateBadge, lateBarColor, lateBadge,
  paymentDaysBadge, reliabilityBadge, discrepancyBadge,
  riskScoreBadge, fragilityBadge, deltaColor,
  DOC_COLORS, ESTADO_STYLE, PAGE_SIZE, PAGE_SIZE_LG, PAGE_SIZE_SM,
} from '@/lib/analytics'

describe('EUR', () => {
  it('formats zero', () => expect(EUR(0)).toMatch('0'))
  it('formats a positive integer', () => expect(EUR(1000)).toMatch('1'))
  it('returns a string', () => expect(typeof EUR(42)).toBe('string'))
  it('respects decimal places', () => {
    const result = EUR(3.14159, 2)
    expect(result).toMatch('3')
  })
})

describe('SIGN', () => {
  it('returns "+" for positive', () => expect(SIGN(1)).toBe('+'))
  it('returns "" for zero', ()   => expect(SIGN(0)).toBe(''))
  it('returns "" for negative',  () => expect(SIGN(-1)).toBe(''))
})

describe('rateBadge', () => {
  it('red at >= 20',    () => expect(rateBadge(20)).toBe('red'))
  it('red above 20',   () => expect(rateBadge(50)).toBe('red'))
  it('yellow at 19',   () => expect(rateBadge(19)).toBe('yellow'))
  it('yellow at 10',   () => expect(rateBadge(10)).toBe('yellow'))
  it('emerald at 9',   () => expect(rateBadge(9)).toBe('emerald'))
  it('emerald at 0',   () => expect(rateBadge(0)).toBe('emerald'))
})

describe('lateBarColor', () => {
  it('red at >= 60',    () => expect(lateBarColor(60)).toBe('bg-red-500'))
  it('amber at 59',     () => expect(lateBarColor(59)).toBe('bg-amber-500'))
  it('amber at 40',     () => expect(lateBarColor(40)).toBe('bg-amber-500'))
  it('emerald at 39',   () => expect(lateBarColor(39)).toBe('bg-emerald-500'))
})

describe('lateBadge', () => {
  it('red at >= 60',    () => expect(lateBadge(60)).toContain('red'))
  it('amber at 40',     () => expect(lateBadge(40)).toContain('amber'))
  it('emerald at 0',    () => expect(lateBadge(0)).toContain('emerald'))
})

describe('paymentDaysBadge', () => {
  it('red when days > agreed * 1.1',  () => expect(paymentDaysBadge(111, 100)).toContain('red'))
  it('amber when days > agreed',       () => expect(paymentDaysBadge(101, 100)).toContain('amber'))
  it('emerald when on time',           () => expect(paymentDaysBadge(100, 100)).toContain('emerald'))
  it('emerald when early',             () => expect(paymentDaysBadge(30, 60)).toContain('emerald'))
})

describe('reliabilityBadge', () => {
  it('emerald at >= 0.8',   () => expect(reliabilityBadge(0.8)).toContain('emerald'))
  it('amber at 0.79',       () => expect(reliabilityBadge(0.79)).toContain('amber'))
  it('amber at 0.6',        () => expect(reliabilityBadge(0.6)).toContain('amber'))
  it('red below 0.6',       () => expect(reliabilityBadge(0.59)).toContain('red'))
})

describe('discrepancyBadge', () => {
  it('red at >= 10',     () => expect(discrepancyBadge(10)).toContain('red'))
  it('amber at 9.9',     () => expect(discrepancyBadge(9.9)).toContain('amber'))
  it('amber at 7.5',     () => expect(discrepancyBadge(7.5)).toContain('amber'))
  it('emerald below 7.5',() => expect(discrepancyBadge(7.4)).toContain('emerald'))
})

describe('riskScoreBadge', () => {
  it('red at >= 70',    () => expect(riskScoreBadge(70)).toContain('red'))
  it('amber at 69',     () => expect(riskScoreBadge(69)).toContain('amber'))
  it('amber at 40',     () => expect(riskScoreBadge(40)).toContain('amber'))
  it('indigo below 40', () => expect(riskScoreBadge(39)).toContain('indigo'))
})

describe('fragilityBadge', () => {
  it('red at >= 80',    () => expect(fragilityBadge(80)).toContain('red'))
  it('amber at 79',     () => expect(fragilityBadge(79)).toContain('amber'))
  it('amber at 50',     () => expect(fragilityBadge(50)).toContain('amber'))
  it('emerald at 49',   () => expect(fragilityBadge(49)).toContain('emerald'))
})

describe('deltaColor', () => {
  it('red for positive',    () => expect(deltaColor(1)).toBe('text-red-600'))
  it('amber for negative',  () => expect(deltaColor(-1)).toBe('text-amber-600'))
  it('gray for zero',       () => expect(deltaColor(0)).toBe('text-gray-400'))
})

describe('constants', () => {
  it('DOC_COLORS has INVOICE, ORDER, SHIPMENT, CREDIT_NOTE', () => {
    expect(DOC_COLORS).toHaveProperty('INVOICE')
    expect(DOC_COLORS).toHaveProperty('ORDER')
    expect(DOC_COLORS).toHaveProperty('SHIPMENT')
    expect(DOC_COLORS).toHaveProperty('CREDIT_NOTE')
  })
  it('ESTADO_STYLE has SOBREFACTURADO, SUBFACTURADO, CONFORME', () => {
    expect(ESTADO_STYLE).toHaveProperty('SOBREFACTURADO')
    expect(ESTADO_STYLE).toHaveProperty('SUBFACTURADO')
    expect(ESTADO_STYLE).toHaveProperty('CONFORME')
  })
  it('PAGE_SIZE constants are positive integers', () => {
    expect(PAGE_SIZE).toBeGreaterThan(0)
    expect(PAGE_SIZE_LG).toBeGreaterThan(0)
    expect(PAGE_SIZE_SM).toBeGreaterThan(0)
  })
})
