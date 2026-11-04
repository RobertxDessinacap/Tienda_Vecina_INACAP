<script setup>
import { ref } from 'vue'
import {
  MapPin,
  X,
  Check,
  Navigation,
  Home,
  Building2,
  CheckCircle2,
  Search,
} from 'lucide-vue-next'
import { useLocationStore } from '../stores/location'
import { blockDangerousCharsOnKeypress, sanitizeEventInput, sanitizeInput } from '../utils/security'

const locationStore = useLocationStore()

const customCity = ref('')
const customStreet = ref('')
const showCustomForm = ref(false)

function handleSelect(fullLocation) {
  locationStore.setLocation(fullLocation)
}

function handleSaveCustom() {
  if (!customCity.value.trim()) return
  const formatted = customStreet.value.trim()
    ? `${customStreet.value.trim()}, ${customCity.value.trim()}`
    : customCity.value.trim()
  locationStore.setLocation(formatted, customStreet.value.trim())
  customCity.value = ''
  customStreet.value = ''
  showCustomForm.value = false
}
</script>

<template>
  <div
    v-if="locationStore.isModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto"
  >
    <div
      class="bg-brand-surface rounded-2xl shadow-xl max-w-lg w-full overflow-hidden border border-brand-border relative animate-in fade-in zoom-in-95 duration-200 my-auto text-xs flex flex-col max-h-[90vh]"
    >
      <!-- Modal Header -->
      <div class="bg-brand-primary px-6 py-4 flex items-center justify-between border-b border-brand-primary-border shrink-0">
        <div class="flex items-center gap-2">
          <MapPin class="w-5 h-5 text-brand-primary-text" />
          <h2 class="text-base font-bold text-slate-900">
            Elige dónde recibir tus compras
          </h2>
        </div>
        <button
          @click="locationStore.closeLocationModal()"
          class="w-7 h-7 rounded-full bg-brand-surface/80 hover:bg-brand-surface flex items-center justify-center text-slate-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Modal Content -->
      <div class="p-6 overflow-y-auto space-y-4">
        <!-- Current Delivery Location Banner -->
        <div class="bg-brand-primary-subtle border border-brand-primary-border p-3.5 rounded-xl flex items-center justify-between shadow-2xs">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-full bg-brand-accent text-white flex items-center justify-center shrink-0">
              <Home class="w-4 h-4" />
            </div>
            <div>
              <span class="text-[10px] text-brand-primary-text font-bold block uppercase tracking-wider">
                Dirección de entrega actual
              </span>
              <strong class="text-slate-900 text-sm block">
                {{ locationStore.currentLocation }}
              </strong>
            </div>
          </div>
          <span class="bg-brand-primary text-brand-primary-text text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
            <CheckCircle2 class="w-3 h-3 text-brand-accent" />
            Activa
          </span>
        </div>

        <!-- Quick GPS Button -->
        <button
          @click="locationStore.useCurrentGeoLocation()"
          class="w-full flex items-center justify-center gap-2 p-2.5 rounded-lg border border-brand-border hover:border-brand-primary-border hover:bg-brand-primary-subtle text-brand-accent font-bold transition-all text-xs"
        >
          <Navigation class="w-4 h-4" />
          <span>Usar mi ubicación actual</span>
        </button>

        <!-- Chilean Popular Delivery Cities -->
        <div>
          <span class="text-[11px] font-bold text-slate-600 uppercase tracking-wider block mb-2">
            Principales Ciudades y Comunas de Despacho en Chile:
          </span>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="loc in locationStore.savedLocations"
              :key="loc.id"
              @click="handleSelect(loc.full)"
              :class="[
                locationStore.currentLocation === loc.full
                  ? 'bg-brand-primary-subtle border-brand-accent text-brand-accent font-bold shadow-2xs'
                  : 'bg-brand-surface-subtle border-brand-border text-slate-800 hover:bg-brand-primary-subtle hover:border-brand-primary-border'
              ]"
              class="p-2.5 rounded-xl border text-left transition-all flex items-center justify-between group"
            >
              <div>
                <span class="font-bold block text-xs group-hover:text-black">{{ loc.city }}</span>
                <span class="text-[10px] text-slate-500 block">{{ loc.region }}</span>
              </div>
              <Check v-if="locationStore.currentLocation === loc.full" class="w-4 h-4 text-brand-accent" />
            </button>
          </div>
        </div>

        <!-- Custom Address Section -->
        <div class="pt-2 border-t border-brand-border">
          <button
            v-if="!showCustomForm"
            @click="showCustomForm = true"
            class="text-xs text-brand-accent hover:underline font-bold flex items-center gap-1"
          >
            <Building2 class="w-4 h-4" />
            <span>+ Ingresar otra calle, comuna o región</span>
          </button>

          <form v-else @submit.prevent="handleSaveCustom" class="space-y-2.5 bg-brand-surface-subtle p-3.5 rounded-xl border border-brand-border">
            <span class="font-bold text-slate-900 block text-xs">Ingresar dirección personalizada:</span>
            
            <div>
              <label class="block text-[11px] font-semibold text-slate-700 mb-0.5">Comuna o Ciudad *</label>
              <input
                v-model="customCity"
                type="text"
                @keypress="blockDangerousCharsOnKeypress"
                @input="e => sanitizeEventInput(e, v => customCity = v)"
                placeholder="Ej: Ñuñoa, Santiago o La Serena"
                required
                class="w-full p-2 bg-brand-surface rounded-lg border border-brand-border focus:outline-none focus:ring-1 focus:ring-brand-accent text-xs"
              />
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-slate-700 mb-0.5">Calle y Número (Opcional)</label>
              <input
                v-model="customStreet"
                type="text"
                @keypress="blockDangerousCharsOnKeypress"
                @input="e => sanitizeEventInput(e, v => customStreet = v)"
                placeholder="Ej: Av. Apoquindo 4800, depto 402"
                class="w-full p-2 bg-brand-surface rounded-lg border border-brand-border focus:outline-none focus:ring-1 focus:ring-brand-accent text-xs"
              />
            </div>

            <div class="flex gap-2 pt-1">
              <button
                type="submit"
                class="bg-brand-accent hover:bg-brand-accent-hover text-white font-bold py-1.5 px-4 rounded-lg text-xs transition-colors shadow-2xs"
              >
                Guardar Dirección
              </button>
              <button
                type="button"
                @click="showCustomForm = false"
                class="text-slate-500 hover:text-slate-700 text-xs py-1.5 px-3"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="p-4 bg-brand-surface-subtle border-t border-brand-border flex items-center justify-between shrink-0">
        <span class="text-[11px] text-slate-500">
          Los tiempos y costos de despacho express se actualizarán para esta zona.
        </span>
        <button
          @click="locationStore.closeLocationModal()"
          class="bg-brand-primary-subtle hover:bg-brand-primary text-brand-primary-text font-bold py-1.5 px-4 rounded-lg text-xs transition-colors"
        >
          Cerrar
        </button>
      </div>
    </div>
  </div>
</template>
