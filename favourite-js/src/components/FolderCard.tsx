import { useState, useRef, type MouseEvent } from 'react'
import { Card, Typography, Badge, Tooltip, Button, Dropdown, Modal, Input, message } from 'antd'
import { 
  FolderOpenOutlined, 
  LockOutlined, 
  UnlockOutlined,
  MoreOutlined,
  KeyOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Folder, setFolderPassword, removeFolderPassword } from '../core/database'
import { useUIStore } from '../stores/uiStore'
import { isItemUnlocked, setItemUnlocked, verifyPassword, hashPassword, generateSalt } from '../utils/password'
import { setFolderOpenCenter } from '../utils/pageTransition'
import { highlightText } from '../utils/highlight'
import TagPills from './TagPills'

const { Text, Paragraph } = Typography

interface FolderCardProps {
  folder: Folder
  onPasswordChange?: () => void
  /** Current search query - used to highlight matched text and tags */
  searchQuery?: string
}

export default function FolderCard({ folder, onPasswordChange, searchQuery = '' }: FolderCardProps) {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { darkMode, themeColor } = useUIStore()
  
  const [showUnlockModal, setShowUnlockModal] = useState(false)
  const [showSetPasswordModal, setShowSetPasswordModal] = useState(false)
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false)
  const [showRemovePasswordModal, setShowRemovePasswordModal] = useState(false)
  const [password, setPassword] = useState('')
  const [unlockLoading, setUnlockLoading] = useState(false)
  const [passwordState, setPasswordState] = useState({
    hash: folder.password_hash,
    salt: folder.password_salt
  })
  const isMenuActionRef = useRef(false)

  const isLocked = passwordState.hash && !isItemUnlocked('folder', folder.id)
  const hasPassword = !!passwordState.hash

  const handleClick = (e?: MouseEvent<HTMLDivElement>) => {
    if (isMenuActionRef.current) {
      isMenuActionRef.current = false
      return
    }

    // Remember where this card is so the items page can expand from it
    if (e && e.currentTarget) {
      const rect = e.currentTarget.getBoundingClientRect()
      setFolderOpenCenter(rect.left + rect.width / 2, rect.top + rect.height / 2)
    }
    
    if (passwordState.hash && !isItemUnlocked('folder', folder.id)) {
      setShowUnlockModal(true)
    } else {
      navigate(`/folder/${folder.id}`)
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
        setItemUnlocked('folder', folder.id)
        message.success(t('unlock'))
        setShowUnlockModal(false)
        setPassword('')
        navigate(`/folder/${folder.id}`)
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
    await setFolderPassword(folder.id, hash, salt)
    
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

    await removeFolderPassword(folder.id)
    
    // Update local state immediately
    setPasswordState({ hash: null, salt: null })
    
    message.success(t('password_removed'))
    setShowRemovePasswordModal(false)
    setPassword('')
    onPasswordChange?.()
  }

  const menuItems = [
    {
      key: 'password',
      icon: <KeyOutlined />,
      label: hasPassword ? t('change_password') : t('set_password'),
      onClick: () => {
        isMenuActionRef.current = true
        hasPassword ? setShowChangePasswordModal(true) : setShowSetPasswordModal(true)
      }
    },
    hasPassword ? {
      key: 'remove-password',
      icon: <LockOutlined />,
      label: t('remove_password'),
      danger: true,
      onClick: () => {
        isMenuActionRef.current = true
        setShowRemovePasswordModal(true)
      }
    } : null
  ].filter(Boolean)

  return (
    <>
      <Card
        hoverable={!isLocked}
        onClick={(e) => handleClick(e)}
        style={{
          background: darkMode ? '#262626' : '#fff',
          borderColor: isLocked ? themeColor : (darkMode ? '#3d3d3d' : '#e8e8e8'),
          borderWidth: isLocked ? 2 : 1,
          borderRadius: 12,
          cursor: isLocked ? 'not-allowed' : 'pointer',
          transition: 'all 0.3s ease',
          opacity: isLocked ? 0.8 : 1
        }}
        styles={{
          body: { padding: '1rem' }
        }}
      >
        <div 
          style={{ 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.75rem',
            position: 'relative'
          }}
        >
          {/* More Options Button */}
          <Dropdown menu={{ items: menuItems }} trigger={['click']}>
            <Tooltip title={t('more_options')}>
              <Button
                type="text"
                icon={<MoreOutlined />}
                size="small"
                style={{ position: 'absolute', top: 0, right: 0 }}
                onClick={(e) => e.stopPropagation()}
              />
            </Tooltip>
          </Dropdown>

          {/* Folder Icon with Lock Indicator */}
          <div
            style={{
              width: '4rem',
              height: '4rem',
              borderRadius: 12,
              background: isLocked 
                ? `${themeColor}20` 
                : `linear-gradient(135deg, ${themeColor}20, ${themeColor}40)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative'
            }}
          >
            {isLocked ? (
              <LockOutlined 
                style={{ fontSize: '2rem', color: themeColor }} 
              />
            ) : (
              <FolderOpenOutlined 
                style={{ fontSize: '2rem', color: themeColor }} 
              />
            )}
            
            {/* Lock Badge */}
            {hasPassword && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '-0.25rem',
                  right: '-0.25rem',
                  width: '1.25rem',
                  height: '1.25rem',
                  borderRadius: '50%',
                  background: isLocked ? themeColor : '#52c41a',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {isLocked ? (
                  <LockOutlined style={{ fontSize: '0.625rem', color: '#fff' }} />
                ) : (
                  <UnlockOutlined style={{ fontSize: '0.625rem', color: '#fff' }} />
                )}
              </div>
            )}
          </div>

          {/* Folder Name */}
          <Paragraph 
            ellipsis={{ rows: 2 }}
            style={{ 
              margin: 0, 
              textAlign: 'center',
              color: darkMode ? '#fff' : '#333',
              fontWeight: 500,
              fontSize: '0.875rem'
            }}
          >
            {highlightText(folder.name, searchQuery)}
          </Paragraph>

          {/* Item Count */}
          <Badge 
            count={folder.item_count || 0} 
            style={{ backgroundColor: themeColor }}
          />

          {/* Tags */}
          {folder.tags && folder.tags.length > 0 && (
            <TagPills tags={folder.tags} highlight={searchQuery} variant="theme" max={5} center />
          )}

          {/* Created Date */}
          <Text 
            className="folder-card-date"
            type="secondary" 
            style={{ fontSize: '0.6875rem' }}
          >
            {new Date(folder.created_at).toLocaleDateString()}
          </Text>
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
            <Text>{t('folder_locked')}</Text>
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
          />            <Text type="secondary" style={{ fontSize: '0.75rem' }}>
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
          />            <Text type="secondary" style={{ fontSize: '0.75rem' }}>
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
