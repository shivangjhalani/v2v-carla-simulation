import React from 'react';

export function MapView({ vehicles }) {
  return (
    <div className="bg-gray-200 p-4 h-64 relative">
      {vehicles.map((vehicle) => (
        <div
          key={vehicle.id}
          className="absolute w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
        >
          {vehicle.id}
        </div>
      ))}
    </div>
  );
}

