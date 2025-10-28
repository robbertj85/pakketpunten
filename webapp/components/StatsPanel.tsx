'use client';

import { PakketpuntData, Filters, PakketpuntProperties } from '@/types/pakketpunten';

interface StatsPanelProps {
  data: PakketpuntData | null;
  filters: Filters;
}

export default function StatsPanel({ data, filters }: StatsPanelProps) {
  if (!data) {
    return null;
  }

  const isNationalView = data.metadata.slug === 'nederland';

  // Calculate filtered stats
  const points = data.features.filter(f => f.properties.type === 'pakketpunt');
  const filteredPoints = points.filter((feature) => {
    const props = feature.properties as PakketpuntProperties;
    return (
      filters.providers.includes(props.vervoerder) &&
      props.bezettingsgraad >= filters.minOccupancy &&
      props.bezettingsgraad <= filters.maxOccupancy
    );
  });

  const avgOccupancy =
    filteredPoints.length > 0
      ? Math.round(
          filteredPoints.reduce((sum, f) => {
            const props = f.properties as PakketpuntProperties;
            return sum + props.bezettingsgraad;
          }, 0) / filteredPoints.length
        )
      : 0;

  return (
    <div className="p-4 bg-white rounded-lg shadow-md space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{data.metadata.gemeente}</h3>
        <p className="text-xs text-gray-600">
          Laatste update: {new Date(data.metadata.generated_at).toLocaleString('nl-NL')}
        </p>
        {isNationalView && (
          <p className="text-xs text-blue-600 mt-1 font-medium">
            {(data.metadata as any).municipalities_included - 1} gemeentes
          </p>
        )}
      </div>

      <div className={`grid ${filters.showMockData ? 'grid-cols-2' : 'grid-cols-1'} gap-4`}>
        <div className="p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-gray-700 font-medium">Pakketpunten</p>
          <p className="text-2xl font-bold text-blue-600">
            {filteredPoints.length}
            <span className="text-sm font-normal text-gray-600"> / {points.length}</span>
          </p>
        </div>

        {filters.showMockData && (
          <div className="p-3 bg-green-50 rounded-lg">
            <p className="text-xs text-gray-700 font-medium">Gem. Bezetting <span className="text-amber-700">(mock)</span></p>
            <p className="text-2xl font-bold text-green-600">{avgOccupancy}%</p>
          </div>
        )}
      </div>
    </div>
  );
}
