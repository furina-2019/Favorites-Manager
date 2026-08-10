import { create } from 'zustand'
import { 
  addFolder, 
  getFolders, 
  renameFolder, 
  deleteFolder,
  addItem,
  getItemsByFolder,
  updateItem,
  deleteItem,
  deleteItems,
  searchItems,
  Folder,
  Item
} from '../core/database'

interface DBState {
  folders: Folder[]
  currentFolderId: number | null
  currentFolderName: string
  items: Item[]
  loading: boolean
  error: string | null
  
  // Folder actions
  loadFolders: () => Promise<void>
  createFolder: (name: string, tags?: string[]) => Promise<number>
  renameFolder: (id: number, name: string, tags?: string[]) => Promise<void>
  removeFolder: (id: number) => Promise<void>
  
  // Item actions
  loadItems: (folderId: number) => Promise<void>
  addItem: (
    folderId: number,
    itemType: 'link' | 'file',
    title: string,
    urlOrPath: string,
    category?: string,
    coverPath?: string,
    summary?: string,
    tags?: string[]
  ) => Promise<number>
  updateItem: (
    id: number,
    title: string,
    urlOrPath: string,
    category: string,
    coverPath?: string,
    summary?: string,
    tags?: string[]
  ) => Promise<void>
  removeItem: (id: number) => Promise<void>
  removeItems: (ids: number[]) => Promise<void>
  searchItems: (query: string) => Promise<void>
  
  // State setters
  setCurrentFolder: (id: number | null, name: string) => void
  clearError: () => void
}

export const useDBStore = create<DBState>((set, get) => ({
  folders: [],
  currentFolderId: null,
  currentFolderName: '',
  items: [],
  loading: false,
  error: null,
  
  loadFolders: async () => {
    set({ loading: true, error: null })
    try {
      const folders = await getFolders()
      set({ folders, loading: false })
    } catch (err) {
      set({ error: (err as Error).message, loading: false })
    }
  },
  
  createFolder: async (name: string, tags?: string[]) => {
    set({ loading: true, error: null })
    try {
      const id = await addFolder(name, tags)
      const folders = await getFolders()
      set({ folders, loading: false })
      return id
    } catch (err) {
      set({ error: (err as Error).message, loading: false })
      throw err
    }
  },
  
  renameFolder: async (id: number, name: string, tags?: string[]) => {
    try {
      await renameFolder(id, name, tags)
      const folders = await getFolders()
      set({ folders })
    } catch (err) {
      set({ error: (err as Error).message })
    }
  },
  
  removeFolder: async (id: number) => {
    set({ loading: true, error: null })
    try {
      await deleteFolder(id)
      const folders = await getFolders()
      set({ 
        folders, 
        loading: false,
        currentFolderId: get().currentFolderId === id ? null : get().currentFolderId,
        items: get().currentFolderId === id ? [] : get().items
      })
    } catch (err) {
      set({ error: (err as Error).message, loading: false })
    }
  },
  
  loadItems: async (folderId: number) => {
    set({ loading: true, error: null })
    try {
      const items = await getItemsByFolder(folderId)
      set({ items, loading: false, currentFolderId: folderId })
    } catch (err) {
      set({ error: (err as Error).message, loading: false })
    }
  },
  
  addItem: async (folderId, itemType, title, urlOrPath, category = '', coverPath = '', summary = '', tags?: string[]) => {
    set({ loading: true, error: null })
    try {
      const id = await addItem(folderId, itemType, title, urlOrPath, category, coverPath, summary, tags)
      const items = await getItemsByFolder(folderId)
      // Update folder item count
      const folders = await getFolders()
      set({ items, folders, loading: false })
      return id
    } catch (err) {
      set({ error: (err as Error).message, loading: false })
      throw err
    }
  },
  
  updateItem: async (id, title, urlOrPath, category, coverPath = '', summary = '', tags?: string[]) => {
    try {
      await updateItem(id, title, urlOrPath, category, coverPath, summary, tags)
      if (get().currentFolderId) {
        const folderId = get().currentFolderId!
        const items = await getItemsByFolder(folderId)
        set({ items })
      }
    } catch (err) {
      set({ error: (err as Error).message })
    }
  },
  
  removeItem: async (id: number) => {
    set({ loading: true, error: null })
    try {
      await deleteItem(id)
      if (get().currentFolderId) {
        const folderId = get().currentFolderId!
        const items = await getItemsByFolder(folderId)
        const folders = await getFolders()
        set({ items, folders, loading: false })
      } else {
        set({ loading: false })
      }
    } catch (err) {
      set({ error: (err as Error).message, loading: false })
    }
  },
  
  removeItems: async (ids: number[]) => {
    set({ loading: true, error: null })
    try {
      await deleteItems(ids)
      if (get().currentFolderId) {
        const folderId = get().currentFolderId!
        const items = await getItemsByFolder(folderId)
        const folders = await getFolders()
        set({ items, folders, loading: false })
      } else {
        set({ loading: false })
      }
    } catch (err) {
      set({ error: (err as Error).message, loading: false })
    }
  },
  
  searchItems: async (query: string) => {
    if (!get().currentFolderId) return
    try {
      const folderId = get().currentFolderId!
      const items = await searchItems(folderId, query)
      set({ items })
    } catch (err) {
      set({ error: (err as Error).message })
    }
  },
  
  setCurrentFolder: (id: number | null, name: string) => {
    set({ currentFolderId: id, currentFolderName: name })
  },
  
  clearError: () => {
    set({ error: null })
  },
}))
