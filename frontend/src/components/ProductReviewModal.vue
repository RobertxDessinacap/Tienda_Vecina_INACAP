<script setup>
import { ref, watch } from 'vue'
import { useProductStore } from '../stores/products'
import { useAuthStore } from '../stores/auth'
import { blockDangerousCharsOnKeypress, sanitizeEventInput, sanitizeInput } from '../utils/security'
import {
  X,
  Star,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
} from 'lucide-vue-next'

const productStore = useProductStore()
const authStore = useAuthStore()

const rating = ref(5)
const hoverRating = ref(0)
const comment = ref('')
const localError = ref(null)
const successMsg = ref(null)
const isSubmitting = ref(false)

watch(
  () => productStore.reviewModalOpen,
  (open) => {
    if (open) {
      rating.value = 5
      hoverRating.value = 0
      comment.value = ''
      localError.value = null
      successMsg.value = null
    }
  }
)

function onCommentInput(e) {
  sanitizeEventInput(e, (cleaned) => {
    comment.value = cleaned
  })
}

async function handleSubmit() {
  if (!authStore.isAuthenticated) {
    authStore.openAuthModal('login')
    return
  }

  localError.value = null
  successMsg.value = null

  if (rating.value < 1 || rating.value > 5) {
    localError.value = 'Selecciona una calificación entre 1 y 5 estrellas.'
    return
  }

  isSubmitting.value = true
  const res = await productStore.submitReview(productStore.reviewingProduct.slug, {
    rating: rating.value,
    comment: sanitizeInput(comment.value),
  })
  isSubmitting.value = false

  if (res.success) {
    successMsg.value = '¡Gracias por tu opinión! Tu valoración ha sido registrada.'
    setTimeout(() => {
      productStore.closeReviewModal()
    }, 1200)
  } else {
    localError.value = res.error || 'No se pudo enviar tu opinión.'
  }
}
</script>

<template>
  <div
    v-if="productStore.reviewModalOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200"
  >
    <div class="bg-brand-surface rounded-2xl max-w-md w-full shadow-2xl border border-brand-border overflow-hidden">
      <!-- Modal Header -->
      <div class="p-5 border-b border-brand-border flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-amber-50 text-amber-500 flex items-center justify-center">
            <Star class="w-4 h-4 fill-amber-400" />
          </div>
          <div>
            <h3 class="font-bold text-base text-slate-900 leading-tight">Evaluar Producto</h3>
            <p class="text-[11px] text-slate-500">Comparte tu experiencia de compra con la comunidad</p>
          </div>
        </div>
        <button
          @click="productStore.closeReviewModal()"
          class="text-slate-400 hover:text-slate-600 p-1 rounded-lg transition-colors cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Form Body -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
        <!-- Product info card -->
        <div
          v-if="productStore.reviewingProduct"
          class="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-brand-border"
        >
          <img
            :src="productStore.reviewingProduct.display_image_url || productStore.reviewingProduct.image_url"
            :alt="productStore.reviewingProduct.title"
            class="w-12 h-12 rounded-lg object-cover bg-white shrink-0 border border-brand-border"
          />
          <div class="min-w-0">
            <h4 class="text-xs font-bold text-slate-900 truncate">
              {{ productStore.reviewingProduct.title }}
            </h4>
            <p class="text-[11px] text-slate-500">
              Vendido por {{ productStore.reviewingProduct.seller_nombre || productStore.reviewingProduct.seller_alias }}
            </p>
          </div>
        </div>

        <!-- Success Banner -->
        <div
          v-if="successMsg"
          class="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2"
        >
          <CheckCircle2 class="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{{ successMsg }}</span>
        </div>

        <!-- Error Banner -->
        <div
          v-if="localError"
          class="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2"
        >
          <AlertCircle class="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
          <span>{{ localError }}</span>
        </div>

        <!-- Star Rating Picker -->
        <div class="space-y-2 text-center py-2">
          <label class="block text-xs font-bold text-slate-700">
            ¿Cómo calificarías este producto?
          </label>
          <div class="flex items-center justify-center gap-2">
            <button
              v-for="star in 5"
              :key="star"
              type="button"
              @click="rating = star"
              @mouseenter="hoverRating = star"
              @mouseleave="hoverRating = 0"
              class="p-1 transition-transform hover:scale-125 focus:outline-none cursor-pointer"
            >
              <Star
                :class="[
                  (hoverRating || rating) >= star
                    ? 'fill-amber-400 text-amber-400'
                    : 'text-slate-300',
                  'w-8 h-8 transition-colors'
                ]"
              />
            </button>
          </div>
          <span class="text-xs font-bold text-slate-700 block">
            {{ ['Pésimo', 'Regular', 'Bueno', 'Muy bueno', 'Excelente'][ (hoverRating || rating) - 1 ] }}
          </span>
        </div>

        <!-- Optional Comment -->
        <div class="space-y-1">
          <label class="block text-xs font-bold text-slate-700 flex items-center gap-1.5">
            <MessageSquare class="w-3.5 h-3.5 text-slate-400" />
            <span>Opinión o Comentario (Opcional)</span>
          </label>
          <textarea
            v-model="comment"
            @keypress="blockDangerousCharsOnKeypress"
            @input="onCommentInput"
            rows="3"
            placeholder="Cuéntale a otros compradores qué tal te pareció la calidad del producto, el despacho o la atención..."
            class="w-full bg-slate-50 border border-brand-border focus:border-brand-accent focus:bg-white rounded-lg p-3 text-xs text-slate-800 focus:outline-none leading-relaxed"
          ></textarea>
        </div>

        <!-- Buttons -->
        <div class="pt-2 flex items-center justify-end gap-2">
          <button
            type="button"
            @click="productStore.closeReviewModal()"
            class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 transition-colors cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="isSubmitting"
            class="bg-brand-accent hover:bg-brand-accent-hover text-white font-bold text-xs py-2.5 px-5 rounded-xl transition-all shadow-md disabled:opacity-50 cursor-pointer"
          >
            {{ isSubmitting ? 'Enviando...' : 'Publicar Calificación' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
