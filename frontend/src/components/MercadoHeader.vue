<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useProductStore } from '../stores/products'
import { useCartStore } from '../stores/cart'
import { useLocationStore } from '../stores/location'
import { blockDangerousCharsOnKeypress, sanitizeInput, sanitizeEventInput } from '../utils/security'
import {
  Search,
  ShoppingCart,
  MapPin,
  User,
  PlusCircle,
  Package,
  ShieldCheck,
  LogOut,
  ChevronDown,
  Store,
  CheckCircle2,
} from 'lucide-vue-next'

const authStore = useAuthStore()
const productStore = useProductStore()
const cartStore = useCartStore()
const locationStore = useLocationStore()

const localSearch = ref('')

function onSearchInput(event) {
  sanitizeEventInput(event, (cleaned) => {
    localSearch.value = cleaned
  })
}

function handleSearch() {
  const safeQuery = sanitizeInput(localSearch.value)
  localSearch.value = safeQuery
  productStore.setSearch(safeQuery)
}

function handleSellClick() {
  if (!authStore.isAuthenticated) {
    authStore.openAuthModal('register')
  } else if (authStore.isSeller) {
    productStore.openCreateModal()
  } else {
    // Abrir modal explicativo con beneficios para convertirse en vendedor
    authStore.openBecomeSellerModal()
  }
}
</script>

<template>
  <header class="bg-brand-primary border-b border-brand-primary-border sticky top-0 z-40 shadow-xs">
    <div class="max-w-7xl mx-auto px-4 py-2.5">
      <!-- Top Row: Logo, Search Bar, Header Banner/Actions -->
      <div class="flex items-center justify-between gap-4">
        <!-- Logo -->
        <div class="flex items-center gap-2 cursor-pointer select-none" @click="productStore.goToCatalog()">
          <div class="w-10 h-10 bg-brand-surface rounded-lg flex items-center justify-center shadow-xs border border-brand-border">
            <span class="text-xl font-black text-brand-accent tracking-tighter">IN</span>
          </div>
          <div class="leading-tight">
            <span class="text-xl font-extrabold text-brand-primary-text tracking-tight block">inacap</span>
            <span class="text-[10px] font-bold text-brand-primary-text/80 uppercase tracking-widest block -mt-1">e-commerce</span>
          </div>
        </div>

        <!-- Search Bar -->
        <form @submit.prevent="handleSearch" class="flex-1 max-w-2xl relative">
          <div class="relative flex items-center shadow-xs">
            <input
              v-model="localSearch"
              type="text"
              @keypress="blockDangerousCharsOnKeypress"
              @input="onSearchInput"
              placeholder="Buscar productos, marcas, computación y más..."
              class="w-full bg-brand-surface text-slate-800 text-sm pl-4 pr-12 py-2.5 rounded-sm border border-transparent focus:outline-none focus:ring-2 focus:ring-brand-accent placeholder-slate-400"
            />
            <button
              type="submit"
              class="absolute right-0 top-0 bottom-0 px-3.5 bg-brand-surface hover:bg-brand-primary-subtle border-l border-brand-border text-brand-primary-text hover:text-slate-900 rounded-r-sm transition-colors flex items-center justify-center"
              title="Buscar"
            >
              <Search class="w-4 h-4" />
            </button>
          </div>
        </form>

        <!-- Right Side: Security Trust Badge -->
        <div class="hidden lg:flex items-center gap-2 text-xs bg-brand-primary-subtle px-3 py-1.5 rounded-full text-brand-primary-text border border-brand-primary-border shadow-2xs">
          <ShieldCheck class="w-4 h-4 text-brand-accent" />
          <span class="font-semibold">Certificación de seguridad</span>
        </div>
      </div>

      <!-- Bottom Sub-Row: Location, Navigation Categories, User & Sell Actions -->
      <div class="flex items-center justify-between mt-2 pt-1 text-xs text-brand-primary-text">
        <!-- Location Picker (Interactive) -->
        <button
          type="button"
          @click="locationStore.openLocationModal()"
          class="flex items-center gap-1.5 cursor-pointer hover:bg-brand-primary-hover/60 px-2 py-1 rounded transition-all border border-transparent hover:border-brand-primary-border text-left"
          title="Cambiar dirección o ciudad de entrega"
        >
          <MapPin class="w-4 h-4 text-brand-primary-text shrink-0" />
          <div class="leading-tight">
            <span class="text-[9px] text-brand-primary-text/80 block">Enviar a</span>
            <span class="font-bold text-slate-900 truncate max-w-[120px] sm:max-w-[150px] block">{{ locationStore.currentLocation }}</span>
          </div>
        </button>

        <!-- Category Links (with themed scrollbar) -->
        <nav class="flex items-center gap-4 text-slate-700 font-normal overflow-x-auto py-1 scrollbar-categories">
          <button
            @click="productStore.setCategory(null)"
            :class="[!productStore.activeCategory ? 'font-bold text-slate-900 border-b-2 border-brand-primary-text' : 'hover:text-black']"
            class="transition-colors whitespace-nowrap pb-0.5 shrink-0"
          >
            Todos los Productos
          </button>
          <button
            v-for="cat in productStore.categories"
            :key="cat.id"
            @click="productStore.setCategory(cat.slug)"
            :class="[productStore.activeCategory === cat.slug ? 'font-bold text-slate-900 border-b-2 border-brand-primary-text' : 'hover:text-black']"
            class="transition-colors whitespace-nowrap pb-0.5 shrink-0"
          >
            {{ cat.name }}
          </button>
        </nav>

        <!-- User / Actions -->
        <div class="flex items-center gap-2">
          <!-- Mis Publicaciones (Vista Única para Vendedores) -->
          <button
            v-if="authStore.isSeller"
            @click="productStore.goToMyProducts()"
            :class="productStore.activeView === 'my_products' ? 'bg-brand-accent text-white font-bold' : 'bg-brand-surface text-brand-primary-text hover:bg-brand-primary-subtle font-semibold'"
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-sm transition-all shadow-2xs border border-brand-primary-border text-xs cursor-pointer"
            title="Ver y administrar mis publicaciones exclusivas"
          >
            <Package class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">Mis Publicaciones</span>
          </button>

          <!-- Vender / Publicar Button -->
          <button
            @click="handleSellClick"
            class="flex items-center gap-1 font-semibold text-brand-primary-text hover:text-slate-900 bg-brand-surface hover:bg-brand-primary-subtle px-3 py-1 rounded-sm transition-all shadow-2xs border border-brand-primary-border cursor-pointer text-xs"
          >
            <PlusCircle class="w-3.5 h-3.5 text-brand-accent" />
            <span>Vender</span>
          </button>

          <!-- User State -->
          <template v-if="authStore.isAuthenticated">
            <div class="flex items-center gap-2 bg-brand-surface px-2.5 py-1 rounded-sm border border-brand-primary-border shadow-2xs">
              <div class="w-5 h-5 rounded-full bg-brand-accent text-white flex items-center justify-center font-bold text-[10px]">
                {{ authStore.intermediateAlias.charAt(0).toUpperCase() }}
              </div>
              <div class="leading-tight text-left">
                <div class="flex items-center gap-1">
                  <span class="font-bold text-slate-900">{{ authStore.intermediateAlias }}</span>
                  <CheckCircle2 v-if="authStore.isSeller" class="w-3 h-3 text-brand-accent" title="Vendedor Verificado" />
                </div>
                <span class="text-[9px] text-slate-500 block uppercase font-medium">
                  Rol: {{ authStore.userRole }}
                </span>
              </div>
              <button
                @click="authStore.logout"
                class="ml-1 text-slate-400 hover:text-red-500 transition-colors"
                title="Cerrar Sesión Segura"
              >
                <LogOut class="w-3.5 h-3.5" />
              </button>
            </div>
          </template>

          <template v-else>
            <div class="flex items-center gap-2 text-slate-800">
              <button
                @click="authStore.openAuthModal('register')"
                class="hover:text-black transition-colors"
              >
                Crea tu cuenta
              </button>
              <span class="text-brand-primary-border">|</span>
              <button
                @click="authStore.openAuthModal('login')"
                class="font-semibold hover:text-black transition-colors"
              >
                Ingresa
              </button>
            </div>
          </template>

          <!-- Cart Button -->
          <button
            @click="cartStore.openCart()"
            class="relative p-1 text-slate-800 hover:text-black transition-colors"
            title="Ver Carrito de Compras"
          >
            <ShoppingCart class="w-4 h-4" />
            <span
              v-if="cartStore.totalItemsCount > 0"
              class="absolute -top-1 -right-1 bg-brand-accent text-white text-[9px] font-bold rounded-full w-3.5 h-3.5 flex items-center justify-center animate-in zoom-in-50 duration-200"
            >
              {{ cartStore.totalItemsCount }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
