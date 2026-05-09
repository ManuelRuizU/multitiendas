import { Routes, Route } from 'react-router-dom'
import { CartProvider } from './context/CartContext'
import CartFAB from './components/CartFAB'
import CartDrawer from './components/CartDrawer'
import Home from './pages/Home'
import TiendasPage from './pages/TiendasPage'
import TiendaPage from './pages/TiendaPage'
import CarritoPage from './pages/CarritoPage'
import CheckoutPage from './pages/CheckoutPage'

export default function App() {
  return (
    <CartProvider>
      <CartFAB />
      <CartDrawer />
      <Routes>
        <Route path="/"             element={<Home />} />
        <Route path="/tiendas"      element={<TiendasPage />} />
        <Route path="/tienda/:slug" element={<TiendaPage />} />
        <Route path="/carrito"      element={<CarritoPage />} />
        <Route path="/checkout"     element={<CheckoutPage />} />
      </Routes>
    </CartProvider>
  )
}
