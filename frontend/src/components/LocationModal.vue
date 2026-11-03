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
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-2xs overflow-y-auto"
  >
    <div
      class="bg-white rounded-lg shadow-2xl max-w-lg w-full overflow-hidden border border-gray-200 relative animate-in fade-in zoom-in-95 duration-200 my-auto text-xs flex flex-col max-h-[90vh]"
    >
      <!-- Modal Header -->
      <div class="bg-[#FFE600] px-6 py-4 flex items-center justify-between border-b border-yellow-400 shrink-0">
        <div class="flex items-center gap-2">
          <MapPin class="w-5 h-5 text-gray-900" />
          <h2 class="text-base font-bold text-gray-900">
            Elige dónde recibir tus compras
          </h2>
        </div>
        <button
          @click="locationStore.closeLocationModal()"
          class="w-7 h-7 rounded-full bg-white/80 hover:bg-white flex items-center justify-center text-gray-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Modal Content -->
      <div class="p-6 overflow-y-auto space-y-4">
        <!-- Current Delivery Location Banner -->
        <div class="bg-blue-50 border border-blue-200 p-3 rounded-lg flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0">
              <Home class="w-4 h-4" />
            </div>
            <div>
              <span class="text-[10px] text-blue-700 font-bold block uppercase tracking-wider">
                Dirección de entrega actual
              </span>
              <strong class="text-gray-900 text-sm block">
                {{ locationStore.currentLocation }}
              </strong>
            </div>
          </div>
          <span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
            <CheckCircle2 class="w-3 h-3 text-emerald-600" />
            Activa
          </span>
        </div>

        <!-- Quick GPS Button -->
        <button
          @click="locationStore.useCurrentGeoLocation()"
          class="w-full flex items-center justify-center gap-2 p-2.5 rounded-md border border-gray-300 hover:border-blue-500 hover:bg-blue-50/50 text-blue-600 font-bold transition-all text-xs"
        >
          <Navigation class="w-4 h-4" />
          <span>Usar mi ubicación actual</span>
        </button>

        <!-- Chilean Popular Delivery Cities -->
        <div>
          <span class="text-[11px] font-bold text-gray-600 uppercase tracking-wider block mb-2">
            Principales Ciudades y Comunas de Despacho en Chile:
          </span>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="loc in locationStore.savedLocations"
              :key="loc.id"
              @click="handleSelect(loc.full)"
              :class="[
                locationStore.currentLocation === loc.full
                  ? 'bg-blue-50 border-[#3483FA] text-[#3483FA] font-bold shadow-2xs'
                  : 'bg-gray-50 border-gray-200 text-gray-800 hover:bg-gray-100 hover:border-gray-300'
              ]"
              class="p-2.5 rounded-md border text-left transition-all flex items-center justify-between group"
            >
              <div>
                <span class="font-bold block text-xs group-hover:text-black">{{ loc.city }}</span>
                <span class="text-[10px] text-gray-500 block">{{ loc.region }}</span>
              </div>
              <Check v-if="locationStore.currentLocation === loc.full" class="w-4 h-4 text-[#3483FA]" />
            </button>
          </div>
        </div>

        <!-- Custom Address Section -->
        <div class="pt-2 border-t border-gray-200">
          <button
            v-if="!showCustomForm"
            @click="showCustomForm = true"
            class="text-xs text-[#3483FA] hover:underline font-bold flex items-center gap-1"
          >
            <Building2 class="w-4 h-4" />
            <span>+ Ingresar otra calle, comuna o región</span>
          </button>

          <form v-else @submit.prevent="handleSaveCustom" class="space-y-2.5 bg-gray-50 p-3 rounded-lg border border-gray-200">
            <span class="font-bold text-gray-900 block text-xs">Ingresar dirección personalizada:</span>
            
            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-0.5">Comuna o Ciudad *</label>
              <input
                v-model="customCity"
                type="text"
                @keypress="blockDangerousCharsOnKeypress"
                @input="e => sanitizeEventInput(e, v => customCity = v)"
                placeholder="Ej: Ñuñoa, Santiago o La Serena"
                required
                class="w-full p-2 bg-white rounded border border-gray-300 focus:outline-none focus:ring-1 focus:ring-[#3483FA] text-xs"
              />
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-0.5">Calle y Número (Opcional)</label>
              <input
                v-model="customStreet"
                type="text"
                @keypress="blockDangerousCharsOnKeypress"
                @input="e => sanitizeEventInput(e, v => customStreet = v)"
                placeholder="Ej: Av. Apoquindo 4800, depto 402"
                class="w-full p-2 bg-white rounded border border-gray-300 focus:outline-none focus:ring-1 focus:ring-[#3483FA] text-xs"
              />
            </div>

            <div class="flex gap-2 pt-1">
              <button
                type="submit"
                class="bg-[#3483FA] hover:bg-[#2968C8] text-white font-bold py-1.5 px-4 rounded text-xs transition-colors"
              >
                Guardar Dirección
              </button>
              <button
                type="button"
                @click="showCustomForm = false"
                class="text-gray-500 hover:text-gray-700 text-xs py-1.5 px-3"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="p-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between shrink-0">
        <span class="text-[11px] text-gray-500">
          Los tiempos y costos de despacho express se actualizarán para esta zona.
        </span>
        <button
          @click="locationStore.closeLocationModal()"
          class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-1.5 px-4 rounded text-xs transition-colors"
        >
          Cerrar
        </button>
      </div>
    </div>
  </div>
</template>
