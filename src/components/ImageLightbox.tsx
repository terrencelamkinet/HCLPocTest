import { useEffect } from 'react'
import SvcIcon from './SvcIcon'

/* ImageLightbox — 名片圖放大（2026-09-15 Terrence：click 放大 + 放大動畫） */
export default function ImageLightbox({ src, alt = '', caption, onClose }: {
  src: string
  alt?: string
  caption?: string
  onClose: () => void
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.stopPropagation(); onClose() } }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="nx-lightbox" onClick={onClose} role="dialog" aria-modal="true" aria-label={caption || alt || '名卡片'}>
      <button type="button" className="nx-lightbox-x" onClick={onClose} aria-label="關閉">
        <SvcIcon name="x" size={18} />
      </button>
      <figure className="nx-lightbox-figure" onClick={(e) => e.stopPropagation()}>
        <img src={src} alt={alt} />
        {caption && <figcaption>{caption}</figcaption>}
      </figure>
    </div>
  )
}
