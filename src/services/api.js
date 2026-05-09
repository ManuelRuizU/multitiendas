import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  headers: { 'Content-Type': 'application/json' },
})

// Adjunta el token JWT en cada request si existe
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Si el access token expiró (401), intenta renovar con el refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post(
            'http://127.0.0.1:8000/api/token/refresh/',
            { refresh }
          )
          localStorage.setItem('access_token', data.access)
          original.headers.Authorization = `Bearer ${data.access}`
          return api(original)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api
