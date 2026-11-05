<script setup>
import { computed } from 'vue'
import { Zap, Star, ShieldCheck, ShoppingCart } from 'lucide-vue-next'
import { useProductStore } from '../stores/products'
import { useCartStore } from '../stores/cart'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
})

const productStore = useProductStore()
const cartStore = useCartStore()

// Format currency to Chilean Pesos (CLP)
function formatCLP(amount) {
  if (amount == null) return '$ 0'
  return '$ ' + Math.round(amount).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

const installmentValue = computed(() => {
  const parts = props.product.installments || 6
  return formatCLP(props.product.price / parts)
})
</script>

<template>
  <div
    @click="productStore.openDetail(product)"
    class="bg-brand-surface rounded-xl border border-brand-border hover:border-brand-primary-border hover:shadow-md transition-all duration-200 cursor-pointer flex flex-col justify-between overflow-hidden group select-none shadow-2xs"
  >
    <!-- Image Area -->
    <div class="relative w-full pt-[75%] bg-brand-surface border-b border-brand-border/60 overflow-hidden">
      <img
        :src="product.display_image_url || product.image_url"
        :alt="product.title"
        class="absolute inset-0 w-full h-full object-contain p-3 group-hover:scale-105 transition-transform duration-300"
        loading="lazy"
      />
      <div v-if="product.discount_percentage > 0" class="absolute top-2 left-2 bg-brand-accent text-white font-black text-[10px] px-2 py-0.5 rounded-full tracking-tight shadow-2xs">
        {{ product.discount_percentage }}% OFF
      </div>

      <!-- Quick Add to Cart Button -->
      <button
        @click.stop="cartStore.addItem(product, 1)"
        class="absolute bottom-2 right-2 w-8 h-8 rounded-full bg-brand-surface/95 hover:bg-brand-accent text-slate-700 hover:text-white shadow-md border border-brand-border flex items-center justify-center transition-all opacity-0 group-hover:opacity-100"
        title="Agregar al Carrito"
      >
        <ShoppingCart class="w-4 h-4" />
      </button>
    </div>

    <!-- Product Details Area -->
    <div class="p-3.5 flex flex-col flex-1 justify-between gap-2">
      <!-- Title -->
      <h3 class="text-xs text-slate-700 font-normal line-clamp-2 leading-relaxed min-h-[2.5rem]">
        {{ product.title }}
      </h3>

      <!-- Price & Installments -->
      <div class="space-y-0.5 mt-1">
        <div v-if="product.original_price && product.original_price > product.price" class="text-[11px] text-slate-400 line-through">
          {{ formatCLP(product.original_price) }}
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-xl font-bold text-slate-900 tracking-tight">
            {{ formatCLP(product.price) }}
          </span>
          <span v-if="product.discount_percentage > 0" class="text-xs font-semibold text-brand-accent">
            {{ product.discount_percentage }}% OFF
          </span>
        </div>
        <div class="text-[11px] text-slate-500">
          en <span class="text-slate-800 font-medium">{{ product.installments }}x {{ installmentValue }}</span> sin interés
        </div>
      </div>

      <!-- Shipping Badge -->
      <div v-if="product.free_shipping" class="flex items-center gap-1 text-[11px] font-bold text-emerald-600">
        <Zap class="w-3 h-3 fill-emerald-600" />
        <span>Llega gratis mañana</span>
      </div>

      <!-- Footer: Intermediate Seller Pseudonym & Rating -->
      <div class="pt-2 border-t border-brand-border/60 flex items-center justify-between text-[11px] text-slate-400">
        <div class="truncate max-w-[130px]" :title="'Vendido por ' + (product.seller_official_store_name || product.seller_alias || 'Vendedor')">
          <span v-if="product.is_official_store" class="text-brand-accent font-bold">Oficial: </span>
          <span v-else class="text-slate-400">Por </span>
          <span class="font-medium text-slate-700">{{ product.is_official_store ? product.seller_official_store_name : product.seller_alias }}</span>
        </div>
        <div v-if="product.reviews_count > 0 && product.rating" class="flex items-center gap-0.5 text-amber-500 font-medium">
          <Star class="w-3 h-3 fill-amber-400" />
          <span>{{ product.rating }}</span>
          <span class="text-slate-400 text-[10px]">({{ product.reviews_count }})</span>
        </div>
        <div v-else class="text-[10px] text-brand-accent font-semibold bg-blue-50 px-1.5 py-0.5 rounded">
          Nuevo
        </div>
      </div>
    </div>
  </div>
</template>
