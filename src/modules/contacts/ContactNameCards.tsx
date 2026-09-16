import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import ImageLightbox from '../../components/ImageLightbox'
import { apiClient } from '../../lib/api'

type CardRow = {
  id: string
  status?: string
  created_at?: string
  cropped_image_url?: string | null
  image_url?: string | null
}

function fmt(ts?: string): string {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ''
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

/* ContactNameCards — contact 頁「名片」區（放喺 General Info 同 Ownership 中間）
   2026-09-15 Terrence spec：有 name card preview、click 放大（有放大動畫）；
   同一個 contact 有舊卡時全部列出（舊卡一樣可以 preview）。 */
export default function ContactNameCards({ contactId }: { contactId: string }) {
  const { t } = useTranslation()
  const [cards, setCards] = useState<CardRow[]>([])
  const [zoom, setZoom] = useState<{ src: string; cap: string } | null>(null)

  useEffect(() => {
    let alive = true
    apiClient.get<{ items: CardRow[] }>(`/api/v1/crm/name-cards?contact_id=${contactId}&limit=50`)
      .then((r) => { if (alive) setCards(Array.isArray(r?.items) ? r.items : []) })
      .catch(() => { if (alive) setCards([]) })
    return () => { alive = false }
  }, [contactId])

  if (!cards.length) return null

  const img = (c: CardRow) => c.cropped_image_url || c.image_url || ''

  return (
    <div className="cnc">
      {cards.map((c, i) => {
        const src = img(c)
        const isCurrent = i === 0
        return (
          <figure className="cnc-item" key={c.id}>
            <button type="button" className="cnc-thumb" disabled={!src}
              aria-label={t('nameCard.zoom', { defaultValue: '放大名片' })}
              onClick={() => src && setZoom({ src, cap: fmt(c.created_at) })}>
              {src ? <img src={src} alt="" loading="lazy" /> : <span className="cnc-none">—</span>}
            </button>
            <figcaption className="cnc-cap">
              <span className={`cnc-badge${isCurrent ? ' is-current' : ''}`}>
                {isCurrent
                  ? t('nameCard.currentCard', { defaultValue: '目前' })
                  : t('nameCard.oldCard', { defaultValue: '舊紀錄' })}
              </span>
              <span className="cnc-date">{fmt(c.created_at)}</span>
            </figcaption>
          </figure>
        )
      })}
      {zoom && <ImageLightbox src={zoom.src} caption={zoom.cap} onClose={() => setZoom(null)} />}
    </div>
  )
}
