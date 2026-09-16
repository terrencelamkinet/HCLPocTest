import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { UnifiedTimeline, type TimelineEvent } from './NexusDetailPageV2'
import { apiClient } from '../../lib/api'
import ImageLightbox from '../../components/ImageLightbox'
import SvcIcon from '../../components/SvcIcon'

interface ActivityItem {
  id: string
  entity_id?: string
  entity_type?: string
  action?: string
  description?: string
  created_at: string
}

interface Touchpoint {
  id: string
  title?: string
  type?: string
  description?: string
  company_id?: string
  contact_id?: string
  created_at: string
}

interface NameCardRow {
  id: string
  status?: string
  created_at?: string
  cropped_image_url?: string | null
  image_url?: string | null
}

function timeAgo(d: string): string {
  if (!d) return ''
  const then = new Date(d).getTime()
  const mins = Math.floor((Date.now() - then) / 60000)
  if (mins < 1) return '剛剛'
  if (mins < 60) return `${mins} 分鐘前`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} 小時前`
  return `${Math.floor(hrs / 24)} 天前`
}

const typeEmoji: Record<string, string> = {
  call: '📞', meeting: '🤝', email: '✉️', note: '📝', task: '✅', default: '📌',
}

/**
 * V2 timeline for Overview/Timeline tabs.
 * 用 UnifiedTimeline render → 冇 events 時自動顯示 .nx-empty-state（Bug #2 fix）。
 *
 * 2026-09-15 Terrence spec：contact 嘅 timeline 要有名片紀錄 —
 *   • 首次新增名片 = 「新增名片」（click 放大）
 *   • 之後每次取代／更新 = 「更新名片」，舊卡保留、可以 click 放大對照
 */
export function V2ActivityTimeline({ entityId, filterType }: {
  entityId: string
  filterType: 'company' | 'contact' | 'project' | 'task' | 'touchpoint'
}) {
  const { t } = useTranslation()
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [zoom, setZoom] = useState<{ src: string; cap: string } | null>(null)

  useEffect(() => {
    let alive = true
    Promise.all([
      apiClient.get<{ items: ActivityItem[] }>('/api/v1/crm/activities?page_size=100').catch(() => ({ items: [] })),
      apiClient.get<{ items: Touchpoint[] }>('/api/v1/crm/touchpoints?limit=100').catch(() => ({ items: [] })),
      (filterType === 'contact'
        ? apiClient.get<{ items: NameCardRow[] }>(`/api/v1/crm/name-cards?contact_id=${entityId}&limit=50`).catch(() => ({ items: [] }))
        : Promise.resolve({ items: [] as NameCardRow[] })),
    ]).then(([aRes, tpRes, ncRes]) => {
      if (!alive) return
      const acts = (aRes.items || []).filter(a => a.entity_id === entityId)
      const tps = (tpRes.items || []).filter(tp => {
        if (filterType === 'company') return tp.company_id === entityId
        if (filterType === 'contact') return tp.contact_id === entityId
        return tp.company_id === entityId || tp.contact_id === entityId
      })
      /* 名片紀錄：由舊到新排（第一張 = 首次新增，之後每張 = 一次更新，舊卡保留） */
      const cards = [...(ncRes.items || [])].sort(
        (a, b) => new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime(),
      )
      const cardEvents: TimelineEvent[] = cards.map((c, i) => {
        const src = c.cropped_image_url || c.image_url || ''
        const stamp = c.created_at || ''
        const cap = stamp ? `${stamp.slice(0, 10)} ${stamp.slice(11, 16)}` : ''
        return {
          id: `nc-${c.id}`,
          icon: <SvcIcon name="credit-card" size={15} />,
          title: i === 0
            ? t('nameCard.tlAdded', { defaultValue: '新增名片' })
            : t('nameCard.tlUpdated', { defaultValue: '更新名片' }),
          meta: [cap, timeAgo(stamp)].filter(Boolean).join(' · '),
          body: i === 0 ? undefined : t('nameCard.tlOldKept', { defaultValue: '舊名片已保留 — 點擊放大對照' }),
          sortKey: stamp,
          imageUrl: src || undefined,
          onClick: src ? () => setZoom({ src, cap }) : undefined,
        }
      })
      const mapped: TimelineEvent[] = [
        ...acts.map(a => ({
          id: `a-${a.id}`, icon: '📝', title: a.action || '—', meta: timeAgo(a.created_at),
          body: a.description || undefined, sortKey: a.created_at,
        })),
        ...tps.map(tp => ({
          id: `tp-${tp.id}`, icon: typeEmoji[tp.type || ''] || typeEmoji.default, title: tp.title || '—',
          meta: timeAgo(tp.created_at), body: tp.description || undefined, sortKey: tp.created_at,
        })),
        ...cardEvents,
      ].sort((a, b) => new Date(b.sortKey).getTime() - new Date(a.sortKey).getTime())
      setEvents(mapped)
    })
    return () => { alive = false }
  }, [entityId, filterType, t])

  return (
    <>
      <UnifiedTimeline events={events} />
      {zoom && <ImageLightbox src={zoom.src} caption={zoom.cap} onClose={() => setZoom(null)} />}
    </>
  )
}
