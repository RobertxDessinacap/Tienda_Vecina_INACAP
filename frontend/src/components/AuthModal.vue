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
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-2xs overflow-y-auto"
  >
    <div
      class="bg-white rounded-lg shadow-2xl max-w-md w-full overflow-hidden border border-gray-200 relative animate-in fade-in zoom-in-95 duration-200 my-auto"
    >
      <!-- Modal Header -->
      <div class="bg-[#FFE600] px-6 py-4 flex items-center justify-between border-b border-yellow-400">
        <div class="flex items-center gap-2">
          <Lock class="w-5 h-5 text-gray-900" />
          <h2 class="text-base font-bold text-gray-900">
            {{ activeTab === 'login' ? 'Iniciar Sesión Segura' : 'Crear Cuenta en Inacap' }}
          </h2>
        </div>
        <button
          @click="authStore.closeAuthModal"
          class="w-7 h-7 rounded-full bg-white/80 hover:bg-white flex items-center justify-center text-gray-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Tab Buttons -->
      <div class="flex border-b border-gray-200 text-xs font-bold text-center">
        <button
          @click="activeTab = 'login'"
          :class="[activeTab === 'login' ? 'text-[#3483FA] border-b-2 border-[#3483FA] bg-blue-50/30' : 'text-gray-500 hover:text-gray-800']"
          class="flex-1 py-3 transition-colors"
        >
          Ingresar
        </button>
        <button
          @click="activeTab = 'register'"
          :class="[activeTab === 'register' ? 'text-[#3483FA] border-b-2 border-[#3483FA] bg-blue-50/30' : 'text-gray-500 hover:text-gray-800']"
          class="flex-1 py-3 transition-colors"
        >
          Registrar Nueva Cuenta
        </button>
      </div>

      <div class="p-6 space-y-4 text-xs">
        <!-- Error Message -->
        <div v-if="authStore.error" class="bg-red-50 border border-red-200 text-red-700 p-3 rounded-md flex items-center gap-2">
          <AlertCircle class="w-4 h-4 shrink-0" />
          <span>{{ authStore.error }}</span>
        </div>

        <!-- ================= LOGIN TAB ================= -->
        <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="space-y-3.5">
          <div>
            <label class="block font-bold text-gray-700 mb-1">Correo Electrónico Institucional / Personal</label>
            <div class="relative">
              <input
                v-model="loginForm.email"
                type="email"
                placeholder="ejemplo@inacap.cl"
                required
                class="w-full pl-8 pr-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
              />
              <Mail class="w-4 h-4 text-gray-400 absolute left-2.5 top-2.5" />
            </div>
          </div>

          <div>
            <label class="block font-bold text-gray-700 mb-1">Contraseña</label>
            <div class="relative">
              <input
                v-model="loginForm.password"
                type="password"
                placeholder="••••••••"
                required
                class="w-full pl-8 pr-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
              />
              <KeyRound class="w-4 h-4 text-gray-400 absolute left-2.5 top-2.5" />
            </div>
          </div>

          <button
            type="submit"
            :disabled="authStore.loading"
            class="w-full bg-[#3483FA] hover:bg-[#2968C8] text-white font-bold py-2.5 rounded-md text-xs uppercase tracking-wider transition-colors disabled:opacity-50 shadow-xs flex items-center justify-center gap-2"
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
            <label class="block font-bold text-gray-700 mb-1.5">Selecciona el Rol de tu Cuenta *</label>
            <div class="grid grid-cols-2 gap-2">
              <div
                @click="registerForm.role = 'BUYER'"
                :class="[registerForm.role === 'BUYER' ? 'border-[#3483FA] bg-blue-50/50 text-[#3483FA]' : 'border-gray-200 bg-white text-gray-600']"
                class="p-2.5 rounded-lg border-2 cursor-pointer transition-all flex flex-col items-center text-center space-y-1 hover:border-blue-300"
              >
                <ShoppingBag class="w-5 h-5" />
                <span class="font-bold text-xs">Comprador</span>
                <span class="text-[10px] text-gray-500 leading-tight">Buscar y comprar productos de forma segura</span>
              </div>

              <div
                @click="registerForm.role = 'SELLER'"
                :class="[registerForm.role === 'SELLER' ? 'border-[#3483FA] bg-blue-50/50 text-[#3483FA]' : 'border-gray-200 bg-white text-gray-600']"
                class="p-2.5 rounded-lg border-2 cursor-pointer transition-all flex flex-col items-center text-center space-y-1 hover:border-blue-300"
              >
                <Store class="w-5 h-5" />
                <span class="font-bold text-xs">Vendedor</span>
                <span class="text-[10px] text-gray-500 leading-tight">Publicar productos y gestionar catálogo</span>
              </div>
            </div>
          </div>

          <div>
            <label class="block font-bold text-gray-700 mb-1">Correo Electrónico *</label>
            <input
              v-model="registerForm.email"
              type="email"
              placeholder="tu_correo@inacap.cl"
              required
              class="w-full px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
            />
          </div>

          <div>
            <label class="block font-bold text-gray-700 mb-1">Nombre Completo (PII Segregada)</label>
            <input
              v-model="registerForm.fullName"
              type="text"
              placeholder="Ej: Roberto González"
              class="w-full px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
            />
          </div>

          <!-- Intermediate Account Public Alias Box (ISO 27001) -->
          <div class="bg-amber-50/80 border border-amber-200 p-2.5 rounded-md space-y-1">
            <div class="flex items-center gap-1.5 font-bold text-amber-900">
              <ShieldCheck class="w-4 h-4 text-amber-700" />
              <span>Cuenta Intermedia Pública (Seudónimo):</span>
            </div>
            <p class="text-[10px] text-amber-800 leading-tight">
              Para proteger tu privacidad (ISO 27001), los compradores y el catálogo sólo verán tu alias público, nunca tu correo:
            </p>
            <input
              v-model="registerForm.customAlias"
              type="text"
              :placeholder="intermediateAliasPreview"
              class="w-full px-2.5 py-1.5 rounded-sm border border-amber-300 bg-white text-xs font-mono font-semibold text-gray-800"
            />
          </div>

          <div>
            <label class="block font-bold text-gray-700 mb-1">Contraseña Segura (mínimo 8 caracteres) *</label>
            <input
              v-model="registerForm.password"
              type="password"
              placeholder="••••••••"
              minlength="8"
              required
              class="w-full px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
            />
          </div>

          <button
            type="submit"
            :disabled="authStore.loading"
            class="w-full bg-[#3483FA] hover:bg-[#2968C8] text-white font-bold py-2.5 rounded-md text-xs uppercase tracking-wider transition-colors disabled:opacity-50 shadow-xs"
          >
            <span v-if="authStore.loading">Creando Cuenta Segura...</span>
            <span v-else>Registrarse como {{ registerForm.role === 'SELLER' ? 'Vendedor' : 'Comprador' }}</span>
          </button>
        </form>

        <!-- Fast Demo Credential Buttons -->
        <div class="pt-3 border-t border-gray-200">
          <span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider block mb-1.5">
            Cuentas Demo para Pruebas Rápidas:
          </span>
          <div class="grid grid-cols-3 gap-1.5">
            <button
              type="button"
              @click="fillDemo('vendedor@inacap.cl', 'Vendedor1234!', 'SELLER')"
              class="bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-200 py-1 px-2 rounded-xs text-[10px] font-semibold transition-colors"
            >
              Vendedor
            </button>
            <button
              type="button"
              @click="fillDemo('comprador@inacap.cl', 'Comprador1234!', 'BUYER')"
              class="bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 py-1 px-2 rounded-xs text-[10px] font-semibold transition-colors"
            >
              Comprador
            </button>
            <button
              type="button"
              @click="fillDemo('admin@inacap.cl', 'Admin1234!', 'ADMIN')"
              class="bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-200 py-1 px-2 rounded-xs text-[10px] font-semibold transition-colors"
            >
              Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
