import { defineStore } from 'pinia'
import apiClient from '../services/api'

export const useProductStore = defineStore('products', {
  state: () => ({
    products: [],
    categories: [],
    selectedProduct: null,
    detailModalOpen: false,
    createModalOpen: false,
    loading: false,
    error: null,
    activeCategory: null,
    searchQuery: '',
    ordering: '-created_at',
  }),

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
        if (this.searchQuery) {
          params.q = this.searchQuery
        }
        if (this.activeCategory) {
          params.category = this.activeCategory
        }
        if (this.ordering) {
          params.ordering = this.ordering
        }

        const response = await apiClient.get('/products/', { params })
        this.products = response.data.data || []
      } catch (err) {
        this.error = 'No se pudieron cargar los productos del catálogo.'
        console.error('Error cargando productos:', err)
      } finally {
        this.loading = false
      }
    },

    setSearch(query) {
      this.searchQuery = query
      this.fetchProducts()
    },

    setCategory(categorySlug) {
      this.activeCategory = this.activeCategory === categorySlug ? null : categorySlug
      this.fetchProducts()
    },

    setOrdering(sortOrder) {
      this.ordering = sortOrder
      this.fetchProducts()
    },

    openDetail(product) {
      this.selectedProduct = product
      this.detailModalOpen = true
    },

    closeDetail() {
      this.selectedProduct = null
      this.detailModalOpen = false
    },

    openCreateModal() {
      this.createModalOpen = true
    },

    closeCreateModal() {
      this.createModalOpen = false
    },

    async createProduct(productData) {
      this.loading = true
      try {
        const response = await apiClient.post('/products/', productData)
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
          }
        }
        return { success: false, error: msg }
      } finally {
        this.loading = false
      }
    },
  },
})
