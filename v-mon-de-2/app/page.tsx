'use client'

import { LeftSidebar } from '@/components/left-sidebar'
import { MapView } from '@/components/map-view'
import { RightSidebar } from '@/components/right-sidebar'
import { useEffect, useState } from 'react'
import { Navbar } from '@/components/navbar'

interface VehicleData {
  id: string
  speed: number
  acceleration: number
  proximityAlert: string
  position: [number, number]
  brakeStatus: string
}

interface Alert {
  type: string
  message: string
  severity: 'warning' | 'error' | 'info'
}

export default function DashboardPage() {
  const [vehicles, setVehicles] = useState<VehicleData[]>([
    {
      id: 'V001',
      speed: 60,
      acceleration: 2.5,
      proximityAlert: 'Clear',
      position: [51.4965, -0.0731],
      brakeStatus: 'Normal'
    },
    {
      id: 'V002',
      speed: 45,
      acceleration: 1.8,
      proximityAlert: 'Warning',
      position: [51.4975, -0.0721],
      brakeStatus: 'Applied'
    }
  ])

  const [alerts, setAlerts] = useState<Alert[]>([
    {
      type: 'Road Condition',
      message: 'Slippery surface ahead',
      severity: 'warning'
    },
    {
      type: 'Collision Risk',
      message: 'Vehicle approaching rapidly from behind',
      severity: 'error'
    }
  ])

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Navbar at the top */}
      <Navbar links={[{ name: 'Home', href: '/' }]} title="Vehicle Dashboard" />

      {/* Main content area */}
      <div className="flex flex-1">
        {/* Left sidebar */}
        <LeftSidebar vehicles={vehicles} />
        
        {/* Main map view */}
        <main className="flex-1 p-4">
          <MapView vehicles={vehicles} />
        </main>
        
        {/* Right sidebar */}
        <RightSidebar alerts={alerts} />
      </div>
    </div>
  )
}
