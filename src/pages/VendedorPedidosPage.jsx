import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'

// ── Helpers ────────────────────────────────────────────────────────────────

function timeAgo(dateStr) {
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000)
  if (diff < 60) return 'hace <1min'
  if (diff < 3600) return `hace ${Math.floor(diff / 60)}min`
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)}h`
  return `hace ${Math.floor(diff / 86400)}d`
}

function formatCLP(n) {
  return `$${Number(n).toLocaleString('es-CL')}`
}

// ── Config ─────────────────────────────────────────────────────────────────

const SECTIONS = [
  {
    key: 'pendientes',
    label: 'Pendientes',
    emoji: '🟡',
    pill: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  },
  {
    key: 'confirmados',
    label: 'Confirmados',
    emoji: '🔵',
    pill: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  },
  {
    key: 'en_preparacion',
    label: 'Preparando',
    emoji: '🟠',
    pill: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  },
  {
    key: 'en_camino',
    label: 'En camino',
    emoji: '🟣',
    pill: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
  },
  {
    key: 'entregados_hoy',
    label: 'Entregados hoy',
    emoji: '🟢',
    pill: 'bg-green-500/10 text-green-400 border-green-500/30',
    collapsible: true,
  },
]

const STATUS_PILL = {
  PENDING:    'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
  CONFIRMED:  'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  PREPARING:  'bg-orange-500/15 text-orange-400 border border-orange-500/30',
  ON_THE_WAY: 'bg-purple-500/15 text-purple-400 border border-purple-500/30',
  DELIVERED:  'bg-green-500/15 text-green-400 border border-green-500/30',
  CANCELLED:  'bg-red-500/15 text-red-400 border border-red-500/30',
}

function getNextAction(order) {
  switch (order.status) {
    case 'PENDING':    return { status: 'CONFIRMED',   label: '✓ Confirmar' }
    case 'CONFIRMED':  return { status: 'PREPARING',   label: '🍳 Preparar' }
    case 'PREPARING':
      return order.tipo_entrega === 'REPARTO'
        ? { status: 'ON_THE_WAY', label: '🚚 Despachar' }
        : { status: 'DELIVERED',  label: '✓ Listo — entregado' }
    case 'ON_THE_WAY': return { status: 'DELIVERED',   label: '✓ Entregar' }
    default: return null
  }
}

const CANCELLABLE = new Set(['PENDING', 'CONFIRMED', 'PREPARING', 'ON_THE_WAY'])

// ── Main page ──────────────────────────────────────────────────────────────

export default function VendedorPedidosPage() {
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()

  const [data, setData]           = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [initLoading, setInitLoading] = useState(true)
  const [updating, setUpdating]   = useState({})
  const [collapsed, setCollapsed] = useState({ entregados_hoy: true })
  const [lastRefresh, setLastRefresh] = useState(null)
  const intervalRef = useRef(null)

  // Route guard
  useEffect(() => {
    if (!authLoading && (!user || !user.is_vendedor)) navigate('/')
  }, [authLoading, user, navigate])

  const load = useCallback(async (silent = false) => {
    if (!silent) setInitLoading(true)
    setLoadError(null)
    try {
      const { data: res } = await api.get('pedidos/panel_vendedor/')
      setData(res)
      setLastRefresh(new Date())
    } catch {
      setLoadError('No se pudo cargar los pedidos. Verifica la conexión.')
    } finally {
      if (!silent) setInitLoading(false)
    }
  }, [])

  useEffect(() => {
    if (authLoading || !user?.is_vendedor) return
    load()
    intervalRef.current = setInterval(() => load(true), 30_000)
    return () => clearInterval(intervalRef.current)
  }, [authLoading, user, load])

  const changeStatus = async (orderId, newStatus) => {
    setUpdating(u => ({ ...u, [orderId]: true }))
    try {
      await api.post(`pedidos/${orderId}/change_status/`, { status: newStatus })
      await load(true)
    } catch {
      await load(true)
    } finally {
      setUpdating(u => { const n = { ...u }; delete n[orderId]; return n })
    }
  }

  if (authLoading || initLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <p className="text-white/40 text-sm animate-pulse">Cargando panel…</p>
      </div>
    )
  }

  if (!user?.is_vendedor) return null

  const activeCount = data
    ? (data.pendientes?.length ?? 0) +
      (data.confirmados?.length ?? 0) +
      (data.en_preparacion?.length ?? 0) +
      (data.en_camino?.length ?? 0)
    : 0

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header
        title="Mis pedidos"
        subtitle={
          activeCount > 0
            ? `${activeCount} pedido${activeCount !== 1 ? 's' : ''} activo${activeCount !== 1 ? 's' : ''}`
            : 'Sin pedidos activos'
        }
        onBack={() => navigate('/vendedor/panel')}
      />

      <main className="max-w-2xl mx-auto px-3 pt-4 pb-20 space-y-6">

        {/* Refresh bar */}
        <div className="flex items-center justify-between">
          <p className="text-xs text-white/25">
            {lastRefresh ? `Actualizado ${timeAgo(lastRefresh)} · auto cada 30s` : ''}
          </p>
          <button
            onClick={() => load(true)}
            className="flex items-center gap-1.5 text-xs text-white/40 hover:text-white/70 px-3 py-1.5 rounded-full hover:bg-white/5 border border-white/5 hover:border-white/10 transition-all"
          >
            ↻ Actualizar
          </button>
        </div>

        {/* Error */}
        {loadError && (
          <div className="bg-red-900/20 border border-red-800/40 text-red-400 rounded-xl p-4 text-sm text-center">
            {loadError}
          </div>
        )}

        {/* Order sections */}
        {data && SECTIONS.map(({ key, label, emoji, pill, collapsible }) => {
          const orders = data[key] ?? []
          const isOpen = !(collapsible && collapsed[key])

          return (
            <section key={key}>
              {/* Section header */}
              <div
                className="flex items-center justify-between mb-3 cursor-pointer select-none"
                onClick={() => collapsible && setCollapsed(c => ({ ...c, [key]: !c[key] }))}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${pill}`}>
                    {emoji} {label}
                  </span>
                  {orders.length > 0 && (
                    <span className="text-white/35 text-xs font-medium">{orders.length}</span>
                  )}
                </div>
                {collapsible && (
                  <span className="text-white/25 text-xs">{isOpen ? '▲' : '▼'}</span>
                )}
              </div>

              {isOpen && (
                orders.length === 0 ? (
                  <p className="text-white/25 text-xs pl-1 pb-1">Sin pedidos aquí</p>
                ) : (
                  <div className="space-y-3">
                    {orders.map(order => (
                      <OrderCard
                        key={order.id}
                        order={order}
                        isUpdating={!!updating[order.id]}
                        onAction={changeStatus}
                      />
                    ))}
                  </div>
                )
              )}
            </section>
          )
        })}

        {/* Estadísticas placeholder */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-bold px-2.5 py-1 rounded-full border bg-white/5 text-white/35 border-white/10">
              📊 Estadísticas
            </span>
          </div>
          <div className="bg-white/[0.03] border border-white/8 rounded-2xl p-8 text-center">
            <p className="text-4xl mb-3">📊</p>
            <p className="text-white/45 text-sm font-medium">Próximamente</p>
            <p className="text-white/25 text-xs mt-1">
              Ventas del día, productos más pedidos, horas pico y más.
            </p>
          </div>
        </section>

      </main>
    </div>
  )
}

// ── OrderCard ──────────────────────────────────────────────────────────────

function OrderCard({ order, isUpdating, onAction }) {
  const [showItems, setShowItems] = useState(false)
  const nextAction = getNextAction(order)
  const canCancel = CANCELLABLE.has(order.status)

  return (
    <div className={[
      'bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden transition-opacity',
      isUpdating ? 'opacity-50' : '',
    ].join(' ')}>

      {/* ── Header row ── */}
      <div className="p-4 pb-2.5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-white text-sm">#{order.id}</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${STATUS_PILL[order.status]}`}>
                {order.status_display}
              </span>
            </div>
            <p className="text-xs text-white/50 mt-0.5 truncate">{order.cliente_nombre}</p>
          </div>
          <div className="text-right shrink-0">
            <p className="font-bold text-white text-sm">{formatCLP(order.total_amount)}</p>
            <p className="text-[10px] text-white/35 mt-0.5">{timeAgo(order.order_date)}</p>
          </div>
        </div>

        {/* Tags row */}
        <div className="flex flex-wrap gap-1.5 mt-2.5">
          <span className="text-[10px] bg-white/8 text-white/45 px-2 py-0.5 rounded-full">
            {order.tipo_entrega === 'REPARTO' ? '🚚' : '🏪'} {order.tipo_entrega_display}
          </span>
          <span className="text-[10px] bg-white/8 text-white/45 px-2 py-0.5 rounded-full">
            💳 {order.metodo_pago_display}
          </span>
        </div>

        {/* Customer phone */}
        {order.cliente_telefono && (
          <a
            href={`tel:${order.cliente_telefono}`}
            className="inline-flex items-center gap-1.5 mt-2.5 text-xs text-green-400/80 hover:text-green-300 transition-colors"
          >
            📞 {order.cliente_telefono}
          </a>
        )}

        {/* Customer notes */}
        {order.customer_notes && (
          <p className="mt-2.5 text-xs text-yellow-300/80 bg-yellow-500/8 rounded-xl px-3 py-2 leading-relaxed">
            📝 {order.customer_notes}
          </p>
        )}
      </div>

      {/* ── Items toggle ── */}
      <button
        onClick={() => setShowItems(v => !v)}
        className="w-full flex items-center justify-between px-4 py-2 text-xs text-white/35 hover:text-white/55 hover:bg-white/5 transition-colors border-t border-white/8"
      >
        <span>{order.items.length} producto{order.items.length !== 1 ? 's' : ''}</span>
        <span className="text-white/25">{showItems ? '▲' : '▼'}</span>
      </button>

      {/* ── Items list ── */}
      {showItems && (
        <div className="px-4 pb-3 pt-2 space-y-1.5 border-t border-white/5">
          {order.items.map(item => (
            <div key={item.id} className="flex items-center justify-between gap-2 text-xs">
              <span className="text-white/65">
                <span className="text-white/40">{item.quantity}×</span> {item.nombre_producto}
              </span>
              <span className="text-white/35 shrink-0">{formatCLP(item.price_at_purchase)}</span>
            </div>
          ))}
          {order.tipo_entrega === 'REPARTO' && Number(order.delivery_cost) > 0 && (
            <div className="flex items-center justify-between gap-2 text-xs pt-1.5 border-t border-white/5">
              <span className="text-white/35">Costo de envío</span>
              <span className="text-white/35">{formatCLP(order.delivery_cost)}</span>
            </div>
          )}
          <div className="flex items-center justify-between gap-2 text-xs pt-1.5 border-t border-white/5">
            <span className="text-white/55 font-medium">Total</span>
            <span className="text-white font-bold">{formatCLP(order.total_amount)}</span>
          </div>
        </div>
      )}

      {/* ── Actions ── */}
      {(nextAction || canCancel) && (
        <div className="px-4 pb-4 pt-3 flex gap-2 border-t border-white/5">
          {nextAction && (
            <button
              disabled={isUpdating}
              onClick={() => onAction(order.id, nextAction.status)}
              className="flex-1 py-3 rounded-xl bg-orange-500 hover:bg-orange-400 active:scale-[0.97] text-white font-bold text-sm transition-all disabled:opacity-50"
            >
              {isUpdating ? '…' : nextAction.label}
            </button>
          )}
          {canCancel && (
            <button
              disabled={isUpdating}
              onClick={() => onAction(order.id, 'CANCELLED')}
              title="Cancelar pedido"
              className="px-4 py-3 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-sm font-bold transition-colors disabled:opacity-50"
            >
              ✕
            </button>
          )}
        </div>
      )}
    </div>
  )
}
