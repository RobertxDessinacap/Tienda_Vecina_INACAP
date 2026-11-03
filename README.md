# Inacap E-Commerce 🛒🇨🇱

Plataforma de comercio electrónico moderna, segura y de alto rendimiento diseñada con la estética limpia y amigable de MercadoLibre / Mercado Pago. Desarrollada con **Django** (PostgreSQL ORM) en el Backend y **Vue 3** (Vite + Tailwind CSS + Pinia) en el Frontend.

El proyecto incorpora una arquitectura de desacoplamiento de usuarios (`Userdjango` $\leftrightarrow$ `UserProfile` $\leftrightarrow$ `Persona` y `ROL -> UserRol`), procesamiento y blindaje de imágenes a 900x600 ($\le$ 1 MB), validador ADS de más de 250 caracteres, cálculo de carrito 100% en servidor (anti-manipulación JS), pasarela de pagos integrada con **Transbank Webpay Plus**, selector dinámico de ubicación de despacho para Chile, protección de doble capa contra ataques **XSS (Cross-Site Scripting)** y aislamiento total de secretos en variables de entorno `.env`.

---

## 📑 Documentación Técnica
- 📖 [DOCUMENTACION_SISTEMA.md](DOCUMENTACION_SISTEMA.md): Documento técnico integral indexado (Arquitectura de identidades, reglas de negocio, blindaje de imágenes, prevención OWASP Anti-XSS y matriz de mitigaciones).
- 💳 [GUIA_TRANSBANK_WEBPAY.md](GUIA_TRANSBANK_WEBPAY.md): Guía paso a paso para programar e integrar la pasarela oficial Webpay Plus de Transbank.

---

## ⚙️ Requisitos Previos

Antes de comenzar, asegúrate de tener instalado en tu sistema:
- **Python 3.11+** (probado y compatible con Python 3.14).
- **Node.js 18+** y **npm 9+**.
- **PostgreSQL 14+** (Opcional: el sistema incluye un mecanismo de detección de puerto con fallback transparente a SQLite local para levantar inmediatamente sin configurar base de datos).
- **Git**.

---

## 🚀 Guía de Instalación y Puesta en Marcha

### 1. Clonar el Repositorio
```bash
git clone https://github.com/RobertxDessinacap/inacap-ecommerce.git
cd inacap-ecommerce
```

---

### 2. Puesta en Marcha del Backend (Django API)

Abre una terminal en la carpeta raíz del proyecto:

```powershell
# 1. Entrar a la carpeta backend
cd backend

# 2. Crear entorno virtual de Python
python -m venv .venv

# 3. Activar el entorno virtual
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Windows (CMD):
.venv\Scripts\activate.bat
# En Linux / macOS:
source .venv/bin/activate

# 4. Instalar dependencias requeridas
pip install -r requirements.txt

# 5. Crear archivo de entorno .env a partir de la plantilla example.env (o .env.example)
# En Windows (PowerShell):
Copy-Item example.env .env
# En Linux / macOS:
cp example.env .env

# 6. Ejecutar migraciones de base de datos
python manage.py migrate

# 7. Poblar datos iniciales (Roles, Cuentas Demo, Categorías y Productos)
python manage.py seed_ecommerce

# 8. Iniciar el servidor de desarrollo
python manage.py runserver 127.0.0.1:8000
```

> **Nota de Base de Datos:** Si tienes PostgreSQL activo en el puerto `5432` con la base de datos `inacap_ecommerce`, el sistema se conectará de inmediato a través de `psycopg 3`. Si no está disponible en tu máquina, el sistema activará de forma automática y transparente SQLite para que puedas probar todo sin trabas.

El Backend quedará escuchando en: **`http://127.0.0.1:8000/api/v1/`**

---

### 3. Puesta en Marcha del Frontend (Vue 3 + Vite)

Abre **otra terminal** (manteniendo el backend activo) en la carpeta raíz del proyecto:

```bash
# 1. Entrar a la carpeta frontend
cd frontend

# 2. Instalar dependencias de Node
npm install

# 3. Iniciar el servidor de desarrollo Vite
npm run dev
```

El Frontend se iniciará de inmediato en: **`http://localhost:5173`**

---

## 👥 Cuentas de Acceso de Demostración

El comando `seed_ecommerce` deja precargadas 3 cuentas listas para probar las diferentes rolificaciones:

| Rol | Correo Electrónico | Contraseña | Permisos |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@inacap.cl` | `Admin1234!` | Control total, catálogo y gestión |
| **Vendedor** | `vendedor@inacap.cl` | `Vendedor1234!` | Publicación de productos con ADS (+250 car.), fotos e inventario |
| **Comprador** | `comprador@inacap.cl` | `Comprador1234!` | Exploración, carrito seguro y checkout Transbank |

> **Acceso Rápido:** Dentro de la ventana de inicio de sesión, puedes hacer clic en los botones de prueba rápida (*"Demo Vendedor"*, *"Demo Comprador"*, *"Demo Admin"*) para autocompletar credenciales al instante.

---

## 💳 Pruebas de Pago con Transbank Webpay Plus

Para simular una compra real mediante la pasarela oficial Webpay Plus:
1. Agrega cualquier producto al carrito de compras.
2. Abre el carrito y selecciona **Transbank Webpay Plus** en el carrusel de medios de pago.
3. Presiona **Continuar al Pago Seguro**.
4. En el entorno de integración oficial de Transbank, utiliza los datos de prueba:
   - **Tarjeta de Débito (Redcompra):** Cualquier número terminado en `6623` (ej: `6623`).
   - **Clave Webpay:** `1213`.
5. Al autorizarse el pago, el backend descontará el stock automáticamente en la base de datos y emitirá el voucher oficial imprimible con código de autorización.

---

## 🧪 Ejecución de Pruebas Automatizadas

El proyecto incluye pruebas unitarias que validan la arquitectura del docente y los estándares de seguridad:

```powershell
cd backend
python manage.py test apps.accounts apps.products apps.payments
```

**Cobertura de Pruebas (8/8 Exitosas):**
1. `test_user_profile_between_user_and_persona`: Validación del desacoplamiento `User` $\leftrightarrow$ `UserProfile` $\leftrightarrow$ `Persona`.
2. `test_seller_role_assignment`: Validación de asignación estricta de roles (`ROL -> UserRol`).
3. `test_caracteristicas_ads_min_length_validation`: Rechazo de especificaciones con $\le 250$ caracteres.
4. `test_seller_creates_product_with_valid_ads_and_clean_url`: Generación de URL limpia y exposición del nombre del vendedor.
5. `test_safe_cart_calculation_anti_tampering`: Verificación de cálculo inviolable de totales en el servidor.
6. `test_transbank_init_and_commit_flow`: Flujo de inicialización y confirmación de Webpay Plus.
7. `test_xss_payload_rejected_in_product_creation`: Detección y bloqueo de scripts y caracteres especiales prohibidos (`[`, `]`, `{`, `}`, `*`, `<`, `>`).
8. `test_search_endpoint_sanitizes_xss_and_brackets`: Sanitización segura de parámetros de búsqueda sin colapso.

---

## 📦 Compilación para Producción (Frontend)

Para generar el paquete optimizado de distribución:
```bash
cd frontend
npm run build
```
Los archivos estáticos optimizados se generarán en `frontend/dist/`.

---

## 📄 Licencia
Proyecto desarrollado para fines académicos y de evaluación de comercio electrónico seguro bajo estándares ISO 27001 y OWASP Top 10.
