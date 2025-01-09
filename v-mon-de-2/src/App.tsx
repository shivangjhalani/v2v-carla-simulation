import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import { AlertPanel } from './components/AlertPanel';
import { VehicleStatus } from './components/VehicleStatus';
import { MapView } from './components/MapView';
import { SpeedChart } from './components/SpeedChart';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const socket = io('http://localhost:5000');

export default function App() {
  const [vehicles, setVehicles] = useState([]);
  const [roadConditions, setRoadConditions] = useState([]);

  useEffect(() => {
    socket.on('vehicleUpdate', (data) => setVehicles(data));
    socket.on('roadConditionUpdate', (data) => setRoadConditions(data));

    return () => {
      socket.off('vehicleUpdate');
      socket.off('roadConditionUpdate');
    };
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Vehicle Monitoring Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <AlertPanel roadConditions={roadConditions} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Vehicle Status</CardTitle>
          </CardHeader>
          <CardContent>
            <VehicleStatus vehicles={vehicles} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Map View</CardTitle>
          </CardHeader>
          <CardContent>
            <MapView vehicles={vehicles} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Speed Chart</CardTitle>
          </CardHeader>
          <CardContent>
            <SpeedChart vehicles={vehicles} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

