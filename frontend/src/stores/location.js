import { defineStore } from 'pinia'

export const useLocationStore = defineStore('location', {
  state: () => ({
    currentLocation: localStorage.getItem('inacap_delivery_location') || 'Santiago, Chile',
    currentAddress: localStorage.getItem('inacap_delivery_address') || '',
    isModalOpen: false,
    savedLocations: [
      { id: 'stgo-centro', city: 'Santiago Centro', region: 'Región Metropolitana', full: 'Santiago Centro, RM' },
      { id: 'providencia', city: 'Providencia', region: 'Región Metropolitana', full: 'Providencia, RM' },
      { id: 'las-condes', city: 'Las Condes', region: 'Región Metropolitana', full: 'Las Condes, RM' },
      { id: 'maipu', city: 'Maipú', region: 'Región Metropolitana', full: 'Maipú, RM' },
      { id: 'vina', city: 'Viña del Mar', region: 'Valparaíso', full: 'Viña del Mar, Valparaíso' },
      { id: 'valpo', city: 'Valparaíso', region: 'Valparaíso', full: 'Valparaíso, Valparaíso' },
      { id: 'conce', city: 'Concepción', region: 'Biobío', full: 'Concepción, Biobío' },
      { id: 'antofa', city: 'Antofagasta', region: 'Antofagasta', full: 'Antofagasta' },
      { id: 'laserena', city: 'La Serena', region: 'Coquimbo', full: 'La Serena, Coquimbo' },
      { id: 'temuco', city: 'Temuco', region: 'La Araucanía', full: 'Temuco, Araucanía' },
      { id: 'ptomontt', city: 'Puerto Montt', region: 'Los Lagos', full: 'Puerto Montt, Los Lagos' },
      { id: 'rancagua', city: 'Rancagua', region: 'O\'Higgins', full: 'Rancagua, O\'Higgins' },
    ],
  }),

  actions: {
    openLocationModal() {
      this.isModalOpen = true
    },

    closeLocationModal() {
      this.isModalOpen = false
    },

    setLocation(locationName, address = '') {
      this.currentLocation = locationName
      this.currentAddress = address
      localStorage.setItem('inacap_delivery_location', locationName)
      if (address) {
        localStorage.setItem('inacap_delivery_address', address)
      }
      this.closeLocationModal()
    },

    useCurrentGeoLocation() {
      if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            // Geolocation success - defaulting to Santiago Providencia for Chile demo
            this.setLocation('Providencia, RM', 'Av. Providencia 1200')
          },
          (err) => {
            // Geolocation denied or unavailable - default to Santiago Centro
            this.setLocation('Santiago Centro, RM')
          },
          { timeout: 5000 }
        )
      } else {
        this.setLocation('Santiago Centro, RM')
      }
    },
  },
})
