import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { Button, Tooltip } from 'antd'
import { ZoomInOutlined, ZoomOutOutlined, FullscreenOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { Folder, Item } from '../core/database'
import { useUIStore } from '../stores/uiStore'
import TagPills from './TagPills'

// Colors per the spec: folder red, category/type green, item blue + gray details
const FOLDER_COLOR = '#F5222D'
const GROUP_COLOR = '#52C41A'
const ITEM_COLOR = '#1890FF'
const DETAIL_COLOR = '#999999'
const MATCH_COLOR = '#d48806'

// Layout constants (radial: depth -> distance from the center)
const LEVEL_GAP = 250
const NODE_W = 210
const BRANCH_H = 48
const ITEM_H = 112
const PADDING = 24
// Extra margin outside the node boxes (summary button room)
const BUTTON_EXTRA = 32

type NodeKind = 'folder' | 'category' | 'type' | 'item'

const DEPTH_OF: Record<NodeKind, number> = {
  folder: 0,
  category: 1,
  type: 2,
  item: 3,
}

interface MindNode {
  id: string
  kind: NodeKind
  label: string
  subLabel?: string
  detail?: string
  item?: Item
  children: MindNode[]
  angle: number
  x: number
  y: number
}

interface MindMapViewProps {
  folder?: Folder | null
  items: Item[]
  /** Called when an item node is clicked (e.g. jump back to the list view) */
  onItemClick?: (item: Item) => void
  /** Called when the summary button on an item node is clicked */
  onViewSummary?: (item: Item) => void
  /** Current search query - highlights matched text and tags */
  searchQuery?: string
}

const truncate = (text: string, max: number): string =>
  text.length > max ? `${text.slice(0, max - 1)}…` : text

/** Highlights query matches inside an SVG <text> via gold <tspan>s */
const renderHighlighted = (text: string, query: string | undefined, max: number): ReactNode => {
  const truncated = truncate(text, max)
  const q = query?.trim().toLowerCase()
  if (!q || !truncated.toLowerCase().includes(q)) return truncated

  const lower = truncated.toLowerCase()
  const parts: ReactNode[] = []
  let i = 0
  let idx = lower.indexOf(q)
  while (idx !== -1) {
    if (idx > i) parts.push(truncated.slice(i, idx))
    parts.push(
      <tspan key={`m-${idx}`} fill={MATCH_COLOR} fontWeight={700}>
        {truncated.slice(idx, idx + q.length)}
      </tspan>,
    )
    i = idx + q.length
    idx = lower.indexOf(q, i)
  }
  if (i < truncated.length) parts.push(truncated.slice(i))
  return parts
}

const heightOf = (n: MindNode): number => (n.kind === 'item' ? ITEM_H : BRANCH_H)

export default function MindMapView({
  folder,
  items,
  onItemClick,
  onViewSummary,
  searchQuery,
}: MindMapViewProps) {
  const { t } = useTranslation()
  const { darkMode, themeColor } = useUIStore()

  // "+N" popup state: which item's tags to show and where to anchor it
  const [tagPopup, setTagPopup] = useState<{ item: Item; anchor: { x: number; y: number } } | null>(null)
  // Zoom state for the view (0.1x - 3x)
  const [zoom, setZoom] = useState(1)
  // Fractional viewport center before a zoom, so the view stays anchored
  const centerRef = useRef<{ fx: number; fy: number } | null>(null)

  // Left-button drag to pan the scrollable canvas
  const scrollRef = useRef<HTMLDivElement>(null)
  const [dragging, setDragging] = useState(false)
  const dragRef = useRef<{
    sx: number; sy: number; sl: number; st: number; moved: boolean
  } | null>(null)
  // Clicks within this window after a drag are treated as part of the drag
  const suppressUntilRef = useRef(0)

  useEffect(() => {
    if (!dragging) return
    const onMove = (e: MouseEvent) => {
      const d = dragRef.current
      const el = scrollRef.current
      if (!d || !el) return
      const dx = e.clientX - d.sx
      const dy = e.clientY - d.sy
      if (!d.moved && Math.hypot(dx, dy) > 5) d.moved = true
      if (d.moved) {
        el.scrollLeft = d.sl - dx
        el.scrollTop = d.st - dy
      }
    }
    const onUp = () => {
      if (dragRef.current?.moved) suppressUntilRef.current = Date.now() + 300
      dragRef.current = null
      setDragging(false)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [dragging])

  const onMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button !== 0) return
    const el = scrollRef.current
    if (!el) return
    dragRef.current = {
      sx: e.clientX,
      sy: e.clientY,
      sl: el.scrollLeft,
      st: el.scrollTop,
      moved: false,
    }
    setDragging(true)
  }

  const zoomBy = (factor: number) => {
    const el = scrollRef.current
    if (el) {
      centerRef.current = {
        fx: (el.scrollLeft + el.clientWidth / 2) / el.scrollWidth,
        fy: (el.scrollTop + el.clientHeight / 2) / el.scrollHeight,
      }
    }
    setZoom(z => Math.min(3, Math.max(0.1, z * factor)))
  }

  const zoomToFit = () => {
    const el = scrollRef.current
    if (!el || !layout) return
    const fit = Math.min(el.clientWidth / layout.width, el.clientHeight / layout.height, 1)
    centerRef.current = { fx: 0.5, fy: 0.5 }
    setZoom(Math.max(0.1, fit))
  }

  // Keep the same point under the viewport center after a zoom
  useEffect(() => {
    const c = centerRef.current
    if (!c) return
    centerRef.current = null
    const el = scrollRef.current
    if (!el) return
    el.scrollLeft = c.fx * el.scrollWidth - el.clientWidth / 2
    el.scrollTop = c.fy * el.scrollHeight - el.clientHeight / 2
  }, [zoom])

  // Ctrl + mouse wheel zooms (native non-passive listener so preventDefault works)
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey) return
      e.preventDefault()
      zoomBy(e.deltaY < 0 ? 1.1 : 1 / 1.1)
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [])

  const tree = useMemo(() => {
    if (!folder) return null

    const root: MindNode = {
      id: 'folder',
      kind: 'folder',
      label: folder.name || t('untitled'),
      angle: 0,
      x: 0,
      y: 0,
      children: [],
    }

    // Group items by category, then by item type
    const byCategory = new Map<string, Item[]>()
    for (const item of items) {
      const key = item.category || ''
      const list = byCategory.get(key) || []
      list.push(item)
      byCategory.set(key, list)
    }

    const sortedCategories = Array.from(byCategory.keys()).sort((a, b) => {
      if (!a) return 1 // uncategorized last
      if (!b) return -1
      return a.localeCompare(b)
    })

    let seq = 0
    for (const category of sortedCategories) {
      const catItems = byCategory.get(category)!
      const catNode: MindNode = {
        id: `cat-${seq++}`,
        kind: 'category',
        label: category ? (t(`category_${category.toLowerCase()}`) || category) : t('uncategorized'),
        angle: 0,
        x: 0,
        y: 0,
        children: [],
      }

      for (const itemType of ['link', 'file'] as const) {
        const typeItems = catItems.filter(item => item.item_type === itemType)
        if (typeItems.length === 0) continue

        const typeNode: MindNode = {
          id: `type-${seq++}`,
          kind: 'type',
          label: itemType === 'link' ? t('type_link') : t('type_file'),
          angle: 0,
          x: 0,
          y: 0,
          children: typeItems.map(item => ({
            id: `item-${item.id}`,
            kind: 'item' as const,
            label: item.title || item.url || t('untitled'),
            subLabel: item.url || undefined,
            detail: item.category
              ? `${t(`category_${item.category.toLowerCase()}`) || item.category} · ${new Date(item.created_at).toLocaleDateString()}`
              : new Date(item.created_at).toLocaleDateString(),
            item,
            angle: 0,
            x: 0,
            y: 0,
            children: [],
          })),
        }
        catNode.children.push(typeNode)
      }

      if (catNode.children.length > 0) root.children.push(catNode)
    }

    return root
  }, [folder, items, t])

  const layout = useMemo(() => {
    if (!tree) return null

    // Radial layout with compact branches: adjacent outermost cards (items)
    // are spaced ~10° apart. If there are too many to fit a full circle the
    // spacing is compressed, and the whole radius extends outward so the cards
    // always keep a comfortable tangential gap. Internal nodes sit at the
    // circular midpoint of their leaves, so each category/type branch hugs the
    // same compact arc instead of spreading around the whole circle.
    let leafCount = 0
    const countLeaves = (n: MindNode): void => {
      if (n.children.length === 0) leafCount++
      else n.children.forEach(countLeaves)
    }
    countLeaves(tree)
    if (leafCount === 0) leafCount = 1

    const BASE_STEP = (Math.PI * 7) / 180 // ~7° per branch
    const step = Math.min(BASE_STEP, (2 * Math.PI) / leafCount)
    const span = (leafCount - 1) * step
    const startAngle = -Math.PI / 2 - span / 2 // fan centered at the top
    // Extend the radius so adjacent item cards keep at least this tangential gap
    const MIN_TANGENTIAL = 240
    const itemRadius = Math.max(3 * LEVEL_GAP, MIN_TANGENTIAL / (2 * Math.sin(step / 2)))
    const radiusFor = (depth: number) => (itemRadius / 3) * depth

    const circularMean = (angles: number[]): number => {
      let sx = 0
      let sy = 0
      for (const a of angles) {
        sx += Math.cos(a)
        sy += Math.sin(a)
      }
      return Math.atan2(sy, sx)
    }

    let leafIndex = 0
    const assignAngle = (n: MindNode): void => {
      if (n.children.length === 0) {
        n.angle = startAngle + leafIndex * step
        leafIndex++
        return
      }
      n.children.forEach(assignAngle)
      n.angle = circularMean(n.children.map(c => c.angle))
    }
    assignAngle(tree)

    // Point where the ray from (cx,cy) toward (tx,ty) exits the box
    const borderPoint = (cx: number, cy: number, hw: number, hh: number, tx: number, ty: number) => {
      const dx = tx - cx
      const dy = ty - cy
      const s = Math.min(
        dx !== 0 ? hw / Math.abs(dx) : Infinity,
        dy !== 0 ? hh / Math.abs(dy) : Infinity,
      )
      const k = s === Infinity ? 0 : s
      return { x: cx + dx * k, y: cy + dy * k }
    }

    const nodes: MindNode[] = []
    const edges: Array<{ x1: number; y1: number; x2: number; y2: number }> = []
    const collect = (n: MindNode) => {
      const radius = radiusFor(DEPTH_OF[n.kind])
      n.x = Math.cos(n.angle) * radius
      n.y = Math.sin(n.angle) * radius
      nodes.push(n)
      n.children.forEach(child => {
        collect(child) // resolve the child's position before clipping the edge
        const p = borderPoint(n.x, n.y, NODE_W / 2, heightOf(n) / 2, child.x, child.y)
        const c = borderPoint(child.x, child.y, NODE_W / 2, heightOf(child) / 2, n.x, n.y)
        edges.push({ x1: p.x, y1: p.y, x2: c.x, y2: c.y })
      })
    }
    collect(tree)

    let minX = Infinity
    let maxX = -Infinity
    let minY = Infinity
    let maxY = -Infinity
    for (const n of nodes) {
      const hw = NODE_W / 2
      const hh = heightOf(n) / 2
      minX = Math.min(minX, n.x - hw)
      maxX = Math.max(maxX, n.x + hw)
      minY = Math.min(minY, n.y - hh)
      maxY = Math.max(maxY, n.y + hh)
    }
    if (minX === Infinity) {
      minX = 0
      maxX = NODE_W
      minY = 0
      maxY = BRANCH_H
    }
    const margin = PADDING + BUTTON_EXTRA

    return {
      nodes,
      edges,
      offsetX: margin - minX,
      offsetY: margin - minY,
      width: maxX - minX + margin * 2,
      height: maxY - minY + margin * 2,
    }
  }, [tree])

  if (!tree || !layout) return null

  const nodeFill = darkMode ? '#262626' : '#ffffff'
  const edgeColor = darkMode ? '#595959' : '#d9d9d9'

  const handleItemOpen = (item: Item) => {
    if (Date.now() < suppressUntilRef.current) return
    onItemClick?.(item)
  }

  return (
    <div style={{ position: 'relative', height: '100%' }}>
      <div
        ref={scrollRef}
        onMouseDown={onMouseDown}
        style={{
          height: '100%',
          overflow: 'auto',
          padding: 8,
          cursor: dragging ? 'grabbing' : 'grab',
          userSelect: dragging ? 'none' : undefined,
        }}
      >
      <svg
        width={layout.width * zoom}
        height={layout.height * zoom}
        viewBox={`0 0 ${layout.width} ${layout.height}`}
        style={{ display: 'block' }}
      >
        {/* Connecting edges (center-to-center, clipped at the node borders) */}
        {layout.edges.map((edge, index) => (
          <line
            key={`edge-${index}`}
            x1={edge.x1 + layout.offsetX}
            y1={edge.y1 + layout.offsetY}
            x2={edge.x2 + layout.offsetX}
            y2={edge.y2 + layout.offsetY}
            stroke={edgeColor}
            strokeWidth={1.5}
          />
        ))}

        {/* Nodes */}
        {layout.nodes.map(node => {
          const cx = node.x + layout.offsetX
          const cy = node.y + layout.offsetY
          const color = node.kind === 'folder'
            ? FOLDER_COLOR
            : node.kind === 'item'
              ? ITEM_COLOR
              : GROUP_COLOR
          const height = heightOf(node)
          const isItem = node.kind === 'item'
          const itemTags = isItem ? (node.item?.tags || []) : []
          const shownTags = itemTags.slice(0, 2)
          const hiddenTags = itemTags.length - shownTags.length

          return (
            <g
              key={node.id}
              transform={`translate(${cx - NODE_W / 2}, ${cy - height / 2})`}
              onClick={isItem && node.item ? () => handleItemOpen(node.item!) : undefined}
              style={{ cursor: dragging ? 'grabbing' : (isItem ? 'pointer' : 'default') }}
            >
              <title>
                {node.label}
                {node.subLabel ? `\n${node.subLabel}` : ''}
              </title>
              <rect
                width={NODE_W}
                height={height}
                rx={10}
                fill={nodeFill}
                stroke={color}
                strokeWidth={2}
              />
              {isItem ? (
                <>
                  <text x={12} y={24} fill={color} fontSize={13} fontWeight={600}>
                    {renderHighlighted(node.label, searchQuery, 22)}
                  </text>
                  {node.subLabel && (
                    <text x={12} y={44} fill={DETAIL_COLOR} fontSize={11}>
                      {renderHighlighted(node.subLabel, searchQuery, 32)}
                    </text>
                  )}
                  {node.detail && (
                    <text x={12} y={62} fill={DETAIL_COLOR} fontSize={11}>
                      {renderHighlighted(node.detail, searchQuery, 32)}
                    </text>
                  )}

                  {/* Tags: up to 2 pills + a "+N" chip that opens the all-tags popup */}
                  {itemTags.length > 0 && (
                    <g>
                      {shownTags.map((tag, i) => (
                        <g key={tag} transform={`translate(${12 + i * 84}, 74)`}>
                          <rect
                            width={76}
                            height={18}
                            rx={9}
                            fill={darkMode ? '#1f1f1f' : '#f5f5f5'}
                            stroke={darkMode ? '#3d3d3d' : '#d9d9d9'}
                            strokeWidth={1}
                          />
                          <text
                            x={38}
                            y={13}
                            textAnchor="middle"
                            fill={darkMode ? '#ccc' : '#666'}
                            fontSize={10}
                          >
                            {renderHighlighted(tag, searchQuery, 10)}
                          </text>
                        </g>
                      ))}
                      {hiddenTags > 0 && (
                        <g
                          transform={`translate(${12 + shownTags.length * 84}, 74)`}
                          style={{ cursor: 'pointer' }}
                          onClick={(e) => {
                            e.stopPropagation()
                            if (Date.now() < suppressUntilRef.current) return
                            const rect = (e.currentTarget as SVGGElement).getBoundingClientRect()
                            setTagPopup({
                              item: node.item!,
                              anchor: { x: rect.left, y: rect.bottom },
                            })
                          }}
                        >
                          <title>{t('all_tags')}</title>
                          <rect
                            width={30}
                            height={18}
                            rx={9}
                            fill={darkMode ? '#1f1f1f' : '#f5f5f5'}
                            stroke={themeColor}
                            strokeWidth={1}
                          />
                          <text
                            x={15}
                            y={13}
                            textAnchor="middle"
                            fill={themeColor}
                            fontSize={10}
                            fontWeight={600}
                          >
                            +{hiddenTags}
                          </text>
                        </g>
                      )}
                    </g>
                  )}
                </>
              ) : (
                <text x={12} y={height / 2 + 5} fill={color} fontSize={14} fontWeight={600}>
                  {renderHighlighted(node.label, searchQuery, 26)}
                </text>
              )}

              {/* Details button: outside the node box, on its right side */}
              {isItem && node.item && onViewSummary && (
                <g
                  transform={`translate(${NODE_W + 8}, ${ITEM_H / 2 - 11})`}
                  style={{ cursor: 'pointer' }}
                  onClick={(e) => {
                    e.stopPropagation()
                    if (Date.now() < suppressUntilRef.current) return
                    onViewSummary?.(node.item!)
                  }}
                >
                  <title>{t('view_details')}</title>
                  <rect
                    width={22}
                    height={22}
                    rx={6}
                    fill={nodeFill}
                    stroke={DETAIL_COLOR}
                    strokeWidth={1}
                  />
                  <text x={11} y={16} textAnchor="middle" fontSize={12}>
                    📝
                  </text>
                </g>
              )}
            </g>
          )
        })}
      </svg>
      </div>

      {/* Zoom controls (floating, always visible) */}
      <div
        style={{
          position: 'absolute',
          top: 8,
          right: 8,
          zIndex: 5,
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          padding: 4,
          borderRadius: 8,
          background: darkMode ? 'rgba(38, 38, 38, 0.92)' : 'rgba(255, 255, 255, 0.92)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
        }}
      >
        <Tooltip title={t('zoom_out')}>
          <Button size="small" icon={<ZoomOutOutlined />} onClick={() => zoomBy(1 / 1.25)} />
        </Tooltip>
        <span style={{ fontSize: '0.75rem', minWidth: '2.75rem', textAlign: 'center', color: darkMode ? '#ccc' : '#555' }}>
          {Math.round(zoom * 100)}%
        </span>
        <Tooltip title={t('zoom_in')}>
          <Button size="small" icon={<ZoomInOutlined />} onClick={() => zoomBy(1.25)} />
        </Tooltip>
        <Tooltip title={t('fit_view')}>
          <Button size="small" icon={<FullscreenOutlined />} onClick={zoomToFit} />
        </Tooltip>
      </div>

      {/* All-tags popup for the "+N" chip (HTML, anchored near the chip) */}
      {tagPopup && (
        <TagPills
          tags={tagPopup.item.tags || []}
          highlight={searchQuery}
          variant="plain"
          max={tagPopup.item.tags?.length || 0}
          popupAnchor={tagPopup.anchor}
          popupOpen
          onPopupClose={() => setTagPopup(null)}
        />
      )}
    </div>
  )
}
