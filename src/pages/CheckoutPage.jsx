import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import { useCart } from '../context/CartContext'

const fmt = (p) => `$${parseInt(p).toLocaleString('es-CL')}`

function buildWhatsAppUrl(waUrl, grupo) {
  if (!waUrl) return null
  const lines = [
    `Hola! 👋 Quiero hacer el siguiente pedido desde *MultiTienda Angol*:\n`,
  ]
  for (const item of grupo.items) {
    lines.push(`• ${item.cantidad}× ${item.nombre_producto} — ${fmt(item.subtotal)}`)
  }
  lines.push(`\n💰 *Subtotal:* ${fmt(grupo.subtotal)}`)
  const envio = parseInt(grupo.costo_envio ?? 0)
  if (envio > 0) lines.push(`🚚 *Envío:* ${fmt(grupo.costo_envio)}`)
  lines.push(`✅ *Total:* ${fmt(grupo.total)}\n\n¡Gracias!`)
  const base = waUrl.replace(/\/$/, '')
  return `${base}?text=${encodeURIComponent(lines.join('\n'))}`
}

// ── Success screen ───────────────────────────────────────────────────
function SuccessScreen({ grupos, onRestart }) {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header title="Pedido confirmado" />

      <main className="max-w-lg mx-auto px-4 pt-10 pb-20 flex flex-col items-center text-center">

        <div
          role="img"
          aria-label="Pedido confirmado"
          className="w-20 h-20 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center text-4xl mb-6"
        >
          ✅
        </div>

        <h1 className="text-xl font-bold mb-2">¡Pedido confirmado!</h1>
        <p className="text-sm text-white/45 mb-8 max-w-xs leading-relaxed">
          Ahora contacta a cada tienda por WhatsApp para coordinar la entrega y el pago.
        </p>

        <div className="w-full space-y-3 mb-10" role="list" aria-label="Tiendas a contactar">
          {grupos.map((grupo) => {
            const waUrl = buildWhatsAppUrl(grupo.tienda_whatsapp_url, grupo)
            const count = grupo.items.length
            return (
              <article
                key={grupo.tienda_id}
                role="listitem"
                className="bg-white/[0.04] border border-white/10 rounded-2xl p-4 text-left"
              >
                <div className="flex items-center gap-2 mb-1">
                  {grupo.tienda_logo
                    ? <img src={grupo.tienda_logo} alt="" aria-hidden="true" className="w-7 h-7 rounded-lg object-cover" />
                    : <span aria-hidden="true" className="text-xl">🏪</span>
                  }
                  <p className="font-semibold text-sm">{grupo.tienda_nombre}</p>
                </div>
                <p className="text-xs text-white/40 mb-3">
                  {count} producto{count !== 1 ? 's' : ''} · {fmt(grupo.total)}
                </p>

                {waUrl ? (
                  <a
                    href={waUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`Contactar a ${grupo.tienda_nombre} por WhatsApp`}
                    className="flex items-center justify-center gap-2 bg-green-600 hover:bg-green-500 text-white text-sm font-semibold px-4 py-2.5 rounded-full transition-colors w-full"
                  >
                    <span aria-hidden="true">📲</span>
                    Contactar por WhatsApp
                  </a>
                ) : (
                  <p className="text-xs text-white/25 text-center italic">
                    Esta tienda no tiene WhatsApp configurado
                  </p>
                )}
              </article>
            )
          })}
        </div>

        <button
          onClick={onRestart}
          className="text-sm text-orange-400 hover:text-orange-300 transition-colors"
        >
          ← Hacer otro pedido
        </button>

      </main>
    </div>
  )
}

// ── Checkout main screen ─────────────────────────────────────────────
export default function CheckoutPage() {
  const navigate = useNavigate()
  const { cart, clearCart } = useCart()

  const [submitting, setSubmitting] = useState(false)
  const [confirmed,  setConfirmed]  = useState(false)
  const [orderGroups, setOrderGroups] = useState([])

  const isEmpty = !cart || cart.esta_vacio

  const handleConfirm = async () => {
    if (!cart?.grupos?.length) return
    setSubmitting(true)
    const grupos = [...cart.grupos]   // snapshot before clearing
    try { await clearCart() } catch { /* ignore — order already "confirmed" */ }
    setOrderGroups(grupos)
    setConfirmed(true)
    setSubmitting(false)
  }

  if (confirmed) {
    return <SuccessScreen grupos={orderGroups} onRestart={() => navigate('/')} />
  }

  if (isEmpty) {
    return (
      <div className="min-h-screen bg-slate-950 text-white">
        <Header title="Checkout" onBack={() => navigate('/carrito')} />
        <main className="flex flex-col items-center justify-center gap-4 pt-24 text-white/30">
          <p aria-hidden="true" className="text-4xl">🛒</p>
          <p className="text-sm">No hay productos en tu carrito</p>
          <button onClick={() => navigate('/')} className="text-orange-400 text-sm hover:underline">
            ← Explorar tiendas
          </button>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header title="Confirmar pedido" onBack={() => navigate('/carrito')} />

      <main className="max-w-lg mx-auto px-4 pt-6 pb-36">

        <h2 className="text-xs font-semibold text-white/40 uppercase tracking-widest mb-4">
          Resumen del pedido
        </h2>

        {/* Groups by store */}
        {cart.grupos.map((grupo) => (
          <section
            key={grupo.tienda_id}
            aria-label={`Pedido en ${grupo.tienda_nombre}`}
            className="bg-white/[0.04] border border-white/5 rounded-2xl overflow-hidden mb-4"
          >
            {/* Store header */}
            <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2">
              {grupo.tienda_logo
                ? <img src={grupo.tienda_logo} alt="" aria-hidden="true" className="w-7 h-7 rounded-lg object-cover" />
                : <span aria-hidden="true" className="text-xl">🏪</span>
              }
              <span className="font-semibold text-sm">{grupo.tienda_nombre}</span>
            </div>

            {/* Items */}
            <ul className="divide-y divide-white/5">
              {grupo.items.map((item) => (
                <li key={item.id} className="flex justify-between items-center px-4 py-2.5">
                  <span className="text-sm">
                    <span className="text-white/45 mr-1.5" aria-label={`${item.cantidad} unidades`}>
                      {item.cantidad}×
                    </span>
                    {item.nombre_producto}
                  </span>
                  <span className="text-sm text-white/65 shrink-0 ml-3">{fmt(item.subtotal)}</span>
                </li>
              ))}
            </ul>

            {/* Subtotal row */}
            <div className="flex justify-between items-center px-4 py-3 border-t border-white/5 text-sm">
              <span className="text-white/45">Subtotal</span>
              <span className="font-semibold">{fmt(grupo.subtotal)}</span>
            </div>

            {/* Shipping if any */}
            {parseInt(grupo.costo_envio ?? 0) > 0 && (
              <div className="flex justify-between items-center px-4 pb-3 text-sm text-white/45">
                <span>Envío</span>
                <span>{fmt(grupo.costo_envio)}</span>
              </div>
            )}
          </section>
        ))}

        {/* Global total */}
        <div className="flex justify-between items-center px-1 py-3">
          <span className="font-bold text-base">Total</span>
          <span className="font-bold text-xl text-orange-400">{fmt(cart.total_global)}</span>
        </div>

        <p className="text-xs text-white/25 text-center mt-2 leading-relaxed">
          Al confirmar se generarán los enlaces de WhatsApp para que puedas coordinar la entrega con cada tienda.
        </p>

      </main>

      {/* Sticky footer */}
      <div className="fixed bottom-0 left-0 right-0 bg-slate-950/95 backdrop-blur-sm border-t border-white/10 px-4 py-4">
        <div className="max-w-lg mx-auto">
          <button
            onClick={handleConfirm}
            disabled={submitting}
            aria-busy={submitting}
            className="w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-sm py-4 rounded-2xl transition-colors flex items-center justify-center gap-2"
          >
            {submitting ? (
              <span className="text-white/70">Procesando…</span>
            ) : (
              <>
                <span aria-hidden="true">📲</span>
                Confirmar y contactar por WhatsApp
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
