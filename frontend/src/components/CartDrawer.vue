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
    class="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs transition-opacity duration-300"
    @click.self="cartStore.closeCart"
  >
    <!-- Slide-over Drawer -->
    <div
      class="bg-brand-surface w-full max-w-md h-full flex flex-col shadow-2xl border-l border-brand-border animate-in slide-in-from-right duration-300 select-none"
    >
      <!-- Header -->
      <div class="bg-brand-primary px-5 py-4 flex items-center justify-between border-b border-brand-primary-border">
        <div class="flex items-center gap-2">
          <ShoppingCart class="w-5 h-5 text-brand-primary-text" />
          <h2 class="text-sm font-bold text-slate-900">
            Carrito de Compras ({{ cartStore.totalItemsCount }} {{ cartStore.totalItemsCount === 1 ? 'producto' : 'productos' }})
          </h2>
        </div>
        <button
          @click="cartStore.closeCart"
          class="w-7 h-7 rounded-full bg-brand-surface/80 hover:bg-brand-surface flex items-center justify-center text-slate-700 transition-colors"
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
          <div class="w-16 h-16 rounded-full bg-brand-primary-subtle flex items-center justify-center text-brand-accent">
            <ShoppingCart class="w-8 h-8" />
          </div>
          <h3 class="text-sm font-bold text-slate-800">Tu carrito está vacío</h3>
          <p class="text-xs text-slate-500 max-w-xs">
            ¿No sabes qué comprar? ¡Miles de productos con despacho gratis te están esperando en Inacap E-Commerce!
          </p>
          <button
            @click="cartStore.closeCart"
            class="bg-brand-accent text-white text-xs font-semibold px-4 py-2 rounded-lg hover:bg-brand-accent-hover transition-colors shadow-xs"
          >
            Explorar Catálogo
          </button>
        </div>

        <!-- Product Cards in Cart -->
        <div
          v-for="item in cartStore.items"
          :key="item.product.id"
          class="flex items-center gap-3 p-3 bg-brand-surface rounded-xl border border-brand-border shadow-2xs hover:border-brand-primary-border transition-all"
        >
          <!-- Product Thumbnail -->
          <div class="w-16 h-16 bg-brand-surface-subtle rounded-lg border border-brand-border flex items-center justify-center p-1 shrink-0 overflow-hidden">
            <img
              :src="item.product.display_image_url || item.product.image_url"
              :alt="item.product.title"
              class="max-w-full max-h-full object-contain"
            />
          </div>

          <!-- Product Info & Quantity Controls -->
          <div class="flex-1 min-w-0">
            <h4 class="text-xs text-slate-800 font-medium truncate">
              {{ item.product.title }}
            </h4>
            <div class="text-[11px] text-slate-400 mt-0.5">
              Por: <span class="text-slate-600 font-semibold">{{ item.product.seller_alias }}</span>
            </div>

            <div class="flex items-center justify-between mt-2">
              <span class="text-sm font-bold text-slate-900">
                {{ formatCLP(item.product.price * item.quantity) }}
              </span>

              <!-- Quantity Controls -->
              <div class="flex items-center border border-brand-border rounded-md overflow-hidden bg-brand-surface-subtle">
                <button
                  @click="cartStore.addItem(item.product, -1)"
                  class="px-2 py-0.5 hover:bg-brand-primary-subtle text-slate-600 transition-colors"
                  title="Disminuir"
                >
                  <Minus class="w-3 h-3" />
                </button>
                <span class="px-2 text-xs font-bold text-slate-800">{{ item.quantity }}</span>
                <button
                  @click="cartStore.addItem(item.product, 1)"
                  class="px-2 py-0.5 hover:bg-brand-primary-subtle text-slate-600 transition-colors"
                  title="Aumentar"
                >
                  <Plus class="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>

          <!-- Delete Item -->
          <button
            @click="cartStore.removeItem(item.product.id)"
            class="p-1.5 text-slate-300 hover:text-red-500 transition-colors rounded-md"
            title="Eliminar producto"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Footer Checkout Summary -->
      <div v-if="cartStore.hasItems" class="p-4 bg-brand-surface-subtle border-t border-brand-border space-y-3">
        <!-- Security Seal -->
        <div class="flex items-center gap-1.5 text-[10px] text-brand-primary-text bg-brand-primary-subtle border border-brand-primary-border p-2 rounded-lg">
          <ShieldCheck class="w-4 h-4 text-brand-accent shrink-0" />
          <span>Compra 100% protegida y garantizada a todo Chile.</span>
        </div>

        <!-- Breakdown -->
        <div class="space-y-1 text-xs">
          <div class="flex justify-between text-slate-600">
            <span>Subtotal</span>
            <span class="font-semibold text-slate-800">{{ displaySubtotal }}</span>
          </div>
          <div class="flex justify-between text-emerald-600 font-semibold">
            <span class="flex items-center gap-1">
              <Truck class="w-3.5 h-3.5" />
              Envío a todo Chile
            </span>
            <span>Gratis</span>
          </div>
          <div class="pt-2 border-t border-brand-border flex justify-between text-sm font-bold text-slate-900">
            <span>Total</span>
            <span class="text-base text-slate-900">{{ displayTotal }}</span>
          </div>
        </div>

        <!-- Checkout Action Button -->
        <button
          @click="handleProceedToPayment"
          class="w-full bg-brand-accent hover:bg-brand-accent-hover text-white font-bold py-2.5 rounded-lg text-xs uppercase tracking-wider transition-colors shadow-xs flex items-center justify-center gap-2"
        >
          <span>Ir a Medios de Pago</span>
          <ArrowRight class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>
