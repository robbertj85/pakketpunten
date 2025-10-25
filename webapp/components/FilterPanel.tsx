'use client';

import { Filters } from '@/types/pakketpunten';

interface FilterPanelProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  availableProviders?: string[];
  providerCounts?: Record<string, number>;
}

const PROVIDER_INFO = {
  DHL: { name: 'DHL', color: '#FFCC00', textColor: '#D40511' },
  PostNL: { name: 'PostNL', color: '#FF6600', textColor: '#FFFFFF' },
  VintedGo: { name: 'VintedGo', color: '#09B1BA', textColor: '#FFFFFF' },
  DeBuren: { name: 'De Buren', color: '#4CAF50', textColor: '#FFFFFF' },
  Amazon: { name: 'Amazon', color: '#FF9900', textColor: '#146EB4' },
  DPD: { name: 'DPD', color: '#DC0032', textColor: '#FFFFFF' },
};

export default function FilterPanel({ filters, onChange, availableProviders, providerCounts }: FilterPanelProps) {
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
              checked={filters.showBuffer500}
              onChange={(e) => onChange({ ...filters, showBuffer500: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-900">500m buffer lijn</span>
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
        </div>
      </div>

      {/* Reset button */}
      <button
        onClick={() =>
          onChange({
            providers: providers,
            showBuffer300: true,
            showBuffer500: true,
            showBufferFill: false,
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
