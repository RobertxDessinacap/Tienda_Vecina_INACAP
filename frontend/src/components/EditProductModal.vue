<script setup>
import { ref, computed, watch } from 'vue'
import { useProductStore } from '../stores/products'
import { blockDangerousCharsOnKeypress, sanitizeInput, sanitizeEventInput } from '../utils/security'
import {
  X,
  Upload,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Trash2,
  Plus,
  HelpCircle,
  Image as ImageIcon,
  ExternalLink,
  Save,
} from 'lucide-vue-next'

const productStore = useProductStore()

const form = ref({
  id: '',
  slug: '',
  title: '',
  price: '',
  original_price: '',
  stock: 1,
  category: '',
  caracteristicas_ads: '',
  description: '',
  free_shipping: true,
  installments: 6,
})

const photos = ref([])
const confirmDeleteId = ref(null)
const fileError = ref(null)
const localError = ref(null)
const isSubmitting = ref(false)

// Cargar datos cuando se abre el modal
watch(
  () => productStore.editingProduct,
  (prod) => {
    if (prod) {
      form.value = {
        id: prod.id,
        slug: prod.slug,
        title: prod.title || '',
        price: prod.price || '',
        original_price: prod.original_price || '',
        stock: prod.stock ?? 1,
        category: prod.category || '',
        caracteristicas_ads: prod.caracteristicas_ads || '',
        description: prod.description || '',
        free_shipping: !!prod.free_shipping,
        installments: prod.installments || 6,
      }
      photos.value = []
      if (prod.images && Array.isArray(prod.images) && prod.images.length > 0) {
        photos.value = prod.images.map((u, i) => ({
          id: `existing-${i}`,
          url: u,
          file: null,
          isExisting: true,
        }))
      } else if (prod.display_image_url || prod.image_url) {
        const u = prod.display_image_url || prod.image_url
        photos.value = [
          {
            id: 'existing-0',
            url: u,
            file: null,
            isExisting: true,
          },
        ]
      }
      confirmDeleteId.value = null
      fileError.value = null
      localError.value = null
    }
  },
  { immediate: true }
)

const adsLength = computed(() => (form.value.caracteristicas_ads || '').length)
const isAdsValid = computed(() => adsLength.value > 250)
const adsProgress = computed(() => Math.min(100, Math.round((adsLength.value / 251) * 100)))

function onTitleInput(e) {
  sanitizeEventInput(e, (cleaned) => {
    form.value.title = cleaned
  })
}

function onDescriptionInput(e) {
  sanitizeEventInput(e, (cleaned) => {
    form.value.description = cleaned
  })
}

function onAdsInput(e) {
  sanitizeEventInput(e, (cleaned) => {
    form.value.caracteristicas_ads = cleaned
  })
}

function promptDelete(id) {
  confirmDeleteId.value = id
}

function cancelDelete() {
  confirmDeleteId.value = null
}

function confirmDelete(id) {
  photos.value = photos.value.filter((p) => p.id !== id)
  confirmDeleteId.value = null
}

function handleFilesSelect(e) {
  const files = Array.from(e.target.files || [])
  if (!files.length) return
  fileError.value = null

  const allowed = ['.jpg', '.jpeg', '.png', '.webp']
  for (const file of files) {
    if (photos.value.length >= 5) {
      fileError.value = 'Se alcanzó el límite máximo de 5 fotografías por publicación.'
      break
    }
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!allowed.includes(ext)) {
      fileError.value = `Extensión '${ext}' no permitida. Solo se admiten: ${allowed.join(', ')}`
      continue
    }
    photos.value.push({
      id: 'file-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7),
      url: URL.createObjectURL(file),
      file: file,
      isExisting: false,
    })
  }
  e.target.value = ''
}

function handleDrop(e) {
  e.preventDefault()
  const files = e.dataTransfer.files
  if (files && files.length) {
    handleFilesSelect({ target: { files } })
  }
}

async function executeSave(redirectAfter = false) {
  localError.value = null

  if (!form.value.title.trim()) {
    localError.value = 'El título de la publicación es obligatorio.'
    return
  }

  if (!form.value.price || Number(form.value.price) <= 0) {
    localError.value = 'El precio debe ser un valor positivo.'
    return
  }

  if (!isAdsValid.value) {
    localError.value = `Las características en ADS deben contener más de 250 caracteres (actual: ${adsLength.value}).`
    return
  }

  if (photos.value.length === 0) {
    localError.value = 'Debes mantener al menos una fotografía para la publicación.'
    return
  }

  isSubmitting.value = true

  const formData = new FormData()
  formData.append('title', sanitizeInput(form.value.title))
  formData.append('price', form.value.price)
  if (form.value.original_price) {
    formData.append('original_price', form.value.original_price)
  }
  formData.append('stock', form.value.stock)
  if (form.value.category) {
    formData.append('category', form.value.category)
  }
  formData.append('caracteristicas_ads', sanitizeInput(form.value.caracteristicas_ads))
  formData.append('description', sanitizeInput(form.value.description))
  formData.append('free_shipping', form.value.free_shipping)
  formData.append('installments', form.value.installments)

  const existingUrls = []
  photos.value.forEach((p) => {
    if (p.file) {
      formData.append('image_files', p.file)
    } else if (p.url) {
      existingUrls.push(p.url)
    }
  })
  if (existingUrls.length > 0) {
    formData.append('existing_images', JSON.stringify(existingUrls))
    formData.append('image_url', existingUrls[0])
  } else if (photos.value.length > 0 && photos.value[0].file) {
    formData.append('image_file', photos.value[0].file)
  }

  const res = await productStore.updateProduct(form.value.slug, formData)
  isSubmitting.value = false

  if (res.success) {
    productStore.closeEditModal()
    if (redirectAfter && res.product?.slug) {
      productStore.fetchProductBySlug(res.product.slug)
    }
  } else {
    localError.value = res.error || 'No se pudo guardar la publicación.'
  }
}
</script>

<template>
  <div
    v-if="productStore.editModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto animate-in fade-in duration-200"
  >
    <div class="bg-brand-surface rounded-2xl max-w-2xl w-full max-h-[92vh] flex flex-col shadow-2xl border border-brand-border my-auto">
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-brand-border flex items-center justify-between sticky top-0 bg-brand-surface z-10 rounded-t-2xl">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-blue-50 text-brand-accent flex items-center justify-center font-bold">
            <ImageIcon class="w-4 h-4" />
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-900 leading-tight">
              Editar Publicación
            </h3>
          </div>
        </div>
        <button
          @click="productStore.closeEditModal()"
          class="text-slate-400 hover:text-slate-600 p-1 rounded-lg transition-colors cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Modal Body (Scrollable) -->
      <form @submit.prevent="executeSave(false)" class="p-6 space-y-5 overflow-y-auto flex-1">
        <!-- Error Banner -->
        <div
          v-if="localError"
          class="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2"
        >
          <AlertCircle class="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
          <span>{{ localError }}</span>
        </div>

        <!-- 1. Título del Producto -->
        <div class="space-y-1">
          <label class="block text-xs font-bold text-slate-700">
            Título de la Publicación <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.title"
            type="text"
            @keypress="blockDangerousCharsOnKeypress"
            @input="onTitleInput"
            placeholder="Ej: Teclado Mecánico Custom Pro RGB Wireless"
            class="w-full bg-slate-50 border border-brand-border focus:border-brand-accent focus:bg-white rounded-lg px-3.5 py-2 text-xs text-slate-800 focus:outline-none transition-colors"
          />
          <p class="text-[10px] text-slate-400">
            Si modificas el título, se actualizará automáticamente en toda la plataforma.
          </p>
        </div>

        <!-- 2. Precios y Stock -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="space-y-1">
            <label class="block text-xs font-bold text-slate-700">
              Precio de Venta (CLP) <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.price"
              type="number"
              min="1"
              step="1"
              placeholder="Ej: 89990"
              class="w-full bg-slate-50 border border-brand-border focus:border-brand-accent focus:bg-white rounded-lg px-3.5 py-2 text-xs text-slate-800 focus:outline-none"
            />
          </div>

          <div class="space-y-1">
            <label class="block text-xs font-bold text-slate-700">
              Precio Anterior / Lista (Opcional)
            </label>
            <input
              v-model="form.original_price"
              type="number"
              min="0"
              step="1"
              placeholder="Ej: 119990"
              class="w-full bg-slate-50 border border-brand-border focus:border-brand-accent focus:bg-white rounded-lg px-3.5 py-2 text-xs text-slate-800 focus:outline-none"
            />
          </div>

          <div class="space-y-1">
            <label class="block text-xs font-bold text-slate-700">
              Stock Disponible <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.stock"
              type="number"
              min="0"
              step="1"
              class="w-full bg-slate-50 border border-brand-border focus:border-brand-accent focus:bg-white rounded-lg px-3.5 py-2 text-xs text-slate-800 focus:outline-none"
            />
          </div>
        </div>

        <!-- 3. Categoría -->
        <div class="space-y-1">
          <label class="block text-xs font-bold text-slate-700">
            Categoría del Producto
          </label>
          <select
            v-model="form.category"
            class="w-full bg-slate-50 border border-brand-border focus:border-brand-accent focus:bg-white rounded-lg px-3.5 py-2 text-xs text-slate-800 focus:outline-none"
          >
            <option value="">Selecciona una categoría...</option>
            <option
              v-for="cat in productStore.categories"
              :key="cat.id"
              :value="cat.id"
            >
              {{ cat.name }}
            </option>
          </select>
        </div>

        <!-- 4. Requisito ADS (+250 Caracteres) -->
        <div class="space-y-2 bg-slate-50 p-3.5 rounded-xl border border-brand-border">
          <div class="flex items-center justify-between">
            <label class="block text-xs font-bold text-slate-800">
              Especificaciones en ADS (+250 Caracteres Obligatorios) <span class="text-red-500">*</span>
            </label>
            <span
              :class="isAdsValid ? 'text-emerald-600 bg-emerald-50' : 'text-amber-600 bg-amber-50'"
              class="text-[11px] font-mono font-bold px-2 py-0.5 rounded-md"
            >
              {{ adsLength }} / 251 car.
            </span>
          </div>

          <!-- Progress Bar -->
          <div class="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
            <div
              :style="{ width: `${adsProgress}%` }"
              :class="isAdsValid ? 'bg-emerald-500' : 'bg-amber-500'"
              class="h-full transition-all duration-200"
            ></div>
          </div>

          <textarea
            v-model="form.caracteristicas_ads"
            @keypress="blockDangerousCharsOnKeypress"
            @input="onAdsInput"
            rows="4"
            placeholder="Ingresa las especificaciones completas para publicidad ADS (procesador, componentes, compatibilidad, certificaciones y garantía)..."
            class="w-full bg-white border border-brand-border focus:border-brand-accent rounded-lg p-3 text-xs text-slate-800 focus:outline-none leading-relaxed"
          ></textarea>

          <p v-if="!isAdsValid" class="text-[11px] text-amber-700 font-medium">
            Faltan {{ 251 - adsLength }} caracteres para cumplir con la validación de ADS.
          </p>
        </div>

        <!-- 5. Descripción General -->
        <div class="space-y-1">
          <label class="block text-xs font-bold text-slate-700">
            Descripción General del Producto
          </label>
          <textarea
            v-model="form.description"
            @keypress="blockDangerousCharsOnKeypress"
            @input="onDescriptionInput"
            rows="3"
            placeholder="Detalles sobre el uso, empaque y condiciones del producto..."
            class="w-full bg-slate-50 border border-brand-border focus:border-brand-accent focus:bg-white rounded-lg p-3 text-xs text-slate-800 focus:outline-none"
          ></textarea>
        </div>

        <!-- 6. Fotografías de la Publicación (Hasta 5 fotos) -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <label class="block text-xs font-bold text-slate-700 flex items-center gap-1.5">
              <ImageIcon class="w-4 h-4 text-brand-accent" />
              Fotografías de la Publicación
              <span class="text-xs font-semibold text-slate-500">({{ photos.length }}/5 fotos)</span>
            </label>
            <span
              :class="[photos.length >= 5 ? 'bg-amber-100 text-amber-800' : 'bg-blue-50 text-brand-accent']"
              class="text-[10px] font-bold px-2 py-0.5 rounded-full"
            >
              {{ photos.length >= 5 ? 'Máximo alcanzado (5/5)' : 'Hasta 5 fotos' }}
            </span>
          </div>
          <p class="text-[10px] text-slate-500 leading-tight">
            Pasa el cursor sobre cualquier fotografía para ver la opción de eliminarla con confirmación.
          </p>

          <!-- Photos Grid -->
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2.5 pt-1">
            <!-- Photo Cards -->
            <div
              v-for="(photo, index) in photos"
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
              v-if="photos.length < 5"
              @click="$refs.editFileInput.click()"
              @dragover.prevent
              @drop="handleDrop"
              class="border-2 border-dashed border-brand-border hover:border-brand-accent rounded-xl aspect-[9/6] flex flex-col items-center justify-center text-center p-2 cursor-pointer bg-white/70 hover:bg-blue-50/50 transition-colors group"
            >
              <div class="w-7 h-7 rounded-full bg-blue-50 group-hover:bg-blue-100 text-brand-accent flex items-center justify-center mb-1 transition-colors">
                <Plus class="w-4 h-4" />
              </div>
              <span class="text-[11px] font-bold text-slate-700 group-hover:text-brand-accent transition-colors">
                Agregar foto
              </span>
              <span class="text-[9px] text-slate-400">
                ({{ 5 - photos.length }} disponibles)
              </span>
            </div>
          </div>

          <input
            ref="editFileInput"
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp"
            class="hidden"
            @change="handleFilesSelect"
          />
          <p v-if="fileError" class="text-xs text-red-600 font-medium">{{ fileError }}</p>
        </div>

        <!-- 7. Opciones de Despacho y Cuotas -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-brand-border">
          <label class="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-700">
            <input
              type="checkbox"
              v-model="form.free_shipping"
              class="w-4 h-4 text-brand-accent rounded border-brand-border focus:ring-brand-accent"
            />
            <span>Ofrecer Envío Gratis en todo Chile</span>
          </label>

          <div class="flex items-center gap-2 text-xs">
            <span class="font-semibold text-slate-700">Hasta</span>
            <select
              v-model="form.installments"
              class="bg-slate-50 border border-brand-border rounded px-2 py-1 text-xs text-slate-800"
            >
              <option :value="3">3 cuotas sin interés</option>
              <option :value="6">6 cuotas sin interés</option>
              <option :value="12">12 cuotas sin interés</option>
            </select>
          </div>
        </div>
      </form>

      <!-- Modal Footer with Required Action Buttons -->
      <div class="px-6 py-4 border-t border-brand-border bg-slate-50 rounded-b-2xl flex flex-col sm:flex-row items-center justify-between gap-3">
        <button
          type="button"
          @click="productStore.closeEditModal()"
          class="w-full sm:w-auto px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 transition-colors cursor-pointer"
        >
          Cancelar
        </button>

        <div class="flex flex-col sm:flex-row items-center gap-2.5 w-full sm:w-auto">
          <!-- Botón 1: Solo Guardar -->
          <button
            type="button"
            :disabled="isSubmitting || !isAdsValid"
            @click="executeSave(false)"
            class="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs py-2.5 px-4 rounded-xl transition-all shadow-xs disabled:opacity-50 cursor-pointer"
          >
            <Save class="w-3.5 h-3.5" />
            <span>{{ isSubmitting ? 'Guardando...' : 'Guardar' }}</span>
          </button>

          <!-- Botón 2: Guardar y ver página de venta -->
          <button
            type="button"
            :disabled="isSubmitting || !isAdsValid"
            @click="executeSave(true)"
            class="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 bg-brand-accent hover:bg-brand-accent-hover text-white font-bold text-xs py-2.5 px-5 rounded-xl transition-all shadow-md hover:shadow-lg disabled:opacity-50 cursor-pointer"
          >
            <span>{{ isSubmitting ? 'Guardando...' : 'Guardar y ver página de venta' }}</span>
            <ExternalLink class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
