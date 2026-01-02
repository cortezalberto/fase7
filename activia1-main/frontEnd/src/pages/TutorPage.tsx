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
import { Loader2 } from 'lucide-react';

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
import RiskMonitorPanel from '../components/RiskMonitorPanel';

export default function TutorPage() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);

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
        />

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
        >
          {riskAnalysis.riskData && <RiskAnalysisViewer data={riskAnalysis.riskData} />}
        </Modal>

        {/* Chat Container */}
        <div className="flex-1 bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] flex flex-col overflow-hidden">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 chat-scroll">
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

          {/* Input Area */}
          <ChatInput
            input={tutorSession.input}
            onInputChange={tutorSession.setInput}
            onSubmit={handleSendMessage}
            isLoading={tutorSession.isLoading}
            isDisabled={!tutorSession.session}
            sessionId={tutorSession.session?.id}
          />
        </div>

        {/* Suggested Questions */}
        <SuggestedQuestions
          onSelect={tutorSession.setInput}
          visible={tutorSession.messages.length <= 1}
        />
      </div>

      {/* Risk Monitor Panel */}
      {riskAnalysis.showRiskPanel && (
        <div className="w-80 flex-shrink-0">
          <RiskMonitorPanel
            currentRiskLevel={riskAnalysis.riskData?.risk_level || 'info'}
            dimensions={riskAnalysis.riskData?.dimensions}
          />
        </div>
      )}
    </div>
  );
}
