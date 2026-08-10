import { useEffect, useRef, useState } from 'react'
import { Input, Modal, Tooltip, message } from 'antd'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'
import { getAllTags, createTag, deleteTag } from '../core/database'

interface TagSelectorProps {
  value: string[]
  onChange: (tags: string[]) => void
}

/**
 * Tag picker used by the folder / item dialogs.
 *
 * - Type a name and press Enter to create the tag (if new) and attach it.
 * - While typing, the created-tag cards below are filtered by name.
 * - Clicking a pill card toggles the tag for the current folder/item; the
 *   selected cards light up in the theme color.
 * - The red "×" on a card opens a confirm dialog that deletes the tag
 *   globally (pool + all folders/items).
 */
export default function TagSelector({ value, onChange }: TagSelectorProps) {
  const { t } = useTranslation()
  const { darkMode, themeColor } = useUIStore()

  // Pool of all tags ever created (global)
  const [pool, setPool] = useState<string[]>([])
  const [input, setInput] = useState('')
  const [confirmTag, setConfirmTag] = useState<string | null>(null)

  // Mobile keyboards: the "Next"/"Done" action key commits IME composition and
  // may move focus to the next field instead of firing a plain Enter keydown,
  // so antd's onPressEnter never fires and the tag is not created. Handle the
  // full keydown + composition sequence instead:
  //   - Enter while NOT composing -> create immediately (desktop / English)
  //   - Enter / key press while composing -> wait for compositionend, then create
  //     (Android Chrome commits the composition and sends no follow-up Enter)
  const composingRef = useRef(false)
  const pendingCreateRef = useRef(false)
  // Set when the user clicks inside the tag area (pills / delete ×) so the
  // blur fallback below doesn't create a tag they didn't mean to submit
  const ignoreBlurRef = useRef(false)

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const composing = e.nativeEvent.isComposing || e.keyCode === 229
    if (e.key === 'Enter' || e.keyCode === 13) {
      if (composing) {
        pendingCreateRef.current = true
      } else {
        // Stop the default "move focus to the next field" behaviour
        e.preventDefault()
        handleCreate()
      }
    } else if (composing) {
      // A physical key pressed while the IME is composing - on Android the
      // "Next"/"Done" action key arrives as keyCode 229 and commits the
      // composition with no follow-up Enter keydown.
      pendingCreateRef.current = true
    }
  }

  const handleCompositionStart = () => {
    composingRef.current = true
  }

  const handleCompositionEnd = () => {
    composingRef.current = false
    if (pendingCreateRef.current) {
      pendingCreateRef.current = false
      handleCreate()
    }
  }

  // Mobile fallback: some keyboards commit the composition and move focus to
  // the next field without a usable keydown/compositionend sequence. If the
  // input still holds text when focus leaves it, attach it as a tag.
  const handleBlur = () => {
    if (ignoreBlurRef.current) {
      ignoreBlurRef.current = false
      return
    }
    if (!composingRef.current && input.trim()) handleCreate()
  }

  const refreshPool = async () => {
    setPool(await getAllTags())
  }

  useEffect(() => {
    refreshPool()
  }, [])

  const query = input.trim().toLowerCase()
  const visibleTags = pool.filter(tag => tag.toLowerCase().includes(query))

  const handleCreate = async () => {
    const name = input.trim()
    if (!name) return
    if (!value.includes(name)) {
      if (!pool.includes(name)) {
        await createTag(name)
        await refreshPool()
      }
      onChange([...value, name])
    }
    setInput('')
  }

  const toggleTag = (tag: string) => {
    onChange(value.includes(tag) ? value.filter(x => x !== tag) : [...value, tag])
  }

  const handleDelete = async () => {
    if (!confirmTag) return
    const tag = confirmTag
    await deleteTag(tag)
    onChange(value.filter(x => x !== tag))
    setConfirmTag(null)
    await refreshPool()
    message.success(t('tag_deleted'))
  }

  return (
    <div>
      <Input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onCompositionStart={handleCompositionStart}
        onCompositionEnd={handleCompositionEnd}
        onBlur={handleBlur}
        placeholder={t('tag_input_placeholder')}
        allowClear
      />
      <div style={{ fontSize: '0.75rem', color: '#999', marginTop: '0.25rem' }}>
        {t('tag_input_hint')}
      </div>

      {/* Created tags: pill cards (semicircle ends, rectangle middle) */}
      <div
        onMouseDown={() => { ignoreBlurRef.current = true }}
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginTop: '0.5rem',
          maxHeight: '8.75rem',
          overflowY: 'auto'
        }}
      >
        {visibleTags.map(tag => {
          const selected = value.includes(tag)
          return (
            <span
              key={tag}
              onClick={() => toggleTag(tag)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.125rem',
                padding: '0.125rem 0.25rem 0.125rem 0.75rem',
                borderRadius: 999,
                border: `1px solid ${selected ? themeColor : darkMode ? '#3d3d3d' : '#d9d9d9'}`,
                background: selected ? themeColor : (darkMode ? '#262626' : '#fff'),
                color: selected ? '#fff' : (darkMode ? '#ccc' : '#555'),
                fontSize: '0.8125rem',
                cursor: 'pointer',
                userSelect: 'none',
                transition: 'all 0.2s ease'
              }}
            >
              {tag}
              <Tooltip title={t('tag_delete')}>
                <span
                  onClick={(e) => {
                    e.stopPropagation()
                    setConfirmTag(tag)
                  }}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '1.125rem',
                    height: '1.125rem',
                    borderRadius: '50%',
                    color: '#ff4d4f',
                    fontSize: '0.9375rem',
                    lineHeight: 1,
                    cursor: 'pointer',
                    fontWeight: 600
                  }}
                >
                  ×
                </span>
              </Tooltip>
            </span>
          )
        })}
        {pool.length === 0 && (
          <span style={{ fontSize: '0.75rem', color: '#999' }}>{t('tag_no_tags')}</span>
        )}
        {pool.length > 0 && visibleTags.length === 0 && (
          <span style={{ fontSize: '0.75rem', color: '#999' }}>{t('tag_no_match')}</span>
        )}
      </div>

      {/* Confirm tag deletion */}
      <Modal
        title={t('confirm_delete')}
        open={confirmTag !== null}
        onCancel={() => setConfirmTag(null)}
        onOk={handleDelete}
        okText={t('confirm_delete')}
        cancelText={t('cancel')}
        okButtonProps={{ danger: true }}
      >
        {confirmTag && <span>{t('delete_tag_confirm', { tag: confirmTag })}</span>}
      </Modal>
    </div>
  )
}
