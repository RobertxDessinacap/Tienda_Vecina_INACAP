<script setup>
import { onMounted, ref } from 'vue'
import MercadoHeader from './components/MercadoHeader.vue'
import PromoBanner from './components/PromoBanner.vue'
import ProductCard from './components/ProductCard.vue'
import ProductDetailModal from './components/ProductDetailModal.vue'
import ProductCleanUrlView from './components/ProductCleanUrlView.vue'
import CreateProductModal from './components/CreateProductModal.vue'
import EditProductModal from './components/EditProductModal.vue'
import RegisterStoreModal from './components/RegisterStoreModal.vue'
import ProductReviewModal from './components/ProductReviewModal.vue'
import SellerProductsView from './components/SellerProductsView.vue'
import AuthModal from './components/AuthModal.vue'
import BecomeSellerModal from './components/BecomeSellerModal.vue'
import PriceFilterModal from './components/PriceFilterModal.vue'
import CartDrawer from './components/CartDrawer.vue'
import PaymentCarouselModal from './components/PaymentCarouselModal.vue'
import SecurityBadge from './components/SecurityBadge.vue'
import InfoPagesModal from './components/InfoPagesModal.vue'
import LocationModal from './components/LocationModal.vue'
import { useProductStore } from './stores/products'
import { useAuthStore } from './stores/auth'
import { useCartStore } from './stores/cart'
import {
  SlidersHorizontal,
  PackageOpen,
  Shield,
  CreditCard,
  Truck,
  RotateCcw,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
} from 'lucide-vue-next'

const productStore = useProductStore()
const authStore = useAuthStore()
const cartStore = useCartStore()
const infoModalRef = ref(null)

async function changePage(targetPage) {
  if (targetPage < 1 || targetPage > productStore.totalPages) return
  await productStore.fetchProducts(targetPage)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(async () => {
  await Promise.all([
    authStore.initAuth(),
    productStore.fetchCategories(),
    productStore.fetchProducts(),
  ])

  // Manejo de retorno desde Webpay Plus (/api/v1/payments/transbank/commit/)
  const urlParams = new URLSearchParams(window.location.search)
  const paymentStatus = urlParams.get('payment_status')
  if (paymentStatus) {
    const buyOrder = urlParams.get('buy_order') || ''
    const authCode = urlParams.get('auth_code') || ''
    const rawAmount = urlParams.get('amount')
    const amount = rawAmount !== null && rawAmount !== '' ? Number(rawAmount) : 0
    const cardLastDigits = urlParams.get('card_last_digits') || ''
    const message = urlParams.get('message') || ''

    if (paymentStatus === 'AUTHORIZED') {
      cartStore.clearCart()
      cartStore.openPaymentModal()
      cartStore.paymentVoucher = {
        buy_order: buyOrder,
        authorization_code: authCode,
        amount: Number.isFinite(amount) ? amount : 0,
        card_last_digits: cardLastDigits,
        status: 'APROBADO',
      }
      await productStore.fetchProducts(productStore.page)
    } else {
      cartStore.openPaymentModal()
      const statusMessages = {
        CANCELLED: 'El pago fue cancelado en Transbank Webpay Plus.',
        REVERSED: 'Stock insuficiente al confirmar el pago. La transacción fue reversada automáticamente.',
        NOT_FOUND: 'No se encontró la orden asociada al token de pago.',
        ERROR: 'Ocurrió un error al validar la transacción con Transbank.',
      }
      cartStore.paymentError =
        message ||
        statusMessages[paymentStatus] ||
        'La transacción fue rechazada por Transbank.'
    }

    const cleanUrl = window.location.pathname + (window.location.hash || '')
    window.history.replaceState({}, '', cleanUrl)
  }

  // Soporte de URL Limpia y rutas en la carga inicial
  const path = window.location.pathname
  if (path.startsWith('/producto/')) {
    const slug = path.replace('/producto/', '').replace(/\/$/, '')
    if (slug) {
      productStore.fetchProductBySlug(slug)
    }
  } else if (path === '/mis-publicaciones') {
    productStore.goToMyProducts()
  }

  // Manejar botón Atrás/Adelante del navegador
  window.addEventListener('popstate', () => {
    const currentPath = window.location.pathname
    if (currentPath.startsWith('/producto/')) {
      const slug = currentPath.replace('/producto/', '').replace(/\/$/, '')
      if (slug) {
        productStore.fetchProductBySlug(slug)
      }
    } else if (currentPath === '/mis-publicaciones') {
      productStore.goToMyProducts()
    } else {
      productStore.activeView = 'catalog'
      productStore.selectedProduct = null
    }
  })
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-brand-bg text-slate-800">
    <!-- Header Centralizado -->
    <MercadoHeader />

    <!-- Main Content Container -->
    <main class="flex-1 w-full">
      <!-- VISTA 1: Página de Producto con URL Limpia -->
      <template v-if="productStore.activeView === 'product_page'">
        <ProductCleanUrlView />
      </template>

      <!-- VISTA 2: Mis Publicaciones (Panel Único para Vendedores) -->
      <template v-else-if="productStore.activeView === 'my_products'">
        <SellerProductsView />
      </template>

      <!-- VISTA 3: Catálogo Completo -->
      <template v-else>
        <div class="max-w-7xl mx-auto px-4 py-4">
          <!-- Promotional Banner -->
          <PromoBanner />

          <!-- Section Title & Filter / Ordering Toolbar -->
          <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4 bg-brand-surface p-3.5 rounded-xl border border-brand-border shadow-2xs">
            <div>
              <h2 class="text-base font-bold text-slate-900 tracking-tight">
                <span v-if="productStore.searchQuery">Resultados para "{{ productStore.searchQuery }}"</span>
                <span v-else-if="productStore.activeCategory">Categoría: {{ productStore.activeCategory }}</span>
                <span v-else>Catálogo Oficial en Tienda Vecina</span>
              </h2>
              <p class="text-xs text-slate-500">
                {{ productStore.totalCount }} productos disponibles con despacho inmediato
              </p>
            </div>

            <!-- Toolbar con Botón de Filtros y Combobox de Ordenar Por (sin label) -->
            <div class="flex items-center gap-2.5 w-full sm:w-auto justify-between sm:justify-end">
              <!-- Botón rápido Limpiar filtros si hay alguno activo -->
              <button
                v-if="productStore.hasActiveFilters"
                type="button"
                @click="productStore.clearAllFilters()"
                class="text-xs text-[#f97316] hover:underline font-semibold flex items-center gap-1 cursor-pointer"
              >
                <RotateCcw class="w-3 h-3" />
                <span class="hidden md:inline">Limpiar filtros</span>
              </button>

              <!-- Botón Filtro (Abre el Modal de Rango de Precio y Filtros) -->
              <button
                type="button"
                @click="productStore.openFilterModal()"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-border bg-brand-surface-subtle hover:bg-brand-primary-subtle text-xs font-semibold text-slate-700 transition-all cursor-pointer shadow-2xs hover:border-brand-primary-border"
              >
                <SlidersHorizontal class="w-3.5 h-3.5 text-brand-accent" />
                <span>Filtros</span>
                <span
                  v-if="productStore.activeFiltersCount > 0"
                  class="bg-[#f97316] text-white text-[10px] font-extrabold rounded-full w-4 h-4 flex items-center justify-center leading-none"
                >
                  {{ productStore.activeFiltersCount }}
                </span>
              </button>

              <!-- Combobox Ordenar Por (Placeholder/Texto integrado dentro del select, sin label externo) -->
              <div class="relative flex items-center">
                <select
                  :value="productStore.ordering"
                  @change="productStore.setOrdering($event.target.value)"
                  class="appearance-none bg-brand-surface-subtle border border-brand-border hover:border-brand-primary-border rounded-lg py-1.5 pl-3 pr-8 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-accent cursor-pointer shadow-2xs transition-colors"
                >
                  <option value="-created_at">Ordenar por: Más recientes</option>
                  <option value="price_asc">Ordenar por: Menor precio</option>
                  <option value="price_desc">Ordenar por: Mayor precio</option>
                  <option value="rating">Ordenar por: Mejor valorados</option>
                </select>
                <ChevronDown class="w-3.5 h-3.5 text-slate-400 absolute right-2.5 pointer-events-none" />
              </div>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="productStore.loading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 gap-4">
            <div v-for="n in 8" :key="n" class="bg-brand-surface rounded-xl p-4 border border-brand-border animate-pulse space-y-3">
              <div class="w-full pt-[75%] bg-brand-primary-subtle rounded-md"></div>
              <div class="h-3 bg-brand-primary-subtle rounded-sm w-3/4"></div>
              <div class="h-5 bg-brand-primary-subtle rounded-sm w-1/2"></div>
              <div class="h-3 bg-brand-primary-subtle rounded-sm w-1/3"></div>
            </div>
          </div>

          <!-- Empty State -->
          <div
            v-else-if="productStore.products.length === 0"
            class="bg-brand-surface rounded-xl border border-brand-border p-12 text-center space-y-3 my-6 shadow-2xs"
          >
            <PackageOpen class="w-12 h-12 text-slate-300 mx-auto" />
            <h3 class="text-base font-bold text-slate-900">No encontramos publicaciones que coincidan con tus filtros</h3>
            <p class="text-xs text-slate-500 max-w-sm mx-auto">
              Intenta ampliar el rango de precio, seleccionar otra categoría o borrar los filtros aplicados.
            </p>
            <button
              @click="productStore.clearAllFilters()"
              class="inline-flex items-center gap-1.5 bg-[#f97316] hover:bg-[#ea580c] text-white font-semibold text-xs px-4 py-2 rounded-lg transition-colors shadow-2xs mt-2 cursor-pointer"
            >
              Borrar todos los filtros y ver catálogo
            </button>
          </div>

          <!-- Product Cards Grid -->
          <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 gap-4">
            <ProductCard
              v-for="product in productStore.products"
              :key="product.id"
              :product="product"
            />
          </div>

          <!-- Pagination Controls -->
          <div
            v-if="!productStore.loading && productStore.totalPages > 1"
            class="flex items-center justify-center gap-3 mt-6 py-3"
          >
            <button
              type="button"
              :disabled="productStore.page <= 1"
              @click="changePage(productStore.page - 1)"
              class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-brand-border bg-brand-surface hover:bg-brand-primary-subtle text-xs font-semibold text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors shadow-2xs"
            >
              <ChevronLeft class="w-4 h-4" />
              <span>Anterior</span>
            </button>
            <span class="text-xs font-semibold text-slate-600 px-2">
              Página {{ productStore.page }} de {{ productStore.totalPages }}
            </span>
            <button
              type="button"
              :disabled="productStore.page >= productStore.totalPages"
              @click="changePage(productStore.page + 1)"
              class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-brand-border bg-brand-surface hover:bg-brand-primary-subtle text-xs font-semibold text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors shadow-2xs"
            >
              <span>Siguiente</span>
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>

          <!-- Security & ISO 27001 Informational Section -->
          <SecurityBadge />
        </div>
      </template>
    </main>

    <!-- Modals & Drawers -->
    <CartDrawer />
    <PaymentCarouselModal />
    <CreateProductModal />
    <EditProductModal />
    <RegisterStoreModal />
    <ProductReviewModal />
    <AuthModal />
    <BecomeSellerModal />
    <PriceFilterModal />
    <InfoPagesModal ref="infoModalRef" />
    <LocationModal />

    <!-- Clean Footer -->
    <footer class="bg-brand-surface border-t border-brand-border text-slate-600 text-xs py-8 mt-12">
      <div class="max-w-7xl mx-auto px-4 space-y-6">
        <!-- Top Footer Badges -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 pb-6 border-b border-brand-border">
          <div class="flex items-center gap-3">
            <CreditCard class="w-7 h-7 text-brand-accent" />
            <div>
              <strong class="text-slate-900 block font-bold">Transbank Webpay Plus</strong>
              <span class="text-[11px] text-slate-500">Tarjetas de Débito Redcompra y Crédito</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Truck class="w-7 h-7 text-emerald-600" />
            <div>
              <strong class="text-slate-900 block font-bold">Envío gratis a todo Chile</strong>
              <span class="text-[11px] text-slate-500">Rápido y asegurado</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Shield class="w-7 h-7 text-brand-accent" />
            <div>
              <strong class="text-slate-900 block font-bold">Compra 100% Protegida</strong>
              <span class="text-[11px] text-slate-500">Garantía oficial en todas tus compras</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <RotateCcw class="w-7 h-7 text-brand-accent" />
            <div>
              <strong class="text-slate-900 block font-bold">Devolución gratis</strong>
              <span class="text-[11px] text-slate-500">Tienes 30 días para cambiarlo</span>
            </div>
          </div>
        </div>

        <!-- Working Footer Links -->
        <div class="flex flex-col md:flex-row items-center justify-between gap-4 text-[11px] text-slate-500">
          <div class="flex items-center gap-4 flex-wrap justify-center">
            <button @click="infoModalRef?.open('terms')" class="hover:text-slate-900 hover:underline cursor-pointer transition-colors">
              Términos y condiciones
            </button>
            <button @click="infoModalRef?.open('privacy')" class="hover:text-slate-900 hover:underline cursor-pointer transition-colors">
              Política de privacidad
            </button>
            <button @click="infoModalRef?.open('payments')" class="hover:text-slate-900 hover:underline cursor-pointer transition-colors">
              Medios de Pago & Transbank
            </button>
            <button @click="infoModalRef?.open('help')" class="hover:text-slate-900 hover:underline cursor-pointer transition-colors">
              Centro de Ayuda Tienda Vecina
            </button>
          </div>
          <p>© 2026 Tienda Vecina Inc. Todos los derechos reservados. Tu tienda online segura en Chile.</p>
        </div>
      </div>
    </footer>
  </div>
</template>
