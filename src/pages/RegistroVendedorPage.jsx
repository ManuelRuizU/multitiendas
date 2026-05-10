import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import Modal from '../components/Modal'

// ── Shared styles ───────────────────────────────────────────────────
const INPUT    = 'w-full bg-white/[0.06] border border-white/10 focus:border-orange-500/60 focus:outline-none rounded-xl px-4 py-2.5 text-sm text-white placeholder-white/20 transition-colors'
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
        id={id} name={name} type={type} autoComplete={autoComplete}
        value={value} onChange={readOnly ? undefined : onChange}
        readOnly={readOnly} placeholder={placeholder}
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

// ── Tipo negocio options ────────────────────────────────────────────
const TIPO_OPCIONES = [
  { value: 'COMIDA',    label: '🍕 Comida y Bebidas' },
  { value: 'RETAIL',   label: '🛍️ Tienda / Retail'  },
  { value: 'SERVICIOS',label: '🔧 Servicios'          },
  { value: 'OTRO',     label: '🏪 Otro'               },
]

// ── Step 1: Registro ────────────────────────────────────────────────
function StepRegistro({ onSuccess }) {
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
      onSuccess(data.tokens, form.rut)
    } catch (err) {
      const d = err?.response?.data
      setError(d && typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Error al registrarse.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-3">
      <p className={SECTION}>Cuenta</p>
      <div className="grid grid-cols-2 gap-3">
        <Field id="rfn" label="Nombre"   name="first_name" value={form.first_name} onChange={set} placeholder="Juan" />
        <Field id="rln" label="Apellido" name="last_name"  value={form.last_name}  onChange={set} placeholder="Pérez" />
      </div>
      <Field id="run"  label="Usuario"            name="username"  value={form.username}  onChange={set} placeholder="juanperez" autoComplete="username" />
      <Field id="rem"  label="Email"              name="email"     type="email" value={form.email} onChange={set} placeholder="juan@email.com" />
      <Field id="rpw"  label="Contraseña"         name="password"  type="password" value={form.password}  onChange={set} placeholder="••••••••" autoComplete="new-password" />
      <Field id="rpw2" label="Repetir contraseña" name="password2" type="password" value={form.password2} onChange={set} placeholder="••••••••" autoComplete="new-password" />

      <p className={SECTION}>Negocio</p>
      <Field id="rwa"  label="WhatsApp (+56912345678)" name="whatsapp"          value={form.whatsapp}          onChange={set} placeholder="+56912345678" />
      <Field id="rtel" label="Teléfono (opcional)"     name="telefono_vendedor" value={form.telefono_vendedor} onChange={set} placeholder="+56222345678" />
      <Field id="rrut" label="RUT"                     name="rut"               value={form.rut}               onChange={set} placeholder="12345678-9" />
      <Field id="rrs"  label="Razón social"            name="razon_social"      value={form.razon_social}      onChange={set} placeholder="Juan Pérez SpA" />
      <Field id="rgi"  label="Giro"                    name="giro"              value={form.giro}              onChange={set} placeholder="Elaboración y venta de alimentos" />
      <Field id="rdf"  label="Dirección fiscal"        name="direccion_fiscal"  value={form.direccion_fiscal}  onChange={set} placeholder="Av. Principal 123, Angol" />

      <p className={SECTION}>Dirección de la tienda</p>
      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <Field id="rca" label="Calle"  name="calle"  value={form.calle}  onChange={set} placeholder="Av. Principal" />
        </div>
        <Field id="rnu" label="Número" name="numero" value={form.numero} onChange={set} placeholder="123" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Field id="rco" label="Comuna" name="comuna" value={form.comuna} onChange={set} placeholder="Angol" />
        <Field id="rci" label="Ciudad" name="ciudad" value={form.ciudad} onChange={set} placeholder="Angol" />
      </div>
      <Field id="rre" label="Región" name="region" value={form.region} onChange={set} placeholder="La Araucanía" />

      <ErrorBox msg={error} />
      <button type="submit" disabled={loading}
        className="w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all mt-1">
        {loading ? 'Registrando cuenta…' : 'Continuar →'}
      </button>
    </form>
  )
}

// ── Step 2: Crear Tienda ────────────────────────────────────────────
function StepCrearTienda({ vendorRut, onSuccess }) {
  const [form, setForm] = useState({
    nombre: '', tipo_negocio: 'COMIDA', descripcion: '',
    direccion: '', horario_atencion: '', acepta_efectivo: true,
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
      setError(d && typeof d === 'object' ? Object.values(d).flat().join(' ') : 'Error al crear la tienda.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-3">
      {/* RUT locked */}
      <div>
        <label className={LABEL}>
          RUT del negocio
          <span className="ml-1 text-[10px] text-white/25 normal-case tracking-normal">🔒 bloqueado</span>
        </label>
        <div className={INPUT_RO}>{vendorRut}</div>
      </div>

      <Field id="tnombre" label="Nombre de la tienda *" name="nombre" value={form.nombre} onChange={set} placeholder="Ej: Pizzería Don Pedro" />

      <div>
        <label htmlFor="ttipo" className={LABEL}>Tipo de negocio</label>
        <select id="ttipo" name="tipo_negocio" value={form.tipo_negocio} onChange={set}
          className={INPUT + ' appearance-none'}>
          {TIPO_OPCIONES.map((o) => (
            <option key={o.value} value={o.value} className="bg-slate-900">{o.label}</option>
          ))}
        </select>
      </div>

      <Field id="tdir"  label="Dirección *"             name="direccion"        value={form.direccion}        onChange={set} placeholder="Av. Caupolican 123, Angol" />
      <Field id="tdesc" label="Descripción (opcional)"  name="descripcion"      value={form.descripcion}      onChange={set} placeholder="Breve descripción de tu negocio" />
      <Field id="thor"  label="Horario (opcional)"      name="horario_atencion" value={form.horario_atencion} onChange={set} placeholder="Lun–Vie 11:00–22:00" />

      <div className="flex items-center gap-2 pt-1">
        <input type="checkbox" id="tef" name="acepta_efectivo" checked={form.acepta_efectivo} onChange={set}
          className="w-4 h-4 accent-orange-500" />
        <label htmlFor="tef" className="text-sm text-white/70">Acepta efectivo</label>
      </div>

      <ErrorBox msg={error} />
      <button type="submit" disabled={loading}
        className="w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all mt-1">
        {loading ? 'Creando tienda…' : 'Crear tienda →'}
      </button>
    </form>
  )
}

// ── Page ────────────────────────────────────────────────────────────
export default function RegistroVendedorPage() {
  const navigate  = useNavigate()
  const { loadUser } = useAuth()
  const { mergeGuestCart } = useCart()

  const [phase,      setPhase]      = useState('registro') // 'registro' | 'crear-tienda'
  const [vendorRut,  setVendorRut]  = useState('')
  const [showModal,  setShowModal]  = useState(false)      // success modal

  // Step 1 done
  const handleRegistroSuccess = async (tokens, rut) => {
    localStorage.setItem('access_token',  tokens.access)
    localStorage.setItem('refresh_token', tokens.refresh)
    await loadUser()
    setVendorRut(rut)
    setPhase('crear-tienda')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Step 2 done → show success modal
  const handleTiendaCreada = () => {
    setShowModal(true)
  }

  // Modal confirmed → go to panel
  const handleGoToPanel = () => {
    setShowModal(false)
    mergeGuestCart().catch(() => {})
    navigate('/vendedor/panel?bienvenida=1')
  }

  const stepLabel = phase === 'registro' ? 'Paso 1 de 2 — Cuenta' : 'Paso 2 de 2 — Tu tienda'

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-start pt-10 pb-16 px-4">

      {/* Brand */}
      <div className="mb-6 text-center">
        <span className="text-4xl">🏪</span>
        <h1 className="text-2xl font-black mt-3 leading-none">Registro Vendedor</h1>
        <p className="text-[11px] font-semibold text-white/40 tracking-[0.2em] mt-1">MULTTIENDA ANGOL</p>
      </div>

      {/* Step indicator */}
      <div className="w-full max-w-sm mb-4">
        <div className="flex items-center gap-2 mb-2">
          <Step n={1} active={phase === 'registro'}   done={phase === 'crear-tienda'} label="Cuenta" />
          <div className="flex-1 h-px bg-white/10" />
          <Step n={2} active={phase === 'crear-tienda'} done={false} label="Tienda" />
        </div>
        <p className="text-xs text-white/30 text-center">{stepLabel}</p>
      </div>

      {/* Form card */}
      <div className="w-full max-w-sm bg-white/[0.05] border border-white/10 rounded-2xl p-6">
        {phase === 'registro' && (
          <StepRegistro onSuccess={handleRegistroSuccess} />
        )}
        {phase === 'crear-tienda' && (
          <StepCrearTienda vendorRut={vendorRut} onSuccess={handleTiendaCreada} />
        )}
      </div>

      <Link to="/login" className="mt-6 text-xs text-white/30 hover:text-white/60 transition-colors">
        ¿Ya tienes cuenta? Inicia sesión
      </Link>

      {/* ── Success Modal ── */}
      <Modal open={showModal} onClose={handleGoToPanel}>
        <div className="text-center space-y-4">
          <div className="text-5xl animate-bounce">🎉</div>
          <div>
            <h3 className="text-lg font-black text-white">¡Tu tienda está lista!</h3>
            <p className="text-sm text-white/50 mt-1.5 leading-relaxed">
              Cuenta creada y tienda activa. Ahora agrega productos y empieza a vender.
            </p>
          </div>
          <div className="space-y-2 pt-1">
            <button
              onClick={handleGoToPanel}
              className="w-full bg-orange-500 hover:bg-orange-400 active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all"
            >
              Ir al panel de vendedor →
            </button>
            <button
              onClick={() => navigate('/')}
              className="w-full text-xs text-white/40 hover:text-white/70 transition-colors py-1.5"
            >
              Ir al inicio
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

function Step({ n, active, done, label }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={[
        'w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold transition-colors',
        done   ? 'bg-green-500/80 text-white'     : '',
        active ? 'bg-orange-500 text-white'       : '',
        !done && !active ? 'bg-white/10 text-white/30' : '',
      ].join(' ')}>
        {done ? '✓' : n}
      </div>
      <span className={`text-xs ${active ? 'text-white font-semibold' : done ? 'text-white/40' : 'text-white/20'}`}>
        {label}
      </span>
    </div>
  )
}
