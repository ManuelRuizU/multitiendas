import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'

const INPUT = 'w-full bg-white/[0.06] border border-white/10 focus:border-orange-500/60 focus:outline-none rounded-xl px-4 py-2.5 text-sm text-white placeholder-white/20 transition-colors disabled:opacity-40'
const LABEL = 'block text-xs text-white/50 mb-1.5'

const ROLE_BADGE = {
  cliente:    'bg-blue-900/40 text-blue-300 border-blue-800/40',
  vendedor:   'bg-orange-900/40 text-orange-300 border-orange-800/40',
  repartidor: 'bg-green-900/40 text-green-300 border-green-800/40',
}

export default function PerfilPage() {
  const navigate = useNavigate()
  const { user, loadUser, logout } = useAuth()

  const [editing, setEditing] = useState(false)
  const [form,    setForm]    = useState({ first_name: '', last_name: '', email: '' })
  const [saving,  setSaving]  = useState(false)
  const [msg,     setMsg]     = useState(null)

  // Redirect if not logged in
  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center gap-4 text-white/40">
        <p className="text-4xl">🔒</p>
        <p className="text-sm">Debes iniciar sesión para ver tu perfil</p>
        <button
          onClick={() => navigate('/login')}
          className="text-orange-400 hover:text-orange-300 text-sm transition-colors"
        >
          Ir a iniciar sesión →
        </button>
      </div>
    )
  }

  const startEdit = () => {
    setForm({ first_name: user.first_name || '', last_name: user.last_name || '', email: user.email || '' })
    setMsg(null)
    setEditing(true)
  }

  const cancelEdit = () => { setEditing(false); setMsg(null) }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMsg(null)
    try {
      await api.patch(`usuarios/users/${user.id}/`, {
        first_name: form.first_name,
        last_name:  form.last_name,
        email:      form.email,
      })
      await loadUser()
      setEditing(false)
      setMsg({ type: 'ok', text: 'Perfil actualizado correctamente.' })
    } catch (err) {
      const d = err?.response?.data
      const text = d && typeof d === 'object'
        ? Object.values(d).flat().join(' ')
        : 'Error al guardar. Intenta de nuevo.'
      setMsg({ type: 'err', text })
    } finally {
      setSaving(false)
    }
  }

  const roles = user.roles ?? []

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header title="Mi perfil" onBack={() => navigate(-1)} />

      <main className="max-w-lg mx-auto px-4 pt-6 pb-16 space-y-4">

        {/* Avatar + nombre */}
        <div className="flex items-center gap-4 bg-white/[0.04] border border-white/5 rounded-2xl p-4">
          <div className="w-14 h-14 rounded-full bg-orange-500/80 flex items-center justify-center text-xl font-black text-white shrink-0">
            {(user.first_name || user.username || 'U').slice(0, 2).toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="font-bold text-base leading-snug truncate">
              {user.first_name ? `${user.first_name} ${user.last_name}`.trim() : user.username}
            </p>
            <p className="text-xs text-white/40 truncate">{user.email}</p>
            {roles.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {roles.map((r) => (
                  <span
                    key={r}
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${ROLE_BADGE[r] ?? 'bg-white/10 text-white/50 border-white/10'}`}
                  >
                    {r}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Feedback message */}
        {msg && (
          <p
            role="alert"
            className={`text-xs rounded-lg px-3 py-2 ${
              msg.type === 'ok'
                ? 'text-green-400 bg-green-900/20 border border-green-800/30'
                : 'text-red-400 bg-red-900/20 border border-red-800/30'
            }`}
          >
            {msg.text}
          </p>
        )}

        {/* Data card */}
        <div className="bg-white/[0.04] border border-white/5 rounded-2xl p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold">Datos de cuenta</h2>
            {!editing && (
              <button
                onClick={startEdit}
                className="text-xs text-orange-400 hover:text-orange-300 transition-colors"
              >
                Editar
              </button>
            )}
          </div>

          {editing ? (
            <form onSubmit={handleSave} noValidate className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={LABEL}>Nombre</label>
                  <input className={INPUT} value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} placeholder="Juan" />
                </div>
                <div>
                  <label className={LABEL}>Apellido</label>
                  <input className={INPUT} value={form.last_name}  onChange={(e) => setForm((f) => ({ ...f, last_name:  e.target.value }))} placeholder="Pérez" />
                </div>
              </div>
              <div>
                <label className={LABEL}>Email</label>
                <input className={INPUT} type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} placeholder="juan@email.com" />
              </div>
              <div className="flex gap-2 pt-1">
                <button
                  type="submit" disabled={saving}
                  className="flex-1 bg-orange-500 hover:bg-orange-400 disabled:opacity-50 text-white font-bold text-sm py-2.5 rounded-xl transition-all active:scale-[0.98]"
                >
                  {saving ? 'Guardando…' : 'Guardar'}
                </button>
                <button
                  type="button" onClick={cancelEdit}
                  className="flex-1 bg-white/5 hover:bg-white/10 text-white/60 font-semibold text-sm py-2.5 rounded-xl transition-all"
                >
                  Cancelar
                </button>
              </div>
            </form>
          ) : (
            <dl className="space-y-3">
              <Row label="Usuario"  value={user.username} />
              <Row label="Nombre"   value={[user.first_name, user.last_name].filter(Boolean).join(' ') || '—'} />
              <Row label="Email"    value={user.email} />
            </dl>
          )}
        </div>

        {/* Quick links */}
        <div className="bg-white/[0.04] border border-white/5 rounded-2xl divide-y divide-white/5">
          <QuickLink icon="📦" label="Mis pedidos"  onClick={() => navigate('/mis-pedidos')} />
          <QuickLink icon="🔑" label="Cambiar contraseña" onClick={() => navigate('/cambiar-password')} />
        </div>

        {/* Logout */}
        <button
          onClick={() => { logout(); navigate('/') }}
          className="w-full text-sm text-red-400 hover:text-red-300 border border-red-900/40 hover:bg-red-900/20 rounded-xl py-3 transition-all"
        >
          Cerrar sesión
        </button>

      </main>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt className="text-xs text-white/35 shrink-0">{label}</dt>
      <dd className="text-xs text-white/80 text-right break-all">{value}</dd>
    </div>
  )
}

function QuickLink({ icon, label, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 px-4 py-3 text-sm text-white/70 hover:text-white hover:bg-white/5 transition-colors text-left"
    >
      <span className="text-base" aria-hidden="true">{icon}</span>
      <span className="flex-1">{label}</span>
      <span className="text-white/20 text-xs">›</span>
    </button>
  )
}
