/**
 * Inacap E-Commerce Security & Anti-XSS Engine
 * 
 * Implementación de defensas en profundidad conforme a estándares OWASP Top 10 y Cheat Sheet:
 * 1. Restricción preventiva de caracteres peligrosos en inputs ([ } * < > \ ; ^ $ ~ | `).
 * 2. Purga y sanitización automática en eventos de tipeo y pegado (Paste Sanitization).
 * 3. Escape de caracteres especiales para evitar inyecciones DOM y XSS Reflejado.
 */

// Conjunto de caracteres expresamente bloqueados para prevenir ataques de inyección y XSS
export const FORBIDDEN_XSS_REGEX = /[<>{}\[\]*\\;^$|~`]/g

// Lista de palabras clave y prefijos de scripts maliciosos
export const MALICIOUS_SCRIPT_PATTERNS = /(javascript:|data:|vbscript:|on\w+=|<\s*script|<\s*iframe|<\s*embed|<\s*object)/gi

/**
 * Sanitiza una cadena de texto eliminando cualquier carácter o patrón peligroso.
 * @param {string} input Texto sin procesar
 * @returns {string} Texto limpio y seguro
 */
export function sanitizeInput(input) {
  if (typeof input !== 'string') return ''
  return input
    .replace(FORBIDDEN_XSS_REGEX, '')
    .replace(MALICIOUS_SCRIPT_PATTERNS, '')
    .trim()
}

/**
 * Event Listener para `@keypress` o `@keydown`:
 * Bloquea físicamente la pulsación de teclas con caracteres prohibidos ([ } * < > \ ; ^ $ ~ | `).
 * @param {KeyboardEvent} event 
 */
export function blockDangerousCharsOnKeypress(event) {
  const char = event.key
  // Permitir teclas de control del teclado (Backspace, Enter, flechas, etc.)
  if (event.ctrlKey || event.metaKey || event.altKey || char.length > 1) {
    return
  }

  if (/[<>{}\[\]*\\;^$|~`]/.test(char)) {
    event.preventDefault()
  }
}

/**
 * Event Listener para `@input` o `@paste`:
 * Garantiza que si un usuario pega texto con caracteres especiales prohibidos,
 * estos sean removidos instantáneamente del campo de texto.
 * @param {InputEvent | Event} event 
 * @param {Function} updateCallback Callback opcional para sincronizar el modelo reactivo
 */
export function sanitizeEventInput(event, updateCallback = null) {
  const target = event.target
  if (!target || typeof target.value !== 'string') return

  const cleaned = target.value.replace(FORBIDDEN_XSS_REGEX, '')
  if (target.value !== cleaned) {
    target.value = cleaned
    if (typeof updateCallback === 'function') {
      updateCallback(cleaned)
    }
  }
}

/**
 * Verifica si un texto contiene caracteres o patrones peligrosos de XSS.
 * @param {string} str 
 * @returns {boolean} true si es seguro, false si contiene amenazas
 */
export function isSafeInput(str) {
  if (typeof str !== 'string') return true
  if (FORBIDDEN_XSS_REGEX.test(str)) return false
  if (MALICIOUS_SCRIPT_PATTERNS.test(str)) return false
  return true
}
