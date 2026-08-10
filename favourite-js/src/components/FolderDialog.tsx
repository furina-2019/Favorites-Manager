import { Modal, Form, Input, Button } from 'antd'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import TagSelector from './TagSelector'

interface FolderDialogProps {
  open: boolean
  onClose: () => void
  onSubmit: (name: string, tags: string[]) => void
  title?: string
  initialName?: string
  initialTags?: string[]
}

export default function FolderDialog({
  open,
  onClose,
  onSubmit,
  title,
  initialName = '',
  initialTags = []
}: FolderDialogProps) {
  const [form] = Form.useForm()
  const { t } = useTranslation()
  const [tags, setTags] = useState<string[]>([])

  useEffect(() => {
    if (open) {
      form.setFieldsValue({ name: initialName })
      setTags(initialTags)
    } else {
      form.resetFields()
      setTags([])
    }
  }, [open, initialName, initialTags, form])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      onSubmit(values.name, tags)
      onClose()
    } catch (err) {
      // Validation failed
    }
  }

  const dialogTitle = title || (initialName ? t('rename_folder_dialog_title') : t('add_folder_dialog_title'))

  return (
    <Modal
      title={dialogTitle}
      open={open}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>
          {t('cancel')}
        </Button>,
        <Button key="submit" type="primary" onClick={handleSubmit}>
          {t('confirm')}
        </Button>
      ]}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label={t('add_folder_dialog_label')}
          rules={[
            { required: true, message: t('error') },
            { max: 100, message: 'Max 100 characters' }
          ]}
        >
          <Input 
            placeholder={t('folder_search_placeholder')}
            autoFocus
          />
        </Form.Item>

        <Form.Item label={t('tags')} style={{ marginBottom: 0 }}>
          <TagSelector value={tags} onChange={setTags} />
        </Form.Item>
      </Form>
    </Modal>
  )
}
