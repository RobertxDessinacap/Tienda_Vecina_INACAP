# Tiena_Vecina_INACAP

Plataforma de comercio electrónico moderna, segura y de alto rendimiento diseñada con la estética limpia y amigable de MercadoLibre / Mercado Pago. Desarrollada con **Django** (PostgreSQL ORM) en el Backend y **Vue 3** (Vite + Tailwind CSS + Pinia) en el Frontend.

El proyecto incorpora una arquitectura de desacoplamiento de usuarios (`Userdjango` $\leftrightarrow$ `UserProfile` $\leftrightarrow$ `Persona` y `ROL -> UserRol`), procesamiento y blindaje de imágenes a 900x600 ($\le$ 1 MB), validador ADS de más de 250 caracteres, cálculo de carrito 100% en servidor (anti-manipulación JS), pasarela de pagos integrada con **Transbank Webpay Plus**, selector dinámico de ubicación de despacho para Chile, protección de doble capa contra ataques **XSS (Cross-Site Scripting)**, código limpio modular y aislamiento total de secretos en variables de entorno `.env`.

## Documentación Técnica
- [DOCUMENTACION_SISTEMA.md](DOCUMENTACION_SISTEMA.md): Documento técnico integral indexado (Instalación de frameworks y DB, Diagrama C4, Matriz de Endpoints REST, Clean Code, Arquitectura de identidades, reglas de negocio, blindaje de imágenes, prevención OWASP Anti-XSS y matriz de mitigaciones).
- [GUIA_TRANSBANK_WEBPAY.md](GUIA_TRANSBANK_WEBPAY.md): Guía paso a paso para programar e integrar la pasarela oficial Webpay Plus de Transbank.
- [example.env](example.env): Plantilla de configuración comentada exhaustivamente para replicación por IA o desarrolladores.
- [docker-compose.yml](docker-compose.yml): Orquestación multi-servicio para arranque instantáneo en contenedores (PostgreSQL 16 + Django 6 + Vue 3).

## 1. Guía de Instalación de Frameworks y Base de Datos

### A. Base de Datos: PostgreSQL (Versión 14+)

El sistema está diseñado para operar con PostgreSQL 16/17 en el puerto estándar `5432` con la base de datos `inacap_ecommerce`.

#### Instalación en Windows:
- **Opción 1 (Instalador Oficial EDB):** Descarga el instalador desde [PostgreSQL Windows Downloads](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads), ejecuta el asistente y define la contraseña `postgres`.
- **Opción 2 (Despliegue Portable sin Administrador):**
  ```powershell
  # Descargar binarios portables y extraer en una carpeta de usuario
  curl.exe -L -o postgres.zip "https://get.enterprisedb.com/postgresql/postgresql-16.8-1-windows-x64-binaries.zip"
  tar.exe -xf postgres.zip -C "C:\Users\<TuUsuario>\pgsql"
  # Inicializar cluster de datos
  & "C:\Users\<TuUsuario>\pgsql\pgsql\bin\initdb.exe" -D "C:\Users\<TuUsuario>\pgsql\data" -U postgres -E UTF8 --locale=C -A trust
  # Iniciar el motor en segundo plano
  & "C:\Users\<TuUsuario>\pgsql\pgsql\bin\postgres.exe" -D "C:\Users\<TuUsuario>\pgsql\data"
  ```
- **Opción 3 (Docker):**
  ```bash
  docker run --name inacap-postgres -e POSTGRES_DB=inacap_ecommerce -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16-alpine
  ```

#### Instalación en Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib libpq-dev
sudo systemctl enable --now postgresql
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres' SUPERUSER;"
sudo -u postgres createdb -O postgres inacap_ecommerce
```

#### Instalación en macOS (Homebrew):
```bash
brew install postgresql@16
brew services start postgresql@16
createuser -s postgres
createdb -O postgres inacap_ecommerce
```

> **Resiliencia Automática:** Si por alguna razón PostgreSQL no está activo al arrancar Django, la variable `DB_FALLBACK_SQLITE_IF_PG_UNAVAILABLE=True` conmuta de forma automática y transparente a SQLite local para que el entorno pueda probarse de inmediato sin fallar.

### B. Backend: Python & Django Framework

El backend es una API REST desacoplada desarrollada sobre **Django 6** y **Django REST Framework**.

1. **Instalar Python:** Descarga Python 3.11 o superior desde [python.org](https://www.python.org/) asegurándote de marcar *"Add Python to PATH"*.
2. **Preparar el Entorno Virtual:**
   ```bash
   cd backend
   python -m venv .venv

   # Activar entorno virtual
   # En Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # En Linux / macOS:
   source .venv/bin/activate
   ```
3. **Instalar Dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
   *Dependencias clave instaladas:*
   - `Django` & `djangorestframework`: Framework web y motor de API RESTful.
   - `psycopg` & `psycopg-binary`: Driver C moderno de PostgreSQL (psycopg 3).
   - `pillow`: Motor gráfico de verificación de magic bytes y normalización 900x600.
   - `transbank-sdk`: SDK oficial de pagos Webpay Plus para Chile.
   - `python-dotenv`: Carga aislada de variables desde `.env`.
   - `django-cors-headers`: Control de acceso y seguridad de red entre orígenes.

4. **Configurar Variables de Entorno (`.env`):**
   ```bash
   # En Windows:
   Copy-Item example.env .env
   # En Linux / macOS:
   cp example.env .env
   ```
5. **Ejecutar Migraciones y Poblado:**
   ```bash
   python manage.py migrate
   python manage.py seed_ecommerce
   python manage.py runserver 127.0.0.1:8000
   ```

### C. Frontend: Node.js & Vue 3 Framework

El frontend es una aplicación de página única (SPA) desarrollada sobre **Vue 3** y empaquetada con **Vite**.

1. **Instalar Node.js:** Descarga la versión LTS de Node.js (v18 o v20+) desde [nodejs.org](https://nodejs.org/).
2. **Entrar a la carpeta frontend e instalar dependencias:**
   ```bash
   cd frontend
   npm install
   ```
   *Dependencias clave instaladas:*
   - `vue` (v3.5): Framework reactivo con Composition API (`<script setup>`).
   - `pinia`: Gestión de estado global reactivo (auth, cart, products, location).
   - `tailwindcss` (v4): Sistema de diseño utilitario para la estética MercadoLibre.
   - `lucide-vue-next`: Biblioteca de íconos vectoriales SVG.
   - `axios`: Cliente HTTP con interceptores de autenticación JWT.
3. **Iniciar el Servidor de Desarrollo:**
   ```bash
   npm run dev
   ```
   El frontend abrirá en: **`http://localhost:5173`**.

## 2. Principios de Código Limpio (Clean Code) Aplicados

1. **Arquitectura Modular por Aplicaciones de Dominio (`apps/`):**
   El backend se divide en componentes independientes con una única responsabilidad (SRP):
   - `apps.accounts`: Identidad (`UserCredential`), perfiles (`UserProfile`), datos civiles (`Persona`) y roles (`Rol`, `UserRol`).
   - `apps.products`: Catálogo, categorías, serializadores de productos y motor de procesamiento de imágenes Pillow.
   - `apps.payments`: Órdenes inmutables, servicio de cálculo seguro de carrito y pasarela Transbank Webpay Plus.
   - `apps.security`: Middlewares de seguridad ISO 27001, auditoría y cabeceras HTTP.
2. **Separación Estricta de Capas (Backend REST $\leftrightarrow$ Frontend SPA):**
   - Cero plantillas HTML acopladas en Django. La comunicación es 100% mediante endpoints JSON tipados y documentados.
3. **Nomenclatura Semántica y Funciones Puras:**
   - Métodos y funciones con nombres autodescriptivos (`validate_xss_safe`, `process_and_secure_product_image`, `calculate_safe_cart_totals`).
4. **Principio DRY (Don't Repeat Yourself):**
   - Utilidades centralizadas en `utils/security.js` en frontend y `apps/products/utils.py` en backend.

## 3. Marco Integral de Seguridad (ISO 27001 & OWASP Top 10)

| Control / Pilar de Seguridad | Implementación en Inacap E-Commerce | Estándar Cumplido |
| :--- | :--- | :--- |
| **Aislamiento de Secretos** | Cero contraseñas o llaves en `settings.py`. 100% en `.env` (ignorado en `.gitignore`). Plantilla documentada `example.env`. | ISO 27001 A.8.9 |
| **Desacoplamiento de Identidades** | Jerarquía `Userdjango` $\leftrightarrow$ `UserProfile` $\leftrightarrow$ `Persona`. Los compradores nunca ven correos ni datos civiles, solo el alias público. | ISO 27001 A.8.2 |
| **Control de Acceso (RBAC)** | Roles explícitos `ROL -> UserRol`. Solo vendedores autorizados (`SELLER`) pueden publicar productos en el catálogo. | ISO 27001 A.8.2 |
| **Anti-Tampering en Carrito** | El cálculo del total se ejecuta 100% en el backend con el ORM de PostgreSQL. El cliente solo envía IDs y cantidades. Cero cálculo en JS. | OWASP A04:2021 |
| **Prevención Anti-XSS** | Bloqueo físico en inputs de caracteres `[`, `]`, `{`, `}`, `*`, `<`, `>`, `\`, `;`. Sanitización al pegar y validadores en serializadores. | OWASP A03:2021 |
| **Seguridad de Archivos Subidos** | Validación de extensión en lista blanca, inspección de magic bytes con Pillow, lienzo fijo 900x600 y compresión $\le 1$ MB. | OWASP A08:2021 |
| **Protección contra Inyección SQL** | Consultas 100% parametrizadas mediante el ORM de Django con driver `psycopg 3`. Cero SQL crudo concatenado. | OWASP A03:2021 |
| **Cabeceras HTTP de Servidor** | `Content-Security-Policy (CSP)`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`. | ISO 27001 A.8.26 |
| **Integridad Transaccional** | Transacciones ACID `@transaction.atomic` en pagos Transbank y descuento de stock en PostgreSQL. | Principio ACID |

### Auditoría de Cumplimiento y Análisis de Brechas (Gap Analysis)
- **¿Por qué cumple la aplicación a nivel de código?** El sistema implementa de forma nativa las mitigaciones de ingeniería de software para los 10 riesgos de **OWASP Top 10:2021** (Anti-SQLi, Anti-XSS, Anti-Tampering, RBAC, Criptografía PBKDF2/JWT) y los controles tecnológicos del **Anexo A de ISO/IEC 27001:2022** (A.5.15, A.8.2, A.8.5, A.8.9, A.8.15, A.8.24, A.8.26, A.8.28).
- **¿Qué falta para una certificación formal al 100% en producción?** A nivel organizacional y de infraestructura empresarial se requiere:
  1. *Gobernanza ISO 27001:* Política formal del SGSI aprobada por la alta dirección, matriz de riesgos (ISO 27005) y declaración de aplicabilidad (SoA).
  2. *Resiliencia Operativa:* Plan de Recuperación ante Desastres (DRP) y Continuidad del Negocio (BCP) con RTO/RPO probados.
  3. *Gestión de Claves:* Migrar secretos a un Módulo de Seguridad en Hardware (HSM) o Cloud KMS / Vault.
  4. *Infraestructura en Borde:* WAF de Capa 7 (Cloudflare / AWS WAF), Rate Limiting con cluster Redis y CAPTCHA adaptativo (Turnstile) en login.
  5. *Auditoría de Certificación:* Superar auditorías externas Fase 1 y 2 conducidas por un organismo acreditador internacional (BSI, AENOR, TÜV).
- *Consulta el desglose y justificación exhaustiva en:* [DOCUMENTACION_SISTEMA.md (Capítulo 14)](DOCUMENTACION_SISTEMA.md#sec-14-auditoria-cumplimiento).

## Cuentas de Acceso de Demostración

El comando `seed_ecommerce` deja precargadas 3 cuentas listas para probar las diferentes rolificaciones:

| Rol | Correo Electrónico | Contraseña | Permisos |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@inacap.cl` | `Admin1234!` | Control total, catálogo y gestión |
| **Vendedor** | `vendedor@inacap.cl` | `Vendedor1234!` | Publicación de productos con ADS (+250 car.), fotos e inventario |
| **Comprador** | `comprador@inacap.cl` | `Comprador1234!` | Exploración, carrito seguro y checkout Transbank |

> **Acceso Rápido:** Dentro de la ventana de inicio de sesión, puedes hacer clic en los botones de prueba rápida (*"Demo Vendedor"*, *"Demo Comprador"*, *"Demo Admin"*) para autocompletar credenciales al instante.

## Pruebas de Pago con Transbank Webpay Plus

Para simular una compra real mediante la pasarela oficial Webpay Plus:
1. Agrega cualquier producto al carrito de compras.
2. Abre el carrito y selecciona **Transbank Webpay Plus** en el carrusel de medios de pago.
3. Presiona **Continuar al Pago Seguro**.
4. En el entorno de integración oficial de Transbank, utiliza los datos de prueba:
   - **Tarjeta de Débito (Redcompra):** Cualquier número terminado en `6623` (ej: `6623`).
   - **Clave Webpay:** `1213`.
5. Al autorizarse el pago, el backend descontará el stock automáticamente en la base de datos PostgreSQL y emitirá el voucher oficial imprimible con código de autorización.

## Ejecución de Pruebas Automatizadas

El proyecto incluye pruebas unitarias que validan la arquitectura del docente y los estándares de seguridad:

```powershell
cd backend
python manage.py test apps.accounts apps.products apps.payments
```

**Cobertura de Pruebas (8/8 Exitosas sobre PostgreSQL):**
1. `test_user_profile_between_user_and_persona`: Validación del desacoplamiento `User` $\leftrightarrow$ `UserProfile` $\leftrightarrow$ `Persona`.
2. `test_seller_role_assignment`: Validación de asignación estricta de roles (`ROL -> UserRol`).
3. `test_caracteristicas_ads_min_length_validation`: Rechazo de especificaciones con $\le 250$ caracteres.
4. `test_seller_creates_product_with_valid_ads_and_clean_url`: Generación de URL limpia y exposición del nombre del vendedor.
5. `test_safe_cart_calculation_anti_tampering`: Verificación de cálculo inviolable de totales en el servidor.
6. `test_transbank_init_and_commit_flow`: Flujo de inicialización y confirmación de Webpay Plus.
7. `test_xss_payload_rejected_in_product_creation`: Detección y bloqueo de scripts y caracteres especiales prohibidos (`[`, `]`, `{`, `}`, `*`, `<`, `>`).
8. `test_search_endpoint_sanitizes_xss_and_brackets`: Sanitización segura de parámetros de búsqueda sin colapso.

## Compilación para Producción (Frontend)

Para generar el paquete optimizado de distribución:
```bash
cd frontend
npm run build
```
Los archivos estáticos optimizados se generarán en `frontend/dist/`.
