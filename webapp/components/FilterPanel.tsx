'use client';

import { Filters } from '@/types/pakketpunten';
import { BoundaryLoadProgress } from '@/utils/boundaryLoader';

interface FilterPanelProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  availableProviders?: string[];
  providerCounts?: Record<string, number>;
  boundariesLoading?: boolean;
  boundaryLoadProgress?: BoundaryLoadProgress | null;
}

const PROVIDER_INFO = {
  DHL: { name: 'DHL', color: '#FFCC00', textColor: '#D40511' },
  PostNL: { name: 'PostNL', color: '#FF6600', textColor: '#FFFFFF' },
  VintedGo: { name: 'VintedGo', color: '#09B1BA', textColor: '#FFFFFF' },
  DeBuren: { name: 'De Buren', color: '#4CAF50', textColor: '#FFFFFF' },
  Amazon: { name: 'Amazon', color: '#FF9900', textColor: '#146EB4' },
  DPD: { name: 'DPD', color: '#DC0032', textColor: '#FFFFFF' },
};

export default function FilterPanel({ filters, onChange, availableProviders, providerCounts, boundariesLoading, boundaryLoadProgress }: FilterPanelProps) {
  const toggleProvider = (provider: string) => {
    const newProviders = filters.providers.includes(provider)
      ? filters.providers.filter((p) => p !== provider)
      : [...filters.providers, provider];

    onChange({ ...filters, providers: newProviders });
  };

  const providers = availableProviders || Object.keys(PROVIDER_INFO);

  return (
    <div className="space-y-6 p-4 bg-white rounded-lg shadow-md">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Filters</h3>
      </div>

      {/* Provider filters */}
      <div>
        <label className="block text-sm font-medium text-gray-900 mb-2">Vervoerders</label>
        <div className="space-y-2">
          {providers.map((provider) => {
            const info = PROVIDER_INFO[provider as keyof typeof PROVIDER_INFO];
            if (!info) return null;

            const isSelected = filters.providers.includes(provider);
            const count = providerCounts?.[provider] || 0;

            return (
              <label key={provider} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleProvider(provider)}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <span
                  className="w-4 h-4 rounded-full border border-white"
                  style={{ backgroundColor: info.color }}
                />
                <span className="text-sm text-gray-900 flex-1">{info.name}</span>
                {isSelected && count > 0 && (
                  <span className="text-sm font-semibold text-gray-900 ml-auto">
                    {count}
                  </span>
                )}
              </label>
            );
          })}
        </div>
      </div>

      {/* Marker Style */}
      <div>
        <label className="block text-sm font-medium text-gray-900 mb-2">Markering weergave</label>
        <div className="space-y-2">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="radio"
              name="markerStyle"
              checked={!filters.useSimpleMarkers}
              onChange={() => onChange({ ...filters, useSimpleMarkers: false })}
              className="w-4 h-4 text-blue-600 focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-900">🏢 Logo iconen</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="radio"
              name="markerStyle"
              checked={filters.useSimpleMarkers}
              onChange={() => onChange({ ...filters, useSimpleMarkers: true })}
              className="w-4 h-4 text-blue-600 focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-900">● Gekleurde stippen</span>
          </label>
        </div>
      </div>

      {/* Buffer zones */}
      <div>
        <label className="block text-sm font-medium text-gray-900 mb-2">Dekkingsgebieden</label>
        <div className="space-y-2">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.showBuffer300}
              onChange={(e) => onChange({ ...filters, showBuffer300: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-900">300m buffer lijn</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.showBuffer400}
              onChange={(e) => onChange({ ...filters, showBuffer400: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-900">400m buffer lijn</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.showBufferFill}
              onChange={(e) => onChange({ ...filters, showBufferFill: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-900">Buffer opvulling</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.showBoundary}
              onChange={(e) => onChange({ ...filters, showBoundary: e.target.checked })}
              disabled={boundariesLoading}
              className="w-4 h-4 text-red-600 rounded focus:ring-2 focus:ring-red-500 disabled:opacity-50"
            />
            <div className="flex-1">
              <span className="text-sm text-gray-900">Gemeentegrens</span>
              {boundariesLoading && boundaryLoadProgress && (
                <div className="mt-1 text-xs text-blue-600">
                  <div className="flex items-center gap-2">
                    <span>Laden: {boundaryLoadProgress.loaded}/{boundaryLoadProgress.total} provincies</span>
                    <span>({boundaryLoadProgress.percentage}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                    <div
                      className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${boundaryLoadProgress.percentage}%` }}
                    />
                  </div>
                </div>
              )}
              {boundariesLoading && !boundaryLoadProgress && (
                <span className="ml-2 text-xs text-blue-600">(laden...)</span>
              )}
            </div>
          </label>
        </div>
      </div>

      {/* Reset button */}
      <button
        onClick={() =>
          onChange({
            providers: providers,
            showBuffer300: true,
            showBuffer400: true,
            showBufferFill: false,
            showBoundary: false,
            useSimpleMarkers: false,
            minOccupancy: 0,
            maxOccupancy: 100,
            showMockData: false,
          })
        }
        className="w-full px-4 py-2 text-sm font-medium text-gray-900 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
      >
        Reset Filters
      </button>
    </div>
  );
}
