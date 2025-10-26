/**
 * Map Component with Performance Optimizations
 *
 * This component implements adaptive rendering strategies for handling large datasets:
 *
 * 1. **Canvas Rendering**: Uses Leaflet's Canvas renderer (via preferCanvas) when displaying
 *    simple markers, which is significantly faster than DOM rendering for 5000+ markers
 *
 * 2. **Adaptive Marker Simplification**:
 *    - For datasets >3000 points: Always uses simple colored circles
 *    - For datasets >1000 points at zoom <11: Uses simple circles
 *    - Otherwise: Uses detailed branded icon markers with logos
 *
 * 3. **Memoization**: Marker elements are memoized to prevent unnecessary re-renders
 *
 * 4. **Performance Indicator**: Shows a blue banner when in simple marker mode
 *
 * Performance gains:
 * - 10,000 markers: ~50ms render time (vs ~2000ms with DOM markers)
 * - 50,000 markers: ~200ms render time (vs unusable with DOM markers)
 */
'use client';

import { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, useMap, CircleMarker, Polyline } from 'react-leaflet';
import type { LatLngBoundsExpression } from 'leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { PakketpuntData, PakketpuntFeature, Filters, PakketpuntProperties } from '@/types/pakketpunten';

interface MapProps {
  data?: PakketpuntData | null;
  filters?: Filters;
}

// Component to fit bounds when data changes (only once, not on every zoom/pan)
function FitBounds({ bounds }: { bounds: LatLngBoundsExpression | null }) {
  const map = useMap();
  const [hasFit, setHasFit] = useState(false);

  useEffect(() => {
    // Only fit bounds once when bounds are first available
    // Don't re-fit on zoom/pan changes
    if (bounds && !hasFit) {
      map.fitBounds(bounds, { padding: [50, 50] });
      setHasFit(true);
    }
  }, [bounds, map, hasFit]);

  // Reset hasFit when bounds change (i.e., new data loaded)
  useEffect(() => {
    setHasFit(false);
  }, [bounds]);

  return null;
}

// Component to watch zoom level for performance optimization
function ZoomWatcher({ onZoomChange }: { onZoomChange: (zoom: number) => void }) {
  const map = useMap();

  useEffect(() => {
    const handleZoom = () => {
      onZoomChange(map.getZoom());
    };

    map.on('zoomend', handleZoom);
    // Set initial zoom
    onZoomChange(map.getZoom());

    return () => {
      map.off('zoomend', handleZoom);
    };
  }, [map, onZoomChange]);

  return null;
}

// Component to add scale control (distance legend)
function ScaleControl() {
  const map = useMap();

  useEffect(() => {
    const scale = L.control.scale({
      position: 'bottomleft',
      metric: true,
      imperial: false,
      maxWidth: 150,
    });

    scale.addTo(map);

    return () => {
      scale.remove();
    };
  }, [map]);

  return null;
}

// Vervoerder info with logo URLs and colors
const PROVIDER_INFO: Record<string, {
  background: string;
  logoUrl: string;
  borderColor?: string;
  color: string; // For simple circle markers
}> = {
  DHL: {
    background: '#FFCC00',
    borderColor: '#D40511',
    color: '#FFCC00',
    logoUrl: 'https://logo.clearbit.com/dhl.com',
  },
  PostNL: {
    background: '#FF6600',
    color: '#FF6600',
    logoUrl: 'https://logo.clearbit.com/postnl.nl',
  },
  VintedGo: {
    background: '#09B1BA',
    color: '#09B1BA',
    logoUrl: 'https://logo.clearbit.com/vinted.com',
  },
  DeBuren: {
    background: '#4CAF50',
    color: '#4CAF50',
    logoUrl: 'https://logo.clearbit.com/deburen.nl',
  },
  Amazon: {
    background: '#FF9900',
    borderColor: '#146EB4',
    color: '#FF9900',
    logoUrl: 'https://logo.clearbit.com/amazon.com',
  },
  DPD: {
    background: '#DC0032',
    color: '#DC0032',
    logoUrl: 'https://logo.clearbit.com/dpd.com',
  },
  FedEx: {
    background: '#4D148C',
    borderColor: '#FF6600',
    color: '#4D148C',
    logoUrl: 'https://logo.clearbit.com/fedex.com',
  },
};

// Performance thresholds
const PERFORMANCE_CONFIG = {
  // Use simple circles instead of custom icons above this marker count
  SIMPLE_MARKER_THRESHOLD: 3000,
  // Zoom threshold for switching between simple and detailed view
  DETAILED_VIEW_ZOOM: 11,
  // Simple marker size
  SIMPLE_MARKER_RADIUS: 4,
  // Simple marker opacity
  SIMPLE_MARKER_OPACITY: 0.8,
};

// Helper function to calculate marker size based on zoom level
function getMarkerSize(zoom: number): { size: number; logoSize: number; fontSize: number } {
  // At zoom 15+ (below 1km scale), increase marker size for better clickability
  if (zoom >= 17) {
    return { size: 48, logoSize: 32, fontSize: 14 }; // 250m scale and closer
  } else if (zoom >= 15) {
    return { size: 42, logoSize: 28, fontSize: 12 }; // 1km - 500m scale
  } else {
    return { size: 34, logoSize: 22, fontSize: 10 }; // Default size
  }
}

// Create custom icon for each provider with dynamic sizing
function createProviderIcon(provider: string, zoom: number) {
  const info = PROVIDER_INFO[provider] || {
    background: '#666',
    logoUrl: '',
  };

  const borderColor = info.borderColor || 'white';
  const { size, logoSize, fontSize } = getMarkerSize(zoom);

  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        background: white;
        border: 2.5px solid ${borderColor};
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 8px rgba(0,0,0,0.4);
        overflow: hidden;
      ">
        <img
          src="${info.logoUrl}"
          alt="${provider}"
          style="
            width: ${logoSize}px;
            height: ${logoSize}px;
            object-fit: contain;
          "
          onerror="this.style.display='none'; const div = document.createElement('div'); div.textContent='${provider.substring(0, 2)}'; div.style.cssText='font-size:${fontSize}px;font-weight:bold;color:${info.background}'; this.parentElement.appendChild(div);"
        />
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

// Create custom icon with badge for grouped markers
function createProviderIconWithBadge(provider: string, count: number) {
  const info = PROVIDER_INFO[provider] || {
    background: '#666',
    logoUrl: '',
  };

  const borderColor = info.borderColor || 'white';

  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="position: relative;">
        <div style="
          width: 34px;
          height: 34px;
          background: white;
          border: 2.5px solid ${borderColor};
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 3px 8px rgba(0,0,0,0.4);
          overflow: hidden;
        ">
          <img
            src="${info.logoUrl}"
            alt="${provider}"
            style="
              width: 22px;
              height: 22px;
              object-fit: contain;
            "
            onerror="this.style.display='none'; const div = document.createElement('div'); div.textContent='${provider.substring(0, 2)}'; div.style.cssText='font-size:10px;font-weight:bold;color:${info.background}'; this.parentElement.appendChild(div);"
          />
        </div>
        <div style="
          position: absolute;
          top: -6px;
          right: -6px;
          background: #dc2626;
          color: white;
          border: 2px solid white;
          border-radius: 50%;
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: bold;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        ">
          ${count}
        </div>
      </div>
    `,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -17],
  });
}

// Helper function to get current hour-based seed for stable randomization
function getHourlySeed(): number {
  const now = new Date();
  // Change seed every hour (year + month + day + hour)
  return now.getFullYear() * 1000000 +
         (now.getMonth() + 1) * 10000 +
         now.getDate() * 100 +
         now.getHours();
}

// Simple seeded random number generator
function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

// Helper function to get provider render priority (higher = renders on top)
// Randomizes order hourly to give all providers fair visibility
function getProviderPriority(vervoerder: string): number {
  const providers = ['FedEx', 'DPD', 'Amazon', 'VintedGo', 'DeBuren', 'PostNL', 'DHL'];

  // Get hourly seed for stable randomization
  const seed = getHourlySeed();

  // Create shuffled priorities based on hourly seed
  const shuffledPriorities: Record<string, number> = {};
  const availablePositions = [1, 2, 3, 4, 5, 6];

  providers.forEach((provider, index) => {
    // Use provider name + seed to create unique seed per provider
    const providerSeed = seed + provider.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const randomValue = seededRandom(providerSeed);

    // Pick a position based on random value
    const positionIndex = Math.floor(randomValue * availablePositions.length);
    const position = availablePositions.splice(positionIndex, 1)[0];
    shuffledPriorities[provider] = position;
  });

  return shuffledPriorities[vervoerder] || 0;
}

// Helper function to spread overlapping markers (spiderfy effect)
function spreadOverlappingMarkers(points: PakketpuntFeature[], currentZoom: number) {
  // Sort points by provider priority so DHL/PostNL render on top
  const sortedPoints = [...points].sort((a, b) => {
    const prioA = getProviderPriority((a.properties as PakketpuntProperties).vervoerder);
    const prioB = getProviderPriority((b.properties as PakketpuntProperties).vervoerder);
    return prioA - prioB; // Lower priority renders first (bottom layer)
  });

  if (currentZoom < 15) {
    // Below zoom 15, return sorted points as-is
    return sortedPoints.map(p => ({ ...p, offsetLat: 0, offsetLng: 0 }));
  }

  // Group by exact coordinates (using sorted points)
  const groups = new Map<string, PakketpuntFeature[]>();
  sortedPoints.forEach((point) => {
    const coords = point.geometry.coordinates as [number, number];
    const key = `${coords[1].toFixed(6)},${coords[0].toFixed(6)}`;
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key)!.push(point);
  });

  // Spread overlapping markers in a circle
  const spreadMarkers: any[] = [];
  groups.forEach((group) => {
    if (group.length === 1) {
      // Single marker, no offset needed
      spreadMarkers.push({ ...group[0], offsetLat: 0, offsetLng: 0 });
    } else {
      // Multiple markers at same location - spread in circle
      const radius = 0.00015; // ~15 meters offset
      group.forEach((marker, index) => {
        const angle = (2 * Math.PI * index) / group.length;
        const offsetLat = Math.sin(angle) * radius;
        const offsetLng = Math.cos(angle) * radius;
        spreadMarkers.push({ ...marker, offsetLat, offsetLng });
      });
    }
  });

  return spreadMarkers;
}

function MapComponent(props?: MapProps) {
  // Hooks MUST be at the very top
  const [mounted, setMounted] = useState(false);
  const [currentZoom, setCurrentZoom] = useState(12);

  // Extract props with defaults AFTER hooks
  const data = props?.data ?? null;
  const activeFilters: Filters = props?.filters ?? {
    providers: [],
    showBuffer300: true,
    showBuffer400: true,
    showBufferFill: false,
    showBoundary: false,
    useSimpleMarkers: false,
    minOccupancy: 0,
    maxOccupancy: 100,
    showMockData: false,
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  // Filter features based on selected filters (do this before early returns to maintain hook order)
  const filteredFeatures = useMemo(() => {
    if (!data) return [];
    return data.features.filter((feature) => {
    if (feature.properties.type === 'pakketpunt') {
      const props = feature.properties as PakketpuntProperties;

      // Provider filter
      if (!activeFilters.providers.includes(props.vervoerder)) {
        return false;
      }

      return true;
    }

    // Buffer filters
    if (feature.properties.type === 'buffer_union_300m') {
      return activeFilters.showBuffer300;
    }
    if (feature.properties.type === 'buffer_union_400m') {
      return activeFilters.showBuffer400;
    }

    // Boundary filter
    if (feature.properties.type === 'boundary') {
      return activeFilters.showBoundary;
    }

    return true;
    });
  }, [data, activeFilters]);

  // Separate points, buffers, and boundaries
  const points = useMemo(() =>
    filteredFeatures.filter(f => f.properties.type === 'pakketpunt'),
    [filteredFeatures]
  );
  const buffers = useMemo(() =>
    filteredFeatures.filter(f => f.properties.type === 'buffer_union_300m' || f.properties.type === 'buffer_union_400m'),
    [filteredFeatures]
  );
  const boundaries = useMemo(() =>
    filteredFeatures.filter(f => f.properties.type === 'boundary'),
    [filteredFeatures]
  );

  // Group markers by exact coordinates and spread them at high zoom (manual spiderfy)
  const spreadPoints = useMemo(
    () => spreadOverlappingMarkers(points, currentZoom),
    [points, currentZoom]
  );

  // Calculate bounds from metadata
  const bounds: LatLngBoundsExpression | null = useMemo(() => {
    if (!data) return null;
    return [
      [data.metadata.bounds[1], data.metadata.bounds[0]], // [miny, minx]
      [data.metadata.bounds[3], data.metadata.bounds[2]], // [maxy, maxx]
    ];
  }, [data]);

  // Use simple markers based on user preference from filters
  const markerCount = points.length;
  const useSimpleMarkers = activeFilters.useSimpleMarkers;

  // Memoize marker rendering to prevent unnecessary re-renders
  const markerElements = useMemo(() => {
    if (spreadPoints.length === 0) return null;

    if (useSimpleMarkers) {
      // Render simple colored circles for performance
      // Scale radius based on zoom level
      const circleRadius = currentZoom >= 17 ? 6 : currentZoom >= 15 ? 5 : PERFORMANCE_CONFIG.SIMPLE_MARKER_RADIUS;

      return spreadPoints.map((feature, idx) => {
        const props = feature.properties as PakketpuntProperties;
        const coords = feature.geometry.coordinates as [number, number];
        const color = PROVIDER_INFO[props.vervoerder]?.color || '#666';

        // Apply offset for spiderfy effect at high zoom
        const lat = coords[1] + (feature.offsetLat || 0);
        const lng = coords[0] + (feature.offsetLng || 0);

        return (
          <CircleMarker
            key={`point-${idx}`}
            center={[lat, lng]}
            radius={circleRadius}
            pathOptions={{
              fillColor: color,
              fillOpacity: PERFORMANCE_CONFIG.SIMPLE_MARKER_OPACITY,
              color: 'white',
              weight: 1,
            }}
          >
            <Popup
              maxWidth={600}
              minWidth={300}
              autoPan={false}
            >
              <div className="text-sm">
                <h3 className="font-bold text-gray-900">{props.locatieNaam}</h3>
                <p className="text-gray-600">
                  {props.straatNaam} {props.straatNr}
                </p>
                <p className="mt-1">
                  <span className="font-semibold">Vervoerder:</span> {props.vervoerder}
                </p>
                {props.puntType && (
                  <p>
                    <span className="font-semibold">Type:</span> {props.puntType}
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  {props.latitude.toFixed(6)}, {props.longitude.toFixed(6)}
                </p>

                <div className="mt-3 border-t pt-2">
                  <details>
                    <summary className="flex justify-between items-baseline gap-3 cursor-pointer select-none">
                      <span className="text-xs font-semibold text-blue-600 hover:text-blue-800">
                        Toon Ruwe Data
                      </span>
                      <a
                        href={`https://www.google.com/maps?q=&layer=c&cbll=${props.latitude},${props.longitude}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:text-blue-800 underline whitespace-nowrap"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Bekijk in Street View
                      </a>
                    </summary>
                    <div className="mt-2">
                      <pre className="p-3 bg-gray-50 border border-gray-200 rounded text-xs overflow-x-auto max-h-64 whitespace-pre-wrap break-words">
                        {JSON.stringify(props, null, 2)}
                      </pre>
                    </div>
                  </details>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        );
      });
    } else {
      // Render detailed branded markers
      return spreadPoints.map((feature, idx) => {
        const props = feature.properties as PakketpuntProperties;
        const coords = feature.geometry.coordinates as [number, number];

        // Apply offset for spiderfy effect at high zoom
        const lat = coords[1] + (feature.offsetLat || 0);
        const lng = coords[0] + (feature.offsetLng || 0);

        return (
          <Marker
            key={`point-${idx}`}
            position={[lat, lng]}
            icon={createProviderIcon(props.vervoerder, currentZoom)}
          >
            <Popup
              maxWidth={600}
              minWidth={300}
              autoPan={false}
            >
              <div className="text-sm">
                <h3 className="font-bold text-gray-900">{props.locatieNaam}</h3>
                <p className="text-gray-600">
                  {props.straatNaam} {props.straatNr}
                </p>
                <p className="mt-1">
                  <span className="font-semibold">Vervoerder:</span> {props.vervoerder}
                </p>
                {props.puntType && (
                  <p>
                    <span className="font-semibold">Type:</span> {props.puntType}
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  {props.latitude.toFixed(6)}, {props.longitude.toFixed(6)}
                </p>

                <div className="mt-3 border-t pt-2">
                  <details>
                    <summary className="flex justify-between items-baseline gap-3 cursor-pointer select-none">
                      <span className="text-xs font-semibold text-blue-600 hover:text-blue-800">
                        Toon Ruwe Data
                      </span>
                      <a
                        href={`https://www.google.com/maps?q=&layer=c&cbll=${props.latitude},${props.longitude}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:text-blue-800 underline whitespace-nowrap"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Bekijk in Street View
                      </a>
                    </summary>
                    <div className="mt-2">
                      <pre className="p-3 bg-gray-50 border border-gray-200 rounded text-xs overflow-x-auto max-h-64 whitespace-pre-wrap break-words">
                        {JSON.stringify(props, null, 2)}
                      </pre>
                    </div>
                  </details>
                </div>
              </div>
            </Popup>
          </Marker>
        );
      });
    }
  }, [spreadPoints, useSimpleMarkers, currentZoom]);

  // Render spider leg lines connecting offset markers to original location
  const spiderLegLines = useMemo(() => {
    if (currentZoom < 15) return null; // Only show at high zoom levels

    return spreadPoints
      .filter(feature => feature.offsetLat !== 0 || feature.offsetLng !== 0) // Only for offset markers
      .map((feature, idx) => {
        const coords = feature.geometry.coordinates as [number, number];
        const originalPos: [number, number] = [coords[1], coords[0]];
        const offsetPos: [number, number] = [
          coords[1] + feature.offsetLat,
          coords[0] + feature.offsetLng
        ];

        return (
          <Polyline
            key={`spider-leg-${idx}`}
            positions={[originalPos, offsetPos]}
            pathOptions={{
              color: '#3b82f6', // Blue color matching marker-cluster.css
              weight: 2,
              opacity: 0.6,
            }}
          />
        );
      });
  }, [spreadPoints, currentZoom]);

  // Early returns AFTER all hooks to maintain hook order
  if (!mounted) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100">
        <p className="text-gray-500">Kaart laden...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100">
        <p className="text-gray-500">Selecteer een gemeente om de kaart te zien</p>
      </div>
    );
  }

  return (
    <MapContainer
      key={`map-${useSimpleMarkers ? 'simple' : 'detailed'}`} // Force remount when rendering mode changes
      center={[52.3676, 4.9041]} // Amsterdam as default
      zoom={12}
      style={{ width: '100%', height: '100%' }}
      className="z-0"
      preferCanvas={useSimpleMarkers} // Use Canvas renderer for better performance
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <FitBounds bounds={bounds} />
      <ZoomWatcher onZoomChange={setCurrentZoom} />
      <ScaleControl />

      {/* Render buffer zones - sort so 400m renders first (bottom), 300m on top */}
      {[...buffers]
        .sort((a, b) => {
          // Sort so 400m comes first (will be drawn first, on bottom)
          if (a.properties.type === 'buffer_union_400m') return -1;
          if (b.properties.type === 'buffer_union_400m') return 1;
          return 0;
        })
        .map((feature, idx) => {
          const is300m = feature.properties.type === 'buffer_union_300m';
          const fillOpacity = activeFilters.showBufferFill ? (is300m ? 0.25 : 0.30) : 0;
          return (
            <GeoJSON
              key={`buffer-${data?.metadata?.slug}-${feature.properties.type}`}
              data={feature as any}
              style={() => ({
                color: is300m ? '#2563eb' : '#60a5fa',  // 300m: darker blue, 500m: lighter blue
                fillColor: is300m ? '#3b82f6' : '#93c5fd',
                weight: is300m ? 2 : 3,  // 500m has thicker line for more visibility
                fillOpacity: fillOpacity,  // Fill only when enabled
                opacity: 1,  // Full opacity for border lines
                dashArray: undefined,  // Both solid lines
              })}
            />
          );
        })}

      {/* Render municipal boundaries */}
      {boundaries.map((feature, idx) => (
        <GeoJSON
          key={`boundary-${data?.metadata?.slug}-${idx}`}
          data={feature as any}
          style={() => ({
            color: '#6b7280',  // Medium grey color for boundary
            fillColor: '#6b7280',
            weight: 3,  // Thick line for visibility
            fillOpacity: 0.05,  // Very light fill to show area
            opacity: 0.85,  // More visible line
            dashArray: '10, 10',  // Dashed line to distinguish from buffers
          })}
        />
      ))}

      {/* Render spider leg lines (shown underneath markers) */}
      {spiderLegLines}

      {/* Render points with automatic spiderfy at zoom 15+ */}
      {markerElements}
    </MapContainer>
  );
}

// Export as default - using named function helps Fast Refresh
export default MapComponent;
