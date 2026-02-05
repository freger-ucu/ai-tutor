/**
 * TestEditModal - Full-screen modal for editing test questions
 *
 * Provides a complete interface for teachers to:
 * - View all questions in a scrollable list
 * - Add new questions
 * - Delete existing questions
 * - Modify question content, options, and correct answers
 * - Save changes or reset to original state
 *
 * Uses useTestEditor hook for state management.
 *
 * @example
 * <TestEditModal
 *   isOpen={isEditing}
 *   testId={testId}
 *   testTitle={testData.title}
 *   questions={testData.questions}
 *   onSave={handleSaveQuestions}
 *   onClose={() => setIsEditing(false)}
 * />
 */

import { useCallback, useEffect, useState } from "react";
import type { TestQuestion } from "../types/testTypes";
import QuestionEditor from "./QuestionEditor";

interface TestEditModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** The test ID being edited */
  testId: string;
  /** The test title (for display) */
  testTitle: string;
  /** Initial questions array */
  questions: TestQuestion[];
  /** Callback when changes are saved */
  onSave: (questions: TestQuestion[]) => Promise<void> | void;
  /** Callback when modal is closed (without saving) */
  onClose: () => void;
}

/**
 * Generate a unique ID for new questions
 */
const generateQuestionId = (): string => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return `q-${crypto.randomUUID()}`;
  }
  return `q-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

/**
 * Create a new empty question with default values
 */
const createEmptyQuestion = (number: number): TestQuestion => ({
  id: generateQuestionId(),
  number,
  text: "",
  options: [
    { id: "opt-1", text: "" },
    { id: "opt-2", text: "" },
    { id: "opt-3", text: "" },
    { id: "opt-4", text: "" },
  ],
  correctOptionIds: [],
  difficulty: "medium",
  type: "single_choice",
  explanation: "",
});

const TestEditModal = ({
  isOpen,
  testId: _testId, // Reserved for future API integration
  testTitle,
  questions,
  onSave,
  onClose,
}: TestEditModalProps) => {
  // Note: _testId is available for future backend API calls if needed
  void _testId;
  // Local draft state for editing
  const [draftQuestions, setDraftQuestions] = useState<TestQuestion[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Initialize draft when modal opens
  useEffect(() => {
    if (isOpen) {
      // Deep clone to avoid mutations
      setDraftQuestions(JSON.parse(JSON.stringify(questions)));
      setSaveError(null);
    }
  }, [isOpen, questions]);

  // Check if there are unsaved changes
  const hasChanges = JSON.stringify(draftQuestions) !== JSON.stringify(questions);

  /**
   * Handle save - commit changes and close modal
   */
  const handleSave = useCallback(async () => {
    if (isSaving) return;

    setIsSaving(true);
    setSaveError(null);

    try {
      // Renumber questions before saving
      const renumberedQuestions = draftQuestions.map((q, index) => ({
        ...q,
        number: index + 1,
      }));

      await onSave(renumberedQuestions);
      onClose();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Помилка збереження";
      setSaveError(message);
    } finally {
      setIsSaving(false);
    }
  }, [draftQuestions, onSave, onClose, isSaving]);

  /**
   * Handle reset - discard all changes
   */
  const handleReset = useCallback(() => {
    // Reset to original questions
    setDraftQuestions(JSON.parse(JSON.stringify(questions)));
    setSaveError(null);
  }, [questions]);

  /**
   * Handle close - warn if unsaved changes
   */
  const handleClose = useCallback(() => {
    if (hasChanges) {
      const confirmed = window.confirm("Ви маєте незбережені зміни. Закрити без збереження?");
      if (!confirmed) return;
    }
    onClose();
  }, [hasChanges, onClose]);

  /**
   * Update a specific question
   */
  const updateQuestion = useCallback((questionId: string, updates: Partial<TestQuestion>) => {
    setDraftQuestions((prev) =>
      prev.map((q) => (q.id === questionId ? { ...q, ...updates } : q))
    );
  }, []);

  /**
   * Delete a question
   */
  const deleteQuestion = useCallback((questionId: string) => {
    setDraftQuestions((prev) => {
      const filtered = prev.filter((q) => q.id !== questionId);
      // Renumber remaining questions
      return filtered.map((q, index) => ({ ...q, number: index + 1 }));
    });
  }, []);

  /**
   * Move a question up or down
   */
  const moveQuestion = useCallback((questionId: string, direction: "up" | "down") => {
    setDraftQuestions((prev) => {
      const index = prev.findIndex((q) => q.id === questionId);
      if (index === -1) return prev;

      const newIndex = direction === "up" ? index - 1 : index + 1;
      if (newIndex < 0 || newIndex >= prev.length) return prev;

      const newQuestions = [...prev];
      [newQuestions[index], newQuestions[newIndex]] = [newQuestions[newIndex], newQuestions[index]];
      return newQuestions.map((q, i) => ({ ...q, number: i + 1 }));
    });
  }, []);

  /**
   * Add a new question
   */
  const addQuestion = useCallback(() => {
    setDraftQuestions((prev) => {
      const newQuestion = createEmptyQuestion(prev.length + 1);
      return [...prev, newQuestion];
    });
  }, []);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[#1E73F7]">
      {/* Header */}
      <header className="shrink-0 px-6 py-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-lg p-2 text-white/70 hover:bg-white/10 hover:text-white"
              title="Закрити"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
            <div>
              <h1 className="text-xl font-bold text-white">
                Редагування тесту
              </h1>
              <p className="text-sm text-white/70">{testTitle}</p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            {/* Reset button */}
            <button
              type="button"
              onClick={handleReset}
              disabled={!hasChanges || isSaving}
              className="rounded-full border border-white/20 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Скасувати
            </button>

            {/* Save button */}
            <button
              type="button"
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className="rounded-full border border-white bg-white px-5 py-2.5 text-sm font-semibold text-[#1E73F7] transition hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Збереження...
                </>
              ) : (
                "Зберегти"
              )}
            </button>
          </div>
        </div>

        {/* Error message */}
        {saveError && (
          <div className="max-w-6xl mx-auto mt-3">
            <div className="rounded-lg bg-red-100 border border-red-300 px-4 py-2 text-sm text-red-800">
              {saveError}
            </div>
          </div>
        )}
      </header>

      {/* Questions list */}
      <main className="flex-1 overflow-y-auto py-6">
        <div className="max-w-4xl mx-auto px-6 space-y-4">
          {draftQuestions.length === 0 ? (
            <div className="rounded-[22px] border border-dashed border-white/30 bg-white/10 p-12 text-center">
              <div className="text-white/50 mb-4">
                <svg className="mx-auto h-12 w-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M9 12h6M12 9v6M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-white font-medium">Тест не має питань</p>
              <p className="text-white/60 text-sm mt-1">Додайте перше питання</p>
            </div>
          ) : (
            draftQuestions.map((question, index) => (
              <QuestionEditor
                key={question.id}
                question={question}
                onChange={(updates) => updateQuestion(question.id, updates)}
                onDelete={() => deleteQuestion(question.id)}
                onMoveUp={() => moveQuestion(question.id, "up")}
                onMoveDown={() => moveQuestion(question.id, "down")}
                isFirst={index === 0}
                isLast={index === draftQuestions.length - 1}
              />
            ))
          )}

          {/* Add question button */}
          <button
            type="button"
            onClick={addQuestion}
            className="w-full rounded-full border border-white/20 bg-white/10 px-4 py-4 text-sm font-semibold text-white transition hover:bg-white/20 flex items-center justify-center gap-2"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Додати питання
          </button>
        </div>
      </main>

      {/* Footer with summary */}
      <footer className="shrink-0 px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-white/70">
          <div>
            Питань: <span className="font-semibold text-white">{draftQuestions.length}</span>
          </div>
          {hasChanges && (
            <div className="flex items-center gap-2 text-amber-300">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
              </svg>
              Є незбережені зміни
            </div>
          )}
        </div>
      </footer>
    </div>
  );
};

export default TestEditModal;
