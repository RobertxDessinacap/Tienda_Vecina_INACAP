<script setup>
import { ShieldCheck, Lock, EyeOff, UserCheck, Database } from 'lucide-vue-next'
</script>

<template>
  <section class="max-w-7xl mx-auto px-4 my-8">
    <div class="bg-white rounded-lg border border-gray-200/90 shadow-xs p-6">
      <div class="flex items-center gap-2 mb-4 pb-3 border-b border-gray-100">
        <ShieldCheck class="w-6 h-6 text-emerald-600" />
        <div>
          <h2 class="text-sm font-bold text-gray-900">
            Arquitectura de Seguridad & Estándar ISO/IEC 27001
          </h2>
          <p class="text-[11px] text-gray-500">
            Garantías de confidencialidad, integridad y disponibilidad aplicadas en Inacap E-Commerce
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
        <!-- Pillar 1 -->
        <div class="flex items-start gap-2.5 p-3 rounded-md bg-gray-50/60 border border-gray-100">
          <EyeOff class="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <div>
            <strong class="text-gray-900 block font-bold">Cuenta Intermedia Seudónima</strong>
            <p class="text-gray-600 text-[11px] mt-0.5 leading-relaxed">
              Disociación de credenciales reales. Las ventas y compras se operan bajo un Proxy no enumerable, blindando la identidad del usuario.
            </p>
          </div>
        </div>

        <!-- Pillar 2 -->
        <div class="flex items-start gap-2.5 p-3 rounded-md bg-gray-50/60 border border-gray-100">
          <UserCheck class="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
          <div>
            <strong class="text-gray-900 block font-bold">Rolificación Estricta (RBAC)</strong>
            <p class="text-gray-600 text-[11px] mt-0.5 leading-relaxed">
              Control de acceso granular (Comprador, Vendedor y Admin). Solo cuentas verificadas pueden publicar productos en el catálogo.
            </p>
          </div>
        </div>

        <!-- Pillar 3 -->
        <div class="flex items-start gap-2.5 p-3 rounded-md bg-gray-50/60 border border-gray-100">
          <Lock class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <strong class="text-gray-900 block font-bold">Criptografía y Tokens JWT</strong>
            <p class="text-gray-600 text-[11px] mt-0.5 leading-relaxed">
              Contraseñas cifradas con algoritmos seguros y tokens firmados con caducidad garantizada contra manipulaciones.
            </p>
          </div>
        </div>

        <!-- Pillar 4 -->
        <div class="flex items-start gap-2.5 p-3 rounded-md bg-gray-50/60 border border-gray-100">
          <Database class="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
          <div>
            <strong class="text-gray-900 block font-bold">PostgreSQL ORM & Secretos</strong>
            <p class="text-gray-600 text-[11px] mt-0.5 leading-relaxed">
              Consultas parametrizadas contra inyecciones SQL y configuración 100% blindada en variables de entorno (.env).
            </p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
