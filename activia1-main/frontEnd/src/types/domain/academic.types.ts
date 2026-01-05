/**
 * Tipos para gestión de contenido académico.
 *
 * Cortez72: Implementación desde metodologia.md
 *
 * Incluye materias, unidades, apuntes y sus relaciones.
 */

// ==================== Recursos ====================

export interface RecursoExterno {
  url: string;
  titulo: string;
  tipo: 'video' | 'pdf' | 'link';
}

// ==================== Apuntes ====================

export interface ApuntesCreate {
  titulo: string;
  contenido_markdown: string;
  resumen?: string;
  recursos_externos?: RecursoExterno[];
  tiempo_lectura_min?: number;
  nivel_dificultad?: 'basico' | 'intermedio' | 'avanzado';
}

export interface ApuntesUpdate {
  titulo?: string;
  contenido_markdown?: string;
  resumen?: string;
  recursos_externos?: RecursoExterno[];
  tiempo_lectura_min?: number;
  nivel_dificultad?: 'basico' | 'intermedio' | 'avanzado';
}

export interface ApuntesResponse {
  id: string;
  unidad_id: string;
  titulo: string;
  contenido_markdown: string;
  resumen: string | null;
  recursos_externos: RecursoExterno[];
  tiempo_lectura_min: number;
  nivel_dificultad: string;
  orden: number;
  esta_publicado: boolean;
  created_by: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

// ==================== Unidades ====================

export interface UnidadCreate {
  materia_code: string;
  numero: number;
  titulo: string;
  descripcion?: string;
  objetivos_aprendizaje?: string[];
  tiempo_teoria_min?: number;
  tiempo_practica_min?: number;
}

export interface UnidadUpdate {
  titulo?: string;
  descripcion?: string;
  objetivos_aprendizaje?: string[];
  tiempo_teoria_min?: number;
  tiempo_practica_min?: number;
  requiere_unidad_anterior?: boolean;
}

export interface UnidadResponse {
  id: string;
  materia_code: string;
  numero: number;
  titulo: string;
  descripcion: string | null;
  objetivos_aprendizaje: string[];
  tiempo_teoria_min: number;
  tiempo_practica_min: number;
  orden: number;
  esta_publicada: boolean;
  requiere_unidad_anterior: boolean;
  created_by: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UnidadConApuntes extends UnidadResponse {
  apuntes: ApuntesResponse[];
}

export interface UnidadConEjercicios extends UnidadResponse {
  total_ejercicios: number;
  ejercicios_publicados: number;
}

// ==================== Materias ====================

export interface MateriaCreate {
  code: string;
  name: string;
  description?: string;
  language: 'python' | 'java';
  total_units?: number;
  is_active?: boolean;
}

export interface MateriaUpdate {
  name?: string;
  description?: string;
  total_units?: number;
  is_active?: boolean;
}

export interface MateriaResponse {
  code: string;
  name: string;
  description: string | null;
  language: string;
  total_units: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface MateriaConUnidades extends MateriaResponse {
  unidades: UnidadConEjercicios[];
}

// ==================== Archivos Adjuntos ====================

export interface ArchivoAdjunto {
  id: string;
  nombre_original: string;
  tipo_archivo: 'pdf' | 'png' | 'jpg' | 'gif';
  tamano_bytes: number;
  descripcion: string | null;
  orden: number;
  url: string;
}

export interface ArchivoUploadResponse {
  id: string;
  nombre_original: string;
  tipo_archivo: string;
  tamano_bytes: number;
  ruta_relativa: string;
  url: string;
}
