import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface VehicleData {
  id: string
  speed: number
  acceleration: number
  proximityAlert: string
}

export function LeftSidebar({ vehicles }: { vehicles: VehicleData[] }) {
  return (
    <div className="w-80 border-r bg-muted/10 p-4 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Vehicle Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Speed:</span>
            <span className="font-medium">{vehicles[0]?.speed} km/h</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Acceleration:</span>
            <span className="font-medium">{vehicles[0]?.acceleration} m/s²</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Proximity Alert:</span>
            <span className="font-medium">{vehicles[0]?.proximityAlert}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Active Vehicles</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm mb-2">
            Number of active vehicles: {vehicles.length}
          </div>
          <div className="flex flex-wrap gap-2">
            {vehicles.map((vehicle) => (
              <Badge
                key={vehicle.id}
                variant={vehicle.id === 'V001' ? 'default' : 'secondary'}
              >
                {vehicle.id}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

