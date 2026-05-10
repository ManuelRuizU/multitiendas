import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import api from '../services/api'

function getGuestId() {
  let id = localStorage.getItem('guest_id')
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem('guest_id', id)
  }
  return id
}

function countItems(cart) {
  if (!cart?.grupos) return 0
  return cart.grupos.reduce(
    (total, grupo) => total + grupo.items.reduce((s, item) => s + item.cantidad, 0),
    0
  )
}

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const [cart, setCart]           = useState(null)
  const [itemCount, setItemCount] = useState(0)
  const [isCartOpen, setIsCartOpen] = useState(false)

  const openCart  = useCallback(() => setIsCartOpen(true),  [])
  const closeCart = useCallback(() => setIsCartOpen(false), [])

  const isAuth = () => !!localStorage.getItem('access_token')

  const applyCart = (data) => {
    setCart(data)
    setItemCount(countItems(data))
  }

  const fetchCart = useCallback(async () => {
    try {
      const params = isAuth() ? {} : { guest_id: getGuestId() }
      const { data } = await api.get('carritos/mi_carrito/', { params })
      applyCart(data)
    } catch {
      // No cart yet — that's fine
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const addItem = useCallback(async (productoId, cantidad = 1) => {
    const body = { producto_id: productoId, cantidad }
    if (!isAuth()) body.guest_id = getGuestId()
    const { data } = await api.post('carritos/agregar_producto/', body)
    applyCart(data)
    return data
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const updateItem = useCallback(async (productoId, cantidad) => {
    const body = { producto_id: productoId, cantidad }
    if (!isAuth()) body.guest_id = getGuestId()
    const { data } = await api.patch('carritos/actualizar_cantidad/', body)
    applyCart(data)
    return data
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const removeItem = useCallback(async (productoId) => {
    const body = { producto_id: productoId }
    if (!isAuth()) body.guest_id = getGuestId()
    const { data } = await api.post('carritos/eliminar_producto/', body)
    applyCart(data)
    return data
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const clearCart = useCallback(async () => {
    const body = {}
    if (!isAuth()) body.guest_id = getGuestId()
    const { data } = await api.post('carritos/vaciar_carrito/', body)
    applyCart(data)
    return data
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const mergeGuestCart = useCallback(async () => {
    const guestId = localStorage.getItem('guest_id')
    if (!guestId) return
    try {
      const { data } = await api.post('carritos/fusionar_carrito/', { guest_id: guestId })
      applyCart(data)
      localStorage.removeItem('guest_id')
    } catch {
      // Guest cart may not exist — ignore silently
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const resetCart = useCallback(() => {
    setCart(null)
    setItemCount(0)
    setIsCartOpen(false)
  }, [])

  useEffect(() => { fetchCart() }, [fetchCart])

  return (
    <CartContext.Provider value={{
      cart, itemCount,
      isCartOpen, openCart, closeCart,
      fetchCart, addItem, updateItem, removeItem, clearCart, mergeGuestCart, resetCart,
    }}>
      {children}
    </CartContext.Provider>
  )
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used inside CartProvider')
  return ctx
}
