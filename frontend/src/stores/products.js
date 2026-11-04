import { defineStore } from 'pinia'
import apiClient from '../services/api'

export const useProductStore = defineStore('products', {
  state: () => ({
    products: [],
    categories: [],
    selectedProduct: null,
    detailModalOpen: false,
    createModalOpen: false,
    filterModalOpen: false,
    loading: false,
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
    activeView: 'catalog', // 'catalog' | 'product_page'
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
  },
})
