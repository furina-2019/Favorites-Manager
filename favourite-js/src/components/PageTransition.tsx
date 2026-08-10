import { Component, useEffect, useState, type ReactNode } from 'react'
import { useLocation, useOutlet } from 'react-router-dom'
import { Button, Empty } from 'antd'
import { useTranslation } from 'react-i18next'
import { getFolderOpenCenter } from '../utils/pageTransition'

/** The items page gets the special expand/shrink-from-folder-center animation */
const isItemsPath = (pathname: string): boolean => /^\/folder\/\d+/.test(pathname)

/** Longest possible exit animation, so the fallback cleanup never cuts one short */
const EXIT_FALLBACK_MS = 700

/** After this long the enter animation is considered done and gets removed */
const ENTER_FALLBACK_MS = 600

/** Catches render errors inside a page so the user sees a message, not a blank screen */
class PageErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  state: { hasError: boolean } = { hasError: false }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return <PageErrorFallback onReset={() => this.setState({ hasError: false })} />
    }
    return this.props.children
  }
}

function PageErrorFallback({ onReset }: { onReset: () => void }) {
  const { t } = useTranslation()
  return (
    <div style={{ textAlign: 'center', padding: 48 }}>
      <Empty description={t('page_render_error')}>
        <Button type="primary" onClick={onReset}>
          {t('retry')}
        </Button>
      </Empty>
    </div>
  )
}

/** The settled (post-animation) wrapper classes for a page */
const settledClass = (pathname: string): string =>
  isItemsPath(pathname) ? 'page-enter page-fixed' : 'page-enter page-settled'

/**
 * A frozen view of a page: its element, the location that produced it, and the
 * wrapper classes it had the moment it was shown. The animation class is stored
 * here (not derived from live router state at render time), so the page that is
 * currently on screen can never briefly play the next page's animation.
 */
interface PageSnapshot {
  outlet: ReactNode
  key: string
  pathname: string
  enterClass: string
}

/**
 * Renders the current route's element (from the router itself) with a CSS enter
 * animation, while keeping the previous page mounted just long enough to play
 * its exit animation. The route matching stays 100% inside the outer <Routes>,
 * so there is no nested <Routes location> override that could silently fail.
 */
export default function PageTransition() {
  const location = useLocation()
  const outlet = useOutlet()

  const [displayed, setDisplayed] = useState<PageSnapshot>({
    outlet,
    key: location.key,
    pathname: location.pathname,
    // First load: no animation (and the items page is full-viewport)
    enterClass: isItemsPath(location.pathname) ? 'page-enter page-fixed' : 'page-enter',
  })
  const [exiting, setExiting] = useState<PageSnapshot | null>(null)

  // Navigation: freeze the old page for its exit animation, show the new one.
  // The new page's animation class is decided HERE, in the same update that
  // swaps the page, so the previously shown page keeps its own classes until
  // the swap and can never flash the new page's animation.
  useEffect(() => {
    if (location.key === displayed.key) return

    const enteringItems = isItemsPath(location.pathname)
    const enterClass = enteringItems
      ? 'page-enter page-fixed page-expand-in'
      : isItemsPath(displayed.pathname)
        ? 'page-enter' // revealed by the shrinking items page - no animation
        : 'page-enter page-slide-in'

    // The items page expands to cover the whole viewport, so when it opens
    // there is no need to keep the old page around at all
    setExiting(enteringItems ? null : displayed)
    setDisplayed({ outlet, key: location.key, pathname: location.pathname, enterClass })
  }, [location, outlet, displayed])

  // Safety net: if the exit animation's onAnimationEnd never fires
  // (e.g. animation suppressed), still remove the old page
  useEffect(() => {
    if (!exiting) return
    const timer = setTimeout(() => setExiting(null), EXIT_FALLBACK_MS)
    return () => clearTimeout(timer)
  }, [exiting])

  // Safety net: drop the enter animation after a while so the page can never
  // stay in a transformed/hidden state
  useEffect(() => {
    const timer = setTimeout(() => {
      setDisplayed(prev =>
        prev.key === location.key ? { ...prev, enterClass: settledClass(prev.pathname) } : prev,
      )
    }, ENTER_FALLBACK_MS)
    return () => clearTimeout(timer)
  }, [location.key])

  // For the items page, anchor the scale animation at the folder card center
  // (stored by FolderCard when it was clicked); otherwise fall back to center.
  // The enter animation has already started by the time this ref runs, so the
  // element is mid-transform and getBoundingClientRect() would return a scaled
  // box (origin would land near the top-left). Temporarily drop the animation
  // to measure the true (untransformed) rect, then restore it — all before the
  // browser paints, so nothing visible changes.
  const applyOrigin = (el: HTMLElement | null, isItems: boolean) => {
    if (!el) return
    const center = getFolderOpenCenter()
    if (!isItems || !center) {
      el.style.transformOrigin = '50% 50%'
      return
    }
    const anim = el.style.animation
    el.style.animation = 'none'
    const rect = el.getBoundingClientRect()
    el.style.transformOrigin = `${center.x - rect.left}px ${center.y - rect.top}px`
    el.style.animation = anim
  }

  // Old page: slides out to the right between normal pages; shrinks back into
  // the folder card when leaving the items page
  const exitClassName = exiting
    ? isItemsPath(exiting.pathname)
      ? 'page-exit page-fixed page-shrink-out'
      : 'page-exit page-slide-out'
    : ''

  return (
    <div className="page-stack">
      {exiting && (
        <div
          key={`exit-${exiting.key}`}
          className={exitClassName}
          // Only the wrapper's own animation counts; child animations (e.g. antd
          // fade-ins) bubble up and must not cut the exit short
          onAnimationEnd={(e) => {
            if (e.target === e.currentTarget) setExiting(null)
          }}
          ref={(el) => { applyOrigin(el, isItemsPath(exiting.pathname)) }}
        >
          <PageErrorBoundary>{exiting.outlet}</PageErrorBoundary>
        </div>
      )}
      <div
        key={`enter-${displayed.key}`}
        className={displayed.enterClass}
        onAnimationEnd={(e) => {
          if (e.target !== e.currentTarget) return
          setDisplayed(prev =>
            prev.key === displayed.key ? { ...prev, enterClass: settledClass(prev.pathname) } : prev,
          )
        }}
        ref={(el) => { applyOrigin(el, isItemsPath(displayed.pathname)) }}
      >
        <PageErrorBoundary>{displayed.outlet}</PageErrorBoundary>
      </div>
    </div>
  )
}
