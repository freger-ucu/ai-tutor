/**
 * TeacherTestEditor - Inline test editing component for teacher view
 *
 * Provides two modes:
 * 1. Read-only mode (default): Displays test questions in a read-only format
 * 2. Edit mode: Questions and answers become editable inputs
 *
 * Features:
 * - "Edit test" button to enter edit mode
 * - Save/Cancel buttons in edit mode
 * - Proper state cloning when entering edit mode
 * - Cancel fully reverts to original state
 * - Add/delete/modify questions
 * - Mark correct answers
 * - Edit question text, options, difficulty, type
 *
 * @example
 * <TeacherTestEditor
 *   testData={testData}
 *   onSave={handleSaveQuestions}
 * />
 */

import { useState, useCallback, useMemo } from "react";
import type { TestQuestion, TestData, DifficultyLevel, QuestionType, TestOption } from "../types/testTypes";
import TestNavigation from "./test/TestNavigation";

interface TeacherTestEditorProps {
  /** The test data to display/edit */
  testData: TestData;
  /** Callback when changes are saved */
  onSave: (questions: TestQuestion[]) => Promise<void> | void;
}

// Difficulty level options with labels
const DIFFICULTY_OPTIONS: { value: DifficultyLevel; label: string; color: string }[] = [
  { value: "easy", label: "Легкий", color: "bg-green-100 text-green-700" },
  { value: "medium", label: "Середній", color: "bg-yellow-100 text-yellow-700" },
  { value: "hard", label: "Складний", color: "bg-red-100 text-red-700" },
];

// Question type options with labels
const TYPE_OPTIONS: { value: QuestionType; label: string }[] = [
  { value: "single_choice", label: "Одна відповідь" },
  { value: "multiple_choice", label: "Декілька відповідей" },
  { value: "open", label: "Відкрите питання" },
];

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
 * Generate a unique ID for new options
 */
const generateOptionId = (): string => {
  return `opt-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
};

/**
 * Create a new empty question with default values
 */
const createEmptyQuestion = (number: number): TestQuestion => ({
  id: generateQuestionId(),
  number,
  text: "",
  options: [
    { id: generateOptionId(), text: "" },
    { id: generateOptionId(), text: "" },
    { id: generateOptionId(), text: "" },
    { id: generateOptionId(), text: "" },
  ],
  correctOptionIds: [],
  difficulty: "medium",
  type: "single_choice",
  explanation: "",
});

/**
 * Deep clone questions array to prevent mutations
 */
const cloneQuestions = (questions: TestQuestion[]): TestQuestion[] => {
  return JSON.parse(JSON.stringify(questions));
};

const TeacherTestEditor = ({ testData, onSave }: TeacherTestEditorProps) => {
  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Original questions (preserved when entering edit mode)
  const [originalQuestions, setOriginalQuestions] = useState<TestQuestion[]>([]);

  // Draft questions (edited copy)
  const [draftQuestions, setDraftQuestions] = useState<TestQuestion[]>(testData.questions);

  // Current question index for navigation
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // Questions to display (original when not editing, draft when editing)
  const displayQuestions = isEditMode ? draftQuestions : testData.questions;
  const currentQuestion = displayQuestions[currentQuestionIndex];

  // Track answered questions for navigation (in read-only mode, all are "answered")
  const answeredQuestionIndices = useMemo(() => {
    return new Set(displayQuestions.map((_, index) => index));
  }, [displayQuestions]);

  /**
   * Enter edit mode - clone original state
   */
  const handleStartEdit = useCallback(() => {
    // Store original questions for cancel operation
    setOriginalQuestions(cloneQuestions(testData.questions));
    // Create editable draft
    setDraftQuestions(cloneQuestions(testData.questions));
    setSaveError(null);
    setIsEditMode(true);
  }, [testData.questions]);

  /**
   * Cancel editing - restore original state
   */
  const handleCancelEdit = useCallback(() => {
    // Restore to original state before editing started
    setDraftQuestions(cloneQuestions(originalQuestions));
    setIsEditMode(false);
    setSaveError(null);
    // Reset to first question if current index is out of bounds
    if (currentQuestionIndex >= originalQuestions.length) {
      setCurrentQuestionIndex(0);
    }
  }, [originalQuestions, currentQuestionIndex]);

  /**
   * Save changes and exit edit mode
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
      setIsEditMode(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Помилка збереження";
      setSaveError(message);
    } finally {
      setIsSaving(false);
    }
  }, [draftQuestions, onSave, isSaving]);

  /**
   * Update a specific question in draft
   */
  const updateQuestion = useCallback((questionId: string, updates: Partial<TestQuestion>) => {
    setDraftQuestions((prev) =>
      prev.map((q) => (q.id === questionId ? { ...q, ...updates } : q))
    );
  }, []);

  /**
   * Delete a question from draft
   */
  const deleteQuestion = useCallback((questionId: string) => {
    setDraftQuestions((prev) => {
      const filtered = prev.filter((q) => q.id !== questionId);
      // Renumber remaining questions
      return filtered.map((q, index) => ({ ...q, number: index + 1 }));
    });
    // Adjust current index if needed
    setCurrentQuestionIndex((prev) => {
      const newLength = draftQuestions.length - 1;
      if (prev >= newLength && newLength > 0) {
        return newLength - 1;
      }
      return prev;
    });
  }, [draftQuestions.length]);

  /**
   * Add a new question to draft
   */
  const addQuestion = useCallback(() => {
    setDraftQuestions((prev) => {
      const newQuestion = createEmptyQuestion(prev.length + 1);
      return [...prev, newQuestion];
    });
    // Navigate to the new question
    setCurrentQuestionIndex(draftQuestions.length);
  }, [draftQuestions.length]);

  /**
   * Move question up or down
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
    // Update current index to follow the moved question
    setCurrentQuestionIndex((prev) => {
      if (direction === "up" && prev > 0) return prev - 1;
      if (direction === "down" && prev < draftQuestions.length - 1) return prev + 1;
      return prev;
    });
  }, [draftQuestions.length]);

  /**
   * Handle question text change
   */
  const handleTextChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (!currentQuestion) return;
      updateQuestion(currentQuestion.id, { text: e.target.value });
    },
    [currentQuestion, updateQuestion]
  );

  /**
   * Handle difficulty change
   */
  const handleDifficultyChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      if (!currentQuestion) return;
      updateQuestion(currentQuestion.id, { difficulty: e.target.value as DifficultyLevel });
    },
    [currentQuestion, updateQuestion]
  );

  /**
   * Handle question type change
   */
  const handleTypeChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      if (!currentQuestion) return;
      const newType = e.target.value as QuestionType;
      if (newType === "open") {
        updateQuestion(currentQuestion.id, { type: newType, correctOptionIds: [], options: [] });
      } else if (newType === "single_choice" && currentQuestion.correctOptionIds.length > 1) {
        updateQuestion(currentQuestion.id, { type: newType, correctOptionIds: currentQuestion.correctOptionIds.slice(0, 1) });
      } else {
        updateQuestion(currentQuestion.id, { type: newType });
      }
    },
    [currentQuestion, updateQuestion]
  );

  /**
   * Handle option text change
   */
  const handleOptionTextChange = useCallback(
    (optionId: string, text: string) => {
      if (!currentQuestion) return;
      const updatedOptions = currentQuestion.options.map((opt) =>
        opt.id === optionId ? { ...opt, text } : opt
      );
      updateQuestion(currentQuestion.id, { options: updatedOptions });
    },
    [currentQuestion, updateQuestion]
  );

  /**
   * Handle correct answer toggle
   */
  const handleCorrectToggle = useCallback(
    (optionId: string) => {
      if (!currentQuestion) return;
      const isCurrentlyCorrect = currentQuestion.correctOptionIds.includes(optionId);

      if (currentQuestion.type === "single_choice") {
        updateQuestion(currentQuestion.id, { correctOptionIds: isCurrentlyCorrect ? [] : [optionId] });
      } else {
        const newCorrectIds = isCurrentlyCorrect
          ? currentQuestion.correctOptionIds.filter((id) => id !== optionId)
          : [...currentQuestion.correctOptionIds, optionId];
        updateQuestion(currentQuestion.id, { correctOptionIds: newCorrectIds });
      }
    },
    [currentQuestion, updateQuestion]
  );

  /**
   * Add a new option to current question
   */
  const handleAddOption = useCallback(() => {
    if (!currentQuestion) return;
    const newOption: TestOption = {
      id: generateOptionId(),
      text: "",
    };
    updateQuestion(currentQuestion.id, { options: [...currentQuestion.options, newOption] });
  }, [currentQuestion, updateQuestion]);

  /**
   * Remove an option from current question
   */
  const handleRemoveOption = useCallback(
    (optionId: string) => {
      if (!currentQuestion) return;
      const updatedOptions = currentQuestion.options.filter((opt) => opt.id !== optionId);
      const updatedCorrectIds = currentQuestion.correctOptionIds.filter((id) => id !== optionId);
      updateQuestion(currentQuestion.id, { options: updatedOptions, correctOptionIds: updatedCorrectIds });
    },
    [currentQuestion, updateQuestion]
  );

  /**
   * Handle explanation change
   */
  const handleExplanationChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (!currentQuestion) return;
      updateQuestion(currentQuestion.id, { explanation: e.target.value });
    },
    [currentQuestion, updateQuestion]
  );

  /**
   * Navigate to question
   */
  const handleQuestionSelect = useCallback((index: number) => {
    setCurrentQuestionIndex(index);
  }, []);

  // Get difficulty display info
  const getDifficultyInfo = (difficulty: DifficultyLevel) => {
    return DIFFICULTY_OPTIONS.find((opt) => opt.value === difficulty) || DIFFICULTY_OPTIONS[1];
  };

  // Check if there are unsaved changes
  const hasChanges = isEditMode && JSON.stringify(draftQuestions) !== JSON.stringify(originalQuestions);

  if (!currentQuestion) {
    return (
      <div className="rounded-2xl bg-white p-8 text-center text-slate-500">
        Тест не має питань
        {isEditMode && (
          <button
            type="button"
            onClick={addQuestion}
            className="mt-4 rounded-xl bg-[#1E73F7] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#1557c0]"
          >
            Додати питання
          </button>
        )}
      </div>
    );
  }

  const isOpenQuestion = currentQuestion.type === "open";
  const difficultyInfo = getDifficultyInfo(currentQuestion.difficulty);

  return (
    <div className="space-y-6">
      {/* Header with Edit/Save/Cancel buttons */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <h2 className="text-lg font-bold text-white lg:text-xl">{testData.title}</h2>

        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          {!isEditMode ? (
            /* Edit button - visible in read-only mode */
            <button
              type="button"
              onClick={handleStartEdit}
              className="flex w-full items-center justify-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1557c0] hover:border-[#1557c0] lg:w-auto"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
              Редагувати тест
            </button>
          ) : (
            /* Save/Cancel buttons - visible in edit mode */
            <>
              <button
                type="button"
                onClick={handleCancelEdit}
                disabled={isSaving}
                className="w-full rounded-full border border-white/20 bg-white/10 px-5 py-2 text-sm font-semibold text-white transition hover:bg-[#1557c0] hover:border-[#1557c0] disabled:opacity-50 disabled:cursor-not-allowed lg:w-auto"
              >
                Скасувати
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={isSaving || !hasChanges}
                className="flex w-full items-center justify-center gap-2 rounded-full bg-[#6FDB9B] px-5 py-2 text-sm font-semibold text-white hover:bg-[#5BC88A] disabled:opacity-50 disabled:cursor-not-allowed lg:w-auto"
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
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
                      <polyline points="17,21 17,13 7,13 7,21" />
                      <polyline points="7,3 7,8 15,8" />
                    </svg>
                    Зберегти
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Error message */}
      {saveError && (
        <div className="rounded-lg bg-red-100 border border-red-300 px-4 py-2 text-sm text-red-700">
          {saveError}
        </div>
      )}

      {/* Edit mode indicator */}
      {isEditMode && (
        <div className="flex items-center gap-2 rounded-lg bg-amber-100 border border-amber-300 px-4 py-2 text-sm text-amber-700">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
          </svg>
          Режим редагування. Зміни не зберігаються автоматично.
          {hasChanges && <span className="ml-2 font-semibold">Є незбережені зміни.</span>}
        </div>
      )}

      {/* Navigation */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="hidden lg:block">
          <TestNavigation
            totalQuestions={displayQuestions.length}
            currentQuestionIndex={currentQuestionIndex}
            answeredQuestions={answeredQuestionIndices}
            onQuestionSelect={handleQuestionSelect}
            showResult={false}
            resultMap={new Map()}
          />
        </div>
        <div className="flex w-full items-center justify-between rounded-xl bg-white/10 px-3 py-2 text-xs font-semibold text-white lg:hidden">
          <span>Питання {currentQuestionIndex + 1} з {displayQuestions.length}</span>
          <span>Всього: {displayQuestions.length}</span>
        </div>

        {/* Question count and Add button (in edit mode) */}
        <div className="flex w-full items-center gap-3 lg:w-auto">
          <span className="hidden text-sm text-white/80 lg:inline">
            Питань: {displayQuestions.length}
          </span>
          {isEditMode && (
            <button
              type="button"
              onClick={addQuestion}
              className="flex w-full items-center justify-center gap-2 rounded-full bg-white/10 border border-white/20 px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1557c0] hover:border-[#1557c0] lg:w-auto"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12h14" />
              </svg>
              Додати питання
            </button>
          )}
        </div>
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {/* Left column - Question Card */}
        <div className="flex flex-col gap-6">
          {/* Question card */}
          <div className="rounded-2xl bg-white p-6 shadow-sm">
            {/* Question header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#1E73F7] text-base font-bold text-white">
                  {currentQuestion.number}
                </span>
                <span className={`rounded-full px-3 py-1 text-xs font-medium ${difficultyInfo.color}`}>
                  {difficultyInfo.label}
                </span>
              </div>

              {/* Edit mode actions for current question */}
              {isEditMode && (
                <div className="flex items-center gap-2">
                  {/* Move up */}
                  <button
                    type="button"
                    onClick={() => moveQuestion(currentQuestion.id, "up")}
                    disabled={currentQuestionIndex === 0}
                    className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Перемістити вгору"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 15l-6-6-6 6" />
                    </svg>
                  </button>
                  {/* Move down */}
                  <button
                    type="button"
                    onClick={() => moveQuestion(currentQuestion.id, "down")}
                    disabled={currentQuestionIndex === displayQuestions.length - 1}
                    className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Перемістити вниз"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M6 9l6 6 6-6" />
                    </svg>
                  </button>
                  {/* Delete */}
                  <button
                    type="button"
                    onClick={() => deleteQuestion(currentQuestion.id)}
                    disabled={displayQuestions.length <= 1}
                    className="rounded-lg p-2 text-red-500 hover:bg-red-50 hover:text-red-700 disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Видалити питання"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 6h18" />
                      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                    </svg>
                  </button>
                </div>
              )}
            </div>

            {/* Question text */}
            {isEditMode ? (
              <textarea
                value={currentQuestion.text}
                onChange={handleTextChange}
                placeholder="Введіть текст питання..."
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7] resize-none mb-4"
                rows={3}
              />
            ) : (
              <p className="text-lg text-slate-900 mb-6">{currentQuestion.text}</p>
            )}

            {/* Type and Difficulty selectors (edit mode only) */}
            {isEditMode && (
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Тип питання
                  </label>
                  <select
                    value={currentQuestion.type}
                    onChange={handleTypeChange}
                    className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-slate-900 focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7] bg-white"
                  >
                    {TYPE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Складність
                  </label>
                  <select
                    value={currentQuestion.difficulty}
                    onChange={handleDifficultyChange}
                    className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-slate-900 focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7] bg-white"
                  >
                    {DIFFICULTY_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* Options */}
            {!isOpenQuestion && (
              <div className="space-y-3">
                {isEditMode && (
                  <label className="block text-sm font-medium text-slate-700">
                    Варіанти відповідей
                    <span className="ml-2 text-xs text-slate-500">
                      ({currentQuestion.type === "single_choice" ? "оберіть правильну" : "оберіть правильні"})
                    </span>
                  </label>
                )}
                {currentQuestion.options.map((option, index) => {
                  const isCorrect = currentQuestion.correctOptionIds.includes(option.id);
                  const optionLetter = String.fromCharCode(65 + index);

                  if (isEditMode) {
                    // Editable option
                    return (
                      <div key={option.id} className="flex items-center gap-3">
                        {/* Correct answer toggle */}
                        <button
                          type="button"
                          onClick={() => handleCorrectToggle(option.id)}
                          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
                            isCorrect
                              ? "border-green-500 bg-green-500 text-white"
                              : "border-slate-300 bg-white hover:border-slate-400"
                          }`}
                          title={isCorrect ? "Правильна відповідь" : "Позначити як правильну"}
                        >
                          {isCorrect && (
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                              <path d="M20 6L9 17l-5-5" />
                            </svg>
                          )}
                        </button>

                        {/* Option letter */}
                        <span className="text-sm font-medium text-slate-500 w-6">
                          {optionLetter}.
                        </span>

                        {/* Option text input */}
                        <input
                          type="text"
                          value={option.text}
                          onChange={(e) => handleOptionTextChange(option.id, e.target.value)}
                          placeholder={`Варіант ${optionLetter}...`}
                          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7]"
                        />

                        {/* Remove option button */}
                        {currentQuestion.options.length > 2 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveOption(option.id)}
                            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-red-500"
                            title="Видалити варіант"
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M18 6L6 18M6 6l12 12" />
                            </svg>
                          </button>
                        )}
                      </div>
                    );
                  }

                  // Read-only option
                  return (
                    <div
                      key={option.id}
                      className={`flex items-center gap-3 rounded-xl border-2 px-4 py-3 ${
                        isCorrect
                          ? "border-green-500 bg-green-50"
                          : "border-slate-200 bg-white"
                      }`}
                    >
                      <span
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
                          isCorrect
                            ? "bg-green-500 text-white"
                            : "bg-slate-200 text-slate-600"
                        }`}
                      >
                        {optionLetter}
                      </span>
                      <span className="text-slate-900">{option.text}</span>
                      {isCorrect && (
                        <svg className="ml-auto h-5 w-5 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M20 6L9 17l-5-5" />
                        </svg>
                      )}
                    </div>
                  );
                })}

                {/* Add option button (edit mode only) */}
                {isEditMode && currentQuestion.options.length < 6 && (
                  <button
                    type="button"
                    onClick={handleAddOption}
                    className="flex items-center gap-2 text-sm font-medium text-[#1E73F7] hover:text-[#1557c0] mt-2"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 5v14M5 12h14" />
                    </svg>
                    Додати варіант
                  </button>
                )}
              </div>
            )}

            {/* Open question indicator */}
            {isOpenQuestion && !isEditMode && (
              <div className="rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center text-slate-500">
                Відкрите питання — учень вводить відповідь самостійно
              </div>
            )}
          </div>

          {/* Navigation buttons */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => handleQuestionSelect(currentQuestionIndex - 1)}
              disabled={currentQuestionIndex === 0}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                currentQuestionIndex === 0
                  ? "cursor-not-allowed bg-white/60 text-slate-300"
                  : "cursor-pointer bg-white text-[#1E73F7] hover:-translate-y-0.5 hover:shadow-lg"
              }`}
            >
              ← Попереднє
            </button>
            <button
              type="button"
              onClick={() => handleQuestionSelect(currentQuestionIndex + 1)}
              disabled={currentQuestionIndex >= displayQuestions.length - 1}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                currentQuestionIndex >= displayQuestions.length - 1
                  ? "cursor-not-allowed bg-white/60 text-slate-300"
                  : "cursor-pointer bg-white text-[#1E73F7] hover:-translate-y-0.5 hover:shadow-lg"
              }`}
            >
              Наступне →
            </button>
          </div>
        </div>

        {/* Right column - Explanation */}
        <div className="flex flex-col gap-4">
          {isEditMode ? (
            /* Editable explanation */
            <div className="rounded-2xl bg-white p-6 shadow-sm">
              <label className="block text-sm font-semibold text-slate-900 mb-3">
                Пояснення
                <span className="ml-2 text-xs font-normal text-slate-500">(необов'язково)</span>
              </label>
              <textarea
                value={currentQuestion.explanation || ""}
                onChange={handleExplanationChange}
                placeholder="Пояснення для учня після відповіді..."
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7] resize-none"
                rows={6}
              />
            </div>
          ) : currentQuestion.explanation ? (
            /* Read-only explanation */
            <div className="rounded-2xl bg-amber-50 border border-amber-200 p-6">
              <div className="flex items-center gap-2 mb-3">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-amber-600">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 16v-4M12 8h.01" />
                </svg>
                <span className="text-sm font-semibold text-amber-800">Пояснення</span>
              </div>
              <p className="text-sm text-amber-900 leading-relaxed whitespace-pre-wrap">
                {currentQuestion.explanation}
              </p>
            </div>
          ) : (
            /* No explanation placeholder */
            <div className="rounded-2xl border-2 border-dashed border-white/30 bg-white/10 p-6 text-center">
              <p className="text-sm text-white/70">
                Пояснення для цього питання ще не додано
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeacherTestEditor;
