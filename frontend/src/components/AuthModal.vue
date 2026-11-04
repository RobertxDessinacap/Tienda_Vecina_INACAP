<script setup>
import { reactive, ref, computed } from 'vue'
import {
  X,
  Lock,
  Mail,
  UserCheck,
  ShieldCheck,
  ShoppingBag,
  Store,
  AlertCircle,
  KeyRound,
  ArrowRight,
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { blockDangerousCharsOnKeypress, sanitizeEventInput } from '../utils/security'

const authStore = useAuthStore()

const activeTab = ref(authStore.authModalMode || 'login')

const loginForm = reactive({
  email: '',
  password: '',
})

const registerForm = reactive({
  email: '',
  password: '',
  role: 'BUYER',
  fullName: '',
  customAlias: '',
})

// Auto-generated preview of the Intermediate Account Alias
const intermediateAliasPreview = computed(() => {
  if (registerForm.customAlias.trim()) {
    return registerForm.customAlias.trim()
  }
  if (registerForm.email.includes('@')) {
    const base = registerForm.email.split('@')[0].replace(/[^a-zA-Z0-9_]/g, '_')
    return `${base}_${registerForm.role.toLowerCase()}`
  }
  return 'alias_intermedio_aleatorio'
})

async function handleLogin() {
  await authStore.login(loginForm.email, loginForm.password)
}

async function handleRegister() {
  await authStore.register({
    email: registerForm.email,
    password: registerForm.password,
    role: registerForm.role,
    fullName: registerForm.fullName,
    customAlias: registerForm.customAlias,
  })
}

// Demo quick-fill credentials
function fillDemo(email, pass, role = null) {
  if (activeTab.value === 'login') {
    loginForm.email = email
    loginForm.password = pass
  } else {
    registerForm.email = email
    registerForm.password = pass
    if (role) registerForm.role = role
  }
}
</script>

<template>
  <div
    v-if="authStore.authModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto"
  >
    <div
      class="bg-brand-surface rounded-2xl shadow-xl max-w-md w-full overflow-hidden border border-brand-border relative animate-in fade-in zoom-in-95 duration-200 my-auto"
    >
      <!-- Modal Header -->
      <div class="bg-brand-primary px-6 py-4 flex items-center justify-between border-b border-brand-primary-border">
        <div class="flex items-center gap-2">
          <Lock class="w-5 h-5 text-brand-primary-text" />
          <h2 class="text-base font-bold text-slate-900">
            {{ activeTab === 'login' ? 'Iniciar Sesión Segura' : 'Crear Cuenta en Inacap' }}
          </h2>
        </div>
        <button
          @click="authStore.closeAuthModal"
          class="w-7 h-7 rounded-full bg-brand-surface/80 hover:bg-brand-surface flex items-center justify-center text-slate-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Tab Buttons -->
      <div class="flex border-b border-brand-border text-xs font-bold text-center">
        <button
          @click="activeTab = 'login'"
          :class="[activeTab === 'login' ? 'text-brand-accent border-b-2 border-brand-accent bg-brand-primary-subtle' : 'text-slate-500 hover:text-slate-800']"
          class="flex-1 py-3 transition-colors"
        >
          Ingresar
        </button>
        <button
          @click="activeTab = 'register'"
          :class="[activeTab === 'register' ? 'text-brand-accent border-b-2 border-brand-accent bg-brand-primary-subtle' : 'text-slate-500 hover:text-slate-800']"
          class="flex-1 py-3 transition-colors"
        >
          Registrar Nueva Cuenta
        </button>
      </div>

      <div class="p-6 space-y-4 text-xs">
        <!-- Error Message -->
        <div v-if="authStore.error" class="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg flex items-center gap-2">
          <AlertCircle class="w-4 h-4 shrink-0" />
          <span>{{ authStore.error }}</span>
        </div>

        <!-- ================= LOGIN TAB ================= -->
        <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="space-y-3.5">
          <div>
            <label class="block font-bold text-slate-700 mb-1">Correo Electrónico Institucional / Personal</label>
            <div class="relative">
              <input
                v-model="loginForm.email"
                type="email"
                placeholder="ejemplo@inacap.cl"
                required
                class="w-full pl-8 pr-3 py-2 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
              />
              <Mail class="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
            </div>
          </div>

          <div>
            <label class="block font-bold text-slate-700 mb-1">Contraseña</label>
            <div class="relative">
              <input
                v-model="loginForm.password"
                type="password"
                placeholder="••••••••"
                required
                class="w-full pl-8 pr-3 py-2 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
              />
              <KeyRound class="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
            </div>
          </div>

          <button
            type="submit"
            :disabled="authStore.loading"
            class="w-full bg-brand-accent hover:bg-brand-accent-hover text-white font-bold py-2.5 rounded-lg text-xs uppercase tracking-wider transition-colors disabled:opacity-50 shadow-xs flex items-center justify-center gap-2"
          >
            <span v-if="authStore.loading">Verificando Credenciales...</span>
            <span v-else class="flex items-center gap-1.5">
              <span>Ingresar</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </span>
          </button>
        </form>

        <!-- ================= REGISTER TAB ================= -->
        <form v-else @submit.prevent="handleRegister" class="space-y-3.5">
          <!-- Role Selection Cards (RBAC) -->
          <div>
            <label class="block font-bold text-slate-700 mb-1.5">Selecciona el Rol de tu Cuenta *</label>
            <div class="grid grid-cols-2 gap-2">
              <div
                @click="registerForm.role = 'BUYER'"
                :class="[registerForm.role === 'BUYER' ? 'border-brand-accent bg-brand-accent-soft text-brand-accent' : 'border-brand-border bg-brand-surface text-slate-600']"
                class="p-2.5 rounded-xl border-2 cursor-pointer transition-all flex flex-col items-center text-center space-y-1 hover:border-brand-primary-border"
              >
                <ShoppingBag class="w-5 h-5" />
                <span class="font-bold text-xs">Comprador</span>
                <span class="text-[10px] text-slate-500 leading-tight">Buscar y comprar productos de forma segura</span>
              </div>

              <div
                @click="registerForm.role = 'SELLER'"
                :class="[registerForm.role === 'SELLER' ? 'border-brand-accent bg-brand-accent-soft text-brand-accent' : 'border-brand-border bg-brand-surface text-slate-600']"
                class="p-2.5 rounded-xl border-2 cursor-pointer transition-all flex flex-col items-center text-center space-y-1 hover:border-brand-primary-border"
              >
                <Store class="w-5 h-5" />
                <span class="font-bold text-xs">Vendedor</span>
                <span class="text-[10px] text-slate-500 leading-tight">Publicar productos y gestionar catálogo</span>
              </div>
            </div>
          </div>

          <div>
            <label class="block font-bold text-slate-700 mb-1">Correo Electrónico *</label>
            <input
              v-model="registerForm.email"
              type="email"
              placeholder="tu_correo@inacap.cl"
              required
              class="w-full px-3 py-2 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
            />
          </div>

          <div>
            <label class="block font-bold text-slate-700 mb-1">Nombre Completo</label>
            <input
              v-model="registerForm.fullName"
              type="text"
              @keypress="blockDangerousCharsOnKeypress"
              @input="e => sanitizeEventInput(e, v => registerForm.fullName = v)"
              placeholder="Ej: Roberto González"
              class="w-full px-3 py-2 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
            />
          </div>

          <div>
            <label class="block font-bold text-slate-700 mb-1">Nombre de usuario o apodo</label>
            <input
              v-model="registerForm.customAlias"
              type="text"
              @keypress="blockDangerousCharsOnKeypress"
              @input="e => sanitizeEventInput(e, v => registerForm.customAlias = v)"
              :placeholder="intermediateAliasPreview || 'Ej: RobertoG o MiTienda'"
              class="w-full px-3 py-2 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
            />
          </div>

          <div>
            <label class="block font-bold text-slate-700 mb-1">Contraseña Segura (mínimo 8 caracteres) *</label>
            <input
              v-model="registerForm.password"
              type="password"
              placeholder="••••••••"
              minlength="8"
              required
              class="w-full px-3 py-2 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
            />
          </div>

          <button
            type="submit"
            :disabled="authStore.loading"
            class="w-full bg-brand-accent hover:bg-brand-accent-hover text-white font-bold py-2.5 rounded-lg text-xs uppercase tracking-wider transition-colors disabled:opacity-50 shadow-xs"
          >
            <span v-if="authStore.loading">Creando Cuenta Segura...</span>
            <span v-else>Registrarse como {{ registerForm.role === 'SELLER' ? 'Vendedor' : 'Comprador' }}</span>
          </button>
        </form>

        <!-- Fast Demo Credential Buttons -->
        <div class="pt-3 border-t border-brand-border">
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
            Cuentas Demo para Pruebas Rápidas:
          </span>
          <div class="grid grid-cols-3 gap-1.5">
            <button
              type="button"
              @click="fillDemo('vendedor@inacap.cl', 'Vendedor1234!', 'SELLER')"
              class="bg-brand-accent-soft hover:bg-brand-primary-subtle text-brand-primary-text border border-brand-accent-border py-1 px-2 rounded-md text-[10px] font-semibold transition-colors"
            >
              Vendedor
            </button>
            <button
              type="button"
              @click="fillDemo('comprador@inacap.cl', 'Comprador1234!', 'BUYER')"
              class="bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 py-1 px-2 rounded-md text-[10px] font-semibold transition-colors"
            >
              Comprador
            </button>
            <button
              type="button"
              @click="fillDemo('admin@inacap.cl', 'Admin1234!', 'ADMIN')"
              class="bg-indigo-50 hover:bg-indigo-100 text-indigo-800 border border-indigo-200 py-1 px-2 rounded-md text-[10px] font-semibold transition-colors"
            >
              Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
