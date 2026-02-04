'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import Image from 'next/image';
import {
  Municipality,
  PakketpuntData,
  PakketpuntFeature,
  PakketpuntProperties,
  Filters,
  getPointCategory,
} from '@/types/pakketpunten';
import { findNearestPoints, formatDistance, NearestPoint } from '@/utils/distanceUtils';

// Mapping table for PDOK municipality names to our database names (same as AddressSearchInput)
const MUNICIPALITY_NAME_MAPPING: Record<string, string> = {
  "'s-gravenhage": "den haag",
  "'s-hertogenbosch": "s-hertogenbosch",
  "bergen (nh)": "bergen (nh.)",
  "bergen (l)": "bergen (l.)",
  "hengelo (o)": "hengelo",
  "beek (l)": "beek",
  "laren (nh)": "laren",
  "middelburg (z)": "middelburg",
  "rijswijk (zh)": "rijswijk",
  "stein (l)": "stein",
  "hengelo (o.)": "hengelo",
  "beek (l.)": "beek",
  "laren (nh.)": "laren",
  "middelburg (z.)": "middelburg",
  "rijswijk (zh.)": "rijswijk",
  "stein (l.)": "stein",
};

// Provider info matching Map.tsx
const PROVIDER_INFO: Record<string, { color: string; logoUrl: string; borderColor?: string }> = {
  DHL: { color: '#FFCC00', logoUrl: '/logos/dhl.svg', borderColor: '#D40511' },
  PostNL: { color: '#FF6600', logoUrl: '/logos/postnl.svg' },
  VintedGo: { color: '#09B1BA', logoUrl: '/logos/vintedgo.svg' },
  DeBuren: { color: '#4CAF50', logoUrl: '/logos/deburen.png' },
  Amazon: { color: '#FF9900', logoUrl: '/logos/amazon.svg', borderColor: '#146EB4' },
  DPD: { color: '#DC0032', logoUrl: '/logos/dpd.svg' },
  GLS: { color: '#003C7E', logoUrl: '/logos/gls.svg', borderColor: '#FFC600' },
};

interface SearchResult {
  id: string;
  displayName: string;
  type: string;
  municipality?: string;
  score: number;
}

interface NearestPointsFinderProps {
  isOpen: boolean;
  onClose: () => void;
  municipalities: Municipality[];
  currentMunicipalityData: PakketpuntData | null;
  filters: Filters;
  onMunicipalityChange: (slug: string) => void;
  onSearchLocationChange: (location: { latitude: number; longitude: number } | null) => void;
  onHighlightedPointsChange: (points: Set<string> | null) => void;
  onPointSelect: (coordinates: { latitude: number; longitude: number }) => void;
  initialSearch?: {
    coordinates: { latitude: number; longitude: number };
    displayName: string;
  } | null;
}

export default function NearestPointsFinder({
  isOpen,
  onClose,
  municipalities,
  currentMunicipalityData,
  filters,
  onMunicipalityChange,
  onSearchLocationChange,
  onHighlightedPointsChange,
  onPointSelect,
  initialSearch,
}: NearestPointsFinderProps) {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [error, setError] = useState<string | null>(null);
  const [searchLocation, setSearchLocation] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);
  const [nearestPoints, setNearestPoints] = useState<NearestPoint[]>([]);
  const [pendingMunicipalitySlug, setPendingMunicipalitySlug] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const initialSearchUsedRef = useRef(false);

  // Handle initial search from main PDOK search bar when panel opens
  useEffect(() => {
    if (isOpen && initialSearch && !initialSearchUsedRef.current) {
      console.log('NearestPointsFinder: Using initial search from PDOK bar', initialSearch);
      // Set the query display
      setQuery(initialSearch.displayName);
      // Set the search location
      setSearchLocation(initialSearch.coordinates);
      onSearchLocationChange(initialSearch.coordinates);
      // Mark as used for this session so it doesn't re-trigger immediately
      initialSearchUsedRef.current = true;
      // Don't clear lastAddressSearch - keep it for re-toggling
    }
  }, [isOpen, initialSearch, onSearchLocationChange]);

  // Reset the ref when panel closes
  useEffect(() => {
    if (!isOpen) {
      initialSearchUsedRef.current = false;
    }
  }, [isOpen]);

  // Helper to check if point matches filters
  const matchesFilters = useCallback(
    (props: PakketpuntProperties): boolean => {
      // Provider filter
      if (!filters.providers.includes(props.vervoerder)) return false;

      // Category filter
      const category = getPointCategory(props.puntType);
      if (!filters.pointCategories.includes(category)) return false;

      // Service filter
      const wantsPickup = filters.serviceFilters.includes('pickup');
      const wantsDropoff = filters.serviceFilters.includes('dropoff');
      if (wantsPickup && wantsDropoff) {
        if (!props.canPickup && !props.canDropoff) return false;
      } else if (wantsPickup && !props.canPickup) {
        return false;
      } else if (wantsDropoff && !props.canDropoff) {
        return false;
      }

      return true;
    },
    [filters]
  );

  // Get filtered points from current municipality data
  const filteredPoints = useMemo(() => {
    if (!currentMunicipalityData) return [];
    return currentMunicipalityData.features.filter((f) => {
      if (f.properties.type !== 'pakketpunt') return false;
      return matchesFilters(f.properties as PakketpuntProperties);
    }) as PakketpuntFeature[];
  }, [currentMunicipalityData, matchesFilters]);

  // Calculate nearest points when search location or filtered points change
  // Limited to 500m max distance
  // Also re-runs when panel opens to re-apply highlighting
  useEffect(() => {
    // Only calculate when panel is open
    if (!isOpen) return;

    if (searchLocation && filteredPoints.length > 0) {
      const nearest = findNearestPoints(searchLocation, filteredPoints, 10, 500);
      setNearestPoints(nearest);

      // Create set of highlighted point keys
      const highlightedSet = new Set<string>();
      nearest.forEach((np) => {
        const props = np.feature.properties as PakketpuntProperties;
        highlightedSet.add(`${props.latitude.toFixed(6)},${props.longitude.toFixed(6)}`);
      });
      onHighlightedPointsChange(highlightedSet);
    } else {
      setNearestPoints([]);
      onHighlightedPointsChange(null);
    }
  }, [isOpen, searchLocation, filteredPoints, onHighlightedPointsChange]);

  // When municipality data loads after a pending switch, recalculate
  useEffect(() => {
    if (pendingMunicipalitySlug && currentMunicipalityData) {
      if (currentMunicipalityData.metadata.slug === pendingMunicipalitySlug) {
        setPendingMunicipalitySlug(null);
        // The useEffect above will recalculate nearest points
      }
    }
  }, [currentMunicipalityData, pendingMunicipalitySlug]);

  // Find municipality by PDOK name
  const findMunicipality = useCallback(
    (pdokName: string): Municipality | null => {
      let normalizedName = pdokName.toLowerCase();
      if (MUNICIPALITY_NAME_MAPPING[normalizedName]) {
        normalizedName = MUNICIPALITY_NAME_MAPPING[normalizedName];
      }

      // Try exact match
      let municipality = municipalities.find(
        (m) => m.name.toLowerCase() === normalizedName
      );

      // Try slug match
      if (!municipality) {
        municipality = municipalities.find(
          (m) => m.slug.toLowerCase() === normalizedName.replace(/\s+/g, '-').replace(/\./g, '')
        );
      }

      return municipality || null;
    },
    [municipalities]
  );

  // Debounced search function
  const searchAddress = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/geocode?q=${encodeURIComponent(searchQuery)}`);
      if (!response.ok) throw new Error('Geocoding failed');

      const data = await response.json();
      setSearchResults(data.results || []);
      setShowDropdown(true);
      setSelectedIndex(-1);
    } catch (err) {
      console.error('Geocoding error:', err);
      setError('Adres zoeken mislukt');
      setSearchResults([]);
      setShowDropdown(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle input change with debouncing
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      searchAddress(value);
    }, 300);
  };

  // Process search result and switch municipality
  const processSearchResult = async (result: SearchResult) => {
    setQuery(result.displayName);
    setShowDropdown(false);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/geocode?id=${encodeURIComponent(result.id)}`);
      if (!response.ok) throw new Error('Address lookup failed');

      const details = await response.json();

      if (!details.coordinates) {
        setError('Geen coordinaten beschikbaar');
        setIsLoading(false);
        return;
      }

      if (!details.municipality) {
        setError('Geen gemeente gevonden');
        setIsLoading(false);
        return;
      }

      // Find and switch to the municipality
      const municipality = findMunicipality(details.municipality);
      if (!municipality) {
        setError(`Gemeente "${details.municipality}" niet in database`);
        setIsLoading(false);
        return;
      }

      // Set search location and marker
      setSearchLocation(details.coordinates);
      onSearchLocationChange(details.coordinates);

      // Switch municipality if needed
      if (currentMunicipalityData?.metadata.slug !== municipality.slug) {
        setPendingMunicipalitySlug(municipality.slug);
        onMunicipalityChange(municipality.slug);
      }
    } catch (err) {
      console.error('Address lookup error:', err);
      setError('Adres ophalen mislukt');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle direct search (Enter without dropdown selection)
  const handleDirectSearch = async () => {
    if (query.length < 2) return;

    setIsLoading(true);
    setError(null);
    setShowDropdown(false);

    try {
      const suggestResponse = await fetch(`/api/geocode?q=${encodeURIComponent(query)}`);
      if (!suggestResponse.ok) throw new Error('Geocoding failed');

      const suggestData = await suggestResponse.json();
      const results = suggestData.results || [];

      if (results.length === 0) {
        setError('Geen resultaten gevonden');
        setIsLoading(false);
        return;
      }

      // Auto-select first result
      await processSearchResult(results[0]);
    } catch (err) {
      console.error('Direct search error:', err);
      setError('Adres zoeken mislukt');
      setIsLoading(false);
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (showDropdown && selectedIndex >= 0 && selectedIndex < searchResults.length) {
        processSearchResult(searchResults[selectedIndex]);
      } else {
        handleDirectSearch();
      }
      return;
    }

    if (!showDropdown || searchResults.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => (prev < searchResults.length - 1 ? prev + 1 : prev));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Escape':
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;
    }
  };

  // Handle clicking on a result row
  const handlePointClick = (point: NearestPoint) => {
    const props = point.feature.properties as PakketpuntProperties;
    onPointSelect({ latitude: props.latitude, longitude: props.longitude });
  };

  // Clear search
  const handleClear = () => {
    setQuery('');
    setSearchResults([]);
    setShowDropdown(false);
    setError(null);
    setSearchLocation(null);
    setNearestPoints([]);
    onSearchLocationChange(null);
    onHighlightedPointsChange(null);
    inputRef.current?.focus();
  };

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  if (!isOpen) return null;

  return (
    <div className="fixed right-4 top-20 z-30 w-80 max-h-[calc(100vh-120px)] bg-white rounded-lg shadow-xl border border-gray-200 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <span className="font-medium text-gray-900 text-sm">Dichtstbijzijnde pakketpunten</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 transition"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="p-4 flex-1 overflow-y-auto">
        {/* Search input */}
        <div className="relative">
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Adres of postcode..."
              className="w-full px-3 py-2.5 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 text-sm"
            />
            {isLoading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <svg className="animate-spin h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            )}
            {!isLoading && query && (
              <button
                onClick={handleClear}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Error message */}
          {error && <div className="mt-2 text-xs text-red-600">{error}</div>}

          {/* Dropdown results */}
          {showDropdown && searchResults.length > 0 && (
            <div
              ref={dropdownRef}
              className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto"
            >
              {searchResults.map((result, index) => (
                <button
                  key={result.id}
                  onClick={() => processSearchResult(result)}
                  className={`w-full px-3 py-2 text-left hover:bg-blue-50 transition ${
                    index === selectedIndex ? 'bg-blue-50' : ''
                  } ${index !== searchResults.length - 1 ? 'border-b border-gray-200' : ''}`}
                >
                  <div className="text-sm text-gray-900 truncate">{result.displayName}</div>
                  {result.municipality && (
                    <div className="text-xs text-gray-500">{result.municipality}</div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* No results within 500m */}
        {searchLocation && !pendingMunicipalitySlug && nearestPoints.length === 0 && (
          <div className="mt-4 text-sm text-gray-500 text-center py-4">
            <svg className="w-8 h-8 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Geen pakketpunten binnen 500m gevonden
          </div>
        )}

        {/* Results list */}
        {searchLocation && nearestPoints.length > 0 && (
          <div className="mt-4 space-y-1">
            <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              {nearestPoints.length} pakketpunt{nearestPoints.length !== 1 ? 'en' : ''} binnen 500m
            </div>
            {nearestPoints.map((point, index) => {
              const props = point.feature.properties as PakketpuntProperties;
              const providerInfo = PROVIDER_INFO[props.vervoerder] || { color: '#666', logoUrl: '' };

              return (
                <button
                  key={`${props.vervoerder}-${props.latitude}-${props.longitude}-${index}`}
                  onClick={() => handlePointClick(point)}
                  className="w-full text-left p-2 rounded-lg hover:bg-blue-50 transition group border border-transparent hover:border-blue-200"
                >
                  <div className="flex items-start gap-2">
                    {/* Rank number */}
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white">
                      {index + 1}
                    </div>

                    {/* Provider logo */}
                    <div
                      className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center bg-white border-2 overflow-hidden"
                      style={{ borderColor: providerInfo.borderColor || providerInfo.color }}
                      title={props.vervoerder}
                    >
                      <Image
                        src={providerInfo.logoUrl}
                        alt={props.vervoerder}
                        width={16}
                        height={16}
                        className="object-contain"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          const parent = target.parentElement;
                          if (parent) {
                            parent.innerHTML = `<span class="text-[8px] font-bold" style="color: ${providerInfo.color}">${props.vervoerder.substring(0, 2).toUpperCase()}</span>`;
                          }
                        }}
                      />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate group-hover:text-blue-600">
                        {props.locatieNaam}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {props.straatNaam} {props.straatNr}
                      </div>
                    </div>

                    {/* Distance badge */}
                    <div className="flex-shrink-0">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {formatDistance(point.distance)}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* Loading state while waiting for municipality data */}
        {searchLocation && pendingMunicipalitySlug && (
          <div className="mt-4 text-sm text-gray-500 text-center py-4">
            <svg className="animate-spin h-5 w-5 mx-auto mb-2 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Gemeente laden...
          </div>
        )}

        {/* Helper text */}
        {!searchLocation && !query && (
          <div className="mt-3 text-xs text-gray-400">
            Voer een adres of postcode in. De kaart schakelt automatisch naar de juiste gemeente en toont de 10 dichtstbijzijnde pakketpunten.
          </div>
        )}
      </div>
    </div>
  );
}
