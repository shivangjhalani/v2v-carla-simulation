'use client'

import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

interface VehicleData {
  id: string
  position: [number, number]
}

export function MapView({ vehicles }: { vehicles: VehicleData[] }) {
  const mapRef = useRef<L.Map | null>(null)
  const markersRef = useRef<{ [key: string]: L.Marker }>({})

  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map('map').setView([51.4965, -0.0731], 15)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(mapRef.current)
    }

    // Update or create markers for each vehicle
    vehicles.forEach((vehicle) => {
      if (markersRef.current[vehicle.id]) {
        markersRef.current[vehicle.id].setLatLng(vehicle.position)
      } else {
        const marker = L.marker(vehicle.position, {
          icon: L.divIcon({
            className: 'bg-primary text-white px-2 py-1 rounded-full',
            html: vehicle.id
          })
        }).addTo(mapRef.current!)
        markersRef.current[vehicle.id] = marker
      }
    })

    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [vehicles])

  return (
    <div id="map" className="h-full w-full rounded-lg shadow-lg" />
  )
}

