<script setup>
import { computed } from 'vue'
import { Zap, Star, ShieldCheck } from 'lucide-vue-next'
import { useProductStore } from '../stores/products'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
})

const productStore = useProductStore()

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
    class="bg-white rounded-lg border border-gray-200/90 hover:border-gray-300 hover:shadow-lg transition-all duration-200 cursor-pointer flex flex-col justify-between overflow-hidden group select-none"
  >
    <!-- Image Area -->
    <div class="relative w-full pt-[85%] bg-white border-b border-gray-100 overflow-hidden">
      <img
        :src="product.image_url"
        :alt="product.title"
        class="absolute inset-0 w-full h-full object-contain p-4 group-hover:scale-105 transition-transform duration-300"
        loading="lazy"
      />
      <div v-if="product.discount_percentage > 0" class="absolute top-2 left-2 bg-[#00A650] text-white font-black text-[10px] px-2 py-0.5 rounded-xs tracking-tight">
        {{ product.discount_percentage }}% OFF
      </div>
    </div>

    <!-- Product Details Area -->
    <div class="p-3.5 flex flex-col flex-1 justify-between gap-2">
      <!-- Title -->
      <h3 class="text-xs text-gray-700 font-normal line-clamp-2 leading-relaxed min-h-[2.5rem]">
        {{ product.title }}
      </h3>

      <!-- Price & Installments -->
      <div class="space-y-0.5 mt-1">
        <div v-if="product.original_price && product.original_price > product.price" class="text-[11px] text-gray-400 line-through">
          {{ formatCLP(product.original_price) }}
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-xl font-bold text-gray-900 tracking-tight">
            {{ formatCLP(product.price) }}
          </span>
          <span v-if="product.discount_percentage > 0" class="text-xs font-semibold text-[#00A650]">
            {{ product.discount_percentage }}% OFF
          </span>
        </div>
        <div class="text-[11px] text-gray-600">
          en <span class="text-gray-900 font-medium">{{ product.installments }}x {{ installmentValue }}</span> sin interés
        </div>
      </div>

      <!-- Shipping Badge (MercadoLibre green) -->
      <div v-if="product.free_shipping" class="flex items-center gap-1 text-[11px] font-bold text-[#00A650]">
        <Zap class="w-3 h-3 fill-[#00A650]" />
        <span>Llega gratis mañana</span>
      </div>

      <!-- Footer: Intermediate Seller Pseudonym & Rating -->
      <div class="pt-2 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500">
        <div class="truncate max-w-[130px]" :title="'Vendido por ' + (product.seller_alias || 'Vendedor')">
          <span class="text-gray-400">Por </span>
          <span class="font-medium text-gray-700">{{ product.seller_alias }}</span>
        </div>
        <div class="flex items-center gap-0.5 text-amber-500 font-medium">
          <Star class="w-3 h-3 fill-amber-400" />
          <span>{{ product.rating }}</span>
          <span class="text-gray-400 text-[10px]">({{ product.reviews_count }})</span>
        </div>
      </div>
    </div>
  </div>
</template>
