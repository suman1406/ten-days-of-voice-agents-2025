import React from 'react';

interface OrderState {
  drinkType: string;
  size: string;
  milk: string;
  extras: string[];
  name: string;
}

interface BeverageDisplayProps {
  order: OrderState | null;
}

export function BeverageDisplay({ order }: BeverageDisplayProps) {
  if (!order) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300">
        <p className="text-gray-500">Waiting for order...</p>
      </div>
    );
  }

  const { drinkType, size, milk, extras, name } = order;

  // Simple visual mapping
  let cupSizeClass = 'h-32 w-24';
  if (size.toLowerCase() === 'small') cupSizeClass = 'h-24 w-20';
  if (size.toLowerCase() === 'large') cupSizeClass = 'h-40 w-28';

  let drinkColor = 'bg-amber-800'; // Coffee
  if (drinkType.toLowerCase().includes('latte')) drinkColor = 'bg-amber-200';
  if (drinkType.toLowerCase().includes('milk')) drinkColor = 'bg-white';
  if (drinkType.toLowerCase().includes('tea')) drinkColor = 'bg-green-200';

  return (
    <div className="flex flex-col items-center p-6 bg-white rounded-xl shadow-lg border border-gray-200">
      <h3 className="text-xl font-bold mb-4 text-gray-800">Current Order</h3>
      
      <div className="relative flex items-end justify-center mb-4">
        {/* Cup */}
        <div className={`${cupSizeClass} ${drinkColor} rounded-b-xl rounded-t-sm border-4 border-gray-800 relative overflow-hidden transition-all duration-500`}>
          {/* Milk foam/layer if applicable */}
          {milk && milk !== 'None' && (
            <div className="absolute top-0 left-0 right-0 h-4 bg-white opacity-80"></div>
          )}
        </div>

        {/* Whipped Cream */}
        {extras.some(e => e.toLowerCase().includes('whipped')) && (
          <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 w-full text-center">
             ☁️
          </div>
        )}
      </div>

      <div className="w-full text-left space-y-2">
        <p><strong>Name:</strong> {name || 'Guest'}</p>
        <p><strong>Drink:</strong> {size} {drinkType}</p>
        <p><strong>Milk:</strong> {milk}</p>
        <p><strong>Extras:</strong> {extras.join(', ') || 'None'}</p>
      </div>
    </div>
  );
}
