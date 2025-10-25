'use client';

import { useState, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import MunicipalitySelector from '@/components/MunicipalitySelector';
import FilterPanel from '@/components/FilterPanel';
import StatsPanel from '@/components/StatsPanel';
import AboutModal from '@/components/AboutModal';
import { Municipality, PakketpuntData, Filters, PakketpuntProperties } from '@/types/pakketpunten';

// Dynamically import Map component to avoid SSR issues with Leaflet
const Map = dynamic(() => import('@/components/Map'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-gray-100">
      <p className="text-gray-500">Kaart laden...</p>
    </div>
  ),
});

export default function Home() {
  const [municipalities, setMunicipalities] = useState<Municipality[]>([]);
  const [selectedMunicipality, setSelectedMunicipality] = useState<string>('');
  const [data, setData] = useState<PakketpuntData | null>(null);
  const [loading, setLoading] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    providers: ['DHL', 'PostNL', 'VintedGo', 'DeBuren'],
    showBuffer300: true,
    showBuffer500: true,
    showBufferFill: false,
    useSimpleMarkers: false,
    minOccupancy: 0,
    maxOccupancy: 100,
    showMockData: false,
  });

  // Load municipalities on mount
  useEffect(() => {
    fetch('/municipalities.json')
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        // Sort alphabetically, but put Nederland at the bottom
        const sortedData = data.sort((a: Municipality, b: Municipality) => {
          if (a.slug === 'nederland') return 1;
          if (b.slug === 'nederland') return -1;
          return a.name.localeCompare(b.name);
        });

        setMunicipalities(sortedData);

        // Auto-select Zwolle as default
        const zwolle = sortedData.find((m: Municipality) => m.slug === 'zwolle');
        if (zwolle) {
          setSelectedMunicipality('zwolle');
        } else if (sortedData.length > 0) {
          setSelectedMunicipality(sortedData[0].slug);
        }
      })
      .catch((err) => console.error('Error loading municipalities:', err));
  }, []);

  // Load data when municipality changes
  useEffect(() => {
    if (!selectedMunicipality) {
      setData(null);
      return;
    }

    setLoading(true);
    fetch(`/data/${selectedMunicipality}.geojson`)
      .then(async (res) => {
        console.log('Response status:', res.status);
        console.log('Content-Type:', res.headers.get('content-type'));

        if (!res.ok) {
          const text = await res.text();
          console.error('Response body:', text.substring(0, 200));
          throw new Error(`HTTP error! status: ${res.status}`);
        }

        // Check content type
        const contentType = res.headers.get('content-type');
        if (!contentType || (!contentType.includes('json') && !contentType.includes('geo'))) {
          const text = await res.text();
          console.error('Wrong content type. First 500 chars:', text.substring(0, 500));
          throw new Error(`Expected JSON but got: ${contentType}`);
        }

        return res.json();
      })
      .then((data) => {
        console.log('Data loaded successfully!', data.metadata);
        setData(data);
        // Reset filters when changing municipality
        // Automatically use simple markers for Nederland view (better performance)
        const isNederland = selectedMunicipality === 'nederland';
        setFilters({
          providers: data.metadata.providers || ['DHL', 'PostNL', 'VintedGo', 'DeBuren'],
          showBuffer300: true,
          showBuffer500: true,
          showBufferFill: false,
          useSimpleMarkers: isNederland,
          minOccupancy: 0,
          maxOccupancy: 100,
          showMockData: false,
        });
      })
      .catch((err) => {
        console.error('Error loading data:', err);
        console.error('Failed to load:', `/data/${selectedMunicipality}.geojson`);
      })
      .finally(() => setLoading(false));
  }, [selectedMunicipality]);

  // Calculate provider counts for filtered data
  const providerCounts = useMemo(() => {
    if (!data) return {};

    const points = data.features.filter(f => f.properties.type === 'pakketpunt');
    const filteredPoints = points.filter((feature) => {
      const props = feature.properties as PakketpuntProperties;
      return (
        filters.providers.includes(props.vervoerder) &&
        props.bezettingsgraad >= filters.minOccupancy &&
        props.bezettingsgraad <= filters.maxOccupancy
      );
    });

    return filteredPoints.reduce((acc, feature) => {
      const props = feature.properties as PakketpuntProperties;
      acc[props.vervoerder] = (acc[props.vervoerder] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [data, filters]);

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm z-10">
        <div className="px-4 py-3 flex items-center gap-4">
          {/* Logo */}
          <div className="flex-shrink-0">
            <h1 className="text-xl font-bold text-gray-900">📦 Pakketpunten</h1>
          </div>

          {/* Municipality Selector */}
          <div className="flex-1 max-w-md">
            <MunicipalitySelector
              municipalities={municipalities}
              selected={selectedMunicipality}
              onChange={setSelectedMunicipality}
            />
          </div>

          {/* Loading indicator */}
          {loading && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Laden...
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-2 ml-auto">
            <a
              href="/data-export"
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Data and Export
            </a>
            <button
              onClick={() => setShowAbout(true)}
              className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Over
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside className="w-80 bg-gray-50 p-4 overflow-y-auto space-y-4">
          {data && (
            <>
              <StatsPanel data={data} filters={filters} />
              <FilterPanel
                filters={filters}
                onChange={setFilters}
                availableProviders={data.metadata.providers}
                providerCounts={providerCounts}
              />
            </>
          )}
        </aside>

        {/* Map */}
        <main className="flex-1 relative">
          <Map data={data} filters={filters} />
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-4 py-2">
        <div className="max-w-7xl mx-auto flex justify-between items-center text-xs text-gray-500">
          <p>
            Data bronnen: DHL, PostNL, VintedGo, De Buren
          </p>
          {data && (
            <p>
              Laatste update: {new Date(data.metadata.generated_at).toLocaleDateString('nl-NL')}
            </p>
          )}
        </div>
      </footer>

      {/* About Modal */}
      <AboutModal isOpen={showAbout} onClose={() => setShowAbout(false)} />
    </div>
  );
}
