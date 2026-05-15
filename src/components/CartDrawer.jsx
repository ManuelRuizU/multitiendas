import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'

// ── Helpers ────────────────────────────────────────────────────────────────

const fmt = (p) => `$${parseInt(p).toLocaleString('es-CL')}`

// metodos_pago_tienda returns display names; map them to codes
const PAGO_A_CODIGO = {
  'Efectivo':              'EFECTIVO',
  'Transferencia bancaria': 'TRANSFERENCIA',
  'Link de pago':          'LINK_PAGO',
}
const PAGO_LABEL = { EFECTIVO: 'Efectivo', TRANSFERENCIA: 'Transferencia', LINK_PAGO: 'Link de pago' }
const PAGO_ICON  = { EFECTIVO: '💵', TRANSFERENCIA: '🏦', LINK_PAGO: '🔗' }

const NOTAS_PH = {
  COMIDA:    'Sin cebolla, extra salsa, alérgenos...',
  RETAIL:    'Talla M, color azul, variante...',
  SERVICIOS: 'Disponible de tarde, detalles del trabajo...',
  OTRO:      'Instrucciones especiales para la tienda...',
}

function storeStatus(g) {
  if (!g.tienda_hora_apertura) return 'open'
  if (g.tienda_esta_abierta)   return 'open'
  return g.tienda_acepta_programados ? 'schedulable' : 'closed'
}

function timeError(hora, ap, cl) {
  if (!hora) return 'Selecciona un horario'
  const now = new Date()
  const [h, m] = hora.split(':').map(Number)
  const t = new Date(); t.setHours(h, m, 0, 0)
  if (t <= now) t.setDate(t.getDate() + 1)
  if (t < new Date(now.getTime() + 30 * 60 * 1000)) return 'Mín. 30 min desde ahora'
  if (ap && cl) {
    const toMin = s => s.split(':').reduce((a, b, i) => a + (+b) * (i === 0 ? 60 : 1), 0)
    const [s, a, c] = [hora, ap, cl].map(toMin)
    if (!(c >= a ? s >= a && s <= c : s >= a || s <= c)) return `Entre ${ap} y ${cl}`
  }
  return null
}

function buildWaLink(waUrl, grupo, tipo, metodo, form) {
  if (!waUrl) return null
  const lines = [
    '🛒 *NUEVO PEDIDO*',
    `📅 ${new Date().toLocaleString('es-CL', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}`,
    '',
    '👤 *Cliente:*',
    `Nombre: ${form.nombre || 'Sin nombre'}`,
  ]
  if (form.telefono) lines.push(`Teléfono: ${form.telefono}`)
  if (form.email)    lines.push(`Email: ${form.email}`)
  lines.push('')
  lines.push(`🚚 *Entrega:* ${tipo === 'RETIRO' ? 'Retiro en local' : 'Despacho a domicilio'}`)
  if (form.hora) lines.push(`⏰ Hora sugerida: ${form.hora}`)
  if (tipo !== 'RETIRO' && form.dir) lines.push(`📍 Dirección: ${form.dir}`)
  lines.push('')
  lines.push('🧾 *Detalle del pedido:*')
  grupo.items.forEach(item =>
    lines.push(`• ${item.cantidad}× ${item.nombre_producto} — ${fmt(item.subtotal)}`)
  )
  lines.push('')
  lines.push(`💰 Subtotal: ${fmt(grupo.subtotal)}`)
  if (tipo !== 'RETIRO' && parseInt(grupo.costo_envio ?? 0) > 0) {
    lines.push(`🚚 Envío: ${fmt(grupo.costo_envio)}`)
  }
  lines.push(`✅ *TOTAL: ${fmt(grupo.total ?? grupo.subtotal ?? 0)}*`)
  lines.push('')
  lines.push(`💳 *Pago:* ${PAGO_LABEL[metodo] ?? metodo}`)
  if (metodo === 'EFECTIVO' && form.vuelto) {
    const total  = parseInt(grupo.total ?? grupo.subtotal ?? 0)
    const pagaCon = parseInt(form.vuelto)
    if (pagaCon > total) {
      lines.push(`💵 Paga con: ${fmt(pagaCon)} → Vuelto: ${fmt(pagaCon - total)}`)
    }
  }
  if (form.notas) { lines.push(''); lines.push(`📝 *Notas:* ${form.notas}`) }
  return `${waUrl.replace(/\/$/, '')}?text=${encodeURIComponent(lines.join('\n'))}`
}

// ── Main CartDrawer ────────────────────────────────────────────────────────

export default function CartDrawer() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { cart, itemCount, isCartOpen, closeCart, updateItem, removeItem, clearCart,
          pendingWaOrders, savePendingOrders } = useCart()
  const { user, openAuthModal } = useAuth()

  // step: 'cart' | 'auth' | 'checkout' | 'success'
  const [step, setStep]      = useState('cart')
  const [busy, setBusy]      = useState({})
  const [submitting, setSub] = useState(false)

  // Guest fields
  const [gNombre,   setGNombre]   = useState('')
  const [gTelefono, setGTelefono] = useState('')
  const [gEmail,    setGEmail]    = useState('')

  // Addresses
  const [addrs,   setAddrs]   = useState([])
  const [selAddr, setSelAddr] = useState(null)
  const [manAddr, setManAddr] = useState({ calle: '', numero: '', comuna: 'Angol', ciudad: 'Angol' })

  // Per-group config (key = tienda_id)
  const [tipo,   setTipo]   = useState({})
  const [metod,  setMetod]  = useState({})
  const [notas,  setNotas]  = useState({})
  const [vuelto, setVuelto] = useState({})
  const [horas,  setHoras]  = useState({})

  // Validation errors & all-done flag
  const [errs,    setErrs]    = useState({})
  const [allDone, setAllDone] = useState(false)

  // Body scroll lock
  useEffect(() => {
    document.body.style.overflow = isCartOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [isCartOpen])

  // Reset to 'cart' after close animation — only if no pending orders
  useEffect(() => {
    if (!isCartOpen) {
      const t = setTimeout(() => {
        if (!pendingWaOrders.some(o => !o.sent)) {
          setStep('cart')
          setAllDone(false)
        }
      }, 450)
      return () => clearTimeout(t)
    }
  }, [isCartOpen, pendingWaOrders])

  // Restore success screen when opening with pending orders
  useEffect(() => {
    if (isCartOpen && pendingWaOrders.some(o => !o.sent)) {
      setStep('success')
    }
  }, [isCartOpen]) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-advance from auth choice when user logs in
  useEffect(() => {
    if (step === 'auth' && user) setStep('checkout')
  }, [user, step])

  // Load saved addresses when entering checkout (auth users only)
  useEffect(() => {
    if (step !== 'checkout' || !user) return
    api.get('usuarios/direcciones/')
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : (data.results ?? [])
        setAddrs(list)
        const principal = list.find(d => d.principal) ?? list[0]
        if (principal) setSelAddr(principal.id)
      })
      .catch(() => {})
  }, [step, user])

  // Initialize per-group defaults when entering checkout
  useEffect(() => {
    if (step !== 'checkout' || !cart?.grupos) return
    const t = {}; const m = {}
    cart.grupos.forEach(g => {
      t[g.tienda_id] = g.tipo_entrega || 'REPARTO'
      // g.metodo_pago is already a code (e.g. 'EFECTIVO')
      const firstCode = PAGO_A_CODIGO[g.metodos_pago_tienda?.[0]] ?? 'EFECTIVO'
      m[g.tienda_id] = g.metodo_pago || firstCode
    })
    setTipo(t); setMetod(m)
  }, [step, cart])

  if (pathname === '/checkout') return null
  const isEmpty = !cart || cart.esta_vacio

  const withBusy = async (key, fn) => {
    setBusy(b => ({ ...b, [key]: true }))
    try { await fn() } finally { setBusy(b => { const n = { ...b }; delete n[key]; return n }) }
  }

  const validate = () => {
    const e = {}
    if (!user) {
      if (!gNombre.trim())   e.nombre   = 'Nombre requerido'
      if (!gTelefono.trim()) e.telefono = 'Teléfono requerido'
      const needsAddr = cart?.grupos?.some(g => (tipo[g.tienda_id] ?? 'REPARTO') === 'REPARTO')
      if (needsAddr) {
        if (!manAddr.calle.trim())  e.calle  = 'Calle requerida'
        if (!manAddr.numero.trim()) e.numero = 'Número requerido'
      }
    }
    cart?.grupos?.forEach(g => {
      const s = storeStatus(g)
      if (s === 'closed') e[`cl_${g.tienda_id}`] = `${g.tienda_nombre} está cerrada`
      if (s === 'schedulable') {
        const te = timeError(horas[g.tienda_id], g.tienda_hora_apertura?.slice(0, 5), g.tienda_hora_cierre?.slice(0, 5))
        if (te) e[`h_${g.tienda_id}`] = te
      }
    })
    setErrs(e)
    return !Object.keys(e).length
  }

  const handleConfirm = async () => {
    if (!validate()) return
    setSub(true)
    const grupos = [...(cart?.grupos ?? [])]
    const nombre   = user ? [user.first_name, user.last_name].filter(Boolean).join(' ') : gNombre
    const telefono = user ? '' : gTelefono
    const email    = user ? user.email : gEmail
    let dir = ''
    if (!user) {
      dir = [manAddr.calle, manAddr.numero, manAddr.comuna, manAddr.ciudad].filter(Boolean).join(', ')
    } else if (selAddr) {
      const a = addrs.find(d => d.id === selAddr)
      if (a) dir = [a.calle, a.numero, a.comuna, a.ciudad].filter(Boolean).join(', ')
    }
    const result = grupos.map(g => {
      const t = tipo[g.tienda_id]  ?? 'REPARTO'
      const m = metod[g.tienda_id] ?? 'EFECTIVO'
      const waHref = buildWaLink(g.tienda_whatsapp_url, g, t, m, {
        nombre, telefono, email, dir,
        notas:  notas[g.tienda_id]  ?? '',
        hora:   horas[g.tienda_id]  ?? '',
        vuelto: vuelto[g.tienda_id] ?? '',
      })
      return {
        tienda_id:     g.tienda_id,
        tienda_nombre: g.tienda_nombre,
        tienda_logo:   g.tienda_logo,
        waHref,
        items: g.items,
        total: parseInt(g.total ?? g.subtotal ?? 0),
        sent:  false,
      }
    })
    try { await clearCart() } catch {}
    setAllDone(false)
    savePendingOrders(result)
    setStep('success')
    setSub(false)
  }

  const markSent = (tienda_id) => {
    const updated = pendingWaOrders.map(o =>
      o.tienda_id === tienda_id ? { ...o, sent: true } : o
    )
    if (updated.every(o => o.sent)) {
      savePendingOrders([])
      setAllDone(true)
    } else {
      savePendingOrders(updated)
    }
  }

  // Track position based on step
  const trackPos =
    step === 'cart'    ? 'translateX(0%)'        :
    step === 'auth'    ? 'translateX(-33.333%)'   :
                         'translateX(-66.667%)'

  return (
    <div
      className={['fixed inset-0 z-[60] flex justify-end', isCartOpen ? '' : 'pointer-events-none'].join(' ')}
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

      {/* Panel — overflow-hidden is essential for the slide */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={step === 'cart' ? 'Carrito de compras' : step === 'auth' ? 'Opciones de acceso' : 'Confirmar pedido'}
        className={[
          'relative overflow-hidden',
          'w-[90vw] sm:w-[420px] h-full',
          'bg-slate-900 border-l border-white/10',
          'transition-transform duration-[450ms] ease-[cubic-bezier(0.32,0,0.15,1)]',
          isCartOpen ? 'translate-x-0' : 'translate-x-full',
        ].join(' ')}
      >
        {/* ── Sliding track: 300% wide, flex row ── */}
        <div
          className="flex h-full"
          style={{
            width: '300%',
            transform: trackPos,
            transition: 'transform 400ms cubic-bezier(0.32, 0, 0.15, 1)',
          }}
        >

          {/* ════ Estado 1 — Carrito ════ */}
          <CartSlide
            cart={cart}
            isEmpty={isEmpty}
            itemCount={itemCount}
            busy={busy}
            withBusy={withBusy}
            updateItem={updateItem}
            removeItem={removeItem}
            onClose={closeCart}
            onCheckout={() => user ? setStep('checkout') : setStep('auth')}
          />

          {/* ════ Estado 2 — Elige cómo continuar (solo invitados) ════ */}
          <div className="h-full flex flex-col" style={{ width: '33.333%' }}>
            <AuthChoiceSlide
              onBack={() => setStep('cart')}
              onClose={closeCart}
              onLogin={openAuthModal}
              onGuest={() => setStep('checkout')}
            />
          </div>

          {/* ════ Estado 3 — Checkout / Éxito ════ */}
          <div className="h-full flex flex-col" style={{ width: '33.333%' }}>
            {step === 'success' ? (
              <SuccessSlide
                pending={pendingWaOrders}
                allDone={allDone}
                onMarkSent={markSent}
                onClose={closeCart}
                onViewOrders={() => { closeCart(); navigate('/mis-pedidos') }}
              />
            ) : (
              <CheckoutSlide
                cart={cart}
                user={user}
                gNombre={gNombre}         setGNombre={setGNombre}
                gTelefono={gTelefono}     setGTelefono={setGTelefono}
                gEmail={gEmail}           setGEmail={setGEmail}
                addrs={addrs}
                selAddr={selAddr}         setSelAddr={setSelAddr}
                manAddr={manAddr}         setManAddr={setManAddr}
                tipo={tipo}               setTipo={setTipo}
                metod={metod}             setMetod={setMetod}
                notas={notas}             setNotas={setNotas}
                vuelto={vuelto}           setVuelto={setVuelto}
                horas={horas}             setHoras={setHoras}
                errs={errs}
                submitting={submitting}
                onBack={() => setStep(user ? 'cart' : 'auth')}
                onClose={closeCart}
                onConfirm={handleConfirm}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── CartSlide ──────────────────────────────────────────────────────────────

function CartSlide({ cart, isEmpty, itemCount, busy, withBusy, updateItem, removeItem, onClose, onCheckout }) {
  return (
    <div className="h-full flex flex-col" style={{ width: '33.333%' }}>
      {/* Header */}
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
          onClick={onClose}
          aria-label="Cerrar carrito"
          className="w-8 h-8 flex items-center justify-center rounded-full text-white/50 hover:text-white hover:bg-white/10 transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Body */}
      <div
        className="flex-1 overflow-y-auto overscroll-contain px-4 py-4 space-y-5"
        style={{ WebkitOverflowScrolling: 'touch' }}
      >
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center gap-3 pt-16 text-white/30">
            <span aria-hidden="true" className="text-5xl">🛒</span>
            <p className="text-sm font-medium">Tu carrito está vacío</p>
            <button onClick={onClose} className="text-sm text-orange-400 hover:text-orange-300 transition-colors mt-1">
              ← Seguir comprando
            </button>
          </div>
        ) : (
          cart.grupos.map((grupo) => (
            <section key={grupo.tienda_id} aria-label={`Productos de ${grupo.tienda_nombre}`}>
              <div className="flex items-center gap-2 mb-2">
                {grupo.tienda_logo
                  ? <img src={grupo.tienda_logo} alt="" aria-hidden="true" className="w-5 h-5 rounded object-cover" />
                  : <span aria-hidden="true" className="text-sm">🏪</span>
                }
                <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wide truncate">
                  {grupo.tienda_nombre}
                </h3>
              </div>

              <div className="space-y-2">
                {grupo.items.map((item) => (
                  <div key={item.id} className="flex items-center gap-2 bg-white/[0.04] rounded-xl px-3 py-2.5">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white leading-snug truncate">{item.nombre_producto}</p>
                      <p className="text-xs text-orange-400 mt-0.5">{fmt(item.subtotal)}</p>
                    </div>
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
                      >−</button>
                      <span className="text-sm font-semibold w-5 text-center">{item.cantidad}</span>
                      <button
                        disabled={busy[item.id]}
                        onClick={() => withBusy(item.id, () => updateItem(item.producto, item.cantidad + 1))}
                        aria-label={`Aumentar cantidad de ${item.nombre_producto}`}
                        className="w-6 h-6 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-xs font-bold disabled:opacity-30 transition-colors"
                      >+</button>
                      <button
                        disabled={busy[item.id]}
                        onClick={() => withBusy(item.id, () => removeItem(item.producto))}
                        aria-label={`Eliminar ${item.nombre_producto}`}
                        className="w-6 h-6 rounded-full bg-red-900/30 hover:bg-red-800/50 text-red-400 flex items-center justify-center text-[10px] disabled:opacity-30 transition-colors ml-0.5"
                      >✕</button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-between text-xs text-white/35 mt-2 px-1">
                <span>Subtotal {grupo.tienda_nombre}</span>
                <span className="font-semibold text-white/55">{fmt(grupo.subtotal ?? grupo.total ?? 0)}</span>
              </div>
            </section>
          ))
        )}
      </div>

      {/* Footer */}
      {!isEmpty && (
        <div className="shrink-0 border-t border-white/10 px-4 py-4 space-y-3 bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sm text-white">Total</span>
            <span className="font-bold text-lg text-orange-400">{fmt(cart.total_global ?? 0)}</span>
          </div>
          <button
            onClick={onCheckout}
            className="w-full bg-orange-500 hover:bg-orange-400 active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all"
          >
            Hacer pedido →
          </button>
          <button
            onClick={onClose}
            className="w-full text-xs text-white/40 hover:text-white/70 transition-colors py-1"
          >
            ← Seguir comprando
          </button>
        </div>
      )}
    </div>
  )
}

// ── AuthChoiceSlide ────────────────────────────────────────────────────────

function AuthChoiceSlide({ onBack, onClose, onLogin, onGuest }) {
  return (
    <>
      {/* Header */}
      <div className="shrink-0 flex items-center gap-3 px-4 py-4 border-b border-white/10">
        <button
          onClick={onBack}
          aria-label="Volver al carrito"
          className="text-white/50 hover:text-white transition-colors text-base p-1 -ml-1 leading-none"
        >
          ←
        </button>
        <h2 className="font-bold text-white text-base leading-none flex-1 truncate">
          ¿Cómo continuar?
        </h2>
        <button
          onClick={onClose}
          aria-label="Cerrar"
          className="w-8 h-8 flex items-center justify-center rounded-full text-white/50 hover:text-white hover:bg-white/10 transition-colors shrink-0"
        >
          ✕
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 flex flex-col justify-center px-5 py-8 gap-4">
        <p className="text-sm text-white/50 text-center mb-2 leading-relaxed">
          Inicia sesión para usar tus datos guardados o continúa como invitado.
        </p>

        {/* Login button */}
        <button
          onClick={onLogin}
          className="w-full min-h-[56px] flex items-center justify-center gap-2.5 bg-orange-500 hover:bg-orange-400 active:scale-[0.98] text-white font-bold text-sm rounded-xl transition-all"
        >
          <span aria-hidden="true">🔑</span>
          Iniciar sesión
        </button>

        {/* Guest button */}
        <button
          onClick={onGuest}
          className="w-full min-h-[64px] flex flex-col items-center justify-center gap-1 bg-white/[0.06] hover:bg-white/[0.10] active:scale-[0.98] border border-white/10 hover:border-white/20 text-white font-semibold text-sm rounded-xl transition-all"
        >
          <span>Continuar sin registrarse →</span>
          <span className="text-xs text-white/35 font-normal">
            Llenarás tus datos en el siguiente paso
          </span>
        </button>
      </div>

      {/* Footer */}
      <div className="shrink-0 px-5 py-5 border-t border-white/8 text-center">
        <p className="text-xs text-white/25 flex items-center justify-center gap-1.5">
          <span aria-hidden="true">🔒</span>
          Tus datos están seguros y protegidos
        </p>
      </div>
    </>
  )
}

// ── CheckoutSlide ──────────────────────────────────────────────────────────

function CheckoutSlide({
  cart, user,
  gNombre, setGNombre, gTelefono, setGTelefono, gEmail, setGEmail,
  addrs, selAddr, setSelAddr, manAddr, setManAddr,
  tipo, setTipo, metod, setMetod, notas, setNotas, vuelto, setVuelto, horas, setHoras,
  errs, submitting, onBack, onClose, onConfirm,
}) {
  const grupos      = cart?.grupos ?? []
  const hasReparto  = grupos.some(g => (tipo[g.tienda_id] ?? 'REPARTO') === 'REPARTO')
  const closedGrups = grupos.filter(g => storeStatus(g) === 'closed')
  const hasBlocked  = closedGrups.length > 0

  const upTipo  = (id, v) => setTipo(p  => ({ ...p, [id]: v }))
  const upMetod = (id, v) => setMetod(p => ({ ...p, [id]: v }))
  const upNotas = (id, v) => setNotas(p => ({ ...p, [id]: v }))
  const upVuelto= (id, v) => setVuelto(p=> ({ ...p, [id]: v }))
  const upHoras = (id, v) => setHoras(p => ({ ...p, [id]: v }))

  return (
    <>
      {/* Header */}
      <div className="shrink-0 flex items-center gap-3 px-4 py-4 border-b border-white/10">
        <button
          onClick={onBack}
          aria-label="Volver al carrito"
          className="text-white/50 hover:text-white transition-colors text-base p-1 -ml-1 leading-none"
        >
          ←
        </button>
        <h2 className="font-bold text-white text-base leading-none flex-1 truncate">Confirmar pedido</h2>
        <button
          onClick={onClose}
          aria-label="Cerrar"
          className="w-8 h-8 flex items-center justify-center rounded-full text-white/50 hover:text-white hover:bg-white/10 transition-colors shrink-0"
        >
          ✕
        </button>
      </div>

      {/* Scrollable form */}
      <div
        className="flex-1 overflow-y-auto overscroll-contain px-4 py-4 space-y-6"
        style={{ WebkitOverflowScrolling: 'touch' }}
      >
        {/* ── Tiendas cerradas ── */}
        {hasBlocked && (
          <div role="alert" className="bg-red-900/20 border border-red-800/30 rounded-xl p-4">
            <p className="text-sm font-semibold text-red-400 mb-1">Tiendas cerradas</p>
            {closedGrups.map(g => (
              <p key={g.tienda_id} className="text-xs text-red-400/70">• {g.tienda_nombre}</p>
            ))}
            <p className="text-[10px] text-red-400/50 mt-2">
              Elimina esos productos del carrito para continuar.
            </p>
          </div>
        )}

        {/* ── Datos del cliente (invitados) ── */}
        {!user && (
          <section>
            <SectionTitle>Tus datos</SectionTitle>
            <div className="space-y-3">
              <Field label="Nombre completo" required value={gNombre} onChange={setGNombre}
                placeholder="Juan Pérez" error={errs.nombre} />
              <Field label="Teléfono" required type="tel" value={gTelefono} onChange={setGTelefono}
                placeholder="+56912345678" error={errs.telefono} />
              <Field label="Email (opcional)" type="email" value={gEmail} onChange={setGEmail}
                placeholder="tu@email.com" />
            </div>
          </section>
        )}

        {/* ── Config por tienda ── */}
        {grupos.map(g => {
          const s        = storeStatus(g)
          const t        = tipo[g.tienda_id]  ?? 'REPARTO'
          const m        = metod[g.tienda_id] ?? 'EFECTIVO'
          const n        = notas[g.tienda_id] ?? ''
          const v        = vuelto[g.tienda_id] ?? ''
          const h        = horas[g.tienda_id]  ?? ''
          const totalNum = parseInt(g.total ?? g.subtotal ?? 0)
          const vueltoNum= parseInt(v) || 0
          const cambio   = vueltoNum > totalNum ? vueltoNum - totalNum : 0
          const metodsDisp = (g.metodos_pago_tienda ?? [])
            .map(name => PAGO_A_CODIGO[name]).filter(Boolean)
          if (!metodsDisp.length) metodsDisp.push('EFECTIVO')
          const notesPh = NOTAS_PH[g.tienda_tipo_negocio] ?? NOTAS_PH.OTRO

          return (
            <section
              key={g.tienda_id}
              className="bg-white/[0.03] border border-white/8 rounded-2xl overflow-hidden"
            >
              {/* Store header row */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-white/8">
                {g.tienda_logo
                  ? <img src={g.tienda_logo} alt="" className="w-6 h-6 rounded-lg object-cover shrink-0" />
                  : <span className="text-lg shrink-0">🏪</span>
                }
                <span className="font-semibold text-sm text-white flex-1 truncate">{g.tienda_nombre}</span>
                {g.tienda_hora_apertura && (
                  <span className={[
                    'text-[9px] font-bold px-1.5 py-0.5 rounded-full border shrink-0',
                    s === 'open'
                      ? 'bg-green-500/15 text-green-400 border-green-500/25'
                      : s === 'schedulable'
                        ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25'
                        : 'bg-red-500/15 text-red-400 border-red-500/25',
                  ].join(' ')}>
                    {s === 'open' ? '● Abierto' : s === 'schedulable' ? '○ Programar' : '○ Cerrado'}
                  </span>
                )}
              </div>

              <div className="px-4 py-3 space-y-4">
                {/* Tipo de entrega */}
                <div>
                  <p className="text-xs text-white/45 font-medium mb-2">Tipo de entrega</p>
                  <div className="flex gap-2">
                    {['REPARTO', 'RETIRO'].map(opt => (
                      <button
                        key={opt}
                        onClick={() => upTipo(g.tienda_id, opt)}
                        className={[
                          'flex-1 py-2 rounded-xl text-xs font-semibold border transition-all',
                          t === opt
                            ? 'bg-orange-500/20 border-orange-500/40 text-orange-300'
                            : 'bg-white/5 border-white/10 text-white/40 hover:text-white/70 hover:bg-white/8',
                        ].join(' ')}
                      >
                        {opt === 'REPARTO' ? '🚚 Reparto' : '🏪 Retiro'}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Método de pago */}
                <div>
                  <p className="text-xs text-white/45 font-medium mb-2">Método de pago</p>
                  <div className="flex flex-wrap gap-2">
                    {metodsDisp.map(cod => (
                      <button
                        key={cod}
                        onClick={() => upMetod(g.tienda_id, cod)}
                        className={[
                          'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all',
                          m === cod
                            ? 'bg-orange-500/20 border-orange-500/40 text-orange-300'
                            : 'bg-white/5 border-white/10 text-white/40 hover:text-white/70',
                        ].join(' ')}
                      >
                        {PAGO_ICON[cod]} {PAGO_LABEL[cod]}
                      </button>
                    ))}
                  </div>

                  {/* Vuelto (solo efectivo) */}
                  {m === 'EFECTIVO' && (
                    <div className="mt-3 bg-white/[0.03] border border-white/8 rounded-xl p-3">
                      <p className="text-xs text-white/45 mb-2">¿Con cuánto pagas? (opcional)</p>
                      <input
                        type="number"
                        min={totalNum}
                        step="1000"
                        value={v}
                        onChange={e => upVuelto(g.tienda_id, e.target.value)}
                        placeholder={`Ej: ${fmt(Math.ceil(totalNum / 1000) * 1000)}`}
                        className="w-full bg-white/[0.06] border border-white/10 focus:border-orange-500/50 focus:outline-none rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/20 transition-colors"
                      />
                      {cambio > 0 && (
                        <p className="text-xs text-green-400 mt-1.5 font-medium">
                          Vuelto: <span className="font-bold">{fmt(cambio)}</span>
                        </p>
                      )}
                    </div>
                  )}
                </div>

                {/* Horario programado */}
                {s === 'schedulable' && (
                  <div className="bg-yellow-500/8 border border-yellow-500/20 rounded-xl p-3">
                    <p className="text-xs text-yellow-400/80 font-medium mb-2">
                      🕐 Tienda cerrada — programa tu pedido
                      {g.tienda_hora_apertura && g.tienda_hora_cierre && (
                        <span className="text-white/30 font-normal">
                          {' '}({g.tienda_hora_apertura.slice(0, 5)}–{g.tienda_hora_cierre.slice(0, 5)})
                        </span>
                      )}
                    </p>
                    <input
                      type="time"
                      value={h}
                      onChange={e => upHoras(g.tienda_id, e.target.value)}
                      className="w-full bg-white/[0.06] border border-white/10 focus:border-yellow-500/60 focus:outline-none rounded-lg px-3 py-1.5 text-sm text-white transition-colors"
                    />
                    {errs[`h_${g.tienda_id}`] && (
                      <p className="text-[10px] text-red-400 mt-1">{errs[`h_${g.tienda_id}`]}</p>
                    )}
                  </div>
                )}

                {/* Notas */}
                <div>
                  <p className="text-xs text-white/45 font-medium mb-2">Notas para la tienda (opcional)</p>
                  <textarea
                    rows={2}
                    value={n}
                    onChange={e => upNotas(g.tienda_id, e.target.value)}
                    placeholder={notesPh}
                    className="w-full bg-white/[0.06] border border-white/10 focus:border-orange-500/40 focus:outline-none rounded-xl px-3 py-2.5 text-sm text-white placeholder:text-white/20 resize-none transition-colors leading-relaxed"
                  />
                </div>

                {/* Group total row */}
                <div className="flex justify-between items-center text-xs text-white/40 pt-1 border-t border-white/8">
                  <span>
                    {g.items.length} producto{g.items.length !== 1 ? 's' : ''}
                    {t === 'REPARTO' && parseInt(g.costo_envio ?? 0) > 0
                      ? ` + envío ${fmt(g.costo_envio)}`
                      : ''}
                  </span>
                  <span className="font-bold text-white/60">{fmt(g.total ?? g.subtotal ?? 0)}</span>
                </div>
              </div>
            </section>
          )
        })}

        {/* ── Dirección de entrega ── */}
        {hasReparto && (
          <section>
            <SectionTitle>Dirección de entrega</SectionTitle>
            {user && addrs.length > 0 ? (
              <div className="space-y-2">
                {addrs.map(a => (
                  <button
                    key={a.id}
                    onClick={() => setSelAddr(a.id)}
                    className={[
                      'w-full flex items-start gap-3 p-3 rounded-xl border text-left transition-all',
                      selAddr === a.id
                        ? 'bg-orange-500/10 border-orange-500/40'
                        : 'bg-white/[0.03] border-white/8 hover:bg-white/[0.06]',
                    ].join(' ')}
                  >
                    <span className="text-base shrink-0 mt-0.5">📍</span>
                    <div className="flex-1 min-w-0">
                      {a.etiqueta && (
                        <p className="text-xs font-semibold text-white/60 mb-0.5">{a.etiqueta}</p>
                      )}
                      <p className="text-sm text-white leading-snug">{a.calle} {a.numero}</p>
                      <p className="text-xs text-white/40 mt-0.5">{a.comuna}, {a.ciudad}</p>
                    </div>
                    {selAddr === a.id && (
                      <span className="text-orange-400 shrink-0 font-bold">✓</span>
                    )}
                  </button>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {user && addrs.length === 0 && (
                  <p className="text-xs text-white/35 -mt-1 mb-1">
                    No tienes direcciones guardadas. Ingresa una:
                  </p>
                )}
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Calle" required value={manAddr.calle}
                    onChange={v => setManAddr(a => ({ ...a, calle: v }))}
                    placeholder="Los Aromos" error={errs.calle} />
                  <Field label="Número" required value={manAddr.numero}
                    onChange={v => setManAddr(a => ({ ...a, numero: v }))}
                    placeholder="456" error={errs.numero} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Comuna" value={manAddr.comuna}
                    onChange={v => setManAddr(a => ({ ...a, comuna: v }))}
                    placeholder="Angol" />
                  <Field label="Ciudad" value={manAddr.ciudad}
                    onChange={v => setManAddr(a => ({ ...a, ciudad: v }))}
                    placeholder="Angol" />
                </div>
              </div>
            )}
          </section>
        )}

        {/* ── Total global ── */}
        <div className="flex justify-between items-center py-2 border-t border-white/10">
          <span className="font-bold text-base text-white">Total a pagar</span>
          <span className="font-black text-xl text-orange-400">{fmt(cart?.total_global ?? 0)}</span>
        </div>

        <p className="text-[11px] text-white/25 text-center leading-relaxed pb-2">
          Al confirmar se generarán los enlaces de WhatsApp para coordinar con cada tienda.
        </p>
      </div>

      {/* Footer CTA */}
      <div className="shrink-0 border-t border-white/10 px-4 py-4 bg-slate-900">
        {hasBlocked ? (
          <p className="text-xs text-red-400/70 text-center py-2.5">
            Hay tiendas cerradas — elimínalas del carrito para continuar
          </p>
        ) : (
          <button
            onClick={onConfirm}
            disabled={submitting}
            className="w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-50 text-white font-bold text-sm py-3.5 rounded-xl transition-all flex items-center justify-center gap-2 active:scale-[0.98]"
          >
            {submitting
              ? <span className="animate-pulse">Procesando…</span>
              : <><span aria-hidden="true">📲</span> Confirmar y contactar por WhatsApp</>
            }
          </button>
        )}
      </div>
    </>
  )
}

// ── SuccessSlide ───────────────────────────────────────────────────────────

function SuccessSlide({ pending, allDone, onMarkSent, onClose, onViewOrders }) {
  // All-done screen
  if (allDone) {
    return (
      <>
        <div className="shrink-0 flex items-center justify-between px-4 py-4 border-b border-white/10">
          <h2 className="font-bold text-white text-base leading-none">¡Pedidos enviados!</h2>
          <button onClick={onClose} aria-label="Cerrar"
            className="w-8 h-8 flex items-center justify-center rounded-full text-white/50 hover:text-white hover:bg-white/10 transition-colors">
            ✕
          </button>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center px-6 py-8 text-center gap-5">
          <div className="w-20 h-20 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center text-4xl">
            ✅
          </div>
          <div>
            <p className="font-bold text-white text-lg mb-2">Todos los pedidos enviados</p>
            <p className="text-sm text-white/45 leading-relaxed">
              Cada tienda recibirá tu mensaje y coordinará la entrega contigo.
            </p>
          </div>
          <button
            onClick={onViewOrders}
            className="w-full bg-orange-500 hover:bg-orange-400 active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all"
          >
            Ver mis pedidos
          </button>
          <button onClick={onClose}
            className="text-sm text-white/40 hover:text-white/60 transition-colors">
            ← Seguir comprando
          </button>
        </div>
      </>
    )
  }

  const unsentCount = pending.filter(o => !o.sent).length

  return (
    <>
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between px-4 py-4 border-b border-white/10">
        <div>
          <h2 className="font-bold text-white text-base leading-none">¡Pedido confirmado!</h2>
          <p className="text-xs text-white/40 mt-0.5">
            {unsentCount} de {pending.length} por enviar
          </p>
        </div>
        <button onClick={onClose} aria-label="Cerrar"
          className="w-8 h-8 flex items-center justify-center rounded-full text-white/50 hover:text-white hover:bg-white/10 transition-colors">
          ✕
        </button>
      </div>

      {/* Body */}
      <div
        className="flex-1 overflow-y-auto overscroll-contain px-4 py-5 space-y-4"
        style={{ WebkitOverflowScrolling: 'touch' }}
      >
        <p className="text-sm text-white/45 text-center leading-relaxed">
          Abre WhatsApp para coordinar con cada tienda. Márcalo como enviado al hacerlo.
        </p>

        {pending.map((order) => (
          <div
            key={order.tienda_id}
            className={[
              'border rounded-2xl p-4 transition-all duration-300',
              order.sent
                ? 'bg-green-500/[0.06] border-green-500/25'
                : 'bg-white/[0.04] border-white/8',
            ].join(' ')}
          >
            {/* Store header */}
            <div className="flex items-center gap-2 mb-2">
              {order.tienda_logo
                ? <img src={order.tienda_logo} alt="" className="w-7 h-7 rounded-lg object-cover shrink-0" />
                : <span className="text-xl shrink-0">🏪</span>
              }
              <span className="font-semibold text-sm text-white flex-1 truncate">{order.tienda_nombre}</span>
              {order.sent && (
                <span className="text-green-400 text-xs font-bold shrink-0">✅ Enviado</span>
              )}
            </div>

            <p className="text-xs text-white/35 mb-3">
              {order.items.length} producto{order.items.length !== 1 ? 's' : ''} · {fmt(order.total)}
            </p>

            {order.sent ? (
              <p className="text-xs text-green-400/60 text-center py-1 italic">
                Mensaje enviado correctamente
              </p>
            ) : order.waHref ? (
              <a
                href={order.waHref}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => onMarkSent(order.tienda_id)}
                className="flex items-center justify-center gap-2 w-full py-2.5 rounded-full bg-green-600 hover:bg-green-500 active:scale-[0.98] text-white text-sm font-semibold transition-all"
              >
                <WaIcon /> Abrir WhatsApp
              </a>
            ) : (
              <div className="space-y-2">
                <p className="text-xs text-white/25 text-center italic">Sin WhatsApp configurado</p>
                <button
                  onClick={() => onMarkSent(order.tienda_id)}
                  className="w-full py-2 rounded-xl border border-white/12 text-xs text-white/40 hover:text-white/60 hover:border-white/25 transition-all"
                >
                  Marcar como enviado ✓
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  )
}

// ── Small reusable primitives ──────────────────────────────────────────────

function SectionTitle({ children }) {
  return (
    <h3 className="text-xs font-bold text-white/45 uppercase tracking-widest mb-3">
      {children}
    </h3>
  )
}

function Field({ label, required, value, onChange, placeholder, type = 'text', error }) {
  return (
    <div>
      <label className="block text-xs text-white/45 mb-1.5">
        {label}{required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className={[
          'w-full bg-white/[0.06] border rounded-xl px-3 py-2.5 text-sm text-white',
          'placeholder:text-white/20 focus:outline-none transition-colors',
          error
            ? 'border-red-500/60 focus:border-red-500/80'
            : 'border-white/10 focus:border-orange-500/50',
        ].join(' ')}
      />
      {error && <p className="text-[10px] text-red-400 mt-1">{error}</p>}
    </div>
  )
}

function WaIcon() {
  return (
    <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current shrink-0" aria-hidden="true">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
    </svg>
  )
}
