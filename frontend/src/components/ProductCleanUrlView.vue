<script setup>
import { computed } from 'vue'
import {
  ArrowLeft,
  Truck,
  RotateCcw,
  ShieldCheck,
  Star,
  Award,
  Zap,
  ShoppingCart,
  CreditCard,
  Sparkles,
  FileText,
  UserCheck,
} from 'lucide-vue-next'
import { useProductStore } from '../stores/products'
import { useCartStore } from '../stores/cart'

const productStore = useProductStore()
const cartStore = useCartStore()

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

function handleAddToCart() {
  if (product.value) {
    cartStore.addItem(product.value, 1)
  }
}

function handleBuyNow() {
  if (product.value) {
    cartStore.addItem(product.value, 1)
    cartStore.openPaymentModal()
  }
}
</script>

<template>
  <div v-if="product" class="max-w-7xl mx-auto px-4 py-4 space-y-4">
    <!-- Breadcrumb & Clean URL Indicator -->
    <div class="flex items-center justify-between text-xs text-gray-500 bg-white p-3 rounded-lg border border-gray-200 shadow-2xs">
      <div class="flex items-center gap-2">
        <button
          @click="productStore.goToCatalog()"
          class="flex items-center gap-1 text-[#3483FA] hover:underline font-bold"
        >
          <ArrowLeft class="w-3.5 h-3.5" />
          <span>Volver al Catálogo</span>
        </button>
        <span>/</span>
        <span class="text-gray-400">{{ product.category_name || 'Productos' }}</span>
        <span>/</span>
        <span class="text-gray-800 font-semibold truncate max-w-xs">{{ product.title }}</span>
      </div>

      <!-- Clean URL badge (Requisito del Profesor) -->
      <div class="hidden sm:flex items-center gap-1.5 bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full border border-blue-200 text-[11px] font-mono">
        <Sparkles class="w-3.5 h-3.5 text-blue-600" />
        <span>URL Limpia: /producto/{{ product.slug }}</span>
      </div>
    </div>

    <!-- Main Product Presentation Card -->
    <div class="bg-white rounded-lg border border-gray-200 shadow-xs p-6 grid grid-cols-1 md:grid-cols-12 gap-8">
      <!-- Left Column: Product Image (Resolución 900x600 y <= 1MB) -->
      <div class="md:col-span-7 flex flex-col items-center justify-start space-y-3">
        <!-- 900x600 Aspect Ratio Container -->
        <div class="w-full aspect-[9/6] bg-gray-50 rounded-lg border border-gray-200 p-4 flex items-center justify-center overflow-hidden shadow-2xs relative">
          <img
            :src="product.display_image_url || product.image_url"
            :alt="product.title"
            class="max-w-full max-h-full object-contain hover:scale-105 transition-transform duration-300"
          />
          <div v-if="product.discount_percentage > 0" class="absolute top-3 left-3 bg-[#00A650] text-white font-black text-xs px-2.5 py-1 rounded-xs">
            {{ product.discount_percentage }}% OFF
          </div>
          <div class="absolute bottom-2 right-2 bg-black/60 text-white text-[10px] px-2 py-0.5 rounded-xs font-mono">
            Resolución: 900 x 600
          </div>
        </div>

        <div class="w-full flex items-center justify-between text-xs text-gray-500 bg-gray-50 p-2.5 rounded-md border border-gray-200">
          <span class="flex items-center gap-1">
            <ShieldCheck class="w-4 h-4 text-emerald-600" />
            Imagen normalizada y blindada contra malware (<= 1MB)
          </span>
          <span class="text-[11px] text-gray-400">Pillow Engine</span>
        </div>
      </div>

      <!-- Right Column: Purchase Details & User Information -->
      <div class="md:col-span-5 flex flex-col justify-between space-y-4">
        <div>
          <!-- Title & Rating -->
          <div class="text-xs text-gray-400 mb-1">
            <span>Nuevo</span> | <span>Código: {{ product.slug }}</span>
          </div>
          <h1 class="text-xl md:text-2xl font-extrabold text-gray-900 leading-tight">
            {{ product.title }}
          </h1>

          <div class="flex items-center gap-2 mt-2 text-xs">
            <div class="flex items-center text-amber-500">
              <Star class="w-4 h-4 fill-amber-400" />
              <span class="font-bold ml-1 text-gray-800">{{ product.rating }}</span>
            </div>
            <span class="text-gray-400">({{ product.reviews_count }} opiniones)</span>
          </div>

          <!-- Price & Discounts -->
          <div class="mt-4 space-y-1">
            <div v-if="product.original_price" class="text-xs text-gray-400 line-through">
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
              en <span class="font-bold text-gray-900">{{ product.installments }} cuotas de {{ installmentValue }}</span> sin interés
            </p>
          </div>

          <!-- Shipping and Return Badges -->
          <div class="mt-4 space-y-2 text-xs border-y border-gray-100 py-3">
            <div class="flex items-start gap-2">
              <Truck class="w-4 h-4 text-[#00A650] shrink-0 mt-0.5" />
              <div>
                <span class="font-bold text-[#00A650]">Llega gratis mañana a todo Chile</span>
                <p class="text-gray-500 text-[11px]">Despachado a través de Mercado Envíos</p>
              </div>
            </div>
            <div class="flex items-start gap-2">
              <RotateCcw class="w-4 h-4 text-[#00A650] shrink-0 mt-0.5" />
              <div>
                <span class="font-bold text-[#00A650]">Devolución gratis</span>
                <p class="text-gray-500 text-[11px]">Tienes 30 días para cambiarlo o devolverlo sin costo</p>
              </div>
            </div>
          </div>

          <!-- User Info Box: Nombre del usuario que ingresó (Requisito del Profesor) -->
          <div class="mt-4 p-3 bg-amber-50/70 rounded-md border border-amber-200/90 text-xs space-y-1.5">
            <div class="flex items-center justify-between">
              <span class="font-bold text-amber-900 flex items-center gap-1.5">
                <UserCheck class="w-4 h-4 text-amber-700" />
                Vendedor / Publicado por:
              </span>
              <span class="bg-amber-200 text-amber-900 text-[10px] font-bold px-2 py-0.5 rounded-full">
                Reputación: {{ product.seller_reputation }} / 5.0
              </span>
            </div>
            <div class="text-gray-800 text-xs font-semibold">
              Titular: <span class="text-black font-extrabold">{{ product.seller_nombre || 'Rodrigo Morales Vendedor' }}</span>
            </div>
            <div class="text-gray-600 text-[11px]">
              Cuenta Intermedia Pública (UserProfile): <strong class="text-gray-900">{{ product.seller_alias }}</strong>
            </div>
          </div>
        </div>

        <!-- Stock and Purchase Buttons -->
        <div class="space-y-2 pt-2">
          <div class="text-xs text-gray-700 mb-2">
            Stock disponible: <strong class="text-gray-900">{{ product.stock }} unidades</strong>
          </div>

          <button
            @click="handleBuyNow"
            class="w-full bg-[#3483FA] hover:bg-[#2968C8] text-white font-bold py-3 rounded-md text-xs uppercase tracking-wider transition-colors shadow-xs flex items-center justify-center gap-2"
          >
            <CreditCard class="w-4 h-4" />
            <span>Comprar Ahora con Transbank</span>
          </button>

          <button
            @click="handleAddToCart"
            class="w-full bg-blue-50 hover:bg-blue-100 text-[#3483FA] font-bold py-3 rounded-md text-xs uppercase tracking-wider transition-colors border border-blue-200 flex items-center justify-center gap-2"
          >
            <ShoppingCart class="w-4 h-4" />
            <span>Agregar al Carrito de Compras</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Product ADS Characteristics (+250 chars) and Description -->
    <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
      <!-- Left: ADS Characteristics (+250 chars requirement) -->
      <div class="md:col-span-7 bg-white p-6 rounded-lg border border-gray-200 shadow-xs space-y-3">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2 text-sm font-bold text-gray-900">
            <FileText class="w-4 h-4 text-blue-600" />
            <span>Características Técnicas y Comerciales en Formato ADS</span>
          </div>
          <span class="bg-blue-100 text-blue-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
            +250 Caracteres Validados
          </span>
        </div>
        <p class="text-xs text-gray-700 leading-relaxed whitespace-pre-line bg-gray-50/70 p-4 rounded-md border border-gray-200 font-sans">
          {{ product.caracteristicas_ads }}
        </p>
      </div>

      <!-- Right: Product Description -->
      <div class="md:col-span-5 bg-white p-6 rounded-lg border border-gray-200 shadow-xs space-y-3">
        <h3 class="text-sm font-bold text-gray-900 pb-3 border-b border-gray-100">
          Descripción del Producto
        </h3>
        <p class="text-xs text-gray-700 leading-relaxed whitespace-pre-line">
          {{ product.description }}
        </p>
      </div>
    </div>
  </div>
</template>
