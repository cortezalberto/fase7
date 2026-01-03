# Integracion de AI-Native MVP con Moodle via LTI 1.3

## Documentacion Tecnica Completa

**Version**: 3.3 (Cortez65.1 + Vinculacion Actividades Moodle-AI-Native)
**Fecha**: Enero 2026
**Proyecto**: AI-Native MVP - Tesis Doctoral
**Historia de Usuario**: HU-SYS-010 - Integracion LTI 1.3
**Estado**: Implementado pero NO HABILITADO (90%)

> **Novedad v3.3**: Vinculacion completa de actividades Moodle con AI-Native. El docente puede vincular sus actividades de AI-Native (con politicas pedagogicas) a actividades de Moodle. Cuando el estudiante hace clic en la actividad de Moodle, automaticamente se carga la actividad correcta con sus politicas. Incluye 3 nuevos endpoints y seccion 11.5 con documentacion completa.
>
> **Novedad v3.2**: Se agrego `resource_link_title` para capturar el nombre de la actividad de Moodle. Ahora todos los datos requeridos estan disponibles: nombre completo del estudiante, nombre del curso, comision, y nombre de la actividad.
>
> **Novedad v3.1**: Se agrego la seccion 7 completamente expandida con una guia paso a paso para administradores de Moodle. Incluye 17 subsecciones con instrucciones detalladas para configurar la herramienta LTI, obtener credenciales, crear actividades y probar la integracion.

---

## Indice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Que es LTI y Por Que Importa](#2-que-es-lti-y-por-que-importa)
3. [Estado Actual de Implementacion](#3-estado-actual-de-implementacion)
4. [Arquitectura de Integracion](#4-arquitectura-de-integracion)
5. [Componentes Implementados](#5-componentes-implementados)
6. [Como Habilitar LTI](#6-como-habilitar-lti)
7. [Configuracion de Moodle - Guia Completa para Administradores](#7-configuracion-de-moodle---guia-completa-para-administradores)
   - 7.1 [Prerequisitos en Moodle](#71-prerequisitos-en-moodle)
   - 7.2 [Acceder al Panel de Administracion](#72-acceder-al-panel-de-administracion-de-herramientas-externas)
   - 7.3 [Registrar AI-Native como Herramienta](#73-registrar-ai-native-como-herramienta-externa-lti-13)
   - 7.4 [Seccion Tool Settings](#74-formulario-de-configuracion---seccion-tool-settings)
   - 7.5 [Seccion Tool Configuration](#75-formulario-de-configuracion---seccion-tool-configuration)
   - 7.6 [Seccion Services](#76-formulario-de-configuracion---seccion-services)
   - 7.7 [Seccion Privacy](#77-formulario-de-configuracion---seccion-privacy)
   - 7.8 [Seccion Miscellaneous](#78-formulario-de-configuracion---seccion-miscellaneous)
   - 7.9 [Guardar Configuracion](#79-guardar-la-configuracion)
   - 7.10 [Obtener Credenciales](#710-obtener-credenciales-de-moodle)
   - 7.11 [Registrar Deployment en AI-Native](#711-registrar-el-deployment-en-ai-native)
   - 7.12 [Verificar Configuracion](#712-verificar-la-configuracion)
   - 7.13 [Crear Actividad LTI](#713-crear-una-actividad-lti-en-un-curso)
   - 7.14 [Probar el Launch](#714-probar-el-launch-como-estudiante)
   - 7.15 [Parametros Personalizados](#715-configuracion-avanzada---parametros-personalizados)
   - 7.16 [Multiples Moodles](#716-gestion-de-multiples-moodles)
   - 7.17 [Desactivar Deployment](#717-desactivar-un-deployment)
8. [Configuracion de AI-Native](#8-configuracion-de-ai-native)
9. [Flujo de Autenticacion Detallado](#9-flujo-de-autenticacion-detallado)
10. [Frontend en Modo Embebido](#10-frontend-en-modo-embebido)
11. [LTI Advantage Services](#11-lti-advantage-services)
12. [Integracion con el Sistema de Agentes](#12-integracion-con-el-sistema-de-agentes)
13. [Seguridad y Gobernanza](#13-seguridad-y-gobernanza)
14. [Testing](#14-testing)
15. [Troubleshooting](#15-troubleshooting)
16. [Proximos Pasos](#16-proximos-pasos)

---

## 1. Resumen Ejecutivo

### 1.1 Vision General

Este documento explica como integrar el sistema AI-Native MVP con Moodle utilizando el estandar LTI 1.3 (Learning Tools Interoperability). La integracion permite que los estudiantes accedan al tutor de inteligencia artificial directamente desde sus cursos en Moodle, sin necesidad de crear cuentas adicionales ni navegar entre plataformas distintas. Cuando un estudiante hace clic en la actividad "Tutor IA" dentro de Moodle, el sistema lo autentica automaticamente, identifica el curso y la actividad que esta realizando, y lo lleva directamente al tutor con todo el contexto academico necesario.

La decision de implementar LTI 1.3 en lugar de versiones anteriores responde a requisitos de seguridad modernos. LTI 1.3 utiliza OAuth 2.0, OpenID Connect y JSON Web Tokens, tecnologias probadas que garantizan que solo usuarios legitimos desde plataformas autorizadas puedan acceder al sistema. Esto es particularmente importante para un proyecto de tesis doctoral donde la integridad de los datos y la trazabilidad del proceso de aprendizaje son fundamentales.

### 1.2 Estado Actual (Cortez65)

Con la implementacion de Cortez65, el proyecto tiene ahora el **85% de la infraestructura** necesaria para LTI:

| Componente | Estado | Archivo |
|------------|--------|---------|
| Modelos de BD (LTIDeploymentDB, LTISessionDB) | IMPLEMENTADO | `backend/database/models/lti.py` |
| Repositorios LTI | IMPLEMENTADO | `backend/database/repositories/lti_repository.py` |
| Schemas Pydantic | IMPLEMENTADO | `backend/api/schemas/sprint5_6.py` |
| **Router LTI con OIDC** | **IMPLEMENTADO (Cortez65)** | `backend/api/routers/lti.py` |
| **Variables de entorno** | **IMPLEMENTADO (Cortez65)** | `.env.example`, `backend/api/config.py` |
| **Frontend LTI Service** | **IMPLEMENTADO (Cortez65)** | `frontEnd/src/services/api/lti.service.ts` |
| **LTI Container Component** | **IMPLEMENTADO (Cortez65)** | `frontEnd/src/components/LTIContainer.tsx` |
| Registro en main.py | PENDIENTE (manual) | Requiere habilitacion |
| LTI Advantage (AGS, NRPS) | PENDIENTE | Fase avanzada |

### 1.3 Que Cambio en Cortez65

Antes de Cortez65, el proyecto tenia los modelos y repositorios pero no podia procesar ningun launch LTI porque faltaba el router que implementa el flujo OIDC. Ahora el sistema tiene:

1. **Router LTI completo** (~650 lineas) con endpoints para login, launch, JWKS y administracion de deployments.

2. **Configuracion centralizada** con variables de entorno documentadas y valores por defecto seguros.

3. **Frontend preparado** para detectar cuando la aplicacion se ejecuta dentro de un iframe de Moodle y adaptar su comportamiento.

El router esta implementado pero **no esta registrado en main.py** intencionalmente. Esto permite tener el codigo listo sin activar la funcionalidad hasta que el administrador configure Moodle y habilite la integracion explicitamente.

---

## 2. Que es LTI y Por Que Importa

### 2.1 El Problema que Resuelve

Imagina que eres docente de un curso de Programacion I y quieres que tus estudiantes utilicen el tutor de IA de AI-Native como parte de sus actividades de aprendizaje. Sin integracion LTI, enfrentarias varios problemas practicos que degradan la experiencia educativa.

Primero, tus estudiantes ya estan autenticados en Moodle con sus credenciales institucionales. Si AI-Native requiere un login separado, tendrian que crear y recordar otra cuenta, lo cual genera friccion y abandono. Peor aun, algunos estudiantes podrian crear cuentas con nombres o emails falsos, rompiendo la trazabilidad que necesitas para evaluar su proceso de aprendizaje.

Segundo, cuando un estudiante accede a AI-Native de forma independiente, el sistema no sabe en que curso esta inscripto, que actividad especifica esta realizando, ni cual es tu politica pedagogica para ese curso en particular. El tutor funcionaria de forma generica, sin poder adaptar sus respuestas al contexto academico real.

Tercero, si AI-Native genera evaluaciones o metricas del proceso cognitivo del estudiante, tendrias que exportar esos datos manualmente e ingresarlos en Moodle. Con decenas o cientos de estudiantes, esto se vuelve impracticable y propenso a errores.

LTI resuelve estos problemas creando un puente estandarizado entre Moodle (la "Plataforma" en terminologia LTI) y AI-Native (la "Herramienta"). Este puente transmite la identidad del estudiante, el contexto del curso y la actividad, y opcionalmente permite que las calificaciones fluyan de vuelta a Moodle automaticamente.

### 2.2 Como Funciona LTI 1.3

LTI 1.3 es la version moderna del estandar, publicada en 2019 por IMS Global Learning Consortium. A diferencia de versiones anteriores que usaban OAuth 1.0 (considerado obsoleto), LTI 1.3 se construye sobre tecnologias de autenticacion actuales que son ampliamente utilizadas en la industria.

El flujo utiliza **OAuth 2.0** para la autorizacion, asegurando que solo plataformas registradas puedan solicitar acceso. Utiliza **OpenID Connect (OIDC)** para el intercambio seguro de la identidad del usuario, evitando que credenciales sensibles viajen por la red. Los mensajes entre Moodle y AI-Native se firman digitalmente usando **JSON Web Tokens (JWT)**, lo cual permite verificar que no fueron alterados en transito. Finalmente, las claves publicas necesarias para verificar estas firmas se publican en endpoints **JWKS (JSON Web Key Sets)**, permitiendo rotacion de claves sin coordinacion manual.

Cuando un estudiante hace clic en una actividad LTI dentro de Moodle, ocurre una "danza" de autenticacion en tres pasos. Primero, Moodle redirige al navegador del estudiante hacia AI-Native con parametros que identifican quien es (un hint, no la identidad completa) y que actividad quiere acceder. Segundo, AI-Native verifica que el issuer sea conocido, genera tokens de seguridad unicos (state y nonce), y redirige de vuelta a Moodle solicitando autenticacion. Tercero, Moodle verifica al usuario, genera un JWT firmado con toda la informacion necesaria, y lo envia a AI-Native via POST. AI-Native valida la firma usando las claves publicas de Moodle, extrae la informacion del usuario y curso, crea una sesion, y finalmente redirige al estudiante al frontend del tutor.

Este flujo puede parecer complejo, pero garantiza que ningun actor malicioso pueda suplantar a Moodle o a un estudiante. Cada mensaje esta firmado y cada token es de uso unico.

### 2.3 Beneficios para AI-Native

La integracion LTI aporta valor significativo al sistema en multiples dimensiones. El **Single Sign-On** elimina la friccion de autenticacion, ya que los estudiantes acceden directamente desde Moodle sin crear cuentas adicionales. El **contexto academico** permite que el tutor sepa en que curso esta el estudiante, que actividad realiza, y si tiene rol de estudiante o instructor.

La **trazabilidad institucional** vincula cada sesion de tutorado con un curso real de Moodle, lo cual es fundamental para el modelo de evaluacion basada en proceso que implementa AI-Native. Las **calificaciones automaticas** (via LTI-AGS) permitiran eventualmente que los reportes de proceso se envien directamente al libro de calificaciones de Moodle. El **roster sync** (via LTI-NRPS) permitira obtener la lista de estudiantes del curso para generar reportes comparativos sin necesidad de ingreso manual.

Desde la perspectiva del docente, la **gestion centralizada** significa que puede configurar actividades, ver progreso y gestionar estudiantes desde una sola plataforma (Moodle) sin alternar entre sistemas.

### 2.4 Terminologia Esencial

Para entender la documentacion tecnica y los logs del sistema, es importante familiarizarse con la terminologia LTI:

| Termino | Significado | Ejemplo en AI-Native |
|---------|-------------|----------------------|
| **Platform** | El LMS que inicia el launch | Moodle |
| **Tool** | La aplicacion externa | AI-Native |
| **Issuer** | URL unica que identifica al Platform | `https://moodle.universidad.edu` |
| **Client ID** | ID de la herramienta registrada en Moodle | `abc123xyz` (generado por Moodle) |
| **Deployment ID** | ID de un deployment especifico | `1` (asignado por Moodle) |
| **Resource Link** | Actividad especifica en Moodle | La actividad "Tutor IA" en un curso |
| **JWKS** | Conjunto de claves publicas para validar tokens | URL donde Moodle publica sus claves |
| **Claims** | Datos dentro del JWT | Usuario, curso, roles, actividad |
| **State** | Token de seguridad para prevenir CSRF | UUID generado por AI-Native |
| **Nonce** | Token para prevenir replay attacks | UUID generado por AI-Native |

---

## 3. Estado Actual de Implementacion

### 3.1 Componentes de Backend

El backend tiene tres capas de implementacion para LTI: modelos de base de datos, repositorios de acceso a datos, y el router HTTP.

Los **modelos de base de datos** fueron implementados durante el Sprint 6 del proyecto y representan la estructura de datos necesaria para almacenar configuraciones de plataformas LTI y sesiones de usuarios que acceden via LTI. El modelo `LTIDeploymentDB` almacena la configuracion de cada Moodle registrado, incluyendo sus URLs de autenticacion y claves publicas. El modelo `LTISessionDB` mapea cada launch LTI a una sesion de AI-Native, guardando el contexto del curso y la actividad.

Los **repositorios** implementan el patron Repository para encapsular el acceso a la base de datos. `LTIDeploymentRepository` permite crear, buscar y desactivar deployments. `LTISessionRepository` maneja la creacion y busqueda de sesiones LTI, incluyendo el vinculo con sesiones AI-Native.

El **router LTI** implementado en Cortez65 es el componente que conecta todo. Define los endpoints HTTP que Moodle invoca durante el flujo OIDC, valida los tokens JWT, y orquesta la creacion de sesiones. El router incluye:

- `POST /api/v1/lti/login`: Inicio del flujo OIDC. Moodle redirige aqui cuando un estudiante hace clic en una actividad LTI.
- `POST /api/v1/lti/launch`: Callback que recibe el JWT firmado por Moodle con la informacion del usuario.
- `GET /api/v1/lti/jwks`: Endpoint que publica las claves publicas de AI-Native para que Moodle pueda verificar tokens que firmemos (necesario para LTI Advantage).
- `POST /api/v1/lti/deployments`: Endpoint de administracion para registrar nuevas plataformas Moodle.
- `GET /api/v1/lti/deployments`: Lista los deployments registrados.
- `DELETE /api/v1/lti/deployments/{id}`: Desactiva un deployment.
- `GET /api/v1/lti/health`: Health check del subsistema LTI.

### 3.2 Componentes de Frontend

El frontend tiene dos nuevos componentes implementados en Cortez65 para soportar el modo LTI embebido.

El **servicio LTI** (`lti.service.ts`) proporciona funciones de utilidad para detectar cuando la aplicacion esta ejecutandose en contexto LTI. Cuando un estudiante llega al frontend despues de un launch exitoso, la URL contiene parametros como `?session_id=xxx&lti=true`. El servicio detecta estos parametros, los almacena en sessionStorage para persistir entre recargas de pagina, y proporciona metodos para verificar si estamos en un iframe (tipico de integraciones LTI).

El **componente LTIContainer** es un wrapper que envuelve la aplicacion cuando se detecta modo LTI. Proporciona un banner que muestra el contexto del curso (nombre del curso, nombre del estudiante), aplica estilos especiales para el modo embebido (eliminando margenes innecesarios, adaptando el layout para iframes), y expone un contexto React para que cualquier componente hijo pueda saber si esta en modo LTI.

### 3.3 Configuracion

La configuracion LTI esta centralizada en dos lugares. El archivo `.env.example` documenta todas las variables de entorno disponibles con sus valores por defecto y explicaciones detalladas. El archivo `backend/api/config.py` lee estas variables y las expone como constantes tipadas para el resto del sistema.

Las variables principales son:

- `LTI_ENABLED`: Switch maestro que habilita o deshabilita todo el subsistema LTI. Por defecto es `false`.
- `LTI_FRONTEND_URL`: URL del frontend donde redirigir despues de un launch exitoso. Por defecto `http://localhost:3000`.
- `LTI_STATE_EXPIRATION_MINUTES`: Tiempo de vida del token state de OIDC. Por defecto 10 minutos.
- `LTI_NONCE_EXPIRATION_HOURS`: Tiempo durante el cual un nonce se considera usado (proteccion contra replay). Por defecto 1 hora.
- `LTI_JWKS_CACHE_TTL_SECONDS`: Tiempo de cache para las claves publicas de Moodle. Por defecto 1 hora.

### 3.4 Lo Que Falta

Aunque el 85% de la infraestructura esta implementada, hay dos areas pendientes:

1. **Registro del router en main.py**: El router existe pero no esta activo. Esto es intencional para evitar exponer endpoints sin que el administrador haya configurado Moodle primero.

2. **LTI Advantage (AGS y NRPS)**: Los servicios avanzados de LTI que permiten enviar calificaciones a Moodle (AGS) y obtener la lista de estudiantes del curso (NRPS) no estan implementados. Estos son mejoras incrementales que pueden agregarse despues de validar que el flujo basico funciona correctamente.

---

## 4. Arquitectura de Integracion

### 4.1 Vision General

La integracion LTI conecta dos sistemas que operan de forma independiente: Moodle como plataforma de gestion de aprendizaje y AI-Native como herramienta de tutoria inteligente. El flujo de datos es unidireccional en la autenticacion (de Moodle hacia AI-Native) pero puede ser bidireccional cuando se implementen los servicios avanzados (calificaciones de AI-Native hacia Moodle).

```
+==================================================================================+
|                        ARQUITECTURA LTI 1.3 - AI-Native MVP                       |
+==================================================================================+

                                  MOODLE LMS
                          +------------------------+
                          |  +------------------+  |
                          |  |   Curso:         |  |
                          |  |   Programacion I |  |
                          |  +--------+---------+  |
                          |           |            |
                          |  +--------v---------+  |
                          |  | Actividad LTI:   |  |
                          |  | "Tutor IA"       |  |
                          |  +--------+---------+  |
                          +-----------|------------+
                                      |
                          (1) OIDC Login Request
                          (redirect con login_hint)
                                      |
                                      v
+==================================================================================+
|                              AI-NATIVE MVP                                        |
+==================================================================================+
|                                                                                   |
|  +-------------------+     +-------------------+     +-------------------+        |
|  |  LTI Router       |---->|  JWT Validator    |---->|   Repositories    |        |
|  |  /api/v1/lti/*    |     |  (JWKS fetch)     |     |   (PostgreSQL)    |        |
|  +-------------------+     +-------------------+     +-------------------+        |
|         |                         |                         |                     |
|  (2) Validate OIDC         (3) Verify Signature      +------v------+             |
|      Parameters                   |                  | lti_deployments|             |
|         |                         |                  | lti_sessions   |             |
|         v                         v                  | sessions       |             |
|  +-------------------+     +-------------------+     +---------------+             |
|  |  State/Nonce      |     |   Session         |                                   |
|  |  Cache (Memory)   |     |   Creator         |                                   |
|  +-------------------+     +--------+----------+                                   |
|                                     |                                              |
|                          (4) Create AI-Native                                      |
|                              Session                                               |
|                                     |                                              |
|                                     v                                              |
|  +=========================================================================+      |
|  |                      AI GATEWAY (STATELESS)                              |      |
|  +=========================================================================+      |
|  |   +----------+   +----------+   +----------+   +----------+             |      |
|  |   | T-IA-Cog |   | E-IA-Proc|   | S-IA-X   |   | GOV-IA   |             |      |
|  |   | (Tutor)  |   | (Eval)   |   | (Sim)    |   | (Gov)    |             |      |
|  |   +----------+   +----------+   +----------+   +----------+             |      |
|  |        |              |              |              |                    |      |
|  |        +-------+------+------+-------+              |                    |      |
|  |                |             |                      |                    |      |
|  |         +------v------+     +v---------------------v+                   |      |
|  |         | N4 Traces   |     | Course-aware Policies |                   |      |
|  |         | (PostgreSQL)|     | (via LTI context)     |                   |      |
|  |         +-------------+     +------------------------+                   |      |
|  +=========================================================================+      |
|                                                                                   |
+==================================================================================+
                                      |
                          (5) Redirect to Frontend
                          /tutor?session_id=xxx&lti=true
                                      |
                                      v
                          +------------------------+
                          |     FRONTEND           |
                          |  +------------------+  |
                          |  | LTIContainer     |  |
                          |  | - Detect LTI     |  |
                          |  | - Show banner    |  |
                          |  | - Adapt layout   |  |
                          |  +--------+---------+  |
                          |           |            |
                          |  +--------v---------+  |
                          |  |    TutorPage     |  |
                          |  | (with context)   |  |
                          |  +------------------+  |
                          +------------------------+
```

### 4.2 Flujo de Datos

El flujo de datos durante un launch LTI sigue una secuencia precisa diseñada para garantizar seguridad y correcta transferencia de contexto.

Todo comienza cuando un estudiante, ya autenticado en Moodle, hace clic en una actividad configurada como herramienta LTI externa. Moodle genera una solicitud OIDC que incluye el issuer (la URL de Moodle), un login_hint (identificador opaco del usuario), y la URL de destino. Esta solicitud viaja como una redireccion del navegador hacia el endpoint `/lti/login` de AI-Native.

AI-Native recibe la solicitud, busca el deployment correspondiente al issuer, genera tokens de seguridad (state y nonce), los almacena temporalmente, y redirige de vuelta a Moodle con una solicitud de autorizacion. Esta redireccion incluye el state y nonce generados, que Moodle debera incluir en su respuesta.

Moodle verifica que el usuario este autenticado (ya lo estaba), genera un JWT firmado con su clave privada que contiene toda la informacion del usuario (nombre, email, roles) y del contexto (curso, actividad), e incluye el nonce recibido. Este JWT se envia via POST al endpoint `/lti/launch`.

AI-Native recibe el JWT, verifica que el state coincida con uno previamente generado (previniendo CSRF), obtiene las claves publicas de Moodle desde su endpoint JWKS, valida la firma del JWT (asegurando que realmente proviene de Moodle), verifica que el nonce no haya sido usado antes (previniendo replay attacks), y extrae los claims del token.

Con los claims extraidos, AI-Native crea o recupera una sesion. Si el usuario ya habia lanzado esta actividad previamente y tiene una sesion activa, la reutiliza. Si no, crea una nueva sesion con el contexto LTI (ID del curso, nombre del curso, si es instructor, etc.).

Finalmente, AI-Native redirige el navegador del estudiante al frontend, incluyendo el ID de sesion y una bandera indicando que es un launch LTI. El frontend detecta estos parametros, inicializa el LTIContainer, y presenta el tutor con el contexto apropiado.

---

## 5. Componentes Implementados

### 5.1 Router LTI (backend/api/routers/lti.py)

El router LTI es el componente central implementado en Cortez65. Con aproximadamente 650 lineas de codigo, implementa el flujo completo de autenticacion OIDC y la gestion de deployments.

El endpoint de **login** (`POST /lti/login`) es el punto de entrada del flujo OIDC. Cuando Moodle redirige aqui, el router:

1. Extrae los parametros del request: `iss` (issuer), `login_hint`, `target_link_uri`, y opcionalmente `client_id` y `lti_deployment_id`.
2. Busca el deployment correspondiente en la base de datos por issuer. Si no existe, retorna error 404.
3. Genera un `state` UUID para prevenir ataques CSRF.
4. Genera un `nonce` UUID para prevenir replay attacks.
5. Almacena state y nonce en un cache en memoria (con TTL configurable).
6. Construye la URL de autorizacion de Moodle con los parametros requeridos.
7. Redirige el navegador a Moodle.

El endpoint de **launch** (`POST /lti/launch`) recibe el JWT de Moodle y completa la autenticacion:

1. Extrae `id_token` (el JWT) y `state` del form POST.
2. Verifica que el state exista en cache y no haya expirado.
3. Consume el state (one-time use) eliminandolo del cache.
4. Obtiene el deployment asociado al state.
5. Hace fetch del JWKS de Moodle (con cache para evitar requests repetidos).
6. Valida el JWT: firma, issuer, audience, expiracion, nonce.
7. Verifica que el nonce del token coincida con el almacenado.
8. Extrae los claims LTI: usuario, contexto del curso, resource link, roles.
9. Crea o recupera un usuario AI-Native basado en el usuario LTI.
10. Crea o recupera una sesion AI-Native con el contexto LTI.
11. Crea un registro LTISession vinculando todo.
12. Redirige al frontend con `session_id` y `lti=true`.

El endpoint **JWKS** (`GET /lti/jwks`) publica las claves publicas de AI-Native. Aunque actualmente devuelve un keyset vacio (ya que no firmamos tokens para Moodle en el flujo basico), esta preparado para cuando se implemente LTI Advantage y necesitemos firmar requests hacia Moodle.

Los endpoints de **deployments** (`POST/GET/DELETE /lti/deployments`) permiten administrar las plataformas Moodle registradas. Actualmente no tienen autenticacion (marcados como TODO), pero permiten listar, crear y desactivar deployments.

### 5.2 Configuracion (backend/api/config.py)

La configuracion LTI se agrego al archivo config.py existente con una seccion dedicada:

```python
# =============================================================================
# LTI 1.3 Configuration (HU-SYS-010)
# =============================================================================
LTI_ENABLED = os.getenv("LTI_ENABLED", "false").lower() == "true"
LTI_STATE_EXPIRATION_MINUTES = int(os.getenv("LTI_STATE_EXPIRATION_MINUTES", "10"))
LTI_NONCE_EXPIRATION_HOURS = int(os.getenv("LTI_NONCE_EXPIRATION_HOURS", "1"))
LTI_JWKS_CACHE_TTL_SECONDS = int(os.getenv("LTI_JWKS_CACHE_TTL_SECONDS", "3600"))
LTI_FRONTEND_URL = os.getenv("LTI_FRONTEND_URL", "http://localhost:3000")
LTI_PRIVATE_KEY_PATH = os.getenv("LTI_PRIVATE_KEY_PATH", "")
LTI_PUBLIC_KEY_PATH = os.getenv("LTI_PUBLIC_KEY_PATH", "")
```

Al iniciar el backend, se loguea el estado de la configuracion LTI, indicando si esta habilitado o deshabilitado.

### 5.3 Servicio Frontend (frontEnd/src/services/api/lti.service.ts)

El servicio LTI del frontend proporciona funciones para detectar y manejar el contexto LTI:

- `detectLTIContext()`: Lee los query params de la URL y retorna un objeto con `isLTI`, `sessionId`, etc.
- `isLTIMode()`: Shortcut para verificar si estamos en modo LTI.
- `isEmbedded()`: Detecta si la app esta en un iframe (tipico de LTI).
- `getEmbeddedClass()`: Retorna clase CSS para aplicar estilos especiales.
- `cleanURL()`: Elimina los parametros LTI de la URL despues de procesarlos.
- `storeLTIContext()` / `getStoredLTIContext()`: Persiste el contexto en sessionStorage.

El servicio tambien incluye metodos para interactuar con los endpoints de administracion (`listDeployments`, `createDeployment`, `deactivateDeployment`).

### 5.4 Componente LTIContainer (frontEnd/src/components/LTIContainer.tsx)

El componente LTIContainer es un wrapper que envuelve la aplicacion cuando se detecta modo LTI. Proporciona:

1. **Deteccion automatica**: Al montarse, detecta si hay parametros LTI en la URL y los almacena.
2. **Context provider**: Expone un contexto React (`useLTIContext`) para que cualquier componente pueda saber si esta en modo LTI.
3. **Banner de contexto**: Muestra un banner naranja con el nombre del curso y usuario cuando aplica.
4. **Estilos embebidos**: Aplica clases CSS especiales para el modo iframe (menos padding, sin margenes externos).

El componente inyecta estilos CSS en el `<head>` del documento para evitar dependencias externas.

### 5.5 Modelos de Base de Datos

Los modelos LTI fueron implementados en el Sprint 6 y permanecen sin cambios:

**LTIDeploymentDB** almacena la configuracion de cada plataforma:
- `platform_name`: Nombre amigable (ej: "Moodle Universidad Nacional")
- `issuer`: URL unica de Moodle (ej: "https://moodle.edu.ar")
- `client_id`: ID OAuth2 generado por Moodle
- `deployment_id`: ID del deployment especifico
- `auth_login_url`: URL para iniciar OIDC
- `auth_token_url`: URL para obtener tokens (AGS)
- `public_keyset_url`: URL del JWKS de Moodle
- `access_token_url`: URL para tokens de acceso (AGS)
- `is_active`: Permite desactivar sin eliminar

**LTISessionDB** mapea launches a sesiones:
- `deployment_id`: FK al deployment
- `lti_user_id`: ID del usuario en Moodle
- `lti_user_name`, `lti_user_email`: Datos del usuario (nombre completo y email)
- `lti_context_id`, `lti_context_label`, `lti_context_title`: Datos del curso
  - `lti_context_label`: Codigo de la comision (ej: "PROG1-A")
  - `lti_context_title`: Nombre completo del curso (ej: "Programacion I - Comision A")
- `resource_link_id`, `resource_link_title`: Datos de la actividad
  - `resource_link_id`: ID unico de la actividad
  - `resource_link_title`: Nombre de la actividad (ej: "Ejercicio 1: Variables")
- `session_id`: FK a la sesion AI-Native
- `launch_token`: JWT del launch (para AGS posterior)
- `locale`: Idioma del usuario

---

## 6. Como Habilitar LTI

### 6.1 Prerequisitos

Antes de habilitar LTI, asegurate de tener:

1. **Moodle 3.9+** (recomendado 4.x) con permisos de administrador.
2. **AI-Native desplegado con HTTPS**. LTI 1.3 requiere conexiones seguras.
3. **Certificado SSL valido**. Certificados auto-firmados pueden causar problemas.
4. **Acceso a la consola del servidor** para modificar archivos de configuracion.

### 6.2 Paso 1: Configurar Variables de Entorno

Edita el archivo `.env` (o crea uno basado en `.env.example`) y agrega:

```bash
# Habilitar LTI
LTI_ENABLED=true

# URL del frontend (donde redirigir despues del launch)
LTI_FRONTEND_URL=https://tu-dominio.com

# Opcional: Ajustar tiempos de expiracion si es necesario
LTI_STATE_EXPIRATION_MINUTES=10
LTI_NONCE_EXPIRATION_HOURS=1
LTI_JWKS_CACHE_TTL_SECONDS=3600
```

### 6.3 Paso 2: Registrar el Router

Edita `backend/api/main.py` y agrega el router LTI:

```python
# Buscar la seccion donde se registran los routers
from backend.api.routers import lti

# Agregar despues de los otros routers
app.include_router(lti.router, prefix="/api/v1/lti", tags=["lti"])
```

### 6.4 Paso 3: Reiniciar el Backend

```bash
# Con Docker
docker-compose restart api

# Sin Docker
python -m backend
```

### 6.5 Paso 4: Verificar que LTI esta Activo

```bash
curl https://tu-dominio.com/api/v1/lti/health
```

Deberia retornar:
```json
{
  "status": "warning",
  "state_cache_size": 0,
  "nonce_cache_size": 0,
  "jwks_cache_size": 0,
  "message": "LTI router loaded but NOT registered in main.py"
}
```

Si el mensaje dice "LTI router loaded", el sistema esta listo para recibir launches.

---

## 7. Configuracion de Moodle - Guia Completa para Administradores

Esta seccion proporciona instrucciones detalladas paso a paso para configurar Moodle como plataforma LTI que se conecta con AI-Native. Las instrucciones estan escritas asumiendo Moodle 4.x, pero son compatibles con Moodle 3.9+.

### 7.1 Prerequisitos en Moodle

Antes de comenzar, verifica que tu instalacion de Moodle cumple con estos requisitos:

**Version de Moodle:**
- Minimo: Moodle 3.9 (primera version con soporte LTI 1.3 completo)
- Recomendado: Moodle 4.0 o superior (mejor interfaz de administracion)

**Permisos requeridos:**
- Debes tener rol de **Administrador del sitio** (Site Administrator)
- Acceso a **Site administration** en el menu principal

**Verificar version de Moodle:**
1. Inicia sesion como administrador
2. Ve a **Site administration > Notifications**
3. La version aparece en la esquina superior derecha o en la pagina de notificaciones

**Servidor correctamente configurado:**
- HTTPS habilitado (LTI 1.3 requiere conexiones seguras)
- Certificado SSL valido (no auto-firmado en produccion)
- Cron de Moodle ejecutandose (para tareas de sincronizacion)

### 7.2 Acceder al Panel de Administracion de Herramientas Externas

El primer paso es acceder a la seccion donde se gestionan las herramientas LTI. Moodle llama a estas herramientas "External tools" (herramientas externas).

**Navegacion:**

```
Site administration > Plugins > Activity modules > External tool > Manage tools
```

**Pasos detallados:**

1. **Inicia sesion** en Moodle con tu cuenta de administrador.

2. En el panel lateral izquierdo o en el menu hamburguesa, busca **"Site administration"** (Administracion del sitio). En Moodle 4.x aparece como un icono de engranaje.

3. En el arbol de navegacion de administracion, expande:
   - **Plugins** (click para expandir)
   - **Activity modules** (click para expandir)
   - **External tool** (click para expandir)
   - Click en **Manage tools**

4. Llegaras a una pagina que muestra las herramientas LTI configuradas. Veras tres pestanas:
   - **Tools** - Herramientas activas
   - **Tool types** - Tipos de herramienta (plantillas)
   - **Tool proxies** - Proxies LTI 2.0 (no lo usaremos)

### 7.3 Registrar AI-Native como Herramienta Externa (LTI 1.3)

Ahora vamos a configurar AI-Native como una herramienta LTI 1.3. Este proceso tiene dos partes: primero creamos la configuracion de la herramienta en Moodle, y luego copiamos las credenciales generadas a AI-Native.

**Iniciar configuracion manual:**

1. En la pagina **Manage tools**, busca el boton **"configure a tool manually"** (configurar una herramienta manualmente). En algunas versiones aparece como **"Add tool"** con un icono de mas (+).

2. Click en ese boton para abrir el formulario de configuracion.

### 7.4 Formulario de Configuracion - Seccion "Tool Settings"

El formulario tiene multiples secciones. Comienza por la seccion principal de configuracion:

#### Tool name (Nombre de la herramienta)
```
AI-Native Tutor
```
Este nombre aparecera en la lista de herramientas y cuando los docentes agreguen actividades. Usa un nombre descriptivo que los docentes reconozcan facilmente.

#### Tool URL
```
https://TU-DOMINIO-AINATIVE.com/api/v1/lti/launch
```
**IMPORTANTE**: Reemplaza `TU-DOMINIO-AINATIVE.com` con el dominio real donde esta desplegado AI-Native. Por ejemplo:
- Desarrollo: `https://localhost:8000/api/v1/lti/launch` (requiere HTTPS)
- Produccion: `https://tutor-ia.universidad.edu/api/v1/lti/launch`

Este es el endpoint donde Moodle enviara el JWT despues del flujo de autenticacion.

#### Tool description (Descripcion)
```
Tutor de Inteligencia Artificial para aprendizaje de programacion con evaluacion basada en proceso cognitivo N4.
```
Esta descripcion ayuda a los docentes a entender que hace la herramienta.

#### LTI version
Selecciona: **LTI 1.3**

Esta es la opcion critica. NO selecciones "Legacy LTI" o "LTI 1.0/1.1" ya que AI-Native solo soporta LTI 1.3.

### 7.5 Formulario de Configuracion - Seccion "Tool Configuration"

Esta seccion configura los parametros tecnicos de LTI 1.3:

#### Public key type
Selecciona: **Keyset URL**

Esto indica que AI-Native publicara sus claves publicas en una URL (en lugar de copiar la clave directamente). Es la opcion mas flexible ya que permite rotacion de claves.

#### Public keyset
```
https://TU-DOMINIO-AINATIVE.com/api/v1/lti/jwks
```
Esta URL es donde Moodle buscara las claves publicas de AI-Native para verificar tokens que AI-Native firme (necesario para LTI Advantage).

#### Initiate login URL
```
https://TU-DOMINIO-AINATIVE.com/api/v1/lti/login
```
Esta es la URL donde Moodle enviara la solicitud inicial de login OIDC cuando un estudiante haga clic en la actividad.

#### Redirection URI(s)
```
https://TU-DOMINIO-AINATIVE.com/api/v1/lti/launch
```
Puede ser la misma que Tool URL. Es la URL permitida para recibir el callback de autenticacion.

#### Custom parameters
Deja este campo **vacio** por ahora. Se puede usar para pasar parametros adicionales al tutor (como ID de actividad especifica).

### 7.6 Formulario de Configuracion - Seccion "Services"

Esta seccion configura que servicios LTI Advantage estaran disponibles. Aunque AI-Native actualmente no implementa estos servicios, es buena practica configurarlos para cuando se agreguen.

#### IMS LTI Assignment and Grade Services
Selecciona: **Use this service for grade sync and column management**

Esto permitira que AI-Native envie calificaciones de vuelta a Moodle (cuando se implemente AGS).

#### IMS LTI Names and Role Provisioning Services
Selecciona: **Use this service to retrieve members' information as needed**

Esto permitira que AI-Native obtenga la lista de estudiantes del curso (cuando se implemente NRPS).

#### Tool Settings
Selecciona: **Use this service as instructed by the tool**

### 7.7 Formulario de Configuracion - Seccion "Privacy"

Esta seccion es **muy importante** para AI-Native ya que determina que informacion del estudiante se comparte:

#### Share launcher's name with tool
Selecciona: **Always**

AI-Native necesita el nombre del estudiante para:
- Mostrar saludos personalizados
- Identificar trazas cognitivas
- Generar reportes por estudiante

#### Share launcher's email with tool
Selecciona: **Always**

El email sirve como identificador unico y para:
- Vincular sesiones del mismo estudiante
- Contacto si es necesario
- Deduplicacion de usuarios

#### Accept grades from the tool
Selecciona: **Always**

Aunque AI-Native actualmente no envia calificaciones, configurar esto permite habilitarlo en el futuro sin reconfiguracion.

### 7.8 Formulario de Configuracion - Seccion "Miscellaneous"

#### Default launch container
Selecciona: **Embed** o **New window** segun preferencia

- **Embed**: El tutor se muestra dentro de Moodle (en un iframe). Mejor experiencia integrada.
- **Embed without blocks**: Similar pero oculta los bloques laterales de Moodle.
- **New window**: Abre el tutor en una ventana/tab nueva. Mas espacio pero menos integracion.

Para AI-Native recomendamos **Embed** ya que el LTIContainer esta optimizado para este modo.

#### Content Selection URL
Deja **vacio**. Se usa para Deep Linking que no esta implementado.

#### Secure Tool URL
Deja **vacio** si ya usas HTTPS en Tool URL.

### 7.9 Guardar la Configuracion

1. Revisa que todos los campos esten completos
2. Click en **"Save changes"** (Guardar cambios) al final del formulario

**Despues de guardar**, Moodle procesara la configuracion y mostrara una pagina de confirmacion con las **credenciales generadas**. Esta informacion es **critica** - debes copiarla para configurar AI-Native.

### 7.10 Obtener Credenciales de Moodle

Despues de guardar, Moodle muestra una pantalla con la configuracion de la herramienta y las credenciales generadas. Busca la seccion **"Tool configuration details"** o similar.

Necesitas copiar estos valores:

| Campo en Moodle | Ejemplo | Descripcion |
|-----------------|---------|-------------|
| **Platform ID** | `https://moodle.universidad.edu` | El issuer - URL unica de tu Moodle |
| **Client ID** | `x7K9mPqR2sT4vW6y` | Identificador generado para AI-Native |
| **Deployment ID** | `1` | Normalmente es "1" para el primer deployment |
| **Public keyset URL** | `https://moodle.universidad.edu/mod/lti/certs.php` | Donde Moodle publica sus claves JWKS |
| **Access token URL** | `https://moodle.universidad.edu/mod/lti/token.php` | Para LTI Advantage (AGS) |
| **Authentication request URL** | `https://moodle.universidad.edu/mod/lti/auth.php` | URL de autenticacion OIDC |

**Tip**: Copia estos valores a un archivo de texto temporalmente. Los necesitaras para el siguiente paso.

Si cierras esta pagina y necesitas recuperar los valores:
1. Ve a **Site administration > Plugins > Activity modules > External tool > Manage tools**
2. Busca "AI-Native Tutor" en la lista
3. Click en el icono de configuracion (engranaje) junto a la herramienta
4. Los detalles de configuracion estaran disponibles

### 7.11 Registrar el Deployment en AI-Native

Con las credenciales de Moodle copiadas, ahora debes registrar este deployment en AI-Native. Hay dos metodos:

#### Metodo 1: Via API (Recomendado)

Ejecuta este comando reemplazando los valores con los que copiaste de Moodle:

```bash
curl -X POST https://TU-DOMINIO-AINATIVE.com/api/v1/lti/deployments \
  -H "Content-Type: application/json" \
  -d '{
    "platform_name": "Moodle Universidad XYZ",
    "issuer": "https://moodle.universidad.edu",
    "client_id": "x7K9mPqR2sT4vW6y",
    "deployment_id": "1",
    "auth_login_url": "https://moodle.universidad.edu/mod/lti/auth.php",
    "auth_token_url": "https://moodle.universidad.edu/mod/lti/token.php",
    "public_keyset_url": "https://moodle.universidad.edu/mod/lti/certs.php"
  }'
```

**Respuesta exitosa:**
```json
{
  "id": "uuid-generado",
  "platform_name": "Moodle Universidad XYZ",
  "issuer": "https://moodle.universidad.edu",
  "client_id": "x7K9mPqR2sT4vW6y",
  "deployment_id": "1",
  "is_active": true,
  "created_at": "2026-01-02T12:00:00Z"
}
```

#### Metodo 2: Via SQL Directo

Si prefieres insertar directamente en la base de datos:

```sql
INSERT INTO lti_deployments (
    id,
    platform_name,
    issuer,
    client_id,
    deployment_id,
    auth_login_url,
    auth_token_url,
    public_keyset_url,
    access_token_url,
    is_active,
    created_at
) VALUES (
    gen_random_uuid()::text,
    'Moodle Universidad XYZ',
    'https://moodle.universidad.edu',
    'x7K9mPqR2sT4vW6y',
    '1',
    'https://moodle.universidad.edu/mod/lti/auth.php',
    'https://moodle.universidad.edu/mod/lti/token.php',
    'https://moodle.universidad.edu/mod/lti/certs.php',
    'https://moodle.universidad.edu/mod/lti/token.php',
    true,
    NOW()
);
```

### 7.12 Verificar la Configuracion

Antes de probar con estudiantes, verifica que todo este configurado correctamente:

**En AI-Native:**
```bash
# Verificar que el deployment esta registrado
curl https://TU-DOMINIO-AINATIVE.com/api/v1/lti/deployments

# Verificar que LTI esta activo
curl https://TU-DOMINIO-AINATIVE.com/api/v1/lti/health
```

**En Moodle:**
1. Ve a **Site administration > Plugins > Activity modules > External tool > Manage tools**
2. Verifica que "AI-Native Tutor" aparece en la lista con estado activo

### 7.13 Crear una Actividad LTI en un Curso

Ahora que la herramienta esta configurada a nivel de sitio, los docentes pueden agregarla a sus cursos. Como administrador, puedes hacerlo tu o instruir a los docentes.

**Pasos para agregar la actividad:**

1. **Navega al curso** donde quieres agregar el tutor IA.

2. **Activa el modo de edicion**:
   - Moodle 4.x: Click en **"Edit mode"** (boton en la esquina superior derecha)
   - Moodle 3.x: Click en **"Turn editing on"** (boton o en el menu de engranaje)

3. En la seccion/tema donde quieres agregar la actividad, click en **"Add an activity or resource"** (Agregar actividad o recurso).

4. En el selector de actividades, busca **"External tool"** (Herramienta externa) y seleccionala.

5. En el formulario de configuracion:

   **Activity name (Nombre):**
   ```
   Tutor IA - Asistente de Programacion
   ```

   **Preconfigured tool:**
   Selecciona **"AI-Native Tutor"** del dropdown. Esto carga automaticamente toda la configuracion que creaste.

   **Description (Descripcion):**
   ```
   Accede al tutor de inteligencia artificial para resolver dudas de programacion.
   El sistema analiza tu proceso de resolucion y proporciona retroalimentacion
   personalizada segun tu nivel cognitivo.
   ```

6. **Opciones de privacidad** (Privacy):
   Asegurate de que esten habilitadas:
   - Share launcher's name with tool: Yes
   - Share launcher's email with tool: Yes

7. **Launch container** (Contenedor de lanzamiento):
   - **Embed**: Recomendado - el tutor aparece dentro de Moodle
   - **New window**: Alternativa - abre en ventana separada

8. Click en **"Save and return to course"** o **"Save and display"**

### 7.14 Probar el Launch como Estudiante

Para verificar que todo funciona:

1. **Cambia al rol de estudiante** en Moodle:
   - En el curso, busca el menu de usuario (esquina superior derecha)
   - Click en **"Switch role to..."** > **"Student"**

2. **Navega a la actividad** "Tutor IA" que creaste

3. **Click en la actividad** - deberia iniciar el flujo LTI:
   - Moodle te redirigira momentaneamente
   - Veras el tutor cargarse (dentro del iframe si elegiste Embed)
   - Si hay un banner naranja con tu nombre de curso, LTI funciona correctamente

4. **Verifica en AI-Native** que se creo la sesion:
   ```bash
   # Ver sesiones LTI recientes
   SELECT * FROM lti_sessions ORDER BY created_at DESC LIMIT 5;
   ```

5. **Regresar al rol de administrador**:
   - Click en **"Return to my normal role"** en el menu de usuario

### 7.15 Configuracion Avanzada - Parametros Personalizados

Los parametros personalizados permiten pasar informacion adicional de Moodle a AI-Native. Por ejemplo, para indicar que actividad especifica del tutor usar.

**En la configuracion de la herramienta o la actividad:**

Campo **Custom parameters**:
```
activity_type=programacion_basica
difficulty_level=beginner
language=python
```

Estos parametros llegaran al frontend como query params adicionales y pueden usarse para personalizar la experiencia.

### 7.16 Gestion de Multiples Moodles

Si necesitas conectar AI-Native a multiples instancias de Moodle (por ejemplo, Moodle de diferentes facultades), repite el proceso de registro para cada una:

1. Configura la herramienta en cada Moodle (secciones 7.3-7.9)
2. Registra cada deployment en AI-Native con un `platform_name` descriptivo

AI-Native identificara cada plataforma por su `issuer` (URL unica) y mantendra sesiones separadas.

**Ejemplo de multiples deployments:**
```bash
# Deployment 1 - Facultad de Ingenieria
curl -X POST .../lti/deployments -d '{
    "platform_name": "Moodle Ingenieria",
    "issuer": "https://moodle-ing.universidad.edu",
    ...
}'

# Deployment 2 - Facultad de Ciencias
curl -X POST .../lti/deployments -d '{
    "platform_name": "Moodle Ciencias",
    "issuer": "https://moodle-ciencias.universidad.edu",
    ...
}'
```

### 7.17 Desactivar un Deployment

Si necesitas desactivar temporalmente la integracion con un Moodle especifico (sin perder la configuracion):

```bash
# Desactivar deployment
curl -X DELETE https://TU-DOMINIO-AINATIVE.com/api/v1/lti/deployments/{deployment_id}
```

Esto marca el deployment como inactivo. Los intentos de launch desde ese Moodle retornaran error "Unknown LTI platform".

Para reactivar, actualmente debes actualizar directamente en la base de datos:
```sql
UPDATE lti_deployments SET is_active = true WHERE id = 'deployment-id';
```

---

## 8. Configuracion de AI-Native

### 8.1 Variables de Entorno Completas

El archivo `.env.example` documenta todas las variables disponibles:

```bash
# =============================================================================
# LTI 1.3 INTEGRATION (HU-SYS-010: Moodle Integration)
# =============================================================================

# Master switch - habilita/deshabilita toda la integracion
LTI_ENABLED=false

# URL del frontend para redirecciones post-launch
LTI_FRONTEND_URL=http://localhost:3000

# Seguridad OIDC
LTI_STATE_EXPIRATION_MINUTES=10   # TTL del token state
LTI_NONCE_EXPIRATION_HOURS=1      # Ventana de replay protection

# Cache de JWKS
LTI_JWKS_CACHE_TTL_SECONDS=3600   # 1 hora

# Claves RSA (solo necesario para LTI Advantage/AGS)
LTI_PRIVATE_KEY_PATH=
LTI_PUBLIC_KEY_PATH=
```

### 8.2 Generar Claves RSA (Opcional)

Las claves RSA solo son necesarias si planeas implementar LTI Advantage (envio de calificaciones a Moodle). Para el flujo basico no son requeridas.

```bash
# Crear directorio
mkdir -p keys

# Generar clave privada RSA 2048 bits
openssl genrsa -out keys/lti_private.pem 2048

# Extraer clave publica
openssl rsa -in keys/lti_private.pem -pubout -out keys/lti_public.pem

# Verificar
openssl rsa -in keys/lti_private.pem -check
```

Luego actualiza el `.env`:

```bash
LTI_PRIVATE_KEY_PATH=/app/keys/lti_private.pem
LTI_PUBLIC_KEY_PATH=/app/keys/lti_public.pem
```

### 8.3 Deployment via SQL (Alternativa)

Si prefieres registrar el deployment directamente en la base de datos:

```sql
INSERT INTO lti_deployments (
    id,
    platform_name,
    issuer,
    client_id,
    deployment_id,
    auth_login_url,
    auth_token_url,
    public_keyset_url,
    access_token_url,
    is_active,
    created_at
) VALUES (
    gen_random_uuid()::text,
    'Moodle Universidad',
    'https://tu-moodle.edu',
    'abc123xyz',
    '1',
    'https://tu-moodle.edu/mod/lti/auth.php',
    'https://tu-moodle.edu/mod/lti/token.php',
    'https://tu-moodle.edu/mod/lti/certs.php',
    'https://tu-moodle.edu/mod/lti/token.php',
    true,
    NOW()
);
```

---

## 9. Flujo de Autenticacion Detallado

### 9.1 Diagrama de Secuencia

```
Estudiante          Moodle              AI-Native           AI-Native
  (Browser)        (Platform)          (LTI Router)         (Frontend)
     |                 |                    |                    |
     | 1. Click        |                    |                    |
     |    "Tutor IA"   |                    |                    |
     |---------------->|                    |                    |
     |                 |                    |                    |
     |    2. OIDC      |                    |                    |
     |    Login Init   |                    |                    |
     |<----------------|                    |                    |
     |  (redirect)     |                    |                    |
     |                 |                    |                    |
     | 3. GET /lti/login                    |                    |
     |-----------------|------------------>|                    |
     |                 |   iss, login_hint |                    |
     |                 |   target_link_uri |                    |
     |                 |                    |                    |
     |                 |   4. Validate     |                    |
     |                 |      issuer       |                    |
     |                 |      Generate     |                    |
     |                 |      state/nonce  |                    |
     |                 |      Store in     |                    |
     |                 |      cache        |                    |
     |                 |                    |                    |
     |    5. Redirect  |                    |                    |
     |    to Moodle    |                    |                    |
     |<----------------|<-------------------|                    |
     |  (auth request) |                    |                    |
     |                 |                    |                    |
     | 6. Follow       |                    |                    |
     |    redirect     |                    |                    |
     |---------------->|                    |                    |
     |                 |                    |                    |
     |                 | 7. Authenticate   |                    |
     |                 |    user (already  |                    |
     |                 |    logged in)     |                    |
     |                 |                    |                    |
     |                 | 8. Generate JWT   |                    |
     |                 |    Sign with      |                    |
     |                 |    private key    |                    |
     |                 |                    |                    |
     |    9. POST      |                    |                    |
     |    /lti/launch  |                    |                    |
     |<----------------|                    |                    |
     |  (form_post)    |                    |                    |
     |                 |                    |                    |
     | 10. Submit form |                    |                    |
     |-----------------|------------------>|                    |
     |                 |  id_token, state  |                    |
     |                 |                    |                    |
     |                 |   11. Verify      |                    |
     |                 |       state       |                    |
     |                 |                    |                    |
     |                 |   12. Fetch JWKS  |                    |
     |                 |       from Moodle |                    |
     |                 |                    |                    |
     |                 |   13. Validate    |                    |
     |                 |       JWT sig     |                    |
     |                 |                    |                    |
     |                 |   14. Verify      |                    |
     |                 |       nonce       |                    |
     |                 |                    |                    |
     |                 |   15. Extract     |                    |
     |                 |       claims      |                    |
     |                 |                    |                    |
     |                 |   16. Create/Get  |                    |
     |                 |       user        |                    |
     |                 |                    |                    |
     |                 |   17. Create/Get  |                    |
     |                 |       session     |                    |
     |                 |                    |                    |
     |                 |   18. Create      |                    |
     |                 |       LTI session |                    |
     |                 |                    |                    |
     |    19. Redirect |                    |                    |
     |    to frontend  |                    |                    |
     |<----------------|<-------------------|                    |
     |  /tutor?session_id=xxx&lti=true      |                    |
     |                 |                    |                    |
     | 20. Load frontend                    |                    |
     |-----------------|--------------------|------------------->|
     |                 |                    |                    |
     |                 |                    |   21. Detect LTI   |
     |                 |                    |       params       |
     |                 |                    |                    |
     |                 |                    |   22. Initialize   |
     |                 |                    |       LTIContainer |
     |                 |                    |                    |
     |                 |                    |   23. Show tutor   |
     |                 |                    |       with context |
     |                 |                    |                    |
     |    24. Tutor    |                    |                    |
     |    ready!       |                    |                    |
     |<----------------|--------------------|--------------------|
```

### 9.2 Claims JWT del Launch

Cuando Moodle envia el JWT, contiene claims estandar y LTI-especificos:

```json
{
  "iss": "https://moodle.universidad.edu",
  "aud": "abc123xyz",
  "sub": "user123",
  "exp": 1702500000,
  "iat": 1702496400,
  "nonce": "uuid-nonce-generado",
  "name": "Juan Perez",
  "email": "juan.perez@universidad.edu",
  "locale": "es_AR",

  "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
  "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
  "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "1",

  "https://purl.imsglobal.org/spec/lti/claim/context": {
    "id": "course123",
    "label": "PROG1",
    "title": "Programacion I - Comision A",
    "type": ["CourseSection"]
  },

  "https://purl.imsglobal.org/spec/lti/claim/resource_link": {
    "id": "resource789",
    "title": "Actividad Tutor IA"
  },

  "https://purl.imsglobal.org/spec/lti/claim/roles": [
    "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
  ]
}
```

### 9.3 Mapeo de Datos LTI a AI-Native

El router extrae los claims y los mapea a entidades de AI-Native:

| LTI Claim | AI-Native Field | Descripcion |
|-----------|-----------------|-------------|
| `sub` | Usuario hash | SHA256 de `issuer:sub` (identificador unico) |
| `name` | `LTISession.lti_user_name` | **Nombre completo** del estudiante |
| `email` | `LTISession.lti_user_email` | Email del estudiante |
| `context.id` | `LTISession.lti_context_id` | ID interno del curso |
| `context.label` | `LTISession.lti_context_label` | **Comision** (ej: "PROG1-A") |
| `context.title` | `LTISession.lti_context_title` | **Nombre del curso** |
| `resource_link.id` | `LTISession.resource_link_id` | ID unico de la actividad |
| `resource_link.title` | `LTISession.resource_link_title` | **Nombre de la actividad** |
| `roles` | Rol de usuario | Buscar "Instructor" para rol docente |

---

## 10. Frontend en Modo Embebido

### 10.1 Deteccion de Contexto LTI

Cuando el frontend carga despues de un launch LTI, la URL contiene parametros especiales:

```
https://tu-dominio.com/tutor?session_id=abc123&lti=true
```

El servicio `ltiService.detectLTIContext()` lee estos parametros y retorna:

```typescript
{
  isLTI: true,
  sessionId: "abc123",
  contextTitle: null,  // Se puede obtener del backend
  userName: null       // Se puede obtener del backend
}
```

### 10.2 Uso del LTIContainer

El componente LTIContainer se usa como wrapper en las rutas que soportan LTI:

```tsx
// En App.tsx o en la ruta /tutor
import { LTIContainer } from './components/LTIContainer';

function TutorRoute() {
  return (
    <LTIContainer showBanner={true}>
      <TutorPage />
    </LTIContainer>
  );
}
```

El LTIContainer automaticamente:
- Detecta si hay parametros LTI en la URL
- Los almacena en sessionStorage
- Muestra un banner con el contexto del curso
- Aplica estilos para modo embebido

### 10.3 Hook useLTIContext

Cualquier componente puede acceder al contexto LTI usando el hook:

```tsx
import { useLTIContext } from './components/LTIContainer';

function MyComponent() {
  const { isLTI, isEmbedded, context } = useLTIContext();

  if (isLTI) {
    return <p>Bienvenido desde {context?.contextTitle}</p>;
  }

  return <p>Acceso directo</p>;
}
```

### 10.4 Estilos para Modo Embebido

Cuando la app esta en modo LTI/embebido, se aplican clases CSS especiales:

- `.lti-mode`: Aplicada cuando `isLTI=true`
- `.lti-embedded`: Aplicada cuando esta en iframe
- `.lti-compact`: Aplicada para reducir espaciado

Puedes ocultar elementos en modo LTI:

```css
.lti-mode .hide-in-lti {
  display: none !important;
}
```

O mostrar elementos solo en modo LTI:

```css
.show-in-lti {
  display: none !important;
}
.lti-mode .show-in-lti {
  display: block !important;
}
```

---

## 11. LTI Advantage Services

### 11.1 Assignment and Grade Services (AGS)

LTI-AGS permite enviar calificaciones de AI-Native a Moodle. Esto es util para:
- Reportar el puntaje de proceso del estudiante
- Sincronizar evaluaciones automaticamente
- Mantener el libro de calificaciones actualizado

**Estado**: No implementado. Requiere:
1. Generar claves RSA para AI-Native
2. Implementar obtencion de access tokens
3. Implementar endpoint para enviar scores
4. Integrar con el sistema de evaluacion existente

### 11.2 Names and Role Provisioning Services (NRPS)

LTI-NRPS permite obtener la lista de estudiantes del curso desde Moodle. Util para:
- Generar reportes comparativos sin ingreso manual
- Detectar estudiantes que no han accedido
- Sincronizar roster automaticamente

**Estado**: No implementado.

### 11.3 Deep Linking

Deep Linking permite que docentes seleccionen contenido especifico de AI-Native para agregar a su curso. Por ejemplo, podrian elegir un tema o actividad especifica del tutor.

**Estado**: No implementado.

---

## 11.5. Vinculacion de Actividades Moodle-AI-Native (Cortez65.1)

Esta funcionalidad permite al docente vincular actividades de AI-Native con actividades de Moodle para que cuando un estudiante haga clic en la actividad de Moodle, automaticamente se cargue la actividad correcta en AI-Native con sus politicas pedagogicas.

### 11.5.1 Flujo de Vinculacion

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONFIGURACION (Docente)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Docente crea actividad en AI-Native con politicas                       │
│  2. Docente crea actividad LTI en Moodle (nombre: "Ejercicio 1")           │
│  3. Docente vincula ambas usando POST /api/v1/lti/activities/link          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EJECUCION (Estudiante)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Estudiante hace clic en "Ejercicio 1" en Moodle                        │
│  2. Moodle envia LTI launch con resource_link_title = "Ejercicio 1"        │
│  3. AI-Native busca actividad donde moodle_resource_name = "Ejercicio 1"   │
│  4. Se carga la actividad del docente con sus politicas                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.5.2 Campos de Vinculacion en ActivityDB

```python
# Nuevos campos agregados a ActivityDB (Cortez65.1)
moodle_course_id    # context_id de Moodle (ID unico del curso)
moodle_course_name  # context_title (nombre del curso)
moodle_course_label # context_label (codigo de comision, ej: "PROG1-A")
moodle_resource_name # resource_link_title (nombre de la actividad en Moodle)
```

### 11.5.3 API de Vinculacion

**Vincular actividad a Moodle:**

```bash
POST /api/v1/lti/activities/link
Content-Type: application/json

{
    "activity_id": "actividad_variables_python",
    "moodle_course_id": "course123",
    "moodle_course_name": "Programacion I",
    "moodle_course_label": "PROG1-A",
    "moodle_resource_name": "Ejercicio 1: Variables en Python"
}
```

**Respuesta:**
```json
{
    "success": true,
    "message": "Activity 'Variables en Python' linked to Moodle",
    "activity_id": "actividad_variables_python",
    "moodle_course_id": "course123",
    "moodle_course_name": "Programacion I",
    "moodle_course_label": "PROG1-A",
    "moodle_resource_name": "Ejercicio 1: Variables en Python"
}
```

**Desvincular actividad:**

```bash
DELETE /api/v1/lti/activities/actividad_variables_python/link
```

**Listar actividades vinculadas:**

```bash
GET /api/v1/lti/activities/linked?teacher_id=uuid-del-docente
```

### 11.5.4 Estrategia de Matching

Cuando un estudiante hace launch desde Moodle, AI-Native busca la actividad en dos pasos:

1. **Match exacto**: `moodle_course_id` + `moodle_resource_name` (mas especifico)
2. **Fallback**: Solo `moodle_resource_name` (para actividades compartidas entre cursos)

Si no hay match, se usa el `resource_link_id` de Moodle como identificador de actividad.

### 11.5.5 Ejemplo Completo

**Paso 1: Docente crea actividad en AI-Native**

```bash
POST /api/v1/activities
{
    "activity_id": "ej1_variables_python",
    "title": "Ejercicio 1: Variables en Python",
    "instructions": "Implementa una funcion que...",
    "policies": {
        "max_help_level": "MEDIO",
        "block_complete_solutions": true
    }
}
```

**Paso 2: Docente crea actividad LTI en Moodle**

En Moodle, crea una actividad LTI con nombre "Ejercicio 1: Variables en Python" apuntando a AI-Native.

**Paso 3: Docente vincula ambas**

```bash
POST /api/v1/lti/activities/link
{
    "activity_id": "ej1_variables_python",
    "moodle_course_id": "course456",
    "moodle_course_name": "Programacion I - 2026",
    "moodle_course_label": "PROG1-A",
    "moodle_resource_name": "Ejercicio 1: Variables en Python"
}
```

**Paso 4: Estudiante accede desde Moodle**

Cuando "Juan Perez" hace clic en la actividad en Moodle, AI-Native:
1. Recibe el LTI launch con `resource_link_title = "Ejercicio 1: Variables en Python"`
2. Busca en `activities` donde `moodle_resource_name = "Ejercicio 1: Variables en Python"`
3. Encuentra la actividad `ej1_variables_python`
4. Crea una sesion vinculada a esa actividad
5. Aplica las politicas del docente (`max_help_level: MEDIO`, etc.)

---

## 12. Integracion con el Sistema de Agentes

### 12.1 Contexto LTI en Sesiones

Cuando una sesion proviene de un launch LTI, el contexto se almacena y esta disponible para los agentes:

```python
# En session.context - Datos disponibles de Moodle
{
    "lti_launch": True,
    "lti_user_name": "Juan Perez",            # Nombre completo del estudiante
    "lti_context_id": "course123",
    "lti_context_label": "PROG1-A",           # Comision
    "lti_context_title": "Programacion I",    # Nombre del curso
    "resource_link_title": "Ejercicio 1: Variables",  # Nombre de la actividad
    "is_instructor": False,
    "roles": ["Learner"]
}
```

### 12.2 Politicas por Curso (GOV-IA)

El agente de gobernanza puede aplicar politicas diferenciadas segun el curso:

```python
# Ejemplo de politica por curso
if session.context.get("lti_context_id") == "curso_avanzado":
    policy = {
        "max_ai_assistance": 0.5,  # Menos ayuda
        "require_justification": True
    }
else:
    policy = default_policy
```

### 12.3 Trazabilidad N4 con Contexto Academico

Las trazas N4 generadas durante una sesion LTI incluyen el contexto del curso, permitiendo:
- Agrupar trazas por curso para analisis institucional
- Comparar progreso entre cursos
- Generar reportes por cohorte

---

## 13. Seguridad y Gobernanza

### 13.1 Medidas de Seguridad Implementadas

| Aspecto | Medida | Implementacion |
|---------|--------|----------------|
| **Transporte** | Solo HTTPS | Configuracion de deployment |
| **State** | UUID aleatorio, TTL 10 min | Cache en memoria |
| **Nonce** | Uso unico, TTL 1 hora | Cache en memoria |
| **JWT** | Validacion completa con JWKS | python-jose |
| **Issuer** | Whitelist de deployments | Base de datos |
| **Client ID** | Validacion contra deployment | Router |

### 13.2 Proteccion contra Ataques

**CSRF (Cross-Site Request Forgery)**:
- El parametro `state` es un UUID generado por AI-Native
- Solo se acepta si coincide con uno previamente generado
- Se consume inmediatamente (one-time use)

**Replay Attacks**:
- El parametro `nonce` se valida contra una lista de usados
- Si el nonce ya fue usado, se rechaza el launch
- Los nonces expiran despues de 1 hora

**Token Tampering**:
- Los JWT se validan usando las claves publicas de Moodle
- Se verifica firma, issuer, audience y expiracion
- No se aceptan tokens auto-firmados

### 13.3 Auditoria

Se recomienda agregar logging de eventos LTI:

```python
logger.info(
    "LTI launch: user=%s, context=%s, resource=%s",
    lti_user_id, lti_context_id, resource_link_id,
    extra={
        "event": "lti_launch",
        "deployment": deployment.id,
        "success": True
    }
)
```

---

## 14. Testing

### 14.1 Herramientas de Prueba

| Herramienta | URL | Uso |
|-------------|-----|-----|
| **IMS LTI RI** | https://lti-ri.imsglobal.org | Test completo LTI 1.3 |
| **Moodle Sandbox** | https://sandbox.moodledemo.net | Moodle de prueba |
| **JWT.io** | https://jwt.io | Depurar tokens |

### 14.2 Tests Manuales

1. **Verificar JWKS**:
```bash
curl https://tu-dominio.com/api/v1/lti/jwks
# Deberia retornar {"keys": [...]}
```

2. **Verificar Health**:
```bash
curl https://tu-dominio.com/api/v1/lti/health
# Deberia retornar status ok/warning
```

3. **Listar Deployments**:
```bash
curl https://tu-dominio.com/api/v1/lti/deployments
# Deberia mostrar deployments registrados
```

### 14.3 Test con Moodle Sandbox

1. Crea una cuenta en https://sandbox.moodledemo.net
2. Registra AI-Native como herramienta externa
3. Crea un curso de prueba
4. Agrega una actividad LTI
5. Verifica que el launch funcione

---

## 15. Troubleshooting

### 15.1 Errores Comunes

| Error | Causa | Solucion |
|-------|-------|----------|
| "Unknown LTI platform" | Issuer no registrado | Verificar deployment en BD |
| "Invalid or expired state parameter" | State expirado o no existe | Verificar TTL, reiniciar launch |
| "Failed to verify platform credentials" | JWKS no accesible | Verificar URL, limpiar cache |
| "Invalid nonce" | Nonce no coincide | Verificar almacenamiento |
| "Deployment ID mismatch" | Configuracion incorrecta | Verificar deployment_id |

### 15.2 Debugging

**Verificar configuracion**:
```bash
# En el servidor
grep LTI .env
```

**Verificar deployments**:
```sql
SELECT * FROM lti_deployments WHERE is_active = true;
```

**Verificar conectividad con Moodle**:
```bash
curl -I https://tu-moodle.edu/mod/lti/certs.php
```

**Ver logs del router**:
```bash
docker-compose logs api | grep LTI
```

### 15.3 Problemas de Iframe

Si el contenido no se muestra en el iframe de Moodle:

1. Verificar headers de seguridad (X-Frame-Options, CSP)
2. Verificar que el frontend permite embedding
3. Verificar que las cookies tienen SameSite=None

---

## 16. Proximos Pasos

### 16.1 Fase Actual Completada

- [x] Router LTI con OIDC (Cortez65)
- [x] Variables de entorno (Cortez65)
- [x] Frontend LTI service (Cortez65)
- [x] LTIContainer component (Cortez65)
- [x] Documentacion actualizada (Cortez65)

### 16.2 Pendiente para Habilitacion

- [ ] Registrar router en main.py
- [ ] Configurar deployment de Moodle real
- [ ] Test de integracion completo
- [ ] Autenticacion de endpoints admin

### 16.3 Mejoras Futuras

- [ ] Implementar LTI-AGS (calificaciones)
- [ ] Implementar LTI-NRPS (roster)
- [ ] Migracion a Redis para state/nonce (produccion)
- [ ] Dashboard de administracion LTI
- [ ] Deep Linking

---

## Referencias

### Especificaciones

- [IMS LTI 1.3 Specification](https://www.imsglobal.org/spec/lti/v1p3/)
- [LTI Advantage](https://www.imsglobal.org/lti-advantage-overview)
- [LTI Security Framework](https://www.imsglobal.org/spec/security/v1p0/)

### Documentacion Moodle

- [Moodle LTI Provider](https://docs.moodle.org/en/LTI_and_Moodle)
- [External Tool Settings](https://docs.moodle.org/en/External_tool_settings)

### Librerias Utilizadas

| Libreria | Uso |
|----------|-----|
| **python-jose** | Validacion JWT con JWKS |
| **httpx** | HTTP client async para JWKS |
| **pydantic** | Validacion de schemas |

---

**Documento actualizado**: Enero 2026 (Cortez65)
**Autor**: Claude Code (Implementacion y Documentacion)
**Proyecto**: AI-Native MVP - Tesis Doctoral
**Historia de Usuario**: HU-SYS-010 - Integracion LTI 1.3
