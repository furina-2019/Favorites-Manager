import { useState, useRef, type CSSProperties } from 'react'
import { Card, Typography, Tag, Button, Dropdown, Tooltip, Modal, Input, message } from 'antd'
import { 
  LinkOutlined, 
  FileOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  GlobalOutlined,
  FolderOpenOutlined,
  CopyOutlined,
  FileTextOutlined,
  LockOutlined,
  UnlockOutlined,
  KeyOutlined
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { Item, setItemPassword, removeItemPassword, incrementItemClicks } from '../core/database'
import { useUIStore } from '../stores/uiStore'
import { isItemUnlocked, setItemUnlocked, verifyPassword, hashPassword, generateSalt } from '../utils/password'
import { getPresetCover, isGradientCover, isPresetCover, proxiedCoverUrl } from '../utils/presetCovers'
import { highlightText } from '../utils/highlight'
import TagPills from './TagPills'

const { Text, Paragraph } = Typography

interface ItemCardProps {
  item: Item
  onEdit: (item: Item) => void
  onDelete: (item: Item) => void
  onViewSummary?: (item: Item) => void
  onPasswordChange?: () => void
  isSelected?: boolean
  onSelect?: (item: Item) => void
  /** Temporary highlight (e.g. when jumping to this item from the mind map) */
  highlighted?: boolean
  /** Current search query - used to highlight matched text and tags */
  searchQuery?: string
}

export default function ItemCard({ 
  item, 
  onEdit, 
  onDelete,
  onViewSummary,
  onPasswordChange,
  isSelected,
  onSelect,
  highlighted,
  searchQuery = ''
}: ItemCardProps) {
  const { t } = useTranslation()
  const { darkMode, themeColor } = useUIStore()

  const [showUnlockModal, setShowUnlockModal] = useState(false)
  const [showSetPasswordModal, setShowSetPasswordModal] = useState(false)
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false)
  const [showRemovePasswordModal, setShowRemovePasswordModal] = useState(false)
  const [password, setPassword] = useState('')
  const [unlockLoading, setUnlockLoading] = useState(false)
  const [passwordState, setPasswordState] = useState({
    hash: item.password_hash,
    salt: item.password_salt
  })
  const isMenuActionRef = useRef(false)

  const hasSummary = !!item.summary
  const isLocked = passwordState.hash && !isItemUnlocked('item', item.id)
  const hasPassword = !!passwordState.hash

  // Resolve the cover: preset -> solid color + category icon; legacy gradient -> render directly; else image
  const presetCover = getPresetCover(item.cover_path)
  const isPreset = isPresetCover(item.cover_path)
  const isGradient = isGradientCover(item.cover_path)
  const coverBackground = isLocked
    ? `${themeColor}20`
    : isPreset
      ? (presetCover?.color || '#8C8C8C')
      : isGradient
        ? item.cover_path!
        : item.cover_path
          ? `url(${proxiedCoverUrl(item.cover_path)}) center/cover no-repeat`
          : (item.item_type === 'link' ? `${themeColor}20` : '#52c41a20')
  const CoverIcon = presetCover?.icon
  const TypeIcon = item.item_type === 'link' ? LinkOutlined : FileOutlined

  const handleOpen = async () => {
    if (isLocked) {
      setShowUnlockModal(true)
      return
    }

    // Count the click so the home-page history ranking stays accurate
    incrementItemClicks(item.id)

    if (item.item_type === 'link' && item.url) {
      window.open(item.url, '_blank')
    } else if (item.item_type === 'file' && item.url) {
      try {
        const link = document.createElement('a')
        link.href = item.url
        link.download = item.url.split(/[\\/]/).pop() || 'file'
        link.click()
      } catch (err) {
        message.warning(t('file_open_failed'))
      }
    }
  }

  const handleUnlock = async () => {
    if (!password) {
      message.error(t('password_empty'))
      return
    }

    setUnlockLoading(true)
    try {
      const isCorrect = await verifyPassword(password, passwordState.hash!, passwordState.salt!)
      if (isCorrect) {
        setItemUnlocked('item', item.id)
        message.success(t('unlock'))
        setShowUnlockModal(false)
        setPassword('')
        
        // Open item after unlock
        incrementItemClicks(item.id)
        if (item.item_type === 'link' && item.url) {
          window.open(item.url, '_blank')
        } else if (item.item_type === 'file' && item.url) {
          try {
            const link = document.createElement('a')
            link.href = item.url
            link.download = item.url.split(/[\\/]/).pop() || 'file'
            link.click()
          } catch (err) {
            message.warning(t('file_open_failed'))
          }
        }
      } else {
        message.error(t('password_incorrect'))
        setPassword('')
      }
    } catch (err) {
      message.error(t('password_incorrect'))
    } finally {
      setUnlockLoading(false)
    }
  }

  const handleSetPassword = async () => {
    if (!password) return

    if (password.length < 6) {
      message.error(t('password_weak'))
      return
    }

    const salt = generateSalt()
    const hash = await hashPassword(password, salt)
    await setItemPassword(item.id, hash, salt)
    
    // Update local state immediately
    setPasswordState({ hash, salt })
    
    message.success(t('password_set'))
    setShowSetPasswordModal(false)
    setShowChangePasswordModal(false)
    setPassword('')
    onPasswordChange?.()
  }

  const handleRemovePassword = async () => {
    if (!password) return

    const isCorrect = await verifyPassword(password, passwordState.hash!, passwordState.salt!)
    if (!isCorrect) {
      message.error(t('password_incorrect'))
      return
    }

    await removeItemPassword(item.id)
    
    // Update local state immediately
    setPasswordState({ hash: null, salt: null })
    
    message.success(t('password_removed'))
    setShowRemovePasswordModal(false)
    setPassword('')
    onPasswordChange?.()
  }

  const handleCopyPath = async () => {
    if (isLocked) {
      setShowUnlockModal(true)
      return
    }

    if (item.url) {
      try {
        await navigator.clipboard.writeText(item.url)
        message.success(t('path_copied'))
      } catch {
        const textArea = document.createElement('textarea')
        textArea.value = item.url
        document.body.appendChild(textArea)
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
        message.success(t('path_copied'))
      }
    }
  }

  const handleViewSummary = async () => {
    if (isLocked) {
      setShowUnlockModal(true)
      return
    }

    // Always available - shows the item details (plus the summary when one exists)
    if (onViewSummary) {
      onViewSummary(item)
    }
  }

  const menuItems = [
    {
      key: 'open',
      icon: item.item_type === 'link' ? <GlobalOutlined /> : <FolderOpenOutlined />,
      label: item.item_type === 'link' ? t('open_link') : t('open_file'),
      onClick: () => {
        isMenuActionRef.current = true
        handleOpen()
      }
    },
    {
      key: 'copy',
      icon: <CopyOutlined />,
      label: t('copy_path'),
      onClick: () => {
        isMenuActionRef.current = true
        handleCopyPath()
      }
    },
    ...(onViewSummary ? [{
      key: 'view-details',
      icon: <FileTextOutlined />,
      label: t('view_details'),
      onClick: () => {
        isMenuActionRef.current = true
        handleViewSummary()
      }
    }] : []),
    {
      key: 'password',
      icon: <KeyOutlined />,
      label: hasPassword ? t('change_password') : t('set_password'),
      onClick: () => {
        isMenuActionRef.current = true
        hasPassword ? setShowChangePasswordModal(true) : setShowSetPasswordModal(true)
      }
    },
    ...(hasPassword ? [{
      key: 'remove-password',
      icon: <LockOutlined />,
      label: t('remove_password'),
      danger: true,
      onClick: () => {
        isMenuActionRef.current = true
        setShowRemovePasswordModal(true)
      }
    }] : []),
    { type: 'divider' as const },
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: t('context_edit'),
      onClick: () => {
        isMenuActionRef.current = true
        onEdit(item)
      }
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: t('context_delete'),
      danger: true,
      onClick: () => {
        isMenuActionRef.current = true
        onDelete(item)
      }
    }
  ]

  return (
    <>
       <Card
          style={{
            background: darkMode ? '#262626' : '#fff',
            borderColor: isLocked ? themeColor : highlighted ? themeColor : (darkMode ? '#3d3d3d' : '#e8e8e8'),
            borderWidth: isLocked || highlighted ? 2 : 1,
            borderRadius: 12,
            cursor: isLocked ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: highlighted ? `0 0 0 4px ${themeColor}55, 0 0 24px ${themeColor}44` : undefined,
            animation: highlighted ? 'item-highlight-pulse 0.9s ease-in-out 3' : undefined,
            opacity: isLocked ? 0.8 : 1,
            width: '100%', // Fill its grid cell (responsive)
            height: '100%', // Stretch to the grid row so cards in a row match
            display: 'flex',
            flexDirection: 'column',
            '--hl-color': themeColor,
          } as CSSProperties}
         styles={{ body: { padding: 0 } }} // Remove default padding to customize layout
         onClick={() => {
           if (isMenuActionRef.current) {
             isMenuActionRef.current = false
             return
           }
           if (!isLocked) {
             onSelect?.(item)
           }
         }}
       >
            {/* Cover Area (16:9 ratio) */}
            <div style={{ 
              width: '100%', 
              height: 'var(--item-cover-h, 8.4375rem)', 
              background: coverBackground,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              backgroundRepeat: 'no-repeat',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              borderTopLeftRadius: 12,
              borderTopRightRadius: 12,
              overflow: 'hidden'
            }}>
            {/* Locate badge (jumped from mind map) */}
            {highlighted && (
              <div
                style={{
                  position: 'absolute',
                  top: '0.5rem',
                  left: '0.5rem',
                  zIndex: 20,
                  background: themeColor,
                  color: '#fff',
                  borderRadius: 10,
                  padding: '0.125rem 0.625rem',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.35)',
                  pointerEvents: 'none'
                }}
              >
                {t('located')}
              </div>
            )}

            {/* Locked: show lock icon on a tinted background */}
            {isLocked && (
              <div style={{ fontSize: '3rem', color: themeColor }}>
                <LockOutlined />
              </div>
            )}
             {/* Preset cover: solid color + category icon */}
             {!isLocked && isPreset && CoverIcon && (
               <div style={{ fontSize: '3rem', color: 'rgba(255, 255, 255, 0.92)' }}>
                 <CoverIcon />
               </div>
             )}
             {/* No cover (or legacy gradient): show type icon */}
             {!isLocked && !isPreset && (!item.cover_path || isGradient) && (
               <div
                 style={{
                   fontSize: '3rem',
                   color: isGradient
                     ? 'rgba(255, 255, 255, 0.92)'
                     : (item.item_type === 'link' ? themeColor : '#52c41a')
                 }}
               >
                 <TypeIcon />
               </div>
             )}
             
             {/* Lock Badge */}
             {hasPassword && (
               <div
                 style={{
                   position: 'absolute',
                   bottom: '0.75rem',
                   right: '0.75rem',
                   width: '1.5rem',
                   height: '1.5rem',
                   borderRadius: '50%',
                   background: isLocked ? themeColor : '#52c41a',
                   display: 'flex',
                   alignItems: 'center',
                   justifyContent: 'center',
                 }}
               >
                 {isLocked ? (
                   <LockOutlined style={{ fontSize: '0.75rem', color: '#fff' }} />
                 ) : (
                   <UnlockOutlined style={{ fontSize: '0.75rem', color: '#fff' }} />
                 )}
               </div>
             )}

             {/* Tags: small pills overlaid at the bottom-left of the cover */}
             {!isLocked && (
               <div style={{ position: 'absolute', left: '0.5rem', bottom: '0.5rem', maxWidth: '75%' }}>
                 <TagPills tags={item.tags || []} highlight={searchQuery} variant="cover" max={3} />
               </div>
             )}
           </div>
           
           {/* Information Area */}
           <div style={{ 
             flex: 1, 
             padding: '0.75rem', 
             overflow: 'hidden',
             display: 'flex',
             flexDirection: 'column'
           }}>
             <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.25rem' }}>
               <Paragraph
                 ellipsis={{ rows: 1 }}
                 style={{
                   margin: 0,
                   color: darkMode ? '#fff' : '#333',
                   fontWeight: 500,
                   fontSize: '0.875rem',
                   flex: 1
                 }}
                 >
                   {isLocked ? t('item_locked') : highlightText(item.title || item.url || t('untitled'), searchQuery)}
                 </Paragraph>
                 
                 <Dropdown menu={{ items: menuItems }} trigger={['click']}>
                 <Tooltip title={t('more_options')}>
                   <Button 
                     type="text" 
                     icon={<MoreOutlined />} 
                     size="small"
                     onClick={(e) => e.stopPropagation()}
                   />
                 </Tooltip>
               </Dropdown>
             </div>
 
             <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
               <Tag 
                 color={item.item_type === 'link' ? 'blue' : 'green'}
                 style={{ margin: 0 }}
               >
                 {item.item_type === 'link' ? t('type_link') : t('type_file')}
               </Tag>
               
               {item.category && (
                 <Tag className="item-card-cat" style={{ margin: 0 }}>{highlightText(t(`category_${item.category.toLowerCase()}`) || item.category, searchQuery)}</Tag>
               )}
               
               {!isLocked && hasSummary && (
                 <Tooltip title={t('has_summary')}>
                   <FileTextOutlined style={{ color: themeColor }} />
                 </Tooltip>
               )}
             </div>
 
             <div
               className="item-card-detail"
               style={{ 
                 flex: 1, 
                 marginTop: 'auto',
                 minHeight: 40
               }}
             >
               {!isLocked && (
                 <>
                   <Text 
                     type="secondary" 
                     ellipsis
                     style={{ 
                       fontSize: '0.75rem', 
                       display: 'block', 
                       marginBottom: '0.125rem',
                       color: darkMode ? '#888' : '#999'
                     }}
                   >
                     {highlightText(item.url || '', searchQuery)}
                   </Text>
 
                   <Text 
                     type="secondary" 
                     style={{ 
                       fontSize: '0.6875rem', 
                       display: 'block', 
                       marginBottom: '0.125rem',
                       color: darkMode ? '#666' : '#bbb'
                     }}
                   >
                     {new Date(item.created_at).toLocaleString()}
                   </Text>
                 </>
               )}
             </div>
             
             {/* Action Buttons - Bottom */}
             <div style={{ 
               display: 'flex', 
               justifyContent: 'space-between', 
               alignItems: 'center',
               marginTop: '0.5rem'
             }}>
               <div style={{ display: 'flex', gap: '0.25rem' }}>
                 <Tooltip title={isLocked ? t('unlock') : (item.item_type === 'link' ? t('open_link') : t('open_file'))}>
                   <Button
                     size="small"
                     icon={isLocked ? <LockOutlined /> : (item.item_type === 'link' ? <GlobalOutlined /> : <FolderOpenOutlined />)}
                     onClick={(e) => {
                       e.stopPropagation()
                       handleOpen()
                     }}
                   />
                 </Tooltip>
                 
                 <Tooltip title={t('copy_path')}>
                   <Button
                     size="small"
                     icon={<CopyOutlined />}
                     onClick={(e) => {
                       e.stopPropagation()
                       handleCopyPath()
                     }}
                   />
                 </Tooltip>
               </div>
               
               {!isLocked && onViewSummary && (
                 <Tooltip title={t('view_details')}>
                   <Button
                     size="small"
                     icon={<FileTextOutlined />}
                     onClick={(e) => {
                       e.stopPropagation()
                       handleViewSummary()
                     }}
                   />
                 </Tooltip>
               )}
             </div>
           </div>
         </Card>

        {/* Unlock Modal */}
        <Modal
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <LockOutlined />
              <span>{t('unlock')}</span>
            </div>
          }
          open={showUnlockModal}
          onCancel={() => {
            setShowUnlockModal(false)
            setPassword('')
          }}
          footer={[
            <Button key="cancel" onClick={() => {
              setShowUnlockModal(false)
              setPassword('')
            }}>
              {t('cancel')}
            </Button>,
            <Button 
              key="unlock" 
              type="primary" 
              onClick={handleUnlock}
              loading={unlockLoading}
            >
              {t('unlock')}
            </Button>
          ]}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ textAlign: 'center' }}>
              <Text>{t('item_locked')}</Text>
            </div>
            <Input.Password
              size="large"
              placeholder={t('password')}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onPressEnter={handleUnlock}
              autoFocus
            />
          </div>
        </Modal>

        {/* Set Password Modal */}
        <Modal
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <KeyOutlined />
              <span>{t('set_password')}</span>
            </div>
          }
          open={showSetPasswordModal}
          onCancel={() => {
            setShowSetPasswordModal(false)
            setPassword('')
          }}
          onOk={handleSetPassword}
          okText={t('confirm')}
          cancelText={t('cancel')}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Input.Password
              placeholder={t('new_password')}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoFocus
            />
            <Text type="secondary" style={{ fontSize: '0.75rem' }}>
              {t('password_weak')}
            </Text>
          </div>
        </Modal>

        {/* Change Password Modal */}
        <Modal
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <KeyOutlined />
              <span>{t('change_password')}</span>
            </div>
          }
          open={showChangePasswordModal}
          onCancel={() => {
            setShowChangePasswordModal(false)
            setPassword('')
          }}
          onOk={handleSetPassword}
          okText={t('confirm')}
          cancelText={t('cancel')}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Input.Password
              placeholder={t('new_password')}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoFocus
            />
            <Text type="secondary" style={{ fontSize: '0.75rem' }}>
              {t('password_weak')}
            </Text>
          </div>
        </Modal>

        {/* Remove Password Modal */}
        <Modal
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <LockOutlined />
              <span>{t('remove_password')}</span>
            </div>
          }
          open={showRemovePasswordModal}
          onCancel={() => {
            setShowRemovePasswordModal(false)
            setPassword('')
          }}
          onOk={handleRemovePassword}
          okText={t('confirm')}
          cancelText={t('cancel')}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ textAlign: 'center' }}>
              <Text>{t('remove_password_confirm')}</Text>
            </div>
            <Input.Password
              placeholder={t('password')}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onPressEnter={handleRemovePassword}
              autoFocus
            />
          </div>
        </Modal>
      </>
  )
}