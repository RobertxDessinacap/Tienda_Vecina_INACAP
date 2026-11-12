# Reporte de Auditoría de Comprensión (Comprehension Test - Stage 6)

**Documento Auditado:** [`DOCUMENTACION_SISTEMA.md`](file:///home/misnull/Proyectos/inacap-ecommerce/DOCUMENTACION_SISTEMA.md)  
**Persona:** Naive Reader / Comprehension Goldfish (cero contexto histórico asumido, lectura estricta e independiente)

---

## High-Level Paraphrase

### What this proposes
El documento describe la arquitectura técnica y operacional de **Tienda Vecina**, una plataforma web de comercio electrónico inspirada en MercadoLibre. La solución propone una arquitectura desacoplada con frontend SPA en Vue 3 y backend RESTful en Django 6, persistencia transaccional en PostgreSQL 16 con fallback a SQLite local, e integración oficial con la pasarela bancaria chilena Transbank Webpay Plus. Establece un modelo estricto de identidad en tres capas (`UserCredential` $\rightarrow$ `UserProfile` $\rightarrow$ `Persona` con RBAC mediante `Rol` y `UserRol`), blindaje de seguridad en subida de imágenes (normalización forzosa a lienzo de 900x600 y compresión $\le 1$ MB), validaciones de contenido ADS mayores a 250 caracteres, cálculo de precios exclusivamente en servidor, filtrado anti-XSS de caracteres peligrosos y un informe de cumplimiento/brecha con ISO/IEC 27001:2022 y OWASP Top 10:2021.

### How the existing system works, per this document
De acuerdo con el documento, el sistema opera con dos servicios principales desacoplados: un cliente web SPA servido en el puerto 5173 y una API Django en el puerto 8000, respaldados por PostgreSQL en el puerto 5432. Los compradores exploran un catálogo de 14 categorías, seleccionan comunas de Chile y gestionan su carrito; al pagar, el backend consulta directamente la base de datos PostgreSQL para calcular precios reales de forma inviolable y delega el cobro al portal Webpay Plus de Transbank. Los vendedores autenticados gestionan sus publicaciones desde una vista privada, donde cada artículo requiere una imagen procesada por Pillow (verificación de magic bytes y límite anti-bomba de 10 MP) y una descripción técnica ADS extensa. Toda la configuración sensible reside en `.env`, las sentencias SQL están parametrizadas por el ORM con `psycopg 3`, y se inyectan cabeceras de seguridad HTTP en cada respuesta.

---

## Detailed Paraphrase

1. **Stack y Orquestación (Sección 1):** Define el stack tecnológico (Python 3.14, Django 6.1, DRF 3.16, Vue 3.5, Vite 8, PostgreSQL 16.8 con driver nativo `psycopg 3`, Pillow 12.1 y Transbank SDK 6.1). Proporciona un diagrama C4 Container, una tabla consolidada con 14 contratos de la API REST (autenticación, productos, pagos y tiendas oficiales) y comandos para levantar el ecosistema completo con Docker Compose (`docker compose up --build -d`).
2. **Modelo de Identidad y Roles (Sección 2):** Responde a un requerimiento docente separando las credenciales de autenticación (`UserCredential` o `Userdjango`, con PBKDF2 SHA-256) de los datos civiles del mundo real (`Persona`, que almacena RUT, nombres, apellidos, teléfono y dirección). Entre ambos sitúa a `UserProfile` como la entidad móvil que opera en el sistema (asociando ventas, órdenes y reputación), y gestiona permisos mediante las entidades `Rol` y la tabla intermedia `UserRol` (RBAC).
3. **Persistencia e Integración PostgreSQL (Sección 3):** Detalla el uso de PostgreSQL 16 vía `psycopg 3` en el puerto 5432 con claves primarias UUIDv4 nativas. Incorpora una función de sondeo TCP mediante sockets en `settings.py` que conmuta automáticamente a SQLite si PostgreSQL no está disponible. Documenta 18 tablas relacionales del esquema `public`, transacciones ACID con decorador `@transaction.atomic` y parametrización absoluta contra inyecciones SQL.
4. **Procesamiento Seguro de Imágenes (Sección 4):** Define una canalización para procesar fotos de productos: filtrado de extensiones, validación estructural de encabezados reales (magic bytes con `image.verify()`), defensa contra bombas de descompresión limitando imágenes a un máximo de 10 megapíxeles (`DecompressionBombError`), redimensionamiento con interpolación LANCZOS sobre un lienzo neutro de 900x600 px y compresión dinámica JPEG iterativa para asegurar un peso inferior o igual a 1 MB.
5. **Reglas de Publicación y URLs Limpias (Sección 5):** Exige un validador de longitud mínima de 251 caracteres en el campo `caracteristicas_ads`. Genera slugs semánticos para productos y expone el nombre del vendedor en la ficha pública citando normativas del SERNAC (Ley 19.496) mientras protege otros datos civiles. Describe el panel de gestión para vendedores ("Mis Publicaciones"), doble flujo de guardado en edición, inicialización de reseñas en cero para evitar falsedades y el registro opcional de "Tienda Oficial" con enlace clickeable.
6. **Seguridad en Carrito y Pagos Transbank (Secciones 6 y 7):** Prohíbe calcular totales en JavaScript en el navegador del cliente para prevenir manipulaciones. El cliente solo envía IDs y cantidades; el backend Django calcula montos reales desde la base de datos y orquesta el flujo de pago con Transbank Webpay Plus en dos etapas (`init` y `commit`), descontando stock de manera atómica al confirmarse la transacción bancaria.
7. **Taxonomía Territorial y Categorías (Sección 8):** Establece 14 categorías comerciales obligatorias (concluyendo con la categoría "Otros"). Detalla un selector modal de regiones y comunas de Chile conectado con la API de geolocalización del navegador y persistido en `localStorage` para calcular tiempos de despacho express.
8. **Blindaje Anti-XSS y Cabeceras HTTP (Sección 9):** Implementa una estrategia de defensa en profundidad contra Cross-Site Scripting basada en OWASP. En frontend, bloquea en tiempo real teclas y caracteres peligrosos (`[`, `]`, `{`, `}`, `*`, `<`, `>`, `\`, `;`, `^`, `$`, `~`, `|`, `` ` ``) mediante `security.js` y renderizado seguro con dobles llaves en Vue. En backend, sanitiza parámetros `?q=` con expresiones regulares y valida serializadores DRF. Inyecta cabeceras de protección (`CSP`, `nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`).
9. **Gestión de Secretos y Operación (Secciones 10, 11 y 12):** Explica el aislamiento de credenciales en `.env` (haciendo referencia a "ONV") mediante la plantilla documentada `example.env`. Detalla la batería de 8 pruebas unitarias automatizadas ejecutadas sobre PostgreSQL, el comando de compilación de Vite y los principios de código limpio (SRP, separación backend/frontend, DRY y nomenclatura semántica).
10. **Auditoría ISO 27001 y OWASP Top 10 (Secciones 13 y 14):** Desglosa la correspondencia técnica entre los controles implementados y las matrices de OWASP Top 10:2021 y controles del Anexo A de ISO/IEC 27001:2022. Concluye con un análisis de brecha (*Gap Analysis*) que especifica qué políticas organizacionales, auditorías externas, WAF, limitadores de tasa y bóvedas de claves en hardware (HSM/KMS) faltan para alcanzar una certificación formal corporativa.

---

## Undefined Acronyms & Jargon

1. **"ADS" (Sección 5, 5.1, 11, y tabla de API):** Se menciona repetidamente ("Características ADS (+250 Caracteres)", `caracteristicas_ads`), pero jamás se desglosa ni se explica su significado.
2. **"ONV" (Sección 10, título y texto):** Se titula *"Gestión de Secretos (.env / ONV)"* citando *"todo lo que tenga seguridad en ONV (.env)"*. No se aclara si es una errata tipográfica de pauta o una sigla con significado formal.
3. **"Userdjango" (Sección 2 y Diagrama C4):** Utilizado en citas y diagramas sin aclarar si es `auth_user`, una subclase o el modelo `accounts_usercredential`.
4. **"RUT" (Sección 2 y 3.4):** Se utiliza sin explicar que corresponde al *Rol Único Tributario* de Chile.
5. **"SERNAC" (Sección 5.3):** Se cita la Ley 19.496 y el SERNAC sin definirlo como el *Servicio Nacional del Consumidor* de Chile.
6. **"PII" (Diagrama C4 y Secciones 5.3, 13):** Aparece como sigla sin definir (*Personally Identifiable Information*).
7. **"ASVS" (Sección 14.4):** Mención de "OWASP ASVS Nivel 3" sin desglosar *Application Security Verification Standard*.
8. **"token_ws" (Secciones 1.3 y 7):** Parámetro de Webpay sin contextualizar la convención de Web Services de Transbank.

---

## Ambiguities & Mental Leap Gaps

1. **Falso Mecanismo de Reconexión en Caliente PostgreSQL $\leftrightarrow$ SQLite:** Se afirma que al iniciar PostgreSQL, Django se enlaza automáticamente a él sin reiniciar el proceso. En Django, `settings.py` se carga una única vez al boot. No existe enrutador dinámico en runtime.
2. **Verificación de Compra en Reseñas:** Se exige rol de comprador, pero no se valida si el usuario efectivamente compró y recibió el producto calificado, contradiciendo la premisa de "Cero Falsedad Comercial".
3. **Validación de URLs de Tiendas Oficiales:** No se especifica si `store_url` valida el protocolo `https://` para evitar ataques de redirección abierta o enlaces maliciosos.
4. **Falsos Positivos Anti-XSS en Productos Reales:** Prohibir `*`, `;`, `[`, `]` impide redactar descripciones de hardware técnico (dimensiones, especificaciones de memoria, listas separadas por punto y coma).

---

## Contradictions & Unclear Invariants

1. **Exposición de PII (`Persona.nombre_completo` vs ISO 27001):**
   - La Sección 5.2/5.3 indica que `Persona.nombre_completo` se muestra públicamente por exigencia del SERNAC.
   - Las Secciones 13 y 14.3 aseguran que los datos civiles de `Persona` están estrictamente aislados y jamás se exponen en el catálogo público, mostrándose solo el alias.
2. **Bloqueo de Geolocalización en Cabecera vs Selector de Comunas:**
   - La cabecera `Permissions-Policy: geolocation=()` desactiva de forma absoluta el acceso a la ubicación en el navegador.
   - La Sección 8.2 promete geolocalización automática del usuario mediante `navigator.geolocation`.
3. **Autenticación en Pasarela de Pago vs Propiedad de la Orden:**
   - La tabla 1.3 marca los endpoints de Transbank `init` y `commit` como `Pública`.
   - Las Secciones 2 y 14.2 garantizan que toda orden pertenece estrictamente a un `UserProfile` autenticado bajo RBAC.
4. **Universalidad Docker vs Rutas Hardcodeadas de Windows:**
   - Se promete despliegue homogéneo multiplataforma con Docker.
   - Se incluyen rutas absolutas de Windows (`C:\Users\Rober\...`) y scripts de PowerShell en múltiples secciones del documento.

---

## Hallazgos Clasificados por Prioridad

### 🔴 Blocker
1. **Invariante Contradictorio de Exposición de Identidad (SERNAC vs ISO 27001):** Definir inequívocamente si la ficha pública expone `Persona.nombre_completo` o `UserProfile.public_alias`.
2. **Incompatibilidad entre `Permissions-Policy` y Geolocalización:** Ajustar la cabecera a `geolocation=(self)` o declarar que la geolocalización del navegador no se utiliza.
3. **Ambigüedad de Autenticación en Checkout:** Aclarar si el checkout requiere autenticación obligatoria o soporte explícito de compra anónima (Guest).

### 🟡 Major
4. **Falsa Promesa de Reconexión en Caliente de Base de Datos:** Corregir la descripción de `settings.py` para reflejar que la conexión no conmuta dinámicamente en tiempo de ejecución.
5. **Definición de "ADS" y "ONV":** Definir explícitamente el significado de ambas siglas en el documento.
6. **Elegibilidad para Reseñas:** Documentar la regla de validación de compra previa para calificar un producto.
7. **Falsos Positivos en Filtro de Caracteres:** Revisar y flexibilizar el bloqueo de caracteres de puntuación estándar.
8. **Limpieza de Rutas Locales de Windows:** Remover referencias a `C:\Users\Rober\...` en favor de rutas relativas o variables de entorno estándar.

### 🟢 Nit
9. **Glosario de Siglas:** Incorporar desglose para RUT, SERNAC, PII y ASVS.
10. **Validación de Protocolo en Tiendas Oficiales:** Exigir `https://` en `store_url`.
11. **Nota sobre `token_ws`:** Documentar brevemente la convención de nombres de Transbank.
