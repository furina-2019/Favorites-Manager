// Password utilities using Web Crypto API

// Generate a random salt
export function generateSalt(): string {
  const salt = new Uint8Array(16)
  crypto.getRandomValues(salt)
  return arrayBufferToBase64(salt)
}

// Convert Uint8Array to base64 string
function arrayBufferToBase64(buffer: Uint8Array): string {
  let binary = ''
  const bytes = new Uint8Array(buffer)
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

// Convert base64 string to Uint8Array
function base64ToArrayBuffer(base64: string): Uint8Array {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}

// Hash password with SHA-256 and salt
export async function hashPassword(password: string, saltBase64: string): Promise<string> {
  const encoder = new TextEncoder()
  const salt = base64ToArrayBuffer(saltBase64)
  const data = encoder.encode(password)
  const combined = new Uint8Array(data.length + salt.length)
  combined.set(data)
  combined.set(salt, data.length)
  
  const hashBuffer = await crypto.subtle.digest('SHA-256', combined)
  return arrayBufferToBase64(new Uint8Array(hashBuffer))
}

// Verify password
export async function verifyPassword(password: string, storedHash: string, salt: string): Promise<boolean> {
  const hash = await hashPassword(password, salt)
  return hash === storedHash
}

// Check if folder/item is unlocked (session)
export function isItemUnlocked(type: 'folder' | 'item', id: number): boolean {
  const key = `favourite-unlocked-${type}-${id}`
  return sessionStorage.getItem(key) === 'true'
}

// Mark as unlocked (session)
export function setItemUnlocked(type: 'folder' | 'item', id: number): void {
  const key = `favourite-unlocked-${type}-${id}`
  sessionStorage.setItem(key, 'true')
}

// Lock (clear session)
export function lockItem(type: 'folder' | 'item', id: number): void {
  const key = `favourite-unlocked-${type}-${id}`
  sessionStorage.removeItem(key)
}

// Lock all items
export function lockAll(): void {
  // Get all session keys and remove favourites ones
  const keys: string[] = []
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i)
    if (key && key.startsWith('favourite-unlocked-')) {
      keys.push(key)
    }
  }
  keys.forEach(key => sessionStorage.removeItem(key))
}
