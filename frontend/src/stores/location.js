import { defineStore } from 'pinia'

function haversineDistanceKm(lat1, lng1, lat2, lng2) {
  const toRad = (deg) => (deg * Math.PI) / 180
  const R = 6371
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) * Math.sin(dLng / 2)
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export const useLocationStore = defineStore('location', {
  state: () => ({
    currentLocation: localStorage.getItem('inacap_delivery_location') || 'Santiago, Chile',
    currentAddress: localStorage.getItem('inacap_delivery_address') || '',
    isModalOpen: false,
    savedLocations: [
      { id: 'stgo-centro', city: 'Santiago Centro', region: 'Región Metropolitana', full: 'Santiago Centro, RM', lat: -33.4489, lng: -70.6693 },
      { id: 'providencia', city: 'Providencia', region: 'Región Metropolitana', full: 'Providencia, RM', lat: -33.4314, lng: -70.6093 },
      { id: 'las-condes', city: 'Las Condes', region: 'Región Metropolitana', full: 'Las Condes, RM', lat: -33.4167, lng: -70.5833 },
      { id: 'maipu', city: 'Maipú', region: 'Región Metropolitana', full: 'Maipú, RM', lat: -33.5106, lng: -70.7573 },
      { id: 'vina', city: 'Viña del Mar', region: 'Valparaíso', full: 'Viña del Mar, Valparaíso', lat: -33.0153, lng: -71.55 },
      { id: 'valpo', city: 'Valparaíso', region: 'Valparaíso', full: 'Valparaíso, Valparaíso', lat: -33.0472, lng: -71.6127 },
      { id: 'conce', city: 'Concepción', region: 'Biobío', full: 'Concepción, Biobío', lat: -36.8201, lng: -73.0444 },
      { id: 'antofa', city: 'Antofagasta', region: 'Antofagasta', full: 'Antofagasta', lat: -23.6509, lng: -70.3975 },
      { id: 'laserena', city: 'La Serena', region: 'Coquimbo', full: 'La Serena, Coquimbo', lat: -29.9027, lng: -71.2519 },
      { id: 'temuco', city: 'Temuco', region: 'La Araucanía', full: 'Temuco, Araucanía', lat: -38.7359, lng: -72.5904 },
      { id: 'ptomontt', city: 'Puerto Montt', region: 'Los Lagos', full: 'Puerto Montt, Los Lagos', lat: -41.4693, lng: -72.9424 },
      { id: 'rancagua', city: 'Rancagua', region: "O'Higgins", full: "Rancagua, O'Higgins", lat: -34.1708, lng: -70.7444 },
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
      } else {
        localStorage.removeItem('inacap_delivery_address')
      }
      this.closeLocationModal()
    },

    useCurrentGeoLocation() {
      if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            const { latitude, longitude } = pos.coords
            let nearest = this.savedLocations[0]
            let minDistance = Infinity
            for (const loc of this.savedLocations) {
              const dist = haversineDistanceKm(latitude, longitude, loc.lat, loc.lng)
              if (dist < minDistance) {
                minDistance = dist
                nearest = loc
              }
            }
            this.setLocation(nearest.full)
          },
          () => {
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
