<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useProductStore } from '../stores/products'
import { useCartStore } from '../stores/cart'
import {
  Search,
  ShoppingCart,
  MapPin,
  User,
  PlusCircle,
  ShieldCheck,
  LogOut,
  ChevronDown,
  Store,
  CheckCircle2,
} from 'lucide-vue-next'

const authStore = useAuthStore()
const productStore = useProductStore()
const cartStore = useCartStore()

const localSearch = ref('')

function handleSearch() {
  productStore.setSearch(localSearch.value)
}

function handleSellClick() {
  if (!authStore.isAuthenticated) {
    authStore.openAuthModal('register')
  } else if (authStore.isSeller) {
    productStore.openCreateModal()
  } else {
    alert('Tu cuenta actual tiene rol de "Comprador". Para publicar productos, debes registrarte o iniciar sesión con una cuenta de "Vendedor".')
  }
}
</script>

<template>
  <header class="bg-[#FFE600] border-b border-[#E6D000] sticky top-0 z-40 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 py-2.5">
      <!-- Top Row: Logo, Search Bar, Header Banner/Actions -->
      <div class="flex items-center justify-between gap-4">
        <!-- Logo -->
        <div class="flex items-center gap-2 cursor-pointer select-none" @click="productStore.goToCatalog()">
          <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-xs border border-yellow-300">
            <span class="text-xl font-black text-[#2D3277] tracking-tighter">IN</span>
          </div>
          <div class="leading-tight">
            <span class="text-xl font-extrabold text-[#2D3277] tracking-tight block">inacap</span>
            <span class="text-[10px] font-bold text-gray-700 uppercase tracking-widest block -mt-1">e-commerce</span>
          </div>
        </div>

        <!-- Search Bar -->
        <form @submit.prevent="handleSearch" class="flex-1 max-w-2xl relative">
          <div class="relative flex items-center shadow-xs">
            <input
              v-model="localSearch"
              type="text"
              placeholder="Buscar productos, marcas, computación y más..."
              class="w-full bg-white text-gray-800 text-sm pl-4 pr-12 py-2.5 rounded-sm border border-transparent focus:outline-none focus:ring-2 focus:ring-[#3483FA] placeholder-gray-400"
            />
            <button
              type="submit"
              class="absolute right-0 top-0 bottom-0 px-3.5 bg-white hover:bg-gray-50 border-l border-gray-200 text-gray-500 hover:text-gray-700 rounded-r-sm transition-colors flex items-center justify-center"
              title="Buscar"
            >
              <Search class="w-4 h-4" />
            </button>
          </div>
        </form>

        <!-- Right Side: Security Trust Badge -->
        <div class="hidden lg:flex items-center gap-2 text-xs bg-yellow-300/60 px-3 py-1.5 rounded-full text-gray-800 border border-yellow-400/50">
          <ShieldCheck class="w-4 h-4 text-emerald-700" />
          <span class="font-semibold">ISO/IEC 27001 Certified Security</span>
        </div>
      </div>

      <!-- Bottom Sub-Row: Location, Navigation Categories, User & Sell Actions -->
      <div class="flex items-center justify-between mt-2 pt-1 text-xs text-gray-800">
        <!-- Location Picker -->
        <div class="hidden sm:flex items-center gap-1.5 cursor-pointer hover:opacity-80 transition-opacity">
          <MapPin class="w-4 h-4 text-gray-700" />
          <div>
            <span class="text-[10px] text-gray-600 block leading-none">Enviar a</span>
            <span class="font-medium text-gray-900 leading-none">Santiago, Chile</span>
          </div>
        </div>

        <!-- Category Links -->
        <nav class="flex items-center gap-4 text-gray-700 font-normal overflow-x-auto py-1">
          <button
            @click="productStore.setCategory(null)"
            :class="[!productStore.activeCategory ? 'font-bold text-gray-900' : 'hover:text-black']"
            class="transition-colors whitespace-nowrap"
          >
            Todos los Productos
          </button>
          <button
            v-for="cat in productStore.categories"
            :key="cat.id"
            @click="productStore.setCategory(cat.slug)"
            :class="[productStore.activeCategory === cat.slug ? 'font-bold text-gray-900 border-b-2 border-gray-800' : 'hover:text-black']"
            class="transition-colors whitespace-nowrap pb-0.5"
          >
            {{ cat.name }}
          </button>
        </nav>

        <!-- User / Actions -->
        <div class="flex items-center gap-3">
          <!-- Vender / Publicar Button (MercadoLibre style) -->
          <button
            @click="handleSellClick"
            class="flex items-center gap-1 font-semibold text-gray-900 hover:text-black bg-yellow-300/90 hover:bg-yellow-400 px-3 py-1 rounded-sm transition-all shadow-2xs border border-yellow-500/30"
          >
            <PlusCircle class="w-3.5 h-3.5 text-blue-800" />
            <span>Vender</span>
          </button>

          <!-- User State -->
          <template v-if="authStore.isAuthenticated">
            <div class="flex items-center gap-2 bg-white/70 px-2.5 py-1 rounded-sm border border-yellow-400/60">
              <div class="w-5 h-5 rounded-full bg-[#3483FA] text-white flex items-center justify-center font-bold text-[10px]">
                {{ authStore.intermediateAlias.charAt(0).toUpperCase() }}
              </div>
              <div class="leading-tight text-left">
                <div class="flex items-center gap-1">
                  <span class="font-bold text-gray-900">{{ authStore.intermediateAlias }}</span>
                  <CheckCircle2 v-if="authStore.isSeller" class="w-3 h-3 text-emerald-600" title="Vendedor Verificado" />
                </div>
                <span class="text-[9px] text-gray-600 block uppercase font-medium">
                  Rol: {{ authStore.userRole }}
                </span>
              </div>
              <button
                @click="authStore.logout"
                class="ml-1 text-gray-500 hover:text-red-600 transition-colors"
                title="Cerrar Sesión Segura"
              >
                <LogOut class="w-3.5 h-3.5" />
              </button>
            </div>
          </template>

          <template v-else>
            <div class="flex items-center gap-2">
              <button
                @click="authStore.openAuthModal('register')"
                class="hover:text-black transition-colors"
              >
                Crea tu cuenta
              </button>
              <span class="text-gray-400">|</span>
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
            class="relative p-1 text-gray-800 hover:text-black transition-colors"
            title="Ver Carrito de Compras"
          >
            <ShoppingCart class="w-4 h-4" />
            <span
              v-if="cartStore.totalItemsCount > 0"
              class="absolute -top-1 -right-1 bg-[#3483FA] text-white text-[9px] font-bold rounded-full w-3.5 h-3.5 flex items-center justify-center animate-in zoom-in-50 duration-200"
            >
              {{ cartStore.totalItemsCount }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
