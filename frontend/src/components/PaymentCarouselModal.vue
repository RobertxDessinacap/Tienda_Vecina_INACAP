<script setup>
import { ref, computed } from 'vue'
import {
  X,
  CreditCard,
  Wallet,
  Building2,
  Smartphone,
  ShieldCheck,
  CheckCircle2,
  Lock,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Printer,
  Sparkles,
} from 'lucide-vue-next'
import { useCartStore } from '../stores/cart'
import { useProductStore } from '../stores/products'

const cartStore = useCartStore()
const productStore = useProductStore()

const paymentMethods = [
  {
    id: 'WEBPAY_PLUS',
    name: 'Transbank Webpay Plus',
    badge: 'Recomendado Transbank',
    tagline: 'Tarjetas de Débito (Redcompra), Crédito y Prepago chilenas',
    icon: CreditCard,
    accent: 'border-red-600 bg-red-50/40 text-red-700',
    headerBg: 'bg-gradient-to-r from-red-600 to-rose-700 text-white',
    benefits: ['Aprobación inmediata', 'Cuotas sin interés', 'Seguridad 3D Secure oficial'],
  },
  {
    id: 'MERCADO_PAGO',
    name: 'Mercado Pago',
    badge: 'Hasta 6 cuotas',
    tagline: 'Dinero en cuenta Mercado Pago y billetera digital',
    icon: Wallet,
    accent: 'border-sky-500 bg-sky-50/40 text-sky-700',
    headerBg: 'bg-gradient-to-r from-sky-400 to-sky-600 text-white',
    benefits: ['Protección al comprador', 'Paga con 1 clic', 'Tarjetas guardadas'],
  },
  {
    id: 'TRANSFER',
    name: 'Transferencia Bancaria Inmediata',
    badge: 'Sin Comisión',
    tagline: 'BancoEstado, Santander, Banco de Chile, BCI',
    icon: Building2,
    accent: 'border-emerald-600 bg-emerald-50/40 text-emerald-700',
    headerBg: 'bg-gradient-to-r from-emerald-600 to-teal-700 text-white',
    benefits: ['Sin intermediarios', 'Confirmación por Khipu/Webpay', 'Conciliación automática'],
  },
  {
    id: 'PREPAY',
    name: 'Tarjetas de Prepago Digital',
    badge: '100% Digital',
    tagline: 'Tenpo, Mach, Dale Coopeuch, Copec Pay',
    icon: Smartphone,
    accent: 'border-purple-600 bg-purple-50/40 text-purple-700',
    headerBg: 'bg-gradient-to-r from-purple-600 to-indigo-700 text-white',
    benefits: ['Sin cuenta corriente', 'Carga al instante', 'Sin cobros sorpresa'],
  },
]

const activeIndex = ref(0)
const selectedMethod = computed(() => paymentMethods[activeIndex.value])

function nextMethod() {
  activeIndex.value = (activeIndex.value + 1) % paymentMethods.length
}

function prevMethod() {
  activeIndex.value = (activeIndex.value - 1 + paymentMethods.length) % paymentMethods.length
}

function selectMethod(idx) {
  activeIndex.value = idx
}

function formatCLP(amount) {
  if (amount == null) return '$ 0'
  return '$ ' + Math.round(amount).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

const totalAmountFormatted = computed(() => {
  if (cartStore.backendCalculation?.total != null) {
    return formatCLP(cartStore.backendCalculation.total)
  }
  const sum = cartStore.items.reduce((acc, it) => acc + (it.product.price * it.quantity), 0)
  return formatCLP(sum)
})

async function handleInitTransbank() {
  await cartStore.initPayment(selectedMethod.value.id)
}

async function handleCommitTransbank() {
  const res = await cartStore.commitPayment()
  if (res?.success) {
    productStore.fetchProducts() // Refrescar stock en catálogo
  }
}

function printVoucher() {
  window.print()
}
</script>

<template>
  <div
    v-if="cartStore.paymentModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto"
  >
    <div
      class="bg-brand-surface rounded-2xl shadow-xl max-w-xl w-full overflow-hidden border border-brand-border relative animate-in fade-in zoom-in-95 duration-200 my-auto text-xs"
    >
      <!-- Modal Header -->
      <div class="bg-brand-primary px-5 py-3.5 flex items-center justify-between border-b border-brand-primary-border">
        <div class="flex items-center gap-2">
          <CreditCard class="w-5 h-5 text-brand-primary-text" />
          <h2 class="text-sm font-bold text-slate-900">
            Carrusel de Medios de Pago & Transbank
          </h2>
        </div>
        <button
          @click="cartStore.closePaymentModal"
          class="w-7 h-7 rounded-full bg-brand-surface/80 hover:bg-brand-surface flex items-center justify-center text-slate-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- ================= PAGO APROBADO: VOUCHER TRANSBANK ================= -->
      <div v-if="cartStore.paymentVoucher" class="p-6 space-y-4 text-center">
        <div class="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-xs">
          <CheckCircle2 class="w-8 h-8" />
        </div>
        <div>
          <span class="inline-block bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider mb-1">
            Transacción Autorizada con Éxito
          </span>
          <h3 class="text-lg font-bold text-slate-900">¡Pago Confirmado por Transbank!</h3>
          <p class="text-slate-500 text-xs">Tu orden de compra ha sido procesada de forma segura.</p>
        </div>

        <!-- Voucher Details -->
        <div class="bg-brand-surface-subtle p-4 rounded-xl border border-brand-border text-left space-y-2 text-xs">
          <div class="flex justify-between border-b border-brand-border pb-1.5">
            <span class="text-slate-500">Orden de Compra:</span>
            <span class="font-mono font-bold text-slate-800">{{ cartStore.paymentVoucher.buy_order }}</span>
          </div>
          <div class="flex justify-between border-b border-brand-border pb-1.5">
            <span class="text-slate-500">Código Autorización:</span>
            <span class="font-mono font-bold text-emerald-600">{{ cartStore.paymentVoucher.authorization_code }}</span>
          </div>
          <div class="flex justify-between border-b border-brand-border pb-1.5">
            <span class="text-slate-500">Medio de Pago:</span>
            <span class="font-semibold text-slate-800">Transbank Webpay Plus (Redcompra Débito)</span>
          </div>
          <div class="flex justify-between border-b border-brand-border pb-1.5">
            <span class="text-slate-500">Tarjeta Utilizada:</span>
            <span class="font-mono text-slate-800">•••• •••• •••• {{ cartStore.paymentVoucher.card_number || '6623' }}</span>
          </div>
          <div class="flex justify-between border-b border-brand-border pb-1.5">
            <span class="text-slate-500">Monto Transaccionado:</span>
            <span class="text-base font-bold text-slate-900">{{ formatCLP(cartStore.paymentVoucher.amount) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-500">Estado de Operación:</span>
            <span class="text-emerald-700 font-bold uppercase">{{ cartStore.paymentVoucher.status }}</span>
          </div>
        </div>

        <!-- Buttons -->
        <div class="flex gap-2 pt-2">
          <button
            @click="printVoucher"
            class="flex-1 bg-brand-surface-subtle hover:bg-brand-primary-subtle text-brand-primary-text font-semibold py-2 rounded-lg border border-brand-border flex items-center justify-center gap-1.5 transition-colors"
          >
            <Printer class="w-4 h-4" />
            <span>Imprimir Comprobante</span>
          </button>
          <button
            @click="cartStore.closePaymentModal(); productStore.goToCatalog()"
            class="flex-1 bg-brand-accent hover:bg-brand-accent-hover text-white font-bold py-2 rounded-lg transition-colors"
          >
            Volver a la Tienda
          </button>
        </div>
      </div>

      <!-- ================= PANTALLA OFICIAL TRANSBANK EN CURSO ================= -->
      <div v-else-if="cartStore.transbankData" class="p-6 space-y-4">
        <!-- Transbank Official Header -->
        <div class="bg-red-600 text-white p-4 rounded-xl flex items-center justify-between shadow-xs">
          <div>
            <div class="text-[10px] uppercase font-bold tracking-wider text-red-200">Plataforma Oficial</div>
            <h3 class="text-base font-extrabold tracking-tight">Transbank Webpay Plus</h3>
          </div>
          <Lock class="w-6 h-6 text-red-200" />
        </div>

        <div class="bg-brand-surface-subtle p-3.5 rounded-xl border border-brand-border space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-slate-500">Orden de Compra:</span>
            <span class="font-mono font-bold text-slate-800">{{ cartStore.transbankData.buy_order }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-slate-500">Monto a Pagar:</span>
            <span class="text-base font-bold text-slate-900">{{ formatCLP(cartStore.transbankData.amount) }}</span>
          </div>
        </div>

        <!-- Simulated Webpay payment interactive form -->
        <div class="border border-brand-border rounded-xl p-4 bg-brand-surface space-y-3">
          <span class="text-xs font-bold text-slate-800 block">Simulador Oficial de Pago Seguro Webpay Plus</span>
          <p class="text-[11px] text-slate-500">
            Ingresa los datos de tu tarjeta de prueba para completar la transacción:
          </p>
          <div class="space-y-2">
            <div>
              <label class="block text-[11px] font-semibold text-slate-700 mb-0.5">Número de Tarjeta de Débito (Redcompra)</label>
              <input
                type="text"
                value="•••• •••• •••• 6623 (Débito Aprobada)"
                readonly
                class="w-full bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 font-mono"
              />
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-700 mb-0.5">Clave de Seguridad Webpay</label>
              <input
                type="password"
                value="1213"
                readonly
                class="w-full bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 font-mono"
              />
            </div>
          </div>

          <button
            @click="handleCommitTransbank"
            :disabled="cartStore.paymentLoading"
            class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-lg text-xs uppercase tracking-wider transition-colors shadow-xs flex items-center justify-center gap-1.5"
          >
            <span v-if="cartStore.paymentLoading">Autorizando con el Banco emisor...</span>
            <span v-else class="flex items-center gap-1.5">
              <CheckCircle2 class="w-4 h-4" />
              <span>Pagar y Autorizar Transacción Transbank</span>
            </span>
          </button>
        </div>
      </div>

      <!-- ================= CARRUSEL DE MEDIOS DE PAGO ================= -->
      <div v-else class="p-5 space-y-4">
        <!-- Order Summary Top -->
        <div class="flex items-center justify-between bg-brand-surface-subtle p-3 rounded-xl border border-brand-border">
          <div>
            <span class="text-slate-500 block text-[11px]">Total a Pagar (Cálculo Inviolable ORM):</span>
            <span class="text-base font-extrabold text-slate-900">{{ totalAmountFormatted }}</span>
          </div>
          <div class="flex items-center gap-1 text-[11px] text-emerald-700 font-bold bg-brand-surface px-2.5 py-1 rounded-full border border-brand-border shadow-2xs">
            <ShieldCheck class="w-3.5 h-3.5 text-emerald-600" />
            <span>Sin Recargos Ocultos</span>
          </div>
        </div>

        <!-- Carousel Presentation Slider -->
        <div class="relative">
          <!-- Card Carousel Slide -->
          <div
            :class="selectedMethod.accent"
            class="rounded-xl border-2 p-5 transition-all duration-300 shadow-xs relative overflow-hidden"
          >
            <!-- Badge -->
            <div class="flex items-center justify-between mb-3">
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider bg-white/80 shadow-2xs">
                {{ selectedMethod.badge }}
              </span>
              <span class="text-[11px] font-semibold opacity-75">
                Opción {{ activeIndex + 1 }} de {{ paymentMethods.length }}
              </span>
            </div>

            <!-- Title & Icon -->
            <div class="flex items-center gap-3 mb-2">
              <div class="w-10 h-10 rounded-lg bg-white shadow-xs flex items-center justify-center">
                <component :is="selectedMethod.icon" class="w-5 h-5" />
              </div>
              <div>
                <h4 class="text-sm font-bold text-slate-900">{{ selectedMethod.name }}</h4>
                <p class="text-[11px] opacity-90 leading-tight">{{ selectedMethod.tagline }}</p>
              </div>
            </div>

            <!-- Benefits List -->
            <ul class="mt-3 space-y-1.5 pt-3 border-t border-current/20 text-[11px]">
              <li v-for="(benefit, bIdx) in selectedMethod.benefits" :key="bIdx" class="flex items-center gap-1.5">
                <CheckCircle2 class="w-3.5 h-3.5 shrink-0 opacity-80" />
                <span>{{ benefit }}</span>
              </li>
            </ul>
          </div>

          <!-- Navigation Arrow Buttons -->
          <button
            @click="prevMethod"
            class="absolute left-1 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-brand-surface/90 hover:bg-brand-surface text-slate-700 shadow-md border border-brand-border flex items-center justify-center transition-all"
            title="Anterior"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <button
            @click="nextMethod"
            class="absolute right-1 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-brand-surface/90 hover:bg-brand-surface text-slate-700 shadow-md border border-brand-border flex items-center justify-center transition-all"
            title="Siguiente"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>

        <!-- Carousel Dots / Thumbnails -->
        <div class="flex items-center justify-center gap-2 pt-1">
          <button
            v-for="(method, idx) in paymentMethods"
            :key="method.id"
            @click="selectMethod(idx)"
            :class="[activeIndex === idx ? 'w-6 bg-brand-accent' : 'w-2 bg-brand-primary-border hover:bg-brand-primary-hover']"
            class="h-2 rounded-full transition-all"
            :title="method.name"
          ></button>
        </div>

        <!-- Action Button -->
        <div class="pt-2">
          <button
            @click="handleInitTransbank"
            :disabled="cartStore.paymentLoading"
            class="w-full bg-brand-accent hover:bg-brand-accent-hover text-white font-bold py-2.5 rounded-lg text-xs uppercase tracking-wider transition-colors shadow-xs flex items-center justify-center gap-2"
          >
            <span v-if="cartStore.paymentLoading">Conectando con pasarela...</span>
            <span v-else class="flex items-center gap-1.5">
              <span>Continuar con {{ selectedMethod.name }}</span>
              <ExternalLink class="w-3.5 h-3.5" />
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
