import { useState, type CSSProperties, type MouseEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { highlightText } from '../utils/highlight'

const POPUP_W = 300
const POPUP_H = 240

interface TagPillsProps {
  tags: string[]
  /** Current search query - matching tags are highlighted and never collapsed */
  highlight?: string
  /** How many tags to show before collapsing into a "+N" chip (default 3) */
  max?: number
  /** cover: dark overlay pills (item cover); theme: themed pills (folder card); plain: neutral */
  variant?: 'cover' | 'theme' | 'plain'
  /** Center the row (folder card body) vs. left-aligned (cover overlay) */
  center?: boolean
  /** Controlled popup (used by the mind map, where the trigger lives inside SVG) */
  popupOpen?: boolean
  popupAnchor?: { x: number; y: number } | null
  onPopupClose?: () => void
}

interface PopupState {
  open: boolean
  anchor: { x: number; y: number }
}

/**
 * Read-only tag row shown on cards and in the mind map. Renders up to `max`
 * pills; extra tags collapse into a "+N" chip that opens a small popup with
 * ALL tags (sized like an item card). While searching, tags matching the
 * query are forced visible and the matched part is highlighted.
 *
 * The popup can also be controlled externally (popupOpen/popupAnchor/
 * onPopupClose) - used by the mind map, where the "+N" trigger is an SVG
 * element and only the popup itself is HTML.
 */
export default function TagPills({
  tags,
  highlight = '',
  max = 3,
  variant = 'plain',
  center = false,
  popupOpen,
  popupAnchor = null,
  onPopupClose,
}: TagPillsProps) {
  const { t } = useTranslation()
  const { darkMode, themeColor } = useUIStore()
  const [popup, setPopup] = useState<PopupState>({ open: false, anchor: { x: 0, y: 0 } })

  if (!tags || tags.length === 0) return null

  const controlled = popupOpen !== undefined
  const q = highlight.trim().toLowerCase()
  const matching = q ? tags.filter(tag => tag.toLowerCase().includes(q)) : []
  const shown = tags.slice(0, max)
  // Matching tags are always shown, even if they fall outside the first `max`
  const visible = Array.from(new Set([...shown, ...matching]))
  const hiddenCount = tags.length - visible.length

  const pillStyle = (chip = false): CSSProperties => {
    const base: CSSProperties = {
      borderRadius: 999,
      padding: '0.0625rem 0.5rem',
      fontSize: '0.6875rem',
      lineHeight: '1rem',
    }
    if (variant === 'cover') {
      return {
        ...base,
        background: 'rgba(0, 0, 0, 0.55)',
        color: '#fff',
        border: '1px solid rgba(255, 255, 255, 0.25)',
        ...(chip ? { color: '#fff', fontWeight: 600 } : {}),
      }
    }
    if (variant === 'theme') {
      return {
        ...base,
        background: `${themeColor}18`,
        color: themeColor,
        border: `1px solid ${themeColor}40`,
        ...(chip ? { fontWeight: 600 } : {}),
      }
    }
    return {
      ...base,
      background: darkMode ? '#262626' : '#fff',
      color: darkMode ? '#ccc' : '#555',
      border: `1px solid ${darkMode ? '#3d3d3d' : '#d9d9d9'}`,
      ...(chip ? { fontWeight: 600 } : {}),
    }
  }

  const openPopup = (e: MouseEvent<HTMLElement>) => {
    e.stopPropagation()
    const rect = e.currentTarget.getBoundingClientRect()
    setPopup(prev => ({ open: !prev.open, anchor: { x: rect.left, y: rect.bottom } }))
  }

  const closePopup = () => {
    if (controlled) onPopupClose?.()
    else setPopup(prev => ({ ...prev, open: false }))
  }

  const anchor = controlled ? popupAnchor : popup.anchor
  const popupVisible = controlled ? !!popupOpen && !!anchor : popup.open && hiddenCount > 0
  const left = anchor ? Math.max(8, Math.min(anchor.x, window.innerWidth - POPUP_W - 8)) : 0
  const top = anchor ? Math.max(8, Math.min(anchor.y + 8, window.innerHeight - POPUP_H - 8)) : 0

  return (
    <>
      {/* The pill row is drawn by the caller in controlled mode (mind map SVG) */}
      {!controlled && (
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.25rem',
            justifyContent: center ? 'center' : 'flex-start',
            maxWidth: center ? '12.5rem' : '100%',
          }}
        >
          {visible.map(tag => (
            <span key={tag} style={pillStyle()}>
              {highlightText(tag, q)}
            </span>
          ))}
          {hiddenCount > 0 && (
            <span
              style={{ ...pillStyle(true), cursor: 'pointer', userSelect: 'none' }}
              title={t('all_tags')}
              onClick={openPopup}
            >
              +{hiddenCount}
            </span>
          )}
        </div>
      )}

      {/* All-tags popup: item-card sized, closes on backdrop click / re-clicking the chip.
          Both layers stop propagation so closing never triggers the card underneath
          (folder navigation / item selection). */}
      {popupVisible && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 1001, background: 'transparent' }}
            onClick={(e) => {
              e.stopPropagation()
              closePopup()
            }}
            onMouseDown={(e) => e.stopPropagation()}
          />
          <div
            style={{
              position: 'fixed',
              left,
              top,
              zIndex: 1002,
              width: 'min(300px, calc(100vw - 16px))',
              maxHeight: POPUP_H,
              overflowY: 'auto',
              background: darkMode ? '#1f1f1f' : '#fff',
              border: `1px solid ${darkMode ? '#3d3d3d' : '#e0e0e0'}`,
              borderRadius: 12,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
              padding: '0.75rem',
            }}
            onClick={(e) => e.stopPropagation()}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div style={{ fontSize: '0.75rem', color: '#999', marginBottom: '0.5rem' }}>
              {t('all_tags')}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
              {tags.map(tag => (
                <span
                  key={tag}
                  style={{
                    borderRadius: 999,
                    padding: '0.125rem 0.625rem',
                    fontSize: '0.75rem',
                    lineHeight: '1.125rem',
                    background: darkMode ? '#262626' : '#f5f5f5',
                    color: darkMode ? '#ccc' : '#555',
                    border: `1px solid ${darkMode ? '#3d3d3d' : '#e0e0e0'}`,
                  }}
                >
                  {highlightText(tag, q)}
                </span>
              ))}
            </div>
          </div>
        </>
      )}
    </>
  )
}
