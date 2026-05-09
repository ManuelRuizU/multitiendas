import { useCart } from '../context/CartContext'

export default function Header({ title = 'MultiTienda Angol', subtitle, onBack }) {
  const { itemCount, openCart } = useCart()

  return (
    <header className="border-b border-white/10 backdrop-blur-sm sticky top-0 z-20 bg-slate-950/80">
      <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-3">

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

        <div className="flex-1 min-w-0">
          <h1 className="text-lg font-bold leading-none truncate">{title}</h1>
          {subtitle && (
            <p className="text-xs text-white/40 mt-0.5 truncate">{subtitle}</p>
          )}
        </div>

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

      </div>
    </header>
  )
}
