/**
 * Simulator Configuration - Icons, colors, and welcome messages
 *
 * Cortez43: Extracted from SimulatorsPage.tsx (514 lines)
 */

import {
  Users,
  UserCheck,
  Briefcase,
  AlertTriangle,
  HeadphonesIcon,
  Shield,
  type LucideIcon,
} from 'lucide-react';

// Simulator Icons - use lowercase values to match backend enum
export const simulatorIcons: Record<string, LucideIcon> = {
  product_owner: Briefcase,
  scrum_master: UserCheck,
  tech_interviewer: Users,
  incident_responder: AlertTriangle,
  client: HeadphonesIcon,
  devsecops: Shield,
};

// Simulator Gradient Colors
export const simulatorColors: Record<string, string> = {
  product_owner: 'from-blue-500 to-cyan-600',
  scrum_master: 'from-green-500 to-emerald-600',
  tech_interviewer: 'from-purple-500 to-pink-600',
  incident_responder: 'from-red-500 to-orange-600',
  client: 'from-yellow-500 to-orange-600',
  devsecops: 'from-indigo-500 to-purple-600',
};

// Welcome Messages - using lowercase keys to match backend
export const welcomeMessages: Record<string, string> = {
  product_owner: `¡Hola! Soy el Product Owner de tu equipo.

Estoy aquí para ayudarte a entender mejor los requisitos del negocio y cómo priorizar el trabajo.

**¿Cómo puedo ayudarte hoy?**
- Revisar historias de usuario
- Priorizar el backlog
- Discutir decisiones técnicas desde perspectiva de negocio
- Clarificar requisitos

¿Qué necesitas?`,
  scrum_master: `¡Buenos días! Soy el Scrum Master del equipo.

Mi rol es facilitar y eliminar impedimentos para que el equipo pueda entregar valor.

**Podemos trabajar en:**
- Simular una daily standup
- Identificar y resolver impedimentos
- Mejorar procesos del equipo
- Preparar retrospectivas

¿Cómo te fue ayer? ¿En qué estás trabajando hoy?`,
  tech_interviewer: `Hola, gracias por venir a esta entrevista técnica.

Vamos a evaluar tus conocimientos en programación y resolución de problemas.

**Áreas que cubriremos:**
- Estructuras de datos
- Algoritmos
- Diseño de sistemas
- Buenas prácticas

¿Estás listo para comenzar? Cuéntame un poco sobre tu experiencia.`,
  incident_responder: `🚨 **ALERTA: Incidente en Producción**

Soy el Incident Responder de turno. Tenemos un problema crítico que necesita atención inmediata.

**Situación actual:**
- Los usuarios reportan timeouts en la API
- El sistema de monitoreo muestra alta latencia
- El equipo de soporte está recibiendo múltiples tickets

¿Por dónde empezamos a diagnosticar?`,
  client: `Hola, soy el cliente de tu proyecto.

Necesito un sistema nuevo pero... no estoy seguro exactamente de lo que quiero.

Solo sé que el sistema actual no funciona bien y necesitamos algo mejor.

¿Me puedes ayudar a definir qué necesitamos?`,
  devsecops: `Hola, soy el analista de seguridad del equipo.

Necesito revisar el código del último sprint antes de que pase a producción.

**Áreas de revisión:**
- Vulnerabilidades de seguridad
- Manejo de datos sensibles
- Autenticación y autorización
- Dependencias inseguras

¿Tienes código listo para revisar?`,
};

// Default Mock Simulators - for when API fails
export const defaultSimulators = [
  {
    type: 'product_owner',
    name: 'Product Owner (PO-IA)',
    description:
      'Simula un Product Owner que revisa requisitos, prioriza backlog y cuestiona decisiones técnicas',
    competencies: ['comunicacion_tecnica', 'analisis_requisitos', 'priorizacion'],
    status: 'active',
  },
  {
    type: 'scrum_master',
    name: 'Scrum Master (SM-IA)',
    description:
      'Simula un Scrum Master que facilita daily standups y gestiona impedimentos',
    competencies: ['gestion_tiempo', 'comunicacion', 'identificacion_impedimentos'],
    status: 'active',
  },
  {
    type: 'tech_interviewer',
    name: 'Technical Interviewer (IT-IA)',
    description:
      'Simula un entrevistador técnico que evalúa conocimientos conceptuales y algorítmicos',
    competencies: ['dominio_conceptual', 'analisis_algoritmico', 'comunicacion_tecnica'],
    status: 'active',
  },
  {
    type: 'incident_responder',
    name: 'Incident Responder (IR-IA)',
    description: 'Simula un ingeniero DevOps que gestiona incidentes en producción',
    competencies: ['diagnostico_sistematico', 'priorizacion', 'documentacion'],
    status: 'development',
  },
  {
    type: 'client',
    name: 'Client (CX-IA)',
    description:
      'Simula un cliente con requisitos ambiguos que requiere elicitación y negociación',
    competencies: ['elicitacion_requisitos', 'negociacion', 'empatia'],
    status: 'development',
  },
  {
    type: 'devsecops',
    name: 'DevSecOps (DSO-IA)',
    description:
      'Simula un analista de seguridad que audita código y detecta vulnerabilidades',
    competencies: ['seguridad', 'analisis_vulnerabilidades', 'gestion_riesgo'],
    status: 'active',
  },
];
