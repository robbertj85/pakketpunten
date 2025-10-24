import { promises as fs } from 'fs';
import path from 'path';

interface ProviderCounts {
  [provider: string]: number;
}

interface MunicipalityData {
  name: string;
  slug: string;
  providers: ProviderCounts;
  total: number;
}

async function getMunicipalityData(): Promise<MunicipalityData[]> {
  const dataDir = path.join(process.cwd(), 'public', 'data');
  const files = await fs.readdir(dataDir);
  const geojsonFiles = files.filter(f => f.endsWith('.geojson'));

  const municipalityData: MunicipalityData[] = [];

  for (const file of geojsonFiles) {
    try {
      const filePath = path.join(dataDir, file);
      const content = await fs.readFile(filePath, 'utf-8');
      const data = JSON.parse(content);

      // Extract pakketpunt features only
      const pakketpunten = data.features.filter(
        (f: any) => f.properties?.type === 'pakketpunt'
      );

      // Count by provider
      const providerCounts: ProviderCounts = {};
      pakketpunten.forEach((feature: any) => {
        const provider = feature.properties?.vervoerder || 'Unknown';
        providerCounts[provider] = (providerCounts[provider] || 0) + 1;
      });

      municipalityData.push({
        name: data.metadata.gemeente,
        slug: data.metadata.slug || file.replace('.geojson', ''),
        providers: providerCounts,
        total: pakketpunten.length,
      });
    } catch (error) {
      console.error(`Error reading ${file}:`, error);
    }
  }

  // Sort by municipality name, but put Nederland at the top
  return municipalityData.sort((a, b) => {
    if (a.slug === 'nederland') return -1;
    if (b.slug === 'nederland') return 1;
    return a.name.localeCompare(b.name);
  });
}

export default async function DataMatrixPage() {
  const data = await getMunicipalityData();

  // Get all unique providers
  const allProviders = new Set<string>();
  data.forEach(m => {
    Object.keys(m.providers).forEach(p => allProviders.add(p));
  });
  const providers = Array.from(allProviders).sort();

  // Calculate totals per provider (excluding Nederland to avoid double-counting)
  const municipalitiesOnly = data.filter(m => m.slug !== 'nederland');
  const providerTotals: ProviderCounts = {};
  providers.forEach(provider => {
    providerTotals[provider] = municipalitiesOnly.reduce((sum, m) => sum + (m.providers[provider] || 0), 0);
  });
  const grandTotal = municipalitiesOnly.reduce((sum, m) => sum + m.total, 0);

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Overzicht</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-900">{municipalitiesOnly.length}</div>
            <div className="text-sm text-blue-700">Gemeentes</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-900">{grandTotal.toLocaleString('nl-NL')}</div>
            <div className="text-sm text-green-700">Totaal Pakketpunten</div>
            <div className="text-xs text-green-600 mt-1">(excl. Nederland)</div>
          </div>
          {providers.map(provider => (
            <div key={provider} className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{providerTotals[provider].toLocaleString('nl-NL')}</div>
              <div className="text-sm text-gray-700">{provider}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Data Matrix Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">Pakketpunten per Gemeente en Vervoerder</h2>
          <p className="text-sm text-gray-600 mt-1">
            Deze data wordt automatisch bijgewerkt wanneer nieuwe gegevens worden gegenereerd
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sticky left-0 bg-gray-50 z-10">
                  Gemeente
                </th>
                {providers.map(provider => (
                  <th key={provider} className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                    {provider}
                  </th>
                ))}
                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-900 uppercase tracking-wider bg-gray-100">
                  Totaal
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((municipality, idx) => (
                <tr
                  key={municipality.slug}
                  className={`hover:bg-gray-50 ${municipality.slug === 'nederland' ? 'bg-blue-50 font-semibold' : ''}`}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 sticky left-0 bg-white hover:bg-gray-50 z-10">
                    {municipality.name}
                    {municipality.slug === 'nederland' && (
                      <span className="ml-2 text-xs text-blue-600">(Landelijk)</span>
                    )}
                  </td>
                  {providers.map(provider => {
                    const count = municipality.providers[provider] || 0;
                    return (
                      <td key={provider} className="px-4 py-4 text-center text-sm">
                        {count > 0 ? (
                          <span className={count >= 50 ? 'text-amber-600 font-semibold' : 'text-gray-900'}>
                            {count}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                    );
                  })}
                  <td className="px-4 py-4 text-center text-sm font-semibold text-gray-900 bg-gray-50">
                    {municipality.total}
                  </td>
                </tr>
              ))}

              {/* Totals Row */}
              <tr className="bg-gray-100 font-semibold border-t-2 border-gray-300">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 sticky left-0 bg-gray-100 z-10">
                  TOTAAL
                </td>
                {providers.map(provider => (
                  <td key={provider} className="px-4 py-4 text-center text-sm text-gray-900">
                    {providerTotals[provider].toLocaleString('nl-NL')}
                  </td>
                ))}
                <td className="px-4 py-4 text-center text-sm text-gray-900 bg-gray-200">
                  {grandTotal.toLocaleString('nl-NL')}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="font-semibold text-gray-900 mb-3">Leeswijzer</h3>
        <ul className="text-sm text-gray-700 space-y-2">
          <li className="flex items-center">
            <span className="w-4 h-4 bg-blue-50 border border-blue-200 rounded mr-2"></span>
            <strong className="mr-1">Nederland</strong> - Landelijk overzicht (bevat ontdubbelde data van alle gemeentes)
          </li>
          <li className="flex items-center">
            <span className="text-amber-600 font-semibold mr-2">50</span>
            <strong className="mr-1">Oranje getal</strong> - Maximale API limiet bereikt (mogelijk meer punten aanwezig)
          </li>
          <li className="flex items-center">
            <span className="text-gray-400 mr-2">-</span>
            Geen pakketpunten van deze vervoerder in gemeente
          </li>
        </ul>
      </div>
    </div>
  );
}
