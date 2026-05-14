import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import Modal from '../components/Modal'
import { useCart } from '../context/CartContext'

const fmt = (p) => `$${parseInt(p).toLocaleString('es-CL')}`

// ── Store schedule status ──────────────────────────────────────────
function getStoreStatus(grupo) {
  // If no hora_apertura, the store hasn't configured hours → always available
  if (!grupo.tienda_hora_apertura) return 'open'
  if (grupo.tienda_esta_abierta)   return 'open'
  if (grupo.tienda_acepta_programados) return 'schedulable'
  return 'closed'
}

// ── Time validation ────────────────────────────────────────────────
function validateScheduledTime(hora, apertura, cierre) {
  if (!hora) return 'Selecciona un horario'

  const now = new Date()
  const [h, m] = hora.split(':').map(Number)
  const horaDate = new Date(now)
  horaDate.setHours(h, m, 0, 0)

  // If selected time is in the past today, assume it's tomorrow
  if (horaDate <= now) horaDate.setDate(horaDate.getDate() + 1)

  const minTime = new Date(now.getTime() + 30 * 60 * 1000)
  if (horaDate < minTime) return 'El horario debe ser al menos 30 min desde ahora'

  if (apertura && cierre) {
    const toMin = (t) => { const [hh, mm] = t.split(':').map(Number); return hh * 60 + mm }
    const sel = toMin(hora), ap = toMin(apertura), cl = toMin(cierre)
    const inside = cl >= ap ? sel >= ap && sel <= cl : sel >= ap || sel <= cl
    if (!inside) return `Debe estar entre ${apertura} y ${cierre}`
  }
  return null
}

// ── WhatsApp URL builder ───────────────────────────────────────────
function buildWhatsAppUrl(waUrl, grupo, horaProgramada) {
  if (!waUrl) return null
  const lines = [`Hola! 👋 Quiero hacer el siguiente pedido desde *MultiTienda Angol*:\n`]
  for (const item of grupo.items) {
    lines.push(`• ${item.cantidad}× ${item.nombre_producto} — ${fmt(item.subtotal)}`)
  }
  lines.push(`\n💰 *Subtotal:* ${fmt(grupo.subtotal)}`)
  const envio = parseInt(grupo.costo_envio ?? 0)
  if (envio > 0) lines.push(`🚚 *Envío:* ${fmt(grupo.costo_envio)}`)
  lines.push(`✅ *Total:* ${fmt(grupo.total)}`)
  if (horaProgramada) lines.push(`\n🕐 *Hora de entrega solicitada:* ${horaProgramada}`)
  lines.push('\n¡Gracias!')
  return `${waUrl.replace(/\/$/, '')}?text=${encodeURIComponent(lines.join('\n'))}`
}

// ── Success screen ────────────────────────────────────────────────
function SuccessScreen({ grupos, horasSugeridas, onRestart }) {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header title="Pedido confirmado" />
      <main className="max-w-lg mx-auto px-4 pt-10 pb-20 flex flex-col items-center text-center">
        <div
          role="img" aria-label="Pedido confirmado"
          className="w-20 h-20 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center text-4xl mb-6"
        >
          ✅
        </div>
        <h1 className="text-xl font-bold mb-2">¡Pedido confirmado!</h1>
        <p className="text-sm text-white/45 mb-8 max-w-xs leading-relaxed">
          Contacta a cada tienda por WhatsApp para coordinar la entrega y el pago.
        </p>
        <div className="w-full space-y-3 mb-10" role="list" aria-label="Tiendas a contactar">
          {grupos.map((grupo) => {
            const horaProg = horasSugeridas?.[grupo.tienda_id]
            const waUrl = buildWhatsAppUrl(grupo.tienda_whatsapp_url, grupo, horaProg)
            const count = grupo.items.length
            return (
              <article key={grupo.tienda_id} role="listitem"
                className="bg-white/[0.04] border border-white/10 rounded-2xl p-4 text-left">
                <div className="flex items-center gap-2 mb-1">
                  {grupo.tienda_logo
                    ? <img src={grupo.tienda_logo} alt="" aria-hidden="true" className="w-7 h-7 rounded-lg object-cover" />
                    : <span aria-hidden="true" className="text-xl">🏪</span>
                  }
                  <p className="font-semibold text-sm">{grupo.tienda_nombre}</p>
                </div>
                <p className="text-xs text-white/40 mb-1">
                  {count} producto{count !== 1 ? 's' : ''} · {fmt(grupo.total)}
                </p>
                {horaProg && (
                  <p className="text-xs text-yellow-400/70 mb-3">🕐 Pedido para las {horaProg}</p>
                )}
                {waUrl ? (
                  <a href={waUrl} target="_blank" rel="noopener noreferrer"
                    aria-label={`Contactar a ${grupo.tienda_nombre} por WhatsApp`}
                    className="flex items-center justify-center gap-2 bg-green-600 hover:bg-green-500 text-white text-sm font-semibold px-4 py-2.5 rounded-full transition-colors w-full">
                    <span aria-hidden="true">📲</span> Contactar por WhatsApp
                  </a>
                ) : (
                  <p className="text-xs text-white/25 text-center italic">Sin WhatsApp configurado</p>
                )}
              </article>
            )
          })}
        </div>
        <button onClick={onRestart} className="text-sm text-orange-400 hover:text-orange-300 transition-colors">
          ← Hacer otro pedido
        </button>
      </main>
    </div>
  )
}

// ── Time picker for a schedulable store ──────────────────────────
function TimePicker({ grupo, value, onChange, error }) {
  const ap = grupo.tienda_hora_apertura?.slice(0, 5) // "HH:MM"
  const cl = grupo.tienda_hora_cierre?.slice(0, 5)

  return (
    <div className="mt-3 bg-yellow-500/8 border border-yellow-500/20 rounded-xl p-3">
      <p className="text-xs text-yellow-400/80 font-medium mb-2">
        🕐 Esta tienda está cerrada — programa tu pedido
        {ap && cl && <span className="text-white/30"> (horario: {ap}–{cl})</span>}
      </p>
      <input
        type="time"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        min={ap}
        max={cl}
        className="bg-white/[0.06] border border-white/10 focus:border-yellow-500/60 focus:outline-none rounded-lg px-3 py-1.5 text-sm text-white transition-colors w-full"
      />
      {error && (
        <p className="text-[10px] text-red-400 mt-1">{error}</p>
      )}
    </div>
  )
}

// ── Main checkout ─────────────────────────────────────────────────
export default function CheckoutPage() {
  const navigate = useNavigate()
  const { cart, clearCart } = useCart()

  const [showModal,    setShowModal]    = useState(false)
  const [submitting,   setSubmitting]   = useState(false)
  const [confirmed,    setConfirmed]    = useState(false)
  const [orderGroups,  setOrderGroups]  = useState([])
  // tienda_id → "HH:MM"
  const [horasSugeridas, setHorasSugeridas] = useState({})
  const [timeErrors,     setTimeErrors]     = useState({})

  const isEmpty = !cart || cart.esta_vacio

  // Compute per-group status
  const statusMap = useMemo(() => {
    if (!cart?.grupos) return {}
    return Object.fromEntries(cart.grupos.map((g) => [g.tienda_id, getStoreStatus(g)]))
  }, [cart])

  const closedGroups      = useMemo(() => (cart?.grupos ?? []).filter((g) => statusMap[g.tienda_id] === 'closed'),      [cart, statusMap])
  const schedulableGroups = useMemo(() => (cart?.grupos ?? []).filter((g) => statusMap[g.tienda_id] === 'schedulable'), [cart, statusMap])
  const hasBlockedStores  = closedGroups.length > 0

  // Validate all scheduled times; return first error string or null
  const validateAllTimes = () => {
    const errs = {}
    let first = null
    for (const g of schedulableGroups) {
      const e = validateScheduledTime(
        horasSugeridas[g.tienda_id],
        g.tienda_hora_apertura?.slice(0, 5),
        g.tienda_hora_cierre?.slice(0, 5),
      )
      if (e) { errs[g.tienda_id] = e; if (!first) first = `${g.tienda_nombre}: ${e}` }
    }
    setTimeErrors(errs)
    return first
  }

  const canConfirm = !hasBlockedStores

  const handleConfirm = async () => {
    const timeErr = validateAllTimes()
    if (timeErr) return // errors already set in state
    if (!cart?.grupos?.length) return
    setShowModal(false)
    setSubmitting(true)
    const grupos = [...cart.grupos]
    try { await clearCart() } catch { /* ignore */ }
    setOrderGroups(grupos)
    setConfirmed(true)
    setSubmitting(false)
  }

  const handleOpenModal = () => {
    const timeErr = validateAllTimes()
    if (!timeErr) setShowModal(true)
  }

  if (confirmed) {
    return <SuccessScreen grupos={orderGroups} horasSugeridas={horasSugeridas} onRestart={() => navigate('/')} />
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

        {/* ── Alerta si hay tiendas cerradas sin pedidos programados ── */}
        {hasBlockedStores && (
          <div role="alert" className="bg-red-900/20 border border-red-800/30 rounded-xl p-4 mb-4">
            <p className="text-sm font-semibold text-red-400 mb-1">Tiendas cerradas</p>
            <p className="text-xs text-red-400/70 leading-relaxed">
              Las siguientes tiendas no aceptan pedidos ahora ni pedidos programados:
            </p>
            <ul className="mt-2 space-y-0.5">
              {closedGroups.map((g) => (
                <li key={g.tienda_id} className="text-xs text-red-300/60">• {g.tienda_nombre}</li>
              ))}
            </ul>
            <p className="text-[10px] text-red-400/50 mt-2">
              Elimina esos productos del carrito o vuelve en horario de atención.
            </p>
          </div>
        )}

        <h2 className="text-xs font-semibold text-white/40 uppercase tracking-widest mb-4">
          Resumen del pedido
        </h2>

        {cart.grupos.map((grupo) => {
          const status = statusMap[grupo.tienda_id]
          return (
            <section key={grupo.tienda_id} aria-label={`Pedido en ${grupo.tienda_nombre}`}
              className="bg-white/[0.04] border border-white/5 rounded-2xl overflow-hidden mb-4">
              <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2">
                {grupo.tienda_logo
                  ? <img src={grupo.tienda_logo} alt="" aria-hidden="true" className="w-7 h-7 rounded-lg object-cover" />
                  : <span aria-hidden="true" className="text-xl">🏪</span>
                }
                <span className="font-semibold text-sm flex-1">{grupo.tienda_nombre}</span>
                {/* Status badge */}
                {grupo.tienda_hora_apertura && (
                  <span className={[
                    'text-[9px] font-bold px-1.5 py-0.5 rounded-full border',
                    status === 'open'
                      ? 'bg-green-500/15 text-green-400 border-green-500/25'
                      : status === 'schedulable'
                        ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25'
                        : 'bg-red-500/15 text-red-400 border-red-500/25',
                  ].join(' ')}>
                    {status === 'open' ? 'Abierto' : status === 'schedulable' ? 'Cerrado · Programar' : 'Cerrado'}
                  </span>
                )}
              </div>
              <ul className="divide-y divide-white/5">
                {grupo.items.map((item) => (
                  <li key={item.id} className="flex justify-between items-center px-4 py-2.5">
                    <span className="text-sm">
                      <span className="text-white/45 mr-1.5">{item.cantidad}×</span>
                      {item.nombre_producto}
                    </span>
                    <span className="text-sm text-white/65 shrink-0 ml-3">{fmt(item.subtotal)}</span>
                  </li>
                ))}
              </ul>
              <div className="flex justify-between items-center px-4 py-3 border-t border-white/5 text-sm">
                <span className="text-white/45">Subtotal</span>
                <span className="font-semibold">{fmt(grupo.subtotal)}</span>
              </div>
              {parseInt(grupo.costo_envio ?? 0) > 0 && (
                <div className="flex justify-between items-center px-4 pb-3 text-sm text-white/45">
                  <span>Envío</span><span>{fmt(grupo.costo_envio)}</span>
                </div>
              )}

              {/* Time picker for schedulable stores */}
              {status === 'schedulable' && (
                <div className="px-4 pb-4">
                  <TimePicker
                    grupo={grupo}
                    value={horasSugeridas[grupo.tienda_id] ?? ''}
                    onChange={(v) => {
                      setHorasSugeridas((prev) => ({ ...prev, [grupo.tienda_id]: v }))
                      setTimeErrors((prev) => ({ ...prev, [grupo.tienda_id]: null }))
                    }}
                    error={timeErrors[grupo.tienda_id]}
                  />
                </div>
              )}
            </section>
          )
        })}

        <div className="flex justify-between items-center px-1 py-3">
          <span className="font-bold text-base">Total</span>
          <span className="font-bold text-xl text-orange-400">{fmt(cart.total_global)}</span>
        </div>

        <p className="text-xs text-white/25 text-center mt-2 leading-relaxed">
          Al confirmar se generarán los enlaces de WhatsApp para coordinar la entrega con cada tienda.
        </p>
      </main>

      {/* Sticky CTA */}
      <div className="fixed bottom-0 left-0 right-0 bg-slate-950/95 backdrop-blur-sm border-t border-white/10 px-4 py-4">
        <div className="max-w-lg mx-auto">
          {hasBlockedStores ? (
            <div className="text-center text-xs text-red-400/70 py-3">
              Hay tiendas cerradas — elimínalas del carrito para continuar
            </div>
          ) : (
            <button
              onClick={handleOpenModal}
              disabled={submitting}
              aria-busy={submitting}
              className="w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-sm py-4 rounded-2xl transition-colors flex items-center justify-center gap-2"
            >
              {submitting
                ? <span className="text-white/70">Procesando…</span>
                : <><span aria-hidden="true">📲</span> Confirmar y contactar por WhatsApp</>
              }
            </button>
          )}
        </div>
      </div>

      {/* ── Confirmation Modal ── */}
      <Modal open={showModal} onClose={() => setShowModal(false)} title="Confirmar pedido">
        <div className="space-y-4">
          <p className="text-sm text-white/60 leading-relaxed">
            Se generarán los enlaces de WhatsApp para cada tienda. ¿Deseas confirmar?
          </p>

          <div className="bg-white/[0.04] border border-white/5 rounded-xl px-4 py-3 flex justify-between items-center">
            <span className="text-sm text-white/50">Total a pagar</span>
            <span className="text-lg font-black text-orange-400">{fmt(cart.total_global)}</span>
          </div>

          <ul className="space-y-1">
            {cart.grupos.map((g) => (
              <li key={g.tienda_id} className="flex justify-between text-xs text-white/40">
                <span>🏪 {g.tienda_nombre}</span>
                <span>{fmt(g.subtotal ?? g.total ?? 0)}</span>
              </li>
            ))}
          </ul>

          {/* Scheduled times summary */}
          {schedulableGroups.length > 0 && (
            <div className="bg-yellow-500/8 border border-yellow-500/20 rounded-xl px-3 py-2 space-y-1">
              {schedulableGroups.map((g) => (
                <p key={g.tienda_id} className="text-xs text-yellow-400/80">
                  🕐 {g.tienda_nombre}: {horasSugeridas[g.tienda_id] || '—'}
                </p>
              ))}
            </div>
          )}

          <div className="flex gap-2 pt-1">
            <button
              onClick={handleConfirm}
              className="flex-1 bg-orange-500 hover:bg-orange-400 active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all"
            >
              Confirmar pedido ✓
            </button>
            <button
              onClick={() => setShowModal(false)}
              className="flex-1 bg-white/5 hover:bg-white/10 text-white/60 font-semibold text-sm py-3 rounded-xl transition-all"
            >
              Cancelar
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
