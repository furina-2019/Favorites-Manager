import type { ReactNode } from 'react'

const MARK_STYLE = {
  background: '#ffd666',
  color: '#333',
  borderRadius: 2,
  padding: '0 1px',
  fontWeight: 600,
} as const

/**
 * Splits `text` around every occurrence of `query` (case-insensitive) and
 * wraps the matched parts in highlighted <mark> spans. Returns the plain
 * string when there is nothing to highlight, so callers can render it
 * directly inside text nodes / ellipsized paragraphs.
 */
export function highlightText(text: string, query: string): ReactNode {
  const q = query.trim().toLowerCase()
  if (!q || !text) return text

  const lower = text.toLowerCase()
  const parts: ReactNode[] = []
  let i = 0
  let idx = lower.indexOf(q)
  while (idx !== -1) {
    if (idx > i) parts.push(text.slice(i, idx))
    parts.push(
      <mark key={`h-${idx}`} style={MARK_STYLE}>
        {text.slice(idx, idx + q.length)}
      </mark>,
    )
    i = idx + q.length
    idx = lower.indexOf(q, i)
  }
  if (i < text.length) parts.push(text.slice(i))
  return parts
}
