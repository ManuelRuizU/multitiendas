import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { CartProvider } from './context/CartContext'
import CartFAB from './components/CartFAB'
import CartDrawer from './components/CartDrawer'
import AuthModal from './components/AuthModal'
import Home from './pages/Home'
import TiendasPage from './pages/TiendasPage'
import TiendaPage from './pages/TiendaPage'
import CarritoPage from './pages/CarritoPage'
import CheckoutPage from './pages/CheckoutPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import RegistroVendedorPage from './pages/RegistroVendedorPage'
import PerfilPage from './pages/PerfilPage'
import VendedorPanelPage from './pages/VendedorPanelPage'
import VendedorPedidosPage from './pages/VendedorPedidosPage'
import MisPedidosPage from './pages/MisPedidosPage'

export default function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <CartFAB />
        <CartDrawer />
        <AuthModal />
        <Routes>
          <Route path="/"                      element={<Home />} />
          <Route path="/tiendas"               element={<TiendasPage />} />
          <Route path="/tienda/:slug"          element={<TiendaPage />} />
          <Route path="/carrito"               element={<CarritoPage />} />
          <Route path="/checkout"              element={<CheckoutPage />} />
          <Route path="/login"                 element={<LoginPage />} />
          <Route path="/registro"              element={<RegisterPage />} />
          <Route path="/registro-vendedor"     element={<RegistroVendedorPage />} />
          <Route path="/perfil"                element={<PerfilPage />} />
          <Route path="/vendedor/panel"        element={<VendedorPanelPage />} />
          <Route path="/vendedor/pedidos"      element={<VendedorPedidosPage />} />
          <Route path="/mis-pedidos"           element={<MisPedidosPage />} />
        </Routes>
      </CartProvider>
    </AuthProvider>
  )
}
