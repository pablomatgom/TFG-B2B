import { renderHook, waitFor, act } from '@testing-library/react'
import { useDbStatus } from '@/hooks/useDbStatus'

const mockFetch = jest.fn()
beforeAll(() => { global.fetch = mockFetch })
afterEach(() => { mockFetch.mockReset(); jest.useRealTimers() })

function makeFetchOk()    { mockFetch.mockResolvedValue({ ok: true  }) }
function makeFetchFail()  { mockFetch.mockResolvedValue({ ok: false }) }
function makeFetchThrow() { mockFetch.mockRejectedValue(new Error('network')) }

describe('useDbStatus', () => {
  it('starts as "checking"', () => {
    // Never resolves — prevents setStatus from firing after the test ends
    mockFetch.mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useDbStatus())
    expect(result.current).toBe('checking')
  })

  it('transitions to "connected" when fetch responds ok', async () => {
    makeFetchOk()
    const { result } = renderHook(() => useDbStatus())
    await waitFor(() => expect(result.current).toBe('connected'))
  })

  it('transitions to "disconnected" when fetch responds not-ok', async () => {
    makeFetchFail()
    const { result } = renderHook(() => useDbStatus())
    await waitFor(() => expect(result.current).toBe('disconnected'))
  })

  it('transitions to "disconnected" when fetch throws', async () => {
    makeFetchThrow()
    const { result } = renderHook(() => useDbStatus())
    await waitFor(() => expect(result.current).toBe('disconnected'))
  })

  it('polls again after 15 seconds', async () => {
    jest.useFakeTimers()
    makeFetchOk()
    renderHook(() => useDbStatus())

    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1))

    await act(async () => { jest.advanceTimersByTime(15000) })
    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(2))
  })
})
