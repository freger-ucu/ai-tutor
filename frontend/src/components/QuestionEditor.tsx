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
import type { TestQuestion } from "../types/testTypes";

interface QuestionEditorProps {
  /** The question data to edit */
  question: TestQuestion;
  /** Callback when question data changes */
  onChange: (updates: Partial<TestQuestion>) => void;
  /** Callback when question should be deleted */
  onDelete: () => void;
}

const QuestionEditor = ({
  question,
  onChange,
  onDelete,
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
    <div className="rounded-[22px] bg-white p-6 shadow-lg">
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
                </div>
              );
            })}
          </div>
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
