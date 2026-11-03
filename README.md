# Inacap E-Commerce (Django + PostgreSQL + Vue 3)

Plataforma de comercio electrónico de alta seguridad desarrollada bajo estándares de programación segura y controles **ISO/IEC 27001**, con arquitectura desacoplada y estética visual inspirada en **MercadoLibre**.

---

## 🚀 Arquitectura Tecnológica

- **Backend:** Django 6 con Django REST Framework (DRF) y `django-cors-headers`.
- **Base de Datos:** PostgreSQL con ORM Django (driver nativo de alto rendimiento `psycopg 3`).
- **Frontend:** Vue 3 (Composition API `<script setup>`), Vite 8, Pinia, Tailwind CSS y Lucide Icons.
- **Seguridad ISO 27001:**
  - **Patrón de Cuenta Intermedia (Intermediate Account / Surrogate Identity):** Las publicaciones de productos y compras se asocian exclusivamente a un `AccountProxy` público con seudónimo, garantizando la disociación completa de las credenciales confidenciales del usuario (`UserCredential`) y datos sensibles (`UserProfileSensitive`).
  - **Rolificación (RBAC):** Roles granulares (`ADMIN`, `SELLER`, `BUYER`). Solo `SELLER` y `ADMIN` pueden publicar productos.
  - **Blindaje de Secretos:** 100% de la configuración y claves residen en `.env` (ignorado en Git mediante `.gitignore`).
  - **Cabeceras de Seguridad:** CSP, X-Frame-Options DENY, X-Content-Type nosniff y logging de auditoría.

---

## 👥 Cuentas de Demostración Preconfiguradas

| Rol | Correo Electrónico | Contraseña | Cuenta Intermedia (Alias Público) | Permisos |
| :--- | :--- | :--- | :--- | :--- |
| **Vendedor** | `vendedor@inacap.cl` | `Vendedor1234!` | `TechChile_Plaza` | Ver catálogo + Publicar productos |
| **Comprador** | `comprador@inacap.cl` | `Comprador1234!` | `Cliente_Estudiante_Inacap` | Ver catálogo + Comprar + Perfil |
| **Administrador** | `admin@inacap.cl` | `Admin1234!` | `Inacap_Oficial_Store` | Control total + Publicar + Auditoría |

> *Nota:* En la ventana de inicio de sesión del frontend se incluyen botones de llenado rápido de 1 clic para alternar entre roles instantáneamente.

---

## 🛠️ Puesta en Marcha

### 1. Iniciar el Backend (Django)

```powershell
cd "C:\Users\Rober\inacap e-commerce\backend"

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# (Opcional) Ejecutar tests de seguridad y autorización
python manage.py test apps.accounts apps.products

# Iniciar servidor backend en el puerto 8000
python manage.py runserver 127.0.0.1:8000
```

El backend quedará escuchando en `http://127.0.0.1:8000`.

### 2. Iniciar el Frontend (Vue 3 + Vite)

En una nueva terminal:

```powershell
cd "C:\Users\Rober\inacap e-commerce\frontend"

# Iniciar servidor de desarrollo Vite
npm run dev
```

Abre en tu navegador: **`http://localhost:5173`**

---

## 🐘 Conexión con PostgreSQL

El archivo `backend/.env` viene preparado para conectarse a tu instancia local de PostgreSQL:

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=inacap_ecommerce
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
```

- Si tu servicio PostgreSQL local está activo en el puerto `5432`, Django se conectará automáticamente mediante el driver `psycopg`.
- Si el servicio no está corriendo aún en tu máquina, Django activa un fallback transparente para que puedas desarrollar y probar la interfaz sin interrupciones.
- Para aplicar migraciones en tu PostgreSQL una vez iniciado el servicio:
  ```powershell
  python manage.py migrate
  python manage.py seed_ecommerce
  ```

---

## 🔒 Control de Versiones Git

El proyecto ha sido inicializado con Git (`git init`) y cuenta con un `.gitignore` integral que excluye:
- `.env` y archivos con credenciales o claves privadas.
- `.venv/` y directorios de entorno virtual de Python.
- `node_modules/` y artefactos de compilación `dist/`.
- Archivos temporales de caché `__pycache__` y bases de datos locales.
