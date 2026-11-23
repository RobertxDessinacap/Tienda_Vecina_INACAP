/**
 * Tienda Vecina Security & Anti-XSS Engine
 *
 * Implementación de defensas en profundidad:
 * 1. Sanitización iterativa en punto fijo contra payloads anidados y esquemas XSS.
 * 2. Preservación de puntuación comercial legítima ($, *, [, ], ;, (, ), %, etc.).
 * 3. Expresiones regulares sin estado (/g prohibido en .test()) y validación estricta HTTPS.
 */

// Patrones de scripts y esquemas peligrosos (sin /g para uso seguro en .test())
export const MALICIOUS_SCRIPT_PATTERNS =
  /(?:javascript\s*:|vbscript\s*:|data\s*:\s*text\/html|\bon\w+\s*=|<\s*(?:script|iframe|embed|object)\b)/i

const SAFE_ANGLE_CHECK = /[<>]/
const SAFE_SCRIPT_TAG_CHECK = /<\s*(?:script|iframe|embed|object)\b/i
const SAFE_SCHEME_OR_HANDLER_CHECK = /(?:javascript\s*:|vbscript\s*:|data\s*:\s*text\/html|\bon\w+\s*=)/i

/**
 * Elimina iterativamente etiquetas HTML, bloques <script>, ángulos < > y esquemas/handlers peligrosos
 * hasta alcanzar un punto fijo, evitando bypasses en una sola pasada sin bloquear puntuación comercial.
 * @param {string} input
 * @returns {string}
 */
function stripDangerousPatterns(input) {
  if (typeof input !== 'string') return ''
  let out = input
  let prev
  do {
    prev = out
    out = out
      .replace(/<\s*script\b[^>]*>[\s\S]*?<\s*\/\s*script\s*>/gi, '')
      .replace(/<[^>]*>/g, '')
      .replace(/[<>]/g, '')
      .replace(/(?:javascript\s*:|vbscript\s*:|data\s*:\s*text\/html|\bon\w+\s*=)/gi, '')
  } while (out !== prev)
  return out
}

/**
 * Sanitiza una cadena de texto eliminando cualquier etiqueta HTML o patrón XSS peligroso.
 * @param {string} input Texto sin procesar
 * @returns {string} Texto limpio y seguro
 */
export function sanitizeInput(input) {
  return stripDangerousPatterns(input).trim()
}

/**
 * Event Listener para `@input` o `@paste`:
 * Purga etiquetas HTML y esquemas/handlers peligrosos sin obstruir puntuación comercial.
 * @param {InputEvent | Event} event
 * @param {Function|null} updateCallback Callback opcional para sincronizar el modelo reactivo
 */
export function sanitizeEventInput(event, updateCallback = null) {
  const target = event?.target
  if (!target || typeof target.value !== 'string') return

  const cleaned = stripDangerousPatterns(target.value)
  if (target.value !== cleaned) {
    target.value = cleaned
    if (typeof updateCallback === 'function') {
      updateCallback(cleaned)
    }
  }
}

/**
 * Verifica de manera determinista (sin lastIndex stateful) si un texto está libre de patrones XSS.
 * @param {string} str
 * @returns {boolean} true si es seguro, false si contiene amenazas
 */
export function isSafeInput(str) {
  if (typeof str !== 'string') return true
  if (SAFE_ANGLE_CHECK.test(str)) return false
  if (SAFE_SCRIPT_TAG_CHECK.test(str)) return false
  if (SAFE_SCHEME_OR_HANDLER_CHECK.test(str)) return false
  return true
}

/**
 * Valida estrictamente que una URL use protocolo HTTPS válido.
 * @param {string} url
 * @returns {boolean}
 */
export function isValidHttpsUrl(url) {
  if (typeof url !== 'string') return false
  const trimmed = url.trim()
  if (!trimmed) return false
  try {
    const parsed = new URL(trimmed)
    return parsed.protocol === 'https:' && Boolean(parsed.hostname)
  } catch {
    return false
  }
}

/**
 * Pre-escala una imagen en HTML5 <canvas> a un máximo de maxWidth x maxHeight en JPEG
 * antes de enviarla al backend. Si falla el procesamiento en cliente, retorna el archivo original.
 * @param {File} file
 * @param {number} maxWidth
 * @param {number} maxHeight
 * @param {number} quality
 * @returns {Promise<File>}
 */
export function resizeImageBeforeUpload(file, maxWidth = 900, maxHeight = 600, quality = 0.85) {
  if (!(file instanceof Blob) || typeof document === 'undefined' || typeof Image === 'undefined') {
    return Promise.resolve(file)
  }

  return new Promise((resolve) => {
    let objectUrl = null
    try {
      objectUrl = URL.createObjectURL(file)
      const img = new Image()

      img.onload = () => {
        try {
          const origW = img.naturalWidth || img.width
          const origH = img.naturalHeight || img.height
          if (!origW || !origH) {
            resolve(file)
            return
          }

          const ratio = Math.min(maxWidth / origW, maxHeight / origH, 1)
          const targetW = Math.max(1, Math.round(origW * ratio))
          const targetH = Math.max(1, Math.round(origH * ratio))

          const canvas = document.createElement('canvas')
          canvas.width = targetW
          canvas.height = targetH
          const ctx = canvas.getContext('2d')
          if (!ctx) {
            resolve(file)
            return
          }

          ctx.fillStyle = '#ffffff'
          ctx.fillRect(0, 0, targetW, targetH)
          ctx.drawImage(img, 0, 0, targetW, targetH)

          canvas.toBlob(
            (blob) => {
              if (!blob) {
                resolve(file)
                return
              }
              const baseName = (file.name || 'producto').replace(/\.[^.]+$/, '')
              const resizedFile = new File([blob], `${baseName}.jpg`, {
                type: 'image/jpeg',
                lastModified: Date.now(),
              })
              resolve(resizedFile)
            },
            'image/jpeg',
            quality
          )
        } catch {
          resolve(file)
        } finally {
          if (objectUrl) URL.revokeObjectURL(objectUrl)
        }
      }

      img.onerror = () => {
        if (objectUrl) URL.revokeObjectURL(objectUrl)
        resolve(file)
      }

      img.src = objectUrl
    } catch {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
      resolve(file)
    }
  })
}
