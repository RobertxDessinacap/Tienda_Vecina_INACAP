<script setup>
import { ref, computed, watch } from 'vue'
import { useProductStore } from '../stores/products'
import { blockDangerousCharsOnKeypress, sanitizeInput, sanitizeEventInput } from '../utils/security'
import {
  X,
  Upload,
  CheckCircle2,
  AlertCircle,
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

const selectedFile = ref(null)
const previewUrl = ref(null)
const currentImageUrl = ref(null)
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
      currentImageUrl.value = prod.display_image_url || prod.image_url
      selectedFile.value = null
      previewUrl.value = null
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

function handleFileSelect(e) {
  const file = e.target.files[0]
  if (!file) return

  fileError.value = null
  const allowed = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowed.includes(file.type)) {
    fileError.value = 'Formato no admitido. Debe ser JPG, PNG o WEBP.'
    return
  }

  // Previsualización local
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
}

function handleDrop(e) {
  e.preventDefault()
  const file = e.dataTransfer.files[0]
  if (file) {
    const input = { target: { files: [file] } }
    handleFileSelect(input)
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

  if (selectedFile.value) {
    formData.append('image_file', selectedFile.value)
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
            <p class="text-[11px] text-slate-500 font-mono">
              /producto/{{ form.slug }}
            </p>
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
            Si modificas el título, la URL limpia (/producto/slug) se actualizará automáticamente.
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

        <!-- 6. Fotografía del Producto (Pillow 900x600) -->
        <div class="space-y-2">
          <label class="block text-xs font-bold text-slate-700">
            Fotografía de la Publicación (Resolución exacta 900x600 y ≤ 1 MB)
          </label>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
            <!-- Current Image -->
            <div class="space-y-1">
              <span class="text-[10px] text-slate-500 font-medium block">Imagen Actual:</span>
              <div class="bg-slate-100 border border-brand-border rounded-lg aspect-[9/6] overflow-hidden flex items-center justify-center">
                <img
                  v-if="previewUrl || currentImageUrl"
                  :src="previewUrl || currentImageUrl"
                  alt="Vista previa"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-xs text-slate-400">Sin imagen</span>
              </div>
            </div>

            <!-- Upload New Image Box -->
            <div
              @dragover.prevent
              @drop="handleDrop"
              class="border-2 border-dashed border-brand-border hover:border-brand-accent rounded-xl p-4 text-center cursor-pointer transition-colors bg-slate-50 hover:bg-blue-50/40 aspect-[9/6] flex flex-col items-center justify-center"
              @click="$refs.fileInput.click()"
            >
              <input
                ref="fileInput"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                class="hidden"
                @change="handleFileSelect"
              />
              <Upload class="w-6 h-6 text-slate-400 mb-1" />
              <span class="text-xs font-bold text-brand-accent block">
                {{ selectedFile ? 'Cambiar archivo seleccionado' : 'Subir nueva imagen' }}
              </span>
              <span class="text-[10px] text-slate-400 block mt-0.5">
                JPG, PNG o WEBP (Pillow normalizará a 900x600)
              </span>
            </div>
          </div>
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
