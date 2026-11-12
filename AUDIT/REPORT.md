# Informe Consolidado de Auditoría de Seguridad — Tienda Vecina (`inacap-ecommerce`)

**Rama Auditada:** `develop` (`commit a753dea7bef3bdfa8e458fa53f62c15b113c20c7`)  
**Metodología:** Cloudflare Security Audit Skill (3 Olas Exhaustivas: Reconocimiento, Análisis Profundo y Caza Especializada Asistida por Agentes Autónomos)  
**Fecha de Emisión:** Noviembre 2026  
**Estado del Análisis:** Completo (24 Unidades de Cobertura en Ledger, 31 Registros Auditados)  

---

## 1. Perfil de Ejecución y Declaración de Alcance

- **Perfil de Auditoría:** `deep` (Análisis estático y dinámico exhaustivo de código fuente y entorno local).
- **Declaración de Aislamiento:** Ejecución estrictamente delimitada a inspección de código fuente y pruebas locales de caja blanca (*sandboxed source-and-local-only execution*), sin interactuar con pasarelas financieras externas reales ni entornos de producción en vivo.
- **Alcance Analizado:** Módulos de Backend (`apps/accounts`, `apps/payments`, `apps/products`, `apps/security`, `config/`), Frontend Vue 3 (`src/components/`, `src/stores/`, `src/utils/`, `src/services/`), Infraestructura y Contenedores (`docker-compose.yml`, Dockerfiles, scripts bash/bat, `.env.example`).
- **Presupuesto y Agentes:** Coordinador general y 2 agentes Gemini especializados (Agente 1: Backend Security Hunter; Agente 2: Frontend & Infra Security Hunter).

---

## 2. Resumen Ejecutivo de la Postura de Seguridad

La auditoría integral de la rama `develop` reveló que la plataforma posee una base arquitectónica moderna (Django REST Framework 3.15 + Vue 3 reactivo), con buenas prácticas iniciales de empaquetado y dependencias sin vulnerabilidades públicas (CVEs) en NPM.

Sin embargo, se identificaron **28 vulnerabilidades confirmadas**, incluyendo **1 vulnerabilidad Crítica** en la pasarela de pagos, **7 vulnerabilidades de Severidad Alta**, **9 de Severidad Media** y **11 de Severidad Baja**, además de **2 elementos que requieren validación de arquitectura de despliegue**.

### Vectores de Mayor Riesgo para el Negocio:
1. **Fraude Financiero y Bypass de Pasarela (CRITICAL):** El servicio de confirmación de Transbank captura cualquier excepción (`except Exception:`) y retorna incondicionalmente un voucher simulado como `status: AUTHORIZED`, permitiendo a cualquier usuario adquirir productos gratuitamente sin desembolso real.
2. **Denegación de Inventario y Concurrencia (HIGH):** Ausencia de validación de estado previo en la confirmación de Transbank que permite ataques de repetición (Replay) para vaciar inventarios, sumado a una condición de carrera sin bloqueo transaccional (`select_for_update`) que posibilita sobreventa bajo alta concurrencia.
3. **Exposición de Credenciales y Puerto de Base de Datos (HIGH):** Credenciales administrativas hardcodeadas en componentes Vue compilados en el bundle de producción (`AuthModal.vue`), y exposición irrestricta del puerto 5432 de PostgreSQL en `0.0.0.0` con contraseña por defecto en `docker-compose.yml`.
4. **Bypass de Sanitización por Estado en Expresiones Regulares (HIGH):** El uso de RegExp globales `/g` a nivel de módulo en utilitarios frontend causa retención de `lastIndex`, aprobando entradas maliciosas en llamadas consecutivas.
5. **Lógica de Carrito Manipulable (HIGH):** El botón de decremento en el carrito invoca `addItem(..., -1)` sin verificar cota inferior, permitiendo enviar cantidades negativas y corromper totales de pago.

---

## 3. Matriz Consolidada de Hallazgos Confirmados

| Severidad | Fingerprint | Límite Afectado | Resultado Observado |
|:---:|---|---|---|
| **CRITICAL** | `transbank.commit.unconditional-authorization-bypass` | `TransbankCommitAPIView.post` | El endpoint retorna HTTP 200 con mensaje "Pago aprobado exitosamente mediante Transbank Webpay Pl... |
| **HIGH** | `frontend.auth.hardcoded-admin-credentials-modal` | `template` | El formulario se autocompleta con 'admin@inacap.cl' y 'Admin1234!', permitiendo iniciar sesion co... |
| **HIGH** | `frontend.cart.negative-quantity-logic-flaw` | `cartStore.cartTotal` | La cantidad del producto pasa de 1 a 0 y luego a -1, deduciendo el valor del total del carrito. |
| **HIGH** | `frontend.security.regex-stateful-lastindex-bypass` | `isSafeInput` | La segunda invocacion devuelve true (aprobado), permitiendo el envio del payload malicioso al byp... |
| **HIGH** | `infra.docker.postgres-exposed-public-port` | `services.db.ports` | Conexion exitosa con privilegios de superusuario a la base de datos relacional de la aplicacion. |
| **HIGH** | `infra.env.hardcoded-jwt-secret-fallback` | `jwt.decode` | JWTAuthentication valida la firma HMAC y autentica la peticion como administrador. |
| **HIGH** | `transbank.commit.replay-inventory-depletion` | `TransbankCommitAPIView.post` | El stock del producto se descuenta en cada peticion repetida hasta llegar a 0, dejando el product... |
| **HIGH** | `transbank.concurrency.race-condition-stock-depletion` | `TransbankCommitAPIView.post` | Ambas solicitudes leen stock = 1 y escriben stock = 0, autorizando 2 unidades cuando solo existia... |
| **MEDIUM** | `auth.roles.admin-privilege-demotion-via-upgrade` | `UpgradeToSellerAPIView.post` | El rol del administrador es sobreescrito en base de datos a ROLE_SELLER, perdiendo acceso a endpo... |
| **MEDIUM** | `auth.roles.rbac-userrol-desynchronization` | `IsSellerOrAdmin.has_permission` | IsSellerOrAdmin retorna True porque UserRol permanece activo, permitiendo crear productos a un co... |
| **MEDIUM** | `auth.throttling.missing-rate-limiting-login-register` | `LoginAPIView.post` | Las 100 solicitudes son procesadas retornando 401 Unauthorized sin ninguna respuesta HTTP 429 Too... |
| **MEDIUM** | `catalog.products.unpaginated-resource-exhaustion` | `ProductListCreateView.get` | La respuesta devuelve todos los registros existentes sin paginar, consumiendo ancho de banda y me... |
| **MEDIUM** | `catalog.reviews.unrestricted-fraudulent-reviews` | `ProductReview.save` | El endpoint acepta todas las evaluaciones repetidas y recalcula dinamicamente el promedio del pro... |
| **MEDIUM** | `frontend.security.single-pass-xss-sanitization-bypass` | `sanitizeInput` | La cadena devuelta es '<script>alert(1)', conservando la estructura de etiqueta de script. |
| **MEDIUM** | `frontend.store.unvalidated-external-link-phishing` | `template` | El navegador abre directamente el sitio malicioso en una nueva pestana bajo la apariencia de resp... |
| **MEDIUM** | `infra.docker.insecure-django-runserver-production` | `services.backend.command` | El servidor de desarrollo monohilo/multiproc basico se bloquea o eleva su latencia a varios segun... |
| **MEDIUM** | `security.middleware.csp-wildcard-data-exfiltration` | `ISO27001SecurityHeadersMiddleware.__call__` | El navegador permite solicitudes fetch hacia cualquier dominio HTTPS externo debido al comodin ht... |
| **LOW** | `auth.jwt.missing-account-lock-verification` | `JWTAuthentication.authenticate` | El endpoint responde HTTP 200 OK autorizando la solicitud a pesar de que user.is_locked() es True. |
| **LOW** | `auth.registration.unhandled-integrity-user-enumeration` | `UserRegistrationSerializer.create` | El backend devuelve error HTTP 500 "Ha ocurrido un error interno de seguridad" debido a Integrity... |
| **LOW** | `catalog.store.unverified-official-store-badge-impersonation` | `RegisterStoreAPIView.post` | El perfil del vendedor queda marcado como Tienda Oficial autentica sin intervencion de ningun adm... |
| **LOW** | `frontend.auth.client-side-role-tampering` | `isAdmin` | La barra de navegacion muestra el boton de 'Panel de Administracion' y las rutas /admin son acces... |
| **LOW** | `frontend.dom.createobjecturl-memory-leak` | `handleImageUpload` | El uso de memoria del navegador incrementa continuamente sin ser reclamado por el recolector de b... |
| **LOW** | `frontend.pkg.permissive-semver-ranges` | `dependencies.vue` | npm descarga la version mas reciente dentro del rango de forma silenciosa. |
| **LOW** | `infra.docker.root-container-execution` | `CMD` | uid=0(root) gid=0(root) groups=0(root). |
| **LOW** | `infra.scripts.indiscriminate-process-termination` | `fuser -k` | El proceso ajeno es terminado abruptamente con SIGKILL sin permitir guardado seguro de transaccio... |
| **LOW** | `logging.middleware.crlf-log-injection-audit-spoofing` | `SecurityAuditLoggingMiddleware.__call__` | El logger registra dos lineas independientes, permitiendo falsificar eventos de auditoria ISO 27001. |
| **LOW** | `payments.cart.unhandled-value-error-dos` | `CartCalculateAPIView.post` | El backend devuelve HTTP 500 INTERNAL_SECURITY_ERROR ante datos de entrada invalidos en lugar de ... |
| **LOW** | `security.middleware.missing-hsts-permissions-policy-conflict` | `ISO27001SecurityHeadersMiddleware.__call__` | La respuesta carece de Strict-Transport-Security, posibilitando ataques de degradacion a texto pl... |

---

## 4. Elementos en Espera de Validación de Despliegue (`NEEDS VALIDATION`)

| Fingerprint | Título del Hallazgo | Límite de Arquitectura | Obstáculo / Verificación Pendiente |
|---|---|---|---|
| `auth.jwt.missing-server-side-revocation-denylist` | Ausencia de mecanismo de revocacion de tokens JWT en servidor (ventana de exposicion de 168 horas) | `backend/apps/accounts/authentication.py` | Requiere verificar si la arquitectura de produccion cuenta con un API Gateway (Kong, Cloudflare Workers, AWS API Gateway) que gestione revocacion de sesiones a nivel perimetral. |
| `settings.database.silent-sqlite-fallback-data-leakage` | Conmutacion silenciosa a base de datos SQLite local si PostgreSQL no responde en el arranque | `backend/config/settings.py` | Requiere validar si en el servidor productivo la variable DB_FALLBACK_SQLITE_IF_PG_UNAVAILABLE esta forzada a False en el entorno de despliegue. |

---

## 5. Hipótesis Refutadas y Falsos Positivos Descartados (`REJECTED`)

### `catalog.images.unvalidated-url-xss-via-existing-images`: Inyeccion de codigo XSS o ejecucion de scripts mediante URLs de imagenes en existing_images
- **Justificación de Descarte:** Al verificar la implementacion del frontend en Vue 3 y la politica de seguridad del navegador, se constata que las imagenes se insertan estrictamente en etiquetas <img :src="..."> sin usar innerHTML ni v-html. Los motores de renderizado web modernos bloquean la ejecucion de esquemas javascript: en atributos src de etiquetas de imagen. Asimismo, la cabecera Content-Security-Policy con script-src "self" impide la ejecucion de scripts no autorizados. Por tanto, no existe vector de ejecucion explotable y la hipotesis queda descartada.

---

## 6. Fortalezas de Seguridad Identificadas y Buenas Prácticas

1. **Hashing de Contraseñas Robusto:** Se utiliza el algoritmo estándar PBKDF2 con SHA-256 e iteraciones por defecto de Django en el modelo de usuario.
2. **Ausencia de directiva `v-html` en Vue 3:** Los componentes de la interfaz utilizan enlace reactivo estándar (`{{ }}`), mitigando el riesgo de inyección directa de código HTML en el cliente.
3. **Inyección de Cabeceras Anti-Clickjacking:** El middleware `ISO27001SecurityHeadersMiddleware` establece `X-Frame-Options: DENY` y `X-Content-Type-Options: nosniff` de forma consistente.
4. **Validación Estricta de Parámetros en Serializadores:** La mayoría de las mutaciones de datos emplean `serializers.Serializer` y `ModelSerializer` de DRF con validaciones tipadas.
5. **Ecosistema de Dependencias NPM Limpio:** Las librerías de producción empaquetadas en `package.json` no presentan vulnerabilidades conocidas (CVEs) en bases de datos públicas.

---

## 7. Resumen de Cobertura de Ledger (Fase 3)

- **Total de Unidades de Superficie Evaluadas:** 24
- **Unidades con Vulnerabilidades Identificadas (`candidate`):** 21
- **Unidades con Cobertura Limpia (`covered`):** 3
- **Olas Completadas:** 3 (Reconocimiento inicial, profundización estática, auditoría exhaustiva full-stack asistida por subagentes)
