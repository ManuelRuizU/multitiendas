import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import { useCart } from '../context/CartContext'

const fmt = (p) => `$${parseInt(p).toLocaleString('es-CL')}`

export default function CarritoPage() {
  const navigate = useNavigate()
  const { cart, updateItem, removeItem, clearCart } = useCart()

  const [busy, setBusy] = useState({})

  const withBusy = async (key, fn) => {
    setBusy((b) => ({ ...b, [key]: true }))
    try { await fn() } finally { setBusy((b) => ({ ...b, [key]: false })) }
  }

  const isEmpty = !cart || cart.esta_vacio

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Header title="Mi Carrito" onBack={() => navigate(-1)} />

      <main className="flex-1 max-w-3xl mx-auto w-full px-4 pt-6 pb-28">

        {/* Empty state */}
        {isEmpty && (
          <div className="flex flex-col items-center justify-center gap-4 pt-24 text-white/35">
            <p aria-hidden="true" className="text-5xl">🛒</p>
            <p className="font-medium">Tu carrito está vacío</p>
            <button
              onClick={() => navigate('/')}
              className="mt-2 text-sm text-orange-400 hover:text-orange-300 transition-colors"
            >
              Explorar tiendas →
            </button>
          </div>
        )}

        {/* Cart groups */}
        {!isEmpty && cart.grupos.map((grupo) => (
          <section key={grupo.tienda_id} aria-label={`Productos de ${grupo.tienda_nombre}`} className="mb-6">

            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-sm">{grupo.tienda_nombre}</h2>
              <span className="text-xs text-white/40">
                {grupo.total_items} item{grupo.total_items !== 1 ? 's' : ''}
              </span>
            </div>

            <div className="bg-white/[0.03] border border-white/5 rounded-2xl overflow-hidden divide-y divide-white/5">
              {grupo.items.map((item) => (
                <div key={item.id} className="flex items-center gap-3 p-3">

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{item.nombre_producto}</p>
                    <p className="text-xs text-orange-400 mt-0.5">{fmt(item.subtotal)}</p>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0" role="group" aria-label={`Cantidad de ${item.nombre_producto}`}>
                    <button
                      disabled={busy[item.id]}
                      onClick={() => withBusy(item.id, () => updateItem(item.producto, item.cantidad - 1))}
                      aria-label={`Reducir cantidad de ${item.nombre_producto}`}
                      className="w-7 h-7 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-sm font-bold disabled:opacity-30 transition-colors"
                    >
                      −
                    </button>

                    <span className="text-sm font-semibold w-5 text-center" aria-live="polite">
                      {item.cantidad}
                    </span>

                    <button
                      disabled={busy[item.id]}
                      onClick={() => withBusy(item.id, () => updateItem(item.producto, item.cantidad + 1))}
                      aria-label={`Aumentar cantidad de ${item.nombre_producto}`}
                      className="w-7 h-7 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-sm font-bold disabled:opacity-30 transition-colors"
                    >
                      +
                    </button>

                    <button
                      disabled={busy[item.id]}
                      onClick={() => withBusy(item.id, () => removeItem(item.producto))}
                      aria-label={`Eliminar ${item.nombre_producto} del carrito`}
                      className="w-7 h-7 rounded-full bg-red-900/30 hover:bg-red-800/50 text-red-400 flex items-center justify-center text-xs disabled:opacity-30 transition-colors ml-1"
                    >
                      ✕
                    </button>
                  </div>

                </div>
              ))}
            </div>

            <div className="flex justify-between items-center mt-2 px-1 text-xs text-white/40">
              <span>Subtotal {grupo.tienda_nombre}</span>
              <span className="font-semibold text-white/65">{fmt(grupo.subtotal ?? grupo.total ?? 0)}</span>
            </div>

          </section>
        ))}

      </main>

      {/* Sticky footer — only when cart has items */}
      {!isEmpty && (
        <div className="fixed bottom-0 left-0 right-0 bg-slate-950/95 backdrop-blur-sm border-t border-white/10 px-4 py-4">
          <div className="max-w-3xl mx-auto flex items-center gap-3">
            <div className="flex-1">
              <p className="text-xs text-white/40">Total</p>
              <p className="text-xl font-bold text-orange-400">{fmt(cart.total_global ?? 0)}</p>
            </div>
            <button
              onClick={() => withBusy('clear', clearCart)}
              disabled={busy['clear']}
              aria-label="Vaciar carrito"
              className="text-xs text-white/35 hover:text-white/65 transition-colors px-3 py-2 disabled:opacity-30 rounded-full hover:bg-white/5"
            >
              Vaciar
            </button>
            <button
              onClick={() => navigate('/checkout')}
              className="bg-orange-500 hover:bg-orange-400 text-white font-semibold text-sm px-6 py-2.5 rounded-full transition-colors active:scale-95"
            >
              Hacer pedido
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
