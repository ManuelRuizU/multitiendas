import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import Header from '../components/Header'

const toSlug = (s) =>
  s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/\s+/g, '-')

export default function Home() {
  const navigate      = useNavigate()
  const containerRef  = useRef(null)
  const wrapperRefs   = useRef([])
  const didDragRef    = useRef(false)

  const [categories,  setCategories]  = useState([])
  const [heroBanner,  setHeroBanner]  = useState(null)

  // ── Cargar config de plataforma (hero banner) ────────────────────
  useEffect(() => {
    api.get('configuracion/')
      .then(({ data }) => { if (data.hero_banner) setHeroBanner(data.hero_banner) })
      .catch(() => {})
  }, [])

  // ── Cargar categorías ────────────────────────────────────────────
  useEffect(() => {
    api.get('categorias-plataforma/')
      .then((res) => {
        const d = res.data
        setCategories(Array.isArray(d) ? d : (d.results ?? []))
      })
      .catch(() => {
        setCategories([
          { id: 1, nombre: 'Pizzas',       emoji: '🍕', tipo_negocio: 'COMIDA', orden: 1 },
          { id: 2, nombre: 'Sushi',        emoji: '🍣', tipo_negocio: 'COMIDA', orden: 2 },
          { id: 3, nombre: 'Hamburguesas', emoji: '🍔', tipo_negocio: 'COMIDA', orden: 3 },
          { id: 4, nombre: 'Cafeterías',   emoji: '☕', tipo_negocio: 'COMIDA', orden: 4 },
          { id: 5, nombre: 'Pastelerías',  emoji: '🧁', tipo_negocio: 'COMIDA', orden: 5 },
          { id: 6, nombre: 'Minimarket',   emoji: '🛒', tipo_negocio: 'RETAIL', orden: 6 },
          { id: 7, nombre: 'Farmacias',    emoji: '💊', tipo_negocio: 'RETAIL', orden: 7 },
          { id: 8, nombre: 'Pollos',       emoji: '🍗', tipo_negocio: 'COMIDA', orden: 8 },
        ])
      })
  }, [])

  // ── Orbital animation + drag ─────────────────────────────────────
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const RADIUS    = container.clientWidth * 0.40
    const AUTO_SPEED = 0.3
    let angle             = -90
    let isDragging        = false
    let velocity          = AUTO_SPEED
    let lastInteractionTime = -Infinity
    let lastPointerAngle  = 0
    let startClientX      = 0
    let startClientY      = 0
    let raf

    function pointerAngle(e) {
      const r  = container.getBoundingClientRect()
      const cx = r.left + r.width  / 2
      const cy = r.top  + r.height / 2
      const p  = e.touches ? e.touches[0] : e
      return Math.atan2(p.clientY - cy, p.clientX - cx) * (180 / Math.PI)
    }

    function render() {
      const total = wrapperRefs.current.filter(Boolean).length
      if (total === 0) return
      wrapperRefs.current.forEach((el, i) => {
        if (!el) return
        const a     = (i / total) * 360 + angle
        el.style.transform = `rotate(${a}deg) translateX(${RADIUS}px)`
        const inner = el.firstElementChild
        if (inner) inner.style.transform = `rotate(${-a}deg)`
      })
    }

    function tick() {
      if (!isDragging) {
        const idle = performance.now() - lastInteractionTime
        if (idle < 5000) {
          velocity *= 0.97
        } else {
          velocity += (AUTO_SPEED - velocity) * 0.02
        }
        angle += velocity
      }
      render()
      raf = requestAnimationFrame(tick)
    }

    function onDown(e) {
      isDragging = true
      velocity   = 0
      didDragRef.current = false
      lastPointerAngle   = pointerAngle(e)
      const p = e.touches ? e.touches[0] : e
      startClientX = p.clientX
      startClientY = p.clientY
    }

    function onMouseMove(e) {
      if (!isDragging) return
      const dx = e.clientX - startClientX
      const dy = e.clientY - startClientY
      if (Math.sqrt(dx * dx + dy * dy) > 5) didDragRef.current = true
      const curr = pointerAngle(e)
      let d = curr - lastPointerAngle
      if (d >  180) d -= 360
      if (d < -180) d += 360
      velocity = d
      angle   += d
      lastPointerAngle = curr
    }

    function onTouchMove(e) {
      if (!isDragging) return
      const p  = e.touches[0]
      const dx = p.clientX - startClientX
      const dy = p.clientY - startClientY
      if (Math.sqrt(dx * dx + dy * dy) > 5) didDragRef.current = true
      const curr = pointerAngle(e)
      let d = curr - lastPointerAngle
      if (d >  180) d -= 360
      if (d < -180) d += 360
      velocity = d
      angle   += d
      lastPointerAngle = curr
      if (e.cancelable) e.preventDefault()
    }

    function onUp() {
      isDragging = false
      lastInteractionTime = performance.now()
    }

    raf = requestAnimationFrame(tick)
    container.addEventListener('mousedown', onDown)
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup',   onUp)
    container.addEventListener('touchstart', onDown)
    window.addEventListener('touchmove', onTouchMove, { passive: false })
    window.addEventListener('touchend',  onUp)

    return () => {
      cancelAnimationFrame(raf)
      container.removeEventListener('mousedown', onDown)
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup',   onUp)
      container.removeEventListener('touchstart', onDown)
      window.removeEventListener('touchmove', onTouchMove)
      window.removeEventListener('touchend',  onUp)
    }
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-white">

      <Header subtitle="Pide a tus tiendas favoritas" />

      {/* ── Hero banner ── */}
      {heroBanner && (
        <div className="relative w-full overflow-hidden">
          <img
            src={heroBanner}
            alt="MultiTienda Angol"
            className="w-full h-44 object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 to-transparent pointer-events-none" />
        </div>
      )}

      <main className="max-w-5xl mx-auto px-4 pt-10 pb-16">

        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold">¿Qué quieres pedir hoy?</h2>
          <p className="text-xs text-white/30 mt-1.5 tracking-wide">
            Arrastra para girar · Toca una categoría
          </p>
        </div>

        {/* ── Orbital ── */}
        <div
          ref={containerRef}
          role="region"
          aria-label="Categorías de tiendas"
          className="relative w-full max-w-[420px] aspect-square mx-auto select-none cursor-grab active:cursor-grabbing"
        >
          {/* Decorative orbit ring */}
          <div
            className="absolute rounded-full border border-dashed border-white/15 pointer-events-none"
            style={{ inset: '10%' }}
          />

          {/* Outer glow */}
          <div
            className="absolute rounded-full pointer-events-none"
            style={{ inset: '8%', boxShadow: 'inset 0 0 60px 10px rgba(249,115,22,0.04)' }}
          />

          {/* Central orb — clickable, pointer-events-auto breaks out of parent pointer-events-none */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <button
              onClick={() => { if (!didDragRef.current) navigate('/tiendas') }}
              aria-label="Ver todas las tiendas"
              className="central-orb w-28 h-28 rounded-full flex flex-col items-center justify-center text-center z-10 pointer-events-auto cursor-pointer"
            >
              <span className="text-[22px] font-black leading-tight">Multi</span>
              <span className="text-[22px] font-black leading-tight">Tienda</span>
              <span className="text-[9px] font-semibold text-white/65 mt-0.5 tracking-[0.2em]">ANGOL</span>
            </button>
          </div>

          {/* Category nodes */}
          {categories.map((cat, i) => (
            <div
              key={cat.id}
              ref={(el) => { wrapperRefs.current[i] = el }}
              className="absolute w-16 h-16"
              style={{ left: '50%', top: '50%', marginLeft: '-32px', marginTop: '-32px' }}
            >
              <button
                onClick={() => { if (!didDragRef.current) navigate(`/tiendas?categoria=${toSlug(cat.nombre)}`) }}
                aria-label={`Ver tiendas de ${cat.nombre}`}
                className="w-full h-full rounded-full flex flex-col items-center justify-center gap-0.5 border bg-white/10 border-white/20 hover:bg-white/20 hover:border-white/40 transition-colors duration-200"
              >
                <span className="text-[22px] leading-none pointer-events-none">{cat.emoji}</span>
                <span className="text-[9px] font-medium text-white/80 text-center leading-none px-0.5 pointer-events-none">
                  {cat.nombre}
                </span>
              </button>
            </div>
          ))}
        </div>

      </main>
    </div>
  )
}
