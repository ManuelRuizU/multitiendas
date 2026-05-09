import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useCart } from '../context/CartContext'

const fmt = (p) => `$${parseInt(p).toLocaleString('es-CL')}`

export default function CartDrawer() {
  const navigate  = useNavigate()
  const { pathname } = useLocation()
  const {
    cart, itemCount,
    isCartOpen, closeCart,
    updateItem, removeItem,
  } = useCart()

  const [busy, setBusy] = useState({})

  // Lock body scroll while open
  useEffect(() => {
    document.body.style.overflow = isCartOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [isCartOpen])

  // Hide entirely on checkout (component still mounts so scroll-lock cleans up)
  if (pathname === '/checkout') return null

  const isEmpty = !cart || cart.esta_vacio

  const withBusy = async (key, fn) => {
    setBusy((b) => ({ ...b, [key]: true }))
    try { await fn() } finally { setBusy((b) => ({ ...b, [key]: false })) }
  }

  const goToCheckout = () => {
    closeCart()
    navigate('/checkout')
  }

  return (
    /* ── Root: always in DOM for smooth transitions ── */
    <div
      className={[
        'fixed inset-0 z-[60] flex justify-end',
        isCartOpen ? '' : 'pointer-events-none',
      ].join(' ')}
      aria-hidden={!isCartOpen}
    >
  {/* Backdrop */}
<div
  onClick={closeCart}
  aria-hidden="true"
  className={[
    'absolute inset-0 bg-black/65 backdrop-blur-sm',
    'transition-opacity duration-[450ms] ease-[cubic-bezier(0.32,0,0.15,1)]',
    isCartOpen ? 'opacity-100' : 'opacity-0',
  ].join(' ')}
/>

{/* Panel */}
<div
  role="dialog"
  aria-modal="true"
  aria-label="Carrito de compras"
  className={[
    'relative flex flex-col',
    'w-[85vw] sm:w-[400px] h-full',
    'bg-slate-900 border-l border-white/10',
    'transition-transform duration-[450ms] ease-[cubic-bezier(0.32,0,0.15,1)]',
    isCartOpen ? 'translate-x-0' : 'translate-x-full',
  ].join(' ')}
>

        {/* ── Panel header ── */}
        <div className="shrink-0 flex items-center justify-between px-4 py-4 border-b border-white/10">
          <div>
            <h2 className="font-bold text-white text-base leading-none">Mi Carrito</h2>
            {itemCount > 0 && (
              <p className="text-xs text-white/40 mt-0.5">
                {itemCount} {itemCount === 1 ? 'producto' : 'productos'}
              </p>
            )}
          </div>
          <button
            onClick={closeCart}
            aria-label="Cerrar carrito"
            className="w-8 h-8 flex items-center justify-center rounded-full text-white/50 hover:text-white hover:bg-white/10 transition-colors text-lg"
          >
            ✕
          </button>
        </div>

        {/* ── Scrollable body ── */}
        <div className="flex-1 overflow-y-auto overscroll-contain px-4 py-4 space-y-5">

          {/* Empty state */}
          {isEmpty && (
            <div className="flex flex-col items-center justify-center gap-3 pt-16 text-white/30">
              <span aria-hidden="true" className="text-5xl">🛒</span>
              <p className="text-sm font-medium">Tu carrito está vacío</p>
              <button
                onClick={closeCart}
                className="text-sm text-orange-400 hover:text-orange-300 transition-colors mt-1"
              >
                ← Seguir comprando
              </button>
            </div>
          )}

          {/* Groups by store */}
          {!isEmpty && cart.grupos.map((grupo) => (
            <section key={grupo.tienda_id} aria-label={`Productos de ${grupo.tienda_nombre}`}>

              {/* Store name */}
              <div className="flex items-center gap-2 mb-2">
                {grupo.tienda_logo
                  ? <img src={grupo.tienda_logo} alt="" aria-hidden="true" className="w-5 h-5 rounded object-cover" />
                  : <span aria-hidden="true" className="text-sm">🏪</span>
                }
                <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wide">
                  {grupo.tienda_nombre}
                </h3>
              </div>

              {/* Items */}
              <div className="space-y-2">
                {grupo.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-2 bg-white/[0.04] rounded-xl px-3 py-2.5"
                  >
                    {/* Name + price */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white leading-snug truncate">{item.nombre_producto}</p>
                      <p className="text-xs text-orange-400 mt-0.5">{fmt(item.subtotal)}</p>
                    </div>

                    {/* Qty controls */}
                    <div
                      className="flex items-center gap-1 shrink-0"
                      role="group"
                      aria-label={`Cantidad de ${item.nombre_producto}`}
                    >
                      <button
                        disabled={busy[item.id]}
                        onClick={() => withBusy(item.id, () => updateItem(item.producto, item.cantidad - 1))}
                        aria-label={`Reducir cantidad de ${item.nombre_producto}`}
                        className="w-6 h-6 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-xs font-bold disabled:opacity-30 transition-colors"
                      >
                        −
                      </button>
                      <span
                        className="text-sm font-semibold w-5 text-center"
                        aria-live="polite"
                        aria-label={`${item.cantidad} unidades`}
                      >
                        {item.cantidad}
                      </span>
                      <button
                        disabled={busy[item.id]}
                        onClick={() => withBusy(item.id, () => updateItem(item.producto, item.cantidad + 1))}
                        aria-label={`Aumentar cantidad de ${item.nombre_producto}`}
                        className="w-6 h-6 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-xs font-bold disabled:opacity-30 transition-colors"
                      >
                        +
                      </button>
                      <button
                        disabled={busy[item.id]}
                        onClick={() => withBusy(item.id, () => removeItem(item.producto))}
                        aria-label={`Eliminar ${item.nombre_producto}`}
                        className="w-6 h-6 rounded-full bg-red-900/30 hover:bg-red-800/50 text-red-400 flex items-center justify-center text-[10px] disabled:opacity-30 transition-colors ml-0.5"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Group subtotal */}
              <div className="flex justify-between text-xs text-white/35 mt-2 px-1">
                <span>Subtotal {grupo.tienda_nombre}</span>
                <span className="font-semibold text-white/55">{fmt(grupo.subtotal ?? grupo.total ?? 0)}</span>
              </div>
            </section>
          ))}
        </div>

        {/* ── Footer ── */}
        {!isEmpty && (
          <div className="shrink-0 border-t border-white/10 px-4 py-4 space-y-3 bg-slate-900">
            {/* Total row */}
            <div className="flex items-center justify-between">
              <span className="font-bold text-sm text-white">Total</span>
              <span className="font-bold text-lg text-orange-400">{fmt(cart.total_global ?? 0)}</span>
            </div>

            {/* CTA */}
            <button
              onClick={goToCheckout}
              className="w-full bg-orange-500 hover:bg-orange-400 active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all"
            >
              Hacer pedido →
            </button>

            <button
              onClick={closeCart}
              className="w-full text-xs text-white/40 hover:text-white/70 transition-colors py-1"
            >
              ← Seguir comprando
            </button>
          </div>
        )}

      </div>
    </div>
  )
}
