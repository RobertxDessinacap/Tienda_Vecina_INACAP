<script setup>
import { onMounted, ref } from 'vue'
import { useProductStore } from '../stores/products'
import { useAuthStore } from '../stores/auth'
import {
  Package,
  PlusCircle,
  Edit3,
  Trash2,
  ExternalLink,
  Store,
  Star,
  ShieldCheck,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Boxes,
  TrendingUp,
  Tag,
} from 'lucide-vue-next'

const productStore = useProductStore()
const authStore = useAuthStore()

const deletingSlug = ref(null)
const confirmDeleteModal = ref(false)
const productToDelete = ref(null)

onMounted(() => {
  productStore.fetchMyProducts()
})

function formatCLP(value) {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    maximumFractionDigits: 0,
  }).format(value || 0)
}

function handleStartDelete(product) {
  productToDelete.value = product
  confirmDeleteModal.value = true
}

async function handleConfirmDelete() {
  if (!productToDelete.value) return
  deletingSlug.value = productToDelete.value.slug
  const res = await productStore.deleteProduct(productToDelete.value.slug)
  deletingSlug.value = null
  confirmDeleteModal.value = false
  productToDelete.value = null
  if (!res.success) {
    alert(res.error || 'No se pudo dar de baja el producto.')
  }
}

function handleViewProduct(slug) {
  productStore.fetchProductBySlug(slug)
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6 space-y-6">
    <!-- Top Navigation Breadcrumb -->
    <div class="flex items-center justify-between">
      <button
        @click="productStore.goToCatalog()"
        class="inline-flex items-center gap-2 text-xs font-semibold text-slate-600 hover:text-brand-accent transition-colors cursor-pointer"
      >
        <ArrowLeft class="w-4 h-4" />
        <span>Volver al Catálogo General</span>
      </button>

      <span class="inline-flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 px-3 py-1 rounded-full font-medium">
        <ShieldCheck class="w-3.5 h-3.5 text-brand-accent" />
        Panel de Control de Vendedor Autorizado
      </span>
    </div>

    <!-- Seller Hero Header -->
    <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-700/60 relative overflow-hidden">
      <div class="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <!-- Seller Info -->
        <div class="space-y-2">
          <div class="flex flex-wrap items-center gap-2.5">
            <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Mis Publicaciones
            </h1>
            <span class="bg-brand-accent/20 border border-brand-accent/40 text-brand-accent text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
              <CheckCircle2 class="w-3.5 h-3.5" />
              {{ authStore.intermediateAlias }}
            </span>
          </div>
          <p class="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
            Administra tus productos en tiempo real, actualiza precios, stock, especificaciones ADS y monitorea la visibilidad de tu catálogo.
          </p>

          <!-- Tienda Oficial Badge / Registration Button -->
          <div class="pt-2 flex flex-wrap items-center gap-3">
            <template v-if="authStore.user?.user_profile?.is_official_store">
              <div class="inline-flex items-center gap-2 bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs px-3 py-1.5 rounded-lg">
                <Store class="w-4 h-4 text-emerald-400" />
                <span>Tienda Oficial: <strong class="text-white">{{ authStore.user.user_profile.official_store_name }}</strong></span>
                <a
                  v-if="authStore.user.user_profile.official_store_url"
                  :href="authStore.user.user_profile.official_store_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-emerald-400 hover:text-white underline ml-1 inline-flex items-center gap-0.5"
                >
                  <span>Visitar sitio</span>
                  <ExternalLink class="w-3 h-3" />
                </a>
                <button
                  @click="productStore.openRegisterStoreModal()"
                  class="ml-2 text-[11px] text-slate-300 hover:text-white underline cursor-pointer"
                >
                  Editar
                </button>
              </div>
            </template>
            <template v-else>
              <button
                @click="productStore.openRegisterStoreModal()"
                class="inline-flex items-center gap-2 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-200 text-xs font-bold px-3.5 py-1.5 rounded-lg transition-colors cursor-pointer"
              >
                <Store class="w-4 h-4 text-amber-300" />
                <span>Registra tu Tienda Oficial</span>
              </button>
              <span class="text-[11px] text-slate-400">
                Obtén insignia oficial y enlace directo a tu sitio web.
              </span>
            </template>
          </div>
        </div>

        <!-- Quick Action Buttons -->
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
          <button
            @click="productStore.openCreateModal()"
            class="inline-flex items-center justify-center gap-2 bg-brand-accent hover:bg-brand-accent-hover text-white font-bold text-sm px-5 py-3 rounded-xl transition-all shadow-md hover:shadow-lg cursor-pointer"
          >
            <PlusCircle class="w-5 h-5" />
            <span>Publicar Nuevo Producto</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Stats Bar -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="bg-brand-surface border border-brand-border rounded-xl p-4 flex items-center gap-4 shadow-2xs">
        <div class="w-12 h-12 rounded-xl bg-blue-50 text-brand-accent flex items-center justify-center shrink-0">
          <Boxes class="w-6 h-6" />
        </div>
        <div>
          <span class="text-xs text-slate-500 block font-medium">Publicaciones Activas</span>
          <span class="text-2xl font-black text-slate-900">{{ productStore.myProducts.length }}</span>
        </div>
      </div>

      <div class="bg-brand-surface border border-brand-border rounded-xl p-4 flex items-center gap-4 shadow-2xs">
        <div class="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
          <TrendingUp class="w-6 h-6" />
        </div>
        <div>
          <span class="text-xs text-slate-500 block font-medium">Ventas Concretadas</span>
          <span class="text-2xl font-black text-slate-900">{{ authStore.user?.user_profile?.total_sales || 0 }}</span>
        </div>
      </div>

      <div class="bg-brand-surface border border-brand-border rounded-xl p-4 flex items-center gap-4 shadow-2xs">
        <div class="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
          <Star class="w-6 h-6 fill-amber-500 text-amber-500" />
        </div>
        <div>
          <span class="text-xs text-slate-500 block font-medium">Reputación de Vendedor</span>
          <span class="text-2xl font-black text-slate-900">{{ authStore.intermediateReputation || '5.0' }} / 5.0</span>
        </div>
      </div>
    </div>

    <!-- Products List Section -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-bold text-slate-900">
          Inventario de Publicaciones ({{ productStore.myProducts.length }})
        </h2>
        <span class="text-xs text-slate-500">
          Todas las acciones se sincronizan automáticamente con la base de datos PostgreSQL.
        </span>
      </div>

      <!-- Loading State -->
      <div v-if="productStore.myProductsLoading" class="py-16 text-center space-y-3">
        <div class="w-10 h-10 border-4 border-brand-accent border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p class="text-sm text-slate-500">Cargando tus publicaciones...</p>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="productStore.myProducts.length === 0"
        class="bg-brand-surface border-2 border-dashed border-brand-border rounded-2xl p-12 text-center space-y-4 shadow-2xs"
      >
        <div class="w-16 h-16 bg-blue-50 text-brand-accent rounded-full flex items-center justify-center mx-auto">
          <Package class="w-8 h-8" />
        </div>
        <div class="space-y-1">
          <h3 class="text-lg font-bold text-slate-900">Aún no has publicado productos</h3>
          <p class="text-xs sm:text-sm text-slate-500 max-w-md mx-auto">
            Crea tu primera publicación con fotos optimizadas a 900x600, especificaciones ADS de más de 250 caracteres y URL limpia personalizada.
          </p>
        </div>
        <button
          @click="productStore.openCreateModal()"
          class="inline-flex items-center gap-2 bg-brand-accent hover:bg-brand-accent-hover text-white font-bold text-xs sm:text-sm px-5 py-2.5 rounded-xl transition-colors shadow-sm cursor-pointer"
        >
          <PlusCircle class="w-4 h-4" />
          <span>Crear mi Primera Publicación</span>
        </button>
      </div>

      <!-- Products Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <div
          v-for="product in productStore.myProducts"
          :key="product.id"
          class="bg-brand-surface border border-brand-border hover:border-slate-300 rounded-xl overflow-hidden shadow-2xs hover:shadow-md transition-all flex flex-col justify-between group"
        >
          <!-- Card Top: Image & Badges -->
          <div>
            <div class="relative bg-slate-100 aspect-[9/6] w-full overflow-hidden">
              <img
                :src="product.display_image_url || product.image_url"
                :alt="product.title"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <!-- Stock Badge -->
              <span
                :class="product.stock > 0 ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white'"
                class="absolute top-2.5 left-2.5 text-[10px] font-bold px-2 py-0.5 rounded-full shadow-xs"
              >
                {{ product.stock > 0 ? `Stock: ${product.stock} un.` : 'Agotado' }}
              </span>

              <!-- Category Badge -->
              <span class="absolute top-2.5 right-2.5 bg-black/60 backdrop-blur-xs text-white text-[10px] font-medium px-2 py-0.5 rounded-full">
                {{ product.category_name || 'Sin categoría' }}
              </span>
            </div>

            <!-- Card Body -->
            <div class="p-4 space-y-3">
              <div>
                <!-- Title -->
                <h3
                  class="font-semibold text-slate-900 text-sm line-clamp-2 leading-snug group-hover:text-brand-accent transition-colors"
                  :title="product.title"
                >
                  {{ product.title }}
                </h3>
              </div>

              <!-- Price -->
              <div class="flex items-baseline gap-2">
                <span class="text-lg font-black text-slate-900">
                  {{ formatCLP(product.price) }}
                </span>
                <span
                  v-if="product.original_price && product.original_price > product.price"
                  class="text-xs text-slate-400 line-through"
                >
                  {{ formatCLP(product.original_price) }}
                </span>
              </div>

              <!-- ADS Status and Rating Display -->
              <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-brand-border text-xs">
                <!-- Rating Display (Nuevo vs Estrellas reales) -->
                <div>
                  <template v-if="product.reviews_count > 0 && product.rating">
                    <div class="flex items-center gap-1 text-amber-500 font-bold text-xs">
                      <Star class="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                      <span>{{ product.rating }}</span>
                      <span class="text-slate-400 font-normal">({{ product.reviews_count }})</span>
                    </div>
                  </template>
                  <template v-else>
                    <span class="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                      Nuevo | Sin valoraciones
                    </span>
                  </template>
                </div>

                <!-- Shipping Flag -->
                <span v-if="product.free_shipping" class="text-[11px] font-bold text-emerald-600">
                  Envío Gratis
                </span>
              </div>
            </div>
          </div>

          <!-- Card Actions Toolbar (Editar, Dar de baja, Ir a la página) -->
          <div class="p-3 bg-slate-50/80 border-t border-brand-border flex items-center justify-between gap-2">
            <!-- Editar Button -->
            <button
              @click="productStore.openEditModal(product)"
              class="flex-1 inline-flex items-center justify-center gap-1.5 bg-brand-surface hover:bg-blue-50 text-slate-700 hover:text-brand-accent border border-brand-border hover:border-blue-200 text-xs font-bold py-2 px-3 rounded-lg transition-all shadow-2xs cursor-pointer"
              title="Editar título, precio, stock o fotos de este producto"
            >
              <Edit3 class="w-3.5 h-3.5" />
              <span>Editar</span>
            </button>

            <!-- Dar de Baja Button -->
            <button
              @click="handleStartDelete(product)"
              class="inline-flex items-center justify-center gap-1 bg-brand-surface hover:bg-rose-50 text-slate-600 hover:text-rose-600 border border-brand-border hover:border-rose-200 text-xs font-semibold py-2 px-3 rounded-lg transition-all shadow-2xs cursor-pointer"
              title="Dar de baja y eliminar de la tienda"
            >
              <Trash2 class="w-3.5 h-3.5" />
              <span class="hidden sm:inline">Dar de baja</span>
            </button>

            <!-- Ir a la Página Button -->
            <button
              @click="handleViewProduct(product.slug)"
              class="inline-flex items-center justify-center gap-1 bg-slate-900 hover:bg-black text-white text-xs font-semibold py-2 px-3 rounded-lg transition-all shadow-2xs cursor-pointer"
              title="Ver página de venta con URL limpia"
            >
              <span>Ir a la página</span>
              <ExternalLink class="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Confirm Delete Modal -->
    <div
      v-if="confirmDeleteModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200"
    >
      <div class="bg-brand-surface rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl border border-brand-border">
        <div class="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
          <AlertTriangle class="w-6 h-6" />
        </div>
        <div class="text-center space-y-1">
          <h3 class="text-lg font-bold text-slate-900">¿Dar de baja esta publicación?</h3>
          <p class="text-xs text-slate-500">
            Estás a punto de dar de baja el producto:
            <strong class="text-slate-800 block mt-1">"{{ productToDelete?.title }}"</strong>
          </p>
          <p class="text-[11px] text-rose-600 pt-1">
            Esta acción eliminará el producto del catálogo y no estará disponible para compra.
          </p>
        </div>

        <div class="flex items-center gap-3 pt-2">
          <button
            @click="confirmDeleteModal = false"
            class="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs py-2.5 rounded-lg transition-colors cursor-pointer"
          >
            Cancelar
          </button>
          <button
            @click="handleConfirmDelete"
            class="flex-1 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs py-2.5 rounded-lg transition-colors shadow-sm cursor-pointer"
          >
            Sí, dar de baja
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
