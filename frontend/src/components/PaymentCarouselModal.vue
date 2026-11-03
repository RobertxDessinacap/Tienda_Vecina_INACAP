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
    accent: 'border-blue-500 bg-blue-50/40 text-blue-700',
    headerBg: 'bg-gradient-to-r from-sky-500 to-blue-600 text-white',
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
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-2xs overflow-y-auto"
  >
    <div
      class="bg-white rounded-lg shadow-2xl max-w-xl w-full overflow-hidden border border-gray-200 relative animate-in fade-in zoom-in-95 duration-200 my-auto text-xs"
    >
      <!-- Modal Header -->
      <div class="bg-[#FFE600] px-5 py-3.5 flex items-center justify-between border-b border-yellow-400">
        <div class="flex items-center gap-2">
          <CreditCard class="w-5 h-5 text-gray-900" />
          <h2 class="text-sm font-bold text-gray-900">
            Carrusel de Medios de Pago & Transbank
          </h2>
        </div>
        <button
          @click="cartStore.closePaymentModal"
          class="w-7 h-7 rounded-full bg-white/80 hover:bg-white flex items-center justify-center text-gray-700 transition-colors"
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
          <h3 class="text-lg font-bold text-gray-900">¡Pago Confirmado por Transbank!</h3>
          <p class="text-gray-500 text-xs">Tu orden de compra ha sido procesada de forma segura.</p>
        </div>

        <!-- Voucher Card -->
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 text-left font-mono space-y-2 text-[11px] shadow-2xs">
          <div class="flex justify-between pb-2 border-b border-gray-200">
            <span class="text-gray-500">Comercio:</span>
            <span class="font-bold text-gray-800">INACAP E-COMMERCE CHILE</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">Orden de Compra:</span>
            <span class="font-bold text-gray-900">{{ cartStore.paymentVoucher.buy_order }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">Código de Autorización:</span>
            <span class="font-bold text-emerald-700">{{ cartStore.paymentVoucher.authorization_code }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">Monto Aprobado:</span>
            <span class="font-bold text-gray-900">{{ formatCLP(cartStore.paymentVoucher.amount) }} CLP</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">Tarjeta Utilizada:</span>
            <span class="font-semibold text-gray-800">**** **** **** {{ cartStore.paymentVoucher.card_last_digits }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">Tipo de Pago:</span>
            <span class="font-semibold text-gray-800">{{ cartStore.paymentVoucher.payment_type }}</span>
          </div>
          <div class="flex justify-between pt-2 border-t border-gray-200 text-[10px] text-gray-400">
            <span>Fecha y Hora:</span>
            <span>{{ new Date(cartStore.paymentVoucher.timestamp).toLocaleString('es-CL') }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-2 pt-2">
          <button
            @click="printVoucher"
            class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-2 rounded-md transition-colors flex items-center justify-center gap-1.5"
          >
            <Printer class="w-4 h-4" />
            <span>Imprimir Comprobante</span>
          </button>
          <button
            @click="cartStore.closePaymentModal(); productStore.goToCatalog()"
            class="flex-1 bg-[#3483FA] hover:bg-blue-600 text-white font-bold py-2 rounded-md transition-colors"
          >
            Volver a la Tienda
          </button>
        </div>
      </div>

      <!-- ================= PANTALLA OFICIAL TRANSBANK EN CURSO ================= -->
      <div v-else-if="cartStore.transbankData" class="p-6 space-y-4">
        <!-- Transbank Official Header -->
        <div class="bg-red-600 text-white p-4 rounded-lg flex items-center justify-between shadow-xs">
          <div>
            <div class="text-[10px] uppercase font-bold tracking-wider text-red-200">Plataforma Oficial</div>
            <h3 class="text-base font-extrabold tracking-tight">Transbank Webpay Plus</h3>
          </div>
          <Lock class="w-6 h-6 text-red-200" />
        </div>

        <div class="bg-gray-50 p-3.5 rounded-lg border border-gray-200 space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-gray-600">Orden de Compra:</span>
            <span class="font-bold text-gray-900">{{ cartStore.transbankData.buy_order }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-gray-600">Monto Total a Pagar:</span>
            <span class="text-base font-extrabold text-gray-900">{{ formatCLP(cartStore.transbankData.total_amount) }}</span>
          </div>
          <div class="flex justify-between text-[11px] text-gray-500">
            <span>Código de Sesión Webpay:</span>
            <span class="font-mono text-gray-700 truncate max-w-[200px]" :title="cartStore.transbankData.token">
              {{ cartStore.transbankData.token }}
            </span>
          </div>
        </div>

        <div class="text-[11px] text-gray-600 bg-blue-50 border border-blue-200 p-3 rounded-md space-y-1">
          <strong class="text-blue-900 block font-bold">Instrucciones de Pago Webpay Plus:</strong>
          <ol class="list-decimal list-inside space-y-0.5 text-blue-800">
            <li>Selecciona tu tipo de tarjeta (Débito Redcompra o Crédito).</li>
            <li>Ingresa las coordenadas o clave de tu banco en la pasarela oficial.</li>
            <li>Transbank autoriza la operación y emite tu comprobante oficial.</li>
          </ol>
        </div>

        <div class="space-y-2 pt-2">
          <button
            @click="handleCommitTransbank"
            :disabled="cartStore.paymentLoading"
            class="w-full bg-[#00A650] hover:bg-emerald-600 text-white font-bold py-2.5 rounded-md text-xs uppercase tracking-wider transition-colors shadow-xs flex items-center justify-center gap-2"
          >
            <span v-if="cartStore.paymentLoading">Procesando pago con Transbank...</span>
            <span v-else class="flex items-center gap-1.5">
              <span>Confirmar y Autorizar Pago Webpay</span>
              <CheckCircle2 class="w-4 h-4" />
            </span>
          </button>
          <button
            @click="cartStore.transbankData = null"
            class="w-full text-gray-500 hover:text-gray-700 text-xs py-1"
          >
            Cancelar y volver a seleccionar medio de pago
          </button>
        </div>
      </div>

      <!-- ================= CARRUSEL DE MEDIOS DE PAGO ================= -->
      <div v-else class="p-5 space-y-4">
        <!-- Total to Pay -->
        <div class="flex items-center justify-between bg-gray-50 p-3 rounded-lg border border-gray-200">
          <div>
            <span class="text-gray-500 text-[11px] block">Total a pagar:</span>
            <span class="text-xl font-black text-gray-900">{{ totalAmountFormatted }}</span>
          </div>
          <div class="flex items-center gap-1.5 text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 font-semibold text-[10px]">
            <ShieldCheck class="w-3.5 h-3.5" />
            <span>Página Segura y Verificada</span>
          </div>
        </div>

        <!-- Carousel Container with Arrows -->
        <div class="relative">
          <div class="text-center mb-2">
            <span class="text-[11px] font-bold text-gray-600 uppercase tracking-wider">
              Desliza y selecciona tu opción de pago:
            </span>
          </div>

          <!-- Carousel Card Display -->
          <div
            :class="[selectedMethod.accent]"
            class="rounded-xl border-2 p-5 shadow-xs transition-all duration-300 relative overflow-hidden"
          >
            <div class="flex items-center justify-between mb-3">
              <span class="bg-white/90 font-bold text-[10px] px-2.5 py-0.5 rounded-full uppercase tracking-wider shadow-2xs">
                {{ selectedMethod.badge }}
              </span>
              <component :is="selectedMethod.icon" class="w-6 h-6" />
            </div>

            <h3 class="text-base font-bold text-gray-900 mb-1">
              {{ selectedMethod.name }}
            </h3>
            <p class="text-gray-600 text-xs mb-3 leading-relaxed">
              {{ selectedMethod.tagline }}
            </p>

            <!-- Benefits list -->
            <ul class="space-y-1 text-[11px] text-gray-700 border-t border-gray-200/80 pt-3">
              <li v-for="b in selectedMethod.benefits" :key="b" class="flex items-center gap-1.5">
                <CheckCircle2 class="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                <span>{{ b }}</span>
              </li>
            </ul>
          </div>

          <!-- Carousel Navigation Arrows -->
          <button
            @click="prevMethod"
            class="absolute left-1 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white/90 hover:bg-white text-gray-700 shadow-md border border-gray-200 flex items-center justify-center transition-all"
            title="Anterior"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <button
            @click="nextMethod"
            class="absolute right-1 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white/90 hover:bg-white text-gray-700 shadow-md border border-gray-200 flex items-center justify-center transition-all"
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
            :class="[activeIndex === idx ? 'w-6 bg-[#3483FA]' : 'w-2 bg-gray-300 hover:bg-gray-400']"
            class="h-2 rounded-full transition-all"
            :title="method.name"
          ></button>
        </div>

        <!-- Action Button -->
        <div class="pt-2">
          <button
            @click="handleInitTransbank"
            :disabled="cartStore.paymentLoading"
            class="w-full bg-[#3483FA] hover:bg-[#2968C8] text-white font-bold py-2.5 rounded-md text-xs uppercase tracking-wider transition-colors shadow-xs flex items-center justify-center gap-2"
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
