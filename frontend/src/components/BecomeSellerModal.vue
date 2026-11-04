<script setup>
import { ref } from 'vue'
import {
  X,
  Store,
  Tag,
  DollarSign,
  Layers,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  TrendingUp,
  Package,
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useProductStore } from '../stores/products'

const authStore = useAuthStore()
const productStore = useProductStore()

const upgrading = ref(false)
const errorMessage = ref('')

async function handleUpgrade() {
  upgrading.value = true
  errorMessage.value = ''
  
  const result = await authStore.upgradeToSeller()
  upgrading.value = false

  if (result.success) {
    // Abrir de inmediato el modal de creación de producto
    productStore.openCreateModal()
  } else {
    errorMessage.value = result.error || 'No se pudo actualizar tu perfil. Intenta nuevamente.'
  }
}
</script>

<template>
  <div
    v-if="authStore.becomeSellerModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/50 backdrop-blur-xs overflow-y-auto"
  >
    <div
      class="bg-brand-surface rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-brand-border relative animate-in fade-in zoom-in-95 duration-200 my-auto text-xs"
    >
      <!-- Modal Header -->
      <div class="bg-brand-primary px-6 py-4 flex items-center justify-between border-b border-brand-primary-border">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-brand-surface flex items-center justify-center shadow-xs">
            <Store class="w-5 h-5 text-brand-accent" />
          </div>
          <div>
            <h2 class="text-sm font-bold text-slate-900 leading-tight">
              ¡Comienza a Vender en Mercado Inacap!
            </h2>
            <span class="text-[10px] text-brand-primary-text font-semibold">
              Activa tu perfil de vendedor en 1 clic
            </span>
          </div>
        </div>
        <button
          @click="authStore.closeBecomeSellerModal"
          class="w-7 h-7 rounded-full bg-brand-surface/80 hover:bg-brand-surface flex items-center justify-center text-slate-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 space-y-4">
        <!-- Welcoming Callout -->
        <div class="bg-brand-primary-subtle p-3.5 rounded-xl border border-brand-primary-border flex items-start gap-3">
          <Sparkles class="w-5 h-5 text-brand-accent shrink-0 mt-0.5" />
          <p class="text-slate-700 text-xs leading-relaxed">
            Tu cuenta actual está registrada como <strong class="text-slate-900">Comprador</strong>. 
            Conviértete en <strong class="text-brand-primary-text font-bold">Vendedor Autorizado</strong> y publica tus productos ante miles de compradores en todo Chile.
          </p>
        </div>

        <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-xs">
          {{ errorMessage }}
        </div>

        <!-- Benefits Grid -->
        <div>
          <span class="text-[11px] font-bold text-slate-600 uppercase tracking-wider block mb-2.5">
            Beneficios Exclusivos para Vendedores:
          </span>

          <div class="space-y-2.5">
            <!-- Benefit 1: Categorías -->
            <div class="flex items-start gap-3 p-3 rounded-xl bg-brand-surface-subtle border border-brand-border">
              <div class="w-8 h-8 rounded-lg bg-brand-primary-subtle flex items-center justify-center shrink-0 mt-0.5">
                <Layers class="w-4 h-4 text-brand-accent" />
              </div>
              <div>
                <strong class="text-slate-900 block text-xs font-bold">
                  Publica en todas las categorías del catálogo
                </strong>
                <p class="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
                  Ubica tus publicaciones en Tecnología, Computación, Ropa, Hogar, Herramientas y más para llegar al público ideal.
                </p>
              </div>
            </div>

            <!-- Benefit 2: Precios Libres y Ofertas -->
            <div class="flex items-start gap-3 p-3 rounded-xl bg-brand-surface-subtle border border-brand-border">
              <div class="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center shrink-0 mt-0.5">
                <DollarSign class="w-4 h-4 text-emerald-600" />
              </div>
              <div>
                <strong class="text-slate-900 block text-xs font-bold">
                  Fija tus propios precios y descuentos
                </strong>
                <p class="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
                  Tú decides cuánto cobrar por tus artículos. Aplica rebajas porcentuales y ofrece facilidades de hasta 12 cuotas.
                </p>
              </div>
            </div>

            <!-- Benefit 3: Control de Stock y Envíos -->
            <div class="flex items-start gap-3 p-3 rounded-xl bg-brand-surface-subtle border border-brand-border">
              <div class="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0 mt-0.5">
                <Package class="w-4 h-4 text-indigo-600" />
              </div>
              <div>
                <strong class="text-slate-900 block text-xs font-bold">
                  Gestión total de inventario y despacho
                </strong>
                <p class="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
                  Controla tu stock disponible en tiempo real y ofrece la opción de Envío Gratis para ganar visibilidad inmediata.
                </p>
              </div>
            </div>

            <!-- Benefit 4: Cobros Seguros Transbank -->
            <div class="flex items-start gap-3 p-3 rounded-xl bg-brand-surface-subtle border border-brand-border">
              <div class="w-8 h-8 rounded-lg bg-sky-50 flex items-center justify-center shrink-0 mt-0.5">
                <ShieldCheck class="w-4 h-4 text-brand-accent" />
              </div>
              <div>
                <strong class="text-slate-900 block text-xs font-bold">
                  Cobros garantizados con Webpay Plus
                </strong>
                <p class="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
                  Tus ventas están respaldadas con autenticación bancaria directa y comprobante digital oficial de compra.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="pt-2 space-y-2">
          <button
            @click="handleUpgrade"
            :disabled="upgrading"
            class="w-full bg-brand-accent hover:bg-brand-accent-hover text-white font-bold py-3 rounded-xl text-xs uppercase tracking-wider transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <span v-if="upgrading">Activando perfil de vendedor...</span>
            <span v-else class="flex items-center gap-2">
              <Store class="w-4 h-4" />
              <span>Convertirme en Vendedor y Publicar Ahora</span>
              <ArrowRight class="w-4 h-4" />
            </span>
          </button>

          <button
            type="button"
            @click="authStore.closeBecomeSellerModal"
            class="w-full py-2 text-slate-500 hover:text-slate-800 text-xs font-semibold text-center transition-colors cursor-pointer"
          >
            Seguir explorando como Comprador
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
