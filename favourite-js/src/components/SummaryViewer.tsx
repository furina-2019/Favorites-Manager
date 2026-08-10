import { Modal, Typography, Descriptions, Tag } from 'antd'
import { LinkOutlined, FileOutlined, FileTextOutlined, FolderOpenOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { Item } from '../core/database'

const { Title, Text, Paragraph } = Typography

interface SummaryViewerProps {
  item: Item | null
  open: boolean
  onClose: () => void
}

export default function SummaryViewer({ item, open, onClose }: SummaryViewerProps) {
  const { t } = useTranslation()

  if (!item) return null

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <FileTextOutlined />
          <span>{t('details_title')}</span>
        </div>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width={600}
    >
      {/* Item Info */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <div
            style={{
              width: '3rem',
              height: '3rem',
              borderRadius: 8,
              background: item.item_type === 'link' ? '#1890ff20' : '#52c41a20',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {item.item_type === 'link' ? (
              <LinkOutlined style={{ fontSize: '1.5rem', color: '#1890ff' }} />
            ) : (
              <FileOutlined style={{ fontSize: '1.5rem', color: '#52c41a' }} />
            )}
          </div>
          <div style={{ flex: 1 }}>
            <Title level={4} style={{ margin: 0 }}>
              {item.title || item.url || t('untitled')}
            </Title>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
              <Tag color={item.item_type === 'link' ? 'blue' : 'green'}>
                {item.item_type === 'link' ? t('type_link') : t('type_file')}
              </Tag>
              {item.category && <Tag>{item.category}</Tag>}
            </div>
          </div>
        </div>

        <Descriptions size="small" column={1} bordered>
          <Descriptions.Item label={t('item_url')}>
            <Text copyable={{ text: item.url || '' }} style={{ wordBreak: 'break-all' }}>
              {item.url}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label={t('item_created')}>
            {new Date(item.created_at).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>
      </div>

      {/* Summary Content - only when a summary exists; otherwise the
          dialog shows the item details above and nothing else */}
      {item.summary && (
        <div style={{ borderTop: '1px solid #e8e8e8', paddingTop: '1rem' }}>
          <Title level={5} style={{ marginBottom: '0.75rem' }}>
            📝 {t('summary_content')}
          </Title>
          <Paragraph
            style={{
              background: '#f5f5f5',
              padding: '1rem',
              borderRadius: 8,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontSize: '0.875rem',
              lineHeight: 1.8,
            }}
          >
            {item.summary}
          </Paragraph>
        </div>
      )}
    </Modal>
  )
}
