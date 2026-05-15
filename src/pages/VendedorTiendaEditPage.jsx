
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'

// ── Constants ──────────────────────────────────────────────────────────────

const BANCOS = [
  'Banco de Chile','Banco Estado','Banco BCI','Banco Santander',
  'Banco Scotiabank','Banco Itaú','Banco Falabella','Banco Ripley',
  'Banco Security','Banco BICE','Coopeuch','Otro',
]
const TIPOS_CUENTA = ['Cuenta Corriente','Cuenta Vista','Cuenta RUT','Cuenta de Ahorro']
const DIAS = ['lunes','martes','miercoles','jueves','viernes','sabado','domingo']
const DIAS_LABEL = { lunes:'Lun', martes:'Mar', miercoles:'Mié', jueves:'Jue', viernes:'Vie', sabado:'Sáb', domingo:'Dom' }

const iCls = (err) => [
  'w-full bg-white/[0.06] border rounded-xl px-3 py-2.5 text-sm text-white',
  'placeholder:text-white/20 focus:outline-none transition-colors',
  err ? 'border-red-500/60 focus:border-red-500/80' : 'border-white/10 focus:border-orange-500/50',
].join(' ')

// ── Select con fondo oscuro para que se vean las opciones ──────────────────
const selectCls = (err) => [
  'w-full border rounded-xl px-3 py-2.5 text-sm text-white',
  'focus:outline-none transition-colors appearance-none',
  'bg-slate-800',  // fondo oscuro fijo para que las opciones sean legibles
  err ? 'border-red-500/60 focus:border-red-500/80' : 'border-white/10 focus:border-orange-500/50',
].join(' ')

// ── Main Page ──────────────────────────────────────────────────────────────

export default function VendedorTiendaEditPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()
  const fileRef = useRef()

  const [tienda, setTienda]       = useState(null)
  const [form,   setForm]         = useState(null)
  const [logoFile, setLogoFile]   = useState(null)
  const [logoPrev, setLogoPrev]   = useState(null)
  const [loading, setLoading]     = useState(true)
  const [saving,  setSaving]      = useState(false)
  const [saved,   setSaved]       = useState(false)
  const [errs,    setErrs]        = useState({})

  // Radios de envío (gestión independiente del formulario principal)
  const [radios,        setRadios]        = useState([])
  const [newRadio,      setNewRadio]      = useState({ distancia_max_km: '', costo_envio: '', envio_gratis: false })
  const [addingRadio,   setAddingRadio]   = useState(false)
  const [deletingRadio, setDeletingRadio] = useState(null)
  const [radioErr,      setRadioErr]      = useState('')

  // Auth guard
  useEffect(() => {
    if (authLoading) return
    if (!user)             { navigate('/');  return }
    if (!user.is_vendedor) { navigate('/');  return }
  }, [user, authLoading, navigate])

  // Load tienda
  useEffect(() => {
    if (authLoading || !user) return
    api.get(`tiendas/${slug}/`)
      .then(({ data }) => {
        if (data.vendedor_username !== user.username) {
          navigate('/vendedor/panel')
          return
        }
        setTienda(data)
        setForm({
          nombre:                   data.nombre                   ?? '',
          tipo_negocio:             data.tipo_negocio             ?? 'COMIDA',
          descripcion:              data.descripcion              ?? '',
          activo:                   data.activo                   ?? true,
          direccion:                data.direccion                ?? '',
          telefono:                 data.telefono                 ?? '',
          email:                    data.email                    ?? '',
          url:                      data.url                      ?? '',
          horario_atencion:         data.horario_atencion         ?? '',
          hora_apertura:            data.hora_apertura?.slice(0,5) ?? '',
          hora_cierre:              data.hora_cierre?.slice(0,5)   ?? '',
          acepta_pedidos_programados: data.acepta_pedidos_programados ?? false,
          abre_lunes:               data.abre_lunes    ?? true,
          abre_martes:              data.abre_martes   ?? true,
          abre_miercoles:           data.abre_miercoles ?? true,
          abre_jueves:              data.abre_jueves   ?? true,
          abre_viernes:             data.abre_viernes  ?? true,
          abre_sabado:              data.abre_sabado   ?? false,
          abre_domingo:             data.abre_domingo  ?? false,
          acepta_efectivo:          data.acepta_efectivo          ?? true,
          acepta_transferencia:     data.acepta_transferencia     ?? false,
          acepta_link_pago:         data.acepta_link_pago         ?? false,
          banco:                    data.banco                    ?? '',
          tipo_cuenta:              data.tipo_cuenta              ?? '',
          numero_cuenta:            data.numero_cuenta            ?? '',
          titular_cuenta:           data.titular_cuenta           ?? '',
          rut_titular:              data.rut_titular              ?? '',
          email_transferencia:      data.email_transferencia      ?? '',
          link_pago_url:            data.link_pago_url            ?? '',
          instrucciones_link_pago:  data.instrucciones_link_pago  ?? '',
        })
      })
      .catch(() => navigate('/vendedor/panel'))
      .finally(() => setLoading(false))
  }, [slug, user, authLoading, navigate])

  // Cargar radios cuando ya tenemos el id de la tienda
  useEffect(() => {
    if (!tienda?.id) return
    api.get(`radios-envio/?tienda_id=${tienda.id}`)
      .then(({ data }) => setRadios(Array.isArray(data) ? data : (data.results ?? [])))
      .catch(() => {})
  }, [tienda?.id])

  const upd = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const handleLogoChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setLogoFile(file)
    setLogoPrev(URL.createObjectURL(file))
  }

  const validate = () => {
    const e = {}
    if (!form.nombre.trim())    e.nombre    = 'Nombre requerido'
    if (!form.direccion.trim()) e.direccion = 'Dirección requerida'
    if (!form.acepta_efectivo && !form.acepta_transferencia && !form.acepta_link_pago)
      e.metodos_pago = 'Activa al menos un método de pago'
    if (form.acepta_transferencia) {
      if (!form.banco)               e.banco               = 'Banco requerido'
      if (!form.tipo_cuenta)         e.tipo_cuenta         = 'Tipo de cuenta requerido'
      if (!form.numero_cuenta)       e.numero_cuenta       = 'Número de cuenta requerido'
      if (!form.titular_cuenta)      e.titular_cuenta      = 'Titular requerido'
      if (!form.rut_titular)         e.rut_titular         = 'RUT requerido'
      if (!form.email_transferencia) e.email_transferencia = 'Email requerido'
    }
    if (form.acepta_link_pago && !form.link_pago_url)
      e.link_pago_url = 'Ingresa la URL del link de pago'
    setErrs(e)
    return !Object.keys(e).length
  }

  const handleSave = async () => {
    if (!validate()) return
    setSaving(true)
    setSaved(false)
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => {
        if (v === null || v === undefined || v === '') return
        fd.append(k, typeof v === 'boolean' ? String(v) : v)
      })
      ;['activo','acepta_pedidos_programados','acepta_efectivo','acepta_transferencia','acepta_link_pago',
        ...DIAS.map(d => `abre_${d}`)
      ].forEach(k => fd.set(k, String(form[k])))
      if (logoFile) fd.append('logo', logoFile)

      await api.patch(`tiendas/${slug}/`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3500)
    } catch (err) {
      const detail = err.response?.data
      if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
        setErrs(prev => ({ ...prev, ...detail }))
      } else {
        setErrs({ _global: 'Error al guardar. Intenta nuevamente.' })
      }
    } finally {
      setSaving(false)
    }
  }

  const handleAddRadio = async () => {
    setRadioErr('')
    const km = parseFloat(newRadio.distancia_max_km)
    if (!km || km <= 0) { setRadioErr('Ingresa una distancia válida'); return }
    if (!newRadio.envio_gratis && (newRadio.costo_envio === '' || parseFloat(newRadio.costo_envio) < 0))
      { setRadioErr('Ingresa el costo de envío'); return }
    setAddingRadio(true)
    try {
      const { data } = await api.post('radios-envio/', {
        tienda:           tienda.id,
        distancia_max_km: km,
        costo_envio:      newRadio.envio_gratis ? 0 : parseFloat(newRadio.costo_envio),
        envio_gratis:     newRadio.envio_gratis,
      })
      setRadios(r => [...r, data].sort((a, b) => a.distancia_max_km - b.distancia_max_km))
      setNewRadio({ distancia_max_km: '', costo_envio: '', envio_gratis: false })
    } catch {
      setRadioErr('Error al agregar radio. Intenta nuevamente.')
    } finally {
      setAddingRadio(false)
    }
  }

  const handleDeleteRadio = async (id) => {
    setDeletingRadio(id)
    try {
      await api.delete(`radios-envio/${id}/`)
      setRadios(r => r.filter(x => x.id !== id))
    } catch {
      // silent — radio remains in list
    } finally {
      setDeletingRadio(null)
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────

  if (authLoading || !user) return null

  if (loading || !form) {
    return (
      <div className="min-h-screen bg-slate-950 text-white">
        <Header title="Editar tienda" onBack={() => navigate('/vendedor/panel')} />
        <div className="max-w-2xl mx-auto px-4 pt-6 space-y-4">
          {[1,2,3,4].map(n => (
            <div key={n} className="h-32 bg-white/5 rounded-2xl animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  const logoSrc = logoPrev ?? tienda.logo ?? null

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header title={tienda.nombre} onBack={() => navigate('/vendedor/panel')} />

      <main className="max-w-2xl mx-auto px-4 pt-5 pb-24 space-y-6">

        {/* Error global */}
        {errs._global && (
          <div className="bg-red-900/20 border border-red-700/40 text-red-400 rounded-xl px-4 py-3 text-sm">
            {errs._global}
          </div>
        )}

        {/* ── 1. Info general ─────────────────────────────────── */}
        <Section title="Información general">
          <Field label="Nombre de la tienda" required error={errs.nombre}>
            <input
              type="text" value={form.nombre}
              onChange={e => upd('nombre', e.target.value)}
              placeholder="Ej: Pizzería Don Pedro"
              className={iCls(errs.nombre)}
            />
          </Field>

          <Field label="Tipo de negocio">
            <select
              value={form.tipo_negocio}
              onChange={e => upd('tipo_negocio', e.target.value)}
              className={selectCls()}
            >
              <option value="COMIDA">🍕 Comida y Bebidas</option>
              <option value="RETAIL">🛍️ Tienda / Retail</option>
              <option value="SERVICIOS">🔧 Servicios</option>
              <option value="OTRO">🏪 Otro</option>
            </select>
          </Field>

          <Field label="Descripción">
            <textarea
              rows={3} value={form.descripcion}
              onChange={e => upd('descripcion', e.target.value)}
              placeholder="Describe tu negocio..."
              className={`${iCls()} resize-none`}
            />
          </Field>

          <ToggleRow
            label="Tienda activa" desc="Visible para los clientes"
            checked={form.activo} onChange={v => upd('activo', v)}
          />
        </Section>

        {/* ── 2. Logo ─────────────────────────────────────────── */}
        <Section title="Logo">
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 rounded-2xl overflow-hidden bg-white/5 border border-white/10 flex items-center justify-center shrink-0 text-3xl">
              {logoSrc
                ? <img src={logoSrc} alt="Logo" className="w-full h-full object-cover" />
                : '🏪'
              }
            </div>
            <div>
              <button
                onClick={() => fileRef.current?.click()}
                className="text-sm text-orange-400 hover:text-orange-300 border border-orange-500/30 hover:bg-orange-500/10 px-4 py-2 rounded-full transition-all"
              >
                {logoSrc ? 'Cambiar imagen' : 'Subir imagen'}
              </button>
              <p className="text-xs text-white/25 mt-1.5">PNG, JPG · Máx 2 MB</p>
            </div>
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleLogoChange} />
          </div>
        </Section>

        {/* ── 3. Ubicación y contacto ──────────────────────────── */}
        <Section title="Ubicación y contacto">
          <Field label="Dirección" required error={errs.direccion}>
            <input
              type="text" value={form.direccion}
              onChange={e => upd('direccion', e.target.value)}
              placeholder="Av. O'Higgins 123, Angol"
              className={iCls(errs.direccion)}
            />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Teléfono">
              <input type="tel" value={form.telefono}
                onChange={e => upd('telefono', e.target.value)}
                placeholder="+56912345678" className={iCls()} />
            </Field>
            <Field label="Email de contacto">
              <input type="email" value={form.email}
                onChange={e => upd('email', e.target.value)}
                placeholder="tienda@email.com" className={iCls()} />
            </Field>
          </div>
          <Field label="Sitio web">
            <input type="url" value={form.url}
              onChange={e => upd('url', e.target.value)}
              placeholder="https://..." className={iCls()} />
          </Field>
        </Section>

        {/* ── 4. Horario ──────────────────────────────────────── */}
        <Section title="Horario de atención">
          <Field label="Descripción del horario">
            <input
              type="text" value={form.horario_atencion}
              onChange={e => upd('horario_atencion', e.target.value)}
              placeholder="Lun-Vie 9:00-20:00 | Sáb 9:00-14:00"
              className={iCls()}
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Hora de apertura">
              <input type="time" value={form.hora_apertura}
                onChange={e => upd('hora_apertura', e.target.value)}
                className={iCls()} />
            </Field>
            <Field label="Hora de cierre">
              <input type="time" value={form.hora_cierre}
                onChange={e => upd('hora_cierre', e.target.value)}
                className={iCls()} />
            </Field>
          </div>

          <div>
            <p className="text-xs text-white/45 mb-2">Días de atención</p>
            <div className="flex flex-wrap gap-2">
              {DIAS.map(dia => (
                <button
                  key={dia}
                  type="button"
                  onClick={() => upd(`abre_${dia}`, !form[`abre_${dia}`])}
                  className={[
                    'px-3 py-1.5 rounded-full text-xs font-semibold border transition-all',
                    form[`abre_${dia}`]
                      ? 'bg-orange-500/20 border-orange-500/40 text-orange-300'
                      : 'bg-white/5 border-white/10 text-white/35 hover:text-white/60',
                  ].join(' ')}
                >
                  {DIAS_LABEL[dia]}
                </button>
              ))}
            </div>
          </div>

          <ToggleRow
            label="Acepta pedidos programados"
            desc="Clientes pueden pedir fuera del horario de atención"
            checked={form.acepta_pedidos_programados}
            onChange={v => upd('acepta_pedidos_programados', v)}
          />
        </Section>

        {/* ── 5. Métodos de pago ──────────────────────────────── */}
        <Section title="Métodos de pago" error={errs.metodos_pago}>

          {/* Efectivo */}
          <PayToggle
            icon="💵" label="Efectivo" desc="El cliente paga al recibir"
            checked={form.acepta_efectivo}
            onChange={v => upd('acepta_efectivo', v)}
          />

          {/* Transferencia bancaria */}
          <div>
            <PayToggle
              icon="🏦" label="Transferencia bancaria"
              desc="El cliente transfiere antes del despacho"
              checked={form.acepta_transferencia}
              onChange={v => upd('acepta_transferencia', v)}
            />
            {form.acepta_transferencia && (
              <div className="mt-3 ml-2 pl-4 border-l border-white/10 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Banco" required error={errs.banco}>
                    <select value={form.banco}
                      onChange={e => upd('banco', e.target.value)}
                      className={selectCls(errs.banco)}>
                      <option value="">Seleccionar…</option>
                      {BANCOS.map(b => <option key={b} value={b}>{b}</option>)}
                    </select>
                  </Field>
                  <Field label="Tipo de cuenta" required error={errs.tipo_cuenta}>
                    <select value={form.tipo_cuenta}
                      onChange={e => upd('tipo_cuenta', e.target.value)}
                      className={selectCls(errs.tipo_cuenta)}>
                      <option value="">Seleccionar…</option>
                      {TIPOS_CUENTA.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </Field>
                </div>
                <Field label="Número de cuenta" required error={errs.numero_cuenta}>
                  <input type="text" value={form.numero_cuenta}
                    onChange={e => upd('numero_cuenta', e.target.value)}
                    placeholder="12345678" className={iCls(errs.numero_cuenta)} />
                </Field>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Titular" required error={errs.titular_cuenta}>
                    <input type="text" value={form.titular_cuenta}
                      onChange={e => upd('titular_cuenta', e.target.value)}
                      placeholder="Juan Pérez" className={iCls(errs.titular_cuenta)} />
                  </Field>
                  <Field label="RUT titular" required error={errs.rut_titular}>
                    <input type="text" value={form.rut_titular}
                      onChange={e => upd('rut_titular', e.target.value)}
                      placeholder="12.345.678-9" className={iCls(errs.rut_titular)} />
                  </Field>
                </div>
                <Field label="Email para transferencia" required error={errs.email_transferencia}>
                  <input type="email" value={form.email_transferencia}
                    onChange={e => upd('email_transferencia', e.target.value)}
                    placeholder="pagos@correo.com" className={iCls(errs.email_transferencia)} />
                </Field>
              </div>
            )}
          </div>

          {/* Link de pago */}
          <div>
            <PayToggle
              icon="🔗" label="Link de pago"
              desc="Flow, Khipu, MercadoPago u otro"
              checked={form.acepta_link_pago}
              onChange={v => upd('acepta_link_pago', v)}
            />
            {form.acepta_link_pago && (
              <div className="mt-3 ml-2 pl-4 border-l border-white/10 space-y-3">
                <Field label="URL del link de pago" required error={errs.link_pago_url}>
                  <input type="url" value={form.link_pago_url}
                    onChange={e => upd('link_pago_url', e.target.value)}
                    placeholder="https://flow.cl/..." className={iCls(errs.link_pago_url)} />
                </Field>
                <Field label="Instrucciones (opcional)">
                  <input type="text" value={form.instrucciones_link_pago}
                    onChange={e => upd('instrucciones_link_pago', e.target.value)}
                    placeholder="Indica tu número de pedido al pagar"
                    className={iCls()} />
                </Field>
              </div>
            )}
          </div>
        </Section>

        {/* ── 6. Zona de despacho ──────────────────────────────── */}
        <Section title="Zona de despacho">

          {/* Hint */}
          <p className="text-xs text-white/35 leading-relaxed">
            Ej: Hasta 3 km → $1.500 &nbsp;|&nbsp; Hasta 6 km → $2.500 &nbsp;|&nbsp; Hasta 10 km → Gratis
          </p>

          {/* Radios existentes */}
          {radios.length > 0 && (
            <div className="space-y-2">
              {radios.map(radio => (
                <div
                  key={radio.id}
                  className="flex items-center gap-3 bg-white/[0.04] border border-white/8 rounded-xl px-3 py-2.5"
                >
                  <span className="text-base shrink-0">📍</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white leading-snug">
                      Hasta {radio.distancia_max_km} km
                    </p>
                    <p className="text-xs text-white/40 mt-0.5">
                      {radio.envio_gratis
                        ? '🎁 Envío gratis'
                        : `$${Number(radio.costo_envio).toLocaleString('es-CL')}`
                      }
                    </p>
                  </div>
                  <button
                    onClick={() => handleDeleteRadio(radio.id)}
                    disabled={deletingRadio === radio.id}
                    aria-label={`Eliminar radio ${radio.distancia_max_km} km`}
                    className="w-7 h-7 flex items-center justify-center rounded-full bg-red-900/30 hover:bg-red-800/50 text-red-400 text-xs disabled:opacity-30 transition-colors shrink-0"
                  >
                    {deletingRadio === radio.id ? '…' : '✕'}
                  </button>
                </div>
              ))}
            </div>
          )}

          {radios.length === 0 && (
            <p className="text-xs text-white/25 text-center py-3 border border-dashed border-white/10 rounded-xl">
              Sin radios de envío configurados
            </p>
          )}

          {/* Formulario nuevo radio */}
          <div className="bg-white/[0.03] border border-white/8 rounded-xl p-3 space-y-3">
            <p className="text-xs font-semibold text-white/50">Agregar radio de envío</p>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Distancia máx. (km)">
                <input
                  type="number" min="0.1" step="0.5"
                  value={newRadio.distancia_max_km}
                  onChange={e => setNewRadio(r => ({ ...r, distancia_max_km: e.target.value }))}
                  placeholder="5"
                  className={iCls(radioErr && !newRadio.distancia_max_km)}
                />
              </Field>
              <Field label="Costo de envío ($)">
                <input
                  type="number" min="0" step="100"
                  value={newRadio.costo_envio}
                  disabled={newRadio.envio_gratis}
                  onChange={e => setNewRadio(r => ({ ...r, costo_envio: e.target.value }))}
                  placeholder="1500"
                  className={`${iCls(radioErr && !newRadio.envio_gratis && !newRadio.costo_envio)} disabled:opacity-35`}
                />
              </Field>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Toggle
                  checked={newRadio.envio_gratis}
                  onChange={v => setNewRadio(r => ({ ...r, envio_gratis: v, costo_envio: v ? '' : r.costo_envio }))}
                />
                <span className="text-sm text-white/60">Envío gratis</span>
              </div>
              <button
                onClick={handleAddRadio}
                disabled={addingRadio}
                className="flex items-center gap-1.5 bg-orange-500 hover:bg-orange-400 disabled:opacity-50 active:scale-[0.97] text-white text-xs font-bold px-4 py-2 rounded-full transition-all"
              >
                {addingRadio ? '…' : '+ Agregar radio'}
              </button>
            </div>

            {radioErr && (
              <p className="text-[10px] text-red-400">{radioErr}</p>
            )}
          </div>

          {/* Cuadrantes — nota */}
          <p className="text-xs text-white/25 text-center pt-1">
            Para zonas de despacho personalizadas (polígonos), contacta al soporte.
          </p>
        </Section>

        {/* ── Botón Guardar con feedback visual ───────────────── */}
        <button
          onClick={handleSave}
          disabled={saving || saved}
          className={[
            'w-full font-bold py-3.5 rounded-xl transition-all duration-300 active:scale-[0.98]',
            saved
              ? 'bg-green-500 hover:bg-green-400 text-white'
              : 'bg-orange-500 hover:bg-orange-400 disabled:opacity-50 text-white',
          ].join(' ')}
        >
          {saving ? '⏳ Guardando...' : saved ? '✅ Cambios guardados' : '💾 Guardar cambios'}
        </button>

      </main>
    </div>
  )
}

// ── Helpers ────────────────────────────────────────────────────────────────

function Section({ title, children, error }) {
  return (
    <section>
      <h2 className="text-xs font-bold text-white/40 uppercase tracking-widest mb-3">{title}</h2>
      {error && <p className="text-xs text-red-400 -mt-1 mb-3">{error}</p>}
      <div className="space-y-3">{children}</div>
    </section>
  )
}

function Field({ label, required, children, error }) {
  return (
    <div>
      <label className="block text-xs text-white/45 mb-1.5">
        {label}{required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      {children}
      {error && <p className="text-[10px] text-red-400 mt-1">{error}</p>}
    </div>
  )
}

function Toggle({ checked, onChange }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={[
        'relative w-11 h-6 rounded-full transition-colors shrink-0',
        checked ? 'bg-orange-500' : 'bg-white/15',
      ].join(' ')}
      aria-checked={checked}
      role="switch"
    >
      <span className={[
        'absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform',
        checked ? 'translate-x-5' : 'translate-x-0.5',
      ].join(' ')} />
    </button>
  )
}

function ToggleRow({ label, desc, checked, onChange }) {
  return (
    <div className="flex items-center justify-between gap-4 p-3 bg-white/[0.04] rounded-xl border border-white/8">
      <div>
        <p className="text-sm font-medium text-white">{label}</p>
        {desc && <p className="text-xs text-white/35 mt-0.5">{desc}</p>}
      </div>
      <Toggle checked={checked} onChange={onChange} />
    </div>
  )
}

function PayToggle({ icon, label, desc, checked, onChange }) {
  return (
    <div className={[
      'flex items-center justify-between gap-4 p-3 rounded-xl border transition-all',
      checked ? 'bg-orange-500/10 border-orange-500/30' : 'bg-white/[0.04] border-white/8',
    ].join(' ')}>
      <div className="flex items-center gap-3">
        <span className="text-xl shrink-0">{icon}</span>
        <div>
          <p className="text-sm font-medium text-white">{label}</p>
          <p className="text-xs text-white/35">{desc}</p>
        </div>
      </div>
      <Toggle checked={checked} onChange={onChange} />
    </div>
  )
}