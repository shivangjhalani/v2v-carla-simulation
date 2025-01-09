import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ExclamationTriangleIcon, InfoCircledIcon } from "@radix-ui/react-icons"

interface AlertData {
  type: string
  message: string
  severity: 'warning' | 'error' | 'info'
}

export function RightSidebar({ alerts }: { alerts: AlertData[] }) {
  return (
    <div className="w-80 border-l bg-muted/10 p-4 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Warnings and Alerts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {alerts.map((alert, index) => (
            <Alert
              key={index}
              variant={alert.severity === 'error' ? 'destructive' : 'default'}
            >
              {alert.severity === 'error' ? (
                <ExclamationTriangleIcon className="h-4 w-4" />
              ) : (
                <InfoCircledIcon className="h-4 w-4" />
              )}
              <AlertTitle>{alert.type}</AlertTitle>
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Live Sensor Data</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Temperature:</span>
              <span className="font-medium">24°C</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Humidity:</span>
              <span className="font-medium">65%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Pressure:</span>
              <span className="font-medium">1013 hPa</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

