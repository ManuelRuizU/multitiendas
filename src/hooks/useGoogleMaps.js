import { useLoadScript } from '@react-google-maps/api'

// Defined outside component to avoid re-creating on each render
const LIBRARIES = ['places']

export function useGoogleMaps() {
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_KEY ?? '',
    libraries: LIBRARIES,
  })
  return { isLoaded, loadError }
}
