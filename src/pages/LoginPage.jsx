import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { mergeGuestCart, fetchCart } = useCart()

  const [form,    setForm]    = useState({ username: '', password: '' })
  const [error,   setError]   = useState(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { data } = await api.post('token/', {
        username: form.username,
        password: form.password,
      })
      login({ access: data.access, refresh: data.refresh }, data.user)
      await mergeGuestCart()
      await fetchCart()
      navigate('/')
    } catch (err) {
      const detail = err?.response?.data?.detail
      setError(detail || 'Usuario o contraseña incorrectos')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center px-4">

      <div className="mb-8 text-center">
        <span className="text-4xl">🛒</span>
        <h1 className="text-2xl font-black mt-3 leading-none">MultiTienda</h1>
        <p className="text-[11px] font-semibold text-white/40 tracking-[0.25em] mt-1">ANGOL</p>
      </div>

      <div className="w-full max-w-sm bg-white/[0.05] border border-white/10 rounded-2xl p-6">
        <h2 className="text-base font-bold mb-5">Iniciar sesión</h2>

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-xs text-white/50 mb-1.5">
              Usuario
            </label>
            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              required
              value={form.username}
              onChange={handleChange}
              placeholder="tu_usuario"
              className="w-full bg-white/[0.06] border border-white/10 focus:border-orange-500/60 focus:outline-none rounded-xl px-4 py-2.5 text-sm text-white placeholder-white/20 transition-colors"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-xs text-white/50 mb-1.5">
              Contraseña
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={form.password}
              onChange={handleChange}
              placeholder="••••••••"
              className="w-full bg-white/[0.06] border border-white/10 focus:border-orange-500/60 focus:outline-none rounded-xl px-4 py-2.5 text-sm text-white placeholder-white/20 transition-colors"
            />
          </div>

          {error && (
            <p role="alert" className="text-xs text-red-400 bg-red-900/20 border border-red-800/30 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all mt-1"
          >
            {loading ? 'Ingresando…' : 'Ingresar'}
          </button>
        </form>

        <p className="text-xs text-white/30 text-center mt-5">
          ¿No tienes cuenta?{' '}
          <Link to="/registro" className="text-orange-400 hover:text-orange-300 transition-colors">
            Regístrate
          </Link>
        </p>
      </div>

      <Link to="/" className="mt-6 text-xs text-white/30 hover:text-white/60 transition-colors">
        ← Volver al inicio
      </Link>
    </div>
  )
}
