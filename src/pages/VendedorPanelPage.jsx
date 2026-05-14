import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'

const fmt = (p) => `$${parseInt(p).toLocaleString('es-CL')}`

const TIPO_EMOJI = { COMIDA: '🍕', RETAIL: '🛍️', SERVICIOS: '🔧', OTRO: '🏪' }

export default function VendedorPanelPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { user, loading: authLoading } = useAuth()

  const bienvenida = searchParams.get('bienvenida') === '1'

  const [tiendas,    setTiendas]    = useState([])
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState(null)
  const [showBanner, setShowBanner] = useState(bienvenida)

  // Redirect if not authenticated or not a vendor (wait for auth to resolve first)
  useEffect(() => {
    if (authLoading) return
    if (!user) { navigate('/login'); return }
    if (!user.is_vendedor) { navigate('/'); return }
  }, [user, authLoading, navigate])

  useEffect(() => {
    api.get('tiendas/mis_tiendas/')
      .then(({ data }) => {
        setTiendas(Array.isArray(data) ? data : (data.results ?? []))
      })
      .catch(() => setError('No se pudieron cargar tus tiendas.'))
      .finally(() => setLoading(false))
  }, [])

  // Dismiss banner and clean URL param
  const dismissBanner = () => {
    setShowBanner(false)
    setSearchParams({}, { replace: true })
  }

  if (authLoading || !user) return null

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header title="Panel Vendedor" onBack={() => navigate(-1)} />

      <main className="max-w-3xl mx-auto px-4 pt-6 pb-16 space-y-5">

        {/* ── Banner de bienvenida ── */}
        {showBanner && (
          <div className="relative bg-gradient-to-r from-orange-900/40 to-amber-900/20 border border-orange-700/40 rounded-2xl p-5 overflow-hidden">
            <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 80% 50%, rgba(249,115,22,0.08), transparent 60%)' }} />
            <div className="relative">
              <p className="text-2xl mb-2">🎉</p>
              <h2 className="font-black text-lg leading-snug text-white">
                ¡Bienvenido a MultiTienda, {user.first_name || user.username}!
              </h2>
              <p className="text-sm text-white/60 mt-1.5 leading-relaxed">
                Tu cuenta y tienda están listas. Agrega productos y empieza a vender hoy.
              </p>
              <button
                onClick={dismissBanner}
                className="mt-4 text-xs text-orange-400 hover:text-orange-300 transition-colors"
              >
                Entendido ✓
              </button>
            </div>
          </div>
        )}

        {/* ── Mis tiendas ── */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-white/80">Mis tiendas</h2>
            <Link
              to="/vendedor/crear-tienda"
              className="text-xs text-orange-400 hover:text-orange-300 border border-orange-500/30 hover:bg-orange-500/10 px-3 py-1.5 rounded-full transition-all"
            >
              + Nueva tienda
            </Link>
          </div>

          {loading && (
            <div className="space-y-3">
              {[1, 2].map((n) => (
                <div key={n} className="h-20 bg-white/5 rounded-2xl animate-pulse" />
              ))}
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-800/40 text-red-400 rounded-xl p-4 text-sm text-center">
              {error}
            </div>
          )}

          {!loading && !error && tiendas.length === 0 && (
            <div className="text-center py-10 text-white/25 border border-dashed border-white/10 rounded-2xl">
              <p className="text-3xl mb-2">🏪</p>
              <p className="text-sm">Aún no tienes tiendas</p>
              <Link
                to="/vendedor/crear-tienda"
                className="inline-block mt-3 text-sm text-orange-400 hover:text-orange-300 transition-colors"
              >
                Crear mi primera tienda →
              </Link>
            </div>
          )}

          {!loading && !error && tiendas.length > 0 && (
            <div className="space-y-3">
              {tiendas.map((tienda) => (
                <TiendaCard key={tienda.id} tienda={tienda} navigate={navigate} />
              ))}
            </div>
          )}
        </section>

        {/* ── Acciones rápidas ── */}
        <section>
          <h2 className="text-sm font-bold text-white/80 mb-3">Acciones rápidas</h2>
          <div className="grid grid-cols-2 gap-3">
            <ActionCard icon="📦" label="Mis pedidos" desc="Ver y gestionar pedidos" onClick={() => navigate('/vendedor/pedidos')} />
            <ActionCard icon="🏷️" label="Productos"   desc="Agregar o editar productos" onClick={() => navigate('/vendedor/productos')} />
            <ActionCard icon="📊" label="Estadísticas" desc="Ventas y métricas" onClick={() => navigate('/vendedor/estadisticas')} />
            <ActionCard icon="⚙️"  label="Configuración" desc="Datos del negocio" onClick={() => navigate('/perfil')} />
          </div>
        </section>

      </main>
    </div>
  )
}

function TiendaCard({ tienda, navigate }) {
  return (
    <div className="flex items-center gap-4 bg-white/[0.04] hover:bg-white/[0.07] border border-white/5 rounded-2xl p-4 transition-colors">
      {/* Logo */}
      <div className="w-12 h-12 rounded-xl overflow-hidden shrink-0 bg-white/5 flex items-center justify-center text-2xl">
        {tienda.logo
          ? <img src={tienda.logo} alt={tienda.nombre} className="w-full h-full object-cover" />
          : (TIPO_EMOJI[tienda.tipo_negocio] ?? '🏪')
        }
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm leading-snug truncate">{tienda.nombre}</p>
        <p className="text-xs text-white/35 truncate mt-0.5">{tienda.direccion}</p>
        <div className="flex items-center gap-2 mt-1.5">
          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${tienda.activo ? 'bg-green-900/40 text-green-400' : 'bg-white/5 text-white/30'}`}>
            {tienda.activo ? '● Activa' : '○ Inactiva'}
          </span>
          {tienda.metodos_pago?.map((m) => (
            <span key={m} className="text-[10px] bg-white/5 text-white/30 px-1.5 py-0.5 rounded-full">{m}</span>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col gap-1.5 shrink-0">
        <button
          onClick={() => navigate(`/tienda/${tienda.slug}`)}
          className="text-xs text-white/50 hover:text-white border border-white/10 hover:border-white/20 px-3 py-1 rounded-full transition-all"
        >
          Ver →
        </button>
        <button
          onClick={() => navigate(`/vendedor/tienda/${tienda.slug}/editar`)}
          className="text-xs text-orange-400 hover:text-orange-300 border border-orange-500/20 hover:border-orange-500/40 px-3 py-1 rounded-full transition-all"
        >
          Editar
        </button>
      </div>
    </div>
  )
}

function ActionCard({ icon, label, desc, onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-start gap-1.5 bg-white/[0.04] hover:bg-white/[0.07] border border-white/5 rounded-2xl p-4 text-left transition-colors active:scale-[0.98]"
    >
      <span className="text-xl">{icon}</span>
      <p className="text-sm font-semibold text-white leading-none">{label}</p>
      <p className="text-xs text-white/35 leading-snug">{desc}</p>
    </button>
  )
}
