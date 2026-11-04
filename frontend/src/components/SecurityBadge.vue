<script setup>
import { ShieldCheck, Lock, UserCheck, Truck } from 'lucide-vue-next'
</script>

<template>
  <section class="max-w-7xl mx-auto px-4 my-8">
    <div class="bg-brand-surface rounded-xl border border-brand-border shadow-2xs p-6">
      <div class="flex items-center gap-2 mb-4 pb-3 border-b border-brand-border">
        <ShieldCheck class="w-6 h-6 text-brand-accent" />
        <div>
          <h2 class="text-sm font-bold text-slate-900">
            Garantías de Compra Segura y Confianza
          </h2>
          <p class="text-[11px] text-slate-500">
            Tus compras protegidas de extremo a extremo con los más altos estándares de calidad
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
        <!-- Pillar 1 -->
        <div class="flex items-start gap-2.5 p-3 rounded-xl bg-brand-surface-subtle border border-brand-border">
          <Lock class="w-4 h-4 text-brand-accent shrink-0 mt-0.5" />
          <div>
            <strong class="text-slate-900 block font-bold">Privacidad y Protección</strong>
            <p class="text-slate-600 text-[11px] mt-0.5 leading-relaxed">
              Tus datos personales y de contacto se mantienen siempre confidenciales y resguardados en cada operación.
            </p>
          </div>
        </div>

        <!-- Pillar 2 -->
        <div class="flex items-start gap-2.5 p-3 rounded-xl bg-brand-surface-subtle border border-brand-border">
          <UserCheck class="w-4 h-4 text-brand-accent shrink-0 mt-0.5" />
          <div>
            <strong class="text-slate-900 block font-bold">Vendedores Verificados</strong>
            <p class="text-slate-600 text-[11px] mt-0.5 leading-relaxed">
              Publicaciones autorizadas con reputación transparente y seguimiento de entregas a tiempo.
            </p>
          </div>
        </div>

        <!-- Pillar 3 -->
        <div class="flex items-start gap-2.5 p-3 rounded-xl bg-brand-surface-subtle border border-brand-border">
          <ShieldCheck class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <strong class="text-slate-900 block font-bold">Pagos 100% Seguros</strong>
            <p class="text-slate-600 text-[11px] mt-0.5 leading-relaxed">
              Procesamiento oficial con Webpay Plus de Transbank y respaldo inmediato con comprobante de pago.
            </p>
          </div>
        </div>

        <!-- Pillar 4 -->
        <div class="flex items-start gap-2.5 p-3 rounded-xl bg-brand-surface-subtle border border-brand-border">
          <Truck class="w-4 h-4 text-brand-accent shrink-0 mt-0.5" />
          <div>
            <strong class="text-slate-900 block font-bold">Garantía de Entrega</strong>
            <p class="text-slate-600 text-[11px] mt-0.5 leading-relaxed">
              Despacho rápido a todo Chile y derecho a devolución gratuita de 30 días si no estás satisfecho.
            </p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
