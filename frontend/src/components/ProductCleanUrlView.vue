<script setup>
import { computed } from 'vue'
import { useProductStore } from '../stores/products'
import { useCartStore } from '../stores/cart'
import { useLocationStore } from '../stores/location'
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
} from 'lucide-vue-next'

const productStore = useProductStore()
const cartStore = useCartStore()
const locationStore = useLocationStore()

const product = computed(() => productStore.selectedProduct)

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
            :src="product.display_image_url || product.image_url"
            :alt="product.title"
            class="max-w-full max-h-full object-contain hover:scale-105 transition-transform duration-300"
          />
          <div v-if="product.discount_percentage > 0" class="absolute top-3 left-3 bg-brand-accent text-white font-black text-xs px-2.5 py-1 rounded-full shadow-2xs">
            {{ product.discount_percentage }}% OFF
          </div>
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

          <div class="flex items-center gap-2 mt-2 text-xs">
            <div class="flex items-center text-amber-500">
              <Star class="w-4 h-4 fill-amber-400" />
              <span class="font-bold ml-1 text-slate-800">{{ product.rating }}</span>
            </div>
            <span class="text-slate-400">({{ product.reviews_count }} opiniones)</span>
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
              Vendido por: <span class="text-slate-950 font-extrabold">{{ product.seller_nombre || 'Rodrigo Morales Vendedor' }}</span>
            </div>
            <div class="text-slate-600 text-[11px]">
              Tienda oficial: <strong class="text-slate-900">{{ product.seller_alias }}</strong>
            </div>
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
