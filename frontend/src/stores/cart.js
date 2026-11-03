import { defineStore } from 'pinia'
import apiClient from '../services/api'

export const useCartStore = defineStore('cart', {
  state: () => {
    let saved = []
    try {
      saved = JSON.parse(localStorage.getItem('inacap_cart_items') || '[]')
    } catch {
      saved = []
    }

    return {
      items: saved,
      cartDrawerOpen: false,
      paymentModalOpen: false,
      selectedPaymentMethod: 'WEBPAY_PLUS',
      calculating: false,
      backendCalculation: null,
      transbankData: null,
      paymentVoucher: null,
      paymentLoading: false,
      paymentError: null,
    }
  },

  getters: {
    totalItemsCount: (state) => state.items.reduce((acc, it) => acc + (it.quantity || 1), 0),
    hasItems: (state) => state.items.length > 0,
  },

  actions: {
    persist() {
      localStorage.setItem('inacap_cart_items', JSON.stringify(this.items))
    },

    addItem(product, quantity = 1) {
      const existing = this.items.find((it) => it.product.id === product.id)
      if (existing) {
        existing.quantity += quantity
      } else {
        this.items.push({
          product,
          quantity,
        })
      }
      this.persist()
      this.backendCalculation = null // Invalida cálculo previo para forzar cálculo en Backend
      this.openCart()
    },

    removeItem(productId) {
      this.items = this.items.filter((it) => it.product.id !== productId)
      this.persist()
      this.backendCalculation = null
      if (this.items.length > 0) {
        this.calculateSafeTotal()
      }
    },

    updateQuantity(productId, delta) {
      const item = this.items.find((it) => it.product.id === productId)
      if (item) {
        item.quantity += delta
        if (item.quantity <= 0) {
          this.removeItem(productId)
        } else {
          this.persist()
          this.backendCalculation = null
          this.calculateSafeTotal()
        }
      }
    },

    clearCart() {
      this.items = []
      this.backendCalculation = null
      this.persist()
    },

    openCart() {
      this.cartDrawerOpen = true
      this.calculateSafeTotal()
    },

    closeCart() {
      this.cartDrawerOpen = false
    },

    openPaymentModal() {
      this.cartDrawerOpen = false
      this.paymentModalOpen = true
      this.paymentError = null
      this.paymentVoucher = null
    },

    closePaymentModal() {
      this.paymentModalOpen = false
      this.transbankData = null
      this.paymentError = null
    },

    /**
     * Seguridad Crítica (Requisito del Profesor):
     * 'Los procesos donde tenga información delicada no deben estar generadas,
     * calculadas o analizadas por JS, problema de seguridad'.
     * Llama al Backend Django para que valide stock y compute precios reales desde la DB.
     */
    async calculateSafeTotal() {
      if (this.items.length === 0) {
        this.backendCalculation = null
        return
      }

      this.calculating = true
      try {
        const payload = {
          items: this.items.map((it) => ({
            product_id: it.product.id,
            quantity: it.quantity,
          })),
        }
        const response = await apiClient.post('/payments/cart/calculate/', payload)
        this.backendCalculation = response.data.data
      } catch (err) {
        console.error('Error calculando carrito en backend:', err)
      } finally {
        this.calculating = false
      }
    },

    /**
     * Paso 1 Transbank Webpay Plus: Inicialización de la transacción
     */
    async initPayment(paymentMethod = 'WEBPAY_PLUS') {
      this.selectedPaymentMethod = paymentMethod
      this.paymentLoading = true
      this.paymentError = null
      try {
        const payload = {
          items: this.items.map((it) => ({
            product_id: it.product.id,
            quantity: it.quantity,
          })),
          payment_method: paymentMethod,
        }
        const response = await apiClient.post('/payments/transbank/init/', payload)
        this.transbankData = response.data.data
        return { success: true, data: this.transbankData }
      } catch (err) {
        const msg = err.response?.data?.message || 'Error al iniciar transacción con Transbank.'
        this.paymentError = msg
        return { success: false, error: msg }
      } finally {
        this.paymentLoading = false
      }
    },

    /**
     * Paso 2 Transbank Webpay Plus: Confirmación (Commit) de la transacción
     */
    async commitPayment() {
      if (!this.transbankData?.token) return

      this.paymentLoading = true
      this.paymentError = null
      try {
        const response = await apiClient.post('/payments/transbank/commit/', {
          token: this.transbankData.token,
        })
        this.paymentVoucher = response.data.voucher
        this.clearCart() // Vacia el carrito tras el pago exitoso
        return { success: true, voucher: this.paymentVoucher }
      } catch (err) {
        const msg = err.response?.data?.message || 'La transacción no pudo ser autorizada por Transbank.'
        this.paymentError = msg
        return { success: false, error: msg }
      } finally {
        this.paymentLoading = false
      }
    },
  },
})
