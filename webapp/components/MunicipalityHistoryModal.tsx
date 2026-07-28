'use client';

import { MunicipalityHistoryEntry } from '@/types/history';
import { CARRIER_SERIES_COLORS } from '@/lib/carriers';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  BarChart,
  Bar,
  LabelList
} from 'recharts';
import { Card } from '@/components/ui/card';

interface MunicipalityHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  municipalityName: string;
  municipalitySlug: string;
  history: MunicipalityHistoryEntry[];
}

// Provider colors matching the main app
// Validated categorical palette from the shared source. These charts put all
// ten carriers on screen at once, so every one of them needs a legend and
// direct labels: at ten series the palette sits in the 6-8 CVD band, where
// colour alone is not sufficient to tell series apart.
const PROVIDER_COLORS: { [key: string]: string } = CARRIER_SERIES_COLORS;

// Provider logos
const PROVIDER_LOGOS: { [key: string]: string } = {
  DHL: '/logos/dhl.svg',
  PostNL: '/logos/postnl.svg',
  DPD: '/logos/dpd.svg',
  VintedGo: '/logos/vintedgo.svg',
  DeBuren: '/logos/deburen.png',
  Amazon: '/logos/amazon.svg',
  GLS: '/logos/gls.svg',
  ViaTim: '/logos/viatim.svg',
  InPost: '/logos/inpost.svg',
  Budbee: '/logos/budbee.svg',
};

export default function MunicipalityHistoryModal({
  isOpen,
  onClose,
  municipalityName,
  municipalitySlug,
  history
}: MunicipalityHistoryModalProps) {
  if (!isOpen) return null;

  // Get all providers across all history entries
  const allProviders = new Set<string>();
  history.forEach(entry => {
    Object.keys(entry.providers).forEach(p => allProviders.add(p));
  });
  const providers = Array.from(allProviders).sort();

  // Prepare chart data (reverse to show oldest first)
  const chartData = [...history].map(entry => ({
    week: entry.week_label,
    date: entry.date,
    total: entry.total,
    ...entry.providers
  }));

  // Calculate overall trend
  const firstEntry = history[0];
  const lastEntry = history[history.length - 1];
  const totalChange = lastEntry ? lastEntry.total - (firstEntry?.total || 0) : 0;
  const totalPercentageChange = firstEntry?.total > 0
    ? ((totalChange / firstEntry.total) * 100).toFixed(1)
    : '0';

  // Market share data from latest entry
  const marketShareData = providers.map(provider => ({
    name: provider,
    value: lastEntry?.providers[provider] || 0,
    color: PROVIDER_COLORS[provider] || '#888888'
  })).filter(item => item.value > 0).sort((a, b) => b.value - a.value);

  // Growth data per provider
  const growthData = providers.map(provider => {
    const latestCount = lastEntry?.providers[provider] || 0;
    const firstCount = firstEntry?.providers[provider] || 0;
    const change = latestCount - firstCount;
    const percentageChange = firstCount > 0 ? ((change / firstCount) * 100) : 0;
    const marketShare = lastEntry?.total > 0
      ? ((latestCount / lastEntry.total) * 100)
      : 0;
    return {
      provider,
      current: latestCount,
      initial: firstCount,
      change,
      percentageChange,
      marketShare,
      color: PROVIDER_COLORS[provider] || '#888888'
    };
  }).sort((a, b) => b.current - a.current);

  // Weekly change data for bar chart
  const weeklyChangeData = history.slice(1).map((entry, idx) => {
    const prevEntry = history[idx];
    const data: { [key: string]: any } = {
      week: entry.week_label
    };
    providers.forEach(provider => {
      const current = entry.providers[provider] || 0;
      const prev = prevEntry.providers[provider] || 0;
      data[provider] = current - prev;
    });
    data.total = entry.total - prevEntry.total;
    return data;
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      <div className="bg-card rounded-t-xl sm:rounded-lg shadow-xl w-full sm:max-w-6xl max-h-[85vh] sm:max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-border flex justify-between items-center">
          <div>
            <h2 className="text-lg sm:text-xl font-bold text-foreground">{municipalityName}</h2>
            <p className="text-xs sm:text-sm text-muted-foreground">Marktaandeel en groei per vervoerder</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 -mr-2 text-subtle-foreground hover:text-muted-foreground hover:bg-secondary rounded-full transition"
            aria-label="Sluiten"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
          {/* Summary stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            <div className="bg-accent rounded-lg p-3 sm:p-4">
              <div className="text-xl sm:text-2xl font-bold text-accent-foreground">{lastEntry?.total || 0}</div>
              <div className="text-xs sm:text-sm text-primary">Totaal pakketpunten</div>
            </div>
            <div className={`rounded-lg p-3 sm:p-4 ${totalChange >= 0 ? 'bg-success-muted' : 'bg-destructive-muted'}`}>
              <div className={`text-xl sm:text-2xl font-bold ${totalChange >= 0 ? 'text-success' : 'text-destructive'}`}>
                {totalChange >= 0 ? '+' : ''}{totalChange}
              </div>
              <div className={`text-xs sm:text-sm ${totalChange >= 0 ? 'text-success' : 'text-destructive'}`}>
                Sinds {firstEntry?.week_label}
              </div>
            </div>
            <div className={`rounded-lg p-3 sm:p-4 ${Number(totalPercentageChange) >= 0 ? 'bg-success-muted' : 'bg-destructive-muted'}`}>
              <div className={`text-xl sm:text-2xl font-bold ${Number(totalPercentageChange) >= 0 ? 'text-success' : 'text-destructive'}`}>
                {Number(totalPercentageChange) >= 0 ? '+' : ''}{totalPercentageChange}%
              </div>
              <div className={`text-xs sm:text-sm ${Number(totalPercentageChange) >= 0 ? 'text-success' : 'text-destructive'}`}>
                Totale groei
              </div>
            </div>
            <div className="bg-muted rounded-lg p-3 sm:p-4">
              <div className="text-xl sm:text-2xl font-bold text-foreground">{providers.length}</div>
              <div className="text-xs sm:text-sm text-muted-foreground">Vervoerders</div>
            </div>
          </div>

          {/* Market Share and Growth Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            {/* Pie Chart - Market Share */}
            <Card>
              <h3 className="font-semibold text-foreground mb-3 sm:mb-4 text-sm sm:text-base">
                Marktaandeel per vervoerder
              </h3>
              <div className="h-48 sm:h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={marketShareData}
                    layout="vertical"
                    margin={{ top: 4, right: 56, bottom: 4, left: 4 }}
                  >
                    <CartesianGrid horizontal={false} stroke="#e5e7eb" />
                    <XAxis type="number" hide />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={72}
                      tick={{ fontSize: 11, fill: '#4b5563' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      formatter={(value: number) => [value.toLocaleString('nl-NL'), 'Pakketpunten']}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={14}>
                      {marketShareData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                      <LabelList
                        dataKey="value"
                        position="right"
                        formatter={(value: React.ReactNode) =>
                          Number(value).toLocaleString('nl-NL')
                        }
                        style={{ fontSize: 11, fill: '#4b5563' }}
                      />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Growth Summary per Provider */}
            <Card>
              <h3 className="font-semibold text-foreground mb-3 sm:mb-4 text-sm sm:text-base">
                Groei per vervoerder
              </h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {growthData.map(item => (
                  <div key={item.provider} className="flex items-center justify-between p-2 bg-muted rounded-lg">
                    <div className="flex items-center gap-2">
                      {PROVIDER_LOGOS[item.provider] ? (
                        <img
                          src={PROVIDER_LOGOS[item.provider]}
                          alt={item.provider}
                          className="w-6 h-6 object-contain"
                        />
                      ) : (
                        <div
                          className="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold"
                          style={{ backgroundColor: item.color }}
                        >
                          {item.provider.substring(0, 2)}
                        </div>
                      )}
                      <span className="font-medium text-foreground text-sm">{item.provider}</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <span className="text-muted-foreground">{item.current.toLocaleString('nl-NL')}</span>
                      <span className={`font-medium ${item.change >= 0 ? 'text-success' : 'text-destructive'}`}>
                        {item.change >= 0 ? '+' : ''}{item.change}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        item.percentageChange >= 0 ? 'bg-success-muted text-success' : 'bg-destructive-muted text-destructive'
                      }`}>
                        {item.percentageChange >= 0 ? '+' : ''}{item.percentageChange.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* All Providers Line Chart */}
          <Card>
            <h3 className="font-semibold text-foreground mb-3 sm:mb-4 text-sm sm:text-base">Ontwikkeling alle vervoerders over tijd</h3>
            <div className="h-48 sm:h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="week"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => value.split('-')[1]}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                    labelFormatter={(label) => `Week ${label}`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="total"
                    name="Totaal"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6', strokeWidth: 2 }}
                  />
                  {providers.map(provider => (
                    <Line
                      key={provider}
                      type="monotone"
                      dataKey={provider}
                      name={provider}
                      stroke={PROVIDER_COLORS[provider] || '#888888'}
                      strokeWidth={1.5}
                      dot={{ fill: PROVIDER_COLORS[provider] || '#888888', strokeWidth: 1 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Weekly Changes Stacked Bar Chart */}
          <Card>
            <h3 className="font-semibold text-foreground mb-3 sm:mb-4 text-sm sm:text-base">
              Wekelijkse verandering per vervoerder
            </h3>
            {weeklyChangeData.length > 0 ? (
              <div className="h-48 sm:h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weeklyChangeData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                      dataKey="week"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => value?.split('-')[1] || value}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'white',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        fontSize: '12px'
                      }}
                      labelFormatter={(label) => `Week ${label}`}
                      formatter={(value: number, name: string) => [
                        `${value >= 0 ? '+' : ''}${value}`,
                        name
                      ]}
                    />
                    <Legend />
                    {providers.map(provider => (
                      <Bar
                        key={provider}
                        dataKey={provider}
                        name={provider}
                        fill={PROVIDER_COLORS[provider] || '#888888'}
                        stackId="a"
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-subtle-foreground text-sm">
                Onvoldoende historische data beschikbaar om grafiek te tonen
              </div>
            )}
          </Card>

          {/* History table */}
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-border bg-muted">
              <h3 className="font-semibold text-foreground">Wekelijkse data</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted border-b border-border">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">Week</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase">Periode</th>
                    {providers.map(provider => (
                      <th key={provider} className="px-4 py-3 text-center text-xs font-semibold text-muted-foreground uppercase">
                        {provider}
                      </th>
                    ))}
                    <th className="px-4 py-3 text-center text-xs font-semibold text-foreground uppercase bg-secondary">Totaal</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-muted-foreground uppercase">Verschil</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {[...history].reverse().map((entry, idx, arr) => {
                    const prevEntry = arr[idx + 1];
                    const diff = prevEntry ? entry.total - prevEntry.total : 0;

                    return (
                      <tr key={entry.date} className="hover:bg-muted">
                        <td className="px-4 py-3 whitespace-nowrap font-medium text-foreground">
                          {entry.week_label}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-muted-foreground text-xs">
                          {formatDateRange(entry.date_from, entry.date_to)}
                        </td>
                        {providers.map(provider => (
                          <td key={provider} className="px-4 py-3 text-center text-foreground">
                            {entry.providers[provider] || <span className="text-subtle-foreground">-</span>}
                          </td>
                        ))}
                        <td className="px-4 py-3 text-center font-semibold text-foreground bg-muted">
                          {entry.total}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {idx < arr.length - 1 ? (
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              diff > 0 ? 'bg-success-muted text-success' :
                              diff < 0 ? 'bg-destructive-muted text-destructive' :
                              'bg-muted text-subtle-foreground'
                            }`}>
                              {diff > 0 ? '+' : ''}{diff}
                            </span>
                          ) : (
                            <span className="text-subtle-foreground">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-4 sm:px-6 py-3 sm:py-4 border-t border-border bg-muted">
          <button
            onClick={onClose}
            className="w-full px-4 py-3 sm:py-2 bg-primary text-white rounded-lg hover:bg-primary/90 active:bg-primary/80 transition font-medium text-base sm:text-sm"
          >
            Sluiten
          </button>
        </div>
      </div>
    </div>
  );
}

function formatDateRange(from: string, to: string): string {
  const fromDate = new Date(from);
  const toDate = new Date(to);

  const fromDay = fromDate.getDate();
  const toDay = toDate.getDate();
  const fromMonth = fromDate.toLocaleString('nl-NL', { month: 'short' });
  const toMonth = toDate.toLocaleString('nl-NL', { month: 'short' });

  if (fromMonth === toMonth) {
    return `${fromDay} - ${toDay} ${fromMonth}`;
  }
  return `${fromDay} ${fromMonth} - ${toDay} ${toMonth}`;
}
