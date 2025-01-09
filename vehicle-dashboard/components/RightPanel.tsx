import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

type AlertSeverity = 'default' | 'info' | 'warning' | 'error'

interface AlertData {
  type: string
  message: string
  severity: AlertSeverity
}

interface SensorData {
  temperature: number
  speed: number
  lidarDistance: number
}

export default function RightPanel() {
  // Mock data for alerts and vehicle status
  const alerts: AlertData[] = [
    { type: "Road Condition", message: "Slippery surface ahead", severity: "warning" },
    { type: "Vehicle Status", message: "Brakes applied", severity: "info" },
    { type: "Collision Risk", message: "Vehicle approaching rapidly from behind", severity: "error" },
  ]

  // Mock live sensor data
  const sensorData: SensorData = {
    temperature: 25,
    speed: 60,
    lidarDistance: 50,
  }

  // Mock data for speed graph
  const speedData = [
    { time: '00:00', speed: 50 },
    { time: '00:05', speed: 55 },
    { time: '00:10', speed: 52 },
    { time: '00:15', speed: 58 },
    { time: '00:20', speed: 56 },
  ]

  return (
    <div className="w-1/3 p-4 overflow-auto">
      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Warnings and Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {alerts.map((alert, index) => (
            <Alert key={index} variant={alert.severity} className="mb-2">
              <AlertTitle>{alert.type}</AlertTitle>
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          ))}
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Live Sensor Data</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Temperature: {sensorData.temperature}°C</p>
          <p>Speed: {sensorData.speed} km/h</p>
          <p>Lidar Distance: {sensorData.lidarDistance} m</p>
        </CardContent>
      </Card>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Vehicle Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Brake status: Brakes applied</p>
          <p>Indicator status: Left turn signal ON</p>
          <p>Acceleration rate: 1.5 m/s²</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Speed Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={speedData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="speed" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

