import '@testing-library/jest-dom'

// React 19 concurrent mode: declare this is a test environment.
globalThis.IS_REACT_ACT_ENVIRONMENT = true

// Suppress the two well-known React 19 act() warnings that fire when async
// state updates (e.g. after fetch) resolve outside an explicit act() boundary.
// Tests still assert correct behaviour — these are noise-only warnings.
const SUPPRESSED = [
  'not wrapped in act',
  'not configured to support act',
]

const _consoleError = console.error.bind(console)
console.error = (...args: unknown[]) => {
  const msg = typeof args[0] === 'string' ? args[0] : ''
  if (SUPPRESSED.some((w) => msg.includes(w))) return
  _consoleError(...args)
}
