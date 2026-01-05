/**
 * Servicio para gestión de archivos adjuntos.
 *
 * Cortez72: Implementación desde metodologia.md
 *
 * Subida, descarga y eliminación de archivos PDF y otros.
 */

import { BaseApiService } from './base.service';
import type {
  ArchivoAdjunto,
  ArchivoUploadResponse,
} from '@/types/domain/academic.types';

class FilesService extends BaseApiService {
  constructor() {
    super('/files');
  }

  /**
   * Sube un archivo a un apunte específico.
   */
  async uploadToApuntes(
    apuntesId: string,
    file: File,
    descripcion?: string
  ): Promise<ArchivoUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const queryParams = descripcion
      ? `?descripcion=${encodeURIComponent(descripcion)}`
      : '';

    const response = await this.client.post<{ data: ArchivoUploadResponse }>(
      `/files/upload/apuntes/${apuntesId}${queryParams}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.data;
  }

  /**
   * Sube un archivo a una unidad.
   */
  async uploadToUnidad(
    unidadId: string,
    file: File,
    descripcion?: string
  ): Promise<ArchivoUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const queryParams = descripcion
      ? `?descripcion=${encodeURIComponent(descripcion)}`
      : '';

    const response = await this.client.post<{ data: ArchivoUploadResponse }>(
      `/files/upload/unidad/${unidadId}${queryParams}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.data;
  }

  /**
   * Lista archivos de un apunte.
   */
  async getFilesByApuntes(apuntesId: string): Promise<ArchivoAdjunto[]> {
    return this.get<ArchivoAdjunto[]>(`/apuntes/${apuntesId}`);
  }

  /**
   * Lista archivos de una unidad.
   */
  async getFilesByUnidad(unidadId: string): Promise<ArchivoAdjunto[]> {
    return this.get<ArchivoAdjunto[]>(`/unidad/${unidadId}`);
  }

  /**
   * Alias for getFilesByUnidad (used by ContentManagementPage).
   */
  async getByUnidad(unidadId: string): Promise<ArchivoAdjunto[]> {
    return this.getFilesByUnidad(unidadId);
  }

  /**
   * Obtiene la URL de descarga de un archivo.
   */
  getDownloadUrl(path: string): string {
    return `/api/v1/files/download/${path}`;
  }

  /**
   * Elimina un archivo.
   */
  async deleteFile(archivoId: string): Promise<void> {
    return this.delete(`/${archivoId}`);
  }

  /**
   * Formatea tamano de archivo para mostrar.
   */
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
}

export const filesService = new FilesService();
