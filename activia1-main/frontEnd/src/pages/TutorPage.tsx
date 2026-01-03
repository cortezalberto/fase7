/**
 * TutorPage - AI Tutor chat page
 *
 * Cortez43: Refactored from 605 lines to ~180 lines
 * Extracted: useTutorSession, useRiskAnalysis, useTraceability hooks
 * Extracted: TutorHeader, ChatMessageBubble, ChatInput, SuggestedQuestions,
 *            TypingIndicator, Modal components
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../shared/components/Toast/Toast';
import { Loader2, FileText, Code2, MessageCircle, Sparkles, BookOpen, HelpCircle } from 'lucide-react';
import Editor from '@monaco-editor/react';

// Feature imports
import {
  TutorHeader,
  ChatMessageBubble,
  ChatInput,
  SuggestedQuestions,
  TypingIndicator,
  Modal,
  useTutorSession,
  useRiskAnalysis,
  useTraceability,
} from '../features/tutor';

// Components
import CreateSessionModal from '../components/CreateSessionModal';
import TraceabilityDisplay from '../components/TraceabilityDisplay';
import RiskAnalysisViewer from '../components/RiskAnalysisViewer';

// Hardcoded data for nested combos (Cortez63)
const HARDCODED_DATA = {
  languages: [
    { id: 'python', name: 'Python' }
  ],
  units: {
    python: [
      { id: 'estructuras-secuenciales', name: 'Estructuras Secuenciales' }
    ]
  },
  exercises: {
    'estructuras-secuenciales': [
      { id: 'ejercicio-1', name: 'Ejercicio 1' }
    ]
  },
  // Enunciados de ejercicios (Cortez63)
  exerciseStatements: {
    'ejercicio-1': {
      title: 'Ejercicio 1: Calculadora de Promedio',
      description: `Escribe un programa en Python que solicite al usuario tres calificaciones numéricas y calcule su promedio.

**Requisitos:**
1. Solicitar al usuario que ingrese tres calificaciones (pueden ser decimales)
2. Calcular el promedio de las tres calificaciones
3. Mostrar el resultado con dos decimales

**Ejemplo de ejecución:**
\`\`\`
Ingrese la primera calificación: 8.5
Ingrese la segunda calificación: 9.0
Ingrese la tercera calificación: 7.5
El promedio es: 8.33
\`\`\`

**Conceptos a aplicar:**
- Variables y asignación
- Entrada de datos con input()
- Conversión de tipos (float)
- Operaciones aritméticas
- Formateo de salida`,
      starterCode: `# Ejercicio 1: Calculadora de Promedio
# Escribe tu código aquí

# 1. Solicitar las tres calificaciones


# 2. Calcular el promedio


# 3. Mostrar el resultado

`
    }
  }
};

export default function TutorPage() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showChatModal, setShowChatModal] = useState(false);

  // Nested combo state (Cortez63)
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [selectedUnit, setSelectedUnit] = useState('');
  const [selectedExercise, setSelectedExercise] = useState('');

  // Code editor state (Cortez63)
  const [code, setCode] = useState('');

  // Get available units based on selected language
  const availableUnits = selectedLanguage
    ? HARDCODED_DATA.units[selectedLanguage as keyof typeof HARDCODED_DATA.units] || []
    : [];

  // Get available exercises based on selected unit
  const availableExercises = selectedUnit
    ? HARDCODED_DATA.exercises[selectedUnit as keyof typeof HARDCODED_DATA.exercises] || []
    : [];

  // Get current exercise statement (Cortez63)
  const currentExerciseData = selectedExercise
    ? HARDCODED_DATA.exerciseStatements[selectedExercise as keyof typeof HARDCODED_DATA.exerciseStatements]
    : null;

  // Reset dependent combos when parent changes
  const handleLanguageChange = (value: string) => {
    setSelectedLanguage(value);
    setSelectedUnit('');
    setSelectedExercise('');
  };

  const handleUnitChange = (value: string) => {
    setSelectedUnit(value);
    setSelectedExercise('');
  };

  // Initialize code when exercise is selected (Cortez63)
  const handleExerciseChange = (value: string) => {
    setSelectedExercise(value);
    if (value) {
      const exerciseData = HARDCODED_DATA.exerciseStatements[value as keyof typeof HARDCODED_DATA.exerciseStatements];
      if (exerciseData) {
        setCode(exerciseData.starterCode);
      }
    } else {
      setCode('');
    }
  };

  // Custom hooks
  const tutorSession = useTutorSession({
    userId: user?.id || 'guest',
    userName: user?.full_name || user?.username || 'estudiante',
    onError: (message) => showToast(message, 'error'),
  });

  const riskAnalysis = useRiskAnalysis({
    sessionId: tutorSession.session?.id || null,
    onError: (message, duration) => showToast(message, 'error', duration),
  });

  const traceability = useTraceability({
    onError: (message) => showToast(message, 'error'),
  });

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [tutorSession.messages]);

  // Initialize session on mount
  // Note: initializeSession is stable due to useCallback in useTutorSession
  const { initializeSession } = tutorSession;
  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  // Auto-refresh risk analysis when messages change
  const { analyzeRisks, showRiskPanel } = riskAnalysis;
  const sessionId = tutorSession.session?.id;
  const messagesLength = tutorSession.messages.length;
  useEffect(() => {
    if (sessionId && messagesLength > 1 && showRiskPanel) {
      const timer = setTimeout(() => {
        analyzeRisks(true); // Silent update
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [messagesLength, sessionId, showRiskPanel, analyzeRisks]);

  // Handle analyze traceability
  const handleAnalyzeTraceability = useCallback(() => {
    if (tutorSession.lastTraceId) {
      traceability.fetchTraceability(tutorSession.lastTraceId);
    } else {
      showToast('No hay trace_id disponible. Envía un mensaje primero.', 'warning');
    }
  }, [tutorSession.lastTraceId, traceability, showToast]);

  // Handle new session
  const handleNewSession = () => {
    tutorSession.resetSession();
    setShowCreateModal(false);
  };

  // Handle send message
  const { sendMessage, input } = tutorSession;
  const handleSendMessage = useCallback(() => {
    sendMessage(input);
  }, [sendMessage, input]);

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-4 animate-fadeIn">
      {/* Modals */}
      <CreateSessionModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSessionCreated={handleNewSession}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <TutorHeader
          lastTraceId={tutorSession.lastTraceId}
          isLoadingTraceability={traceability.isLoading}
          onAnalyzeTraceability={handleAnalyzeTraceability}
          hasSession={!!tutorSession.session}
          isLoadingRisks={riskAnalysis.isLoading}
          onAnalyzeRisks={() => riskAnalysis.analyzeRisks(false)}
          onNewSession={() => setShowCreateModal(true)}
          showRiskPanel={riskAnalysis.showRiskPanel}
          onToggleRiskPanel={riskAnalysis.toggleRiskPanel}
          courseName={user?.course_name}
          commission={user?.commission}
        />

        {/* Explanatory Panel - Cortez63 */}
        <div className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-xl p-4 mb-4">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">
                Bienvenido al Tutor IA
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="flex items-start gap-2">
                  <Code2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-[var(--text-secondary)]">
                    <span className="font-medium text-[var(--text-primary)]">Ejercitacion asistida por IA:</span> Selecciona un lenguaje, unidad y ejercicio para practicar con guia cognitiva personalizada.
                  </p>
                </div>
                <div className="flex items-start gap-2">
                  <BookOpen className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-[var(--text-secondary)]">
                    <span className="font-medium text-[var(--text-primary)]">Material de estudio:</span> Pregunta al Tutor sobre conceptos, ejemplos y recursos de aprendizaje de cada lenguaje.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-3 pt-3 border-t border-[var(--border-color)]">
                <HelpCircle className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                <p className="text-xs text-[var(--text-muted)]">
                  Usa el boton "Abrir Chat con Tutor IA" para hacer preguntas en cualquier momento.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Chat Button - Above Combos */}
        <div className="flex justify-center mb-4">
          <button
            onClick={() => setShowChatModal(true)}
            className="flex items-center gap-3 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium hover:from-indigo-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <MessageCircle className="w-6 h-6" />
            <span>Abrir Chat con Tutor IA</span>
            {tutorSession.messages.length > 1 && (
              <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
                {tutorSession.messages.length - 1} mensajes
              </span>
            )}
          </button>
        </div>

        {/* Nested Combo Boxes - Cortez63 */}
        <div className="flex items-center gap-4 mb-4">
          {/* Language Combo */}
          <div className="flex-1">
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
              Lenguaje
            </label>
            <select
              value={selectedLanguage}
              onChange={(e) => handleLanguageChange(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm focus:border-[var(--accent-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]/20 transition-all"
            >
              <option value="">Seleccionar lenguaje...</option>
              {HARDCODED_DATA.languages.map((lang) => (
                <option key={lang.id} value={lang.id}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          {/* Unit Combo */}
          <div className="flex-1">
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
              Unidad Temática
            </label>
            <select
              value={selectedUnit}
              onChange={(e) => handleUnitChange(e.target.value)}
              disabled={!selectedLanguage}
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm focus:border-[var(--accent-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">Seleccionar unidad...</option>
              {availableUnits.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.name}
                </option>
              ))}
            </select>
          </div>

          {/* Exercise Combo */}
          <div className="flex-1">
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
              Ejercicio
            </label>
            <select
              value={selectedExercise}
              onChange={(e) => handleExerciseChange(e.target.value)}
              disabled={!selectedUnit}
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm focus:border-[var(--accent-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">Seleccionar ejercicio...</option>
              {availableExercises.map((exercise) => (
                <option key={exercise.id} value={exercise.id}>
                  {exercise.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Exercise Panels - Cortez63 */}
        {currentExerciseData && (
          <div className="relative mb-4">
            {/* Panels Row */}
            <div className="flex gap-4" style={{ height: '600px' }}>
              {/* Left Panel - Exercise Statement */}
              <div className="flex-1 bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] flex flex-col overflow-hidden h-full">
                <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border-color)] bg-[var(--bg-tertiary)]">
                  <FileText className="w-5 h-5 text-[var(--accent-primary)]" />
                  <h3 className="font-semibold text-[var(--text-primary)]">Enunciado</h3>
                </div>
                <div className="flex-1 overflow-y-auto p-5">
                  <h4 className="text-lg font-bold text-[var(--text-primary)] mb-4">
                    {currentExerciseData.title}
                  </h4>
                  <div className="prose prose-invert max-w-none text-[var(--text-secondary)] text-sm leading-relaxed whitespace-pre-wrap">
                    {currentExerciseData.description}
                  </div>
                </div>
              </div>

              {/* Right Panel - Monaco Editor */}
              <div className="flex-1 bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] flex flex-col overflow-hidden h-full">
                <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border-color)] bg-[var(--bg-tertiary)]">
                  <Code2 className="w-5 h-5 text-emerald-500" />
                  <h3 className="font-semibold text-[var(--text-primary)]">Editor de Código</h3>
                  <span className="ml-auto text-xs text-[var(--text-muted)] bg-[var(--bg-secondary)] px-2 py-1 rounded">
                    Python
                  </span>
                </div>
                <div className="flex-1 min-h-0">
                  <Editor
                    height="100%"
                    defaultLanguage="python"
                    theme="vs-dark"
                    value={code}
                    onChange={(value) => setCode(value || '')}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      lineNumbers: 'on',
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                      tabSize: 4,
                      padding: { top: 16 },
                    }}
                  />
                </div>
              </div>
            </div>

          </div>
        )}

        {/* Traceability Modal */}
        <Modal
          isOpen={traceability.showModal}
          onClose={traceability.closeModal}
          title="Trazabilidad N4"
        >
          {traceability.traceData && <TraceabilityDisplay data={traceability.traceData} />}
        </Modal>

        {/* Risk Analysis Modal */}
        <Modal
          isOpen={riskAnalysis.showRiskModal}
          onClose={riskAnalysis.closeRiskModal}
          title="Análisis de Riesgos 5D"
          showCloseButton={true}
          contentStyle={{
            width: '80vw',
            maxWidth: '1400px',
            transform: 'translateX(-100px)'
          }}
        >
          <div style={{ maxHeight: '70vh', overflow: 'auto' }}>
            {riskAnalysis.riskData && <RiskAnalysisViewer data={riskAnalysis.riskData} />}
          </div>
        </Modal>

        {/* Chat Modal - Cortez63 */}
        <Modal
          isOpen={showChatModal}
          onClose={() => setShowChatModal(false)}
          title="Tutor IA - Chat de Ayuda"
          showCloseButton={true}
          contentStyle={{
            width: '80vw',
            maxWidth: '1200px'
          }}
        >
          <div className="flex flex-col" style={{ height: '70vh' }}>
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-scroll bg-[var(--bg-secondary)] rounded-lg">
              {tutorSession.isCreatingSession ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Loader2 className="w-8 h-8 text-[var(--accent-primary)] animate-spin mx-auto mb-4" />
                    <p className="text-[var(--text-secondary)]">Iniciando sesión...</p>
                  </div>
                </div>
              ) : (
                <>
                  {tutorSession.messages.map((message) => (
                    <ChatMessageBubble key={message.id} message={message} />
                  ))}

                  {tutorSession.isLoading && <TypingIndicator />}

                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Suggested Questions */}
            <SuggestedQuestions
              onSelect={tutorSession.setInput}
              visible={tutorSession.messages.length <= 1}
            />

            {/* Input Area */}
            <div className="mt-4">
              <ChatInput
                input={tutorSession.input}
                onInputChange={tutorSession.setInput}
                onSubmit={handleSendMessage}
                isLoading={tutorSession.isLoading}
                isDisabled={!tutorSession.session}
                sessionId={tutorSession.session?.id}
              />
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
}
