import { Typography, Tooltip } from 'antd'
import { LinkOutlined, FileOutlined, LockOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { Item } from '../core/database'
import { useUIStore } from '../stores/uiStore'
import { getPresetCover, isGradientCover, isPresetCover, proxiedCoverUrl } from '../utils/presetCovers'

const { Text } = Typography

interface ItemMiniCardProps {
  item: Item
  /** Whether the item (or its parent folder) is password locked */
  locked?: boolean
  onOpen?: (item: Item) => void
}

/**
 * Compact card used by the "Recent" / "History" rows on the home page.
 * Shows a small cover strip + the title, and forwards clicks to onOpen.
 */
export default function ItemMiniCard({ item, locked = false, onOpen }: ItemMiniCardProps) {
  const { t } = useTranslation()
  const { darkMode, themeColor } = useUIStore()

  const preset = getPresetCover(item.cover_path)
  const isPreset = isPresetCover(item.cover_path)
  const isGradient = isGradientCover(item.cover_path)
  const CoverIcon = preset?.icon
  const TypeIcon = item.item_type === 'link' ? LinkOutlined : FileOutlined
  const title = item.title || item.url || t('untitled')

  // Image covers (photo / data URL) render the image itself; legacy gradient
  // strings and presets fall back to a plain icon instead.
  const hasImage = !!item.cover_path && !isPreset && !isGradient
  const coverBg = isPreset
    ? (preset?.color || '#8C8C8C')
    : hasImage
      ? `url(${proxiedCoverUrl(item.cover_path)}) center/cover no-repeat`
      : (item.item_type === 'link' ? `${themeColor}20` : '#52c41a20')

  return (
    <Tooltip title={title}>
      <div
        onClick={() => onOpen?.(item)}
        style={{
          flexShrink: 0,
          width: '10rem',
          borderRadius: 10,
          border: `1px solid ${darkMode ? '#3d3d3d' : '#e8e8e8'}`,
          background: darkMode ? '#262626' : '#fff',
          overflow: 'hidden',
          cursor: 'pointer',
          userSelect: 'none',
          transition: 'all 0.2s ease',
        }}
      >
        <div
          style={{
            height: '2.75rem',
            background: coverBg,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
          }}
        >
          {locked ? (
            <LockOutlined style={{ fontSize: '1.125rem', color: themeColor }} />
          ) : isPreset && CoverIcon ? (
            <CoverIcon style={{ fontSize: '1.25rem', color: 'rgba(255, 255, 255, 0.92)' }} />
          ) : !hasImage ? (
            <TypeIcon
              style={{
                fontSize: '1.25rem',
                color: item.item_type === 'link' ? themeColor : '#52c41a',
              }}
            />
          ) : null}
        </div>
        <div style={{ padding: '0.5rem' }}>
          <Text
            ellipsis={{ tooltip: title }}
            style={{
              display: 'block',
              fontSize: '0.75rem',
              fontWeight: 500,
              color: darkMode ? '#fff' : '#333',
            }}
          >
            {title}
          </Text>
        </div>
      </div>
    </Tooltip>
  )
}
