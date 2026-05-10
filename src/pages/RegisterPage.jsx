import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'

// ── shared styles ───────────────────────────────────────────────────
const INPUT    = 'w-full bg-white/[0.06] border border-white/10 focus:border-orange-500/60 focus:outline-none rounded-xl px-4 py-2.5 text-sm text-white placeholder-white/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed'
const INPUT_RO = 'w-full bg-white/[0.03] border border-white/5 rounded-xl px-4 py-2.5 text-sm text-white/40 cursor-not-allowed'
const LABEL    = 'block text-xs text-white/50 mb-1.5'
const SECTION  = 'text-[11px] font-semibold text-white/35 uppercase tracking-widest pt-2'

function Field({ id, label, type = 'text', name, value, onChange, placeholder, autoComplete, readOnly = false }) {
  return (
    <div>
      <label htmlFor={id} className={LABEL}>
        {label}
        {readOnly && <span className="ml-1 text-[10px] text-white/25 normal-case tracking-normal">🔒 bloqueado</span>}
      </label>
      <input
        id={id} name={name} type={type}
        autoComplete={autoComplete}
        value={value} onChange={readOnly ? undefined : onChange}
        readOnly={readOnly}
        placeholder={placeholder}
        className={readOnly ? INPUT_RO : INPUT}
      />
    </div>
  )
}

function ErrorBox({ msg }) {
  return msg ? (
    <p role="alert" className="text-xs text-red-400 bg-red-900/20 border border-red-800/30 rounded-lg px-3 py-2">
      {msg}
    </p>
  ) : null
}

// ── Tab: Cliente ────────────────────────────────────────────────────
function TabCliente({ onSuccess }) {
  const [form, setForm] = useState({
    first_name: '', last_name: '', username: '', email: '',
    telefono: '', password: '', password2: '',
  })
  const [error, setError]   = useState(null)
  const [loading, setLoading] = useState(false)
  const set = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    if (form.password !== form.password2) { setError('Las contraseñas no coinciden.'); return }
    setLoading(true)
    try {
      const { data } = await api.post('usuarios/register/cliente/', form)
      onSuccess(data.tokens)
    } catch (err) {
      const d = err?.response?.data
      setError(d && typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Error al registrarse.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-3 mt-4">
      <div className="grid grid-cols-2 gap-3">
        <Field id="fn" label="Nombre"   name="first_name" value={form.first_name} onChange={set} placeholder="Juan" />
        <Field id="ln" label="Apellido" name="last_name"  value={form.last_name}  onChange={set} placeholder="Pérez" />
      </div>
      <Field id="un"  label="Usuario"              name="username"  value={form.username}  onChange={set} placeholder="juanperez" autoComplete="username" />
      <Field id="em"  label="Email"                name="email"     type="email" value={form.email} onChange={set} placeholder="juan@email.com" autoComplete="email" />
      <Field id="te"  label="Teléfono (opcional)"  name="telefono"  value={form.telefono}  onChange={set} placeholder="+56912345678" />
      <Field id="pw"  label="Contraseña"           name="password"  type="password" value={form.password}  onChange={set} placeholder="••••••••" autoComplete="new-password" />
      <Field id="pw2" label="Repetir contraseña"   name="password2" type="password" value={form.password2} onChange={set} placeholder="••••••••" autoComplete="new-password" />
      <ErrorBox msg={error} />
      <button type="submit" disabled={loading}
        className="w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all">
        {loading ? 'Registrando…' : 'Crear cuenta'}
      </button>
    </form>
  )
}

// ── Tab: Vendedor ───────────────────────────────────────────────────
function TabVendedor({ onSuccess }) {
  const [form, setForm] = useState({
    first_name: '', last_name: '', username: '', email: '',
    password: '', password2: '',
    telefono_vendedor: '', whatsapp: '',
    rut: '', razon_social: '', giro: '', direccion_fiscal: '',
    calle: '', numero: '', comuna: '', ciudad: '', region: '',
  })
  const [error, setError]   = useState(null)
  const [loading, setLoading] = useState(false)
  const set = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    if (form.password !== form.password2) { setError('Las contraseñas no coinciden.'); return }
    setLoading(true)
    try {
      const { data } = await api.post('usuarios/register/vendedor/', form)
      // Pass tokens + rut to parent so the next step can show RUT locked
      onSuccess(data.tokens, form.rut)
    } catch (err) {
      const d = err?.response?.data
      setError(d && typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Error al registrarse.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-3 mt-4">
      <p className={SECTION}>Cuenta</p>
      <div className="grid grid-cols-2 gap-3">
        <Field id="vfn" label="Nombre"   name="first_name" value={form.first_name} onChange={set} placeholder="Juan" />
        <Field id="vln" label="Apellido" name="last_name"  value={form.last_name}  onChange={set} placeholder="Pérez" />
      </div>
      <Field id="vun"  label="Usuario"            name="username"  value={form.username}  onChange={set} placeholder="juanperez" autoComplete="username" />
      <Field id="vem"  label="Email"              name="email"     type="email" value={form.email} onChange={set} placeholder="juan@email.com" />
      <Field id="vpw"  label="Contraseña"         name="password"  type="password" value={form.password}  onChange={set} placeholder="••••••••" autoComplete="new-password" />
      <Field id="vpw2" label="Repetir contraseña" name="password2" type="password" value={form.password2} onChange={set} placeholder="••••••••" autoComplete="new-password" />

      <p className={SECTION}>Negocio</p>
      <Field id="vwa"  label="WhatsApp (+56912345678)" name="whatsapp"          value={form.whatsapp}          onChange={set} placeholder="+56912345678" />
      <Field id="vtel" label="Teléfono (opcional)"     name="telefono_vendedor" value={form.telefono_vendedor} onChange={set} placeholder="+56222345678" />
      <Field id="vrut" label="RUT"                     name="rut"               value={form.rut}               onChange={set} placeholder="12345678-9" />
      <Field id="vrs"  label="Razón social"            name="razon_social"      value={form.razon_social}      onChange={set} placeholder="Juan Pérez SpA" />
      <Field id="vgi"  label="Giro"                    name="giro"              value={form.giro}              onChange={set} placeholder="Elaboración y venta de alimentos" />
      <Field id="vdf"  label="Dirección fiscal"        name="direccion_fiscal"  value={form.direccion_fiscal}  onChange={set} placeholder="Av. Principal 123, Angol" />

      <p className={SECTION}>Dirección de la tienda</p>
      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <Field id="vca" label="Calle"  name="calle"  value={form.calle}  onChange={set} placeholder="Av. Principal" />
        </div>
        <Field id="vnu" label="Número" name="numero" value={form.numero} onChange={set} placeholder="123" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Field id="vco" label="Comuna" name="comuna" value={form.comuna} onChange={set} placeholder="Angol" />
        <Field id="vci" label="Ciudad" name="ciudad" value={form.ciudad} onChange={set} placeholder="Angol" />
      </div>
      <Field id="vre" label="Región" name="region" value={form.region} onChange={set} placeholder="La Araucanía" />

      <ErrorBox msg={error} />
      <button type="submit" disabled={loading}
        className="w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all">
        {loading ? 'Registrando…' : 'Crear cuenta de vendedor'}
      </button>
    </form>
  )
}

// ── Step 2: Crear Tienda ────────────────────────────────────────────
const TIPO_OPCIONES = [
  { value: 'COMIDA',    label: '🍕 Comida y Bebidas' },
  { value: 'RETAIL',   label: '🛍️ Tienda / Retail'  },
  { value: 'SERVICIOS',label: '🔧 Servicios'          },
  { value: 'OTRO',     label: '🏪 Otro'               },
]

function StepCrearTienda({ vendorRut, onSuccess }) {
  const [form, setForm] = useState({
    nombre: '', tipo_negocio: 'COMIDA', descripcion: '',
    direccion: '', horario_atencion: '',
    acepta_efectivo: true,
  })
  const [error, setError]   = useState(null)
  const [loading, setLoading] = useState(false)
  const set = (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [e.target.name]: val }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await api.post('tiendas/tiendas/', form)
      onSuccess()
    } catch (err) {
      const d = err?.response?.data
      if (d && typeof d === 'object') {
        const msgs = Object.values(d).flat().join(' ')
        setError(msgs)
      } else {
        setError('Error al crear la tienda. Intenta de nuevo.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-sm bg-white/[0.05] border border-white/10 rounded-2xl p-6">
      {/* Step indicator */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex items-center gap-2 text-white/25 text-xs">
          <span className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center text-[10px] font-bold">✓</span>
          Cuenta
        </div>
        <div className="flex-1 h-px bg-white/10" />
        <div className="flex items-center gap-2 text-orange-400 text-xs font-semibold">
          <span className="w-5 h-5 rounded-full bg-orange-500 flex items-center justify-center text-[10px] font-bold text-white">2</span>
          Tu tienda
        </div>
      </div>

      <h2 className="text-base font-bold mb-1">Crea tu tienda</h2>
      <p className="text-xs text-white/35 mb-5">Puedes editar estos datos más tarde desde tu panel.</p>

      <form onSubmit={handleSubmit} noValidate className="space-y-3">

        {/* RUT bloqueado */}
        <div>
          <label className={LABEL}>
            RUT del negocio
            <span className="ml-1 text-[10px] text-white/25 normal-case tracking-normal">🔒 bloqueado</span>
          </label>
          <div className={INPUT_RO}>{vendorRut}</div>
        </div>

        <Field
          id="tnombre" label="Nombre de la tienda *"
          name="nombre" value={form.nombre} onChange={set}
          placeholder="Ej: Pizzería Don Pedro"
        />

        {/* Tipo negocio */}
        <div>
          <label htmlFor="ttipo" className={LABEL}>Tipo de negocio</label>
          <select
            id="ttipo" name="tipo_negocio" value={form.tipo_negocio} onChange={set}
            className={INPUT + ' appearance-none'}
          >
            {TIPO_OPCIONES.map((o) => (
              <option key={o.value} value={o.value} className="bg-slate-900">{o.label}</option>
            ))}
          </select>
        </div>

        <Field
          id="tdir" label="Dirección de la tienda *"
          name="direccion" value={form.direccion} onChange={set}
          placeholder="Ej: Av. Caupolican 123, Angol"
        />

        <Field
          id="tdesc" label="Descripción (opcional)"
          name="descripcion" value={form.descripcion} onChange={set}
          placeholder="Breve descripción de tu negocio"
        />

        <Field
          id="thor" label="Horario de atención (opcional)"
          name="horario_atencion" value={form.horario_atencion} onChange={set}
          placeholder="Ej: Lun–Vie 11:00–22:00"
        />

        {/* Método de pago */}
        <div className="flex items-center gap-2 pt-1">
          <input
            type="checkbox" id="tefectivo" name="acepta_efectivo"
            checked={form.acepta_efectivo} onChange={set}
            className="w-4 h-4 accent-orange-500"
          />
          <label htmlFor="tefectivo" className="text-sm text-white/70">Acepta efectivo</label>
        </div>

        <ErrorBox msg={error} />

        <button type="submit" disabled={loading}
          className="w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all mt-1">
          {loading ? 'Creando tienda…' : 'Crear tienda y entrar al panel →'}
        </button>
      </form>
    </div>
  )
}

// ── Page ────────────────────────────────────────────────────────────
const TABS = [
  { id: 'cliente',  label: '🛒 Cliente'  },
  { id: 'vendedor', label: '🏪 Vendedor' },
]

export default function RegisterPage() {
  const navigate = useNavigate()
  const { loadUser } = useAuth()
  const { mergeGuestCart, fetchCart } = useCart()

  const [tab,       setTab]       = useState('cliente')
  // 'registro' | 'crear-tienda' — only for vendor flow
  const [phase,     setPhase]     = useState('registro')
  const [vendorRut, setVendorRut] = useState('')

  // Called after cliente registration
  const handleClienteSuccess = async (tokens) => {
    localStorage.setItem('access_token',  tokens.access)
    localStorage.setItem('refresh_token', tokens.refresh)
    await loadUser()
    await mergeGuestCart()
    await fetchCart()
    navigate('/')
  }

  // Called after vendedor registration — move to step 2
  const handleVendedorSuccess = async (tokens, rut) => {
    localStorage.setItem('access_token',  tokens.access)
    localStorage.setItem('refresh_token', tokens.refresh)
    await loadUser()
    setVendorRut(rut)
    setPhase('crear-tienda')
    // Scroll to top so the new form is visible
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Called after tienda created
  const handleTiendaCreada = () => {
    navigate('/vendedor/panel?bienvenida=1')
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-start pt-12 pb-16 px-4">

      <div className="mb-6 text-center">
        <span className="text-4xl">🛒</span>
        <h1 className="text-2xl font-black mt-3 leading-none">MultiTienda</h1>
        <p className="text-[11px] font-semibold text-white/40 tracking-[0.25em] mt-1">ANGOL</p>
      </div>

      {/* ── Phase 2: crear tienda (solo vendedor) ── */}
      {phase === 'crear-tienda' && (
        <StepCrearTienda vendorRut={vendorRut} onSuccess={handleTiendaCreada} />
      )}

      {/* ── Phase 1: registro ── */}
      {phase === 'registro' && (
        <div className="w-full max-w-sm bg-white/[0.05] border border-white/10 rounded-2xl p-6">
          <h2 className="text-base font-bold mb-4">Crear cuenta</h2>

          {/* Tabs */}
          <div className="flex gap-1 bg-white/5 rounded-xl p-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={[
                  'flex-1 text-xs font-semibold py-2 rounded-lg transition-all duration-200',
                  tab === t.id
                    ? 'bg-orange-500 text-white shadow-sm'
                    : 'text-white/40 hover:text-white/70',
                ].join(' ')}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === 'cliente'  && <TabCliente  onSuccess={handleClienteSuccess} />}
          {tab === 'vendedor' && <TabVendedor onSuccess={handleVendedorSuccess} />}

          <p className="text-xs text-white/30 text-center mt-5">
            ¿Ya tienes cuenta?{' '}
            <Link to="/login" className="text-orange-400 hover:text-orange-300 transition-colors">
              Inicia sesión
            </Link>
          </p>
        </div>
      )}

      <Link to="/" className="mt-6 text-xs text-white/30 hover:text-white/60 transition-colors">
        ← Volver al inicio
      </Link>
    </div>
  )
}
