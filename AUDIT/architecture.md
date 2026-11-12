# Resumen de Arquitectura y Modelo de Confianza (Tienda Vecina / Inacap E-Commerce)

## 1. Producto, Principales y Recursos Protegidos
**Tienda Vecina** (proyecto `inacap-ecommerce`) es una plataforma web de comercio electrónico multivendedor con arquitectura desacoplada.

### Principales del Sistema
- **Comprador Anónimo (GUEST):** Navega por el catálogo de productos y categorías, calcula carritos de compras provisionales e inicializa transacciones de pago.
- **Comprador Autenticado (BUYER):** Titular de una cuenta vinculada a `UserCredential`, `UserProfile` y `Persona`. Puede realizar compras, visualizar su información de perfil y publicar evaluaciones de productos.
- **Vendedor Autorizado (SELLER):** Comprador ascendido que posee el rol `SELLER`. Autorizado para publicar nuevos productos en el catálogo, subir imágenes procesadas, editar sus publicaciones y registrar su Tienda Oficial.
- **Administrador (ADMIN):** Acceso al panel administrativo `/admin/`, auditoría y gestión global de catálogos y órdenes.

### Recursos Protegidos
- **Catálogo de Productos (`Product`):** Integridad de precios, inventario (`stock`) e imágenes.
- **Órdenes de Compra y Transacciones (`Order`, `OrderItem`):** Montos calculados exclusivamente en backend y conciliación bancaria con Transbank Webpay Plus.
- **Datos de Identidad (PII) y Credenciales (`Persona`, `UserCredential`, `UserProfile`):** Cifrado de claves (PBKDF2), segregación de roles y emisión de tokens JWT.

---

## 2. Línea Base y Comparativa de Software (E-Commerce B2C / C2C)
El sistema implementa patrones similares a marketplaces como MercadoLibre o Shopify:
- El desacoplamiento entre credenciales técnicas (`UserCredential`), identidad civil (`Persona`) y perfil público (`UserProfile`) permite proteger PII de compradores y vendedores.
- A diferencia de arquitecturas monolíticas con plantillas SSR, la API REST en Django interactúa con una SPA en Vue 3 mediante Bearer JWT.

---

## 3. Stack Tecnológico y Entorno de Ejecución Local
- **Backend:** Python 3.12+, Django 6.1.3, Django REST Framework 3.18.3, PostgreSQL (driver `psycopg` 3.3.8) con fallback local a SQLite.
- **Autenticación y Criptografía:** PyJWT 2.15.1 (HMAC-SHA256), `django.contrib.auth` (PBKDF2 SHA-256).
- **Procesamiento de Archivos:** Pillow 13.0.0 (normalización a 900x600, compresión dinámica <= 1 MB, límite de descompresión de 10 MP).
- **Pasarela de Pagos:** `transbank-sdk` 6.1.0 (Transbank Webpay Plus REST).
- **Frontend:** Vue 3.5.44, Vite 8.3.5, Pinia 4.1.0, Tailwind CSS 4, Axios 1.21.0.
- **Límites de Ejecución Offline:** Suite de tests Django (`apps.accounts`, `apps.products`, `apps.payments`) ejecutable localmente sin dependencias externas obligatorias.

---

## 4. Superficies de Entrada y Flujos Fuente-a-Sumidero (Source-to-Sink)
1. **Autenticación (`/api/v1/auth/`):**
   - Entrada: JSON con email, password, rut, full_name.
   - Sumidero: Creación de registros en `UserCredential`, `UserProfile`, `Persona` y emisión de token JWT.
2. **Catálogo y Productos (`/api/v1/products/`):**
   - Entrada: Parámetros de consulta (`q`, `category`, `min_price`, `max_price`) y payloads multipart/form-data con metadatos e imágenes.
   - Sumidero: Consultas ORM parametrizadas y almacenamiento en disco bajo `media/productos/`.
3. **Evaluaciones (`/api/v1/products/:lookup/reviews/`):**
   - Entrada: JSON con calificación (1-5) y comentario.
   - Sumidero: Modelo `ProductReview` con recálculo dinámico de `rating` del producto en base de datos.
4. **Cálculo y Pagos (`/api/v1/payments/`):**
   - Entrada: Lista de IDs de productos y cantidades enviadas desde el carrito.
   - Sumidero: Cálculo de totales forzado en servidor desde la base de datos (anti-manipulación JS) y generación de órdenes de compra.
   - Confirmación: Recepción de token de Transbank para autorización bancaria y descuento de stock.

---

## 5. Límites de Confianza y Controles Visibles
| Frontera de Confianza | Control Principal Visible en Código Fuente | Efectividad Observada |
| :--- | :--- | :--- |
| **Cliente JS -> Cálculo de Precios** | `calculate_safe_cart_totals()` extrae precios directamente de la base de datos PostgreSQL ignorando el frontend | **Alta**: Previene manipulación de precios desde el cliente. |
| **Cliente -> Subida de Imágenes** | `process_and_secure_product_image()` verifica magic bytes, re-codifica a RGB JPEG y descarta metadatos | **Alta**: Bloquea web shells y polyglots maliciosos. |
| **Cliente -> Cabeceras HTTP** | `ISO27001SecurityHeadersMiddleware` inyecta CSP, nosniff, DENY | **Alta**: Mitiga framing y MIME sniffing. |
| **Transbank -> Autorización** | `TransbankWebpayService.commit_transaction` captura excepciones y retorna mock AUTHORIZED | **CRÍTICA**: Falla de contención que permite bypass de pago total. |
| **Cliente -> Paginación de Catálogo** | `ProductListCreateView` serializa el queryset total sin paginar | **Media**: Ausencia de límite en API pública. |

---

## 6. Selección de Compañeros de Ataque (Companion Selection)
Conforme a [ATTACK-CLASSES.md](ATTACK-CLASSES.md):
- **`WEB-PROTOCOL-AND-AUTH.md`:** Seleccionado por la existencia de autenticación JWT y comunicación REST.
- **`CLIENT-SIDE.md`:** Seleccionado por la aplicación SPA Vue 3, manejo de almacenamiento en `localStorage` y renderizado dinámico de productos.
- **`MEMORY-SAFETY-AND-BINARY.md`:** Excluido con justificación: la aplicación se ejecuta sobre el intérprete gestionado de Python y navegador web, sin extensiones C/C++ ni parsers binarios en código de aplicación.
