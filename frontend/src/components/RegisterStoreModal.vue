<script setup>
import { ref, computed, watch } from 'vue'
import { useProductStore } from '../stores/products'
import { useAuthStore } from '../stores/auth'
import { sanitizeEventInput, sanitizeInput, isValidHttpsUrl } from '../utils/security'
import {
  X,
  Store,
  Globe,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Clock,
} from 'lucide-vue-next'

const productStore = useProductStore()
const authStore = useAuthStore()

const storeName = ref('')
const storeUrl = ref('')
const localError = ref(null)
const successMsg = ref(null)
const isSubmitting = ref(false)

const isStorePending = computed(
  () => authStore.user?.user_profile?.official_store_status === 'PENDING'
)

watch(
  () => productStore.registerStoreModalOpen,
  (open) => {
    if (open) {
      const profile = authStore.user?.user_profile || {}
      storeName.value = profile.official_store_name || ''
      storeUrl.value = profile.official_store_url || ''
      localError.value = null
      successMsg.value = null
    }
  }
)

function onNameInput(e) {
  sanitizeEventInput(e, (cleaned) => {
    storeName.value = cleaned
  })
}

function onUrlInput(e) {
  sanitizeEventInput(e, (cleaned) => {
    storeUrl.value = cleaned
  })
}

async function handleSubmit() {
  localError.value = null
  successMsg.value = null

  const cleanName = sanitizeInput(storeName.value)
  const cleanUrl = storeUrl.value.trim()

  if (!cleanName || cleanName.length < 3) {
    localError.value = 'El nombre de la tienda oficial debe tener al menos 3 caracteres.'
    return
  }

  if (cleanUrl && !isValidHttpsUrl(cleanUrl)) {
    localError.value = 'La URL del sitio web debe ser un enlace válido con protocolo https:// (ej: https://techchile.cl).'
    return
  }

  isSubmitting.value = true
  const res = await productStore.registerStore({
    store_name: cleanName,
    store_url: cleanUrl,
  })
  isSubmitting.value = false

  if (res.success) {
    if (authStore.user && res.data) {
      authStore.user.user_profile = res.data
    } else {
      await authStore.checkAuth()
    }
    const status = res.data?.official_store_status
    successMsg.value =
      status === 'PENDING'
        ? 'Solicitud enviada. Tu tienda oficial está en revisión por administración.'
        : '¡Tienda oficial registrada exitosamente!'
    setTimeout(() => {
      productStore.closeRegisterStoreModal()
    }, 1200)
  } else {
    localError.value = res.error || 'No se pudo registrar la tienda oficial.'
  }
}
</script>

<template>
  <div
    v-if="productStore.registerStoreModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200"
  >
    <div class="bg-brand-surface rounded-2xl max-w-md w-full shadow-2xl border border-brand-border overflow-hidden">
      <!-- Modal Header -->
      <div class="bg-gradient-to-r from-slate-900 to-slate-800 text-white p-5 flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-xl bg-amber-400/20 text-amber-300 flex items-center justify-center">
            <Store class="w-5 h-5" />
          </div>
          <div>
            <h3 class="font-bold text-base leading-tight">Registra tu Tienda Oficial</h3>
            <p class="text-[11px] text-slate-300">Insignia comercial y enlace web para tus productos</p>
          </div>
        </div>
        <button
          @click="productStore.closeRegisterStoreModal()"
          class="text-slate-400 hover:text-white p-1 rounded-lg transition-colors cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Form Body -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
        <!-- Pending Verification Status Notice -->
        <div
          v-if="isStorePending"
          class="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center gap-2"
        >
          <Clock class="w-4 h-4 text-amber-600 shrink-0" />
          <span>Solicitud en revisión por administración</span>
        </div>

        <!-- Success Banner -->
        <div
          v-if="successMsg"
          class="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2"
        >
          <CheckCircle2 class="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{{ successMsg }}</span>
        </div>

        <!-- Error Banner -->
        <div
          v-if="localError"
          class="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2"
        >
          <AlertCircle class="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
          <span>{{ localError }}</span>
        </div>

        <div class="text-xs text-slate-600 bg-blue-50 border border-blue-200 p-3 rounded-xl space-y-1">
          <p class="font-bold text-blue-900 flex items-center gap-1.5">
            <CheckCircle2 class="w-3.5 h-3.5 text-blue-600" />
            Beneficios de la Tienda Oficial:
          </p>
          <ul class="list-disc list-inside space-y-0.5 text-[11px] text-blue-800 pl-1">
            <li>Tus productos destacarán con la etiqueta <strong>"Tienda oficial: [Nombre]"</strong>.</li>
            <li>Si añades una URL, los compradores podrán hacer clic y visitar tu sitio web.</li>
          </ul>
        </div>

        <!-- Nombre de la Tienda -->
        <div class="space-y-1">
          <label class="block text-xs font-bold text-slate-700">
            Nombre de la Tienda Oficial <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <Store class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              v-model="storeName"
              type="text"
              @input="onNameInput"
              placeholder="Ej: TechChile Store, Sony Oficial Chile"
              class="w-full bg-slate-50 border border-brand-border focus:border-brand-accent focus:bg-white rounded-lg pl-9 pr-3 py-2 text-xs text-slate-800 focus:outline-none"
            />
          </div>
        </div>

        <!-- URL de la Tienda -->
        <div class="space-y-1">
          <label class="block text-xs font-bold text-slate-700">
            URL del Sitio Web Oficial (Opcional, solo https://)
          </label>
          <div class="relative">
            <Globe class="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              v-model="storeUrl"
              type="url"
              @input="onUrlInput"
              placeholder="Ej: https://techchile.cl"
              class="w-full bg-slate-50 border border-brand-border focus:border-brand-accent focus:bg-white rounded-lg pl-9 pr-3 py-2 text-xs text-slate-800 focus:outline-none"
            />
          </div>
          <p class="text-[10px] text-slate-400">
            Permite a los usuarios acceder directamente a tu tienda al hacer clic en "Tienda oficial: x".
          </p>
        </div>

        <div class="pt-2 flex items-center justify-end gap-2">
          <button
            type="button"
            @click="productStore.closeRegisterStoreModal()"
            class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 transition-colors cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="isSubmitting"
            class="bg-brand-accent hover:bg-brand-accent-hover text-white font-bold text-xs py-2.5 px-5 rounded-xl transition-all shadow-md disabled:opacity-50 cursor-pointer"
          >
            {{ isSubmitting ? 'Guardando...' : 'Guardar Tienda Oficial' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
