<script setup>
import { ref, computed, watch } from 'vue'
import { useProductStore } from '../stores/products'
import { useCartStore } from '../stores/cart'
import { useLocationStore } from '../stores/location'
import { useAuthStore } from '../stores/auth'
import {
  ArrowLeft,
  Truck,
  RotateCcw,
  ShieldCheck,
  Star,
  ShoppingCart,
  CreditCard,
  UserCheck,
  FileText,
  Lock,
  ExternalLink,
  Edit3,
  Store,
} from 'lucide-vue-next'

const productStore = useProductStore()
const cartStore = useCartStore()
const locationStore = useLocationStore()
const authStore = useAuthStore()

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

const isOwner = computed(() => {
  if (!authStore.isAuthenticated || !product.value) return false
  const userProfile = authStore.user?.user_profile
  const sellerId = product.value.seller?.id
  const sellerAlias = product.value.seller_alias
  return (
    (userProfile?.id && sellerId && userProfile.id === sellerId) ||
    (authStore.intermediateAlias && sellerAlias && authStore.intermediateAlias === sellerAlias) ||
    authStore.isAdmin
  )
})

// Format currency to Chilean Pesos (CLP)
function formatCLP(amount) {
  if (amount == null) return '$ 0'
  return '$ ' + Math.round(amount).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

const installmentValue = computed(() => {
  if (!product.value) return '$ 0'
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
    <div class="flex items-center justify-between text-xs text-slate-500 bg-brand-surface p-3 rounded-xl border border-brand-border shadow-2xs">
      <div class="flex items-center gap-2">
        <button
          @click="productStore.goToCatalog()"
          class="flex items-center gap-1 text-brand-accent hover:underline font-bold"
        >
          <ArrowLeft class="w-3.5 h-3.5" />
          <span>Volver al Catálogo</span>
        </button>
        <span>/</span>
        <span class="text-slate-400">{{ product.category_name || 'Productos' }}</span>
        <span>/</span>
        <span class="text-slate-800 font-semibold truncate max-w-xs">{{ product.title }}</span>
      </div>

      <div class="hidden sm:flex items-center gap-1.5 bg-brand-primary-subtle text-brand-primary-text px-3 py-1 rounded-full border border-brand-primary-border text-xs font-semibold">
        <ShieldCheck class="w-3.5 h-3.5 text-brand-accent" />
        <span>Garantía de Compra Protegida</span>
      </div>
    </div>

    <!-- Main Product Presentation Card -->
    <div class="bg-brand-surface rounded-xl border border-brand-border shadow-2xs p-6 grid grid-cols-1 md:grid-cols-12 gap-8">
      <!-- Left Column: Product Image -->
      <div class="md:col-span-7 flex flex-col items-center justify-start space-y-3">
        <!-- Image Container -->
        <div class="w-full aspect-[9/6] bg-brand-surface-subtle rounded-lg border border-brand-border p-4 flex items-center justify-center overflow-hidden shadow-2xs relative">
          <img
            :src="activeImageUrl"
            :alt="product.title"
            class="max-w-full max-h-full object-contain hover:scale-105 transition-transform duration-300"
          />
          <div v-if="product.discount_percentage > 0" class="absolute top-3 left-3 bg-brand-accent text-white font-black text-xs px-2.5 py-1 rounded-full shadow-2xs">
            {{ product.discount_percentage }}% OFF
          </div>
        </div>

        <!-- Thumbnails Gallery (if > 1 image) -->
        <div v-if="productImages.length > 1" class="w-full flex items-center gap-2 overflow-x-auto py-1">
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
            class="w-16 h-12 rounded-lg border-2 overflow-hidden bg-brand-surface-subtle shrink-0 transition-all cursor-pointer p-0.5"
          >
            <img :src="img" :alt="`Miniatura ${idx + 1}`" class="w-full h-full object-cover rounded" />
          </button>
        </div>

        <div class="w-full flex items-center justify-between text-xs text-slate-500 bg-brand-surface-subtle p-2.5 rounded-lg border border-brand-border">
          <span class="flex items-center gap-1">
            <ShieldCheck class="w-4 h-4 text-brand-accent" />
            Fotografía oficial del producto
          </span>
          <span class="text-[11px] text-brand-primary-text font-semibold">Publicación Verificada</span>
        </div>
      </div>

      <!-- Right Column: Purchase Details & User Information -->
      <div class="md:col-span-5 flex flex-col justify-between space-y-4">
        <div>
          <!-- Title & Rating -->
          <div class="text-xs text-slate-400 mb-1">
            <span>Nuevo</span> | <span>Código: {{ product.slug }}</span>
          </div>
          <h1 class="text-xl md:text-2xl font-extrabold text-slate-900 leading-tight">
            {{ product.title }}
          </h1>

          <div class="flex items-center gap-3 mt-2 text-xs flex-wrap">
            <template v-if="product.reviews_count > 0 && product.rating">
              <div class="flex items-center text-amber-500">
                <Star class="w-4 h-4 fill-amber-400" />
                <span class="font-bold ml-1 text-slate-800">{{ product.rating }}</span>
              </div>
              <span class="text-slate-400">({{ product.reviews_count }} opiniones)</span>
            </template>
            <template v-else>
              <span class="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                Nuevo | Sin calificaciones aún
              </span>
            </template>

            <!-- Botón Calificar Pedido / Opinar -->
            <button
              @click="productStore.openReviewModal(product)"
              class="text-[11px] text-brand-accent hover:underline font-semibold cursor-pointer inline-flex items-center gap-1"
            >
              <Star class="w-3.5 h-3.5 text-amber-500 fill-amber-400" />
              <span>{{ product.reviews_count > 0 ? 'Opinar sobre este producto' : 'Evaluar este producto' }}</span>
            </button>
          </div>

          <!-- Price & Discounts -->
          <div class="mt-4 space-y-1">
            <div v-if="product.original_price" class="text-xs text-slate-400 line-through">
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
              en <span class="font-bold text-slate-900">{{ product.installments }} cuotas de {{ installmentValue }}</span> sin interés
            </p>
          </div>

          <!-- Shipping and Return Badges -->
          <div class="mt-4 space-y-2 text-xs border-y border-brand-border py-3">
            <div class="flex items-start gap-2">
              <Truck class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="font-bold text-emerald-600">Llega gratis mañana a {{ locationStore.currentLocation }}</span>
                  <button @click="locationStore.openLocationModal()" class="text-[10px] text-brand-accent hover:underline cursor-pointer font-medium">
                    (Cambiar)
                  </button>
                </div>
                <p class="text-slate-500 text-[11px]">Despachado a través de Mercado Envíos Express</p>
              </div>
            </div>
            <div class="flex items-start gap-2">
              <RotateCcw class="w-4 h-4 text-brand-accent shrink-0 mt-0.5" />
              <div>
                <span class="font-bold text-brand-primary-text">Devolución gratis</span>
                <p class="text-slate-500 text-[11px]">Tienes 30 días para cambiarlo o devolverlo sin costo</p>
              </div>
            </div>
          </div>

          <!-- User Info Box: Nombre del usuario que ingresó -->
          <div class="mt-4 p-3.5 bg-brand-primary-subtle rounded-xl border border-brand-primary-border text-xs space-y-1.5 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-900 flex items-center gap-1.5">
                <UserCheck class="w-4 h-4 text-brand-accent" />
                Vendedor / Publicado por:
              </span>
              <span class="bg-brand-primary text-brand-primary-text text-[10px] font-bold px-2 py-0.5 rounded-full">
                Reputación: {{ product.seller_reputation }} / 5.0
              </span>
            </div>
            <div class="text-slate-800 text-xs font-semibold">
              Vendido por: <span class="text-slate-950 font-extrabold">{{ product.seller_nombre || product.seller_alias }}</span>
            </div>

            <!-- Tienda Oficial (Solo si está registrada) -->
            <div v-if="product.is_official_store && product.seller_official_store_name" class="text-slate-700 text-xs flex items-center gap-1.5 pt-1">
              <span class="font-medium text-slate-600">Tienda oficial:</span>
              <template v-if="product.seller_official_store_url">
                <a
                  :href="product.seller_official_store_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="font-bold text-brand-accent hover:underline inline-flex items-center gap-1"
                >
                  <span>{{ product.seller_official_store_name }}</span>
                  <ExternalLink class="w-3 h-3" />
                </a>
              </template>
              <template v-else>
                <strong class="font-bold text-slate-900">{{ product.seller_official_store_name }}</strong>
              </template>
            </div>
            <div v-else class="text-slate-500 text-[11px]">
              Vendedor Autorizado Mercado Inacap ({{ product.seller_alias }})
            </div>
          </div>

          <!-- Owner Control Banner (Si el usuario es dueño de esta publicación) -->
          <div v-if="isOwner" class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-bold text-blue-950 flex items-center gap-1.5">
                <Edit3 class="w-4 h-4 text-blue-600" />
                Eres el dueño de esta publicación
              </span>
              <button
                @click="productStore.goToMyProducts()"
                class="text-[11px] text-brand-accent hover:underline font-semibold cursor-pointer"
              >
                Mis Publicaciones
              </button>
            </div>
            <button
              @click="productStore.openEditModal(product)"
              class="w-full bg-slate-900 hover:bg-black text-white font-bold py-2 px-3 rounded-lg text-xs transition-colors shadow-2xs flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <Edit3 class="w-3.5 h-3.5" />
              <span>Editar esta Publicación</span>
            </button>
          </div>
        </div>

        <!-- Stock and Purchase Buttons -->
        <div class="space-y-2 pt-2">
          <div class="text-xs text-slate-700 mb-2">
            Stock disponible: <strong class="text-slate-900">{{ product.stock }} unidades</strong>
          </div>

          <button
            @click="handleBuyNow"
            class="w-full bg-brand-accent hover:bg-brand-accent-hover text-white font-bold py-3 rounded-lg text-xs uppercase tracking-wider transition-colors shadow-xs flex items-center justify-center gap-2"
          >
            <CreditCard class="w-4 h-4" />
            <span>Comprar Ahora con Transbank</span>
          </button>

          <button
            @click="handleAddToCart"
            class="w-full bg-brand-accent-soft hover:bg-brand-primary-subtle text-brand-accent font-bold py-3 rounded-lg text-xs uppercase tracking-wider transition-colors border border-brand-accent-border flex items-center justify-center gap-2"
          >
            <ShoppingCart class="w-4 h-4" />
            <span>Agregar al Carrito de Compras</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Product ADS Characteristics and Description -->
    <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
      <!-- Left: ADS Characteristics -->
      <div class="md:col-span-7 bg-brand-surface p-6 rounded-xl border border-brand-border shadow-2xs space-y-3">
        <div class="flex items-center justify-between pb-3 border-b border-brand-border">
          <div class="flex items-center gap-2 text-sm font-bold text-slate-900">
            <FileText class="w-4 h-4 text-brand-accent" />
            <span>Características Destacadas</span>
          </div>
          <span class="bg-brand-primary-subtle text-brand-primary-text text-[10px] font-semibold px-2.5 py-0.5 rounded-full border border-brand-primary-border">
            Especificaciones Oficiales
          </span>
        </div>
        <p class="text-xs text-slate-700 leading-relaxed whitespace-pre-line bg-brand-surface-subtle p-4 rounded-lg border border-brand-border font-sans">
          {{ product.caracteristicas_ads }}
        </p>
      </div>

      <!-- Right: Product Description -->
      <div class="md:col-span-5 bg-brand-surface p-6 rounded-xl border border-brand-border shadow-2xs space-y-3">
        <h3 class="text-sm font-bold text-slate-900 pb-3 border-b border-brand-border">
          Descripción del Producto
        </h3>
        <p class="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
          {{ product.description }}
        </p>
      </div>
    </div>
  </div>
</template>
