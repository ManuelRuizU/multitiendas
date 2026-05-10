// Modal.jsx
import { useEffect } from 'react'

/**
 * Modal accesible con animación suave.
 * Mobile: desliza desde abajo. Desktop: escala desde el centro.
 */
export default function Modal({ open, onClose, title, children }) {
  // Lock body scroll
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  return (
    <div
      className={[
        'fixed inset-0 z-[80] flex items-end sm:items-center justify-center sm:px-4',
        open ? '' : 'pointer-events-none',
      ].join(' ')}
      aria-hidden={!open}
    >
      {/* ── Backdrop ── */}
      <div
        onClick={onClose}
        aria-hidden="true"
        className={[
          'absolute inset-0 bg-black/70 backdrop-blur-sm',
          'transition-opacity duration-300 ease-out',
          open ? 'opacity-100' : 'opacity-0',
        ].join(' ')}
      />

      {/* ── Panel ── */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={[
          'relative w-full sm:max-w-sm',
          'bg-slate-900 border border-white/10',
          'rounded-t-3xl sm:rounded-2xl',
          'shadow-2xl shadow-black/60',
          'flex flex-col max-h-[92dvh]',
          // Mobile: slide-up  |  Desktop: scale + fade
          'transition-all duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)]',
          open
            ? 'opacity-100 translate-y-0 sm:scale-100'
            : 'opacity-0 translate-y-full sm:translate-y-0 sm:scale-95',
        ].join(' ')}
      >
        {/* Drag handle — mobile only */}
        <div
          aria-hidden="true"
          className="sm:hidden w-10 h-1 bg-white/20 rounded-full mx-auto mt-3"
        />

        {/* Header */}
        {title && (
          <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-white/10">
            <h2 className="font-bold text-base text-white">{title}</h2>
            <button
              onClick={onClose}
              aria-label="Cerrar"
              className="w-7 h-7 flex items-center justify-center rounded-full text-white/40 hover:text-white hover:bg-white/10 transition-colors text-sm"
            >
              ✕
            </button>
          </div>
        )}

        {/* Body */}
        <div className="px-5 pb-6 pt-5 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  )
}
