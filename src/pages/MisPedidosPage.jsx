import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('es-CL', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatCLP(n) {
  return `$${Number(n).toLocaleString('es-CL')}`
}

// ── Config ─────────────────────────────────────────────────────────────────

const STATUS_CONFIG = {
  PENDING:    { label: 'Pendiente',      emoji: '🔴', pill: 'bg-red-500/15 text-red-400 border-red-500/30' },
  CONFIRMED:  { label: 'Confirmado',     emoji: '🟡', pill: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30' },
  PREPARING:  { label: 'En preparación', emoji: '🟠', pill: 'bg-orange-500/15 text-orange-400 border-orange-500/30' },
  ON_THE_WAY: { label: 'En camino',      emoji: '🚴', pill: 'bg-purple-500/15 text-purple-400 border-purple-500/30' },
  DELIVERED:  { label: 'Entregado',      emoji: '✅', pill: 'bg-green-500/15 text-green-400 border-green-500/30' },
  CANCELLED:  { label: 'Cancelado',      emoji: '❌', pill: 'bg-white/8 text-white/35 border-white/10' },
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function MisPedidosPage() {
  const navigate = useNavigate()
  const { user, loading: authLoading, openAuthModal } = useAuth()

  const [pedidos,  setPedidos]  = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)

  // Not logged in → open modal and go home
  useEffect(() => {
    if (authLoading) return
    if (!user) {
      openAuthModal()
      navigate('/', { replace: true })
    }
  }, [user, authLoading, openAuthModal, navigate])

  useEffect(() => {
    if (authLoading || !user) return
    api.get('pedidos/')
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : (data.results ?? [])
        list.sort((a, b) => new Date(b.order_date) - new Date(a.order_date))
        setPedidos(list)
      })
      .catch(() => setError('No se pudieron cargar tus pedidos.'))
      .finally(() => setLoading(false))
  }, [user, authLoading])

  if (authLoading || !user) return null

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header title="Mis pedidos" onBack={() => navigate(-1)} />

      <main className="max-w-2xl mx-auto px-4 pt-6 pb-16 space-y-4">

        {/* Skeleton */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-32 bg-white/5 rounded-2xl animate-pulse" />
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-900/20 border border-red-800/40 text-red-400 rounded-xl p-4 text-sm text-center">
            {error}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && pedidos.length === 0 && (
          <div className="text-center py-20">
            <p className="text-5xl mb-4">📦</p>
            <p className="text-lg font-semibold text-white/80">Aún no tienes pedidos</p>
            <p className="text-sm text-white/40 mt-1.5">¿Qué se te antoja hoy?</p>
            <Link
              to="/tiendas"
              className="inline-block mt-6 px-6 py-3 bg-orange-500 hover:bg-orange-400 active:scale-[0.97] text-white font-semibold rounded-full text-sm transition-all"
            >
              Explorar tiendas
            </Link>
          </div>
        )}

        {/* Pedido cards */}
        {!loading && !error && pedidos.map((order) => (
          <PedidoCard key={order.id} order={order} />
        ))}

      </main>
    </div>
  )
}

// ── PedidoCard ─────────────────────────────────────────────────────────────

function PedidoCard({ order }) {
  const [showItems, setShowItems] = useState(false)
  const cfg = STATUS_CONFIG[order.status] ?? STATUS_CONFIG.PENDING

  const whatsappHref =
    order.tienda_whatsapp && order.resumen_whatsapp
      ? `${order.tienda_whatsapp}?text=${encodeURIComponent(order.resumen_whatsapp)}`
      : null

  return (
    <div className="bg-white/[0.04] border border-white/8 rounded-2xl overflow-hidden">

      {/* ── Header row ── */}
      <div className="p-4 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-white text-sm">#{order.id}</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${cfg.pill}`}>
                {cfg.emoji} {cfg.label}
              </span>
            </div>
            <p className="text-xs font-medium text-white/65 mt-1 truncate">{order.tienda_nombre}</p>
            <p className="text-[11px] text-white/30 mt-0.5">{formatDate(order.order_date)}</p>
          </div>
          <div className="text-right shrink-0">
            <p className="font-bold text-white text-sm">{formatCLP(order.total_amount)}</p>
            <p className="text-[10px] text-white/35 mt-0.5">
              {order.tipo_entrega === 'REPARTO' ? '🚚 Reparto' : '🏪 Retiro'}
            </p>
          </div>
        </div>
      </div>

      {/* ── Items toggle ── */}
      <button
        onClick={() => setShowItems((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2 text-xs text-white/35 hover:text-white/55 hover:bg-white/5 transition-colors border-t border-white/8"
      >
        <span>
          {order.items?.length ?? 0} producto{order.items?.length !== 1 ? 's' : ''}
        </span>
        <span className="text-white/25">{showItems ? '▲' : '▼'}</span>
      </button>

      {/* ── Items list ── */}
      {showItems && (
        <div className="px-4 pb-3 pt-2 space-y-1.5 border-t border-white/5">
          {order.items?.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-2 text-xs">
              <span className="text-white/65">
                <span className="text-white/35">{item.quantity}×</span> {item.nombre_producto}
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

      {/* ── WhatsApp button ── */}
      {whatsappHref && (
        <div className="px-4 pb-4 pt-2.5 border-t border-white/5">
          <a
            href={whatsappHref}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-green-600/20 hover:bg-green-600/30 border border-green-600/30 hover:border-green-500/50 text-green-400 text-sm font-semibold transition-all"
          >
            <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" aria-hidden="true">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
            </svg>
            Contactar por WhatsApp
          </a>
        </div>
      )}
    </div>
  )
}
