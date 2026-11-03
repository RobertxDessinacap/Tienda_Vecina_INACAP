<script setup>
import { computed } from 'vue'
import {
  X,
  Zap,
  Star,
  ShieldCheck,
  Truck,
  RotateCcw,
  CheckCircle2,
  Award,
  CreditCard,
} from 'lucide-vue-next'
import { useProductStore } from '../stores/products'

const productStore = useProductStore()
const product = computed(() => productStore.selectedProduct)

function formatCLP(amount) {
  if (amount == null) return '$ 0'
  return '$ ' + Math.round(amount).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

const installmentValue = computed(() => {
  if (!product.value) return ''
  const parts = product.value.installments || 6
  return formatCLP(product.value.price / parts)
})

function handleBuy() {
  alert(`¡Gracias por tu compra simulada de: "${product.value.title}"!\nTransacción protegida por el estándar de seguridad ISO 27001.`)
}
</script>

<template>
  <div
    v-if="productStore.detailModalOpen && product"
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-2xs overflow-y-auto"
  >
    <div
      class="bg-white rounded-lg shadow-2xl max-w-4xl w-full overflow-hidden border border-gray-200 relative animate-in fade-in zoom-in-95 duration-200 my-auto"
    >
      <!-- Close Button -->
      <button
        @click="productStore.closeDetail"
        class="absolute top-3 right-3 z-10 w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 transition-colors"
      >
        <X class="w-4 h-4" />
      </button>

      <div class="grid grid-cols-1 md:grid-cols-12 gap-6 p-6">
        <!-- Left: Product Image & Gallery View -->
        <div class="md:col-span-7 flex flex-col items-center justify-center bg-gray-50/50 rounded-lg p-6 border border-gray-100">
          <div class="w-full aspect-square max-h-[380px] flex items-center justify-center">
            <img
              :src="product.image_url"
              :alt="product.title"
              class="max-w-full max-h-full object-contain hover:scale-105 transition-transform duration-300"
            />
          </div>
          <!-- Security guarantee seal -->
          <div class="mt-4 flex items-center gap-2 text-xs text-gray-500 bg-white px-3 py-1.5 rounded-full border border-gray-200 shadow-2xs">
            <ShieldCheck class="w-4 h-4 text-emerald-600" />
            <span>Compra Segura y Cifrada - Estándar ISO 27001</span>
          </div>
        </div>

        <!-- Right: Purchase Details & Seller Proxy -->
        <div class="md:col-span-5 flex flex-col justify-between space-y-4">
          <!-- Header details -->
          <div>
            <div class="flex items-center gap-2 text-xs text-gray-500 mb-1">
              <span>Nuevo</span>
              <span>|</span>
              <span>{{ product.reviews_count * 3 }} vendidos</span>
            </div>

            <h1 class="text-lg md:text-xl font-bold text-gray-900 leading-snug">
              {{ product.title }}
            </h1>

            <!-- Rating -->
            <div class="flex items-center gap-1.5 mt-2 text-xs">
              <div class="flex items-center text-amber-500">
                <Star class="w-4 h-4 fill-amber-400" />
                <span class="font-bold ml-1 text-gray-800">{{ product.rating }}</span>
              </div>
              <span class="text-gray-400">({{ product.reviews_count }} opiniones)</span>
            </div>

            <!-- Price -->
            <div class="mt-3.5 space-y-1">
              <div v-if="product.original_price && product.original_price > product.price" class="text-xs text-gray-400 line-through">
                {{ formatCLP(product.original_price) }}
              </div>
              <div class="flex items-baseline gap-3">
                <span class="text-3xl font-extrabold text-gray-900">
                  {{ formatCLP(product.price) }}
                </span>
                <span v-if="product.discount_percentage > 0" class="text-sm font-bold text-[#00A650] bg-emerald-50 px-2 py-0.5 rounded-xs">
                  {{ product.discount_percentage }}% OFF
                </span>
              </div>
              <p class="text-xs text-gray-600">
                en <span class="font-bold text-gray-800">{{ product.installments }} cuotas de {{ installmentValue }}</span> sin interés
              </p>
            </div>

            <!-- Shipping & Warranty -->
            <div class="mt-4 space-y-2.5 text-xs">
              <div class="flex items-start gap-2.5">
                <Truck class="w-4 h-4 text-[#00A650] shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold text-[#00A650]">Llega gratis mañana</span>
                  <p class="text-gray-500 text-[11px]">Enviado a través de Mercado Envíos</p>
                </div>
              </div>
              <div class="flex items-start gap-2.5">
                <RotateCcw class="w-4 h-4 text-[#00A650] shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold text-[#00A650]">Devolución gratis</span>
                  <p class="text-gray-500 text-[11px]">Tienes 30 días desde que lo recibes</p>
                </div>
              </div>
            </div>

            <!-- Stock status -->
            <div class="mt-3 text-xs text-gray-700">
              <span class="font-bold">Stock disponible: </span>
              <span class="text-gray-900 font-semibold">{{ product.stock }} unidades</span>
            </div>
          </div>

          <!-- Description Box -->
          <div class="bg-gray-50 p-3 rounded-md text-xs text-gray-700 max-h-28 overflow-y-auto border border-gray-200">
            <span class="font-bold block text-gray-900 mb-1">Descripción:</span>
            <p class="whitespace-pre-line leading-relaxed">{{ product.description }}</p>
          </div>

          <!-- Intermediate Account Seller Information (ISO 27001) -->
          <div class="bg-blue-50/70 border border-blue-200/80 rounded-md p-3 text-xs space-y-1.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5">
                <Award class="w-4 h-4 text-blue-700" />
                <span class="font-bold text-gray-900">Vendedor: {{ product.seller_alias }}</span>
              </div>
              <span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                Rep: {{ product.seller_reputation }} / 5.0
              </span>
            </div>
            <p class="text-[11px] text-gray-600 leading-tight">
              Identidad protegida mediante Cuenta Intermedia Seudónima (ISO/IEC 27001). Tus datos y los del vendedor se encuentran resguardados.
            </p>
          </div>

          <!-- Action Buttons -->
          <div class="space-y-2 pt-2">
            <button
              @click="handleBuy"
              class="w-full bg-[#3483FA] hover:bg-[#2968C8] text-white font-bold py-2.5 rounded-md text-sm transition-colors shadow-xs"
            >
              Comprar ahora
            </button>
            <button
              @click="alert('Producto añadido al carrito.')"
              class="w-full bg-blue-50 hover:bg-blue-100 text-[#3483FA] font-bold py-2.5 rounded-md text-sm transition-colors border border-blue-200"
            >
              Agregar al carrito
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
