/**
 * Componente para subir archivos PDF y otros formatos permitidos.
 *
 * Soporta drag & drop y selección tradicional.
 *
 * Cortez72: Implementación desde metodologia.md
 * Cortez92: Fixed setTimeout memory leak with useRef cleanup
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, X, FileText, Image, Loader2, Check, AlertCircle } from 'lucide-react';
import { filesService } from '@/services/api/files.service';

interface FileUploaderProps {
  /** ID del apunte o unidad destino */
  targetId: string;
  /** Tipo de destino: 'apuntes' o 'unidad' */
  targetType: 'apuntes' | 'unidad';
  /** Callback al subir archivo exitosamente */
  onUploadSuccess?: (archivo: { id: string; nombre: string; url: string }) => void;
  /** Callback en error */
  onUploadError?: (error: string) => void;
  /** Tipos MIME permitidos */
  acceptedTypes?: string[];
  /** Tamaño máximo en MB */
  maxSizeMB?: number;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

interface PendingFile {
  file: File;
  validationError: string | null;
}

export function FileUploader({
  targetId,
  targetType,
  onUploadSuccess,
  onUploadError,
  acceptedTypes = ['application/pdf', 'image/png', 'image/jpeg'],
  maxSizeMB = 50,
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Cortez92: Track timeouts to prevent memory leaks on unmount
  const timeoutsRef = useRef<Set<ReturnType<typeof setTimeout>>>(new Set());

  // Cleanup all timeouts on unmount
  useEffect(() => {
    return () => {
      timeoutsRef.current.forEach(clearTimeout);
      timeoutsRef.current.clear();
    };
  }, []);

  const validateFile = useCallback((file: File): string | null => {
    if (!acceptedTypes.includes(file.type)) {
      return `Tipo no permitido: ${file.type}. Usa PDF o imagenes.`;
    }

    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > maxSizeMB) {
      return `Archivo muy grande: ${sizeMB.toFixed(1)}MB. Maximo: ${maxSizeMB}MB`;
    }

    return null;
  }, [acceptedTypes, maxSizeMB]);

  const uploadFile = useCallback(async (file: File) => {
    // FIX HIGH-003 Cortez77: Validar targetId antes de intentar subir
    if (!targetId || targetId.trim() === '') {
      const errorMsg = 'Target ID no especificado';
      onUploadError?.(errorMsg);
      return;
    }

    const validationError = validateFile(file);
    if (validationError) {
      setUploadingFiles(prev => [
        ...prev,
        { file, progress: 0, status: 'error', error: validationError }
      ]);
      onUploadError?.(validationError);
      return;
    }

    // Añadir a la lista de subida
    setUploadingFiles(prev => [
      ...prev,
      { file, progress: 0, status: 'uploading' }
    ]);

    try {
      const result = targetType === 'apuntes'
        ? await filesService.uploadToApuntes(targetId, file)
        : await filesService.uploadToUnidad(targetId, file);

      // Actualizar estado a éxito
      setUploadingFiles(prev =>
        prev.map(uf =>
          uf.file === file
            ? { ...uf, progress: 100, status: 'success' }
            : uf
        )
      );

      onUploadSuccess?.({
        id: result.id,
        nombre: result.nombre_original,
        url: result.url,
      });

      // Cortez92: Track timeout for cleanup on unmount
      const timeoutId = setTimeout(() => {
        setUploadingFiles(prev => prev.filter(uf => uf.file !== file));
        timeoutsRef.current.delete(timeoutId);
      }, 2000);
      timeoutsRef.current.add(timeoutId);

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Error al subir archivo';

      setUploadingFiles(prev =>
        prev.map(uf =>
          uf.file === file
            ? { ...uf, status: 'error', error: errorMsg }
            : uf
        )
      );

      onUploadError?.(errorMsg);
    }
  }, [targetId, targetType, validateFile, onUploadSuccess, onUploadError]);

  // Agregar archivos a la lista pendiente (sin subir aún)
  const addPendingFiles = useCallback((files: File[]) => {
    const newPending = files.map(file => ({
      file,
      validationError: validateFile(file),
    }));
    setPendingFiles(prev => [...prev, ...newPending]);
  }, [validateFile]);

  // Subir todos los archivos pendientes válidos
  const uploadAllPending = useCallback(async () => {
    const validFiles = pendingFiles.filter(pf => !pf.validationError);
    if (validFiles.length === 0) return;

    setIsUploading(true);

    for (const pf of validFiles) {
      await uploadFile(pf.file);
    }

    // Limpiar archivos pendientes que se subieron exitosamente
    setPendingFiles(prev => prev.filter(pf => pf.validationError !== null));
    setIsUploading(false);
  }, [pendingFiles, uploadFile]);

  // Remover archivo pendiente
  const removePendingFile = useCallback((file: File) => {
    setPendingFiles(prev => prev.filter(pf => pf.file !== file));
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    addPendingFiles(files);
  }, [addPendingFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    addPendingFiles(files);

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [addPendingFiles]);

  const removeUploadingFile = useCallback((file: File) => {
    setUploadingFiles(prev => prev.filter(uf => uf.file !== file));
  }, []);

  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf') {
      return <FileText className="w-5 h-5 text-red-500" />;
    }
    return <Image className="w-5 h-5 text-blue-500" />;
  };

  return (
    <div className="space-y-4">
      {/* Zona de Drop */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
          transition-colors duration-200
          ${isDragging
            ? 'border-indigo-500 bg-indigo-500/20'
            : 'border-[var(--border-color)] hover:border-indigo-400 hover:bg-[var(--bg-hover)]'
          }
        `}
      >
        <Upload className={`w-8 h-8 mx-auto mb-2 ${isDragging ? 'text-indigo-400' : 'text-[var(--text-muted)]'}`} />
        <p className="text-sm text-[var(--text-secondary)]">
          <span className="font-medium text-indigo-400">Haz clic para seleccionar</span>
          {' '}o arrastra archivos aqui
        </p>
        <p className="text-xs text-[var(--text-muted)] mt-1">
          PDF, PNG, JPG hasta {maxSizeMB}MB
        </p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={acceptedTypes.join(',')}
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Lista de archivos pendientes (antes de subir) */}
      {pendingFiles.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-[var(--text-secondary)]">
            Archivos seleccionados ({pendingFiles.length}):
          </p>
          {pendingFiles.map((pf, index) => (
            <div
              key={`pending-${pf.file.name}-${index}`}
              className={`
                flex items-center gap-3 p-3 rounded-lg border
                ${pf.validationError
                  ? 'bg-red-500/20 border-red-500/30'
                  : 'bg-[var(--bg-tertiary)] border-[var(--border-color)]'}
              `}
            >
              {getFileIcon(pf.file)}

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate text-[var(--text-primary)]">{pf.file.name}</p>
                <p className={`text-xs ${pf.validationError ? 'text-red-400' : 'text-[var(--text-muted)]'}`}>
                  {pf.validationError || filesService.formatFileSize(pf.file.size)}
                </p>
              </div>

              <button
                onClick={() => removePendingFile(pf.file)}
                className="p-1 hover:bg-[var(--bg-hover)] rounded"
                title="Quitar archivo"
              >
                <X className="w-4 h-4 text-[var(--text-muted)]" />
              </button>
            </div>
          ))}

          {/* Botón de subir */}
          <button
            onClick={uploadAllPending}
            disabled={isUploading || pendingFiles.every(pf => pf.validationError !== null)}
            className={`
              w-full py-2.5 px-4 rounded-lg font-medium text-sm
              flex items-center justify-center gap-2
              transition-colors duration-200
              ${isUploading || pendingFiles.every(pf => pf.validationError !== null)
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 text-white'}
            `}
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Subiendo...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Subir Archivos ({pendingFiles.filter(pf => !pf.validationError).length})
              </>
            )}
          </button>
        </div>
      )}

      {/* Lista de archivos en subida */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          {uploadingFiles.map((uf, index) => (
            <div
              key={`${uf.file.name}-${index}`}
              className={`
                flex items-center gap-3 p-3 rounded-lg border
                ${uf.status === 'error' ? 'bg-red-500/20 border-red-500/30' : 'bg-[var(--bg-tertiary)] border-[var(--border-color)]'}
              `}
            >
              {getFileIcon(uf.file)}

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate text-[var(--text-primary)]">{uf.file.name}</p>
                <p className="text-xs text-[var(--text-muted)]">
                  {filesService.formatFileSize(uf.file.size)}
                </p>
              </div>

              {uf.status === 'uploading' && (
                <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
              )}

              {uf.status === 'success' && (
                <Check className="w-5 h-5 text-green-400" />
              )}

              {uf.status === 'error' && (
                <>
                  <AlertCircle className="w-5 h-5 text-red-400" />
                  <button
                    onClick={() => removeUploadingFile(uf.file)}
                    className="p-1 hover:bg-red-500/20 rounded"
                  >
                    <X className="w-4 h-4 text-red-400" />
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
