import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export function VehicleStatus({ vehicles }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Vehicle ID</TableHead>
          <TableHead>State</TableHead>
          <TableHead>Brake Status</TableHead>
          <TableHead>Acceleration</TableHead>
          <TableHead>Speed</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {vehicles.map((vehicle) => (
          <TableRow key={vehicle.id}>
            <TableCell>{vehicle.id}</TableCell>
            <TableCell>{vehicle.state}</TableCell>
            <TableCell>{vehicle.brakeStatus}</TableCell>
            <TableCell>{vehicle.acceleration.toFixed(2)} m/s²</TableCell>
            <TableCell>{vehicle.speed.toFixed(2)} km/h</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

