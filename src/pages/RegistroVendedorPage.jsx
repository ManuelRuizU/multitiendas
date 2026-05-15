
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

function Field({ id, label, type = 'text', name, value, onChange, placeholder, autoComplete, readOnly = false, required = false }) {
  return (
    <div>
      <label htmlFor={id} className={LABEL}>
        {label}
        {required && <span className="ml-1 text-orange-400/60">*</span>}
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

// ── Password field con Show/Hide ────────────────────────────────────
function PasswordField({ id, label, name, value, onChange, autoComplete = 'new-password' }) {
  const [show, setShow] = useState(false)
  return (
    <div>
      <label htmlFor={id} className={LABEL}>
        {label} <span className="text-orange-400/60">*</span>
      </label>
      <div className="relative">
        <input
          id={id} name={name} type={show ? 'text' : 'password'}
          value={value} onChange={onChange}
          autoComplete={autoComplete} placeholder="••••••••"
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
    </div>
  )
}

// ── Teléfono con prefijo +56 ────────────────────────────────────────
function TelefonoField({ id, label, value, onChange, required = false }) {
  const handleChange = (e) => {
    const raw = e.target.value.replace(/\D/g, '').slice(0, 9)
    onChange(raw)
  }
  return (
    <div>
      <label htmlFor={id} className={LABEL}>
        {label}
        {required && <span className="ml-1 text-orange-400/60">*</span>}
      </label>
      <div className="flex bg-white/[0.06] border border-white/10 focus-within:border-orange-500/60 rounded-xl overflow-hidden transition-colors">
        <span className="flex items-center pl-4 pr-3 text-sm text-white/40 select-none shrink-0 border-r border-white/10">
          +56
        </span>
        <input
          id={id}
          type="tel"
          value={value}
          onChange={handleChange}
          placeholder="9 1234 5678"
          maxLength={9}
          className="flex-1 bg-transparent focus:outline-none px-3 py-2.5 text-sm text-white placeholder-white/20"
        />
      </div>
      {required && (
        <p className="text-[10px] text-white/30 mt-1 pl-1">
          Necesario para coordinar pedidos con tus clientes
        </p>
      )}
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
    first_name: '', last_name: '', apellido_materno: '',
    email: '', password: '', password2: '',
    telefono_personal: '', // teléfono personal obligatorio
    whatsapp: '',          // whatsapp del negocio obligatorio
    rut: '', razon_social: '', giro: '', direccion_fiscal: '',
    calle: '', numero: '', comuna: 'Angol', ciudad: 'Angol', region: 'La Araucanía',
  })
  const [error,   setError]   = useState(null)
  const [loading, setLoading] = useState(false)

  const set = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    // Validaciones
    if (!form.first_name.trim()) { setError('El nombre es obligatorio.'); return }
    if (!form.last_name.trim())  { setError('El apellido paterno es obligatorio.'); return }
    if (!form.apellido_materno.trim()) { setError('El apellido materno es obligatorio.'); return }
    if (!form.email.includes('@')) { setError('Ingresa un email válido.'); return }
    if (form.password.length < 8) { setError('La contraseña debe tener al menos 8 caracteres.'); return }
    if (form.password !== form.password2) { setError('Las contraseñas no coinciden.'); return }
    if (!form.telefono_personal || form.telefono_personal.length < 9 || !form.telefono_personal.startsWith('9')) {
      setError('Ingresa un teléfono personal válido (+56 9XXXXXXXX).')
      return
    }
    if (!form.whatsapp) { setError('El WhatsApp del negocio es obligatorio.'); return }
    if (!form.rut.trim()) { setError('El RUT es obligatorio.'); return }
    if (!form.razon_social.trim()) { setError('La razón social es obligatoria.'); return }
    if (!form.giro.trim()) { setError('El giro es obligatorio.'); return }

    setLoading(true)
    try {
      const payload = {
        first_name: form.first_name,
        last_name: form.last_name,
        apellido_materno: form.apellido_materno,
        email: form.email,
        password: form.password,
        password2: form.password2,
        telefono: `+56${form.telefono_personal}`,
        whatsapp: form.whatsapp.startsWith('+56') ? form.whatsapp : `+56${form.whatsapp.replace(/\D/g, '')}`,
        rut: form.rut,
        razon_social: form.razon_social,
        giro: form.giro,
        direccion_fiscal: form.direccion_fiscal || `${form.calle} ${form.numero}, ${form.ciudad}`,
        calle: form.calle,
        numero: form.numero,
        comuna: form.comuna,
        ciudad: form.ciudad,
        region: form.region,
      }
      const { data } = await api.post('usuarios/register/vendedor/', payload)
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

      {/* ── Datos personales ── */}
      <p className={SECTION}>Datos personales</p>

      <div className="grid grid-cols-2 gap-3">
        <Field id="rfn" label="Nombre" name="first_name"
          value={form.first_name} onChange={set}
          placeholder="Juan" required />
        <Field id="rln" label="Apellido paterno" name="last_name"
          value={form.last_name} onChange={set}
          placeholder="Pérez" required />
      </div>

      <Field id="ram" label="Apellido materno" name="apellido_materno"
        value={form.apellido_materno} onChange={set}
        placeholder="García" required />

      <Field id="rem" label="Email" name="email" type="email"
        value={form.email} onChange={set}
        placeholder="juan@email.com" autoComplete="email" required />

      <PasswordField id="rpw" label="Contraseña" name="password"
        value={form.password} onChange={set} />
      <PasswordField id="rpw2" label="Repetir contraseña" name="password2"
        value={form.password2} onChange={set} />

      <TelefonoField
        id="rtel"
        label="Teléfono personal"
        value={form.telefono_personal}
        onChange={(val) => setForm(f => ({ ...f, telefono_personal: val }))}
        required
      />

      {/* ── Datos del negocio ── */}
      <p className={SECTION}>Datos del negocio</p>

      <div>
        <label className={LABEL}>
          WhatsApp del negocio <span className="text-orange-400/60">*</span>
        </label>
        <div className="flex bg-white/[0.06] border border-white/10 focus-within:border-orange-500/60 rounded-xl overflow-hidden transition-colors">
          <span className="flex items-center pl-4 pr-3 text-sm text-white/40 select-none shrink-0 border-r border-white/10">
            +56
          </span>
          <input
            type="tel"
            value={form.whatsapp.replace('+56', '')}
            onChange={(e) => {
              const raw = e.target.value.replace(/\D/g, '').slice(0, 9)
              setForm(f => ({ ...f, whatsapp: `+56${raw}` }))
            }}
            placeholder="9 1234 5678"
            maxLength={9}
            className="flex-1 bg-transparent focus:outline-none px-3 py-2.5 text-sm text-white placeholder-white/20"
          />
        </div>
        <p className="text-[10px] text-white/30 mt-1 pl-1">
          Número donde recibirás los pedidos de tus clientes
        </p>
      </div>

      <Field id="rrut" label="RUT" name="rut"
        value={form.rut} onChange={set}
        placeholder="12345678-9" required />
      <Field id="rrs" label="Razón social" name="razon_social"
        value={form.razon_social} onChange={set}
        placeholder="Juan Pérez SpA" required />
      <Field id="rgi" label="Giro" name="giro"
        value={form.giro} onChange={set}
        placeholder="Elaboración y venta de alimentos" required />
      <Field id="rdf" label="Dirección fiscal" name="direccion_fiscal"
        value={form.direccion_fiscal} onChange={set}
        placeholder="Av. Principal 123, Angol" />

      {/* ── Dirección de la tienda ── */}
      <p className={SECTION}>Dirección de la tienda</p>

      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <Field id="rca" label="Calle" name="calle"
            value={form.calle} onChange={set} placeholder="Av. Principal" required />
        </div>
        <Field id="rnu" label="Número" name="numero"
          value={form.numero} onChange={set} placeholder="123" required />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Field id="rco" label="Comuna" name="comuna"
          value={form.comuna} onChange={set} placeholder="Angol" />
        <Field id="rci" label="Ciudad" name="ciudad"
          value={form.ciudad} onChange={set} placeholder="Angol" />
      </div>
      <Field id="rre" label="Región" name="region"
        value={form.region} onChange={set} placeholder="La Araucanía" />

      <p className="text-[10px] text-white/25 pl-1">
        <span className="text-orange-400/60">*</span> Campos obligatorios
      </p>

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
  const [error,   setError]   = useState(null)
  const [loading, setLoading] = useState(false)

  const set = (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [e.target.name]: val }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    if (!form.nombre.trim()) { setError('El nombre de la tienda es obligatorio.'); return }
    if (!form.direccion.trim()) { setError('La dirección de la tienda es obligatoria.'); return }
    setLoading(true)
    try {
      await api.post('tiendas/', form)
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

      {/* RUT bloqueado */}
      <div>
        <label className={LABEL}>
          RUT del negocio
          <span className="ml-1 text-[10px] text-white/25 normal-case tracking-normal">🔒 bloqueado</span>
        </label>
        <div className={INPUT_RO}>{vendorRut}</div>
      </div>

      <Field id="tnombre" label="Nombre de la tienda" name="nombre"
        value={form.nombre} onChange={set}
        placeholder="Ej: Pizzería Don Pedro" required />

      <div>
        <label htmlFor="ttipo" className={LABEL}>Tipo de negocio</label>
        <select id="ttipo" name="tipo_negocio" value={form.tipo_negocio} onChange={set}
          className={INPUT + ' appearance-none'}>
          {TIPO_OPCIONES.map((o) => (
            <option key={o.value} value={o.value} className="bg-slate-900">{o.label}</option>
          ))}
        </select>
      </div>

      <Field id="tdir"  label="Dirección" name="direccion"
        value={form.direccion} onChange={set}
        placeholder="Av. Caupolican 123, Angol" required />
      <Field id="tdesc" label="Descripción (opcional)" name="descripcion"
        value={form.descripcion} onChange={set}
        placeholder="Breve descripción de tu negocio" />
      <Field id="thor"  label="Horario de atención (opcional)" name="horario_atencion"
        value={form.horario_atencion} onChange={set}
        placeholder="Lun–Vie 11:00–22:00" />

      <div className="flex items-center gap-2 pt-1">
        <input type="checkbox" id="tef" name="acepta_efectivo"
          checked={form.acepta_efectivo} onChange={set}
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
  const navigate       = useNavigate()
  const { loadUser }   = useAuth()
  const { mergeGuestCart } = useCart()

  const [phase,     setPhase]     = useState('registro')
  const [vendorRut, setVendorRut] = useState('')
  const [showModal, setShowModal] = useState(false)

  const handleRegistroSuccess = async (tokens, rut) => {
    localStorage.setItem('access_token',  tokens.access)
    localStorage.setItem('refresh_token', tokens.refresh)
    await loadUser()
    setVendorRut(rut)
    setPhase('crear-tienda')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleTiendaCreada = () => setShowModal(true)

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
        <p className="text-[11px] font-semibold text-white/40 tracking-[0.2em] mt-1">MULTITIENDA ANGOL</p>
      </div>

      {/* Step indicator */}
      <div className="w-full max-w-sm mb-4">
        <div className="flex items-center gap-2 mb-2">
          <Step n={1} active={phase === 'registro'}     done={phase === 'crear-tienda'} label="Cuenta" />
          <div className="flex-1 h-px bg-white/10" />
          <Step n={2} active={phase === 'crear-tienda'} done={false}                   label="Tienda" />
        </div>
        <p className="text-xs text-white/30 text-center">{stepLabel}</p>
      </div>

      {/* Form card */}
      <div className="w-full max-w-sm bg-white/[0.05] border border-white/10 rounded-2xl p-6">
        {phase === 'registro'     && <StepRegistro     onSuccess={handleRegistroSuccess} />}
        {phase === 'crear-tienda' && <StepCrearTienda  vendorRut={vendorRut} onSuccess={handleTiendaCreada} />}
      </div>

      <Link to="/login" className="mt-6 text-xs text-white/30 hover:text-white/60 transition-colors">
        ¿Ya tienes cuenta? Inicia sesión
      </Link>

      {/* ── Modal de éxito ── */}
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
            <button onClick={handleGoToPanel}
              className="w-full bg-orange-500 hover:bg-orange-400 active:scale-[0.98] text-white font-bold text-sm py-3 rounded-xl transition-all">
              Ir al panel de vendedor →
            </button>
            <button onClick={() => navigate('/')}
              className="w-full text-xs text-white/40 hover:text-white/70 transition-colors py-1.5">
              Ir al inicio
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

// ── Step indicator component ────────────────────────────────────────
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