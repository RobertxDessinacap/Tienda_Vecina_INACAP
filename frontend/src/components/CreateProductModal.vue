<script setup>
import { reactive, ref, computed } from 'vue'
import {
  X,
  PlusCircle,
  Upload,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Zap,
  Star,
  FileText,
  Image as ImageIcon,
} from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useProductStore } from '../stores/products'
import { blockDangerousCharsOnKeypress, sanitizeInput, sanitizeEventInput } from '../utils/security'

const authStore = useAuthStore()
const productStore = useProductStore()

const selectedFile = ref(null)
const previewImageSrc = ref('')

const formData = reactive({
  title: '',
  description: '',
  caracteristicas_ads: 'ESPECIFICACIONES ADS OFICIALES: Procesador multinúcleo de 4 nanómetros con inteligencia artificial integrada para tareas de alta demanda, memoria unificada ultra veloz con tasa de transferencia líder en la industria, chasis resistente a impactos y certificación de garantía extendida para uso continuo en todo Chile.',
  price: 199990,
  original_price: null,
  stock: 10,
  category: '',
  image_url: 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=900&auto=format&fit=crop&q=80',
  free_shipping: true,
  installments: 6,
})

const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// ADS Characters Counter (+250 chars requirement)
const adsCharCount = computed(() => (formData.caracteristicas_ads || '').length)
const isAdsValid = computed(() => adsCharCount.value > 250)
const remainingAdsChars = computed(() => Math.max(0, 251 - adsCharCount.value))

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

function handleFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return

  // Validar extensión
  const allowed = ['.jpg', '.jpeg', '.png', '.webp']
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!allowed.includes(ext)) {
    errorMessage.value = `Extensión '${ext}' no permitida por seguridad. Solo se admiten: ${allowed.join(', ')}`
    return
  }

  selectedFile.value = file
  previewImageSrc.value = URL.createObjectURL(file)
  errorMessage.value = ''
}

async function handleSubmit() {
  errorMessage.value = ''
  successMessage.value = ''

  // Sanitización contra inyección de código y ataques XSS (OWASP)
  formData.title = sanitizeInput(formData.title)
  formData.description = sanitizeInput(formData.description)
  formData.caracteristicas_ads = sanitizeInput(formData.caracteristicas_ads)

  if (!formData.title || formData.title.length < 3) {
    errorMessage.value = 'El nombre del producto debe tener al menos 3 caracteres.'
    return
  }
  if (!formData.price || formData.price <= 0) {
    errorMessage.value = 'El precio debe ser mayor a 0.'
    return
  }
  if (!isAdsValid.value) {
    errorMessage.value = `Las características en formato ADS deben contener MÁS DE 250 caracteres (actual: ${adsCharCount.value}). Faltan ${remainingAdsChars.value} caracteres.`
    return
  }

  submitting.value = true

  // Enviar como FormData para soportar subida de archivo y procesamiento Pillow en backend
  const data = new FormData()
  data.append('title', formData.title)
  data.append('description', formData.description)
  data.append('caracteristicas_ads', formData.caracteristicas_ads)
  data.append('price', formData.price)
  if (formData.original_price) {
    data.append('original_price', formData.original_price)
  }
  data.append('stock', formData.stock)
  if (formData.category) {
    data.append('category', formData.category)
  }
  data.append('free_shipping', formData.free_shipping)
  data.append('installments', formData.installments)

  if (selectedFile.value) {
    data.append('image_file', selectedFile.value)
  } else {
    data.append('image_url', formData.image_url)
  }

  const result = await productStore.createProduct(data)
  submitting.value = false

  if (result.success) {
    successMessage.value = '¡Producto publicado con éxito en el catálogo!'
    setTimeout(() => {
      productStore.closeCreateModal()
      successMessage.value = ''
    }, 1500)
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
      class="bg-white rounded-lg shadow-2xl max-w-4xl w-full overflow-hidden border border-gray-200 relative animate-in fade-in zoom-in-95 duration-200 my-auto text-xs"
    >
      <!-- Modal Header -->
      <div class="bg-[#FFE600] px-6 py-4 flex items-center justify-between border-b border-yellow-400">
        <div class="flex items-center gap-2">
          <PlusCircle class="w-5 h-5 text-gray-900" />
          <h2 class="text-sm font-bold text-gray-900">
            Publicar Nuevo Producto en la Tienda
          </h2>
        </div>
        <button
          @click="productStore.closeCreateModal"
          class="w-7 h-7 rounded-full bg-white/80 hover:bg-white flex items-center justify-center text-gray-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- RBAC Guard -->
      <div v-if="!authStore.isSeller" class="p-8 text-center space-y-4">
        <div class="w-12 h-12 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center mx-auto">
          <AlertCircle class="w-6 h-6" />
        </div>
        <h3 class="text-base font-bold text-gray-900">Acceso Exclusivo para Vendedores</h3>
        <p class="text-xs text-gray-600 max-w-md mx-auto">
          Para publicar productos, tu cuenta debe contar con perfil de <strong class="text-gray-900">Vendedor</strong> o <strong class="text-gray-900">Administrador</strong>.
        </p>
        <div class="pt-2 flex justify-center gap-3">
          <button
            @click="productStore.closeCreateModal(); authStore.openAuthModal('register')"
            class="bg-[#3483FA] text-white font-semibold text-xs px-4 py-2 rounded-md hover:bg-blue-600 transition-colors shadow-xs"
          >
            Registrar Cuenta de Vendedor
          </button>
        </div>
      </div>

      <!-- Seller Form & Live 900x600 Preview -->
      <div v-else class="grid grid-cols-1 md:grid-cols-12 gap-6 p-6 max-h-[80vh] overflow-y-auto">
        <!-- Left: Form -->
        <form @submit.prevent="handleSubmit" class="md:col-span-7 space-y-3.5">
          <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 p-3 rounded-md flex items-center gap-2">
            <AlertCircle class="w-4 h-4 shrink-0" />
            <span>{{ errorMessage }}</span>
          </div>
          <div v-if="successMessage" class="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-md flex items-center gap-2">
            <CheckCircle2 class="w-4 h-4 shrink-0" />
            <span>{{ successMessage }}</span>
          </div>

          <!-- Product Name -->
          <div>
            <label class="block font-bold text-gray-700 mb-1">Nombre del Producto *</label>
            <input
              v-model="formData.title"
              type="text"
              @keypress="blockDangerousCharsOnKeypress"
              @input="e => sanitizeEventInput(e, v => formData.title = v)"
              placeholder="Ej: Teclado Mecánico Inalámbrico RGB Switch Brown"
              required
              class="w-full p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
            />
          </div>

          <!-- Category & Stock -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-bold text-gray-700 mb-1">Categoría</label>
              <select
                v-model="formData.category"
                class="w-full p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA] bg-white"
              >
                <option value="">Selecciona categoría</option>
                <option v-for="cat in productStore.categories" :key="cat.id" :value="cat.id">
                  {{ cat.name }}
                </option>
              </select>
            </div>
            <div>
              <label class="block font-bold text-gray-700 mb-1">Stock Disponible *</label>
              <input
                v-model.number="formData.stock"
                type="number"
                min="1"
                required
                class="w-full p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
              />
            </div>
          </div>

          <!-- Price & Original Price -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-bold text-gray-700 mb-1">Precio ($ CLP) *</label>
              <input
                v-model.number="formData.price"
                type="number"
                min="100"
                required
                class="w-full p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
              />
            </div>
            <div>
              <label class="block font-bold text-gray-700 mb-1">Precio Original (Opcional)</label>
              <input
                v-model.number="formData.original_price"
                type="number"
                placeholder="Ej: 249990"
                class="w-full p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
              />
            </div>
          </div>

          <!-- Image Upload -->
          <div class="bg-blue-50/70 p-3 rounded-md border border-blue-200 space-y-2">
            <div class="flex items-center justify-between">
              <label class="block font-bold text-blue-900">
                Fotografía del Producto *
              </label>
              <span class="text-[10px] bg-blue-200 text-blue-900 font-bold px-2 py-0.5 rounded-xs">
                Imagen Oficial
              </span>
            </div>
            <p class="text-[10px] text-blue-800 leading-tight">
              Sube una fotografía clara y nítida (.jpg, .jpeg, .png, .webp). La imagen se adaptará automáticamente para que luzca perfecta en la tienda.
            </p>
            <input
              type="file"
              accept=".jpg,.jpeg,.png,.webp"
              @change="handleFileChange"
              class="w-full text-xs text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
            />
          </div>

          <!-- ADS Characteristics (+250 chars requirement) -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block font-bold text-gray-700">
                Características y Especificaciones del Producto *
              </label>
              <span
                :class="[isAdsValid ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800']"
                class="text-[10px] font-bold px-2 py-0.5 rounded-full"
              >
                {{ adsCharCount }} / 251 mínimos
              </span>
            </div>
            <textarea
              v-model="formData.caracteristicas_ads"
              rows="3"
              @keypress="blockDangerousCharsOnKeypress"
              @input="e => sanitizeEventInput(e, v => formData.caracteristicas_ads = v)"
              placeholder="Ingresa las especificaciones técnicas completas y detalles de uso (mínimo 250 caracteres)..."
              required
              :class="[!isAdsValid ? 'border-red-300 focus:ring-red-400' : 'border-gray-300 focus:ring-[#3483FA]']"
              class="w-full p-2.5 rounded-md border focus:outline-none focus:ring-2 font-mono text-[11px]"
            ></textarea>
            <p v-if="!isAdsValid" class="text-[10px] text-red-600 font-semibold mt-0.5">
              Faltan {{ remainingAdsChars }} caracteres para alcanzar el mínimo requerido de 250 caracteres.
            </p>
            <p v-else class="text-[10px] text-emerald-600 font-semibold mt-0.5 flex items-center gap-1">
              <CheckCircle2 class="w-3 h-3" />
              Especificaciones completas y listas para publicar.
            </p>
          </div>

          <!-- Product Description -->
          <div>
            <label class="block font-bold text-gray-700 mb-1">Descripción del Producto *</label>
            <textarea
              v-model="formData.description"
              rows="2"
              @keypress="blockDangerousCharsOnKeypress"
              @input="e => sanitizeEventInput(e, v => formData.description = v)"
              placeholder="Descripción general, estado y garantía..."
              required
              class="w-full p-2.5 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#3483FA]"
            ></textarea>
          </div>

          <!-- Free Shipping & Installments -->
          <div class="flex items-center justify-between p-2.5 bg-gray-50 rounded-md border border-gray-200">
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="formData.free_shipping" type="checkbox" class="rounded-xs text-[#00A650] focus:ring-[#00A650]" />
              <span class="font-medium text-gray-800">Ofrecer Envío Gratis</span>
            </label>
            <div class="flex items-center gap-2">
              <span class="text-gray-600 font-medium">Cuotas sin interés:</span>
              <select v-model.number="formData.installments" class="p-1 rounded-xs border border-gray-300 bg-white">
                <option :value="3">3x</option>
                <option :value="6">6x</option>
                <option :value="12">12x</option>
              </select>
            </div>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="submitting || !isAdsValid"
            class="w-full bg-[#3483FA] hover:bg-[#2968C8] text-white font-bold py-2.5 rounded-md text-xs uppercase tracking-wider transition-colors disabled:opacity-50 shadow-xs flex items-center justify-center gap-2"
          >
            <span v-if="submitting">Procesando imagen y publicando...</span>
            <span v-else class="flex items-center gap-1.5">
              <span>Publicar Producto en Catálogo</span>
              <CheckCircle2 class="w-4 h-4" />
            </span>
          </button>
        </form>

        <!-- Right: Live Preview Card -->
        <div class="md:col-span-5 flex flex-col justify-start space-y-3 bg-gray-50/70 p-4 rounded-lg border border-gray-200">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-gray-800 flex items-center gap-1.5">
              <Sparkles class="w-3.5 h-3.5 text-blue-600" />
              Vista Previa en Vivo
            </span>
            <span class="text-[10px] text-gray-500">Formato Oficial</span>
          </div>

          <!-- Preview Card -->
          <div class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden pointer-events-none">
            <div class="relative w-full aspect-[9/6] bg-white border-b border-gray-100 flex items-center justify-center overflow-hidden">
              <img
                :src="previewImageSrc || formData.image_url"
                alt="Preview"
                class="max-w-full max-h-full object-contain p-2"
                @error="$event.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=900'"
              />
              <div v-if="previewDiscount > 0" class="absolute top-2 left-2 bg-[#00A650] text-white font-bold text-[10px] px-2 py-0.5 rounded-xs">
                {{ previewDiscount }}% OFF
              </div>
            </div>

            <div class="p-3 space-y-1.5 text-left">
              <h4 class="text-xs font-semibold text-gray-900 line-clamp-2 min-h-[2.5rem]">
                {{ formData.title || 'Nombre del producto...' }}
              </h4>

              <div class="space-y-0.5">
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
                <span class="text-emerald-700 font-semibold">Vendedor Verificado</span>
              </div>
            </div>
          </div>

          <div class="text-[10px] text-gray-600 bg-white p-2.5 rounded-md border border-gray-200 space-y-1">
            <strong class="text-gray-800 block">Recomendación para Vender:</strong>
            <p>
              Las publicaciones con fotografías nítidas y especificaciones detalladas se venden hasta un 40% más rápido en la plataforma.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
