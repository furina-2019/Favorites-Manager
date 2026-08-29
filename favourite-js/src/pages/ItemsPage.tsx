import { Tooltip, Typography, Button, Input, Space, Dropdown, Empty, Spin, Checkbox, message, Upload, Modal, Grid } from 'antd'
import type { MenuProps } from 'antd'
import { 
  ArrowLeftOutlined,
  PlusOutlined,
  SearchOutlined,
  DeleteOutlined,
  FilterOutlined,
  ClearOutlined,
  UploadOutlined,
  FolderOpenOutlined,
  InboxOutlined,
  ApartmentOutlined
} from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useEffect, useState, useCallback } from 'react'
import { useDBStore } from '../stores/dbStore'
import { useUIStore } from '../stores/uiStore'
import ItemCard from '../components/ItemCard'
import ItemDialog from '../components/ItemDialog'
import SummaryViewer from '../components/SummaryViewer'
import MindMapView from '../components/MindMapView'
import { Item } from '../core/database'
import type { UploadProps } from 'antd'

const { Title, Text } = Typography

export default function ItemsPage() {
  const { id } = useParams<{ id: string }>()
  const folderId = id ? parseInt(id) : null
  const navigate = useNavigate()
  const { t } = useTranslation()

  const {
    items,
    folders,
    loading,
    error,
    loadItems,
    loadFolders,
    addItem,
    updateItem,
    removeItem,
    removeItems,
    setCurrentFolder
  } = useDBStore()
  const { darkMode, language } = useUIStore()
  const screens = Grid.useBreakpoint()
  // Below the md breakpoint everything collapses to icon-only controls
  const isMobile = screens.md === false
  
  const currentFolder = folders.find(f => f.id === folderId)
  const currentFolderName = currentFolder?.name || t('folder_placeholder')

  const [searchQuery, setSearchQuery] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<Item | null>(null)
  const [selectedItems, setSelectedItems] = useState<number[]>([])
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [isDragOver, setIsDragOver] = useState(false)
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [summaryViewerOpen, setSummaryViewerOpen] = useState(false)
  const [viewingSummaryItem, setViewingSummaryItem] = useState<Item | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'mindmap'>('list')
  // Mobile: the search bar collapses to an icon that opens an inline input
  const [searchOpen, setSearchOpen] = useState(false)
  // Item jumped to from the mind map: { id, ts } - ts guarantees a fresh
  // effect run even when the same item is clicked again
  const [highlightedItem, setHighlightedItem] = useState<{ id: number; ts: number } | null>(null)

  useEffect(() => {
    if (folderId) {
      loadItems(folderId)
    }
    loadFolders()
  }, [folderId, loadItems, loadFolders])

  // Jump-to-item from the mind map: switch to list view, scroll to the card
  // and auto-clear the highlight after a short while
  useEffect(() => {
    if (viewMode !== 'list' || !highlightedItem) return
    const scrollTimer = setTimeout(() => {
      document.getElementById(`item-card-${highlightedItem.id}`)
        ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 150)
    const clearTimer = setTimeout(() => setHighlightedItem(null), 2800)
    return () => {
      clearTimeout(scrollTimer)
      clearTimeout(clearTimer)
    }
  }, [viewMode, highlightedItem])

  const handleMindMapItemClick = (item: Item) => {
    setViewMode('list')
    setHighlightedItem({ id: item.id, ts: Date.now() })
  }

  const categories: string[] = [...new Set(items.map(item => item.category).filter((cat): cat is string => !!cat))]

  const filteredItems = items.filter(item => {
    const lowerQuery = searchQuery.toLowerCase()
    const matchesSearch = !searchQuery || 
      item.title?.toLowerCase().includes(lowerQuery) ||
      item.url?.toLowerCase().includes(lowerQuery) ||
      item.category?.toLowerCase().includes(lowerQuery) ||
      item.tags?.some(tag => tag.toLowerCase().includes(lowerQuery))
    
    const matchesCategory = !filterCategory || item.category === filterCategory
    
    return matchesSearch && matchesCategory
  })

  const handleBack = () => {
    navigate(-1)
  }

  const handleAddItem = () => {
    setEditingItem(null)
    setDialogOpen(true)
  }

  const handleEditItem = (item: Item) => {
    setEditingItem(item)
    setDialogOpen(true)
  }

  const handleDeleteItem = async (item: Item) => {
    if (window.confirm(t('delete_item_confirm'))) {
      await removeItem(item.id)
      message.success(t('success_delete'))
    }
  }

  const handleViewSummary = (item: Item) => {
    setViewingSummaryItem(item)
    setSummaryViewerOpen(true)
  }

    const handleSubmit = async (data: {
      itemType: 'link' | 'file'
      title: string
      url: string
      category: string
      summary: string
      coverPath?: string
      tags: string[]
    }) => {
      try {
        if (editingItem) {
          await updateItem(
            editingItem.id,
            data.title,
            data.url,
            data.category,
            data.coverPath || '',
            data.summary,
            data.tags
          )
          message.success(t('success_update'))
        } else if (folderId) {
          await addItem(
            folderId,
            data.itemType,
            data.title,
            data.url,
            data.category,
            data.coverPath || '',
            data.summary,
            data.tags
          )
          message.success(t('success_add'))
        }
      } catch (err) {
        message.error(t('error_occurred'))
      }
    }

  const handleSelectItem = (item: Item) => {
    setSelectedItems(prev => 
      prev.includes(item.id)
        ? prev.filter(id => id !== item.id)
        : [...prev, item.id]
    )
  }

  const handleBulkDelete = async () => {
    if (selectedItems.length === 0) {
      message.warning(t('no_selected'))
      return
    }

    if (window.confirm(t('batch_delete_confirm', { count: selectedItems.length }))) {
      await removeItems(selectedItems)
      setSelectedItems([])
      message.success(t('success_delete'))
    }
  }

  const handleClearSelection = () => {
    setSelectedItems([])
  }

  const handleDrop = useCallback(async (files: FileList | null) => {
    if (!files || !folderId) return

    const fileArray = Array.from(files)
    let successCount = 0

    for (const file of fileArray) {
      try {
        await addItem(
          folderId,
          'file',
          file.name,
          file.name,
          '',
          '',
          file.type || ''
        )
        successCount++
      } catch (err) {
        console.error('Failed to add file:', file.name, err)
      }
    }

    if (successCount > 0) {
      message.success(t('files_added', { count: successCount }))
    }
  }, [folderId, addItem, t])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }, [])

  const handleDropEvent = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    handleDrop(e.dataTransfer.files)
  }, [handleDrop])

  const uploadProps: UploadProps = {
    multiple: true,
    showUploadList: false,
    beforeUpload: async (file) => {
      if (folderId) {
        try {
          await addItem(
            folderId,
            'file',
            file.name,
            file.name,
            '',
            '',
            file.type || ''
          )
        } catch (err) {
          console.error('Failed to add file:', file.name, err)
        }
      }
      return false
    },
    onChange(info) {
      if (info.file.status === 'done') {
        message.success(`${info.file.name} ${t('file_added')}`)
      }
    },
  }

  const filterMenuItems: MenuProps['items'] = [
    {
      key: 'all',
      label: t('filter_all'),
      onClick: () => setFilterCategory('')
    },
    { type: 'divider' },
    ...categories.map(cat => ({
      key: cat,
      label: t(`category_${cat.toLowerCase()}`) || cat,
      onClick: () => setFilterCategory(cat)
    }))
  ]

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDropEvent}
      style={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}
    >
      {/* Drag Overlay */}
      {isDragOver && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 120, 215, 0.1)',
            border: '3px dashed #0078d7',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none'
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <InboxOutlined style={{ fontSize: '4rem', color: '#0078d7', marginBottom: '1rem' }} />
            <Title level={3} style={{ color: '#0078d7' }}>
              {t('drop_files_here')}
            </Title>
          </div>
        </div>
      )}

      {/* Toolbar: fixed at the top of the items page, never scrolls away */}
      <div
        style={{
          flexShrink: 0,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 'var(--page-gap)',
          padding: 'var(--page-pad)',
          background: darkMode ? '#1a1a1a' : '#f5f5f5',
          borderBottom: `1px solid ${darkMode ? '#303030' : '#e0e0e0'}`,
          zIndex: 10
        }}
      >
        <Space size="middle">
          <Tooltip title={t('back')}>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={handleBack}
            />
          </Tooltip>
          <div>
            <Title level={3} style={{ margin: 0 }}>
              📁 {currentFolderName}
            </Title>
            <Text type="secondary">
              {filteredItems.length} {t('items')}
              {selectedItems.length > 0 && ` (${selectedItems.length} ${t('selected')})`}
            </Text>
          </div>
        </Space>

        <Space>
          {selectedItems.length > 0 && (
            <>
              <Tooltip title={t('clear_selection')}>
                <Button 
                  icon={<ClearOutlined />} 
                  onClick={handleClearSelection}
                />
              </Tooltip>
              <Tooltip title={t('delete_selected')}>
                <Button 
                  danger 
                  icon={<DeleteOutlined />} 
                  onClick={handleBulkDelete}
                />
              </Tooltip>
            </>
          )}
          
          {isMobile ? (
            <Tooltip title={t('item_search_placeholder')}>
              <Button
                icon={<SearchOutlined />}
                onClick={() => setSearchOpen(true)}
              />
            </Tooltip>
          ) : (
            <Input
              placeholder={t('item_search_placeholder')}
              prefix={<SearchOutlined />}
              allowClear
              style={{ width: '15rem' }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          )}

          <Tooltip title={viewMode === 'list' ? t('mind_map') : t('list_view')}>
            <Button
              icon={<ApartmentOutlined />}
              onClick={() => setViewMode(mode => (mode === 'list' ? 'mindmap' : 'list'))}
            >
              {!isMobile && (viewMode === 'list' ? t('mind_map') : t('list_view'))}
            </Button>
          </Tooltip>

          {categories.length > 0 && (
            <Tooltip title={t('filter_by_category')}>
              <Dropdown menu={{ items: filterMenuItems }}>
                <Button icon={<FilterOutlined />}>
                  {!isMobile && (filterCategory ? (t(`category_${filterCategory.toLowerCase()}`) || filterCategory) : t('filter_all'))}
                </Button>
              </Dropdown>
            </Tooltip>
          )}

          <Tooltip title={t('add_files')}>
            <Button 
              icon={<UploadOutlined />}
              onClick={() => setImportModalOpen(true)}
            />
          </Tooltip>

          <Tooltip title={t('add_item')}>
            <Button
              type="primary"
              icon={language === 'en' ? undefined : <PlusOutlined />}
              onClick={handleAddItem}
            />
          </Tooltip>
        </Space>

        {/* Mobile: tapping the search icon reveals an inline search box */}
        {isMobile && searchOpen && (
          <div style={{ width: '100%' }}>
            <Input
              autoFocus
              placeholder={t('item_search_placeholder')}
              prefix={<SearchOutlined />}
              allowClear
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onBlur={() => setSearchOpen(false)}
            />
          </div>
        )}
      </div>

      {/* Scrollable content: the toolbar above stays put while this area scrolls.
          The mind map gets its own contained area so dragging pans BOTH axes
          inside it (vertical wheel scroll no longer fights the page scroll). */}
      {viewMode === 'mindmap' ? (
        <div
          key="mindmap"
          className="view-switch"
          style={{ flex: 1, minHeight: 0, overflow: 'hidden', padding: 'var(--page-pad)' }}
        >
          {error && (
            <div style={{ color: '#ff4d4f', marginBottom: 16 }}>{error}</div>
          )}
          {loading && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <Spin size="large" />
            </div>
          )}
          {!loading && items.length > 0 && filteredItems.length === 0 && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <Empty description={t('search_no_results')} />
            </div>
          )}
          {!loading && (items.length === 0 || filteredItems.length > 0) && (
            <div style={{ height: '100%' }}>
              <MindMapView
                folder={currentFolder}
                items={filteredItems}
                onItemClick={handleMindMapItemClick}
                onViewSummary={handleViewSummary}
                searchQuery={searchQuery}
              />
            </div>
          )}
        </div>
      ) : (
        <div
          key="list"
          className="view-switch"
          style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '0 var(--page-pad) var(--page-pad)' }}
        >
          {error && (
            <div style={{ color: '#ff4d4f', marginBottom: 16 }}>{error}</div>
          )}
          {loading && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <Spin size="large" />
            </div>
          )}
          {!loading && items.length === 0 && (
            <div style={{ textAlign: 'center', padding: '5rem' }}>
              <Empty
                description={t('no_items')}
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Space>
                  <Tooltip title={t('add_item')}>
                    <Button type="primary" icon={language === 'en' ? undefined : <PlusOutlined />} onClick={handleAddItem}>
                      {t('add_item_btn')}
                    </Button>
                  </Tooltip>
                  <Tooltip title={t('add_files')}>
                    <Button icon={<UploadOutlined />} onClick={() => setImportModalOpen(true)}>
                      {t('upload_files')}
                    </Button>
                  </Tooltip>
                </Space>
              </Empty>
            </div>
          )}
          {!loading && filteredItems.length > 0 && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: isMobile ? 'repeat(2, minmax(0, 1fr))' : 'repeat(auto-fill, minmax(min(280px, 100%), 1fr))',
                gap: isMobile ? '0.75rem' : '1.5rem'
              }}
            >
              {filteredItems.map(item => (
                <div key={item.id} id={`item-card-${item.id}`} style={{ position: 'relative' }}>
                  {selectedItems.includes(item.id) && (
                    <Checkbox
                      checked={selectedItems.includes(item.id)}
                      onChange={() => handleSelectItem(item)}
                      style={{ position: 'absolute', top: 8, left: 8, zIndex: 10 }}
                    />
                  )}
                  <ItemCard
                    item={item}
                    onEdit={handleEditItem}
                    onDelete={handleDeleteItem}
                    onViewSummary={handleViewSummary}
                    isSelected={selectedItems.includes(item.id)}
                    onSelect={handleSelectItem}
                    highlighted={highlightedItem?.id === item.id}
                    searchQuery={searchQuery}
                  />
                </div>
              ))}
            </div>
          )}
          {!loading && items.length > 0 && filteredItems.length === 0 && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <Empty description={t('search_no_results')} />
            </div>
          )}
        </div>
      )}

      {/* Item Dialog */}
      <ItemDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false)
          setEditingItem(null)
        }}
        onSubmit={handleSubmit}
        item={editingItem}
      />

      {/* Summary Viewer */}
      <SummaryViewer
        item={viewingSummaryItem}
        open={summaryViewerOpen}
        onClose={() => {
          setSummaryViewerOpen(false)
          setViewingSummaryItem(null)
        }}
      />

      {/* Import Files Modal */}
      <Modal
        title={t('add_files')}
        open={importModalOpen}
        onCancel={() => setImportModalOpen(false)}
        footer={null}
        width={500}
      >
        <Upload.Dragger {...uploadProps} multiple>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">{t('click_or_drag_files')}</p>
          <p className="ant-upload-hint">
            {t('file_upload_hint')}
          </p>
        </Upload.Dragger>
      </Modal>
    </div>
  )
}
