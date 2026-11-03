<script setup>
import { onMounted, ref } from 'vue'
import MercadoHeader from './components/MercadoHeader.vue'
import PromoBanner from './components/PromoBanner.vue'
import ProductCard from './components/ProductCard.vue'
import ProductDetailModal from './components/ProductDetailModal.vue'
import ProductCleanUrlView from './components/ProductCleanUrlView.vue'
import CreateProductModal from './components/CreateProductModal.vue'
import AuthModal from './components/AuthModal.vue'
import CartDrawer from './components/CartDrawer.vue'
import PaymentCarouselModal from './components/PaymentCarouselModal.vue'
import SecurityBadge from './components/SecurityBadge.vue'
import InfoPagesModal from './components/InfoPagesModal.vue'
import { useProductStore } from './stores/products'
import { useAuthStore } from './stores/auth'
import {
  SlidersHorizontal,
  PackageOpen,
  Shield,
  CreditCard,
  Truck,
  RotateCcw,
} from 'lucide-vue-next'

const productStore = useProductStore()
const authStore = useAuthStore()
const infoModalRef = ref(null)

onMounted(async () => {
  await Promise.all([
    productStore.fetchCategories(),
    productStore.fetchProducts(),
  ])

  // Soporte de URL Limpia en la carga inicial (ej: /producto/samsung-galaxy-s24-ultra)
  const path = window.location.pathname
  if (path.startsWith('/producto/')) {
    const slug = path.replace('/producto/', '').replace(/\/$/, '')
    if (slug) {
      productStore.fetchProductBySlug(slug)
    }
  }

  // Manejar botón Atrás/Adelante del navegador
  window.addEventListener('popstate', () => {
    const currentPath = window.location.pathname
    if (currentPath.startsWith('/producto/')) {
      const slug = currentPath.replace('/producto/', '').replace(/\/$/, '')
      if (slug) {
        productStore.fetchProductBySlug(slug)
      }
    } else {
      productStore.activeView = 'catalog'
      productStore.selectedProduct = null
    }
  })
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-[#EBEBEB] text-[#333333]">
    <!-- MercadoLibre Yellow Header -->
    <MercadoHeader />

    <!-- Main Content Container -->
    <main class="flex-1 w-full">
      <!-- VISTA 1: Página de Producto con URL Limpia (Requisito del Profesor) -->
      <template v-if="productStore.activeView === 'product_page'">
        <ProductCleanUrlView />
      </template>

      <!-- VISTA 2: Catálogo Completo MercadoLibre -->
      <template v-else>
        <div class="max-w-7xl mx-auto px-4 py-4">
          <!-- Promotional Banner -->
          <PromoBanner />

          <!-- Section Title & Filter / Ordering Toolbar -->
          <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4 bg-white p-3.5 rounded-lg border border-gray-200/80 shadow-2xs">
            <div>
              <h2 class="text-base font-bold text-gray-900 tracking-tight">
                <span v-if="productStore.searchQuery">Resultados para "{{ productStore.searchQuery }}"</span>
                <span v-else-if="productStore.activeCategory">Categoría: {{ productStore.activeCategory }}</span>
                <span v-else>Catálogo Oficial en Mercado Inacap</span>
              </h2>
              <p class="text-xs text-gray-500">
                {{ productStore.products.length }} productos disponibles con despacho inmediato
              </p>
            </div>

            <div class="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
              <button
                v-if="productStore.activeCategory || productStore.searchQuery"
                @click="productStore.setCategory(null); productStore.setSearch('')"
                class="text-xs text-[#3483FA] hover:underline font-semibold"
              >
                Limpiar filtros
              </button>

              <div class="flex items-center gap-2 text-xs">
                <SlidersHorizontal class="w-3.5 h-3.5 text-gray-500" />
                <span class="text-gray-600 font-medium">Ordenar por:</span>
                <select
                  :value="productStore.ordering"
                  @change="productStore.setOrdering($event.target.value)"
                  class="bg-gray-50 border border-gray-300 rounded-md py-1 px-2.5 text-xs text-gray-800 focus:outline-none focus:ring-1 focus:ring-[#3483FA]"
                >
                  <option value="-created_at">Más recientes</option>
                  <option value="price_asc">Menor precio</option>
                  <option value="price_desc">Mayor precio</option>
                  <option value="rating">Mejor valorados</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="productStore.loading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 gap-4">
            <div v-for="n in 8" :key="n" class="bg-white rounded-lg p-4 border border-gray-200 animate-pulse space-y-3">
              <div class="w-full pt-[75%] bg-gray-200 rounded-md"></div>
              <div class="h-3 bg-gray-200 rounded-sm w-3/4"></div>
              <div class="h-5 bg-gray-200 rounded-sm w-1/2"></div>
              <div class="h-3 bg-gray-200 rounded-sm w-1/3"></div>
            </div>
          </div>

          <!-- Empty State -->
          <div
            v-else-if="productStore.products.length === 0"
            class="bg-white rounded-lg border border-gray-200 p-12 text-center space-y-3 my-6 shadow-2xs"
          >
            <PackageOpen class="w-12 h-12 text-gray-400 mx-auto" />
            <h3 class="text-base font-bold text-gray-900">No encontramos publicaciones que coincidan con tu búsqueda</h3>
            <p class="text-xs text-gray-500 max-w-sm mx-auto">
              Revisa la ortografía de la palabra o intenta buscar términos más generales.
            </p>
            <button
              @click="productStore.setCategory(null); productStore.setSearch('')"
              class="inline-flex items-center gap-1.5 bg-[#3483FA] text-white font-semibold text-xs px-4 py-2 rounded-md hover:bg-blue-600 transition-colors shadow-2xs mt-2"
            >
              Ver todos los productos
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

          <!-- Security & ISO 27001 Informational Section -->
          <SecurityBadge />
        </div>
      </template>
    </main>

    <!-- Modals & Drawers -->
    <CartDrawer />
    <PaymentCarouselModal />
    <CreateProductModal />
    <AuthModal />
    <InfoPagesModal ref="infoModalRef" />

    <!-- MercadoLibre Clean Footer -->
    <footer class="bg-white border-t border-gray-200/90 text-gray-600 text-xs py-8 mt-12">
      <div class="max-w-7xl mx-auto px-4 space-y-6">
        <!-- Top Footer Badges -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 pb-6 border-b border-gray-200">
          <div class="flex items-center gap-3">
            <CreditCard class="w-7 h-7 text-[#3483FA]" />
            <div>
              <strong class="text-gray-900 block font-bold">Transbank Webpay Plus</strong>
              <span class="text-[11px] text-gray-500">Tarjetas de Débito Redcompra y Crédito</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Truck class="w-7 h-7 text-[#00A650]" />
            <div>
              <strong class="text-gray-900 block font-bold">Envío gratis a todo Chile</strong>
              <span class="text-[11px] text-gray-500">Rápido y asegurado</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Shield class="w-7 h-7 text-emerald-600" />
            <div>
              <strong class="text-gray-900 block font-bold">Compra 100% Protegida</strong>
              <span class="text-[11px] text-gray-500">Garantía oficial en todas tus compras</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <RotateCcw class="w-7 h-7 text-[#3483FA]" />
            <div>
              <strong class="text-gray-900 block font-bold">Devolución gratis</strong>
              <span class="text-[11px] text-gray-500">Tienes 30 días para cambiarlo</span>
            </div>
          </div>
        </div>

        <!-- Working Footer Links -->
        <div class="flex flex-col md:flex-row items-center justify-between gap-4 text-[11px] text-gray-500">
          <div class="flex items-center gap-4 flex-wrap justify-center">
            <button @click="infoModalRef?.open('terms')" class="hover:text-black hover:underline cursor-pointer transition-colors">
              Términos y condiciones
            </button>
            <button @click="infoModalRef?.open('privacy')" class="hover:text-black hover:underline cursor-pointer transition-colors">
              Política de privacidad
            </button>
            <button @click="infoModalRef?.open('payments')" class="hover:text-black hover:underline cursor-pointer transition-colors">
              Medios de Pago & Transbank
            </button>
            <button @click="infoModalRef?.open('help')" class="hover:text-black hover:underline cursor-pointer transition-colors">
              Centro de Ayuda Inacap
            </button>
          </div>
          <p>© 2026 Inacap E-Commerce Inc. Todos los derechos reservados. Tu tienda online segura en Chile.</p>
        </div>
      </div>
    </footer>
  </div>
</template>
