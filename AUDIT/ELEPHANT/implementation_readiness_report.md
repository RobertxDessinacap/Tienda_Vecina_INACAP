# Implementation Readiness Test Report (Stage 9)

**Documento Auditado**: [`DOCUMENTACION_SISTEMA.md`](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md)  
**Código Fuente Cotejado**: `/home/misnull/Proyectos/inacap-ecommerce`  
**Revisores Especializados**:
- `egm-implementation-readiness`: Tech Lead Pragmático (Verificación de accionabilidad, mitigación de riesgos de producción y resolución de las 6 compuertas Go/No-Go).
- `egm-codebase-details`: Auditor Pedante de Calidad de Código (Discrepancias entre código real y documentación, oportunidades de reutilización y localización de código mockup/demo).

---

## 1. Resumen Ejecutivo y Dictamen de Preparación

**Dictamen**: 🔴 **NO APTO PARA PRODUCCIÓN (BLOQUEADORES TÉCNICOS DETECTADOS)**

Aunque [`DOCUMENTACION_SISTEMA.md`](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md) presenta un diseño conceptual detallado y justificaciones de cumplimiento (ISO 27001 y OWASP), el sistema conserva **atajos críticos de prototipo demo y discrepancias sustanciales con el código real**:
1. La pasarela Transbank opera con una auto-aprobación simulada ante excepciones y un modal falso interactivo en cliente.
2. `settings.py` implementa un sondeo TCP de socket que conmuta silenciosamente a SQLite local.
3. Se omiten transacciones atómicas y bloqueos pesimistas en el commit de compras, permitiendo sobreventa.
4. El contenedor Nginx documentado en el diagrama C4 no existe en `docker-compose.yml`, y Django bajo `DEBUG=False` no sirve imágenes en `MEDIA_URL`.
5. Se mantienen botones de "Cuentas Rápidas" con contraseñas hardcodeadas en `AuthModal.vue` y resiembra destructiva en `docker-compose.yml`.
6. Existen discrepancias contractuales directas (rutas de API inexistentes como `/api/v1/auth/profile/` en vez de `/me/`, payloads incompatibles y nombres de estados desalineados).

---

## 2. Matriz de Discrepancias Código vs. Documentación

| ID | Severidad | Elemento Afectado | Documentado en `DOCUMENTACION_SISTEMA.md` | Código Real Implementado |
| :--- | :---: | :--- | :--- | :--- |
| **D-01** | 🔴 Blocker | Ruta de Perfil | `GET /api/v1/auth/profile/` (Línea 124) | `GET /api/v1/auth/me/` en `apps/accounts/urls.py:13` |
| **D-02** | 🔴 Blocker | Reverse Proxy | Nginx Gateway puerto 8000 en Diagrama C4 | No existe Nginx ni `nginx.conf`; solo `runserver` monohilo |
| **D-03** | 🟡 Major | Payload de Registro | `{"nombres", "apellidos", "public_alias"}` (Línea 122) | Serializador exige `{"full_name", "custom_alias", "rut"}` |
| **D-04** | 🟡 Major | Estados de Orden | `COMPLETED` y `REFUNDED` (Líneas 301, 455) | Modelo `Order` define `AUTHORIZED` y `REVERSED` |
| **D-05** | 🟡 Major | Conteo de Tablas BD | Total de 18 tablas (Sección 3.4) | Son 19 tablas (se omitió `products_productreview`) |
| **D-06** | 🟡 Major | Paginación de Catálogo | Catálogo MercadoLibre paginado (Línea 125) | `ProductListCreateView` serializa todo el QuerySet sin paginar |
| **D-07** | 🟡 Major | Geolocalización vs CSP | Promesa de detección automática (Línea 496) | `Permissions-Policy: geolocation=()` desactiva el sensor |
| **D-08** | 🟡 Major | Cuentas Demo en UI | No documentadas formalmente | Botones de fast demo login expuestos en `AuthModal.vue:251-279` |
| **D-09** | 🟢 Nit | Rutas de Archivos | Enlaces absolutos Windows `file:///C:/...` | Repositorio alojado en Linux `/home/misnull/...` |
| **D-10** | 🟢 Nit | Endpoint de Métodos | `/api/v1/payments/methods/` no documentado | Implementado en backend pero desacoplado del frontend |

---

## 3. Inventario de Código Mockup / Demo Detectado

1. **Botones de "Cuentas Rápidas" en UI**:
   - `frontend/src/components/AuthModal.vue` (Líneas 61–71, 251–279): métodos `fillDemo` que autocompletan credenciales (`vendedor@inacap.cl` / `Vendedor1234!`, `comprador@inacap.cl` / `Comprador1234!`, `admin@inacap.cl` / `Admin1234!`).
2. **Resiembra Automática en Docker**:
   - `docker-compose.yml` (Línea 26): `python manage.py seed_ecommerce` se corre en cada inicio, sobreescribiendo datos reales con fixtures académicas.
3. **Simulador Falso de Webpay Plus**:
   - `backend/apps/payments/services.py` (Líneas 112–117, 139–147): auto-aprobación ante excepciones de red con código simulado `'6623'`.
   - `frontend/src/components/PaymentCarouselModal.vue` (Líneas 216–255): modal simulador local que intercepta la navegación bancaria.
4. **Geolocalización Simulada**:
   - `frontend/src/stores/location.js` (Líneas 47–53): hardcodea `'Providencia, RM'` descartando las coordenadas del navegador.

---

## 4. Oportunidades de Reutilización de Librerías

1. **`djangorestframework-simplejwt`**: Reemplazar la generación manual de JWT en `accounts/authentication.py` para obtener rotación de tokens, refresh tokens seguros y listas negras de revocación.
2. **`vue-router` (v4)**: Sustituir la manipulación artesanal de `window.history.pushState` en `App.vue` por navegación declarativa oficial con Navigation Guards.
3. **Paginación Genérica de DRF (`PageNumberPagination`)**: Habilitar paginación estándar en `ProductListCreateView` para evitar saturación de memoria RAM en PostgreSQL.
4. **`whitenoise`**: Incorporar en `settings.py` para permitir la entrega de archivos estáticos comprimidos en producción de forma autónoma.

---

## 5. Plan de Acción Técnico para Producción (Checklist de Ejecución)

### Fase 1: Integridad Financiera y Pasarela Webpay (Gate 1 & Gate 3)
- [ ] **Eliminar el Mock de Aprobación**: En `backend/apps/payments/services.py`, suprimir el fallback de aprobación ante excepciones en `commit_transaction`. Todo error debe retornar `status: 'FAILED'`.
- [ ] **Eliminar el Simulador en Frontend**: En `frontend/src/components/PaymentCarouselModal.vue`, remover el formulario mock de tarjeta y redirigir el navegador hacia la URL oficial de Webpay Plus provista por el backend.
- [ ] **Aislamiento Transaccional y Bloqueo Pesimista**: En `backend/apps/payments/views.py`, decorar `TransbankCommitAPIView.post` con `@transaction.atomic` e implementar `Product.objects.select_for_update()` para asegurar que no se produzca sobreventa de inventario ni pagos sin stock disponible.

### Fase 2: Resiliencia de Base de Datos y Limpieza de Entorno (Gate 2)
- [ ] **Eliminar Sondeo TCP y Fallback SQLite**: En `backend/config/settings.py`, remover la función `check_postgres_connection` y la conmutación a SQLite. Configurar la aplicación para que aplique *Fail-Fast* en producción.
- [ ] **Eliminar Resiembra en Contenedores**: En `docker-compose.yml`, retirar `python manage.py seed_ecommerce` del comando de arranque.
- [ ] **Eliminar Cuentas Demo en UI**: En `frontend/src/components/AuthModal.vue`, borrar el método `fillDemo` y la sección visual de botones "Cuentas Demo para Pruebas Rápidas".

### Fase 3: Infraestructura de Producción (Gate 4)
- [ ] **Configurar Servidor WSGI**: Añadir `gunicorn` en `backend/requirements.txt` y actualizar `Dockerfile` para ejecutar Gunicorn en lugar de `runserver`.
- [ ] **Contenedor Nginx y Volumen de Medios**: Crear `nginx.conf` y añadir el servicio `nginx` en `docker-compose.yml` para servir estáticos, servir `/media/` y proxear la API, asignando un volumen persistente para las fotos de productos.

### Fase 4: Normalización de Entradas y Usabilidad (Gate 5)
- [ ] **Eliminar Intercepción Física de Teclado**: En `frontend/src/utils/security.js` y componentes de formulario, remover `@keypress="blockDangerousCharsOnKeypress"`.
- [ ] **Permitir Puntuación Estándar en Serializadores**: En `backend/apps/products/serializers.py`, permitir caracteres legítimos (`$`, `*`, `[`, `]`, `;`), manteniendo la validación enfocada exclusivamente en scripts y etiquetas HTML peligrosas.

### Fase 5: Alineación de Contratos y Documentación (Gate 6)
- [ ] **Sincronizar Endpoints y Payloads**: Corregir en `DOCUMENTACION_SISTEMA.md` la ruta a `/api/v1/auth/me/`, los campos del serializador de registro y el listado de 19 tablas relacionales.
- [ ] **Ajustar Cabecera de Geolocalización**: Modificar en `backend/apps/security/middleware.py` la cabecera a `Permissions-Policy: geolocation=(self)` para habilitar el selector de comunas.
- [ ] **Reemplazar Rutas Absolutas de Windows**: Convertir todas las URLs `file:///C:/Users/Rober/...` en rutas relativas del repositorio.
