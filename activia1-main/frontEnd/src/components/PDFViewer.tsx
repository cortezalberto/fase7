/**
 * Visor de PDF embebido usando iframe.
 *
 * Para una experiencia mas rica, considerar react-pdf en el futuro.
 *
 * Cortez72: Implementacion desde metodologia.md
 */

import { useState } from 'react';
import { Download, ExternalLink, X, Maximize2, Minimize2 } from 'lucide-react';

interface PDFViewerProps {
  /** URL del archivo PDF */
  url: string;
  /** Nombre del archivo para descargar */
  filename?: string;
  /** Callback para cerrar el visor */
  onClose?: () => void;
  /** Altura del visor */
  height?: string;
}

export function PDFViewer({
  url,
  filename = 'documento.pdf',
  onClose,
  height = '600px',
}: PDFViewerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
  };

  const handleOpenExternal = () => {
    window.open(url, '_blank');
  };

  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-black bg-opacity-90 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-2 bg-gray-900">
          <span className="text-white font-medium truncate">{filename}</span>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded"
              title="Descargar"
            >
              <Download className="w-5 h-5" />
            </button>
            <button
              onClick={handleOpenExternal}
              className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded"
              title="Abrir en nueva pestana"
            >
              <ExternalLink className="w-5 h-5" />
            </button>
            <button
              onClick={() => setIsFullscreen(false)}
              className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded"
              title="Salir de pantalla completa"
            >
              <Minimize2 className="w-5 h-5" />
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded"
                title="Cerrar"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* PDF iframe */}
        <iframe
          src={`${url}#toolbar=1&navpanes=1&scrollbar=1`}
          className="flex-1 w-full bg-gray-800"
          title={filename}
        />
      </div>
    );
  }

  return (
    <div className="border border-[var(--border-color)] rounded-lg overflow-hidden bg-[var(--bg-card)]">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 bg-[var(--bg-tertiary)] border-b border-[var(--border-color)]">
        <span className="text-sm font-medium truncate text-[var(--text-primary)]">{filename}</span>
        <div className="flex items-center gap-1">
          <button
            onClick={handleDownload}
            className="p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] rounded"
            title="Descargar"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsFullscreen(true)}
            className="p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] rounded"
            title="Pantalla completa"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] rounded"
              title="Cerrar"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* PDF iframe */}
      <iframe
        src={`${url}#toolbar=0&navpanes=0`}
        style={{ height }}
        className="w-full bg-[var(--bg-tertiary)]"
        title={filename}
      />
    </div>
  );
}
