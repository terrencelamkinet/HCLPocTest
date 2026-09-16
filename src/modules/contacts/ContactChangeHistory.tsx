import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { apiClient } from '../../lib/api'

/* ═══════════════════════════════════════════════════════════
   ContactChangeHistory — 欄位級歷史時間軸（v1，2026-09-15）

   答 Terrence 嘅問題：「需要了解每一個用戶過往的紀錄，什麼時候轉？轉了什麼？」
   後端：nexus_crm.contact_changes（append-only + RLS FORCE）
        GET /api/v1/crm/contacts/{id}/history
   P仔 review：錯歷史用 retract（verification_status='retracted'）唔硬刪；
               每行帶 source（card/manual/merge/legacy）做 provenance。

   設計跟 NEXUS Design Guide 2026：12/13px body、8px grid、token 顏色；
   mobile 單欄（時間獨佔一行）。冇歷史就唔 render（Less is more，避免空白卡）。
   ═══════════════════════════════════════════════════════════ */

type ChangeRow = {
  id: string
  field: string
  old_value: string | null
  new_value: string | null
  changed_at: string | null
  source: string | null
  source_id: string | null
  confidence: string | null
  verification_status: string | null
}

/* module-scope const 唔可以包 t()（import 時只計一次 → 換語言會殘留舊語言；
   見 skill i18n-translation-management §Pitfall 3(b)）→ 存 labelKey + fallback，
   喺 render 位才翻。key：contact.history.source.* / contact.history.field.*
   （新增 key 只落 JSON、唔入 DB ＝ local bundle 生效） */
const SOURCE_LABEL: Record<string, { key: string; fb: string }> = {
  card: { key: 'contact.history.source.card', fb: '名片' },
  manual: { key: 'contact.history.source.manual', fb: '人手' },
  merge: { key: 'contact.history.source.merge', fb: '併入' },
  import: { key: 'contact.history.source.import', fb: '匯入' },
  ai: { key: 'contact.history.source.ai', fb: 'AI' },
  legacy: { key: 'contact.history.source.legacy', fb: '舊資料' },
}

const FIELD_LABEL: Record<string, { key: string; fb: string }> = {
  name: { key: 'contact.history.field.name', fb: '姓名' },
  email: { key: 'contact.history.field.email', fb: 'Email' },
  phone: { key: 'contact.history.field.phone', fb: '電話' },
  job_title: { key: 'contact.history.field.job_title', fb: '職位' },
  title: { key: 'contact.history.field.title', fb: '職位' },
  company_id: { key: 'contact.history.field.company_id', fb: '公司' },
  company: { key: 'contact.history.field.company', fb: '公司' },
  notes: { key: 'contact.history.field.notes', fb: '備註' },
  tags: { key: 'contact.history.field.tags', fb: '標籤' },
  address: { key: 'contact.history.field.address', fb: '地址' },
  status: { key: 'contact.history.field.status', fb: '狀態' },
  source: { key: 'contact.history.field.source', fb: '來源' },
  owner_id: { key: 'contact.history.field.owner_id', fb: '負責人' },
  next_follow_up: { key: 'contact.history.field.next_follow_up', fb: '下次跟進' },
}

function fmt(ts?: string | null): string {
  if (!ts) return '—'
  const d = new Date(ts)
  if (isNaN(d.getTime())) return '—'
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

export default function ContactChangeHistory({ contactId }: { contactId: string }) {
  const { t } = useTranslation()
  const [rows, setRows] = useState<ChangeRow[]>([])
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let alive = true
    setLoading(true)
    apiClient.get<ChangeRow[]>(`/api/v1/crm/contacts/${contactId}/history?limit=200`)
      .then((r) => { if (alive) { setRows(Array.isArray(r) ? r : []); setFailed(false) } })
      .catch(() => { if (alive) setFailed(true) })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [contactId])

  /* render 位才翻（module-scope const 只存 key + fallback） */
  const srcLabel = (s?: string | null): string => {
    const m = s ? SOURCE_LABEL[s] : undefined
    return m ? t(m.key, { defaultValue: m.fb }) : (s || '—')
  }
  const fldLabel = (f: string): string => {
    const m = FIELD_LABEL[f]
    return m ? t(m.key, { defaultValue: m.fb }) : f
  }

  if (failed || (!loading && rows.length === 0)) return null

  return (
    <section className="cch-wrap">
      <div className="cch-head">
        <h3 className="cch-title">{t('contact.history.title', { defaultValue: '欄位變更紀錄' })}</h3>
        <span className="cch-count">{rows.length}</span>
      </div>
      <p className="cch-sub">
        {t('contact.history.sub', { defaultValue: '每次改動一行 — 時間、來源、舊值 → 新值' })}
      </p>
      {loading ? (
        <div className="cch-empty">{t('common.loading', { defaultValue: 'Loading…' })}</div>
      ) : (
        <ul className="cch-list">
          {rows.map((r) => (
            <li key={r.id} className={`cch-row${r.verification_status === 'retracted' ? ' is-retracted' : ''}`}>
              <div className="cch-meta">
                <span className="cch-time">{fmt(r.changed_at)}</span>
                <span className="cch-badge">{srcLabel(r.source)}</span>
                {r.verification_status === 'retracted' && (
                  <span className="cch-badge is-warn">
                    {t('contact.history.retracted', { defaultValue: '已撤回' })}
                  </span>
                )}
              </div>
              <div className="cch-line">
                <span className="cch-field">{fldLabel(r.field)}</span>
                <span className="cch-old">{r.old_value || '—'}</span>
                <span className="cch-arrow" aria-hidden="true">→</span>
                <span className="cch-new">{r.new_value || '—'}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
