import { analyticsReducer, INITIAL_ANALYTICS_STATE } from '@/hooks/useFetchTab'
import type { AnalyticsAction } from '@/hooks/useFetchTab'

describe('INITIAL_ANALYTICS_STATE', () => {
  it('has null risk', ()              => expect(INITIAL_ANALYTICS_STATE.risk).toBeNull())
  it('has empty arrays for lists', () => {
    expect(INITIAL_ANALYTICS_STATE.scores).toEqual([])
    expect(INITIAL_ANALYTICS_STATE.discrepancy).toEqual([])
    expect(INITIAL_ANALYTICS_STATE.leadTime).toEqual([])
    expect(INITIAL_ANALYTICS_STATE.payment).toEqual([])
    expect(INITIAL_ANALYTICS_STATE.lineage).toEqual([])
  })
  it('has empty gds object', () => {
    expect(INITIAL_ANALYTICS_STATE.gds.bottlenecks).toEqual([])
    expect(INITIAL_ANALYTICS_STATE.gds.communities).toEqual([])
  })
})

describe('analyticsReducer', () => {
  it('merges SET_RISK data into state', () => {
    const action: AnalyticsAction = {
      type: 'SET_RISK',
      data: { risk: null, scores: [{ company_id: 'C1' } as any], fragility: [], geographic: [] },
    }
    const next = analyticsReducer(INITIAL_ANALYTICS_STATE, action)
    expect(next.scores).toHaveLength(1)
    expect(next.scores[0].company_id).toBe('C1')
  })

  it('merges SET_DISCREPANCY data into state', () => {
    const action: AnalyticsAction = {
      type: 'SET_DISCREPANCY',
      data: { discrepancy: [{ supplier_id: 'S1' } as any], commercial: [] },
    }
    const next = analyticsReducer(INITIAL_ANALYTICS_STATE, action)
    expect(next.discrepancy).toHaveLength(1)
  })

  it('merges SET_LEAD_TIME data into state', () => {
    const action: AnalyticsAction = {
      type: 'SET_LEAD_TIME',
      data: { leadTime: [{ category: 'CAT1' } as any] },
    }
    const next = analyticsReducer(INITIAL_ANALYTICS_STATE, action)
    expect(next.leadTime[0].category).toBe('CAT1')
  })

  it('merges SET_GDS data into state', () => {
    const gds = { bottlenecks: [{ company_id: 'B1' } as any], communities: [], pagerank: [], wcc: {} as any }
    const action: AnalyticsAction = { type: 'SET_GDS', data: { gds } }
    const next = analyticsReducer(INITIAL_ANALYTICS_STATE, action)
    expect(next.gds.bottlenecks).toHaveLength(1)
  })

  it('does not mutate the original state', () => {
    const action: AnalyticsAction = {
      type: 'SET_LEAD_TIME',
      data: { leadTime: [{ category: 'X' } as any] },
    }
    analyticsReducer(INITIAL_ANALYTICS_STATE, action)
    expect(INITIAL_ANALYTICS_STATE.leadTime).toHaveLength(0)
  })

  it('preserves unrelated state slices', () => {
    const action: AnalyticsAction = {
      type: 'SET_LEAD_TIME',
      data: { leadTime: [] },
    }
    const stateWithScores = { ...INITIAL_ANALYTICS_STATE, scores: [{ company_id: 'S1' } as any] }
    const next = analyticsReducer(stateWithScores, action)
    expect(next.scores).toHaveLength(1)
  })
})
