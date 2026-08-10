import { Typography, Card, Button, Space, message, Divider, Alert } from 'antd'
import { useTranslation } from 'react-i18next'
import { useUIStore } from '../stores/uiStore'

const { Title, Text } = Typography

export default function SettingsPage() {
  const { t, i18n } = useTranslation()
  const {
    language,
    darkMode,
    themeColor,
    setLanguage,
    setThemeColor,
    setDarkMode,
    toggleDarkMode
  } = useUIStore()

  const colors = [
    '#0078d7', '#00a4ef', '#00b294', '#00cfc8',
    '#5c2d91', '#e3008c', '#d13438', '#ff8c00',
    '#107c10', '#7a7574', '#404040', '#8764b8'
  ]

  const handleLanguageChange = (lang: 'en' | 'zh') => {
    setLanguage(lang)
    i18n.changeLanguage(lang)
    message.success(t('success_update'))
  }

  const handleColorChange = (color: string) => {
    setThemeColor(color)
    message.success(t('success_update'))
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={2}>⚙️ {t('settings_title')}</Title>

      {/* Language Settings */}
      <Card 
        title={t('language_title')}
        style={{ marginBottom: '1.5rem' }}
      >
        <Space size="middle">
          <Button
            type={language === 'en' ? 'primary' : 'default'}
            onClick={() => handleLanguageChange('en')}
          >
            🇺🇸 {t('english')}
          </Button>
          <Button
            type={language === 'zh' ? 'primary' : 'default'}
            onClick={() => handleLanguageChange('zh')}
          >
            🇨🇳 {t('chinese')}
          </Button>
        </Space>
      </Card>

      {/* Password Protection Info */}
      <Card
        title={t('password_protection')}
        style={{ marginBottom: '1.5rem' }}
      >
        <Alert
          message={t('password_protection_title')}
          description={t('password_protection_desc')}
          type="info"
          showIcon
          style={{ marginBottom: '1rem' }}
        />
        <Text type="secondary">
          {t('password_protection_instruction')}
        </Text>
      </Card>

      {/* Appearance Settings */}
      <Card 
        title={t('display_title')}
        style={{ marginBottom: '1.5rem' }}
      >
        {/* Dark Mode */}
        <div style={{ marginBottom: '1.5rem' }}>
          <Title level={5} style={{ marginBottom: '1rem' }}>
            {t('display_mode')}
          </Title>
          <Space size="middle">
            <Button
              type={!darkMode ? 'primary' : 'default'}
              onClick={() => setDarkMode(false)}
            >
              ☀️ {t('light_mode')}
            </Button>
            <Button
              type={darkMode ? 'primary' : 'default'}
              onClick={() => setDarkMode(true)}
            >
              🌙 {t('dark_mode')}
            </Button>
          </Space>
        </div>

        <Divider />

        {/* Theme Color */}
        <div>
          <Title level={5} style={{ marginBottom: '1rem' }}>
            {t('theme_color')}
          </Title>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            {colors.map(color => (
              <Button
                key={color}
                type={themeColor === color ? 'primary' : 'default'}
                onClick={() => handleColorChange(color)}
                style={{
                  width: '3rem',
                  height: '3rem',
                  padding: 0,
                  background: color,
                  borderColor: color,
                }}
              />
            ))}
          </div>
        </div>
      </Card>

      {/* Data Management */}
      <Card title={`💾 ${t('data_management')}`}>
        <Space direction="vertical" size="middle">
          <Text>{t('export_import_desc')}</Text>
          <Space>
            <Button>📤 {t('export_data')}</Button>
            <Button>📥 {t('import_data')}</Button>
          </Space>
          <Text type="secondary">{t('coming_soon')}</Text>
        </Space>
      </Card>
    </div>
  )
}
