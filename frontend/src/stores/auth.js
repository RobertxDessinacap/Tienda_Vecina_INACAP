import { defineStore } from 'pinia'
import apiClient from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => {
    let savedUser = null
    try {
      savedUser = JSON.parse(localStorage.getItem('inacap_auth_user') || 'null')
    } catch {
      savedUser = null
    }

    return {
      user: savedUser,
      token: localStorage.getItem('inacap_auth_token') || null,
      loading: false,
      error: null,
      authModalOpen: false,
      authModalMode: 'login', // 'login' | 'register'
    }
  },

  getters: {
    isAuthenticated: (state) => !!state.token && !!state.user,
    userRole: (state) => state.user?.role || 'GUEST',
    isSeller: (state) => state.user?.role === 'SELLER' || state.user?.role === 'ADMIN',
    isAdmin: (state) => state.user?.role === 'ADMIN',
    intermediateAlias: (state) => state.user?.intermediate_account?.public_alias || 'Usuario Anónimo',
    intermediateReputation: (state) => state.user?.intermediate_account?.reputation_score || 5.0,
  },

  actions: {
    openAuthModal(mode = 'login') {
      this.authModalMode = mode
      this.authModalOpen = true
      this.error = null
    },

    closeAuthModal() {
      this.authModalOpen = false
      this.error = null
    },

    async login(email, password) {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.post('/auth/login/', { email, password })
        const { token, user } = response.data
        this.token = token
        this.user = user

        localStorage.setItem('inacap_auth_token', token)
        localStorage.setItem('inacap_auth_user', JSON.stringify(user))

        this.closeAuthModal()
        return { success: true, user }
      } catch (err) {
        const message = err.response?.data?.errors?.[0] ||
                        err.response?.data?.message ||
                        'Error de autenticación. Verifique sus credenciales.'
        this.error = message
        return { success: false, error: message }
      } finally {
        this.loading = false
      }
    },

    async register({ email, password, role = 'BUYER', fullName = '', customAlias = '' }) {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.post('/auth/register/', {
          email,
          password,
          role,
          full_name: fullName,
          custom_alias: customAlias,
        })
        const { token, user } = response.data
        this.token = token
        this.user = user

        localStorage.setItem('inacap_auth_token', token)
        localStorage.setItem('inacap_auth_user', JSON.stringify(user))

        this.closeAuthModal()
        return { success: true, user }
      } catch (err) {
        let msg = 'Error en el registro.'
        if (err.response?.data?.errors) {
          const errors = err.response.data.errors
          const firstKey = Object.keys(errors)[0]
          if (firstKey && Array.isArray(errors[firstKey])) {
            msg = errors[firstKey][0]
          }
        }
        this.error = msg
        return { success: false, error: msg }
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('inacap_auth_token')
      localStorage.removeItem('inacap_auth_user')
    },
  },
})
