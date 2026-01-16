/**
 * useTestEditor - Hook for managing test editing state
 *
 * This hook provides complete state management for editing tests:
 * - Tracks editing mode (active/inactive)
 * - Manages working copy of questions (draft state)
 * - Provides add/delete/modify question operations
 * - Handles save (commit to storage) and reset (discard changes)
 *
 * @example
 * const {
 *   isEditing,
 *   draftQuestions,
 *   startEditing,
 *   cancelEditing,
 *   saveChanges,
 *   addQuestion,
 *   deleteQuestion,
 *   updateQuestion,
 * } = useTestEditor({ testId, initialQuestions, onSave });
 */

import { useState, useCallback, useMemo } from "react";
import type { TestQuestion, DifficultyLevel, QuestionType } from "../types/testTypes";

// Configuration for the hook
interface UseTestEditorConfig {
  /** The test ID being edited */
  testId: string;
  /** Initial questions array from the test */
  initialQuestions: TestQuestion[];
  /** Callback when changes are saved - receives updated questions array */
  onSave: (questions: TestQuestion[]) => Promise<void> | void;
}

// Return type for the hook
interface UseTestEditorResult {
  /** Whether editing mode is currently active */
  isEditing: boolean;
  /** Whether there are unsaved changes */
  hasChanges: boolean;
  /** Working copy of questions (draft state during editing) */
  draftQuestions: TestQuestion[];
  /** Whether save operation is in progress */
  isSaving: boolean;
  /** Error message if save failed */
  saveError: string | null;
  /** Enter editing mode - creates working copy of questions */
  startEditing: () => void;
  /** Exit editing mode and discard all changes */
  cancelEditing: () => void;
  /** Save changes and exit editing mode */
  saveChanges: () => Promise<void>;
  /** Add a new question to the draft */
  addQuestion: (question?: Partial<TestQuestion>) => void;
  /** Delete a question from the draft by ID */
  deleteQuestion: (questionId: string) => void;
  /** Update a question in the draft */
  updateQuestion: (questionId: string, updates: Partial<TestQuestion>) => void;
  /** Move a question up or down in the list */
  moveQuestion: (questionId: string, direction: "up" | "down") => void;
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
  difficulty: "medium" as DifficultyLevel,
  type: "single_choice" as QuestionType,
  explanation: "",
});

/**
 * Hook to manage test editing state and operations
 */
export function useTestEditor({
  testId: _testId, // Reserved for future API integration
  initialQuestions,
  onSave,
}: UseTestEditorConfig): UseTestEditorResult {
  // Note: _testId is available for future backend API calls if needed
  void _testId;

  // Core editing state
  const [isEditing, setIsEditing] = useState(false);
  const [draftQuestions, setDraftQuestions] = useState<TestQuestion[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Check if there are unsaved changes by comparing draft to initial
  const hasChanges = useMemo(() => {
    if (!isEditing) return false;
    // Simple deep comparison using JSON
    return JSON.stringify(draftQuestions) !== JSON.stringify(initialQuestions);
  }, [isEditing, draftQuestions, initialQuestions]);

  /**
   * Enter editing mode - creates a working copy of the questions
   */
  const startEditing = useCallback(() => {
    // Deep clone the initial questions to avoid mutations
    const clonedQuestions = JSON.parse(JSON.stringify(initialQuestions)) as TestQuestion[];
    setDraftQuestions(clonedQuestions);
    setIsEditing(true);
    setSaveError(null);
  }, [initialQuestions]);

  /**
   * Exit editing mode and discard all changes
   */
  const cancelEditing = useCallback(() => {
    setIsEditing(false);
    setDraftQuestions([]);
    setSaveError(null);
  }, []);

  /**
   * Save changes and exit editing mode
   */
  const saveChanges = useCallback(async () => {
    if (!isEditing || isSaving) return;

    setIsSaving(true);
    setSaveError(null);

    try {
      // Renumber questions before saving to ensure sequential order
      const renumberedQuestions = draftQuestions.map((q, index) => ({
        ...q,
        number: index + 1,
      }));

      await onSave(renumberedQuestions);
      setIsEditing(false);
      setDraftQuestions([]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Помилка збереження";
      setSaveError(message);
    } finally {
      setIsSaving(false);
    }
  }, [isEditing, isSaving, draftQuestions, onSave]);

  /**
   * Add a new question to the draft
   * Optionally accepts partial question data to pre-fill
   */
  const addQuestion = useCallback((question?: Partial<TestQuestion>) => {
    if (!isEditing) return;

    setDraftQuestions((prev) => {
      const newNumber = prev.length + 1;
      const newQuestion: TestQuestion = {
        ...createEmptyQuestion(newNumber),
        ...question,
        id: question?.id || generateQuestionId(),
        number: newNumber,
      };
      return [...prev, newQuestion];
    });
  }, [isEditing]);

  /**
   * Delete a question from the draft by ID
   */
  const deleteQuestion = useCallback((questionId: string) => {
    if (!isEditing) return;

    setDraftQuestions((prev) => {
      const filtered = prev.filter((q) => q.id !== questionId);
      // Renumber remaining questions
      return filtered.map((q, index) => ({
        ...q,
        number: index + 1,
      }));
    });
  }, [isEditing]);

  /**
   * Update a question in the draft
   */
  const updateQuestion = useCallback((questionId: string, updates: Partial<TestQuestion>) => {
    if (!isEditing) return;

    setDraftQuestions((prev) =>
      prev.map((q) =>
        q.id === questionId
          ? { ...q, ...updates }
          : q
      )
    );
  }, [isEditing]);

  /**
   * Move a question up or down in the list
   */
  const moveQuestion = useCallback((questionId: string, direction: "up" | "down") => {
    if (!isEditing) return;

    setDraftQuestions((prev) => {
      const index = prev.findIndex((q) => q.id === questionId);
      if (index === -1) return prev;

      const newIndex = direction === "up" ? index - 1 : index + 1;
      if (newIndex < 0 || newIndex >= prev.length) return prev;

      const newQuestions = [...prev];
      // Swap positions
      [newQuestions[index], newQuestions[newIndex]] = [newQuestions[newIndex], newQuestions[index]];
      // Renumber
      return newQuestions.map((q, i) => ({ ...q, number: i + 1 }));
    });
  }, [isEditing]);

  return {
    isEditing,
    hasChanges,
    draftQuestions,
    isSaving,
    saveError,
    startEditing,
    cancelEditing,
    saveChanges,
    addQuestion,
    deleteQuestion,
    updateQuestion,
    moveQuestion,
  };
}

export default useTestEditor;
