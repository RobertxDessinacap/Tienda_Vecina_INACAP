<script setup>
import { ShieldCheck, Truck, CreditCard, Sparkles } from 'lucide-vue-next'
</script>

<template>
  <div class="relative overflow-hidden bg-gradient-to-r from-brand-primary via-brand-primary-hover to-brand-primary-border text-slate-900 rounded-xl shadow-xs my-4 border border-brand-border">
    <div class="max-w-7xl mx-auto px-6 py-6 md:py-8 flex flex-col md:flex-row items-center justify-between gap-6">
      <div class="space-y-2 text-center md:text-left">
        <div class="inline-flex items-center gap-1.5 bg-brand-surface/90 text-brand-primary-text font-extrabold text-xs px-3 py-1 rounded-full uppercase tracking-wider shadow-2xs border border-brand-primary-border">
          <Sparkles class="w-3.5 h-3.5 text-brand-accent" />
          <span>Especial Inacap Tech</span>
        </div>
        <h1 class="text-2xl md:text-4xl font-black tracking-tight text-slate-950">
          HASTA 40% OFF Y 12 CUOTAS SIN INTERÉS
        </h1>
        <p class="text-slate-700 text-sm max-w-xl font-medium">
          Explora la mejor tecnología, smartphones y computación con envíos gratis garantizados y compra protegida.
        </p>
      </div>

      <!-- Quick Perks Badges -->
      <div class="grid grid-cols-2 gap-3 w-full md:w-auto text-xs">
        <div class="bg-brand-surface/90 backdrop-blur-xs border border-brand-border p-3 rounded-xl flex items-center gap-2.5 shadow-2xs">
          <Truck class="w-5 h-5 text-brand-accent shrink-0" />
          <div>
            <span class="font-bold block text-slate-900">Envío Gratis</span>
            <span class="text-[11px] text-slate-600 block">En miles de productos</span>
          </div>
        </div>
        <div class="bg-brand-surface/90 backdrop-blur-xs border border-brand-border p-3 rounded-xl flex items-center gap-2.5 shadow-2xs">
          <CreditCard class="w-5 h-5 text-brand-accent shrink-0" />
          <div>
            <span class="font-bold block text-slate-900">6 a 12 Cuotas</span>
            <span class="text-[11px] text-slate-600 block">Sin interés con tu banco</span>
          </div>
        </div>
        <div class="col-span-2 bg-brand-surface/90 backdrop-blur-xs border border-brand-border p-2.5 rounded-xl flex items-center justify-center gap-2 text-center shadow-2xs">
          <ShieldCheck class="w-4 h-4 text-emerald-600" />
          <span class="text-xs font-bold text-slate-900">
            Compra Protegida y Certificación de Seguridad
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
