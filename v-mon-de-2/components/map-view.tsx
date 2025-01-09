"use client";

import { useEffect, useRef } from "react";
import dynamic from "next/dynamic"; // For dynamic imports in Next.js
import "leaflet/dist/leaflet.css"; // Import Leaflet styles

interface VehicleData {
  id: string;
  position: [number, number];
}

// Dynamically import Leaflet with SSR disabled
const Leaflet = dynamic(() => import("leaflet"), { ssr: false });

export function MapView({ vehicles }: { vehicles: VehicleData[] }) {
  const mapRef = useRef<any>(null);
  const markersRef = useRef<{ [key: string]: any }>({});

  useEffect(() => {
    // Ensure Leaflet is loaded and window is available
    if (!mapRef.current && typeof window !== "undefined") {
      import("leaflet").then((L) => {
        mapRef.current = L.map("map").setView([51.4965, -0.0731], 15);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap contributors",
        }).addTo(mapRef.current);
      });
    }

    // Update or create markers
    if (mapRef.current) {
      vehicles.forEach((vehicle) => {
        if (markersRef.current[vehicle.id]) {
          markersRef.current[vehicle.id].setLatLng(vehicle.position);
        } else {
          import("leaflet").then((L) => {
            const marker = L.marker(vehicle.position, {
              icon: L.divIcon({
                className: "bg-primary text-white px-2 py-1 rounded-full",
                html: vehicle.id,
              }),
            }).addTo(mapRef.current);
            markersRef.current[vehicle.id] = marker;
          });
        }
      });
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [vehicles]);

  return <div id="map" className="h-full w-full rounded-lg shadow-lg" />;
}
