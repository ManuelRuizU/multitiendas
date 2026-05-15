import { useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import Modal from './Modal'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'

// Pages where the modal must not appear
const HIDDEN_ON = ['/registro-vendedor', '/checkout', '/login', '/registro']

const INPUT = 'w-full bg-white/[0.06] border border-white/10 focus:border-orange-500/60 focus:outline-none rounded-xl px-4 py-2.5 text-sm text-white placeholder-white/20 transition-colors'
const LABEL = 'block text-xs text-white/50 mb-1.5'
const BTN   = 'w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-sm py-3 rounded-xl transition-all active:scale-[0.98]'

// ── Shared: locked email row ────────────────────────────────────────
function EmailLocked({ email, onBack }) {
  return (
    <div className="flex items-center gap-2 bg-white/[0.04] border border-white/8 rounded-xl px-4 py-2.5">
      <span className="text-sm text-white/70 flex-1 truncate">{email}</span>
      <button type="button" onClick={onBack}
        className="text-xs text-orange-400 hover:text-orange-300 transition-colors shrink-0">
        Cambiar
      </button>
    </div>
  )
}

// ── Shared: error pill ─────────────────────────────────────────────
function Err({ msg }) {
  if (!msg) return null
  return (
    <p role="alert" className="text-xs text-red-400 bg-red-900/20 border border-red-800/30 rounded-lg px-3 py-2">
      {msg}
    </p>
  )
}

// ── Shared: password field with show/hide ──────────────────────────
function PasswordInput({ name, value, onChange, placeholder = '••••••••', autoComplete = 'current-password' }) {
  const [show, setShow] = useState(false)
  return (
    <div className="relative">
      <input
        name={name}
        type={show ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
        placeholder={placeholder}
        className={INPUT}
      />
      <button
        type="button"
        onClick={() => setShow(v => !v)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 text-xs transition-colors select-none"
      >
        {show ? 'Ocultar' : 'Ver'}
      </button>
    </div>
  )
}

// ── Step 1: Email — determina si es login o registro ───────────────
function EmailStep({ onExists, onNew }) {
  const [email,    setEmail]    = useState('')
  const [checking, setChecking] = useState(false)
  const [error,    setError]    = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.includes('@')) return
    setChecking(true)
    setError(null)
    try {
      const { data } = await api.post('usuarios/check-email/', { email })
      data.exists ? onExists(email, data.username) : onNew(email)
    } catch {
      // Si el endpoint falla asumimos usuario nuevo
      onNew(email)
    } finally {
      setChecking(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-3">
      <div>
        <label className={LABEL}>Email</label>
        <input
          type="email" value={email}
          onChange={(e) => { setError(null); setEmail(e.target.value) }}
          autoComplete="email" placeholder="tu@email.com"
          className={INPUT}
        />
      </div>
      <Err msg={error} />
      <button type="submit" disabled={checking || !email.includes('@')} className={BTN}>
        {checking ? 'Verificando…' : 'Continuar →'}
      </button>
    </form>
  )
}

// ── Step 2a: Login — email ya existe ──────────────────────────────
function LoginStep({ email, username, onSuccess, onBack }) {
  const [password, setPassword] = useState('')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { data } = await api.post('token/', { username, password })
      await onSuccess({ access: data.access, refresh: data.refresh }, data.user)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Contraseña incorrecta')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-3">
      <EmailLocked email={email} onBack={onBack} />
      <div>
        <label className={LABEL}>Contraseña</label>
        <PasswordInput
          name="password"
          value={password}
          onChange={(e) => { setError(null); setPassword(e.target.value) }}
          autoComplete="current-password"
        />
      </div>
      <Err msg={error} />
      <button type="submit" disabled={loading || !password} className={BTN}>
        {loading ? 'Ingresando…' : 'Ingresar →'}
      </button>
    </form>
  )
}

// ── Step 2b: Register — email nuevo ───────────────────────────────
function RegisterStep({ email, onSuccess, onBack }) {
  const [form, setForm] = useState({
    first_name: '', last_name: '', apellido_materno: '',
    password: '', password2: '', telefono: '',
  })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const set = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  // Acepta solo dígitos, máx 9
  const handleTelefono = (e) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 9)
    setForm((f) => ({ ...f, telefono: raw }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    // Validaciones
    if (!form.first_name.trim()) {
      setError('El nombre es obligatorio.')
      return
    }
    if (!form.last_name.trim()) {
      setError('El apellido paterno es obligatorio.')
      return
    }
    if (!form.apellido_materno.trim()) {
      setError('El apellido materno es obligatorio.')
      return
    }
    if (form.telefono.length < 9 || !form.telefono.startsWith('9')) {
      setError('Ingresa un celular chileno válido (+56 9XXXXXXXX).')
      return
    }
    if (form.password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.')
      return
    }
    if (form.password !== form.password2) {
      setError('Las contraseñas no coinciden.')
      return
    }

    setLoading(true)
    try {
      const { data } = await api.post('usuarios/register/cliente/', {
        ...form,
        email,
        telefono: `+56${form.telefono}`,
      })
      await onSuccess(data.tokens)
    } catch (err) {
      const d = err?.response?.data
      setError(
        d && typeof d === 'object'
          ? Object.values(d).flat().join(' ')
          : 'Error al registrarse.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-3">
      <EmailLocked email={email} onBack={onBack} />

      {/* Nombre + Apellido paterno */}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className={LABEL}>Nombre</label>
          <input name="first_name" value={form.first_name} onChange={set}
            placeholder="Juan" className={INPUT} />
        </div>
        <div>
          <label className={LABEL}>Apellido paterno</label>
          <input name="last_name" value={form.last_name} onChange={set}
            placeholder="Pérez" className={INPUT} />
        </div>
      </div>

      {/* Apellido materno */}
      <div>
        <label className={LABEL}>Apellido materno</label>
        <input name="apellido_materno" value={form.apellido_materno} onChange={set}
          placeholder="García" className={INPUT} />
      </div>

      {/* Teléfono con prefijo +56 fijo */}
      <div>
        <label className={LABEL}>Teléfono celular</label>
        <div className="flex bg-white/[0.06] border border-white/10 focus-within:border-orange-500/60 rounded-xl overflow-hidden transition-colors">
          <span className="flex items-center pl-4 pr-3 text-sm text-white/40 select-none shrink-0 border-r border-white/10">
            +56
          </span>
          <input
            type="tel"
            value={form.telefono}
            onChange={handleTelefono}
            placeholder="9 1234 5678"
            maxLength={9}
            className="flex-1 bg-transparent focus:outline-none px-3 py-2.5 text-sm text-white placeholder-white/20"
          />
        </div>
        <p className="text-[10px] text-white/30 mt-1 pl-1">
          Necesario para coordinar tu pedido
        </p>
      </div>

      {/* Contraseña */}
      <div>
        <label className={LABEL}>Contraseña</label>
        <PasswordInput
          name="password"
          value={form.password}
          onChange={set}
          autoComplete="new-password"
        />
        <p className="text-[10px] text-white/30 mt-1 pl-1">Mínimo 8 caracteres</p>
      </div>

      {/* Repetir contraseña */}
      <div>
        <label className={LABEL}>Repetir contraseña</label>
        <PasswordInput
          name="password2"
          value={form.password2}
          onChange={set}
          autoComplete="new-password"
        />
      </div>

      <Err msg={error} />

      <button type="submit" disabled={loading} className={BTN}>
        {loading ? 'Creando cuenta…' : 'Crear cuenta →'}
      </button>
    </form>
  )
}

// ── Títulos por paso ───────────────────────────────────────────────
const TITLE = {
  email:    'Ingresa o regístrate',
  login:    '¡Bienvenido de vuelta!',
  register: 'Crea tu cuenta',
}

// ── Main component ─────────────────────────────────────────────────
export default function AuthModal() {
  const { pathname }                                         = useLocation()
  const { isAuthModalOpen, closeAuthModal, login, loadUser } = useAuth()
  const { mergeGuestCart, fetchCart }                        = useCart()

  const [step,     setStep]     = useState('email')
  const [email,    setEmail]    = useState('')
  const [username, setUsername] = useState('')

  if (HIDDEN_ON.includes(pathname)) return null

  const handleEmailExists = (em, uname) => {
    setEmail(em)
    setUsername(uname)
    setStep('login')
  }

  const handleEmailNew = (em) => {
    setEmail(em)
    setStep('register')
  }

  const handleLoginSuccess = async (tokens, userData) => {
    login(tokens, userData)
    await mergeGuestCart().catch(() => {})
    await fetchCart()
    closeAuthModal()
  }

  const handleRegisterSuccess = async (tokens) => {
    localStorage.setItem('access_token',  tokens.access)
    localStorage.setItem('refresh_token', tokens.refresh)
    await loadUser()
    await mergeGuestCart().catch(() => {})
    await fetchCart()
    closeAuthModal()
  }

  const handleClose = () => {
    closeAuthModal()
    setTimeout(() => { setStep('email'); setEmail(''); setUsername('') }, 300)
  }

  return (
    <Modal open={isAuthModalOpen} onClose={handleClose} title={TITLE[step]}>

      {step === 'email' && (
        <EmailStep onExists={handleEmailExists} onNew={handleEmailNew} />
      )}
      {step === 'login' && (
        <LoginStep
          email={email} username={username}
          onSuccess={handleLoginSuccess}
          onBack={() => setStep('email')}
        />
      )}
      {step === 'register' && (
        <RegisterStep
          email={email}
          onSuccess={handleRegisterSuccess}
          onBack={() => setStep('email')}
        />
      )}

      {/* Footer */}
      <div className="mt-5 pt-4 border-t border-white/10 space-y-3">
        <button
          onClick={handleClose}
          className="w-full text-xs text-white/30 hover:text-white/60 transition-colors py-1.5"
        >
          Continuar sin registrarse
        </button>

        {pathname !== '/registro-vendedor' && (
          <p className="text-center text-xs text-white/20 leading-relaxed">
            ¿Tienes un negocio?{' '}
            <Link
              to="/registro-vendedor"
              onClick={handleClose}
              className="text-orange-400 hover:text-orange-300 transition-colors font-medium"
            >
              Crea tu tienda aquí →
            </Link>
          </p>
        )}
      </div>

    </Modal>
  )
}