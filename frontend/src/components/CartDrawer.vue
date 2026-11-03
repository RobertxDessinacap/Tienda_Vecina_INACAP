<script setup>
import { computed } from 'vue'
import {
  X,
  Trash2,
  Plus,
  Minus,
  ShoppingCart,
  ShieldCheck,
  ArrowRight,
  Truck,
  Sparkles,
} from 'lucide-vue-next'
import { useCartStore } from '../stores/cart'

const cartStore = useCartStore()

function formatCLP(amount) {
  if (amount == null) return '$ 0'
  return '$ ' + Math.round(amount).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

const displaySubtotal = computed(() => {
  if (cartStore.backendCalculation?.subtotal != null) {
    return formatCLP(cartStore.backendCalculation.subtotal)
  }
  const rough = cartStore.items.reduce((acc, it) => acc + (it.product.price * it.quantity), 0)
  return formatCLP(rough)
})

const displayTotal = computed(() => {
  if (cartStore.backendCalculation?.total != null) {
    return formatCLP(cartStore.backendCalculation.total)
  }
  const rough = cartStore.items.reduce((acc, it) => acc + (it.product.price * it.quantity), 0)
  return formatCLP(rough)
})

function handleProceedToPayment() {
  cartStore.openPaymentModal()
}
</script>

<template>
  <!-- Background Overlay -->
  <div
    v-if="cartStore.cartDrawerOpen"
    class="fixed inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-2xs transition-opacity duration-300"
    @click.self="cartStore.closeCart"
  >
    <!-- Slide-over Drawer -->
    <div
      class="bg-white w-full max-w-md h-full flex flex-col shadow-2xl border-l border-gray-200 animate-in slide-in-from-right duration-300 select-none"
    >
      <!-- Header -->
      <div class="bg-[#FFE600] px-5 py-4 flex items-center justify-between border-b border-yellow-400">
        <div class="flex items-center gap-2">
          <ShoppingCart class="w-5 h-5 text-gray-900" />
          <h2 class="text-sm font-bold text-gray-900">
            Carrito de Compras ({{ cartStore.totalItemsCount }} {{ cartStore.totalItemsCount === 1 ? 'producto' : 'productos' }})
          </h2>
        </div>
        <button
          @click="cartStore.closeCart"
          class="w-7 h-7 rounded-full bg-white/80 hover:bg-white flex items-center justify-center text-gray-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Items List -->
      <div class="flex-1 overflow-y-auto p-4 space-y-3">
        <!-- Empty State -->
        <div
          v-if="!cartStore.hasItems"
          class="h-full flex flex-col items-center justify-center text-center p-6 space-y-3"
        >
          <div class="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
            <ShoppingCart class="w-8 h-8" />
          </div>
          <h3 class="text-sm font-bold text-gray-800">Tu carrito está vacío</h3>
          <p class="text-xs text-gray-500 max-w-xs">
            ¿No sabes qué comprar? ¡Miles de productos con despacho gratis te están esperando en Inacap E-Commerce!
          </p>
          <button
            @click="cartStore.closeCart"
            class="bg-[#3483FA] text-white text-xs font-semibold px-4 py-2 rounded-md hover:bg-blue-600 transition-colors shadow-xs"
          >
            Explorar Catálogo
          </button>
        </div>

        <!-- Product Cards in Cart -->
        <div
          v-for="item in cartStore.items"
          :key="item.product.id"
          class="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200/90 shadow-2xs hover:border-gray-300 transition-all"
        >
          <!-- Product Thumbnail -->
          <div class="w-16 h-16 bg-gray-50 rounded-md border border-gray-100 flex items-center justify-center p-1 shrink-0 overflow-hidden">
            <img
              :src="item.product.display_image_url || item.product.image_url"
              :alt="item.product.title"
              class="max-w-full max-h-full object-contain"
            />
          </div>

          <!-- Info & Controls -->
          <div class="flex-1 min-w-0">
            <h4 class="text-xs font-medium text-gray-900 truncate" :title="item.product.title">
              {{ item.product.title }}
            </h4>
            <div class="text-xs font-bold text-gray-900 mt-0.5">
              {{ formatCLP(item.product.price) }}
            </div>

            <!-- Quantity Selector & Trash -->
            <div class="flex items-center justify-between mt-2">
              <div class="flex items-center border border-gray-300 rounded-sm bg-gray-50">
                <button
                  @click="cartStore.updateQuantity(item.product.id, -1)"
                  class="px-2 py-0.5 text-gray-600 hover:text-black hover:bg-gray-200 transition-colors text-xs"
                >
                  <Minus class="w-3 h-3" />
                </button>
                <span class="px-2.5 py-0.5 text-xs font-bold text-gray-900 bg-white">
                  {{ item.quantity }}
                </span>
                <button
                  @click="cartStore.updateQuantity(item.product.id, 1)"
                  class="px-2 py-0.5 text-gray-600 hover:text-black hover:bg-gray-200 transition-colors text-xs"
                >
                  <Plus class="w-3 h-3" />
                </button>
              </div>

              <button
                @click="cartStore.removeItem(item.product.id)"
                class="text-gray-400 hover:text-red-600 p-1 transition-colors"
                title="Eliminar del carrito"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer & Safe Calculation Checkout -->
      <div v-if="cartStore.hasItems" class="p-4 bg-gray-50 border-t border-gray-200 space-y-3">
        <!-- Anti-Tampering Security Seal -->
        <div class="flex items-center gap-1.5 text-[10px] text-gray-600 bg-emerald-50 border border-emerald-200 p-2 rounded-md">
          <ShieldCheck class="w-4 h-4 text-emerald-700 shrink-0" />
          <span>Total calculado y blindado en Backend PostgreSQL (Sin manipulación JS).</span>
        </div>

        <!-- Breakdown -->
        <div class="space-y-1 text-xs">
          <div class="flex justify-between text-gray-600">
            <span>Subtotal</span>
            <span class="font-semibold text-gray-800">{{ displaySubtotal }}</span>
          </div>
          <div class="flex justify-between text-[#00A650] font-semibold">
            <span class="flex items-center gap-1">
              <Truck class="w-3.5 h-3.5" />
              Envío a todo Chile
            </span>
            <span>Gratis</span>
          </div>
          <div class="pt-2 border-t border-gray-200 flex justify-between text-sm font-bold text-gray-900">
            <span>Total</span>
            <span class="text-base text-gray-900">{{ displayTotal }}</span>
          </div>
        </div>

        <!-- Checkout Action Button -->
        <button
          @click="handleProceedToPayment"
          class="w-full bg-[#3483FA] hover:bg-[#2968C8] text-white font-bold py-2.5 rounded-md text-xs uppercase tracking-wider transition-colors shadow-xs flex items-center justify-center gap-2"
        >
          <span>Ir a Medios de Pago</span>
          <ArrowRight class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>
