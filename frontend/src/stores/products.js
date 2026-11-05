import { defineStore } from 'pinia'
import apiClient from '../services/api'

export const useProductStore = defineStore('products', {
  state: () => ({
    products: [],
    myProducts: [],
    categories: [],
    selectedProduct: null,
    editingProduct: null,
    reviewingProduct: null,
    detailModalOpen: false,
    createModalOpen: false,
    editModalOpen: false,
    filterModalOpen: false,
    registerStoreModalOpen: false,
    reviewModalOpen: false,
    loading: false,
    myProductsLoading: false,
    error: null,
    activeCategory: null,
    searchQuery: '',
    ordering: '-created_at',
    minPrice: null,
    maxPrice: null,
    onlyFreeShipping: false,
    priceBounds: {
      min: 30000,
      max: 2100000,
    },
    activeView: 'catalog', // 'catalog' | 'product_page' | 'my_products'
    activeProductSlug: null,
  }),

  getters: {
    hasActiveFilters(state) {
      return (
        state.minPrice !== null ||
        state.maxPrice !== null ||
        state.onlyFreeShipping ||
        state.activeCategory !== null ||
        (state.searchQuery && state.searchQuery.trim().length > 0)
      )
    },
    activeFiltersCount(state) {
      let count = 0
      if (state.minPrice !== null || state.maxPrice !== null) count++
      if (state.onlyFreeShipping) count++
      if (state.activeCategory !== null) count++
      if (state.searchQuery && state.searchQuery.trim().length > 0) count++
      return count
    },
  },

  actions: {
    async fetchCategories() {
      try {
        const response = await apiClient.get('/products/categories/')
        this.categories = response.data.data || []
      } catch (err) {
        console.error('Error cargando categorías:', err)
      }
    },

    async fetchProducts() {
      this.loading = true
      this.error = null
      try {
        const params = {}
        if (this.searchQuery && this.searchQuery.trim()) {
          params.q = this.searchQuery.trim()
        }
        if (this.activeCategory) {
          params.category = this.activeCategory
        }
        if (this.ordering) {
          params.ordering = this.ordering
        }
        if (this.minPrice !== null && this.minPrice !== undefined && this.minPrice !== '') {
          params.min_price = this.minPrice
        }
        if (this.maxPrice !== null && this.maxPrice !== undefined && this.maxPrice !== '') {
          params.max_price = this.maxPrice
        }
        if (this.onlyFreeShipping) {
          params.free_shipping = true
        }

        const response = await apiClient.get('/products/', { params })
        this.products = response.data.data || []

        if (response.data.price_bounds) {
          this.priceBounds = {
            min: Math.floor(response.data.price_bounds.min || 0),
            max: Math.ceil(response.data.price_bounds.max || 2500000),
          }
        }
      } catch (err) {
        this.error = 'No se pudieron cargar los productos del catálogo.'
        console.error('Error cargando productos:', err)
      } finally {
        this.loading = false
      }
    },

    async fetchProductBySlug(slug) {
      this.loading = true
      try {
        const response = await apiClient.get(`/products/${slug}/`)
        const prod = response.data.data
        this.selectedProduct = prod
        this.activeProductSlug = slug
        this.activeView = 'product_page'
        // Push URL limpia en la barra de direcciones del navegador
        window.history.pushState({}, '', `/producto/${slug}`)
        return prod
      } catch (err) {
        console.error('Error obteniendo producto por URL limpia:', err)
        return null
      } finally {
        this.loading = false
      }
    },

    goToCatalog() {
      this.activeView = 'catalog'
      this.selectedProduct = null
      this.activeProductSlug = null
      window.history.pushState({}, '', '/')
      this.fetchProducts()
    },

    setSearch(query) {
      this.searchQuery = query
      if (this.activeView !== 'catalog') {
        this.activeView = 'catalog'
        window.history.pushState({}, '', '/')
      }
      this.fetchProducts()
    },

    setCategory(categorySlug) {
      this.activeCategory = this.activeCategory === categorySlug ? null : categorySlug
      if (this.activeView !== 'catalog') {
        this.activeView = 'catalog'
        window.history.pushState({}, '', '/')
      }
      this.fetchProducts()
    },

    setOrdering(sortOrder) {
      this.ordering = sortOrder
      this.fetchProducts()
    },

    openDetail(product) {
      this.fetchProductBySlug(product.slug)
    },

    openCreateModal() {
      this.createModalOpen = true
    },

    closeCreateModal() {
      this.createModalOpen = false
    },

    openFilterModal() {
      this.filterModalOpen = true
    },

    closeFilterModal() {
      this.filterModalOpen = false
    },

    applyFilters({ minPrice, maxPrice, onlyFreeShipping, category, searchQuery }) {
      this.minPrice = minPrice !== undefined ? minPrice : this.minPrice
      this.maxPrice = maxPrice !== undefined ? maxPrice : this.maxPrice
      this.onlyFreeShipping = onlyFreeShipping !== undefined ? onlyFreeShipping : this.onlyFreeShipping
      if (category !== undefined) {
        this.activeCategory = category
      }
      if (searchQuery !== undefined) {
        this.searchQuery = searchQuery
      }
      this.filterModalOpen = false
      this.fetchProducts()
    },

    clearAllFilters() {
      this.minPrice = null
      this.maxPrice = null
      this.onlyFreeShipping = false
      this.activeCategory = null
      this.searchQuery = ''
      this.fetchProducts()
    },

    async createProduct(formDataOrJson) {
      this.loading = true
      try {
        const isFormData = formDataOrJson instanceof FormData
        const headers = isFormData ? { 'Content-Type': 'multipart/form-data' } : {}

        const response = await apiClient.post('/products/', formDataOrJson, { headers })
        const newProduct = response.data.data
        this.products.unshift(newProduct)
        this.closeCreateModal()
        return { success: true, product: newProduct }
      } catch (err) {
        let msg = 'Error al publicar el producto.'
        if (err.response?.data?.errors) {
          const errors = err.response.data.errors
          const firstKey = Object.keys(errors)[0]
          if (firstKey && Array.isArray(errors[firstKey])) {
            msg = `${firstKey}: ${errors[firstKey][0]}`
          } else if (typeof errors === 'string') {
            msg = errors
          }
        }
        return { success: false, error: msg }
      } finally {
        this.loading = false
      }
    },

    // ===== VISTA ÚNICA DE VENDEDOR (MIS PUBLICACIONES) =====
    async fetchMyProducts() {
      this.myProductsLoading = true
      try {
        const response = await apiClient.get('/products/my-products/')
        this.myProducts = response.data.data || []
      } catch (err) {
        console.error('Error cargando mis publicaciones:', err)
      } finally {
        this.myProductsLoading = false
      }
    },

    goToMyProducts() {
      this.activeView = 'my_products'
      this.selectedProduct = null
      this.activeProductSlug = null
      window.history.pushState({}, '', '/mis-publicaciones')
      this.fetchMyProducts()
    },

    // ===== MODAL DE EDICIÓN DE PRODUCTO =====
    openEditModal(product) {
      this.editingProduct = { ...product }
      this.editModalOpen = true
    },

    closeEditModal() {
      this.editModalOpen = false
      this.editingProduct = null
    },

    async updateProduct(slug, formDataOrJson) {
      this.loading = true
      try {
        const isFormData = formDataOrJson instanceof FormData
        const headers = isFormData ? { 'Content-Type': 'multipart/form-data' } : {}

        const response = await apiClient.put(`/products/${slug}/`, formDataOrJson, { headers })
        const updated = response.data.data

        // Actualizar en myProducts
        const myIndex = this.myProducts.findIndex((p) => p.slug === slug || p.id === updated.id)
        if (myIndex !== -1) {
          this.myProducts[myIndex] = updated
        }

        // Actualizar en catálogo general
        const catIndex = this.products.findIndex((p) => p.slug === slug || p.id === updated.id)
        if (catIndex !== -1) {
          this.products[catIndex] = updated
        }

        if (this.selectedProduct && (this.selectedProduct.slug === slug || this.selectedProduct.id === updated.id)) {
          this.selectedProduct = updated
        }

        return { success: true, product: updated }
      } catch (err) {
        let msg = 'Error al actualizar la publicación.'
        if (err.response?.data?.errors) {
          const errors = err.response.data.errors
          const firstKey = Object.keys(errors)[0]
          if (firstKey && Array.isArray(errors[firstKey])) {
            msg = `${firstKey}: ${errors[firstKey][0]}`
          } else if (typeof errors === 'string') {
            msg = errors
          }
        }
        return { success: false, error: msg }
      } finally {
        this.loading = false
      }
    },

    async deleteProduct(slug) {
      this.loading = true
      try {
        await apiClient.delete(`/products/${slug}/`)
        this.myProducts = this.myProducts.filter((p) => p.slug !== slug)
        this.products = this.products.filter((p) => p.slug !== slug)
        if (this.selectedProduct?.slug === slug) {
          this.selectedProduct = null
          this.goToCatalog()
        }
        return { success: true }
      } catch (err) {
        const msg = err.response?.data?.message || 'Error al dar de baja el producto.'
        return { success: false, error: msg }
      } finally {
        this.loading = false
      }
    },

    // ===== MODAL REGISTRO DE TIENDA OFICIAL =====
    openRegisterStoreModal() {
      this.registerStoreModalOpen = true
    },

    closeRegisterStoreModal() {
      this.registerStoreModalOpen = false
    },

    async registerStore({ store_name, store_url }) {
      this.loading = true
      try {
        const response = await apiClient.post('/auth/register-store/', { store_name, store_url })
        // Refrescar mis publicaciones y catálogo para reflejar la tienda oficial
        await Promise.all([this.fetchMyProducts(), this.fetchProducts()])
        this.closeRegisterStoreModal()
        return { success: true, data: response.data.data }
      } catch (err) {
        let msg = 'Error al registrar la tienda oficial.'
        if (err.response?.data?.errors) {
          const errors = err.response.data.errors
          const firstKey = Object.keys(errors)[0]
          if (firstKey && Array.isArray(errors[firstKey])) {
            msg = `${firstKey}: ${errors[firstKey][0]}`
          }
        }
        return { success: false, error: msg }
      } finally {
        this.loading = false
      }
    },

    // ===== EVALUACIÓN DE COMPRADOR / CALIFICACIONES =====
    openReviewModal(product) {
      this.reviewingProduct = product
      this.reviewModalOpen = true
    },

    closeReviewModal() {
      this.reviewModalOpen = false
      this.reviewingProduct = null
    },

    async submitReview(slug, { rating, comment }) {
      this.loading = true
      try {
        const response = await apiClient.post(`/products/${slug}/review/`, { rating, comment })
        const { updated_rating, reviews_count } = response.data.data

        // Actualizar el producto seleccionado y en las listas
        if (this.selectedProduct && this.selectedProduct.slug === slug) {
          this.selectedProduct.rating = updated_rating
          this.selectedProduct.reviews_count = reviews_count
        }
        const prod = this.products.find((p) => p.slug === slug)
        if (prod) {
          prod.rating = updated_rating
          prod.reviews_count = reviews_count
        }

        this.closeReviewModal()
        return { success: true, updated_rating, reviews_count }
      } catch (err) {
        let msg = 'Error al registrar tu evaluación.'
        if (err.response?.data?.errors) {
          const errors = err.response.data.errors
          const firstKey = Object.keys(errors)[0]
          if (firstKey && Array.isArray(errors[firstKey])) {
            msg = `${firstKey}: ${errors[firstKey][0]}`
          }
        }
        return { success: false, error: msg }
      } finally {
        this.loading = false
      }
    },
  },
})
