# Critic Review Report (Stage 7): Feature Specification Audit

**Documento Auditado**: [`DOCUMENTACION_SISTEMA.md`](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md) (Secciones 1 a 10)  
**Revisores Especializados**:
- `egm-design`: Crítico de Diseño de Sistemas, Concurrencia, Modelos Transaccionales y Riesgos Operacionales.
- `egm-structural`: Validador Estructural, Jerarquía de Encabezados y Rutas de Enlaces.
- `egm-style`: Editor Técnico de Estilo, Calibración de Afirmaciones y Supresión de Lenguaje Inflado.

---

## 1. Resumen de la Evaluación Crítica

Las Secciones 1 a 10 presentan una disonancia marcada entre las declaraciones formales de alto nivel (garantías de alta disponibilidad, cumplimiento ISO 27001, transacciones ACID inviolables) y la realidad operativa del diseño:

1. **Riesgos Financieros Críticos**: La pasarela Transbank Webpay Plus autoaprueba pagos ante excepciones de red, y la confirmación no implementa aislamiento transaccional pesimista ni atómico, permitiendo sobreventas en compras concurrentes.
2. **Riesgo Operacional de Split-Brain**: Sondeo TCP por socket en `settings.py` que conmuta silenciosamente a SQLite local.
3. **Fallas de Concurrencia y Disponibilidad (DoS)**: Procesamiento síncrono intensivo de hasta 5 imágenes por producto en el hilo principal de Django, junto a un catálogo sin paginación que carga todos los modelos a memoria RAM.
4. **Usabilidad Comercial Rota por Falsas Defensas**: Bloqueo físico de teclado (`@keypress`) y filtros de serializadores que prohíben `$`, `*`, `[`, `]`, `{`, `}`, impidiendo describir productos reales.
5. **Deficiencias de Estructura y Estilo**: Contaminación con rutas absolutas de Windows (`file:///C:/Users/Rober/...`), afirmaciones no calibradas ("Protección Absoluta", "Django se enlaza automáticamente a PostgreSQL") y transcripciones de requerimientos académicos ("en ONV", citas del docente).

---

## 2. Hallazgos Críticos: Bloqueadores de Producción (🔴 Blocker)

### 🔴 Blocker 1: Auto-Aprobación Silenciosa ante Fallas y Modal Simulado de Transbank
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§7, §1.3, §6)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-7-pasarela-transbank), `services.py` (L108-L147), `views.py` (L120-L177), `PaymentCarouselModal.vue`.
- **Falla**: `commit_transaction` captura excepciones con `try/except` y retorna `status: 'AUTHORIZED'` con un código de autorización falso. En el frontend, un modal simulador reemplaza la redirección bancaria. Ante cortes de red o caídas de Transbank, el sistema regala productos y liquida stock sin recaudar dinero.
- **Remediación**:
  - Implementar principio **Fail-Closed**: toda excepción bancaria debe marcar la orden como `FAILED` o `REJECTED`.
  - Reemplazar el modal simulado por el flujo oficial: inicialización en backend -> redirección del navegador a Webpay -> confirmación vía callback en backend -> redirección 302 a página de resultado del frontend.

### 🔴 Blocker 2: Ausencia de Bloqueo Pesimista y Condiciones de Carrera en Stock
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§3.5, §7)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-3-5-transacciones-sqli), `views.py` (L127-L177).
- **Falla**: La documentación asegura el uso de `@transaction.atomic`, pero `TransbankCommitAPIView` carece del decorador y de bloqueos `select_for_update()`. Compras concurrentes causan sobreventa. Si el stock se agota antes del commit, la orden se cobra pero el stock no se descuenta ni se revierte el dinero.
- **Remediación**:
  - Decorar el commit con `@transaction.atomic`.
  - Bloquear filas de productos con `Product.objects.select_for_update()`.
  - Implementar anulación automática (`tx.refund()`) en Transbank si el inventario ya no puede satisfacerse.

### 🔴 Blocker 3: Riesgo de Split-Brain por Sondeo Dinámico a SQLite
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§3.3, §10)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-3-3-sondeo-puerto), `settings.py` (L89-L137).
- **Falla**: Se afirma que Django se enlaza automáticamente a PostgreSQL cuando este inicia. `settings.py` se evalúa una sola vez en el boot; si PostgreSQL tarda más de 1s, los workers de Gunicorn quedan divididos entre SQLite y PostgreSQL, generando estados de datos divergentes.
- **Remediación**:
  - Eliminar el sondeo de socket y el fallback a SQLite.
  - Aplicar **Fail-Fast**: el servicio debe fallar de inmediato si PostgreSQL no responde al iniciar.

### 🔴 Blocker 4: Inexistencia de Servidor Nginx y Medios Rotos en Producción
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§1.2, §1.4)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-1-2-diagrama-c4), `docker-compose.yml`, `urls.py`.
- **Falla**: No existe Nginx en el repositorio; se ejecuta `runserver` monohilo. Al establecer `DEBUG=False`, Django no sirve archivos en `MEDIA_URL`, haciendo que todas las fotos de productos subidas devuelvan `HTTP 404`.
- **Remediación**:
  - Configurar contenedor Nginx que sirva estáticos/medios y proxee la API hacia Gunicorn.
  - Declarar un volumen Docker persistente para `media/`.

### 🔴 Blocker 5: DoS por Procesamiento Sincrónico Bloqueante de Imágenes
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§4.1, §4.2)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-4-seguridad-imagenes), `utils.py` (L16-L76), `serializers.py`.
- **Falla**: Normalizar e iterar compresiones JPEG decrecientes de hasta 5 fotos en el hilo de Django tarda de 4 a 10 segundos de CPU, saturando todos los workers WSGI con pocas peticiones concurrentes.
- **Remediación**: Pre-escalar en frontend mediante Canvas API o delegar la compresión a tareas asíncronas en background; eliminar bucles de compresión iterativos.

### 🔴 Blocker 6: Catálogo Completo sin Paginación (Sobrecarga de Memoria)
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§1.3, §5)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md#sec-1-3-matriz-api), `views.py` (L37-L101).
- **Falla**: `GET /api/v1/products/` se documenta como paginado, pero en el código serializa todos los registros de la tabla sin límites (`limit`/`offset`), combinando escaneos secuenciales `ILIKE` en campos de texto extensos.
- **Remediación**: Implementar `PageNumberPagination` obligatoria (`page_size=20`) y optimizar búsquedas con índices de texto o trigramas.

### 🔴 Blocker 7: Contaminación de Rutas Absolutas de Windows y Comandos Host
- **Ámbito Afectado**: [`DOCUMENTACION_SISTEMA.md` (§3.2, §3.3, §3.6, §4, §5.2, §7, §8.2, §9.4, §9.6)](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md).
- **Falla**: 11 hipervínculos utilizan URIs locales de Windows (`file:///C:/Users/Rober/...`) e instrucciones de PowerShell con rutas de ejecutables de una máquina específica, rompiendo la portabilidad en Linux/macOS y Docker.
- **Remediación**: Sustituir todas las rutas absolutas por rutas relativas del repositorio y estandarizar comandos para entornos Linux y Docker.

---

## 3. Preocupaciones Mayores (🟡 Major)

1. **Bloqueo Naïve de Caracteres Comerciales (`$`, `*`, `[`, `]`, `;`)**: Se impide ingresar descripciones técnicas comunes bajo un argumento de seguridad innecesario (Vue 3 ya escapa texto plano en el DOM). Remediación: permitir caracteres estándar y centrar la validación en scripts HTML reales.
2. **Contradicción en Privacidad de Datos Civiles (SERNAC vs ISO 27001)**: La sección 5 expone `Persona.nombre_completo` en la ficha pública mientras que la sección 13 asegura que los datos civiles nunca se exponen. Remediación: exponer únicamente `UserProfile.public_alias` para personas naturales y reservar la razón social para tiendas oficiales.
3. **Reseñas Vulnerables a Sybil Attack**: El endpoint de reseñas no valida compra previa ni restringe múltiples reseñas del mismo usuario a un producto. Remediación: exigir orden previa pagada y unicidad `(product, user_profile)`.
4. **Doble Fuente de Verdad en Roles (RBAC)**: `UserCredential.role` y `UserRol` coexisten de forma redundante y pueden desincronizarse. Remediación: consolidar la verificación en una sola entidad.
5. **Incompatibilidad entre `Permissions-Policy` y Geolocalización**: `Permissions-Policy: geolocation=()` bloquea el selector de comunas del frontend. Remediación: cambiar a `geolocation=(self)` o documentar el selector como estrictamente manual.
6. **Inestabilidad de URLs Limpias (Slugs)**: Editar el título altera el slug, rompiendo enlaces compartidos e indexación previa (404). Remediación: slugs inmutables o sufijos deterministas con redirecciones 301.
7. **Asimetría de Encabezados y Desincronización con el Índice**: Secciones con encabezados no numerados (`###`) no registrados en el índice de contenidos.
8. **Citas a Enunciados Académicos y Alusiones a "Sesiones de IA"**: Citas del docente ("en ONV", "objeto que se mueve") y meta-instrucciones a modelos de lenguaje que restan rigor al documento formal.

---

## 4. Mejoras Menores (🟢 Nit)

1. **Corrección Léxica**: Sustituir la traducción errónea "fregaderos" por "sumideros del DOM" (*DOM sinks*).
2. **Discrepancia en Endpoints de Autenticación**: Sincronizar la documentación con el endpoint real `GET /api/v1/auth/me/`.
3. **Puntuación y Formato**: Estandarizar encabezados eliminando dos puntos finales (`:`) y reemplazar tablas de texto plano por tablas estándar Markdown GFM.
