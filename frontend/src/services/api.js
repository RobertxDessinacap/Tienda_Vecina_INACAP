import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
})

// Request interceptor: inject JWT Bearer token if present
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('inacap_auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: handle token expiration or unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      const detail = String(error.response.data?.detail || error.response.data?.message || '').toLowerCase()
      if (
        error.response.status === 401 ||
        detail.includes('token') ||
        detail.includes('sesión') ||
        detail.includes('expirado')
      ) {
        // Limpiar credenciales obsoletas o expiradas
        localStorage.removeItem('inacap_auth_token')
        localStorage.removeItem('inacap_auth_user')
        window.dispatchEvent(new CustomEvent('inacap:auth-expired'))
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
