'use client';

import { useState, useEffect, useRef } from 'react';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  municipality: string;
  municipalityName: string;
}

export default function ShareModal({ isOpen, onClose, municipality, municipalityName }: ShareModalProps) {
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedEmbed, setCopiedEmbed] = useState(false);
  const [embedWidth, setEmbedWidth] = useState('100%');
  const [embedHeight, setEmbedHeight] = useState('500');
  const modalRef = useRef<HTMLDivElement>(null);

  const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
  const shareUrl = `${baseUrl}/?gemeente=${municipality}`;
  const embedUrl = `${baseUrl}/embed?gemeente=${municipality}`;
  const embedCode = `<iframe src="${embedUrl}" width="${embedWidth}" height="${embedHeight}" frameborder="0" style="border:0;border-radius:8px;" allowfullscreen></iframe>`;

  useEffect(() => {
    if (!isOpen) {
      setCopiedLink(false);
      setCopiedEmbed(false);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const copyToClipboard = async (text: string, type: 'link' | 'embed') => {
    try {
      await navigator.clipboard.writeText(text);
      if (type === 'link') {
        setCopiedLink(true);
        setTimeout(() => setCopiedLink(false), 2000);
      } else {
        setCopiedEmbed(true);
        setTimeout(() => setCopiedEmbed(false), 2000);
      }
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      if (type === 'link') {
        setCopiedLink(true);
        setTimeout(() => setCopiedLink(false), 2000);
      } else {
        setCopiedEmbed(true);
        setTimeout(() => setCopiedEmbed(false), 2000);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        ref={modalRef}
        className="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Delen</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Share link */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Directe link naar {municipalityName}
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                readOnly
                value={shareUrl}
                className="flex-1 px-3 py-2 text-sm bg-gray-50 border border-gray-300 rounded-lg text-gray-700 font-mono select-all"
                onClick={(e) => (e.target as HTMLInputElement).select()}
              />
              <button
                onClick={() => copyToClipboard(shareUrl, 'link')}
                className={`px-3 py-2 text-sm font-medium rounded-lg transition whitespace-nowrap ${
                  copiedLink
                    ? 'bg-green-100 text-green-700'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {copiedLink ? 'Gekopieerd!' : 'Kopieer'}
              </button>
            </div>
          </div>

          {/* Embed code */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Embed code
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Plak deze code op je website om de kaart van {municipalityName} in te sluiten.
            </p>

            {/* Size controls */}
            <div className="flex gap-3 mb-2">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">Breedte</label>
                <select
                  value={embedWidth}
                  onChange={(e) => setEmbedWidth(e.target.value)}
                  className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-lg bg-white"
                >
                  <option value="100%">100%</option>
                  <option value="800">800px</option>
                  <option value="600">600px</option>
                  <option value="400">400px</option>
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">Hoogte</label>
                <select
                  value={embedHeight}
                  onChange={(e) => setEmbedHeight(e.target.value)}
                  className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-lg bg-white"
                >
                  <option value="400">400px</option>
                  <option value="500">500px</option>
                  <option value="600">600px</option>
                  <option value="800">800px</option>
                </select>
              </div>
            </div>

            <div className="relative">
              <pre className="px-3 py-2 text-xs bg-gray-50 border border-gray-300 rounded-lg text-gray-700 font-mono overflow-x-auto whitespace-pre-wrap break-all">
                {embedCode}
              </pre>
              <button
                onClick={() => copyToClipboard(embedCode, 'embed')}
                className={`absolute top-2 right-2 px-2 py-1 text-xs font-medium rounded transition ${
                  copiedEmbed
                    ? 'bg-green-100 text-green-700'
                    : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {copiedEmbed ? 'Gekopieerd!' : 'Kopieer'}
              </button>
            </div>
          </div>

          {/* Preview */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Voorbeeld
            </label>
            <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-100" style={{ height: '250px' }}>
              <iframe
                src={embedUrl}
                width="100%"
                height="100%"
                style={{ border: 0 }}
                title={`Pakketpunten ${municipalityName}`}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
