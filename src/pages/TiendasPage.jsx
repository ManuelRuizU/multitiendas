import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../services/api'
import Header from '../components/Header'

const TIPO_EMOJI = { COMIDA: '🍕', RETAIL: '🛍️', SERVICIOS: '🔧', OTRO: '🏪' }

// "Cafeterías" → "cafeterias"
const toSlug = (s) =>
  s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/\s+/g, '-')

export default function TiendasPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const categoriaSlug = searchParams.get('categoria') // "pizzas" | null

  const [tiendas,        setTiendas]        = useState([])
  const [categoriaLabel, setCategoriaLabel] = useState(null)
  const [loading,        setLoading]        = useState(true)
  const [error,          setError]          = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    setCategoriaLabel(null)

    async function load() {
      if (!categoriaSlug) {
        // Sin filtro → todas las tiendas activas
        const { data } = await api.get('tiendas/')
        const list = Array.isArray(data) ? data : (data.results ?? [])
        setTiendas(list)
        return
      }

      // 1. Buscar la categoría que coincida con el slug
      const { data: cats } = await api.get('categorias-plataforma/')
      const catList = Array.isArray(cats) ? cats : (cats.results ?? [])
      const cat = catList.find((c) => toSlug(c.nombre) === categoriaSlug)

      if (cat) {
        setCategoriaLabel(`${cat.emoji} ${cat.nombre}`)
        // 2. Filtrar tiendas por tipo_negocio de esa categoría
        const { data } = await api.get('tiendas/', { params: { tipo_negocio: cat.tipo_negocio } })
        const list = Array.isArray(data) ? data : (data.results ?? [])
        setTiendas(list)
      } else {
        // Slug desconocido → mostrar todas
        const { data } = await api.get('tiendas/')
        const list = Array.isArray(data) ? data : (data.results ?? [])
        setTiendas(list)
      }
    }

    load()
      .catch(() => setError('No se pudo cargar las tiendas. Verifica que el servidor esté activo.'))
      .finally(() => setLoading(false))
  }, [categoriaSlug])

  const title    = categoriaLabel ?? 'Todas las tiendas'
  const subtitle = loading ? 'Cargando…' : `${tiendas.length} tienda${tiendas.length !== 1 ? 's' : ''}`

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header
        title={title}
        subtitle={!loading && !error ? subtitle : undefined}
        onBack={() => navigate(-1)}
      />

      <main className="max-w-5xl mx-auto px-4 pt-6 pb-16">

        {/* ── Loading skeletons ── */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((n) => (
              <div key={n} className="bg-white/5 rounded-2xl border border-white/5 overflow-hidden animate-pulse">
                <div className="h-36 bg-white/5" />
                <div className="p-4 space-y-2.5">
                  <div className="h-4 bg-white/10 rounded-full w-2/3" />
                  <div className="h-3 bg-white/5  rounded-full w-full" />
                  <div className="h-3 bg-white/5  rounded-full w-4/5" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── Error ── */}
        {error && (
          <div className="bg-red-900/20 border border-red-800/40 text-red-400 rounded-xl p-4 text-sm text-center">
            {error}
          </div>
        )}

        {/* ── Empty state ── */}
        {!loading && !error && tiendas.length === 0 && (
          <div className="text-center py-20 text-white/30">
            <p className="text-5xl mb-3">🏪</p>
            <p className="text-sm font-medium">No hay tiendas disponibles en esta categoría</p>
            <button
              onClick={() => navigate('/tiendas')}
              className="mt-4 text-sm text-orange-400 hover:text-orange-300 transition-colors"
            >
              Ver todas las tiendas
            </button>
          </div>
        )}

        {/* ── Tiendas grid ── */}
        {!loading && !error && tiendas.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {tiendas.map((tienda) => (
              <button
                key={tienda.id}
                onClick={() => navigate(`/tienda/${tienda.slug}`)}
                aria-label={`Ver tienda ${tienda.nombre}${tienda.horario_atencion ? `, ${tienda.horario_atencion}` : ''}`}
                className="group bg-white/5 border border-white/10 hover:border-orange-500/30 hover:bg-white/[0.08] rounded-2xl overflow-hidden text-left transition-all duration-200 hover:-translate-y-0.5 w-full"
              >
                {/* Thumbnail */}
                <div
                  className="h-36 flex items-center justify-center overflow-hidden"
                  style={{ background: 'linear-gradient(135deg,rgba(249,115,22,.09),rgba(251,191,36,.04))' }}
                >
                  {tienda.logo
                    ? <img src={tienda.logo} alt={tienda.nombre} className="w-full h-full object-cover" />
                    : <span aria-hidden="true" className="text-5xl">{TIPO_EMOJI[tienda.tipo_negocio] ?? '🏪'}</span>
                  }
                </div>

                {/* Info */}
                <div className="p-4">
                  <h2 className="font-semibold text-white text-sm leading-snug group-hover:text-orange-400 transition-colors">
                    {tienda.nombre}
                  </h2>
                  {tienda.descripcion && (
                    <p className="text-xs text-white/40 mt-1 line-clamp-2 leading-relaxed">
                      {tienda.descripcion}
                    </p>
                  )}
                  {tienda.horario_atencion && (
                    <p className="text-xs text-white/30 mt-2">
                      <span aria-hidden="true">🕐</span> {tienda.horario_atencion}
                    </p>
                  )}
                  {tienda.metodos_pago?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-3" aria-label="Métodos de pago">
                      {tienda.metodos_pago.map((m) => (
                        <span key={m} className="text-[10px] bg-white/10 text-white/50 px-2 py-0.5 rounded-full">
                          {m}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}

      </main>
    </div>
  )
}
