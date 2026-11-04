<script setup>
import { ref, computed, watch } from 'vue'
import {
  X,
  SlidersHorizontal,
  Search,
  RotateCcw,
  Tag,
  Truck,
  Check,
  ChevronDown,
} from 'lucide-vue-next'
import { useProductStore } from '../stores/products'

const productStore = useProductStore()

// Límites dinámicos obtenidos del catálogo o valores predeterminados
const catalogMin = computed(() => productStore.priceBounds?.min ?? 30000)
const catalogMax = computed(() => productStore.priceBounds?.max ?? 2500000)
const step = 5000

// Estado local para editar antes de confirmar
const localMin = ref(30000)
const localMax = ref(2500000)
const localCategory = ref(null)
const localSearch = ref('')
const localFreeShipping = ref(false)

// Sincronizar estado local al abrir el modal
watch(
  () => productStore.filterModalOpen,
  (isOpen) => {
    if (isOpen) {
      localMin.value = productStore.minPrice !== null ? productStore.minPrice : catalogMin.value
      localMax.value = productStore.maxPrice !== null ? productStore.maxPrice : catalogMax.value
      localCategory.value = productStore.activeCategory
      localSearch.value = productStore.searchQuery || ''
      localFreeShipping.value = productStore.onlyFreeShipping || false
    }
  },
  { immediate: true }
)

// Cálculo porcentual para posicionar la barra de color entre los dos thumbs
const minPercent = computed(() => {
  const range = catalogMax.value - catalogMin.value
  if (range <= 0) return 0
  const pct = ((localMin.value - catalogMin.value) / range) * 100
  return Math.max(0, Math.min(100, pct))
})

const maxPercent = computed(() => {
  const range = catalogMax.value - catalogMin.value
  if (range <= 0) return 100
  const pct = ((localMax.value - catalogMin.value) / range) * 100
  return Math.max(0, Math.min(100, pct))
})

function handleMinInput(e) {
  const val = Number(e.target.value)
  if (val > localMax.value - step) {
    localMin.value = localMax.value - step
  } else {
    localMin.value = val
  }
}

function handleMaxInput(e) {
  const val = Number(e.target.value)
  if (val < localMin.value + step) {
    localMax.value = localMin.value + step
  } else {
    localMax.value = val
  }
}

function setQuickRange(min, max) {
  localMin.value = min !== null ? min : catalogMin.value
  localMax.value = max !== null ? max : catalogMax.value
}

function formatCLP(val) {
  if (val === null || val === undefined || isNaN(val)) return '$0'
  return '$' + Math.round(val).toLocaleString('es-CL')
}

function resetLocalFilters() {
  localMin.value = catalogMin.value
  localMax.value = catalogMax.value
  localCategory.value = null
  localSearch.value = ''
  localFreeShipping.value = false
}

function applyAndClose() {
  const finalMin = localMin.value > catalogMin.value ? localMin.value : null
  const finalMax = localMax.value < catalogMax.value ? localMax.value : null

  productStore.applyFilters({
    minPrice: finalMin,
    maxPrice: finalMax,
    category: localCategory.value,
    searchQuery: localSearch.value,
    onlyFreeShipping: localFreeShipping.value,
  })
}

function clearAllAndClose() {
  resetLocalFilters()
  productStore.clearAllFilters()
  productStore.closeFilterModal()
}
</script>

<template>
  <div
    v-if="productStore.filterModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto"
    @click.self="productStore.closeFilterModal"
  >
    <div
      class="bg-brand-surface rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-brand-border relative animate-in fade-in zoom-in-95 duration-200 my-auto text-xs"
    >
      <!-- Modal Header -->
      <div class="bg-brand-primary px-6 py-4 flex items-center justify-between border-b border-brand-primary-border">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-brand-surface flex items-center justify-center shadow-xs">
            <SlidersHorizontal class="w-4 h-4 text-brand-accent" />
          </div>
          <div>
            <h2 class="text-sm font-bold text-slate-900 leading-tight">
              Filtrar Catálogo
            </h2>
            <span class="text-[10px] text-brand-primary-text font-semibold">
              Personaliza tu búsqueda en Mercado Inacap
            </span>
          </div>
        </div>
        <button
          @click="productStore.closeFilterModal"
          class="w-7 h-7 rounded-full bg-brand-surface/80 hover:bg-brand-surface flex items-center justify-center text-slate-700 transition-colors cursor-pointer"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Quick Summary Toolbar (Estilo SoloTodo con Resultados y Borrar Filtros) -->
      <div class="px-6 py-2.5 bg-brand-surface-subtle border-b border-brand-border flex items-center justify-between text-xs">
        <span class="font-extrabold text-[#f97316] text-[11px] tracking-wide">
          {{ productStore.products.length }} RESULTADOS
        </span>
        <button
          type="button"
          @click="resetLocalFilters"
          class="text-[11px] font-bold text-[#f97316] hover:underline uppercase tracking-wider flex items-center gap-1 cursor-pointer"
        >
          <RotateCcw class="w-3 h-3" />
          <span>Borrar filtros</span>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 space-y-5">
        <!-- 1. SECCIÓN PRECIO: DUAL RANGE SLIDER (Estilo SoloTodo / E-commerce) -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <label class="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Precio
            </label>
            <div class="text-xs font-extrabold text-[#f97316]">
              {{ formatCLP(localMin) }} — {{ formatCLP(localMax) }}
            </div>
          </div>

          <!-- Slider Track Container -->
          <div class="relative w-full h-8 flex items-center select-none pt-1">
            <!-- Barra de fondo inactiva -->
            <div class="w-full h-1.5 bg-slate-200 rounded-full"></div>

            <!-- Barra de rango activo (Naranja estilo SoloTodo) -->
            <div
              class="absolute h-1.5 bg-[#f97316] rounded-full pointer-events-none transition-all duration-75"
              :style="{
                left: minPercent + '%',
                width: Math.max(0, maxPercent - minPercent) + '%',
              }"
            ></div>

            <!-- Input Min Slider -->
            <input
              type="range"
              class="range-slider-input"
              :min="catalogMin"
              :max="catalogMax"
              :step="step"
              :value="localMin"
              @input="handleMinInput"
            />

            <!-- Input Max Slider -->
            <input
              type="range"
              class="range-slider-input"
              :min="catalogMin"
              :max="catalogMax"
              :step="step"
              :value="localMax"
              @input="handleMaxInput"
            />
          </div>

          <!-- Campos numéricos Desde / Hasta para precisión -->
          <div class="grid grid-cols-2 gap-3 pt-1">
            <div>
              <span class="text-[10px] text-slate-500 font-semibold block mb-1">Mínimo:</span>
              <div class="relative flex items-center">
                <span class="absolute left-2.5 text-slate-400 font-bold">$</span>
                <input
                  type="number"
                  v-model.number="localMin"
                  :min="catalogMin"
                  :max="localMax - step"
                  :step="step"
                  class="w-full pl-6 pr-2 py-1.5 rounded-lg border border-brand-border bg-brand-surface-subtle text-xs font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-accent"
                />
              </div>
            </div>
            <div>
              <span class="text-[10px] text-slate-500 font-semibold block mb-1">Máximo:</span>
              <div class="relative flex items-center">
                <span class="absolute left-2.5 text-slate-400 font-bold">$</span>
                <input
                  type="number"
                  v-model.number="localMax"
                  :min="localMin + step"
                  :max="catalogMax"
                  :step="step"
                  class="w-full pl-6 pr-2 py-1.5 rounded-lg border border-brand-border bg-brand-surface-subtle text-xs font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-accent"
                />
              </div>
            </div>
          </div>

          <!-- Chips de acceso rápido de precio -->
          <div class="flex flex-wrap gap-1.5 pt-1">
            <button
              type="button"
              @click="setQuickRange(catalogMin, 100000)"
              class="px-2 py-1 rounded-md text-[10px] font-semibold bg-brand-surface-subtle hover:bg-brand-primary-subtle text-slate-600 border border-brand-border cursor-pointer transition-colors"
            >
              Hasta $100.000
            </button>
            <button
              type="button"
              @click="setQuickRange(100000, 500000)"
              class="px-2 py-1 rounded-md text-[10px] font-semibold bg-brand-surface-subtle hover:bg-brand-primary-subtle text-slate-600 border border-brand-border cursor-pointer transition-colors"
            >
              $100k a $500k
            </button>
            <button
              type="button"
              @click="setQuickRange(500000, 1000000)"
              class="px-2 py-1 rounded-md text-[10px] font-semibold bg-brand-surface-subtle hover:bg-brand-primary-subtle text-slate-600 border border-brand-border cursor-pointer transition-colors"
            >
              $500k a $1M
            </button>
            <button
              type="button"
              @click="setQuickRange(1000000, catalogMax)"
              class="px-2 py-1 rounded-md text-[10px] font-semibold bg-brand-surface-subtle hover:bg-brand-primary-subtle text-slate-600 border border-brand-border cursor-pointer transition-colors"
            >
              Más de $1M
            </button>
          </div>
        </div>

        <hr class="border-brand-border" />

        <!-- 2. SECCIÓN PALABRAS CLAVE (Estilo SoloTodo) -->
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-slate-900 uppercase tracking-wider block">
            Palabras clave
          </label>
          <div class="relative">
            <Search class="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              v-model="localSearch"
              placeholder="Buscar por marca, modelo o palabra clave..."
              class="w-full pl-8 pr-3 py-2 rounded-lg border border-brand-border bg-brand-surface-subtle text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-accent"
            />
          </div>
        </div>

        <!-- 3. SECCIÓN CATEGORÍAS -->
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-slate-900 uppercase tracking-wider block">
            Categoría
          </label>
          <div class="relative">
            <select
              v-model="localCategory"
              class="w-full appearance-none px-3 py-2 rounded-lg border border-brand-border bg-brand-surface-subtle text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-accent cursor-pointer"
            >
              <option :value="null">Todas las Categorías</option>
              <option
                v-for="cat in productStore.categories"
                :key="cat.id"
                :value="cat.slug"
              >
                {{ cat.name }}
              </option>
            </select>
            <ChevronDown class="w-3.5 h-3.5 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        <!-- 4. SECCIÓN ENVÍO GRATIS -->
        <div class="pt-1">
          <label class="flex items-center gap-2.5 p-2.5 rounded-xl bg-brand-surface-subtle border border-brand-border cursor-pointer hover:border-brand-primary-border transition-colors">
            <input
              type="checkbox"
              v-model="localFreeShipping"
              class="rounded border-slate-300 text-brand-accent focus:ring-brand-accent w-4 h-4 cursor-pointer"
            />
            <div class="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
              <Truck class="w-3.5 h-3.5 text-emerald-600" />
              <span>Solo productos con Envío Gratis</span>
            </div>
          </label>
        </div>
      </div>

      <!-- Action Buttons Footer -->
      <div class="p-6 bg-brand-surface-subtle border-t border-brand-border space-y-2">
        <button
          type="button"
          @click="applyAndClose"
          class="w-full bg-[#f97316] hover:bg-[#ea580c] text-white font-extrabold py-3 rounded-xl text-xs uppercase tracking-wider transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer"
        >
          <Check class="w-4 h-4" />
          <span>Ver Precios / Aplicar Filtros</span>
        </button>

        <button
          type="button"
          @click="clearAllAndClose"
          class="w-full py-2 text-slate-500 hover:text-slate-800 text-xs font-semibold text-center transition-colors cursor-pointer"
        >
          Limpiar y Ver Todo
        </button>
      </div>
    </div>
  </div>
</template>
