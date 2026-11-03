<script setup>
import { ShieldCheck, Truck, CreditCard, Sparkles } from 'lucide-vue-next'
</script>

<template>
  <div class="relative overflow-hidden bg-gradient-to-r from-blue-700 via-indigo-800 to-purple-800 text-white rounded-lg shadow-sm my-4">
    <div class="max-w-7xl mx-auto px-6 py-6 md:py-8 flex flex-col md:flex-row items-center justify-between gap-6">
      <div class="space-y-2 text-center md:text-left">
        <div class="inline-flex items-center gap-1.5 bg-yellow-400 text-gray-950 font-black text-xs px-2.5 py-0.5 rounded-full uppercase tracking-wider">
          <Sparkles class="w-3.5 h-3.5 text-gray-950" />
          <span>Especial Inacap Tech</span>
        </div>
        <h1 class="text-2xl md:text-4xl font-extrabold tracking-tight">
          HASTA 40% OFF Y 12 CUOTAS SIN INTERÉS
        </h1>
        <p class="text-blue-100 text-sm max-w-xl">
          Explora la mejor tecnología, smartphones y computación con envíos gratis garantizados y la máxima seguridad bajo estándar ISO 27001.
        </p>
      </div>

      <!-- Quick Perks Badges -->
      <div class="grid grid-cols-2 gap-3 w-full md:w-auto text-xs">
        <div class="bg-white/10 backdrop-blur-xs border border-white/20 p-3 rounded-lg flex items-center gap-2.5">
          <Truck class="w-5 h-5 text-emerald-300 shrink-0" />
          <div>
            <span class="font-bold block text-white">Envío Gratis</span>
            <span class="text-[11px] text-blue-200 block">En miles de productos</span>
          </div>
        </div>
        <div class="bg-white/10 backdrop-blur-xs border border-white/20 p-3 rounded-lg flex items-center gap-2.5">
          <CreditCard class="w-5 h-5 text-yellow-300 shrink-0" />
          <div>
            <span class="font-bold block text-white">6 a 12 Cuotas</span>
            <span class="text-[11px] text-blue-200 block">Sin interés con tu banco</span>
          </div>
        </div>
        <div class="col-span-2 bg-white/10 backdrop-blur-xs border border-white/20 p-2.5 rounded-lg flex items-center justify-center gap-2 text-center">
          <ShieldCheck class="w-4 h-4 text-emerald-300" />
          <span class="text-xs font-semibold text-emerald-200">
            Compra Protegida & Identidad Seudónima (ISO 27001)
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
