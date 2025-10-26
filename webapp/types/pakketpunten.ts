export interface Municipality {
  name: string;
  slug: string;
  province: string;
  population: number;
}

export interface PakketpuntProperties {
  type: 'pakketpunt';
  locatieNaam: string;
  straatNaam: string;
  straatNr: string;
  vervoerder: 'DHL' | 'PostNL' | 'VintedGo' | 'DeBuren' | 'DPD' | 'FedEx' | 'Amazon';
  puntType: string;
  bezettingsgraad: number;
  latitude: number;
  longitude: number;
}

export interface BufferProperties {
  type: 'buffer_union_300m' | 'buffer_union_400m' | 'boundary';
  buffer_m?: number;
  gemeente?: string;
}

export type FeatureProperties = PakketpuntProperties | BufferProperties;

export interface PakketpuntFeature {
  type: 'Feature';
  geometry: {
    type: 'Point' | 'Polygon' | 'MultiPolygon';
    coordinates: number[] | number[][] | number[][][];
  };
  properties: FeatureProperties;
}

export interface PakketpuntData {
  type: 'FeatureCollection';
  metadata: {
    gemeente: string;
    slug: string;
    generated_at: string;
    total_points: number;
    providers: string[];
    bounds: [number, number, number, number]; // [minx, miny, maxx, maxy]
  };
  features: PakketpuntFeature[];
}

export interface Filters {
  providers: string[];
  showBuffer300: boolean;
  showBuffer400: boolean;
  showBufferFill: boolean;
  showBoundary: boolean;
  useSimpleMarkers: boolean;
  minOccupancy: number;
  maxOccupancy: number;
  showMockData: boolean;
}
