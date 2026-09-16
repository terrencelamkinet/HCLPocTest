import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import SvcIcon from '../components/SvcIcon'
import { apiClient } from '../lib/api'
import { EntitySearch } from './EntitySearch'
import type { NameCardRecord, LinkedContact } from './module-types'

/* ═══════════════════════════════════════════════════════════
   NameCardDetailModal — Original vs Cropped image compare,
   editable fields, tag management, contact linking, and
   destructive/duplicate actions.
   ═══════════════════════════════════════════════════════════ */

interface Props {
  card: NameCardRecord
  onClose: () => void
  onSaved: () => void
  onDeleted: () => void
}

export function NameCardDetailModal({ card, onClose, onSaved, onDeleted }: Props) {
  const { t } = useTranslation()
  const pd = card.parsed_data || {}
  const [form, setForm] = useState({
    name: pd.name || card.name || '',
    title: pd.title || card.title || '',
    email: pd.email || card.email || '',
    phone: pd.phone || card.phone || '',
    /* 2026-09-15 Terrence：「除了 office phone 外要有 mobile phone」⇒ 兩個號碼分開欄位 */
    mobile: (pd as any).mobile || (card as any).mobile || '',
    office_phone: (pd as any).office_phone || (card as any).office_phone || '',
    fax: (pd as any).fax || (card as any).fax || '',
    address: (pd as any).address || (card as any).address || '',
    company: pd.company || card.company || '',
  })
  const [tags, setTags] = useState<string[]>(card.tags || [])
  const [tagInput, setTagInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [linkedContact, setLinkedContact] = useState<LinkedContact | null>((card.contact as LinkedContact | null) || null)
  const [showLinkSearch, setShowLinkSearch] = useState(false)
  const linkedContactId: string = linkedContact ? linkedContact.id : ''
  /* WORKFLOW-2026-09: pending resolve state */
  const [resolving, setResolving] = useState(false)
  const isPending = (card as any).status === 'review' || (card as any).status === 'pending'
  const candRaw = (card as any).review_candidates?.[0] || card.duplicate_candidate || null
  const candName = candRaw?.name || (candRaw?.contact_id ? '現有聯絡人' : '') || '現有聯絡人'

  /* 2026-09-13 Terrence（v4 README a11y 要求）：舊版 modal 完全冇 a11y 接駁
     （grep 全檔：role= / aria-* / Escape / useEffect 全部 0 個）⇒ 補：
     Escape 關閉、開時 focus 入對話框、關時 focus 還原、鎖背景捲動。 */
  const dialogRef = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    const prevActive = document.activeElement as HTMLElement | null
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.stopPropagation(); onClose() } }
    document.addEventListener('keydown', onKey)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    dialogRef.current?.focus()
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
      prevActive?.focus?.()
    }
  }, [onClose])

  /* 2026-09-15 Terrence spec：pending 卡重複決定 = 3 個 object
     ① replace  — 取代現有（舊值自動存入 contact_changes history；contact status 更新）
     ② separate — 開新記錄（唔覆蓋現有，兩者並存）
     ③ delete   — 刪除新卡（唔覆蓋、唔留痕）→ handleDiscard
     ⚠️ 舊版只有 merge（只補空白、永不覆蓋）＋ separate，同 spec 唔一致。 */
  const handleResolve = async (action: 'replace' | 'separate') => {
    if (action === 'replace' && !candRaw?.contact_id) {
      alert(t('nameCard.noMergeTarget', { defaultValue: '冇取代目標 — 先揀一個現有聯絡人' }))
      return
    }
    setResolving(true)
    try {
      await apiClient.post(`/api/v1/crm/name-cards/${card.id}/resolve`, { action })
      onSaved()
    } catch (e: any) {
      alert(e?.detail || e?.message || '處理失敗')
    } finally {
      setResolving(false)
    }
  }

  const handleAddTag = () => {
    const val = tagInput.trim()
    if (val && !tags.includes(val)) setTags(tg => [...tg, val])
    setTagInput('')
  }
  const removeTag = (tg: string) => setTags(tags.filter(x => x !== tg))

  const handleSave = async () => {
    setSaving(true)
    try {
      await apiClient.patch(`/api/v1/crm/name-cards/${card.id}`, {
        ...form, tags, contact_id: linkedContact?.id || null,
        /* phone = 主要電話（手機優先）；mobile / office_phone 分開存 */
        phone: form.mobile || form.office_phone || form.phone,
      })
      onSaved()
    } catch (e: any) {
      alert(e.detail || e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(t('nameCard.confirmDelete', { defaultValue: '刪除呢張名片？' }))) return
    await apiClient.delete(`/api/v1/crm/name-cards/${card.id}`)
    onDeleted()
  }

  /* ③ 刪除新卡 — 唔覆蓋現有聯絡人，亦唔留任何 contact 痕跡 */
  const handleDiscard = async () => {
    if (!confirm(t('nameCard.confirmDiscard', { defaultValue: '刪除呢張新卡？現有聯絡人唔會被改動。' }))) return
    setResolving(true)
    try {
      await apiClient.delete(`/api/v1/crm/name-cards/${card.id}`)
      onDeleted()
    } catch (e: any) {
      alert(e?.detail || e?.message || '刪除失敗')
    } finally {
      setResolving(false)
    }
  }

  const handleDuplicate = async () => {
    await apiClient.post(`/api/v1/crm/name-cards/${card.id}/duplicate`, {})
    onSaved()
  }

  const handleCopyContact = () => {
    const text = `${form.name}\n${form.title}\n${form.company}\n${form.email}\n${form.phone}`
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="nx-modal-overlay is-open" onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className="nx-modal nc-detail-modal is-open" role="dialog" aria-modal="true"
        aria-labelledby="nc-detail-title" tabIndex={-1} ref={dialogRef}>
        {/* 2026-09-15 Terrence「標題走位」：舊版用咗全 repo 冇定義嘅 .nx-modal-header /
            .nx-modal-title ⇒ 標題實測 13.76px / font-weight 400 ✗（手機同桌面都係）。
            改成全站 modal 標準 .nx-modal-head + h2（nexus-modal-tokens.css §Modal shell：
            18px/600，≥1280px 22px）＋ 順便取回手機 sticky header（關閉掣永遠可見）。 */}
        <div className="nx-modal-head">
          <h2 id="nc-detail-title">{t('nameCard.detailTitle', { defaultValue: '名片詳情' })}</h2>
          <button type="button" className="nx-modal-x" aria-label={t('common.close', { defaultValue: '關閉' })}
            onClick={onClose}><SvcIcon name="x" size={16} /></button>
        </div>

        <div className="nc-detail-modal-body">
          {/* ═══ Left: 名片圖（只有 Cropped）═══
              2026-09-15 Terrence spec：冇 Original 只有 Cropped ⇒ 拆走 tabs；
              圖要 full width（舊版 frame 硬寫 aspect-ratio 1.58:1 + contain ⇒ 左右留白）；
              refresh（recrop）／download 用途不大 ⇒ 拆走。 */}
          <div className="nc-detail-images">
            <div className="nc-image-frame">
              {(card.cropped_image_url || card.image_url) ? (
                <img src={card.cropped_image_url || card.image_url} alt={form.name || ''} />
              ) : (
                <div className="nc-image-empty">
                  {t('nameCard.imagePreview', { defaultValue: '名片圖片預覽' })}
                </div>
              )}
            </div>

            {/* ═══ Contact linking box ═══ */}
            <div className="nc-link-contact-box">
              {linkedContact ? (
                <div className="nc-link-contact-linked">
                  <div className="nc-link-avatar">{(linkedContact.name || '?').slice(0, 1)}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12.5, fontWeight: 700 }}>
                      {t('nameCard.linkedTo', { defaultValue: '已連結' })}：{linkedContact.name}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
                      {linkedContact.company_name} · {linkedContact.job_title}
                    </div>
                  </div>
                  <button className="nx-btn nx-btn-secondary" style={{ height: 28, fontSize: 11 }}
                    onClick={() => setLinkedContact(null)}
                    title={t('common.unlink', { defaultValue: '取消連結' })}
                    aria-label={t('common.unlink', { defaultValue: '取消連結' })}>
                    <SvcIcon name="link-2-off" size={12} /> <span className="nc-btn-label">{t('common.unlink', { defaultValue: '取消連結' })}</span>
                  </button>
                </div>
              ) : showLinkSearch ? (
                <EntitySearch
                  searchUrl="/api/v1/crm/contacts?search="
                  value={linkedContactId}
                  placeholder={t('nameCard.searchContact', { defaultValue: '搜尋現有聯絡人…' })}
                  onChange={(cid: string) => {
                    // rebuild a minimal linked-concat object for display + save
                    setLinkedContact({ id: cid, name: '已選聯絡人', company_name: '', job_title: '' })
                    setShowLinkSearch(false)
                  }}
                />
              ) : (
                <button className="nx-btn nx-btn-secondary" style={{ width: '100%' }} onClick={() => setShowLinkSearch(true)}
                  title={t('nameCard.linkContact', { defaultValue: '連結聯絡人' })}
                  aria-label={t('nameCard.linkContact', { defaultValue: '連結聯絡人' })}>
                  <SvcIcon name="search" size={13} /> <span className="nc-btn-label">{t('nameCard.linkContact', { defaultValue: '連結聯絡人' })}</span>
                </button>
              )}
            </div>
          </div>

          {/* ═══ Right: Editable fields + tags + AI confidence ═══ */}
          <div className="nc-detail-fields">
            <div className="nc-detail-field-row">
              <div className="nx-field">
                <label>{t('fields.name', { defaultValue: '姓名' })}</label>
                <input className="input-field" value={form.name} onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))} />
              </div>
              <div className="nx-field">
                <label>{t('fields.jobTitle', { defaultValue: '職位' })}</label>
                <input className="input-field" value={form.title} onChange={(e) => setForm(f => ({ ...f, title: e.target.value }))} />
              </div>
            </div>
            <div className="nc-detail-field-row">
              <div className="nx-field">
                <label>{t('fields.email', { defaultValue: 'Email' })}</label>
                <input className="input-field" value={form.email} onChange={(e) => setForm(f => ({ ...f, email: e.target.value }))} />
              </div>
              <div className="nx-field">
                <label>{t('nameCard.fMobile', { defaultValue: '手機' })}</label>
                <input className="input-field" value={form.mobile} onChange={(e) => setForm(f => ({ ...f, mobile: e.target.value }))} />
              </div>
            </div>
            <div className="nc-detail-field-row">
              <div className="nx-field" style={{ flex: 1 }}>
                <label>{t('nameCard.fOfficePhone', { defaultValue: '公司電話' })}</label>
                <input className="input-field" value={form.office_phone} onChange={(e) => setForm(f => ({ ...f, office_phone: e.target.value }))} />
              </div>
            </div>
            <div className="nc-detail-field-row">
              <div className="nx-field" style={{ flex: 1 }}>
                <label>{t('nameCard.fFax', { defaultValue: '傳真' })}</label>
                <input className="input-field" value={form.fax} onChange={(e) => setForm(f => ({ ...f, fax: e.target.value }))} />
              </div>
            </div>
            <div className="nc-detail-field-row">
              <div className="nx-field" style={{ flex: 1 }}>
                <label>{t('nameCard.fAddress', { defaultValue: '公司地址' })}</label>
                <input className="input-field" value={form.address} onChange={(e) => setForm(f => ({ ...f, address: e.target.value }))} />
              </div>
            </div>
            <div className="nc-detail-field-row">
              <div className="nx-field" style={{ flex: 1 }}>
                <label>{t('fields.company', { defaultValue: '公司' })}</label>
                <input className="input-field" value={form.company} onChange={(e) => setForm(f => ({ ...f, company: e.target.value }))} />
              </div>
            </div>

            {/* ═══ Tags ═══ */}
            <div style={{ marginTop: 16 }}>
              <label style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                {t('nameCard.tags', { defaultValue: '分類 Tag' })}
              </label>
              <div className="nc-detail-tags-edit">
                {tags.map(tg => (
                  <span className="nc-tag-editable" key={tg}>
                    🏷 {tg} <button type="button" className="nc-tag-remove"
                      aria-label={`${t('common.remove', { defaultValue: '移除' })} ${tg}`}
                      onClick={() => removeTag(tg)}>✕</button>
                  </span>
                ))}
                <input
                  className="nc-tag-add-input"
                  placeholder={t('common.addTag', { defaultValue: '+ 新增' })}
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleAddTag() }}
                  onBlur={handleAddTag}
                />
              </div>
            </div>

            {/* 2026-09-15 Terrence：「add tag 下有個紫色 area，請 remove」= 舊版嘅 AI confidence 格
                （rgba(124,92,252,.06) 紫色框）。佢只重覆 compare 區已有嘅 reason，
                而且冇 reason 時仲會出一個空紫盒 ⇒ 整個拆走。 */}

            {/* 2026-09-13 Terrence（v4 MD suggestion T5）：重複卡唔再淨係一句 reason —
                逐個欄位同「現有聯絡人」並排對照，唔同嘅欄位高亮，一眼決定要唔要併入。
                欄位同 backend review_candidates 嘅 shape 一一對應（crm.py:2209）。 */}
            {isPending && candRaw && (() => {
              const FIELDS: { key: 'name' | 'company' | 'title' | 'phone' | 'mobile' | 'office_phone' | 'fax' | 'address' | 'email'; labelKey: string; zh: string }[] = [
                { key: 'name', labelKey: 'nameCard.fName', zh: '姓名' },
                { key: 'company', labelKey: 'nameCard.fCompany', zh: '公司' },
                { key: 'title', labelKey: 'nameCard.fTitle', zh: '職位' },
                { key: 'mobile', labelKey: 'nameCard.fMobile', zh: '手機' },
                { key: 'office_phone', labelKey: 'nameCard.fOfficePhone', zh: '公司電話' },
                { key: 'fax', labelKey: 'nameCard.fFax', zh: '傳真' },
                { key: 'address', labelKey: 'nameCard.fAddress', zh: '公司地址' },
                { key: 'email', labelKey: 'nameCard.fEmail', zh: 'Email' },
              ]
              const norm = (v: any) => String(v ?? '').trim().toLowerCase().replace(/\s+/g, '')
              // P0.5（2026-09-15，P仔 review）：冇時間軸 → 用戶判唔到邊條新。固定 MM-DD HH:mm，唔用 locale format。
              const fmtTime = (v: any) => {
                if (!v) return '—'
                const d = new Date(v)
                if (isNaN(d.getTime())) return '—'
                const p = (n: number) => String(n).padStart(2, '0')
                return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
              }
              return (
                <div className="nc-cmp">
                  {/* 2026-09-15 Terrence：「New and existing compares 頂要有 name card image preview」*/}
                  <div className="nc-cmp-previews">
                    <div className="nc-cmp-preview">
                      <span className="nc-cmp-preview-cap">{t('nameCard.cmpNewCard', { defaultValue: '呢張新卡' })}</span>
                      {(card.cropped_image_url || card.image_url) ? (
                        <img src={card.cropped_image_url || card.image_url} alt="" />
                      ) : (
                        <div className="nc-cmp-preview-empty">{t('nameCard.noImage', { defaultValue: '冇圖' })}</div>
                      )}
                    </div>
                    <div className="nc-cmp-preview">
                      <span className="nc-cmp-preview-cap">
                        {t('nameCard.cmpExisting', { defaultValue: '現有聯絡人' })}：{candName}
                      </span>
                      {(candRaw as any).image_url ? (
                        <img src={(candRaw as any).image_url} alt="" />
                      ) : (
                        <div className="nc-cmp-preview-empty">{t('nameCard.noCardImage', { defaultValue: '冇名片圖' })}</div>
                      )}
                    </div>
                  </div>
                  <div className="nc-cmp-row nc-cmp-head">
                    <span className="nc-cmp-label" />
                    <span className="nc-cmp-val">{t('nameCard.cmpNewCard', { defaultValue: '呢張新卡' })}</span>
                    <span className="nc-cmp-val">
                      {t('nameCard.cmpExisting', { defaultValue: '現有聯絡人' })}：{candName}
                      {candRaw.confidence ? `（${Math.round(Number(candRaw.confidence) * 100)}%）` : ''}
                    </span>
                  </div>
                  {FIELDS.map(f => {
                    const newV = String((form as any)[f.key] ?? '')
                    const oldV = String((candRaw as any)[f.key] ?? '')
                    const diff = norm(newV) !== norm(oldV)
                    return (
                      <div className={`nc-cmp-row ${diff ? 'is-diff' : ''}`} key={f.key}>
                        <span className="nc-cmp-label">{t(f.labelKey, { defaultValue: f.zh })}</span>
                        <span className="nc-cmp-val">{newV || '—'}</span>
                        <span className="nc-cmp-val">{oldV || '—'}</span>
                      </div>
                    )
                  })}
                  {/* P0.5（2026-09-15，P仔 review）：新卡掃描時間 vs 現有聯絡人最後更新時間 */}
                  <div className="nc-cmp-row">
                    <span className="nc-cmp-label">{t('nameCard.cmpTime', { defaultValue: '時間' })}</span>
                    <span className="nc-cmp-val">{fmtTime(card.created_at)}</span>
                    <span className="nc-cmp-val">{fmtTime((candRaw as any).updated_at)}</span>
                  </div>
                  {candRaw.reason && <div className="nc-cmp-reason">🤖 {candRaw.reason}</div>}
                </div>
              )
            })()}

            {/* 2026-09-15 Terrence spec：重複決定 = 3 個 object，每個寫明後果 */}
            {isPending && (
              <div className="nc-resolve-bar">
                <div className="nc-resolve-title">
                  📥 {t('nameCard.pendingResolveTitle', { defaultValue: '發現重複 — 決定：' })}
                </div>
                <div className="nc-resolve-actions">
                  <button type="button" className="nx-btn nx-btn-primary"
                    onClick={() => handleResolve('replace')} disabled={resolving}>
                    <SvcIcon name="merge" size={13} />
                    <span className="nc-btn-label">
                      {t('nameCard.replaceExisting', { defaultValue: '取代現有' })}
                      {candName ? `（${candName}）` : ''}
                    </span>
                    <span className="nc-resolve-sub">
                      {t('nameCard.replaceExistingSub', { defaultValue: '現有資料自動存入紀錄（history），聯絡人狀態同步更新' })}
                    </span>
                  </button>
                  <button type="button" className="nx-btn nx-btn-secondary"
                    onClick={() => handleResolve('separate')} disabled={resolving}>
                    <SvcIcon name="user-plus" size={13} />
                    <span className="nc-btn-label">{t('nameCard.createNew', { defaultValue: '開新記錄' })}</span>
                    <span className="nc-resolve-sub">
                      {t('nameCard.createNewSub', { defaultValue: '唔取代現有，以新記錄形式並存' })}
                    </span>
                  </button>
                  <button type="button" className="nx-btn nc-btn-danger-ghost"
                    onClick={handleDiscard} disabled={resolving}>
                    <SvcIcon name="trash-2" size={13} />
                    <span className="nc-btn-label">{t('nameCard.discardNew', { defaultValue: '刪除新卡' })}</span>
                    <span className="nc-resolve-sub">
                      {t('nameCard.discardNewSub', { defaultValue: '刪除新記錄，唔會覆蓋現有' })}
                    </span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="nc-detail-footer">
          <div className="nc-detail-footer-left">
            <button className="nx-btn nc-btn-danger-ghost" onClick={handleDelete}
              title={t('common.delete', { defaultValue: '刪除' })}
              aria-label={t('common.delete', { defaultValue: '刪除' })}>
              <SvcIcon name="trash-2" size={13} /> <span className="nc-btn-label">{t('common.delete', { defaultValue: '刪除' })}</span>
            </button>
            <button className="nx-btn nx-btn-secondary" onClick={handleCopyContact}
              title={t('nameCard.copyContact', { defaultValue: '複製名片' })}
              aria-label={t('nameCard.copyContact', { defaultValue: '複製名片' })}>
              <SvcIcon name="copy" size={13} /> <span className="nc-btn-label">{t('nameCard.copyContact', { defaultValue: '複製名片' })}</span>
            </button>
            <button className="nx-btn nx-btn-secondary" onClick={handleDuplicate}
              title={t('nameCard.duplicateCard', { defaultValue: '建立副本' })}
              aria-label={t('nameCard.duplicateCard', { defaultValue: '建立副本' })}>
              <SvcIcon name="files" size={13} /> <span className="nc-btn-label">{t('nameCard.duplicateCard', { defaultValue: '建立副本' })}</span>
            </button>
          </div>
          <button className="nx-btn nx-btn-primary" onClick={handleSave} disabled={saving}
            title={t('common.saveChanges', { defaultValue: '儲存變更' })}
            aria-label={t('common.saveChanges', { defaultValue: '儲存變更' })}>
            {saving ? t('common.saving') : (<><SvcIcon name="check" size={13} /> <span className="nc-btn-label">{t('common.saveChanges', { defaultValue: '儲存變更' })}</span></>)}
          </button>
        </div>
      </div>
    </div>
  )
}
