import { Municipality } from '@/types/pakketpunten';
import { findMunicipalityByPdokName } from '@/utils/pdokMunicipality';

export interface LocatedAddress {
  municipality: Municipality;
  coordinates: { latitude: number; longitude: number };
  displayName: string;
}

/** The user (or browser policy) refused location access. */
export class LocationDeniedError extends Error {}

export function isGeolocationSupported(): boolean {
  return typeof window !== 'undefined' && 'geolocation' in navigator;
}

/**
 * Ask the browser for the device position, reverse-geocode it via PDOK and
 * resolve the municipality it falls in. Rejects with an Error whose message is
 * a Dutch, user-facing explanation.
 */
export async function locateUser(municipalities: Municipality[]): Promise<LocatedAddress> {
  if (!isGeolocationSupported()) {
    throw new Error('Locatie wordt niet ondersteund door deze browser');
  }

  const position = await new Promise<GeolocationPosition>((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      resolve,
      (err) => {
        if (err.code === err.PERMISSION_DENIED) {
          reject(new LocationDeniedError('Locatie geweigerd. Schakel locatietoegang in voor deze site.'));
        } else if (err.code === err.POSITION_UNAVAILABLE) {
          reject(new Error('Locatie is op dit moment niet beschikbaar'));
        } else if (err.code === err.TIMEOUT) {
          reject(new Error('Locatie ophalen duurde te lang'));
        } else {
          reject(new Error('Locatie ophalen mislukt'));
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  });

  const { latitude, longitude } = position.coords;

  let details: {
    municipality?: string;
    displayName?: string;
    coordinates?: { latitude: number; longitude: number } | null;
  };
  try {
    const response = await fetch(`/api/geocode?lat=${latitude}&lon=${longitude}`);
    if (!response.ok) throw new Error(`Reverse geocode failed: ${response.status}`);
    details = await response.json();
  } catch (err) {
    console.error('Reverse geocode error:', err);
    throw new Error('Locatie kon niet worden omgezet naar een adres');
  }

  if (!details.municipality) {
    throw new Error('Geen Nederlandse gemeente bij deze locatie gevonden');
  }

  const municipality = findMunicipalityByPdokName(municipalities, details.municipality);
  if (!municipality) {
    throw new Error(`Gemeente "${details.municipality}" niet in database`);
  }

  return {
    municipality,
    coordinates: details.coordinates || { latitude, longitude },
    displayName: details.displayName || 'Mijn locatie',
  };
}
