/**
 * Tutor Components - Barrel export
 *
 * Cortez43: Extracted from TutorPage.tsx (605 lines)
 * FIX Cortez48: Use shared Modal component instead of duplicate
 */

export { TutorHeader } from './TutorHeader';
export { ChatMessageBubble } from './ChatMessage';
export { ChatInput } from './ChatInput';
export { SuggestedQuestions } from './SuggestedQuestions';
export { TypingIndicator } from './TypingIndicator';
// FIX Cortez48: Re-export Modal from shared components to consolidate duplicates
export { Modal } from '@/shared/components/Modal/Modal';
