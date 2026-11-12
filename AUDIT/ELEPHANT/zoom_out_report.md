# Stage 5 Report: Initial Zoom Out Review (Simplicity, Minimalismo & Contradicciones TRIZ)

**Documento Auditado**: [`DOCUMENTACION_SISTEMA.md`](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md)  
**Contexto de Referencia**: [`README.md`](file:///home/misnull/Proyectos/inacap-ecommerce/README.md), Frontend Vue 3 + Vite, Backend Django + PostgreSQL.  
**Revisores Especializados**: `egm-zoom-out` (Arquitecto Escéptico: Simplicidad, YAGNI, Preparación para Producción) y `egm-inventive-catalyst` (Catalizador Inventivo: Resolución de Contradicciones Técnicas TRIZ).

---

## 1. Resumen de la Evaluación Arquitectónica

El documento técnico presenta una contradicción marcada entre las declaraciones formales de alto nivel (SGSI ISO/IEC 27001:2022, OWASP Top 10, pasarela Transbank Webpay Plus, gateways Nginx y transacciones ACID estrictas) y la realidad operativa del código actual, el cual conserva atajos propios de un prototipo académico/mockup:

1. **Simulación Insegura de Pasarela Bancaria**: La pasarela Transbank en frontend opera mediante un modal simulado interactivo que autoaprueba compras ante cualquier excepción o token de prueba.
2. **Riesgo Operativo Crítico (Split-Brain de Base de Datos)**: Sondeo de socket en `settings.py` que conmuta silenciosamente de PostgreSQL a SQLite si la base tarda más de 1 segundo en responder.
3. **Persistencia de Atajos Demo**: Botones de "Cuentas Demo para Pruebas Rápidas" en `AuthModal.vue` exponiendo credenciales en texto claro, y ejecución automática de `seed_ecommerce` en cada inicio del contenedor Docker.
4. **Falsas Defensas Anti-XSS (Usabilidad Rota)**: Intercepción de teclado en `@keypress` y serializadores que prohíben caracteres estándar como `$`, `*`, `[`, `]`, `{`, `}`, rompiendo la descripción de productos legítimos.
5. **Infraestructura de Producción Inexistente**: Ejecución sobre `runserver` y Vite dev server sin Nginx, Gunicorn ni persistencia de medios en volumen Docker.

---

## 2. Hallazgos Críticos: Bloqueadores de Producción (🔴 Blocker)

### 🔴 Blocker 1: Falso Fallback y Auto-Aprobación Silenciosa en Pagos Transbank
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§7)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-7-pasarela-transbank), [`backend/apps/payments/services.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/payments/services.py#L108-L147), [`frontend/src/components/PaymentCarouselModal.vue`](file:///home/misnull/Proyectos/inacap-ecommerce/frontend/src/components/PaymentCarouselModal.vue#L216-L254), [`backend/apps/payments/views.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/payments/views.py#L120-L177).
- **Problema**: El modal de pago en frontend intercepta el flujo e inyecta un simulador local sin redirección bancaria real. Si la pasarela falla o recibe una excepción, `commit_transaction` captura el error y retorna `status: 'AUTHORIZED'` y un código de autorización falso. En producción, cualquier corte de red regala productos sin recaudar dinero.
- **Acción Obligatoria**:
  - Eliminar el modal simulador del frontend.
  - Implementar el flujo bancario estándar: Inicialización -> Redirección del navegador a Webpay Plus -> Retorno bancario oficial al backend -> Verificación criptográfica con SDK -> Confirmación o rechazo explícito.
  - Si Transbank falla, la orden debe marcarse irrevocablemente como `FAILED` o `REQUIRES_RETRY`.

### 🔴 Blocker 2: Conmutación Dinámica Silenciosa a SQLite (Riesgo de Split-Brain)
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§3.3)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-3-3-sondeo-puerto), [`backend/config/settings.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/config/settings.py#L89-L137).
- **Problema**: `check_postgres_connection` abre un socket al puerto 5432 con timeout de 1 segundo en cada arranque/import. Si PostgreSQL experimenta latencia o reinicio, los workers de Gunicorn alternan silenciosamente entre PostgreSQL y un archivo `db.sqlite3` efímero, corrompiendo la consistencia de inventario y compras.
- **Acción Obligatoria**:
  - Eliminar el sondeo de socket y el fallback a SQLite.
  - La aplicación debe aplicar *Fail-Fast*: si `DEBUG=False` o está en producción y PostgreSQL no está disponible, el proceso debe fallar inmediatamente. El control de disponibilidad debe residir en healthchecks de Docker o orquestador.

### 🔴 Blocker 3: Ausencia de Transacciones Atómicas y Condiciones de Carrera en Descuento de Stock
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§3.5, §13)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-3-5-transacciones-sqli), [`backend/apps/payments/views.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/payments/views.py#L127-L177).
- **Problema**: La documentación asegura que el commit y decremento de stock ocurren bajo `@transaction.atomic`. En el código real, `TransbankCommitAPIView` no tiene dicho decorador ni bloqueo pesimista (`select_for_update`). Compras concurrentes pueden provocar sobreventa (Lost Updates). Si el stock se agota antes del commit, la compra se cobra pero el producto no se descuenta ni se anula el cobro.
- **Acción Obligatoria**:
  - Envolver la confirmación de pago bajo `@transaction.atomic`.
  - Aplicar bloqueo `Product.objects.select_for_update()` o expresiones `F('stock') - cantidad`.
  - Implementar reversa automática con Transbank (`Transaction.refund`) en caso de incompatibilidad de inventario durante el commit.

### 🔴 Blocker 4: Cuentas Demo Hardcodeadas y Resiembra Automática en Docker
- **Ámbito Afectado**: [`frontend/src/components/AuthModal.vue`](file:///home/misnull/Proyectos/inacap-ecommerce/frontend/src/components/AuthModal.vue#L251-L279), [`backend/apps/products/management/commands/seed_ecommerce.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/products/management/commands/seed_ecommerce.py#L25-L86), [`docker-compose.yml`](file:///home/misnull/Proyectos/inacap-ecommerce/docker-compose.yml#L24-L27).
- **Problema**: `AuthModal.vue` renderiza botones directos para autocompletar credenciales conocidas (`Admin1234!`, `Vendedor1234!`, `Comprador1234!`). A su vez, `docker-compose.yml` corre `seed_ecommerce` en cada inicio del contenedor, sobreescribiendo datos de producción con catálogos y reseñas ficticias.
- **Acción Obligatoria**:
  - Eliminar los botones de autocompletado demo en `AuthModal.vue` y los métodos `fillDemo`.
  - Retirar `seed_ecommerce` del comando por defecto en `docker-compose.yml`.

### 🔴 Blocker 5: Inexistencia de Servidor Web de Producción y Rutas de Archivos Multimedia Rotas
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§1.2)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-1-2-arquitectura-c4), [`docker-compose.yml`](file:///home/misnull/Proyectos/inacap-ecommerce/docker-compose.yml), [`backend/config/urls.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/config/urls.py#L17-L18).
- **Problema**: Se documenta un reverse proxy Nginx pero solo existen servidores de desarrollo (`runserver` y Vite). Con `DEBUG=False`, Django no sirve archivos en `MEDIA_URL`, haciendo que todas las fotos de productos subidas devuelvan `404 Not Found`.
- **Acción Obligatoria**:
  - Añadir configuración Nginx para servir estáticos compilados de Vue (`dist/`), fotos subidas (`media/`) y proxear `/api/` hacia Gunicorn.
  - Asegurar un volumen Docker persistente para `/media/productos/`.

---

## 3. Preocupaciones Mayores y Deuda Técnica (🟡 Major)

### 🟡 Major 1: Lista Negra Naïve Anti-XSS que Invalida Inputs Comerciales (`$`, `*`, `[`, `]`, `{`, `}`)
- **Ámbito Afectado**: [`frontend/src/utils/security.js`](file:///home/misnull/Proyectos/inacap-ecommerce/frontend/src/utils/security.js#L11-L44), [`backend/apps/products/serializers.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/products/serializers.py#L8-L23), [`DOCUMENTACION_SISTEMA.md` (§9.3)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-9-3-restriccion-caracteres).
- **Impacto**: Se bloquea a los vendedores de escribir "$10.000", "Monitor 24*", o especificaciones entre corchetes "[DDR5]". La justificación de evitar CSTI no aplica a Vue 3, que escapa texto de forma segura por defecto en el DOM.
- **Solución**: Remover la captura destructiva de teclado `@keypress` y las listas negras de caracteres comunes. La defensa XSS debe apoyarse en el escape contextual de Vue 3, CSP estricto y saneamiento de etiquetas script reales en el backend.

### 🟡 Major 2: Procesamiento Gráfico Sincrónico Bloqueante (Riesgo DoS por CPU)
- **Ámbito Afectado**: [`backend/apps/products/utils.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/products/utils.py#L16-L76), [`backend/apps/products/serializers.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/products/serializers.py#L169-L177).
- **Impacto**: Redimensionar y recomprimir iterativamente hasta 5 imágenes en el hilo principal de Django consume entre 3 y 6 segundos de CPU por producto. Pocos vendedores publicando a la vez agotan los hilos del servidor web.
- **Solución**: Pre-escalar en cliente antes de la subida (Canvas HTML5) o delegar el procesamiento a tareas en background.

### 🟡 Major 3: Navegación Manual en Frontend en Lugar de `vue-router`
- **Ámbito Afectado**: [`frontend/src/App.vue`](file:///home/misnull/Proyectos/inacap-ecommerce/frontend/src/App.vue#L45-L70), [`frontend/src/stores/products.js`](file:///home/misnull/Proyectos/inacap-ecommerce/frontend/src/stores/products.js), [`frontend/package.json`](file:///home/misnull/Proyectos/inacap-ecommerce/frontend/package.json).
- **Impacto**: La navegación se maneja manualmente con cadenas en Pinia y llamadas a `window.history.pushState`, lo que genera problemas con el botón atrás/adelante del navegador, sincronización de filtros en query params y protección de rutas.
- **Solución**: Adoptar `vue-router` oficial para gestionar vistas declarativas (`/`, `/producto/:slug`, `/mis-publicaciones`).

### 🟡 Major 4: Desincronización y Redundancia en Modelo de Roles
- **Ámbito Afectado**: [`backend/apps/accounts/models.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/accounts/models.py).
- **Impacto**: Existen dos fuentes de verdad: `UserCredential.role` (enum) y la tabla intermedia `UserRol`. Los signals generan tablas vacías de `Persona` que complican las consultas (joins innecesarios de 3 niveles para obtener datos de un vendedor).
- **Solución**: Unificar la verificación de roles en una sola fuente de verdad inequívoca.

---

## 4. Mejoras Menores (🟢 Nit)

1. **Discrepancias de URLs de Documentación**: La documentación cita `GET /api/v1/auth/profile/`, pero la ruta real implementada es `GET /api/v1/auth/me/`.
2. **Geolocalización Simulada**: El store [`location.js`](file:///home/misnull/Proyectos/inacap-ecommerce/frontend/src/stores/location.js) consulta la geolocalización del navegador pero descarta las coordenadas reales e inyecta siempre "Providencia, RM".
3. **Piso Forzado de 251 Caracteres en ADS**: `MinLengthValidator(251)` obliga a vendedores a redactar texto de relleno; es preferible usar especificaciones estructuradas.
4. **Volumen Docker para Media**: Falta declarar un volumen dedicado para preservar fotos subidas entre recreaciones de contenedores.

---

## 5. Matriz de Síntesis y Recomendaciones Técnicas

| Prioridad | Componente | Hallazgo Crítico | Acción Requerida |
| :--- | :--- | :--- | :--- |
| 🔴 **Blocker** | Pagos Transbank | Aprobación simulada ante excepciones y modal falso | Eliminar modal fake; implementar redirección bancaria real y Fail-Closed |
| 🔴 **Blocker** | Base de Datos | Fallback dinámico a SQLite en `settings.py` | Eliminar sondeo de socket; aplicar fail-fast estricto en producción |
| 🔴 **Blocker** | Inventario | Sin `@transaction.atomic` ni bloqueo pesimista | Implementar bloqueo pesimista y reversa automática de cobro si falta stock |
| 🔴 **Blocker** | Auth & Seeds | Cuentas demo hardcodeadas y autoseed continuo | Eliminar botones de cuentas rápidas y remover autoseed de Docker |
| 🔴 **Blocker** | Servidor Web | Falta de proxy Nginx y medios rotos sin DEBUG | Configurar Nginx para estáticos, uploads y WSGI con Gunicorn |
| 🟡 **Major** | Anti-XSS | Bloqueo de `$`, `*`, `[`, `]` en teclados y backend | Permitir caracteres estándar; confiar en auto-escape de Vue 3 y CSP |
| 🟡 **Major** | Enrutamiento | SPA sin `vue-router` operando con historial manual | Instalar y migrar navegación a `vue-router` oficial |
