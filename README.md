# Tienda Vecina

Plataforma de comercio electrónico con arquitectura desacoplada desarrollada con **Django** y **Django REST Framework** (ORM sobre PostgreSQL) en el Backend, **Vue 3** (Vite + Tailwind CSS + Pinia) en el Frontend y **Nginx + Gunicorn** para despliegue en contenedores.

El sistema implementa una arquitectura de identidad en tres capas (`UserCredential` $\leftrightarrow$ `UserProfile` $\leftrightarrow$ `Persona` y `Rol -> UserRol`), procesamiento y normalización de imágenes a 900x600 ($\le$ 1 MB), especificaciones técnicas detalladas (`caracteristicas_ads` $>$ 250 caracteres), cálculo de carrito 100% en servidor (anti-manipulación JS), integración *Fail-Closed* con **Transbank Webpay Plus**, selector territorial de comunas de Chile, protección anti-XSS con preservación de puntuación comercial, limitación de tasa (rate limiting) y gestión de secretos mediante variables de entorno `.env`.

## Documentación Técnica

- [DOCUMENTACION_SISTEMA.md](DOCUMENTACION_SISTEMA.md): Documento técnico integral indexado (Arquitectura C4 con Nginx/Gunicorn, Contratos API REST, Diccionario de 20 tablas, Transacciones ACID y conmutación Fail-Fast, Seguridad de imágenes, Prevención OWASP Anti-XSS, Cumplimiento ISO/IEC 27001 y Glosario).
- [GUIA_TRANSBANK_WEBPAY.md](GUIA_TRANSBANK_WEBPAY.md): Guía de integración *Fail-Closed* y redirección oficial con Transbank Webpay Plus.
- [example.env](example.env) / [.env.example](.env.example): Plantillas de configuración de entorno para despliegue seguro.
- [docker-compose.yml](docker-compose.yml): Orquestación multi-servicio para producción/staging (`PostgreSQL 16` + `Django/Gunicorn` + `Nginx` con volúmenes persistentes para datos y media).

## 1. Guía de Instalación y Despliegue

### A. Despliegue Recomendado con Docker Compose (Nginx + Gunicorn + PostgreSQL 16)

1. Copia la plantilla de entorno y genera secretos criptográficos únicos:
   ```bash
   cp .env.example backend/.env
   # Genera SECRET_KEY, JWT_SECRET_KEY independientes y DB_PASSWORD robusto:
   openssl rand -hex 32
   ```
2. Levanta los servicios (PostgreSQL queda aislado en red interna de Docker, Nginx sirve estáticos/media en puerto `80` y proxea `/api/` hacia Gunicorn):
   ```bash
   docker compose --env-file backend/.env up --build -d
   ```

> **Comportamiento Fail-Fast en Base de Datos:** El backend utiliza exclusivamente el motor definido en `DB_ENGINE` (por defecto `django.db.backends.postgresql`). No existe conmutación silenciosa automática a SQLite en tiempo de ejecución; si PostgreSQL no responde, la aplicación falla de forma explícita (*Fail-Fast*) para prevenir divergencia de datos (*split-brain*).

### B. Instalación Manual de Base de Datos: PostgreSQL (Versión 14+)

El sistema está diseñado para operar con PostgreSQL 16/17 en el puerto estándar `5432` con la base de datos `inacap_ecommerce`.

- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt update && sudo apt install -y postgresql postgresql-contrib libpq-dev
  sudo systemctl enable --now postgresql
  sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD '<tu_clave_segura>' SUPERUSER;"
  sudo -u postgres createdb -O postgres inacap_ecommerce
  ```
- **macOS (Homebrew):**
  ```bash
  brew install postgresql@16
  brew services start postgresql@16
  createuser -s postgres && createdb -O postgres inacap_ecommerce
  ```
- **Windows / Contenedor PostgreSQL local:**
  ```bash
  docker run --name inacap-postgres -e POSTGRES_DB=inacap_ecommerce -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=<tu_clave_segura> -p 127.0.0.1:5432:5432 -d postgres:16-alpine
  ```

### C. Backend: Python & Django Framework

1. **Preparar el entorno virtual e instalar dependencias:**
   ```bash
   cd backend
   python -m venv .venv
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   # Linux / macOS:      source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configurar variables de entorno (`backend/.env`):**
   ```bash
   cp example.env .env
   ```
   Edita `.env` definiendo `SECRET_KEY`, `JWT_SECRET_KEY` (distinta a `SECRET_KEY`), `DB_PASSWORD` y `DEBUG=True` solo en desarrollo local.
   *(Nota: Si desarrollas localmente sin PostgreSQL, puedes configurar explícitamente `DB_ENGINE=django.db.backends.sqlite3` en tu `.env` local).*
3. **Ejecutar migraciones e iniciar el servidor:**
   ```bash
   python manage.py migrate
   # En Linux/macOS con Gunicorn:
   gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 4
   # En desarrollo local Windows:
   python manage.py runserver 127.0.0.1:8000
   ```

### D. Frontend: Node.js & Vue 3 Framework

1. **Entrar a la carpeta frontend e instalar dependencias exactas desde el lockfile:**
   ```bash
   cd frontend
   npm ci
   ```
2. **Iniciar el servidor de desarrollo o compilar para producción:**
   ```bash
   # Desarrollo (http://localhost:5173)
   npm run dev
   # Compilación optimizada para producción (genera frontend/dist/)
   npm run build
   ```

## 2. Principios de Código Limpio (Clean Code) Aplicados

1. **Arquitectura Modular por Aplicaciones de Dominio (`apps/`):**
   - `apps.accounts`: Identidad (`UserCredential`), perfiles (`UserProfile`), datos civiles (`Persona`), roles (`Rol`, `UserRol`) y revocación de tokens (`RevokedToken`).
   - `apps.products`: Catálogo paginado, categorías, reseñas verificadas (`ProductReview`), validación de especificaciones ADS y procesamiento de imágenes Pillow.
   - `apps.payments`: Órdenes inmutables (`Order`, `OrderItem`), cálculo seguro de carrito y pasarela Transbank Webpay Plus *Fail-Closed*.
   - `apps.security`: Middlewares de cabeceras HTTP, CSP estricto, HSTS, auditoría sanitizada contra inyección CRLF y manejo seguro de excepciones.
2. **Separación Estricta de Capas (Backend REST $\leftrightarrow$ Frontend SPA):**
   - Comunicación mediante contratos JSON estructurados con códigos HTTP semánticos (`200`, `201`, `400`, `401`, `403`, `404`, `409`, `429`, `502`).
3. **Principio DRY (Don't Repeat Yourself):**
   - Utilidades compartidas en `frontend/src/utils/security.js`, `backend/apps/products/utils.py` y `backend/apps/payments/services.py`.

## 3. Marco Integral de Seguridad (ISO/IEC 27001 & OWASP Top 10)

| Control / Pilar de Seguridad | Implementación en Tienda Vecina | Estándar |
| :--- | :--- | :--- |
| **Aislamiento de Secretos** | Credenciales y llaves en `.env` (ignorado en `.gitignore`). `JWT_SECRET_KEY` obligatorio y segregado de `SECRET_KEY` cuando `DEBUG=False`. | ISO 27001 A.8.9 |
| **Privacidad de Identidades (PII)** | Desacoplamiento `UserCredential` $\leftrightarrow$ `UserProfile` $\leftrightarrow$ `Persona`. En catálogo C2C solo se expone `UserProfile.public_alias`; datos civiles reservados al perfil propio autenticado. | ISO 27001 A.8.3 |
| **Control de Acceso (RBAC) y Moderación** | `UserCredential.role` como fuente canónica sincronizada con `UserRol` en señales atómicas. Tiendas Oficiales requieren aprobación `ADMIN` y URLs `https://`. | ISO 27001 A.8.2 |
| **Autenticación, Bloqueo y Revocación** | Bloqueo temporal tras 5 intentos fallidos (`is_locked()` validado también en JWT), expiración de 24h, denylist de `jti` vía `POST /api/v1/auth/logout/` y rate limiting en login/registro. | OWASP A07:2021 |
| **Anti-Tampering y Pagos Fail-Closed** | Cálculo de precios en backend desde ORM. `TransbankWebpayService` falla cerrado ante errores (`FAILED`), `commit` protegido con `@transaction.atomic`, `select_for_update()` y reversa automática (`refund`) ante falta de stock. | OWASP A04:2021 |
| **Prevención Anti-XSS con Usabilidad** | Escape contextual automático de Vue 3 (`{{ }}`), sanitización iterativa en punto fijo contra etiquetas/scripts anidados, validación backend preservando puntuación comercial (`$`, `*`, `[`, `]`, `;`) y CSP estricto sin comodines `https:`. | OWASP A03:2021 |
| **Seguridad de Archivos Subidos** | Límite de subida cruda de 10 MB, pre-escalado `<canvas>` en cliente, lista blanca de extensiones, verificación de magic bytes y límite de 10 MP en Pillow, normalización 900x600 y JPEG $\le 1$ MB. | OWASP A08:2021 |
| **Protección contra Inyección SQL** | Consultas parametrizadas vía Django ORM (`psycopg 3`), sin concatenación de SQL crudo. | OWASP A03:2021 |
| **Cabeceras HTTP y Auditoría** | `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Permissions-Policy: geolocation=(self)` y logs sanitizados contra CRLF. | ISO 27001 A.8.15 / A.8.26 |

Consulte el análisis detallado de cumplimiento y brechas operacionales en [DOCUMENTACION_SISTEMA.md (Sección 14)](DOCUMENTACION_SISTEMA.md#sec-14-auditoria-cumplimiento).

## 4. Cuentas Iniciales y Semillero de Desarrollo

El código fuente de producción y los componentes de interfaz (`AuthModal.vue`) **no contienen credenciales de acceso ni botones de autocompletado demo**.

Para poblar categorías y datos iniciales en desarrollo local:
- Con `DEBUG=True`, puedes ejecutar manualmente:
  ```bash
  cd backend
  python manage.py seed_ecommerce
  ```
- Si `DEBUG=False`, el comando exige explícitamente definir las variables de entorno `SEED_ADMIN_PASSWORD`, `SEED_SELLER_PASSWORD` y `SEED_BUYER_PASSWORD`, fallando en caso contrario para impedir contraseñas predecibles en entornos productivos.
- También puedes registrar cuentas nuevas mediante `POST /api/v1/auth/register/` o desde la interfaz de registro.

## 5. Pagos con Transbank Webpay Plus

El flujo de checkout ejecuta la redirección oficial hacia el portal Webpay Plus de Transbank:
1. Agrega productos al carrito (el backend valida cantidades enteras positivas y calcula el total desde la base de datos).
2. Selecciona el medio de pago en el carrusel y presiona **Continuar**. El backend inicializa la transacción vía `POST /api/v1/payments/transbank/init/`.
3. El frontend envía el formulario `POST` oficial hacia la URL `https://` de Transbank con `token_ws`.
4. Al retornar desde Transbank a `/api/v1/payments/transbank/commit/`, el backend verifica la transacción bajo aislamiento `@transaction.atomic` + `select_for_update()` (Fail-Closed: cualquier fallo o rechazo marca la orden como `FAILED`, e inconsistencias concurrentes de stock disparan reversa `REVERSED`), redirigiendo al frontend con el comprobante o mensaje de error correspondiente.

## 6. Ejecución de Pruebas Automatizadas

El proyecto incluye **37 pruebas automatizadas** que cubren arquitectura, seguridad OWASP/ISO 27001, pagos Fail-Closed, concurrencia, RBAC, throttling, revocación JWT, paginación y procesamiento de imágenes:

```bash
cd backend
# Contra PostgreSQL configurado en .env:
python manage.py test apps.accounts apps.products apps.payments

# O usando SQLite en memoria explícitamente para pruebas locales sin servicio PostgreSQL:
TEST_USE_SQLITE=True python manage.py test apps.accounts apps.products apps.payments
```

Para validar la compilación de producción del frontend:

```bash
cd frontend
npm run build
```
