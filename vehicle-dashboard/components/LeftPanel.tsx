import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import ActiveVehicles from './ActiveVehicles'

export default function LeftPanel() {
  // Mock data
  const vehicleDetails = {
    speed: 60,
    acceleration: 2.5,
    proximityAlert: "Clear"
  }

  return (
    <div className="w-1/4 p-4 overflow-auto">
      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Vehicle Details</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Speed: {vehicleDetails.speed} km/h</p>
          <p>Acceleration: {vehicleDetails.acceleration} m/s²</p>
          <p>Proximity Alert: {vehicleDetails.proximityAlert}</p>
        </CardContent>
      </Card>
      <ActiveVehicles />
    </div>
  )
}

