/**
 * QuestionEditor - Component for editing a single test question
 *
 * Provides a form interface for modifying:
 * - Question text
 * - Answer options (add/remove/edit)
 * - Correct answer selection
 * - Difficulty level
 * - Question type (single/multiple choice, open)
 * - Explanation text
 *
 * @example
 * <QuestionEditor
 *   question={question}
 *   onChange={(updates) => updateQuestion(question.id, updates)}
 *   onDelete={() => deleteQuestion(question.id)}
 *   onMoveUp={() => moveQuestion(question.id, "up")}
 *   onMoveDown={() => moveQuestion(question.id, "down")}
 *   isFirst={index === 0}
 *   isLast={index === questions.length - 1}
 * />
 */

import { useCallback } from "react";
import type { TestQuestion, TestOption, DifficultyLevel, QuestionType } from "../types/testTypes";

interface QuestionEditorProps {
  /** The question data to edit */
  question: TestQuestion;
  /** Callback when question data changes */
  onChange: (updates: Partial<TestQuestion>) => void;
  /** Callback when question should be deleted */
  onDelete: () => void;
  /** Callback to move question up in order */
  onMoveUp?: () => void;
  /** Callback to move question down in order */
  onMoveDown?: () => void;
  /** Whether this is the first question (disables move up) */
  isFirst?: boolean;
  /** Whether this is the last question (disables move down) */
  isLast?: boolean;
}

// Difficulty level options with labels
const DIFFICULTY_OPTIONS: { value: DifficultyLevel; label: string }[] = [
  { value: "easy", label: "Легкий" },
  { value: "medium", label: "Середній" },
  { value: "hard", label: "Складний" },
];

// Question type options with labels
const TYPE_OPTIONS: { value: QuestionType; label: string }[] = [
  { value: "single_choice", label: "Одна відповідь" },
  { value: "multiple_choice", label: "Декілька відповідей" },
  { value: "open", label: "Відкрите питання" },
];

/**
 * Generate a unique ID for new options
 */
const generateOptionId = (): string => {
  return `opt-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
};

const QuestionEditor = ({
  question,
  onChange,
  onDelete,
  onMoveUp,
  onMoveDown,
  isFirst = false,
  isLast = false,
}: QuestionEditorProps) => {
  /**
   * Handle question text change
   */
  const handleTextChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange({ text: e.target.value });
    },
    [onChange]
  );

  /**
   * Handle difficulty level change
   */
  const handleDifficultyChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onChange({ difficulty: e.target.value as DifficultyLevel });
    },
    [onChange]
  );

  /**
   * Handle question type change
   */
  const handleTypeChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const newType = e.target.value as QuestionType;
      // When switching types, reset correct answers if needed
      if (newType === "open") {
        onChange({ type: newType, correctOptionIds: [], options: [] });
      } else if (newType === "single_choice" && question.correctOptionIds.length > 1) {
        // Keep only first correct answer for single choice
        onChange({ type: newType, correctOptionIds: question.correctOptionIds.slice(0, 1) });
      } else {
        onChange({ type: newType });
      }
    },
    [onChange, question.correctOptionIds]
  );

  /**
   * Handle option text change
   */
  const handleOptionTextChange = useCallback(
    (optionId: string, text: string) => {
      const updatedOptions = question.options.map((opt) =>
        opt.id === optionId ? { ...opt, text } : opt
      );
      onChange({ options: updatedOptions });
    },
    [onChange, question.options]
  );

  /**
   * Handle correct answer toggle
   */
  const handleCorrectToggle = useCallback(
    (optionId: string) => {
      const isCurrentlyCorrect = question.correctOptionIds.includes(optionId);

      if (question.type === "single_choice") {
        // Single choice: replace the correct answer
        onChange({ correctOptionIds: isCurrentlyCorrect ? [] : [optionId] });
      } else {
        // Multiple choice: toggle the option
        const newCorrectIds = isCurrentlyCorrect
          ? question.correctOptionIds.filter((id) => id !== optionId)
          : [...question.correctOptionIds, optionId];
        onChange({ correctOptionIds: newCorrectIds });
      }
    },
    [onChange, question.type, question.correctOptionIds]
  );

  /**
   * Add a new option
   */
  const handleAddOption = useCallback(() => {
    const newOption: TestOption = {
      id: generateOptionId(),
      text: "",
    };
    onChange({ options: [...question.options, newOption] });
  }, [onChange, question.options]);

  /**
   * Remove an option
   */
  const handleRemoveOption = useCallback(
    (optionId: string) => {
      const updatedOptions = question.options.filter((opt) => opt.id !== optionId);
      // Also remove from correct answers if present
      const updatedCorrectIds = question.correctOptionIds.filter((id) => id !== optionId);
      onChange({ options: updatedOptions, correctOptionIds: updatedCorrectIds });
    },
    [onChange, question.options, question.correctOptionIds]
  );

  /**
   * Handle explanation change
   */
  const handleExplanationChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange({ explanation: e.target.value });
    },
    [onChange]
  );

  const isOpenQuestion = question.type === "open";

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      {/* Header with question number and controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#1E73F7] text-sm font-bold text-white">
            {question.number}
          </span>
          <span className="text-lg font-semibold text-slate-900">Питання</span>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {/* Move up button */}
          {onMoveUp && (
            <button
              type="button"
              onClick={onMoveUp}
              disabled={isFirst}
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed"
              title="Перемістити вгору"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 15l-6-6-6 6" />
              </svg>
            </button>
          )}

          {/* Move down button */}
          {onMoveDown && (
            <button
              type="button"
              onClick={onMoveDown}
              disabled={isLast}
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed"
              title="Перемістити вниз"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M6 9l6 6 6-6" />
              </svg>
            </button>
          )}

          {/* Delete button */}
          <button
            type="button"
            onClick={onDelete}
            className="rounded-lg p-2 text-red-500 hover:bg-red-50 hover:text-red-700"
            title="Видалити питання"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18" />
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
            </svg>
          </button>
        </div>
      </div>

      {/* Question text */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Текст питання
        </label>
        <textarea
          value={question.text}
          onChange={handleTextChange}
          placeholder="Введіть текст питання..."
          className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7] resize-none"
          rows={3}
        />
      </div>

      {/* Type and Difficulty selectors */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Тип питання
          </label>
          <select
            value={question.type}
            onChange={handleTypeChange}
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7] bg-white"
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
            value={question.difficulty}
            onChange={handleDifficultyChange}
            className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7] bg-white"
          >
            {DIFFICULTY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Options section (for choice questions only) */}
      {!isOpenQuestion && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Варіанти відповідей
            <span className="ml-2 text-xs text-slate-500">
              ({question.type === "single_choice" ? "оберіть правильну" : "оберіть правильні"})
            </span>
          </label>

          <div className="space-y-2">
            {question.options.map((option, index) => {
              const isCorrect = question.correctOptionIds.includes(option.id);
              return (
                <div key={option.id} className="flex items-center gap-3">
                  {/* Correct answer checkbox/radio */}
                  <button
                    type="button"
                    onClick={() => handleCorrectToggle(option.id)}
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
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
                    {String.fromCharCode(65 + index)}.
                  </span>

                  {/* Option text input */}
                  <input
                    type="text"
                    value={option.text}
                    onChange={(e) => handleOptionTextChange(option.id, e.target.value)}
                    placeholder={`Варіант ${String.fromCharCode(65 + index)}...`}
                    className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7]"
                  />

                  {/* Remove option button */}
                  {question.options.length > 2 && (
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
            })}
          </div>

          {/* Add option button */}
          {question.options.length < 6 && (
            <button
              type="button"
              onClick={handleAddOption}
              className="mt-3 flex items-center gap-2 text-sm font-medium text-[#1E73F7] hover:text-[#1557c0]"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12h14" />
              </svg>
              Додати варіант
            </button>
          )}
        </div>
      )}

      {/* Explanation (optional) */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Пояснення
          <span className="ml-2 text-xs text-slate-500">(необов'язково)</span>
        </label>
        <textarea
          value={question.explanation || ""}
          onChange={handleExplanationChange}
          placeholder="Пояснення для учня після відповіді..."
          className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-[#1E73F7] focus:outline-none focus:ring-1 focus:ring-[#1E73F7] resize-none"
          rows={2}
        />
      </div>
    </div>
  );
};

export default QuestionEditor;
