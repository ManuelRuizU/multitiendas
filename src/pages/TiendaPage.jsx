import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'
import Header from '../components/Header'
import { useCart } from '../context/CartContext'

const formatPrice = (p) => `$${parseInt(p).toLocaleString('es-CL')}`

// Group array of products by subcategoria_nombre
function groupBySubcat(products) {
  const groups = {}
  for (const p of products) {
    const key = p.subcategoria_nombre || 'Menú'
    if (!groups[key]) groups[key] = []
    groups[key].push(p)
  }
  return groups
}

export default function TiendaPage() {
  const { slug }   = useParams()
  const navigate   = useNavigate()
  const { addItem, openCart } = useCart()

  const [tienda,   setTienda]   = useState(null)
  const [products, setProducts] = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)

  // Per-product UI state: 'idle' | 'adding' | 'added' | 'error'
  const [btnState, setBtnState] = useState({})

  useEffect(() => {
    setLoading(true)
    setError(null)

    api.get(`tiendas/${slug}/`)
      .then(({ data: t }) => {
        setTienda(t)
        return api.get('productos/', { params: { tienda_id: t.id } })
      })
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : (data.results ?? [])
        setProducts(list)
      })
      .catch(() => setError('No se pudo cargar la tienda. Verifica que el servidor esté activo.'))
      .finally(() => setLoading(false))
  }, [slug])

  const handleAdd = useCallback(async (productoId) => {
    setBtnState((s) => ({ ...s, [productoId]: 'adding' }))
    try {
      await addItem(productoId, 1)
      setBtnState((s) => ({ ...s, [productoId]: 'added' }))
      openCart()
      setTimeout(() => setBtnState((s) => ({ ...s, [productoId]: 'idle' })), 1500)
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Error'
      setBtnState((s) => ({ ...s, [productoId]: 'error:' + msg }))
      setTimeout(() => setBtnState((s) => ({ ...s, [productoId]: 'idle' })), 2500)
    }
  }, [addItem, openCart])

  // ── Loading skeleton ──
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-white">
        <Header subtitle="Cargando…" onBack={() => navigate(-1)} />
        <main className="max-w-3xl mx-auto px-4 pt-8 pb-16 space-y-4">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-20 bg-white/5 rounded-2xl animate-pulse" />
          ))}
        </main>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 text-white">
        <Header onBack={() => navigate(-1)} />
        <main className="flex flex-col items-center justify-center gap-4 pt-24 text-white/40">
          <p className="text-4xl">⚠️</p>
          <p className="text-sm">{error}</p>
          <button onClick={() => navigate('/')} className="text-orange-400 text-sm hover:underline">
            ← Volver al inicio
          </button>
        </main>
      </div>
    )
  }

  const grouped = groupBySubcat(products)

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header
        title={tienda?.nombre}
        subtitle={tienda?.horario_atencion ?? undefined}
        onBack={() => navigate(-1)}
      />

      <main className="max-w-3xl mx-auto px-4 pt-6 pb-16">

        {/* Tienda info banner */}
        {tienda && (
          <div className="flex gap-4 mb-6 p-4 bg-white/5 rounded-2xl border border-white/5">
            {tienda.logo
              ? <img src={tienda.logo} alt={tienda.nombre} className="w-16 h-16 rounded-xl object-cover shrink-0" />
              : <div className="w-16 h-16 rounded-xl bg-orange-500/20 flex items-center justify-center text-3xl shrink-0">🏪</div>
            }
            <div className="min-w-0">
              <h2 className="font-bold text-base leading-snug">{tienda.nombre}</h2>
              {tienda.descripcion && (
                <p className="text-xs text-white/45 mt-1 line-clamp-2 leading-relaxed">{tienda.descripcion}</p>
              )}
              {tienda.metodos_pago?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {tienda.metodos_pago.map((m) => (
                    <span key={m} className="text-[10px] bg-white/10 text-white/50 px-2 py-0.5 rounded-full">{m}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty state */}
        {products.length === 0 && (
          <div className="text-center py-20 text-white/25">
            <p className="text-4xl mb-3">🍽️</p>
            <p className="text-sm">Esta tienda aún no tiene productos publicados</p>
          </div>
        )}

        {/* Products grouped by subcategory */}
        {Object.entries(grouped).map(([subcat, items]) => (
          <section key={subcat} className="mb-8">
            <h3 className="text-xs font-semibold text-white/35 uppercase tracking-widest mb-3 px-1">
              {subcat}
            </h3>
            <div className="space-y-3">
              {items.map((p) => {
                const state   = btnState[p.id] ?? 'idle'
                const adding  = state === 'adding'
                const added   = state === 'added'
                const errMsg  = state.startsWith('error:') ? state.slice(6) : null

                return (
                  <div
                    key={p.id}
                    className="flex gap-3 bg-white/[0.04] hover:bg-white/[0.07] border border-white/5 rounded-2xl p-3 transition-colors"
                  >
                    {/* Image or placeholder */}
                    <div className="w-20 h-20 rounded-xl overflow-hidden shrink-0 bg-white/5">
                      {p.imagen
                        ? <img src={p.imagen} alt={p.nombre} className="w-full h-full object-cover" />
                        : <div className="w-full h-full flex items-center justify-center text-3xl">🍽️</div>
                      }
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0 flex flex-col justify-between">
                      <div>
                        <p className="font-semibold text-sm leading-snug">{p.nombre}</p>
                        {p.descripcion && (
                          <p className="text-xs text-white/35 mt-0.5 line-clamp-2 leading-relaxed">
                            {p.descripcion}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center justify-between mt-2">
                        <div>
                          <span className="font-bold text-sm text-orange-400">
                            {formatPrice(p.precio_efectivo)}
                          </span>
                          {p.tiene_recargo_tarjeta && (
                            <span className="text-[10px] text-white/30 ml-1.5">
                              / {formatPrice(p.precio_tarjeta)} tarjeta
                            </span>
                          )}
                        </div>

                        {errMsg ? (
                          <span role="alert" className="text-[10px] text-red-400 max-w-[120px] text-right leading-tight">
                            {errMsg}
                          </span>
                        ) : (
                          <button
                            onClick={() => handleAdd(p.id)}
                            disabled={adding || added}
                            aria-label={
                              added   ? `${p.nombre} agregado al carrito`
                              : adding ? `Agregando ${p.nombre}…`
                              : `Agregar ${p.nombre} al carrito`
                            }
                            aria-pressed={added}
                            className={[
                              'text-xs font-semibold px-3 py-1.5 rounded-full transition-all duration-200',
                              added
                                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                                : adding
                                  ? 'bg-white/5 text-white/30 border border-white/10 cursor-not-allowed'
                                  : 'bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 border border-orange-500/30 active:scale-95',
                            ].join(' ')}
                          >
                            {added ? '✓ Agregado' : adding ? '…' : '+ Agregar'}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        ))}

      </main>
    </div>
  )
}
