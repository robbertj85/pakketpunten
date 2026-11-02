import { Municipality } from '@/types/pakketpunten';

// PDOK returns official CBS municipality names, which differ from the
// common/simplified names in our database:
//
// PDOK returns:                Our database has:
// - 's-Gravenhage         ->   Den Haag (common name)
// - 's-Hertogenbosch      ->   s-Hertogenbosch (no apostrophe)
// - Bergen (NH)           ->   Bergen (NH.) (with period)
// - Bergen (L)            ->   Bergen (L.) (with period)
// - Hengelo (O)           ->   Hengelo (no region identifier)
// - Beek (L), Laren (NH), Middelburg (Z), Rijswijk (ZH), Stein (L) likewise
const MUNICIPALITY_NAME_MAPPING: Record<string, string> = {
  "'s-gravenhage": 'den haag',
  "'s-hertogenbosch": 's-hertogenbosch',
  'bergen (nh)': 'bergen (nh.)',
  'bergen (l)': 'bergen (l.)',
  'hengelo (o)': 'hengelo',
  'beek (l)': 'beek',
  'laren (nh)': 'laren',
  'middelburg (z)': 'middelburg',
  'rijswijk (zh)': 'rijswijk',
  'stein (l)': 'stein',
  // With periods, in case PDOK returns these variants
  'hengelo (o.)': 'hengelo',
  'beek (l.)': 'beek',
  'laren (nh.)': 'laren',
  'middelburg (z.)': 'middelburg',
  'rijswijk (zh.)': 'rijswijk',
  'stein (l.)': 'stein',
};

/** Map a PDOK municipality name onto one of our municipalities. */
export function findMunicipalityByPdokName(
  municipalities: Municipality[],
  pdokName: string
): Municipality | null {
  let normalized = pdokName.toLowerCase();
  if (MUNICIPALITY_NAME_MAPPING[normalized]) {
    normalized = MUNICIPALITY_NAME_MAPPING[normalized];
  }
  const asSlug = normalized.replace(/\s+/g, '-').replace(/\./g, '');
  return (
    municipalities.find((m) => m.name.toLowerCase() === normalized) ||
    municipalities.find((m) => m.slug.toLowerCase() === asSlug) ||
    null
  );
}
