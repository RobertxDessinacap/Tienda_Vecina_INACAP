<script setup>
import { reactive, ref, computed } from 'vue'
import {
  X,
  PlusCircle,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Zap,
  Star,
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useProductStore } from '../stores/products'

const authStore = useAuthStore()
const productStore = useProductStore()

const formData = reactive({
  title: '',
  description: '',
  price: 199990,
  original_price: null,
  stock: 10,
  category: '',
  image_url: 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=700&auto=format&fit=crop&q=80',
  free_shipping: true,
  installments: 6,
})

const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// Image quick presets for easy testing
const sampleImages = [
  { label: 'Smartwatch', url: 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=700&auto=format&fit=crop&q=80' },
  { label: 'Cámara DSLR', url: 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=700&auto=format&fit=crop&q=80' },
  { label: 'Audífonos Gamer', url: 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=700&auto=format&fit=crop&q=80' },
  { label: 'Laptop Ultrabook', url: 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=700&auto=format&fit=crop&q=80' },
]

function formatCLP(amount) {
  if (amount == null) return '$ 0'
  return '$ ' + Math.round(amount).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

const previewDiscount = computed(() => {
  if (formData.original_price && formData.original_price > formData.price) {
    const diff = formData.original_price - formData.price
    return Math.round((diff / formData.original_price) * 100)
  }
  return 0
})

async function handleSubmit() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!formData.title || formData.title.length < 3) {
    errorMessage.value = 'El título del producto debe tener al menos 3 caracteres.'
    return
  }
  if (!formData.price || formData.price <= 0) {
    errorMessage.value = 'El precio debe ser mayor a 0.'
    return
  }

  submitting.value = true
  const payload = {
    title: formData.title,
    description: formData.description,
    price: formData.price,
    original_price: formData.original_price || null,
    stock: formData.stock,
    category: formData.category || null,
    image_url: formData.image_url,
    free_shipping: formData.free_shipping,
    installments: formData.installments,
  }

  const result = await productStore.createProduct(payload)
  submitting.value = false

  if (result.success) {
    successMessage.value = '¡Producto publicado con éxito en el catálogo!'
    setTimeout(() => {
      productStore.closeCreateModal()
      successMessage.value = ''
    }, 1200)
  } else {
    errorMessage.value = result.error
  }
}
</script>

<template>
  <div
    v-if="productStore.createModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-2xs overflow-y-auto"
  >
    <div
      class="bg-white rounded-lg shadow-2xl max-w-4xl w-full overflow-hidden border border-gray-200 relative animate-in fade-in zoom-in-95 duration-200 my-auto"
    >
      <!-- Modal Header -->
      <div class="bg-[#FFE600] px-6 py-4 flex items-center justify-between border-b border-yellow-400">
        <div class="flex items-center gap-2">
          <PlusCircle class="w-5 h-5 text-gray-900" />
          <h2 class="text-base font-bold text-gray-900">
            Publicar Nuevo Producto en Inacap E-Commerce
          </h2>
        </div>
        <button
          @click="productStore.closeCreateModal"
          class="w-7 h-7 rounded-full bg-white/80 hover:bg-white flex items-center justify-center text-gray-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- If User is NOT a Seller (RBAC Guard) -->
      <div v-if="!authStore.isSeller" class="p-8 text-center space-y-4">
        <div class="w-12 h-12 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center mx-auto">
          <AlertCircle class="w-6 h-6" />
        </div>
        <h3 class="text-lg font-bold text-gray-900">Acceso Restringido por Rol (ISO 27001)</h3>
        <p class="text-sm text-gray-600 max-w-md mx-auto">
          Para publicar productos en la plataforma, tu cuenta debe contar con el rol de
          <strong class="text-gray-900">Vendedor Autorizado</strong> o <strong class="text-gray-900">Administrador</strong>.
        </p>
        <div class="pt-2 flex justify-center gap-3">
          <button
            @click="productStore.closeCreateModal(); authStore.openAuthModal('register')"
            class="bg-[#3483FA] text-white font-semibold text-xs px-4 py-2 rounded-md hover:bg-blue-600 transition-colors"
          >
            Registrar Cuenta de Vendedor
          </button>
          <button
            @click="productStore.closeCreateModal(); authStore.openAuthModal('login')"
            class="bg-gray-100 text-gray-700 font-semibold text-xs px-4 py-2 rounded-md hover:bg-gray-200 transition-colors"
          >
            Iniciar Sesión con Otra Cuenta
          </button>
        </div>
      </div>

      <!-- Seller Product Creation Form with Live Preview -->
      <div v-else class="grid grid-cols-1 md:grid-cols-12 gap-6 p-6 max-h-[80vh] overflow-y-auto">
        <!-- Left: Form -->
        <form @submit.prevent="handleSubmit" class="md:col-span-7 space-y-4">
          <!-- Alert feedback -->
          <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-md flex items-center gap-2">
            <AlertCircle class="w-4 h-4 shrink-0" />
            <span>{{ errorMessage }}</span>
          </div>
          <div v-if="successMessage" class="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs p-3 rounded-md flex items-center gap-2">
            <CheckCircle2 class="w-4 h-4 shrink-0" />
            <span>{{ successMessage }}</span>
          </div>

          <!-- Title -->
          <div>
            <label class="block text-xs font-bold text-gray-700 mb-1">Título del Producto *</label>
            <input
              v-model="formData.title"
              type="text"
              placeholder="Ej: Teclado Mecánico Inalámbrico RGB Switch Brown"
              required
              class="w-full text-xs p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
            />
          </div>

          <!-- Category & Stock -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-gray-700 mb-1">Categoría</label>
              <select
                v-model="formData.category"
                class="w-full text-xs p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA] bg-white"
              >
                <option value="">Selecciona categoría</option>
                <option v-for="cat in productStore.categories" :key="cat.id" :value="cat.id">
                  {{ cat.name }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-700 mb-1">Stock Disponible *</label>
              <input
                v-model.number="formData.stock"
                type="number"
                min="1"
                required
                class="w-full text-xs p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
              />
            </div>
          </div>

          <!-- Price & Original Price -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-gray-700 mb-1">Precio de Venta ($ CLP) *</label>
              <input
                v-model.number="formData.price"
                type="number"
                min="100"
                required
                class="w-full text-xs p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
              />
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-700 mb-1">Precio Original (Opcional, para % OFF)</label>
              <input
                v-model.number="formData.original_price"
                type="number"
                placeholder="Ej: 249990"
                class="w-full text-xs p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
              />
            </div>
          </div>

          <!-- Image URL & Quick sample buttons -->
          <div>
            <label class="block text-xs font-bold text-gray-700 mb-1">URL de la Imagen *</label>
            <input
              v-model="formData.image_url"
              type="url"
              placeholder="https://..."
              required
              class="w-full text-xs p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
            />
            <div class="flex items-center gap-1.5 mt-1.5 flex-wrap">
              <span class="text-[10px] text-gray-500 font-medium">Ejemplos rápidos:</span>
              <button
                v-for="img in sampleImages"
                :key="img.label"
                type="button"
                @click="formData.image_url = img.url"
                class="text-[10px] bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-0.5 rounded-xs transition-colors"
              >
                {{ img.label }}
              </button>
            </div>
          </div>

          <!-- Description -->
          <div>
            <label class="block text-xs font-bold text-gray-700 mb-1">Descripción Detallada *</label>
            <textarea
              v-model="formData.description"
              rows="3"
              placeholder="Describe las características técnicas, estado, garantía y especificaciones del producto..."
              required
              class="w-full text-xs p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
            ></textarea>
          </div>

          <!-- Free Shipping & Installments Toggles -->
          <div class="flex items-center justify-between p-3 bg-gray-50 rounded-md border border-gray-200 text-xs">
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="formData.free_shipping" type="checkbox" class="rounded-xs text-[#00A650] focus:ring-[#00A650]" />
              <span class="font-medium text-gray-800">Ofrecer Envío Gratis</span>
            </label>
            <div class="flex items-center gap-2">
              <span class="text-gray-600 font-medium">Cuotas sin interés:</span>
              <select v-model.number="formData.installments" class="text-xs p-1 rounded-xs border border-gray-300 bg-white">
                <option :value="3">3x</option>
                <option :value="6">6x</option>
                <option :value="12">12x</option>
              </select>
            </div>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="submitting"
            class="w-full bg-[#3483FA] hover:bg-[#2968C8] text-white font-bold py-2.5 rounded-md text-xs uppercase tracking-wider transition-colors disabled:opacity-50 shadow-xs"
          >
            <span v-if="submitting">Publicando en Catálogo...</span>
            <span v-else>Publicar Producto</span>
          </button>
        </form>

        <!-- Right: Live Real-Time Card Preview -->
        <div class="md:col-span-5 flex flex-col justify-start space-y-3 bg-gray-50/70 p-4 rounded-lg border border-gray-200">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-gray-800 flex items-center gap-1.5">
              <Sparkles class="w-3.5 h-3.5 text-blue-600" />
              Vista Previa en Vivo
            </span>
            <span class="text-[10px] text-gray-500">Estilo MercadoLibre</span>
          </div>

          <!-- Preview Card -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden pointer-events-none">
            <div class="relative w-full pt-[80%] bg-white border-b border-gray-100 flex items-center justify-center">
              <img
                :src="formData.image_url"
                alt="Preview"
                class="absolute inset-0 w-full h-full object-contain p-4"
                @error="$event.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600'"
              />
              <div v-if="previewDiscount > 0" class="absolute top-2 left-2 bg-[#00A650] text-white font-bold text-[10px] px-2 py-0.5 rounded-xs">
                {{ previewDiscount }}% OFF
              </div>
            </div>

            <div class="p-3 space-y-1.5 text-left">
              <h4 class="text-xs text-gray-800 line-clamp-2 min-h-[2.5rem]">
                {{ formData.title || 'Título del producto...' }}
              </h4>

              <div class="space-y-0.5">
                <div v-if="formData.original_price" class="text-[11px] text-gray-400 line-through">
                  {{ formatCLP(formData.original_price) }}
                </div>
                <div class="flex items-baseline gap-2">
                  <span class="text-lg font-bold text-gray-900">
                    {{ formatCLP(formData.price) }}
                  </span>
                  <span v-if="previewDiscount > 0" class="text-xs font-semibold text-[#00A650]">
                    {{ previewDiscount }}% OFF
                  </span>
                </div>
                <div class="text-[11px] text-gray-600">
                  en {{ formData.installments }}x {{ formatCLP(formData.price / formData.installments) }} sin interés
                </div>
              </div>

              <div v-if="formData.free_shipping" class="flex items-center gap-1 text-[11px] font-bold text-[#00A650]">
                <Zap class="w-3 h-3 fill-[#00A650]" />
                <span>Llega gratis mañana</span>
              </div>

              <div class="pt-2 border-t border-gray-100 flex items-center justify-between text-[10px] text-gray-500">
                <span>Por <strong class="text-gray-700">{{ authStore.intermediateAlias }}</strong></span>
                <div class="flex items-center text-amber-500">
                  <Star class="w-3 h-3 fill-amber-400" />
                  <span class="ml-0.5">5.0 (Nuevo)</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ISO 27001 Note -->
          <div class="text-[10px] text-gray-500 bg-white p-2.5 rounded-sm border border-gray-200 space-y-1">
            <span class="font-bold text-gray-700 block">Garantía de Aislamiento ISO 27001:</span>
            <p>
              El producto se asociará exclusivamente a tu <strong>Cuenta Intermedia ({{ authStore.intermediateAlias }})</strong>.
              Tu correo y credenciales principales no serán expuestos al público.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
