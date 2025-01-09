import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function ActiveVehicles() {
  // Mock data for active vehicles
  const activeVehicles = [
    { id: "V001", status: "active" },
    { id: "V002", status: "active" },
    { id: "V003", status: "inactive" },
    { id: "V004", status: "active" },
  ]

  const activeCount = activeVehicles.filter(v => v.status === "active").length

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Vehicles</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-2">Number of active vehicles: {activeCount}</p>
        <div className="flex flex-wrap gap-2">
          {activeVehicles.map(vehicle => (
            <Badge key={vehicle.id} variant={vehicle.status === "active" ? "default" : "secondary"}>
              {vehicle.id}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

