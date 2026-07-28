'use client';

import { HistorySnapshot } from '@/types/history';
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
  BarChart,
  Bar
} from 'recharts';
import { Card } from '@/components/ui/card';

interface ProviderHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  providerName: string;
  snapshots: HistorySnapshot[];
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

export default function ProviderHistoryModal({
  isOpen,
  onClose,
  providerName,
  snapshots
}: ProviderHistoryModalProps) {
  if (!isOpen) return null;

  // Prepare chart data from snapshots
  const chartData = snapshots.map(snapshot => ({
    week: snapshot.week_label,
    date: snapshot.date,
    count: snapshot.totals.providers[providerName] || 0,
    total: snapshot.totals.total
  }));

  // Calculate statistics
  const firstEntry = chartData[0];
  const lastEntry = chartData[chartData.length - 1];
  const totalChange = lastEntry ? lastEntry.count - (firstEntry?.count || 0) : 0;
  const percentageChange = firstEntry?.count > 0
    ? ((totalChange / firstEntry.count) * 100).toFixed(1)
    : '0';

  // Calculate weekly changes for bar chart
  const weeklyChanges = chartData.map((entry, idx) => {
    const prevEntry = chartData[idx - 1];
    return {
      week: entry.week,
      change: prevEntry ? entry.count - prevEntry.count : 0
    };
  }).slice(1); // Remove first entry (no previous to compare)

  // Calculate market share over time
  const marketShareData = chartData.map(entry => ({
    week: entry.week,
    share: entry.total > 0 ? ((entry.count / entry.total) * 100).toFixed(1) : 0
  }));

  const providerColor = PROVIDER_COLORS[providerName] || '#888888';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      <div className="bg-card rounded-t-xl sm:rounded-lg shadow-xl w-full sm:max-w-6xl max-h-[85vh] sm:max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-border flex justify-between items-center">
          <div className="flex items-center gap-3">
            {PROVIDER_LOGOS[providerName] ? (
              <img
                src={PROVIDER_LOGOS[providerName]}
                alt={providerName}
                className="w-10 h-10 object-contain"
              />
            ) : (
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: providerColor }}
              >
                <span className="text-white font-bold text-sm">
                  {providerName.substring(0, 2)}
                </span>
              </div>
            )}
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-foreground">{providerName}</h2>
              <p className="text-xs sm:text-sm text-muted-foreground">Historische ontwikkeling pakketpunten</p>
            </div>
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
              <div className="text-xl sm:text-2xl font-bold text-accent-foreground">
                {lastEntry?.count.toLocaleString('nl-NL') || 0}
              </div>
              <div className="text-xs sm:text-sm text-primary">Huidige stand</div>
            </div>
            <div className={`rounded-lg p-3 sm:p-4 ${totalChange >= 0 ? 'bg-success-muted' : 'bg-destructive-muted'}`}>
              <div className={`text-xl sm:text-2xl font-bold ${totalChange >= 0 ? 'text-success' : 'text-destructive'}`}>
                {totalChange >= 0 ? '+' : ''}{totalChange.toLocaleString('nl-NL')}
              </div>
              <div className={`text-xs sm:text-sm ${totalChange >= 0 ? 'text-success' : 'text-destructive'}`}>
                Sinds {firstEntry?.week}
              </div>
            </div>
            <div className={`rounded-lg p-3 sm:p-4 ${Number(percentageChange) >= 0 ? 'bg-success-muted' : 'bg-destructive-muted'}`}>
              <div className={`text-xl sm:text-2xl font-bold ${Number(percentageChange) >= 0 ? 'text-success' : 'text-destructive'}`}>
                {Number(percentageChange) >= 0 ? '+' : ''}{percentageChange}%
              </div>
              <div className={`text-xs sm:text-sm ${Number(percentageChange) >= 0 ? 'text-success' : 'text-destructive'}`}>
                Groei percentage
              </div>
            </div>
            <div className="bg-muted rounded-lg p-3 sm:p-4">
              <div className="text-xl sm:text-2xl font-bold text-foreground">
                {marketShareData[marketShareData.length - 1]?.share || 0}%
              </div>
              <div className="text-xs sm:text-sm text-muted-foreground">Marktaandeel</div>
            </div>
          </div>

          {/* Main Line Chart */}
          <Card>
            <h3 className="font-semibold text-foreground mb-3 sm:mb-4 text-sm sm:text-base">
              Aantal pakketpunten over tijd
            </h3>
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
                    formatter={(value: number) => [value.toLocaleString('nl-NL'), providerName]}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="count"
                    name={providerName}
                    stroke={providerColor}
                    strokeWidth={2}
                    dot={{ fill: providerColor, strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Weekly Changes Bar Chart */}
          {weeklyChanges.length > 0 && (
            <Card>
              <h3 className="font-semibold text-foreground mb-3 sm:mb-4 text-sm sm:text-base">
                Wekelijkse verandering
              </h3>
              <div className="h-40 sm:h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weeklyChanges} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
                      formatter={(value: number) => [
                        `${value >= 0 ? '+' : ''}${value}`,
                        'Verandering'
                      ]}
                    />
                    <Bar
                      dataKey="change"
                      fill={providerColor}
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

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
                    <th className="px-4 py-3 text-center text-xs font-semibold text-foreground uppercase bg-secondary">
                      Pakketpunten
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-muted-foreground uppercase">Verschil</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-muted-foreground uppercase">Marktaandeel</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {[...snapshots].reverse().map((snapshot, idx, arr) => {
                    const count = snapshot.totals.providers[providerName] || 0;
                    const prevSnapshot = arr[idx + 1];
                    const prevCount = prevSnapshot?.totals.providers[providerName] || 0;
                    const diff = idx < arr.length - 1 ? count - prevCount : 0;
                    const share = snapshot.totals.total > 0
                      ? ((count / snapshot.totals.total) * 100).toFixed(1)
                      : '0';

                    return (
                      <tr key={snapshot.date} className="hover:bg-muted">
                        <td className="px-4 py-3 whitespace-nowrap font-medium text-foreground">
                          {snapshot.week_label}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-muted-foreground text-xs">
                          {formatDateRange(snapshot.date_from, snapshot.date_to)}
                        </td>
                        <td className="px-4 py-3 text-center font-semibold text-foreground bg-muted">
                          {count.toLocaleString('nl-NL')}
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
                        <td className="px-4 py-3 text-center text-muted-foreground">
                          {share}%
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
