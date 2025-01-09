import React from 'react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { ExclamationTriangleIcon } from "@radix-ui/react-icons"

export function AlertPanel({ roadConditions }) {
  const getAlertVariant = (condition) => {
    switch (condition) {
      case 'Wet':
      case 'Slippery':
        return 'warning';
      case 'Construction Zone':
      case 'Debris':
        return 'destructive';
      default:
        return 'default';
    }
  };

  return (
    <div className="space-y-2">
      {roadConditions.map((condition, index) => (
        <Alert key={index} variant={getAlertVariant(condition.condition)}>
          <ExclamationTriangleIcon className="h-4 w-4" />
          <AlertTitle>{condition.type}</AlertTitle>
          <AlertDescription>{condition.condition}</AlertDescription>
        </Alert>
      ))}
    </div>
  );
}

