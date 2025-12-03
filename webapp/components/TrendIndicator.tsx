'use client';

interface TrendIndicatorProps {
  change: number;
  label?: string;
  showValue?: boolean;
}

export default function TrendIndicator({ change, label, showValue = true }: TrendIndicatorProps) {
  const isPositive = change > 0;
  const isNegative = change < 0;
  const isNeutral = change === 0;

  const colorClass = isPositive
    ? 'text-green-600'
    : isNegative
      ? 'text-red-600'
      : 'text-gray-500';

  const bgClass = isPositive
    ? 'bg-green-50'
    : isNegative
      ? 'bg-red-50'
      : 'bg-gray-50';

  const arrow = isPositive ? '↑' : isNegative ? '↓' : '→';
  const sign = isPositive ? '+' : '';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClass} ${bgClass}`}>
      <span className="mr-1">{arrow}</span>
      {showValue && <span>{sign}{change}</span>}
      {label && <span className="ml-1 text-gray-500">{label}</span>}
    </span>
  );
}
