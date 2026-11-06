<script setup>
import { ref, computed, watch } from 'vue'
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

const selectedImageIndex = ref(0)
watch(
  () => product.value,
  () => {
    selectedImageIndex.value = 0
  }
)

const productImages = computed(() => {
  if (!product.value) return []
  if (product.value.images && Array.isArray(product.value.images) && product.value.images.length > 0) {
    return product.value.images
  }
  const u = product.value.display_image_url || product.value.image_url
  return u ? [u] : []
})

const activeImageUrl = computed(() => {
  if (productImages.value.length > 0) {
    return productImages.value[selectedImageIndex.value] || productImages.value[0]
  }
  return product.value?.display_image_url || product.value?.image_url
})

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
  alert(`¡Gracias por tu compra de: "${product.value.title}"!\nTu pedido cuenta con garantía oficial de satisfacción.`)
}
</script>

<template>
  <div
    v-if="productStore.detailModalOpen && product"
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto"
  >
    <div
      class="bg-brand-surface rounded-2xl shadow-xl max-w-4xl w-full overflow-hidden border border-brand-border relative animate-in fade-in zoom-in-95 duration-200 my-auto"
    >
      <!-- Close Button -->
      <button
        @click="productStore.closeDetail"
        class="absolute top-3 right-3 z-10 w-8 h-8 rounded-full bg-brand-surface-subtle hover:bg-brand-primary-subtle flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors"
      >
        <X class="w-4 h-4" />
      </button>

      <div class="grid grid-cols-1 md:grid-cols-12 gap-6 p-6">
        <!-- Left: Product Image & Gallery View -->
        <div class="md:col-span-7 flex flex-col items-center justify-center bg-brand-surface-subtle rounded-xl p-6 border border-brand-border">
          <div class="w-full aspect-square max-h-[380px] flex items-center justify-center">
            <img
              :src="activeImageUrl"
              :alt="product.title"
              class="max-w-full max-h-full object-contain hover:scale-105 transition-transform duration-300"
            />
          </div>

          <!-- Thumbnails (if > 1 photo) -->
          <div v-if="productImages.length > 1" class="w-full flex items-center justify-center gap-2 mt-3 overflow-x-auto py-1">
            <button
              v-for="(img, idx) in productImages"
              :key="idx"
              type="button"
              @click="selectedImageIndex = idx"
              :class="[
                selectedImageIndex === idx
                  ? 'border-brand-accent ring-2 ring-brand-accent/30'
                  : 'border-brand-border hover:border-slate-400 opacity-70 hover:opacity-100'
              ]"
              class="w-12 h-10 rounded-md border-2 overflow-hidden bg-brand-surface shrink-0 transition-all cursor-pointer p-0.5"
            >
              <img :src="img" :alt="`Foto ${idx + 1}`" class="w-full h-full object-cover rounded" />
            </button>
          </div>
          <!-- Security guarantee seal -->
          <div class="mt-4 flex items-center gap-2 text-xs text-brand-primary-text bg-brand-surface px-3 py-1.5 rounded-full border border-brand-primary-border shadow-2xs">
            <ShieldCheck class="w-4 h-4 text-brand-accent" />
            <span>Compra Segura y Garantizada</span>
          </div>
        </div>

        <!-- Right: Purchase Details & Seller Proxy -->
        <div class="md:col-span-5 flex flex-col justify-between space-y-4">
          <!-- Header details -->
          <div>
            <div class="flex items-center gap-2 text-xs text-slate-400 mb-1">
              <span>Nuevo</span>
              <span>|</span>
              <span>{{ product.reviews_count * 3 }} vendidos</span>
            </div>

            <h1 class="text-lg md:text-xl font-bold text-slate-900 leading-snug">
              {{ product.title }}
            </h1>

            <!-- Rating -->
            <div class="flex items-center gap-1.5 mt-2 text-xs">
              <template v-if="product.reviews_count > 0 && product.rating">
                <div class="flex items-center text-amber-500">
                  <Star class="w-4 h-4 fill-amber-400" />
                  <span class="font-bold ml-1 text-slate-800">{{ product.rating }}</span>
                </div>
                <span class="text-slate-400">({{ product.reviews_count }} opiniones)</span>
              </template>
              <template v-else>
                <span class="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                  Nuevo | Sin valoraciones aún
                </span>
              </template>
            </div>

            <!-- Price -->
            <div class="mt-3.5 space-y-1">
              <div v-if="product.original_price && product.original_price > product.price" class="text-xs text-slate-400 line-through">
                {{ formatCLP(product.original_price) }}
              </div>
              <div class="flex items-baseline gap-3">
                <span class="text-3xl font-extrabold text-slate-900">
                  {{ formatCLP(product.price) }}
                </span>
                <span v-if="product.discount_percentage > 0" class="text-sm font-bold text-brand-accent bg-brand-accent-soft px-2 py-0.5 rounded-full">
                  {{ product.discount_percentage }}% OFF
                </span>
              </div>
              <p class="text-xs text-slate-600">
                en <span class="font-bold text-slate-800">{{ product.installments }} cuotas de {{ installmentValue }}</span> sin interés
              </p>
            </div>

            <!-- Shipping & Warranty -->
            <div class="mt-4 space-y-2.5 text-xs">
              <div class="flex items-start gap-2.5">
                <Truck class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold text-emerald-600">Llega gratis mañana</span>
                  <p class="text-slate-500 text-[11px]">Enviado a través de Mercado Envíos</p>
                </div>
              </div>
              <div class="flex items-start gap-2.5">
                <RotateCcw class="w-4 h-4 text-brand-accent shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold text-brand-primary-text">Devolución gratis</span>
                  <p class="text-slate-500 text-[11px]">Tienes 30 días desde que lo recibes</p>
                </div>
              </div>
            </div>

            <!-- Stock status -->
            <div class="mt-3 text-xs text-slate-700">
              <span class="font-bold">Stock disponible: </span>
              <span class="text-slate-900 font-semibold">{{ product.stock }} unidades</span>
            </div>
          </div>

          <!-- Description Box -->
          <div class="bg-brand-surface-subtle p-3 rounded-lg text-xs text-slate-700 max-h-28 overflow-y-auto border border-brand-border">
            <span class="font-bold block text-slate-900 mb-1">Descripción:</span>
            <p class="whitespace-pre-line leading-relaxed">{{ product.description }}</p>
          </div>

          <!-- Intermediate Account Seller Information (ISO 27001) -->
          <div class="bg-brand-primary-subtle border border-brand-primary-border rounded-xl p-3 text-xs space-y-1.5 shadow-2xs">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5">
                <Award class="w-4 h-4 text-brand-accent" />
                <span class="font-bold text-slate-900">Vendedor: {{ product.seller_alias }}</span>
              </div>
              <span class="bg-brand-primary text-brand-primary-text text-[10px] font-bold px-2 py-0.5 rounded-full">
                Rep: {{ product.seller_reputation }} / 5.0
              </span>
            </div>
            <p class="text-[11px] text-slate-600 leading-tight">
              Vendedor verificado con entregas a tiempo y compras 100% protegidas.
            </p>
          </div>

          <!-- Action Buttons -->
          <div class="space-y-2 pt-2">
            <button
              @click="handleBuy"
              class="w-full bg-brand-accent hover:bg-brand-accent-hover text-white font-bold py-2.5 rounded-lg text-sm transition-colors shadow-xs"
            >
              Comprar ahora
            </button>
            <button
              @click="alert('Producto añadido al carrito.')"
              class="w-full bg-brand-accent-soft hover:bg-brand-primary-subtle text-brand-accent font-bold py-2.5 rounded-lg text-sm transition-colors border border-brand-accent-border"
            >
              Agregar al carrito
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
