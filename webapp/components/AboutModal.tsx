'use client';

import { useState } from 'react';

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AboutModal({ isOpen, onClose }: AboutModalProps) {
  const [activeTab, setActiveTab] = useState<'about' | 'sources' | 'usage' | 'rapport' | 'acm'>('about');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className={`bg-white rounded-lg shadow-xl w-full overflow-hidden flex flex-col transition-all duration-300 ${
        activeTab === 'acm' ? 'max-w-[90vw] max-h-[95vh]' : 'max-w-3xl max-h-[90vh]'
      }`}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">Over dit project</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            aria-label="Sluiten"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 px-6">
          <button
            onClick={() => setActiveTab('about')}
            className={`py-3 px-4 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'about'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Over
          </button>
          <button
            onClick={() => setActiveTab('sources')}
            className={`py-3 px-4 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'sources'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Data Bronnen
          </button>
          <button
            onClick={() => setActiveTab('usage')}
            className={`py-3 px-4 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'usage'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Gebruik
          </button>
          <button
            onClick={() => setActiveTab('rapport')}
            className={`py-3 px-4 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'rapport'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Rapport
          </button>
          <button
            onClick={() => setActiveTab('acm')}
            className={`py-3 px-4 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'acm'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            ACM Monitor
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {activeTab === 'about' && (
            <div className="space-y-4">
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Pakketpunten Nederland</h3>
                <p className="text-gray-700 text-sm leading-relaxed">
                  Een interactief visualisatieplatform voor pakketpuntlocaties in Nederland.
                  Dit project verzamelt publieke data van meerdere vervoerders en toont deze
                  op een overzichtelijke kaart met filteropties en statistieken.
                </p>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-2">Features</h4>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  <li>Interactieve kaart met 940+ pakketpunten (POC: 5 gemeentes)</li>
                  <li>Real-time filtering op vervoerder en locatie eigenschappen</li>
                  <li>Dekkingsgebied visualisatie (300m en 500m buffers)</li>
                  <li>Statistieken per gemeente en vervoerder</li>
                  <li>Responsive design voor desktop en mobiel</li>
                </ul>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-2">Technologie</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="font-medium text-gray-700">Frontend</p>
                    <ul className="text-gray-600 mt-1 space-y-0.5">
                      <li>• Next.js 16 (App Router)</li>
                      <li>• React + TypeScript</li>
                      <li>• Leaflet + React-Leaflet</li>
                      <li>• Tailwind CSS</li>
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium text-gray-700">Backend</p>
                    <ul className="text-gray-600 mt-1 space-y-0.5">
                      <li>• Python 3.11</li>
                      <li>• GeoPandas + Shapely</li>
                      <li>• REST API integratie</li>
                      <li>• GeoJSON export</li>
                    </ul>
                  </div>
                </div>
              </section>

              <section className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <h4 className="text-md font-semibold text-amber-900 mb-2 flex items-center">
                  <span className="mr-2">⚠️</span>
                  Mock Data Waarschuwing
                </h4>
                <p className="text-sm text-amber-800 leading-relaxed">
                  De <strong>bezettingsgraad</strong> (occupancy) data is willekeurig gegenereerd
                  voor demonstratiedoeleinden. Deze cijfers weerspiegelen geen echte capaciteit of
                  gebruik van pakketpunten en mogen niet gebruikt worden voor zakelijke beslissingen.
                </p>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-2">Open Source</h4>
                <p className="text-sm text-gray-700 leading-relaxed mb-2">
                  Dit project is open source en beschikbaar onder de MIT-licentie.
                </p>
                <a
                  href="https://github.com/Ida-BirdsEye/pakketpunten"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                  </svg>
                  View on GitHub
                </a>
              </section>
            </div>
          )}

          {activeTab === 'sources' && (
            <div className="space-y-4">
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Data Bronnen</h3>
                <p className="text-sm text-gray-700 mb-4">
                  Locatiegegevens worden verzameld van publieke API's en websites van de
                  betreffende vervoerders zonder authenticatie vereisten.
                </p>
              </section>

              <div className="space-y-3">
                <DataSourceCard
                  name="DHL Parcel Netherlands"
                  endpoint="api-gw.dhlparcel.nl/parcel-shop-locations"
                  type="Public REST API"
                  url="https://www.dhl.nl"
                  color="#FFCC00"
                />

                <DataSourceCard
                  name="PostNL"
                  endpoint="productprijslokatie.postnl.nl/location-widget"
                  type="Public REST API"
                  url="https://www.postnl.nl"
                  color="#FF6600"
                />

                <DataSourceCard
                  name="DPD Netherlands"
                  endpoint="pickup.dpd.cz/api/GetParcelShopsByAddress"
                  type="Public REST API (Cached)"
                  url="https://www.dpd.com/nl"
                  color="#DC0032"
                />

                <DataSourceCard
                  name="FedEx Netherlands"
                  endpoint="liveapi.yext.com/v2/accounts/me/entities"
                  type="Public REST API (Yext)"
                  url="https://www.fedex.com/nl"
                  color="#4D148C"
                />

                <DataSourceCard
                  name="VintedGo / Mondial Relay"
                  endpoint="vintedgo.com/nl/carrier-locations"
                  type="Web Scraping"
                  url="https://vintedgo.com"
                  color="#09B1BA"
                />

                <DataSourceCard
                  name="De Buren"
                  endpoint="mijnburen.deburen.nl/maps"
                  type="Web Scraping"
                  url="https://deburen.nl"
                  color="#4CAF50"
                />
              </div>

              <section className="border-t pt-4 mt-4">
                <h4 className="text-md font-semibold text-gray-900 mb-2">Aanvullende Bronnen</h4>
                <ul className="text-sm text-gray-700 space-y-2">
                  <li>
                    <strong>Gemeentegrenzen:</strong> OpenStreetMap / Nominatim
                    <span className="text-gray-500 ml-2">© OpenStreetMap contributors</span>
                  </li>
                  <li>
                    <strong>Bedrijfslogo's:</strong> Clearbit Logo API
                    <span className="text-gray-500 ml-2">© Respectieve merkhouders</span>
                  </li>
                  <li>
                    <strong>Kaartachtergrond:</strong> OpenStreetMap tiles
                    <span className="text-gray-500 ml-2">© OpenStreetMap contributors</span>
                  </li>
                </ul>
              </section>

              <section className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-blue-900 mb-2">Update Frequentie</h4>
                <p className="text-sm text-blue-800">
                  <strong>POC:</strong> Handmatige updates<br />
                  <strong>Productie (gepland):</strong> Wekelijkse automatische updates via GitHub Actions
                </p>
              </section>
            </div>
          )}

          {activeTab === 'usage' && (
            <div className="space-y-4">
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Toegestaan Gebruik</h3>
                <div className="space-y-2">
                  <UsageItem allowed>Persoonlijk onderzoek en analyse</UsageItem>
                  <UsageItem allowed>Educatieve doeleinden</UsageItem>
                  <UsageItem allowed>Niet-commerciële visualisatie</UsageItem>
                  <UsageItem allowed>Open-source ontwikkeling</UsageItem>
                  <UsageItem allowed>Academisch onderzoek</UsageItem>
                  <UsageItem allowed>Ruimtelijke planning studies</UsageItem>
                </div>
              </section>

              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Niet Toegestaan</h3>
                <div className="space-y-2">
                  <UsageItem allowed={false}>Commerciële verkoop of licentie van de data</UsageItem>
                  <UsageItem allowed={false}>Concurreren met bronvervoerders</UsageItem>
                  <UsageItem allowed={false}>Geautomatiseerde hoge-frequentie API verzoeken</UsageItem>
                  <UsageItem allowed={false}>Schending van vervoerders' gebruiksvoorwaarden</UsageItem>
                </div>
              </section>

              <section className="border-t pt-4 mt-4">
                <h4 className="text-md font-semibold text-gray-900 mb-2">Vereiste Attributie</h4>
                <p className="text-sm text-gray-700 mb-3">
                  Bij gebruik of redistributie van dit project moet de volgende attributie worden opgenomen:
                </p>
                <div className="bg-gray-50 border border-gray-200 rounded p-3 text-xs font-mono">
                  <pre className="whitespace-pre-wrap text-gray-800">
{`Data bronnen:
- DHL Parcel Netherlands (https://www.dhl.nl)
- PostNL (https://www.postnl.nl)
- DPD Netherlands (https://www.dpd.com/nl)
- FedEx Netherlands (https://www.fedex.com/nl)
- VintedGo / Mondial Relay (https://vintedgo.com)
- De Buren (https://deburen.nl)
- Gemeente grenzen © OpenStreetMap contributors
- Bedrijfslogo's © respectieve merkhouders

Bezettingsgraad data is willekeurig gegenereerd
voor demonstratie (niet echt)

Project: Pakketpunten Nederland
Repository: github.com/Ida-BirdsEye/pakketpunten
License: MIT`}
                  </pre>
                </div>
              </section>

              <section className="bg-gray-50 border border-gray-300 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-2">Disclaimer</h4>
                <p className="text-xs text-gray-700 leading-relaxed">
                  Dit project wordt geleverd "as is" zonder garantie van welke aard dan ook.
                  De data is verzameld van publieke bronnen en kan onnauwkeurigheden bevatten.
                  Locatiegegevens moeten worden geverifieerd bij de vervoerders voordat zakelijke
                  beslissingen worden genomen. Dit project is niet gelieerd aan, goedgekeurd door,
                  of gesponsord door een van de databronbedrijven.
                </p>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-2">Privacy & GDPR</h4>
                <p className="text-sm text-gray-700 mb-2">
                  Dit project verzamelt of slaat <strong>geen persoonlijke gegevens</strong> op:
                </p>
                <ul className="text-sm text-gray-700 space-y-1 ml-4">
                  <li>✅ Locatie adressen (publieke zakelijke locaties)</li>
                  <li>✅ Bedrijfsnamen (publieke informatie)</li>
                  <li>✅ Geografische coördinaten (publiek)</li>
                  <li>❌ Klantgegevens (niet verzameld)</li>
                  <li>❌ Transactiegegevens (niet verzameld)</li>
                  <li>❌ Gebruikersvolging (niet geïmplementeerd)</li>
                </ul>
              </section>

              <section className="border-t pt-4 mt-4">
                <h4 className="text-md font-semibold text-gray-900 mb-2">Meer Informatie</h4>
                <p className="text-sm text-gray-700">
                  Voor uitgebreide documentatie over databronnen, gebruiksrechten en
                  technische details, zie de volledige documentatie in de GitHub repository:
                </p>
                <div className="mt-2 space-y-1">
                  <a
                    href="https://github.com/Ida-BirdsEye/pakketpunten/blob/main/DATA_SOURCES.md"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-sm text-blue-600 hover:text-blue-800"
                  >
                    → DATA_SOURCES.md
                  </a>
                  <a
                    href="https://github.com/Ida-BirdsEye/pakketpunten/blob/main/README.md"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-sm text-blue-600 hover:text-blue-800"
                  >
                    → README.md
                  </a>
                  <a
                    href="https://github.com/Ida-BirdsEye/pakketpunten/blob/main/CLAUDE.md"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-sm text-blue-600 hover:text-blue-800"
                  >
                    → CLAUDE.md (Technical Documentation)
                  </a>
                </div>
              </section>
            </div>
          )}

          {activeTab === 'rapport' && (
            <div className="space-y-4">
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Inzichten en Effecten Pakketkluizen</h3>
                <p className="text-xs text-gray-500 mb-3">
                  Topsector Logistiek | Publicatie: 10 februari 2025 | Projectperiode: 16 september - 31 december 2024
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-blue-900 leading-relaxed">
                    Een onderzoek naar de inzet van pakketkluizen en alternatieve aflevermethoden
                    om gemeenten te ondersteunen bij strategische en praktische besluitvorming
                    rondom duurzame stedelijke logistiek en leefbare openbare ruimtes.
                  </p>
                </div>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-3">Doelstellingen</h4>
                <p className="text-sm text-gray-700 mb-3">
                  Het initiatief biedt gemeenten een <strong>neutraal kader</strong> dat zowel strategische
                  als praktische aspecten ondersteunt, met focus op:
                </p>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1.5">
                  <li>Duurzame stedelijke logistiek</li>
                  <li>Leefbare openbare ruimtes</li>
                  <li>Balans tussen pakketbezorging en stedelijke leefbaarheid</li>
                  <li>Ondersteuning bij plaatsing en beheer van pakketkluizen</li>
                </ul>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-3">Consortium & Stakeholders</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="font-medium text-gray-800 mb-2">Leidende Organisaties</p>
                    <ul className="text-gray-700 space-y-1">
                      <li>• Rebel</li>
                      <li>• PosadMaxwan</li>
                      <li>• Fishermen</li>
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium text-gray-800 mb-2">Deelnemende Gemeenten</p>
                    <ul className="text-gray-700 space-y-1">
                      <li>• Amsterdam</li>
                      <li>• Utrecht</li>
                      <li>• Den Haag</li>
                      <li>• Zwolle</li>
                      <li>• Rotterdam</li>
                      <li>• 's-Hertogenbosch</li>
                      <li>• Delft</li>
                    </ul>
                  </div>
                </div>
                <div className="mt-3">
                  <p className="font-medium text-gray-800 mb-2 text-sm">Overige Stakeholders</p>
                  <p className="text-sm text-gray-700">
                    <strong>Kluis aanbieders:</strong> De Buren, MyPup, CiPiO<br />
                    <strong>Vervoerders:</strong> DHL, PostNL<br />
                    <strong>Brancheverenigingen:</strong> Thuiswinkel.org<br />
                    <strong>Academische instellingen</strong>
                  </p>
                </div>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-3">Hoofdonderwerpen</h4>
                <div className="space-y-2">
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-blue-600 mr-3 text-lg">📊</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Marktoverzicht Pakketkluizen</p>
                      <p className="text-xs text-gray-600 mt-0.5">Analyse van verschillende kluis systemen en aanbieders</p>
                    </div>
                  </div>
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-blue-600 mr-3 text-lg">📦</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Categorisatie Afhaalpunten</p>
                      <p className="text-xs text-gray-600 mt-0.5">Overzicht en classificatie van verschillende type pakketpunten</p>
                    </div>
                  </div>
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-blue-600 mr-3 text-lg">📋</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Beleidskader Ontwikkeling</p>
                      <p className="text-xs text-gray-600 mt-0.5">Framework voor beleidsvorming rondom pakketlogistiek</p>
                    </div>
                  </div>
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-blue-600 mr-3 text-lg">🗺️</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Strategische Ruimtelijke Planning</p>
                      <p className="text-xs text-gray-600 mt-0.5">Richtlijnen voor optimale locatiebepaling</p>
                    </div>
                  </div>
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-blue-600 mr-3 text-lg">🛠️</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Stapsgewijze Implementatie</p>
                      <p className="text-xs text-gray-600 mt-0.5">Stappenplan voor plaatsing en beheer van pakketkluizen</p>
                    </div>
                  </div>
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-blue-600 mr-3 text-lg">🚚</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Alternatieve Bezorgmethoden</p>
                      <p className="text-xs text-gray-600 mt-0.5">Overzicht van alternatieven voor thuisbezorging</p>
                    </div>
                  </div>
                </div>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-3">Kernbevinding</h4>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <p className="text-sm text-amber-900 leading-relaxed">
                    Het onderzoek erkent de <strong>tegenstrijdige belangen</strong> tussen stakeholders:
                  </p>
                  <ul className="mt-2 space-y-1.5 text-sm text-amber-900">
                    <li><strong>Consumenten:</strong> Prioriteit aan gemak en bereikbaarheid</li>
                    <li><strong>Vervoerders:</strong> Voorkeur voor efficiënte bezorgoplossingen</li>
                    <li><strong>Gemeenten:</strong> Balans tussen ruimtebeperking en bewonersbelangen</li>
                  </ul>
                </div>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-3">Context & Urgentie</h4>
                <p className="text-sm text-gray-700 leading-relaxed mb-2">
                  De groei van e-commerce leidt tot een <strong>toenemende druk op de stedelijke ruimte</strong>
                  door pakketbezorging. Dit onderzoek helpt gemeenten om:
                </p>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  <li>Weloverwogen en strategische beslissingen te nemen</li>
                  <li>Een gezonde, veilige en duurzame stedelijke omgeving te creëren</li>
                  <li>Effectief te reageren op logistieke uitdagingen</li>
                  <li>Samenwerking met bedrijven te faciliteren</li>
                  <li>Financiële aspecten in overweging te nemen</li>
                </ul>
              </section>

              <section className="border-t pt-4">
                <h4 className="text-md font-semibold text-gray-900 mb-3">Rapport Downloaden</h4>
                <a
                  href="https://topsectorlogistiek.nl/wp-content/uploads/2025/02/250205_Eindrapportage.pdf"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download Eindrapportage (PDF)
                </a>
                <p className="text-xs text-gray-500 mt-2">
                  Publicatie: 250205_Eindrapportage.pdf | Topsector Logistiek
                </p>
              </section>

              <section className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-blue-900 mb-2">Meer Informatie</h4>
                <a
                  href="https://topsectorlogistiek.nl/kennisbank/inzichten-en-effecten-pakketkluizen/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-700 hover:text-blue-900 underline"
                >
                  Bezoek de officiële projectpagina op Topsector Logistiek →
                </a>
              </section>
            </div>
          )}

          {activeTab === 'acm' && (
            <div className="space-y-4">
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">ACM Post- en pakketmonitor</h3>
                <p className="text-xs text-gray-500 mb-3">
                  Autoriteit Consument & Markt (ACM) | Interactieve Dashboard
                </p>
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-orange-900 leading-relaxed">
                    De ACM Post- en pakketmonitor is een interactieve Tableau-dashboard die uitgebreide
                    data en statistieken biedt over de Nederlandse post- en pakketmarkt. Dit dashboard
                    wordt beheerd door de Autoriteit Consument & Markt en biedt inzicht in markttrends,
                    prestaties van vervoerders en ontwikkelingen in de sector.
                  </p>
                </div>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-3">Wat vindt u in de monitor?</h4>
                <div className="space-y-2">
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-orange-600 mr-3 text-lg">📈</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Marktstatistieken</p>
                      <p className="text-xs text-gray-600 mt-0.5">
                        Volumes, groeitrends en ontwikkelingen in de post- en pakketmarkt
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-orange-600 mr-3 text-lg">📦</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Pakketzendingen</p>
                      <p className="text-xs text-gray-600 mt-0.5">
                        Gedetailleerde cijfers over pakketbezorging en afhaalpunten
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-orange-600 mr-3 text-lg">🏢</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Marktspelers</p>
                      <p className="text-xs text-gray-600 mt-0.5">
                        Prestaties en marktaandelen van verschillende vervoerders
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-orange-600 mr-3 text-lg">⏱️</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Kwaliteitsindicatoren</p>
                      <p className="text-xs text-gray-600 mt-0.5">
                        Levertijden, klanttevredenheid en service kwaliteit
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start bg-gray-50 rounded-lg p-3">
                    <span className="text-orange-600 mr-3 text-lg">🗺️</span>
                    <div>
                      <p className="font-medium text-sm text-gray-900">Regionale Gegevens</p>
                      <p className="text-xs text-gray-600 mt-0.5">
                        Geografische spreiding en bereikbaarheid van diensten
                      </p>
                    </div>
                  </div>
                </div>
              </section>

              <section>
                <h4 className="text-md font-semibold text-gray-900 mb-3">Over de ACM</h4>
                <p className="text-sm text-gray-700 leading-relaxed mb-2">
                  De Autoriteit Consument & Markt (ACM) is de toezichthouder op de Nederlandse
                  markten. De ACM bevordert concurrentie en beschermt consumenten. In de post-
                  en pakketsector zorgt de ACM ervoor dat diensten toegankelijk, betaalbaar en
                  van goede kwaliteit blijven.
                </p>
                <p className="text-sm text-gray-700 leading-relaxed">
                  De Post- en pakketmonitor biedt transparantie over de markt en helpt
                  consumenten, bedrijven en beleidsmakers bij het maken van geïnformeerde beslissingen.
                </p>
              </section>

              <section className="border-t pt-4">
                <h4 className="text-md font-semibold text-gray-900 mb-3">Dashboard</h4>
                <div className="bg-gray-100 rounded-lg overflow-hidden border border-gray-300" style={{ height: '750px' }}>
                  <iframe
                    src="https://public.tableau.com/views/Post-enpakketmonitor/OVER?:language=en-US&:sid=&:display_count=n&:origin=viz_share_link&publish=yes&:showVizHome=no&:embed=true"
                    width="100%"
                    height="100%"
                    frameBorder="0"
                    allowFullScreen
                    className="w-full h-full"
                  />
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <p className="text-xs text-gray-500">
                    Interactieve Tableau dashboard | Autoriteit Consument & Markt
                  </p>
                  <a
                    href="https://public.tableau.com/views/Post-enpakketmonitor/OVER?%3Alanguage=en-US&%3Asid=&%3Adisplay_count=n&%3Aorigin=viz_share_link&publish=yes&%3AshowVizHome=no#1"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-orange-600 hover:text-orange-800 font-medium flex items-center"
                  >
                    Open in nieuw venster
                    <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </div>
              </section>

              <section className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-orange-900 mb-2">Let op</h4>
                <p className="text-xs text-orange-800 leading-relaxed">
                  De ACM monitor bevat officiële marktdata van de toezichthouder. Dit project
                  (Pakketpunten Nederland) is een onafhankelijk initiatief en niet gelieerd aan de ACM.
                  Voor officiële cijfers en rapportages verwijzen we u naar de ACM monitor.
                </p>
              </section>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
          >
            Sluiten
          </button>
        </div>
      </div>
    </div>
  );
}

// Helper component for data source cards
function DataSourceCard({
  name,
  endpoint,
  type,
  url,
  color
}: {
  name: string;
  endpoint: string;
  type: string;
  url: string;
  color: string;
}) {
  return (
    <div className="border border-gray-200 rounded-lg p-3 hover:border-gray-300 transition">
      <div className="flex items-start">
        <div
          className="w-4 h-4 rounded-full mt-0.5 mr-3 flex-shrink-0"
          style={{ backgroundColor: color }}
        />
        <div className="flex-1 min-w-0">
          <h5 className="font-semibold text-sm text-gray-900">{name}</h5>
          <p className="text-xs text-gray-600 mt-1">
            <span className="font-medium">Type:</span> {type}
          </p>
          <p className="text-xs text-gray-500 mt-0.5 font-mono break-all">
            {endpoint}
          </p>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-600 hover:text-blue-800 mt-1 inline-block"
          >
            {url} ↗
          </a>
        </div>
      </div>
    </div>
  );
}

// Helper component for usage items
function UsageItem({ allowed, children }: { allowed: boolean; children: React.ReactNode }) {
  return (
    <div className="flex items-start text-sm">
      <span className={`mr-2 mt-0.5 ${allowed ? 'text-green-600' : 'text-red-600'}`}>
        {allowed ? '✓' : '✗'}
      </span>
      <span className={allowed ? 'text-gray-700' : 'text-gray-600'}>{children}</span>
    </div>
  );
}
