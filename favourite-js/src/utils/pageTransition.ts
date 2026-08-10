// Shared state for page transitions: remembers where the folder card that
// opened the items page is located, so the items page can expand from that
// point on open and shrink back to it on close.

let folderOpenCenter: { x: number; y: number } | null = null

/** Called by the folder card when it is clicked (viewport coordinates) */
export function setFolderOpenCenter(x: number, y: number): void {
  folderOpenCenter = { x, y }
}

/** Returns the last clicked folder card center, or null */
export function getFolderOpenCenter(): { x: number; y: number } | null {
  return folderOpenCenter
}
