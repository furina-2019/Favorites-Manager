// Persistent storage layer.
// On PC (Electron): writes a JSON file to AppData/Local/Favourites-Manager.
// On Android / Web: uses the built-in storage.
import { storage } from '../utils/storage'

export interface Folder {
  id: number
  name: string
  created_at: string
  item_count?: number
  password_hash?: string | null
  password_salt?: string | null
  tags?: string[]
}

export interface Item {
  id: number
  folder_id: number
  item_type: 'link' | 'file'
  title: string | null
  url: string | null
  category: string | null
  cover_path: string | null
  summary: string | null
  created_at: string
  password_hash?: string | null
  password_salt?: string | null
  tags?: string[]
  click_count?: number
}

const STORAGE_KEYS = {
  FOLDERS: 'favourite_folders',
  ITEMS: 'favourite_items',
  TAGS: 'favourite_tags',
  NEXT_FOLDER_ID: 'favourite_next_folder_id',
  NEXT_ITEM_ID: 'favourite_next_item_id'
}

// Initialize storage with defaults if empty
function initStorage(): void {
  if (!storage.getItem(STORAGE_KEYS.FOLDERS)) {
    storage.setItem(STORAGE_KEYS.FOLDERS, JSON.stringify([]))
  }
  if (!storage.getItem(STORAGE_KEYS.ITEMS)) {
    storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify([]))
  }
  if (!storage.getItem(STORAGE_KEYS.NEXT_FOLDER_ID)) {
    storage.setItem(STORAGE_KEYS.NEXT_FOLDER_ID, '1')
  }
  if (!storage.getItem(STORAGE_KEYS.NEXT_ITEM_ID)) {
    storage.setItem(STORAGE_KEYS.NEXT_ITEM_ID, '1')
  }
  if (!storage.getItem(STORAGE_KEYS.TAGS)) {
    storage.setItem(STORAGE_KEYS.TAGS, JSON.stringify([]))
  }
}

// Tag pool operations (global, shared by folders and items)
export async function getAllTags(): Promise<string[]> {
  initStorage()
  return JSON.parse(storage.getItem(STORAGE_KEYS.TAGS) || '[]')
}

export async function createTag(name: string): Promise<void> {
  initStorage()
  const trimmed = name.trim()
  if (!trimmed) return
  const tags: string[] = JSON.parse(storage.getItem(STORAGE_KEYS.TAGS) || '[]')
  if (!tags.includes(trimmed)) {
    tags.push(trimmed)
    storage.setItem(STORAGE_KEYS.TAGS, JSON.stringify(tags))
  }
}

/** Removes a tag everywhere: from the pool, all folders and all items */
export async function deleteTag(name: string): Promise<void> {
  initStorage()
  const tags: string[] = JSON.parse(storage.getItem(STORAGE_KEYS.TAGS) || '[]')
  storage.setItem(STORAGE_KEYS.TAGS, JSON.stringify(tags.filter(t => t !== name)))

  const folders: Folder[] = JSON.parse(storage.getItem(STORAGE_KEYS.FOLDERS) || '[]')
  const items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  let changed = false
  for (const folder of folders) {
    if (folder.tags?.includes(name)) {
      folder.tags = folder.tags.filter(t => t !== name)
      changed = true
    }
  }
  for (const item of items) {
    if (item.tags?.includes(name)) {
      item.tags = item.tags.filter(t => t !== name)
      changed = true
    }
  }
  if (changed) {
    storage.setItem(STORAGE_KEYS.FOLDERS, JSON.stringify(folders))
    storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(items))
  }
}

export async function initDatabase(): Promise<void> {
  initStorage()
  console.log('[DB] Storage initialized (using storage)')
}

// Folder operations
export async function addFolder(name: string, tags: string[] = []): Promise<number> {
  initStorage()
  const folders: Folder[] = JSON.parse(storage.getItem(STORAGE_KEYS.FOLDERS) || '[]')
  let nextId = parseInt(storage.getItem(STORAGE_KEYS.NEXT_FOLDER_ID) || '1')
  
  const newFolder: Folder = {
    id: nextId,
    name,
    created_at: new Date().toISOString(),
    item_count: 0,
    tags
  }
  
  folders.push(newFolder)
  storage.setItem(STORAGE_KEYS.FOLDERS, JSON.stringify(folders))
  storage.setItem(STORAGE_KEYS.NEXT_FOLDER_ID, String(nextId + 1))
  
  return newFolder.id
}

export async function getFolders(): Promise<Folder[]> {
  initStorage()
  const folders: Folder[] = JSON.parse(storage.getItem(STORAGE_KEYS.FOLDERS) || '[]')
  const items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  
  // Add item count to each folder
  const foldersWithCount = folders.map(folder => ({
    ...folder,
    item_count: items.filter(item => item.folder_id === folder.id).length
  }))
  
  // Sort by created_at descending
  return foldersWithCount.sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
}

export async function renameFolder(id: number, name: string, tags?: string[]): Promise<void> {
  initStorage()
  const folders: Folder[] = JSON.parse(storage.getItem(STORAGE_KEYS.FOLDERS) || '[]')
  
  const index = folders.findIndex(f => f.id === id)
  if (index !== -1) {
    folders[index].name = name
    if (tags !== undefined) folders[index].tags = tags
    storage.setItem(STORAGE_KEYS.FOLDERS, JSON.stringify(folders))
  }
}

export async function deleteFolder(id: number): Promise<void> {
  initStorage()
  let folders: Folder[] = JSON.parse(storage.getItem(STORAGE_KEYS.FOLDERS) || '[]')
  let items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  
  // Remove folder and its items
  folders = folders.filter(f => f.id !== id)
  items = items.filter(item => item.folder_id !== id)
  
  storage.setItem(STORAGE_KEYS.FOLDERS, JSON.stringify(folders))
  storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(items))
}

// Item operations
export async function addItem(
  folderId: number,
  itemType: 'link' | 'file',
  title: string,
  urlOrPath: string,
  category: string = '',
  coverPath: string = '',
  summary: string = '',
  tags: string[] = []
): Promise<number> {
  initStorage()
  const items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  let nextId = parseInt(storage.getItem(STORAGE_KEYS.NEXT_ITEM_ID) || '1')
  
  const newItem: Item = {
    id: nextId,
    folder_id: folderId,
    item_type: itemType,
    title: title || null,
    url: urlOrPath || null,
    category: category || null,
    cover_path: coverPath || null,
    summary: summary || null,
    created_at: new Date().toISOString(),
    tags,
    click_count: 0
  }
  
  items.push(newItem)
  storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(items))
  storage.setItem(STORAGE_KEYS.NEXT_ITEM_ID, String(nextId + 1))
  
  return newItem.id
}

export async function getItemsByFolder(folderId: number): Promise<Item[]> {
  initStorage()
  const items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  
  return items
    .filter(item => item.folder_id === folderId)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}

/** All items across every folder */
export async function getAllItems(): Promise<Item[]> {
  initStorage()
  return JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
}

/** The most recently added items (newest first) */
export async function getRecentItems(limit = 10): Promise<Item[]> {
  const items = await getAllItems()
  return items
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, limit)
}

/**
 * Items ranked by "oldest first, least clicked first" - the candidate pool
 * for the history section. Older + rarely opened items bubble to the top.
 */
export async function getHistoryPool(): Promise<Item[]> {
  const items = await getAllItems()
  return items.sort((a, b) =>
    new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      || (a.click_count || 0) - (b.click_count || 0)
      || a.id - b.id
  )
}

/** Records that an item was opened (used by the history ranking) */
export async function incrementItemClicks(id: number): Promise<void> {
  initStorage()
  const items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  const index = items.findIndex(i => i.id === id)
  if (index !== -1) {
    items[index].click_count = (items[index].click_count || 0) + 1
    storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(items))
  }
}

export async function updateItem(
  id: number,
  title: string,
  urlOrPath: string,
  category: string,
  coverPath: string = '',
  summary: string = '',
  tags?: string[]
): Promise<void> {
  initStorage()
  const items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  
  const index = items.findIndex(i => i.id === id)
  if (index !== -1) {
    items[index].title = title || null
    items[index].url = urlOrPath || null
    items[index].category = category || null
    items[index].cover_path = coverPath || null
    items[index].summary = summary || null
    if (tags !== undefined) items[index].tags = tags
    
    storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(items))
  }
}

export async function deleteItem(id: number): Promise<void> {
  initStorage()
  let items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  
  items = items.filter(i => i.id !== id)
  storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(items))
}

export async function deleteItems(ids: number[]): Promise<void> {
  if (ids.length === 0) return
  
  initStorage()
  let items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  
  items = items.filter(i => !ids.includes(i.id))
  storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(items))
}

// Search items
export async function searchItems(folderId: number, query: string): Promise<Item[]> {
  initStorage()
  const items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  const lowerQuery = query.toLowerCase()
  
  return items
    .filter(item => 
      item.folder_id === folderId &&
      (
        item.title?.toLowerCase().includes(lowerQuery) ||
        item.url?.toLowerCase().includes(lowerQuery) ||
        item.category?.toLowerCase().includes(lowerQuery)
      )
    )
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}

// Export/Import
export function exportData(): string {
  return JSON.stringify({
    folders: JSON.parse(storage.getItem(STORAGE_KEYS.FOLDERS) || '[]'),
    items: JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]'),
    tags: JSON.parse(storage.getItem(STORAGE_KEYS.TAGS) || '[]'),
    exported_at: new Date().toISOString()
  })
}

export function importData(jsonString: string): void {
  const data = JSON.parse(jsonString)
  
  if (data.tags && Array.isArray(data.tags)) {
    storage.setItem(STORAGE_KEYS.TAGS, JSON.stringify(data.tags))
  }
  
  if (data.folders && Array.isArray(data.folders)) {
    storage.setItem(STORAGE_KEYS.FOLDERS, JSON.stringify(data.folders))
    
    // Update next folder ID
    const maxFolderId = Math.max(...data.folders.map((f: Folder) => f.id), 0)
    storage.setItem(STORAGE_KEYS.NEXT_FOLDER_ID, String(maxFolderId + 1))
  }
  
  if (data.items && Array.isArray(data.items)) {
    storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(data.items))
    
    // Update next item ID
    const maxItemId = Math.max(...data.items.map((i: Item) => i.id), 0)
    storage.setItem(STORAGE_KEYS.NEXT_ITEM_ID, String(maxItemId + 1))
  }
}

// Clear all data (for testing)
export function clearAllData(): void {
  storage.removeItem(STORAGE_KEYS.FOLDERS)
  storage.removeItem(STORAGE_KEYS.ITEMS)
  storage.removeItem(STORAGE_KEYS.TAGS)
  storage.removeItem(STORAGE_KEYS.NEXT_FOLDER_ID)
  storage.removeItem(STORAGE_KEYS.NEXT_ITEM_ID)
  initStorage()
}

// Password protection for folders
export async function setFolderPassword(folderId: number, passwordHash: string, salt: string): Promise<void> {
  initStorage()
  const folders: Folder[] = JSON.parse(storage.getItem(STORAGE_KEYS.FOLDERS) || '[]')
  
  const index = folders.findIndex(f => f.id === folderId)
  if (index !== -1) {
    folders[index].password_hash = passwordHash
    folders[index].password_salt = salt
    storage.setItem(STORAGE_KEYS.FOLDERS, JSON.stringify(folders))
  }
}

export async function removeFolderPassword(folderId: number): Promise<void> {
  initStorage()
  const folders: Folder[] = JSON.parse(storage.getItem(STORAGE_KEYS.FOLDERS) || '[]')
  
  const index = folders.findIndex(f => f.id === folderId)
  if (index !== -1) {
    folders[index].password_hash = null
    folders[index].password_salt = null
    storage.setItem(STORAGE_KEYS.FOLDERS, JSON.stringify(folders))
  }
}

// Password protection for items
export async function setItemPassword(itemId: number, passwordHash: string, salt: string): Promise<void> {
  initStorage()
  const items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  
  const index = items.findIndex(i => i.id === itemId)
  if (index !== -1) {
    items[index].password_hash = passwordHash
    items[index].password_salt = salt
    storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(items))
  }
}

export async function removeItemPassword(itemId: number): Promise<void> {
  initStorage()
  const items: Item[] = JSON.parse(storage.getItem(STORAGE_KEYS.ITEMS) || '[]')
  
  const index = items.findIndex(i => i.id === itemId)
  if (index !== -1) {
    items[index].password_hash = null
    items[index].password_salt = null
    storage.setItem(STORAGE_KEYS.ITEMS, JSON.stringify(items))
  }
}
