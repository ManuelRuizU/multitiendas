import { useEffect, useRef, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import { useAuth } from '../context/AuthContext'

const AUTH_PAGES = ['/registro-vendedor', '/checkout', '/login', '/registro']

function initials(user) {
  const name = user?.first_name || user?.username || ''
  return name.slice(0, 2).toUpperCase() || 'U'
}

export default function Header({ title = 'MultiTienda Angol', subtitle, onBack }) {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { itemCount, openCart, resetCart } = useCart()
  const { user, logout, openAuthModal } = useAuth()

  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)

  // Close dropdown on outside click / touch
  useEffect(() => {
    if (!open) return
    function handle(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handle)
    document.addEventListener('touchstart', handle)
    return () => {
      document.removeEventListener('mousedown', handle)
      document.removeEventListener('touchstart', handle)
    }
  }, [open])

  const handleLogout = () => {
    setOpen(false)
    logout()
    resetCart()
    navigate('/')
  }

  const go = (path) => { setOpen(false); navigate(path) }

  return (
    <header className="border-b border-white/10 backdrop-blur-sm sticky top-0 z-20 bg-slate-950/80">
      <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-3">

        {/* Back button or brand icon */}
        {onBack ? (
          <button
            onClick={onBack}
            aria-label="Volver"
            className="text-white/50 hover:text-white transition-colors text-lg leading-none p-1 -ml-1 rounded"
          >
            ←
          </button>
        ) : (
          <span aria-hidden="true" className="text-2xl">🛒</span>
        )}

        {/* Title */}
        <div className="flex-1 min-w-0">
          <h1 className="text-lg font-bold leading-none truncate">{title}</h1>
          {subtitle && (
            <p className="text-xs text-white/40 mt-0.5 truncate">{subtitle}</p>
          )}
        </div>

        {/* Cart button */}
        <button
          onClick={openCart}
          aria-label={
            itemCount > 0
              ? `Carrito con ${itemCount} ${itemCount === 1 ? 'producto' : 'productos'}`
              : 'Ver carrito'
          }
          className="relative flex items-center gap-1.5 text-sm text-white/55 hover:text-white transition-colors px-3 py-1.5 rounded-full hover:bg-white/10 shrink-0"
        >
          <span aria-hidden="true" className="text-lg">🛒</span>
          <span className="hidden sm:inline text-xs">Carrito</span>
          {itemCount > 0 && (
            <span
              aria-hidden="true"
              className="absolute -top-1 -right-1 bg-orange-500 text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1 leading-none"
            >
              {itemCount > 99 ? '99+' : itemCount}
            </span>
          )}
        </button>

        {/* User area */}
        {user ? (
          <div ref={menuRef} className="relative shrink-0">
            {/* Avatar button */}
            <button
              onClick={() => setOpen((v) => !v)}
              aria-label="Menú de usuario"
              aria-expanded={open}
              aria-haspopup="menu"
              className="w-8 h-8 rounded-full bg-orange-500/80 hover:bg-orange-500 flex items-center justify-center text-xs font-bold text-white transition-colors"
            >
              {initials(user)}
            </button>

            {/* Dropdown */}
            <div
              role="menu"
              aria-label="Opciones de usuario"
              className={[
                'absolute right-0 top-11 w-56',
                'bg-slate-800 border border-white/10 rounded-xl',
                'shadow-2xl shadow-black/60 py-1 z-50',
                'transition-all duration-200 ease-[cubic-bezier(0.34,1.56,0.64,1)] origin-top-right',
                open
                  ? 'opacity-100 scale-100 translate-y-0 pointer-events-auto'
                  : 'opacity-0 scale-95 -translate-y-1 pointer-events-none',
              ].join(' ')}
            >
              {/* User header */}
              <div className="px-4 py-3 border-b border-white/10">
                <p className="text-sm font-semibold text-white leading-none truncate">
                  {user.first_name
                    ? `${user.first_name} ${user.last_name || ''}`.trim()
                    : user.username
                  }
                </p>
                <p className="text-xs text-white/40 mt-0.5 truncate">{user.email}</p>
                {/* Role badges */}
                {(user.is_vendedor || user.is_repartidor) && (
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {user.is_vendedor && (
                      <span className="text-[9px] font-semibold bg-orange-900/40 text-orange-300 border border-orange-800/40 px-1.5 py-0.5 rounded-full">
                        Vendedor
                      </span>
                    )}
                    {user.is_repartidor && (
                      <span className="text-[9px] font-semibold bg-green-900/40 text-green-300 border border-green-800/40 px-1.5 py-0.5 rounded-full">
                        Repartidor
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Common options */}
              <MenuItem onClick={() => go('/perfil')}      icon="👤" label="Mi perfil" />
              <MenuItem onClick={() => go('/mis-pedidos')} icon="📦" label="Mis pedidos" />

              {/* Vendor panel — only if is_vendedor */}
              {user.is_vendedor && (
                <MenuItem onClick={() => go('/vendedor/panel')}   icon="🏪" label="Panel vendedor" />
              )}

              {/* Delivery panel — only if is_repartidor */}
              {user.is_repartidor && (
                <MenuItem onClick={() => go('/repartidor/panel')} icon="🛵" label="Panel repartidor" />
              )}

              {/* Logout */}
              <div className="border-t border-white/10 mt-1 pt-1">
                <MenuItem onClick={handleLogout} icon="🚪" label="Cerrar sesión" danger />
              </div>
            </div>
          </div>
        ) : (
          <button
            onClick={() => AUTH_PAGES.includes(pathname) ? navigate('/login') : openAuthModal()}
            aria-label="Iniciar sesión"
            className="shrink-0 text-xs font-semibold text-orange-400 hover:text-orange-300 px-3 py-1.5 rounded-full border border-orange-500/30 hover:border-orange-400/50 hover:bg-orange-500/10 transition-all"
          >
            Ingresar
          </button>
        )}

      </div>
    </header>
  )
}

function MenuItem({ onClick, icon, label, danger = false }) {
  return (
    <button
      role="menuitem"
      onClick={onClick}
      className={[
        'w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-colors',
        danger
          ? 'text-red-400 hover:bg-red-900/20 hover:text-red-300'
          : 'text-white/80 hover:bg-white/10 hover:text-white',
      ].join(' ')}
    >
      <span aria-hidden="true" className="text-base leading-none shrink-0">{icon}</span>
      {label}
    </button>
  )
}
