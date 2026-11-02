'use client';

import { useEffect, useState } from 'react';
import { Municipality } from '@/types/pakketpunten';
import { isGeolocationSupported, locateUser, LocationDeniedError } from '@/utils/geolocate';

const DISMISS_KEY = 'locationPromptDismissedAt';
const DISMISS_DAYS = 30;
const SHOW_DELAY_MS = 1200;

function readDismissed(): boolean {
  try {
    const at = Number(localStorage.getItem(DISMISS_KEY));
    return at > 0 && Date.now() - at < DISMISS_DAYS * 24 * 60 * 60 * 1000;
  } catch {
    return false;
  }
}

function writeDismissed() {
  try {
    localStorage.setItem(DISMISS_KEY, String(Date.now()));
  } catch {
    // Private mode / blocked storage: the prompt just comes back next visit
  }
}

interface LocationPromptProps {
  municipalities: Municipality[];
  /** True while something else already answers "where am I" (a search, the top 10 panel, an open menu). */
  suppressed: boolean;
  onLocated: (
    municipalitySlug: string,
    coordinates: { latitude: number; longitude: number },
    displayName: string
  ) => void;
}

/**
 * Mobile-only toast that offers the device location right away, since on
 * small screens the address search sits behind the menu button.
 */
export default function LocationPrompt({ municipalities, suppressed, onLocated }: LocationPromptProps) {
  // 'idle' until eligibility is known; 'hidden' once dismissed or used.
  const [state, setState] = useState<'idle' | 'offer' | 'hidden'>('idle');
  const [entered, setEntered] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Decide whether to offer at all: geolocation available, not blocked, not
  // recently dismissed. Only offered on small screens.
  useEffect(() => {
    if (!isGeolocationSupported() || readDismissed()) return;
    if (!window.matchMedia('(max-width: 767px)').matches) return;

    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        const status = await navigator.permissions?.query({ name: 'geolocation' });
        if (status?.state === 'denied') return;
      } catch {
        // Permissions API unsupported (older Safari): just offer it
      }
      if (!cancelled) setState('offer');
    }, SHOW_DELAY_MS);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);

  // Slide in on the frame after mounting, so the transition runs
  const visible = state === 'offer' && !suppressed && municipalities.length > 0;
  useEffect(() => {
    if (!visible) {
      setEntered(false);
      return;
    }
    const frame = requestAnimationFrame(() => setEntered(true));
    return () => cancelAnimationFrame(frame);
  }, [visible]);

  if (!visible) return null;

  const dismiss = () => {
    writeDismissed();
    setState('hidden');
  };

  const handleLocate = async () => {
    setError(null);
    setIsLocating(true);
    try {
      const { municipality, coordinates, displayName } = await locateUser(municipalities);
      setState('hidden');
      onLocated(municipality.slug, coordinates, displayName);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Locatie ophalen mislukt');
      // Blocked access won't change by asking again; stop offering it.
      if (err instanceof LocationDeniedError) writeDismissed();
    } finally {
      setIsLocating(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-label="Pakketpunten bij jou in de buurt"
      // Top of the map, right of the zoom controls: the bottom-left is taken by
      // the floating filter button.
      className={`md:hidden absolute left-14 right-3 top-3 z-30 bg-card border border-border rounded-xl shadow-xl p-3 transition-all duration-300 ease-out motion-reduce:transition-none ${
        entered ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0'
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-9 h-9 rounded-full bg-accent text-primary flex items-center justify-center">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11a3 3 0 100-6 3 3 0 000 6z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 22s8-6.5 8-13a8 8 0 10-16 0c0 6.5 8 13 8 13z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-foreground">Pakketpunten bij jou in de buurt?</div>
          <div className="text-xs text-subtle-foreground mt-0.5">
            {error ?? 'Deel je locatie en zie de 10 dichtstbijzijnde punten.'}
          </div>
        </div>
        <button
          onClick={dismiss}
          className="flex-shrink-0 -m-1 p-1 text-subtle-foreground hover:text-muted-foreground"
          aria-label="Sluiten"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <button
        onClick={handleLocate}
        disabled={isLocating}
        className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 active:bg-primary/80 disabled:opacity-60 transition"
      >
        {isLocating && (
          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
        )}
        {isLocating ? 'Locatie ophalen…' : 'Gebruik mijn locatie'}
      </button>
    </div>
  );
}
