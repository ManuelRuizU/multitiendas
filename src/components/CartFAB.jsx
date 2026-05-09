import { useLocation } from 'react-router-dom'
import { useCart } from '../context/CartContext'

const HIDDEN_ON = ['/checkout']

export default function CartFAB() {
  const { itemCount, isCartOpen, openCart } = useCart()
  const { pathname } = useLocation()

  // Hide on checkout, when drawer is already open, or when cart is empty
  if (HIDDEN_ON.includes(pathname) || isCartOpen || itemCount === 0) return null

  return (
    <button
      onClick={openCart}
      aria-label={`Ver carrito — ${itemCount} ${itemCount === 1 ? 'producto' : 'productos'}`}
      className={[
        'fixed bottom-6 left-1/2 -translate-x-1/2 z-50',
        'flex items-center gap-2.5',
        'bg-orange-500 hover:bg-orange-400 active:scale-95',
        'text-white font-semibold text-sm',
        'px-5 py-3 rounded-full',
        'shadow-lg shadow-orange-500/40',
        'transition-all duration-200',
      ].join(' ')}
    >
      <span aria-hidden="true" className="text-base">🛒</span>
      <span aria-live="polite" aria-atomic="true">
        {itemCount} {itemCount === 1 ? 'producto' : 'productos'}
      </span>
      <span className="opacity-60">·</span>
      <span>Ver carrito</span>
    </button>
  )
}
