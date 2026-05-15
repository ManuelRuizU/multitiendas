import { useLocation } from 'react-router-dom'
import { useCart } from '../context/CartContext'

const HIDDEN_ON = ['/checkout']

export default function CartFAB() {
  const { itemCount, isCartOpen, openCart, pendingWaOrders } = useCart()
  const { pathname } = useLocation()

  const pendingUnsent = pendingWaOrders.filter(o => !o.sent)
  const hasPending    = pendingUnsent.length > 0

  if (HIDDEN_ON.includes(pathname) || isCartOpen) return null
  if (!hasPending && itemCount === 0) return null

  return (
    <button
      onClick={openCart}
      aria-label={
        hasPending
          ? `${pendingUnsent.length} pedido${pendingUnsent.length !== 1 ? 's' : ''} pendiente${pendingUnsent.length !== 1 ? 's' : ''} de enviar por WhatsApp`
          : `Ver carrito — ${itemCount} ${itemCount === 1 ? 'producto' : 'productos'}`
      }
      className={[
        'fixed bottom-6 left-1/2 -translate-x-1/2 z-50',
        'flex items-center gap-2.5',
        hasPending
          ? 'bg-green-600 hover:bg-green-500 shadow-lg shadow-green-600/40'
          : 'bg-orange-500 hover:bg-orange-400 shadow-lg shadow-orange-500/40',
        'active:scale-95 text-white font-semibold text-sm',
        'px-5 py-3 rounded-full transition-all duration-200',
      ].join(' ')}
    >
      {hasPending ? (
        <>
          <span aria-hidden="true" className="text-base">📲</span>
          <span aria-live="polite" aria-atomic="true">
            Enviar pedidos
          </span>
          {pendingUnsent.length > 1 && (
            <span className="bg-white/25 rounded-full text-xs px-1.5 py-0.5 font-bold leading-none">
              {pendingUnsent.length}
            </span>
          )}
        </>
      ) : (
        <>
          <span aria-hidden="true" className="text-base">🛒</span>
          <span aria-live="polite" aria-atomic="true">
            {itemCount} {itemCount === 1 ? 'producto' : 'productos'}
          </span>
          <span className="opacity-60">·</span>
          <span>Ver carrito</span>
        </>
      )}
    </button>
  )
}
