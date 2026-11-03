<script setup>
import { ref } from 'vue'
import {
  X,
  FileText,
  ShieldCheck,
  CreditCard,
  HelpCircle,
  Truck,
  RotateCcw,
  CheckCircle2,
  Lock,
} from 'lucide-vue-next'

const isOpen = ref(false)
const currentTab = ref('terms') // 'terms' | 'privacy' | 'payments' | 'help'

function open(tab = 'terms') {
  currentTab.value = tab
  isOpen.value = true
}

function close() {
  isOpen.value = false
}

defineExpose({ open, close })
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-2xs overflow-y-auto"
  >
    <div
      class="bg-white rounded-lg shadow-2xl max-w-3xl w-full overflow-hidden border border-gray-200 relative animate-in fade-in zoom-in-95 duration-200 my-auto text-xs flex flex-col max-h-[85vh]"
    >
      <!-- Modal Header -->
      <div class="bg-[#FFE600] px-6 py-4 flex items-center justify-between border-b border-yellow-400 shrink-0">
        <div class="flex items-center gap-2">
          <ShieldCheck class="w-5 h-5 text-gray-900" />
          <h2 class="text-base font-bold text-gray-900">
            Centro de Información y Ayuda - Inacap E-Commerce
          </h2>
        </div>
        <button
          @click="close"
          class="w-7 h-7 rounded-full bg-white/80 hover:bg-white flex items-center justify-center text-gray-700 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Tab Buttons -->
      <div class="flex border-b border-gray-200 bg-gray-50 text-xs font-bold text-gray-600 shrink-0 overflow-x-auto">
        <button
          @click="currentTab = 'terms'"
          :class="[currentTab === 'terms' ? 'text-[#3483FA] border-b-2 border-[#3483FA] bg-white' : 'hover:text-gray-900']"
          class="flex items-center gap-1.5 px-4 py-3 transition-colors whitespace-nowrap"
        >
          <FileText class="w-4 h-4" />
          <span>Términos y Condiciones</span>
        </button>

        <button
          @click="currentTab = 'privacy'"
          :class="[currentTab === 'privacy' ? 'text-[#3483FA] border-b-2 border-[#3483FA] bg-white' : 'hover:text-gray-900']"
          class="flex items-center gap-1.5 px-4 py-3 transition-colors whitespace-nowrap"
        >
          <Lock class="w-4 h-4" />
          <span>Política de Privacidad</span>
        </button>

        <button
          @click="currentTab = 'payments'"
          :class="[currentTab === 'payments' ? 'text-[#3483FA] border-b-2 border-[#3483FA] bg-white' : 'hover:text-gray-900']"
          class="flex items-center gap-1.5 px-4 py-3 transition-colors whitespace-nowrap"
        >
          <CreditCard class="w-4 h-4" />
          <span>Medios de Pago & Transbank</span>
        </button>

        <button
          @click="currentTab = 'help'"
          :class="[currentTab === 'help' ? 'text-[#3483FA] border-b-2 border-[#3483FA] bg-white' : 'hover:text-gray-900']"
          class="flex items-center gap-1.5 px-4 py-3 transition-colors whitespace-nowrap"
        >
          <HelpCircle class="w-4 h-4" />
          <span>Centro de Ayuda</span>
        </button>
      </div>

      <!-- Tab Content Area -->
      <div class="p-6 overflow-y-auto space-y-4 text-gray-700 leading-relaxed">
        <!-- ================= 1. TÉRMINOS Y CONDICIONES ================= -->
        <div v-if="currentTab === 'terms'" class="space-y-4">
          <h3 class="text-base font-bold text-gray-900">Términos y Condiciones de Uso</h3>
          <p class="text-xs text-gray-500">Última actualización: Noviembre 2026</p>

          <div class="space-y-3">
            <div class="bg-gray-50 p-3.5 rounded-lg border border-gray-200">
              <h4 class="font-bold text-gray-900 mb-1">1. Objeto y Alcance de la Plataforma</h4>
              <p>
                Inacap E-Commerce es un portal de comercio electrónico seguro que conecta a compradores y vendedores autorizados para la adquisición de productos tecnológicos, computación, moda y hogar en Chile. Al navegar o comprar en el sitio, el usuario acepta de manera íntegra estos términos.
              </p>
            </div>

            <div class="bg-gray-50 p-3.5 rounded-lg border border-gray-200">
              <h4 class="font-bold text-gray-900 mb-1">2. Cuentas y Responsabilidad de Usuarios</h4>
              <p>
                Los usuarios pueden registrarse como Compradores o Vendedores. Cada cuenta cuenta con un alias protegido. Los vendedores se comprometen a publicar únicamente productos legítimos, con precios claros, descripciones fidedignas y stock real disponible.
              </p>
            </div>

            <div class="bg-gray-50 p-3.5 rounded-lg border border-gray-200">
              <h4 class="font-bold text-gray-900 mb-1">3. Garantía de Devolución de 30 Días</h4>
              <p>
                Todo producto adquirido a través de la plataforma cuenta con una garantía de devolución gratuita de 30 días desde la fecha de recepción. Si el producto no cumple con lo prometido o presenta fallas, se reembolsará el 100% del dinero pagado.
              </p>
            </div>

            <div class="bg-gray-50 p-3.5 rounded-lg border border-gray-200">
              <h4 class="font-bold text-gray-900 mb-1">4. Envíos y Despachos</h4>
              <p>
                Los productos con la etiqueta "Llega gratis mañana" cuentan con despacho express gratuito a todas las regiones de Chile para compras superiores al monto mínimo estipulado.
              </p>
            </div>
          </div>
        </div>

        <!-- ================= 2. POLÍTICA DE PRIVACIDAD ================= -->
        <div v-else-if="currentTab === 'privacy'" class="space-y-4">
          <h3 class="text-base font-bold text-gray-900">Política de Privacidad y Protección de Datos</h3>
          <p class="text-xs text-gray-500">Compromiso de Confidencialidad y Seguridad</p>

          <div class="space-y-3">
            <div class="bg-emerald-50/60 p-3.5 rounded-lg border border-emerald-200 flex items-start gap-2.5">
              <ShieldCheck class="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" />
              <div>
                <h4 class="font-bold text-emerald-950 mb-0.5">Protección de Identidad y Seudónimos</h4>
                <p class="text-emerald-900">
                  Tu correo electrónico y datos personales nunca son expuestos públicamente en el catálogo ni ante otros usuarios. Toda interacción pública se realiza mediante nombres de tienda o alias seguros.
                </p>
              </div>
            </div>

            <div class="bg-gray-50 p-3.5 rounded-lg border border-gray-200">
              <h4 class="font-bold text-gray-900 mb-1">Cifrado de Credenciales</h4>
              <p>
                Todas las contraseñas se almacenan mediante algoritmos criptográficos irreversibles de alta seguridad. Ningún colaborador de la plataforma tiene acceso a tus claves en texto plano.
              </p>
            </div>

            <div class="bg-gray-50 p-3.5 rounded-lg border border-gray-200">
              <h4 class="font-bold text-gray-900 mb-1">Uso Restringido de la Información</h4>
              <p>
                Los datos de envío (dirección, teléfono y nombre) son utilizados exclusivamente para coordinar la entrega logística del pedido. Inacap E-Commerce no comercializa ni arrienda bases de datos a terceras partes.
              </p>
            </div>

            <div class="bg-gray-50 p-3.5 rounded-lg border border-gray-200">
              <h4 class="font-bold text-gray-900 mb-1">Derechos del Titular (ARCO)</h4>
              <p>
                Puedes solicitar en cualquier momento la actualización, rectificación o eliminación definitiva de tu cuenta y datos personales comunicándote a través del centro de ayuda.
              </p>
            </div>
          </div>
        </div>

        <!-- ================= 3. MEDIOS DE PAGO & TRANSBANK ================= -->
        <div v-else-if="currentTab === 'payments'" class="space-y-4">
          <h3 class="text-base font-bold text-gray-900">Información sobre Pagos Seguros con Transbank Webpay Plus</h3>
          <p class="text-xs text-gray-500">Pasarela oficial y medios de pago admitidos</p>

          <div class="space-y-3">
            <div class="bg-red-50/60 p-3.5 rounded-lg border border-red-200 flex items-start gap-2.5">
              <CreditCard class="w-5 h-5 text-red-700 shrink-0 mt-0.5" />
              <div>
                <h4 class="font-bold text-red-950 mb-0.5">Transbank Webpay Plus Oficial</h4>
                <p class="text-red-900">
                  La plataforma opera integrada con la pasarela oficial Webpay Plus de Transbank, el sistema de pagos electrónicos líder y más seguro de Chile.
                </p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div class="bg-gray-50 p-3 rounded-lg border border-gray-200">
                <span class="font-bold text-gray-900 block mb-1">Tarjetas de Débito (Redcompra)</span>
                <p class="text-[11px] text-gray-600">
                  Pago directo con cargo inmediato a tu cuenta corriente o cuenta RUT de cualquier banco nacional.
                </p>
              </div>
              <div class="bg-gray-50 p-3 rounded-lg border border-gray-200">
                <span class="font-bold text-gray-900 block mb-1">Tarjetas de Crédito Bancarias</span>
                <p class="text-[11px] text-gray-600">
                  Visa, Mastercard, American Express y Magna con opción de 3, 6 y 12 cuotas sin interés.
                </p>
              </div>
              <div class="bg-gray-50 p-3 rounded-lg border border-gray-200">
                <span class="font-bold text-gray-900 block mb-1">Tarjetas de Prepago Digital</span>
                <p class="text-[11px] text-gray-600">
                  Tenpo, Mach, Dale y Copec Pay aceptadas al instante.
                </p>
              </div>
              <div class="bg-gray-50 p-3 rounded-lg border border-gray-200">
                <span class="font-bold text-gray-900 block mb-1">Voucher y Respaldo Oficial</span>
                <p class="text-[11px] text-gray-600">
                  Cada pago genera un comprobante con código de autorización y número de orden verificable.
                </p>
              </div>
            </div>

            <div class="bg-blue-50 p-3 rounded-md border border-blue-200 text-[11px] text-blue-900">
              <strong>Certificación de Seguridad en Pagos:</strong> Tus datos bancarios y números de tarjeta viajan directamente encriptados hacia Transbank bajo protocolos seguros. La tienda nunca almacena claves secretas ni códigos de seguridad CVV.
            </div>
          </div>
        </div>

        <!-- ================= 4. CENTRO DE AYUDA ================= -->
        <div v-else class="space-y-4">
          <h3 class="text-base font-bold text-gray-900">Centro de Ayuda y Preguntas Frecuentes</h3>
          <p class="text-xs text-gray-500">Respuestas rápidas para compradores y vendedores</p>

          <div class="space-y-3">
            <details class="group bg-gray-50 p-3 rounded-lg border border-gray-200 cursor-pointer">
              <summary class="font-bold text-gray-900 flex justify-between items-center list-none">
                <span>¿Cómo realizo una compra en el sitio?</span>
                <span class="text-blue-600 font-bold group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p class="mt-2 text-gray-600 text-[11px] leading-relaxed">
                Selecciona el producto que deseas, presiona "Comprar Ahora" o "Agregar al Carrito". En el carrito de compras podrás revisar el total certificado y elegir tu método de pago preferido en el carrusel de Transbank.
              </p>
            </details>

            <details class="group bg-gray-50 p-3 rounded-lg border border-gray-200 cursor-pointer">
              <summary class="font-bold text-gray-900 flex justify-between items-center list-none">
                <span>¿Cómo puedo comenzar a vender mis productos?</span>
                <span class="text-blue-600 font-bold group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p class="mt-2 text-gray-600 text-[11px] leading-relaxed">
                Crea una cuenta seleccionando el rol de "Vendedor" o ingresa con una cuenta autorizada. Luego presiona el botón "Vender" en la barra superior amarilla para abrir el formulario de publicación, subir tus fotos y características de producto.
              </p>
            </details>

            <details class="group bg-gray-50 p-3 rounded-lg border border-gray-200 cursor-pointer">
              <summary class="font-bold text-gray-900 flex justify-between items-center list-none">
                <span>¿Cuáles son los plazos y costos de envío?</span>
                <span class="text-blue-600 font-bold group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p class="mt-2 text-gray-600 text-[11px] leading-relaxed">
                Todos los productos destacados cuentan con despacho express gratuito. Los pedidos son procesados el mismo día hábil y entregados en un plazo de 24 a 48 horas en Santiago y regiones principales.
              </p>
            </details>

            <details class="group bg-gray-50 p-3 rounded-lg border border-gray-200 cursor-pointer">
              <summary class="font-bold text-gray-900 flex justify-between items-center list-none">
                <span>¿Cómo solicito una devolución o cambio?</span>
                <span class="text-blue-600 font-bold group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <p class="mt-2 text-gray-600 text-[11px] leading-relaxed">
                Dispones de 30 días continuos desde la entrega para iniciar una devolución sin costo. El producto debe devolverse en su embalaje original.
              </p>
            </details>
          </div>
        </div>
      </div>

      <!-- Footer Action -->
      <div class="p-4 bg-gray-50 border-t border-gray-200 flex justify-end shrink-0">
        <button
          @click="close"
          class="bg-[#3483FA] hover:bg-blue-600 text-white font-bold py-2 px-5 rounded-md text-xs transition-colors"
        >
          Entendido / Cerrar
        </button>
      </div>
    </div>
  </div>
</template>
