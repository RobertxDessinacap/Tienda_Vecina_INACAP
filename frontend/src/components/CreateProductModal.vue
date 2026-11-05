<script setup>
import { reactive, ref, computed } from 'vue'
import {
  X,
  PlusCircle,
  Plus,
  Upload,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Trash2,
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

// Lista de fotografías (hasta 5 fotos por producto)
const photoList = ref([
  {
    id: 'default-1',
    url: 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=900&auto=format&fit=crop&q=80',
    file: null,
    isExisting: true,
  },
])
const confirmDeleteId = ref(null)

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

function promptDelete(id) {
  confirmDeleteId.value = id
}

function cancelDelete() {
  confirmDeleteId.value = null
}

function confirmDelete(id) {
  photoList.value = photoList.value.filter((p) => p.id !== id)
  confirmDeleteId.value = null
}

function handleFilesChange(event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  errorMessage.value = ''

  const allowed = ['.jpg', '.jpeg', '.png', '.webp']
  for (const file of files) {
    if (photoList.value.length >= 5) {
      errorMessage.value = 'Se alcanzó el límite máximo de 5 fotografías por producto.'
      break
    }
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!allowed.includes(ext)) {
      errorMessage.value = `Extensión '${ext}' no permitida. Solo se admiten: ${allowed.join(', ')}`
      continue
    }
    photoList.value.push({
      id: 'file-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7),
      url: URL.createObjectURL(file),
      file: file,
      isExisting: false,
    })
  }
  event.target.value = ''
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
  if (photoList.value.length === 0) {
    errorMessage.value = 'Debes subir al menos una fotografía para publicar el producto.'
    return
  }

  submitting.value = true

  // Enviar como FormData para soportar subida de múltiples archivos (hasta 5)
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

  const existingUrls = []
  photoList.value.forEach((p) => {
    if (p.file) {
      data.append('image_files', p.file)
    } else if (p.url) {
      existingUrls.push(p.url)
    }
  })
  if (existingUrls.length > 0) {
    data.append('existing_images', JSON.stringify(existingUrls))
    data.append('image_url', existingUrls[0])
  } else if (photoList.value.length > 0 && photoList.value[0].file) {
    data.append('image_file', photoList.value[0].file)
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
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto"
  >
    <div
      class="bg-brand-surface rounded-2xl shadow-xl max-w-4xl w-full overflow-hidden border border-brand-border relative animate-in fade-in zoom-in-95 duration-200 my-auto text-xs"
    >
      <!-- Modal Header -->
      <div class="bg-brand-primary px-6 py-4 flex items-center justify-between border-b border-brand-primary-border">
        <div class="flex items-center gap-2">
          <PlusCircle class="w-5 h-5 text-brand-primary-text" />
          <h2 class="text-sm font-bold text-slate-900">
            Publicar Nuevo Producto en la Tienda
          </h2>
        </div>
        <button
          @click="productStore.closeCreateModal"
          class="w-7 h-7 rounded-full bg-brand-surface/80 hover:bg-brand-surface flex items-center justify-center text-slate-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- RBAC Guard -->
      <div v-if="!authStore.isSeller" class="p-8 text-center space-y-4">
        <div class="w-12 h-12 bg-brand-primary-subtle text-brand-primary-text rounded-full flex items-center justify-center mx-auto">
          <AlertCircle class="w-6 h-6" />
        </div>
        <h3 class="text-base font-bold text-slate-900">Acceso Exclusivo para Vendedores</h3>
        <p class="text-xs text-slate-600 max-w-md mx-auto">
          Para publicar productos, tu cuenta debe contar con perfil de <strong class="text-slate-900">Vendedor</strong> o <strong class="text-slate-900">Administrador</strong>.
        </p>
        <div class="pt-2 flex justify-center gap-3">
          <button
            @click="productStore.closeCreateModal(); authStore.openAuthModal('register')"
            class="bg-brand-accent hover:bg-brand-accent-hover text-white font-semibold text-xs px-4 py-2 rounded-lg transition-colors shadow-xs"
          >
            Registrar Cuenta de Vendedor
          </button>
        </div>
      </div>

      <!-- Seller Form & Live Preview -->
      <div v-else class="grid grid-cols-1 md:grid-cols-12 gap-6 p-6 max-h-[80vh] overflow-y-auto">
        <!-- Left: Form -->
        <form @submit.prevent="handleSubmit" class="md:col-span-7 space-y-3.5">
          <div v-if="errorMessage" class="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg flex items-center gap-2">
            <AlertCircle class="w-4 h-4 shrink-0" />
            <span>{{ errorMessage }}</span>
          </div>
          <div v-if="successMessage" class="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-lg flex items-center gap-2">
            <CheckCircle2 class="w-4 h-4 shrink-0" />
            <span>{{ successMessage }}</span>
          </div>

          <!-- Product Name -->
          <div>
            <label class="block font-bold text-slate-700 mb-1">Nombre del Producto *</label>
            <input
              v-model="formData.title"
              type="text"
              @keypress="blockDangerousCharsOnKeypress"
              @input="e => sanitizeEventInput(e, v => formData.title = v)"
              placeholder="Ej: Teclado Mecánico Inalámbrico RGB Switch Brown"
              required
              class="w-full p-2.5 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
            />
          </div>

          <!-- Category & Stock -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-bold text-slate-700 mb-1">Categoría</label>
              <select
                v-model="formData.category"
                class="w-full p-2.5 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent bg-brand-surface"
              >
                <option value="">Selecciona categoría</option>
                <option v-for="cat in productStore.categories" :key="cat.id" :value="cat.id">
                  {{ cat.name }}
                </option>
              </select>
            </div>
            <div>
              <label class="block font-bold text-slate-700 mb-1">Stock Disponible *</label>
              <input
                v-model.number="formData.stock"
                type="number"
                min="1"
                required
                class="w-full p-2.5 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
              />
            </div>
          </div>

          <!-- Price & Original Price -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-bold text-slate-700 mb-1">Precio ($ CLP) *</label>
              <input
                v-model.number="formData.price"
                type="number"
                min="100"
                required
                class="w-full p-2.5 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
              />
            </div>
            <div>
              <label class="block font-bold text-slate-700 mb-1">Precio Original (Opcional)</label>
              <input
                v-model.number="formData.original_price"
                type="number"
                placeholder="Ej: 249990"
                class="w-full p-2.5 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
              />
            </div>
          </div>

          <!-- Image Upload (Up to 5 photos) -->
          <div class="bg-brand-primary-subtle p-3.5 rounded-xl border border-brand-primary-border space-y-2.5">
            <div class="flex items-center justify-between">
              <label class="block font-bold text-brand-primary-text flex items-center gap-1.5">
                <ImageIcon class="w-4 h-4 text-brand-accent" />
                Fotografías del Producto
                <span class="text-xs font-semibold text-slate-500">({{ photoList.length }}/5 fotos)</span>
              </label>
              <span
                :class="[photoList.length >= 5 ? 'bg-amber-100 text-amber-800' : 'bg-brand-primary text-brand-primary-text']"
                class="text-[10px] font-bold px-2 py-0.5 rounded-full"
              >
                {{ photoList.length >= 5 ? 'Máximo alcanzado (5/5)' : 'Hasta 5 fotos' }}
              </span>
            </div>
            <p class="text-[10px] text-slate-600 leading-tight">
              Sube hasta 5 fotografías (.jpg, .jpeg, .png, .webp). Pasa el cursor sobre cualquier foto para ver la opción de eliminarla con confirmación.
            </p>

            <!-- Photos Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2.5 pt-1">
              <!-- Photo Cards -->
              <div
                v-for="(photo, index) in photoList"
                :key="photo.id"
                class="group relative aspect-[9/6] rounded-xl overflow-hidden border border-brand-border bg-slate-100 shadow-2xs"
              >
                <img
                  :src="photo.url"
                  :alt="`Foto ${index + 1}`"
                  class="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                />

                <!-- Primary Badge -->
                <div v-if="index === 0" class="absolute top-1.5 left-1.5 z-10 bg-brand-accent text-white text-[9px] font-black px-1.5 py-0.5 rounded shadow-xs pointer-events-none">
                  Portada
                </div>

                <!-- Hover Overlay with Delete Option (Covers Entire Image) -->
                <div
                  v-if="confirmDeleteId !== photo.id"
                  @click.stop="promptDelete(photo.id)"
                  class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col items-center justify-center gap-1 p-2 cursor-pointer z-10 text-white"
                >
                  <div class="w-8 h-8 rounded-full bg-red-600/90 hover:bg-red-600 flex items-center justify-center shadow-md transition-transform hover:scale-110">
                    <Trash2 class="w-4 h-4 text-white" />
                  </div>
                  <span class="text-[10px] font-bold text-white tracking-wide">Eliminar foto</span>
                </div>

                <!-- Confirmation Prompt Overlay (Covers Entire Image) -->
                <div
                  v-else
                  @click.stop
                  class="absolute inset-0 bg-slate-900/95 p-2 flex flex-col items-center justify-center text-center gap-1.5 z-20 animate-in fade-in duration-150"
                >
                  <AlertTriangle class="w-4 h-4 text-amber-400" />
                  <p class="text-[10px] font-bold text-white leading-tight">
                    ¿Eliminar foto?
                  </p>
                  <div class="flex items-center gap-1 mt-0.5">
                    <button
                      type="button"
                      @click.stop="confirmDelete(photo.id)"
                      class="px-2 py-0.5 bg-red-600 hover:bg-red-700 text-white text-[9px] font-bold rounded transition-colors cursor-pointer shadow-xs"
                    >
                      Sí
                    </button>
                    <button
                      type="button"
                      @click.stop="cancelDelete()"
                      class="px-2 py-0.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-[9px] font-bold rounded transition-colors cursor-pointer"
                    >
                      No
                    </button>
                  </div>
                </div>
              </div>

              <!-- Add Photo Button Box (if < 5) -->
              <div
                v-if="photoList.length < 5"
                @click="$refs.multiFileInput.click()"
                class="border-2 border-dashed border-brand-border hover:border-brand-accent rounded-xl aspect-[9/6] flex flex-col items-center justify-center text-center p-2 cursor-pointer bg-white/70 hover:bg-blue-50/50 transition-colors group"
              >
                <div class="w-7 h-7 rounded-full bg-blue-50 group-hover:bg-blue-100 text-brand-accent flex items-center justify-center mb-1 transition-colors">
                  <Plus class="w-4 h-4" />
                </div>
                <span class="text-[11px] font-bold text-slate-700 group-hover:text-brand-accent transition-colors">
                  Agregar foto
                </span>
                <span class="text-[9px] text-slate-400">
                  ({{ 5 - photoList.length }} disponibles)
                </span>
              </div>
            </div>

            <input
              ref="multiFileInput"
              type="file"
              multiple
              accept="image/jpeg,image/png,image/webp"
              class="hidden"
              @change="handleFilesChange"
            />
          </div>

          <!-- ADS Characteristics (+250 chars requirement) -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block font-bold text-slate-700">
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
              :class="[!isAdsValid ? 'border-red-300 focus:ring-red-400' : 'border-brand-border focus:ring-brand-accent']"
              class="w-full p-2.5 rounded-lg border focus:outline-none focus:ring-2 font-mono text-[11px]"
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
            <label class="block font-bold text-slate-700 mb-1">Descripción del Producto *</label>
            <textarea
              v-model="formData.description"
              rows="2"
              @keypress="blockDangerousCharsOnKeypress"
              @input="e => sanitizeEventInput(e, v => formData.description = v)"
              placeholder="Descripción general, estado y garantía..."
              required
              class="w-full p-2.5 rounded-lg border border-brand-border focus:outline-none focus:ring-2 focus:ring-brand-accent"
            ></textarea>
          </div>

          <!-- Free Shipping & Installments -->
          <div class="flex items-center justify-between p-2.5 bg-brand-surface-subtle rounded-lg border border-brand-border">
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="formData.free_shipping" type="checkbox" class="rounded-xs text-brand-accent focus:ring-brand-accent" />
              <span class="font-medium text-slate-800">Ofrecer Envío Gratis</span>
            </label>
            <div class="flex items-center gap-2">
              <span class="text-slate-600 font-medium">Cuotas sin interés:</span>
              <select v-model.number="formData.installments" class="p-1 rounded-md border border-brand-border bg-brand-surface">
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
            class="w-full bg-brand-accent hover:bg-brand-accent-hover text-white font-bold py-2.5 rounded-lg text-xs uppercase tracking-wider transition-colors disabled:opacity-50 shadow-xs flex items-center justify-center gap-2"
          >
            <span v-if="submitting">Procesando imagen y publicando...</span>
            <span v-else class="flex items-center gap-1.5">
              <span>Publicar Producto en Catálogo</span>
              <CheckCircle2 class="w-4 h-4" />
            </span>
          </button>
        </form>

        <!-- Right: Live Preview Card -->
        <div class="md:col-span-5 flex flex-col justify-start space-y-3 bg-brand-surface-subtle p-4 rounded-xl border border-brand-border">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-800 flex items-center gap-1.5">
              <Sparkles class="w-3.5 h-3.5 text-brand-accent" />
              Vista Previa en Vivo
            </span>
            <span class="text-[10px] text-slate-500">Formato Oficial</span>
          </div>

          <!-- Preview Card -->
          <div class="bg-brand-surface rounded-xl border border-brand-border shadow-2xs overflow-hidden pointer-events-none">
            <div class="relative w-full aspect-[9/6] bg-brand-surface border-b border-brand-border/60 flex items-center justify-center overflow-hidden">
              <img
                :src="previewImageSrc || formData.image_url"
                alt="Preview"
                class="max-w-full max-h-full object-contain p-2"
                @error="$event.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=900'"
              />
              <div v-if="previewDiscount > 0" class="absolute top-2 left-2 bg-brand-accent text-white font-bold text-[10px] px-2 py-0.5 rounded-full">
                {{ previewDiscount }}% OFF
              </div>
            </div>

            <div class="p-3 space-y-1.5 text-left">
              <h4 class="text-xs font-semibold text-slate-900 line-clamp-2 min-h-[2.5rem]">
                {{ formData.title || 'Nombre del producto...' }}
              </h4>

              <div class="space-y-0.5">
                <div class="flex items-baseline gap-2">
                  <span class="text-lg font-bold text-slate-900">
                    {{ formatCLP(formData.price) }}
                  </span>
                  <span v-if="previewDiscount > 0" class="text-xs font-semibold text-brand-accent">
                    {{ previewDiscount }}% OFF
                  </span>
                </div>
                <div class="text-[11px] text-slate-600">
                  en {{ formData.installments }}x {{ formatCLP(formData.price / formData.installments) }} sin interés
                </div>
              </div>

              <div v-if="formData.free_shipping" class="flex items-center gap-1 text-[11px] font-bold text-emerald-600">
                <Zap class="w-3 h-3 fill-emerald-600" />
                <span>Llega gratis mañana</span>
              </div>

              <div class="pt-2 border-t border-brand-border/60 flex items-center justify-between text-[10px] text-slate-500">
                <span>Por <strong class="text-slate-700">{{ authStore.intermediateAlias }}</strong></span>
                <span class="text-emerald-700 font-semibold">Vendedor Verificado</span>
              </div>
            </div>
          </div>

          <div class="text-[10px] text-slate-600 bg-brand-surface p-2.5 rounded-lg border border-brand-border space-y-1 shadow-2xs">
            <strong class="text-slate-800 block">Recomendación para Vender:</strong>
            <p>
              Las publicaciones con fotografías nítidas y especificaciones detalladas se venden hasta un 40% más rápido en la plataforma.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
