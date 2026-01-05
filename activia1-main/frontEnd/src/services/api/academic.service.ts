/**
 * Servicio para gestión de contenido académico.
 *
 * Cortez72: Implementación desde metodologia.md
 *
 * CRUD de materias, unidades y apuntes.
 */

import { BaseApiService } from './base.service';
import type {
  MateriaCreate,
  MateriaUpdate,
  MateriaResponse,
  MateriaConUnidades,
  UnidadCreate,
  UnidadUpdate,
  UnidadResponse,
  UnidadConApuntes,
  ApuntesCreate,
  ApuntesUpdate,
  ApuntesResponse,
} from '@/types/domain/academic.types';

class AcademicService extends BaseApiService {
  constructor() {
    super('/academic');
  }

  // ==================== Materias ====================

  async getMaterias(params?: {
    solo_activas?: boolean;
    incluir_unidades?: boolean;
  }): Promise<MateriaConUnidades[]> {
    const queryParams = new URLSearchParams();
    if (params?.solo_activas !== undefined) {
      queryParams.append('solo_activas', String(params.solo_activas));
    }
    if (params?.incluir_unidades !== undefined) {
      queryParams.append('incluir_unidades', String(params.incluir_unidades));
    }
    const query = queryParams.toString();
    return this.get<MateriaConUnidades[]>(`/materias${query ? `?${query}` : ''}`);
  }

  async getMateria(code: string): Promise<MateriaConUnidades> {
    return this.get<MateriaConUnidades>(`/materias/${code}`);
  }

  async createMateria(data: MateriaCreate): Promise<MateriaResponse> {
    return this.post<MateriaResponse>('/materias', data);
  }

  async updateMateria(code: string, data: MateriaUpdate): Promise<MateriaResponse> {
    return this.put<MateriaResponse>(`/materias/${code}`, data);
  }

  async deleteMateria(code: string): Promise<void> {
    return this.delete(`/materias/${code}`);
  }

  async toggleMateriaActive(code: string, isActive: boolean): Promise<MateriaResponse> {
    return this.put<MateriaResponse>(`/materias/${code}`, { is_active: isActive });
  }

  // ==================== Unidades ====================

  async createUnidad(data: UnidadCreate): Promise<UnidadResponse> {
    return this.post<UnidadResponse>('/unidades', data);
  }

  async getUnidad(
    id: string,
    incluirApuntes = true
  ): Promise<UnidadConApuntes> {
    return this.get<UnidadConApuntes>(
      `/unidades/${id}?incluir_apuntes=${incluirApuntes}`
    );
  }

  async updateUnidad(
    id: string,
    data: UnidadUpdate
  ): Promise<UnidadResponse> {
    return this.put<UnidadResponse>(`/unidades/${id}`, data);
  }

  async publicarUnidad(id: string): Promise<UnidadResponse> {
    return this.post<UnidadResponse>(`/unidades/${id}/publicar`);
  }

  async deleteUnidad(id: string): Promise<void> {
    return this.delete(`/unidades/${id}`);
  }

  // ==================== Apuntes ====================

  async createApuntes(
    unidadId: string,
    data: ApuntesCreate
  ): Promise<ApuntesResponse> {
    return this.post<ApuntesResponse>(`/unidades/${unidadId}/apuntes`, data);
  }

  async getApuntes(id: string): Promise<ApuntesResponse> {
    return this.get<ApuntesResponse>(`/apuntes/${id}`);
  }

  async updateApuntes(
    id: string,
    data: ApuntesUpdate
  ): Promise<ApuntesResponse> {
    return this.put<ApuntesResponse>(`/apuntes/${id}`, data);
  }

  async publicarApuntes(id: string): Promise<ApuntesResponse> {
    return this.post<ApuntesResponse>(`/apuntes/${id}/publicar`);
  }

  async deleteApuntes(id: string): Promise<void> {
    return this.delete(`/apuntes/${id}`);
  }
}

export const academicService = new AcademicService();
