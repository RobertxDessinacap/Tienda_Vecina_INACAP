# Registro de Elementos Pendientes de Validación (`NEEDS-VALIDATION.md`)

Este documento recopila las pistas y candidatos de vulnerabilidad que, debido a limitaciones de entorno local (*sandboxed source-and-local-only execution*), requieren comprobación directa sobre la infraestructura de despliegue en la nube, balanceadores de carga o pasarelas financieras de producción.

---

## 1. `auth.jwt.missing-server-side-revocation-denylist`: Ausencia de mecanismo de revocacion de tokens JWT en servidor (ventana de exposicion de 168 horas)

**Descripción:**  
Los tokens JWT generados en apps/accounts/authentication.py tienen una validez de 168 horas (7 dias segun settings.py). El servidor no mantiene una lista de revocacion (denylist/blacklist) ni valida numeros de version de credencial. Al cerrar sesion en el frontend, el token solo se elimina del almacenamiento local del cliente; si el token fue interceptado por un tercero, retiene validez completa en la API hasta su expiracion natural.

**Causa Raíz Planteada:**  
Falta de mecanismo de denylist en JWTAuthentication (apps/accounts/authentication.py:26-63) que verifique si el identificador o fecha del token fue revocado.

#### Traza de Código Fuente:
- `[ENTRYPOINT]` **`backend/apps/accounts/authentication.py:31`** (`JWTAuthentication.authenticate`): Se recibe un token JWT Bearer en la cabecera Authorization.
- `[PROPAGATION]` **`backend/apps/accounts/authentication.py:42`** (`JWTAuthentication.authenticate`): jwt.decode valida firma HMAC y fecha exp sin consultar lista de revocacion.
- `[SINK]` **`backend/apps/accounts/authentication.py:63`** (`JWTAuthentication.authenticate`): Se retorna la tupla (user, token) autorizando la solicitud a pesar de que el usuario haya cerrado sesion en su navegador.

#### Evidencia Verificada:
- **`backend/apps/accounts/authentication.py:42`**: jwt.decode valida la firma pero no verifica ningun identificador de token contra base de datos o cache de revocacion.

#### Obstáculos de Validación Local:
- Requiere verificar si la arquitectura de produccion cuenta con un API Gateway (Kong, Cloudflare Workers, AWS API Gateway) que gestione revocacion de sesiones a nivel perimetral.

#### Plan de Validación Recomendado:
- **Prueba Local Delimitada:** Obtener un token con login, ejecutar logout en frontend, y realizar una peticion curl a /api/v1/auth/me/ con el token para constatar que sigue respondiendo 200 OK.
- **Verificación en Despliegue de Producción:** Consultar al equipo de arquitectura cloud si existe un middleware de revocacion en API Gateway o si se planea implementar Redis denylist.

---

## 2. `settings.database.silent-sqlite-fallback-data-leakage`: Conmutacion silenciosa a base de datos SQLite local si PostgreSQL no responde en el arranque

**Descripción:**  
En backend/config/settings.py la funcion check_postgres_connection realiza un sondeo TCP al puerto de PostgreSQL. Si la conexion falla y la variable DB_FALLBACK_SQLITE_IF_PG_UNAVAILABLE esta en True, Django conmuta automaticamente el motor de persistencia a SQLite local (db.sqlite3). En entornos productivos con multiples contenedores efimeros o politicas de respaldo at-rest en PostgreSQL, esta conmutacion silenciosa causaria almacenamiento de datos en archivos planos locales sin replicacion ni auditoria.

**Causa Raíz Planteada:**  
Logica condicional de seleccion de base de datos en settings.py:105-126 que permite degradar PostgreSQL a SQLite si la conexion inicial no responde en menos de 1 segundo.

#### Traza de Código Fuente:
- `[ENTRYPOINT]` **`backend/config/settings.py:89`** (`check_postgres_connection`): La funcion sondea host y puerto de PostgreSQL con timeout de 1 segundo.
- `[PROPAGATION]` **`backend/config/settings.py:117`** (`DATABASES`): Si falla el sondeo y db_fallback es True, conmuta a django.db.backends.sqlite3.
- `[SINK]` **`backend/config/settings.py:121`** (`DATABASES`): Django inicializa el backend utilizando el archivo local db.sqlite3.

#### Evidencia Verificada:
- **`backend/config/settings.py:117`**: elif db_fallback: DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", ...}}

#### Obstáculos de Validación Local:
- Requiere validar si en el servidor productivo la variable DB_FALLBACK_SQLITE_IF_PG_UNAVAILABLE esta forzada a False en el entorno de despliegue.

#### Plan de Validación Recomendado:
- **Prueba Local Delimitada:** Configurar DB_PORT=9999 en .env local y verificar que manage.py inicia con SQLite imprimiendo mensaje de aviso en lugar de abortar.
- **Verificación en Despliegue de Producción:** Inspeccionar los archivos de configuracion de variables de entorno de produccion (Kubernetes ConfigMap, Docker Swarm o AWS Secrets) para confirmar que DB_FALLBACK_SQLITE_IF_PG_UNAVAILABLE sea False.

---
