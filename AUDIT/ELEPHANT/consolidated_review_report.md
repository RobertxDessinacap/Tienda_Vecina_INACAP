# Consolidated EGM Review Report: Tienda Vecina E-Commerce

**Documento Objetivo**: [`DOCUMENTACION_SISTEMA.md`](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md)  
**Documento de Soporte**: [`README.md`](file:///home/misnull/Proyectos/inacap-ecommerce/README.md)  
**Código Base Analizado**: `/home/misnull/Proyectos/inacap-ecommerce` (Backend Django REST, Frontend Vue 3 + Vite, PostgreSQL 16)  
**Pipeline Ejecutado**: Curated Pipeline (Etapas 5 a 9)  
**Reportes Parciales de Etapa**:
- Etapa 5: [`zoom_out_report.md`](file:///root/.gemini/antigravity-cli/brain/3bfe860b-3fd4-41f9-855b-0ded13b04084/zoom_out_report.md)
- Etapa 6: [`comprehension_report.md`](file:///root/.gemini/antigravity-cli/brain/3bfe860b-3fd4-41f9-855b-0ded13b04084/comprehension_report.md)
- Etapa 7: [`critic_report.md`](file:///root/.gemini/antigravity-cli/brain/3bfe860b-3fd4-41f9-855b-0ded13b04084/critic_report.md)
- Etapa 8: [`intermediate_zoom_out_report.md`](file:///root/.gemini/antigravity-cli/brain/3bfe860b-3fd4-41f9-855b-0ded13b04084/intermediate_zoom_out_report.md)
- Etapa 9: [`implementation_readiness_report.md`](file:///root/.gemini/antigravity-cli/brain/3bfe860b-3fd4-41f9-855b-0ded13b04084/implementation_readiness_report.md)

---

## 1. Veredicto y Resumen Ejecutivo de la Revisión

**Estado Global**: 🔴 **TRANSICIÓN DE MOCKUP A PRODUCCIÓN BLOQUEADA HASTA RESOLVER 6 COMPUERTAS CRÍTICAS**

La plataforma posee una arquitectura base adecuada (**Vue 3 SPA + Django REST Framework + PostgreSQL**), pero conserva atajos estructurales de prototipado/demo y discrepancias documentales que deben ser subsanados para operar en un entorno de producción real:

1. **Simulación Insegura en Pagos**: La pasarela Transbank Webpay Plus autoaprueba pagos ante fallos o excepciones con códigos ficticios, y la interfaz utiliza un modal simulador interactivo en vez de la redirección bancaria oficial.
2. **Riesgo Operativo de Split-Brain**: `settings.py` efectúa un sondeo por socket TCP que conmuta silenciosamente de PostgreSQL a SQLite si la base tarda más de 1 segundo en responder.
3. **Condiciones de Carrera en Stock**: El checkout carece de `@transaction.atomic` y de bloqueos pesimistas (`select_for_update`), permitiendo sobreventas en compras concurrentes.
4. **Infraestructura de Producción Inexistente**: Se documenta un reverse proxy Nginx que no existe en el repositorio; bajo `DEBUG=False`, Django no sirve archivos en `MEDIA_URL`, provocando errores `404` en todas las fotos de productos subidas.
5. **Artefactos Demo Expuestos**: Botones de "Cuentas Rápidas" en `AuthModal.vue` que autocompletan contraseñas en texto claro, y ejecución automática de `seed_ecommerce` en el inicio del contenedor Docker.
6. **Usabilidad Rota por Filtros Anti-XSS**: Intercepción destructiva de teclado (`@keypress`) que bloquea caracteres legítimos como `$`, `*`, `[`, `]`, `;`, impidiendo descripciones técnicas y comerciales normales.

---

## 2. Matriz de Trazabilidad de Hallazgos

| ID | Compuerta / Área | Gravedad | Hallazgo Consolidado | Archivo(s) Afectado(s) | Acción de Remediación |
| :---: | :--- | :---: | :--- | :--- | :--- |
| **G-1** | **Gate 1: Pagos Fail-Closed** | 🔴 Blocker | Auto-aprobación en excepciones bancarias y modal simulado en frontend | `payments/services.py`<br>`payments/views.py`<br>`PaymentCarouselModal.vue` | Eliminar auto-aprobación ante errores (Fail-Closed); remover modal fake e implementar redirección real a Webpay. |
| **G-2** | **Gate 2: DB Fail-Fast** | 🔴 Blocker | Sondeo TCP conmuta a SQLite y Docker ejecuta `seed_ecommerce` en cada inicio | `config/settings.py`<br>`docker-compose.yml` | Eliminar sondeo de socket y fallback a SQLite; aplicar Fail-Fast y retirar auto-seed del arranque de contenedores. |
| **G-3** | **Gate 3: Concurrencia Stock** | 🔴 Blocker | Confirmación de pago sin `@transaction.atomic` ni bloqueo pesimista de stock | `payments/views.py` | Envolver en `@transaction.atomic`, bloquear con `select_for_update` y reversar cobro si no hay stock disponible. |
| **G-4** | **Gate 4: Infraestructura** | 🔴 Blocker | C4 documenta Nginx pero solo hay dev server; `MEDIA_URL` roto con `DEBUG=False` | `docker-compose.yml`<br>`config/urls.py`<br>`backend/Dockerfile` | Configurar Nginx como reverse proxy, ejecutar backend con Gunicorn y añadir volumen persistente para medios. |
| **G-5** | **Gate 5: Usabilidad Input** | 🟡 Major | `@keypress` intercepta teclado y serializadores bloquean `$`, `*`, `[`, `]`, `;` | `frontend/src/utils/security.js`<br>`products/serializers.py` | Remover bloqueo de teclado y listas negras; confiar en el auto-escape de Vue 3, sanitización de scripts y CSP. |
| **G-6** | **Gate 6: Identidad y PII** | 🟡 Major | Contradicción entre exponer nombre civil (SERNAC) y privacidad (ISO 27001) | `products/serializers.py`<br>`DOCUMENTACION_SISTEMA.md` | Mostrar únicamente `UserProfile.public_alias` en catálogo C2C; reservar nombre civil a tiendas oficiales y recibos. |
| **D-1** | **Cuentas Demo** | 🔴 Blocker | Botones de "Cuentas Rápidas" en interfaz exponen credenciales de prueba | `frontend/src/components/AuthModal.vue` | Eliminar función `fillDemo` y el bloque de botones demo del modal de login. |
| **D-2** | **Contratos de API** | 🟡 Major | `/api/v1/auth/profile/` no existe; el endpoint real es `/api/v1/auth/me/` | `DOCUMENTACION_SISTEMA.md`<br>`accounts/urls.py` | Actualizar la matriz de endpoints de la documentación a `/api/v1/auth/me/`. |
| **D-3** | **Geolocalización** | 🟡 Major | `Permissions-Policy: geolocation=()` bloquea el selector de comunas | `security/middleware.py`<br>`DOCUMENTACION_SISTEMA.md` | Cambiar directiva a `geolocation=(self)` o documentar el selector como estrictamente manual. |
| **D-4** | **Rutas Windows** | 🟢 Nit | Presencia de 11 enlaces absolutos `file:///C:/Users/Rober/...` en documentación | `DOCUMENTACION_SISTEMA.md` | Reemplazar todos los enlaces absolutos de Windows por rutas relativas del repositorio. |

---

## 3. Plan de Remediación Técnica (Checklist de Ejecución)

### Paso 1: Limpieza Inmediata de Artefactos Demo
- [ ] Eliminar los botones de "Cuentas Rápidas" y la función `fillDemo` en [`AuthModal.vue`](file:///home/misnull/Proyectos/inacap-ecommerce/frontend/src/components/AuthModal.vue#L251-L279).
- [ ] Remover `python manage.py seed_ecommerce` de la directiva `command` en [`docker-compose.yml`](file:///home/misnull/Proyectos/inacap-ecommerce/docker-compose.yml#L26).

### Paso 2: Integridad Financiera y Pasarela Webpay
- [ ] En [`services.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/payments/services.py): eliminar el fallback que aprueba la orden ante excepciones en `commit_transaction`. Todo error debe marcar la orden como `FAILED`.
- [ ] En [`PaymentCarouselModal.vue`](file:///home/misnull/Proyectos/inacap-ecommerce/frontend/src/components/PaymentCarouselModal.vue): remover el formulario simulador con tarjeta fija y ejecutar la redirección hacia la URL oficial de Webpay Plus provista por el backend.
- [ ] En [`views.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/payments/views.py): envolver `TransbankCommitAPIView.post` bajo `@transaction.atomic` y aplicar `Product.objects.select_for_update()` para asegurar consistencia estricta de inventario.

### Paso 3: Estabilidad de Base de Datos e Infraestructura
- [ ] En [`settings.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/config/settings.py): eliminar la función `check_postgres_connection` y el fallback automático a SQLite. Configurar comportamiento Fail-Fast.
- [ ] En `docker-compose.yml`: agregar un servicio Nginx como reverse proxy para servir estáticos y medios (`media/`), derivando `/api/` hacia Gunicorn.
- [ ] Declarar un volumen Docker persistente para `/media/productos/`.

### Paso 4: Usabilidad y Documentación
- [ ] En [`security.js`](file:///home/misnull/Proyectos/inacap-ecommerce/frontend/src/utils/security.js) y modales: eliminar la función `blockDangerousCharsOnKeypress`.
- [ ] En [`serializers.py`](file:///home/misnull/Proyectos/inacap-ecommerce/backend/apps/products/serializers.py): permitir signos de puntuación y comerciales estándar (`$`, `*`, `[`, `]`, `;`).
- [ ] En [`DOCUMENTACION_SISTEMA.md`](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md): corregir la ruta `/api/v1/auth/me/`, eliminar rutas absolutas de Windows y sincronizar la especificación técnica con el estado del código.
