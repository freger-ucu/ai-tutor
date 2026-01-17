import type { TestQuestion, DifficultyLevel } from "../../types/testTypes";
import TestOption from "./TestOption";
import TestExplanation from "./TestExplanation";
import MarkdownContent from "../MarkdownContent";

interface TestQuestionCardProps {
  question: TestQuestion;
  selectedOptionIds: string[];
  openAnswer?: string;
  onOptionSelect: (optionId: string) => void;
  onOpenAnswerChange: (value: string) => void;
  showResult?: boolean;
  /** View mode - teacher sees correct answers highlighted, student doesn't see difficulty */
  viewMode?: "teacher" | "student";
  /** Show explanation below the question */
  showExplanation?: boolean;
}

const difficultyLabels: Record<DifficultyLevel, string> = {
  easy: "Легкий рівень",
  medium: "Середній рівень",
  hard: "Складний рівень",
};

const difficultyColors: Record<DifficultyLevel, string> = {
  easy: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  hard: "bg-red-100 text-red-700",
};

const TestQuestionCard = ({
  question,
  selectedOptionIds,
  openAnswer = "",
  onOptionSelect,
  onOpenAnswerChange,
  showResult = false,
  viewMode = "student",
  showExplanation = false,
}: TestQuestionCardProps) => {
  const isTeacher = viewMode === "teacher";
  const selectionStatus = (() => {
    if (!showResult || question.type === "open") {
      return "neutral";
    }
    const selected = selectedOptionIds;
    const correct = question.correctOptionIds;
    if (!selected.length) {
      return "neutral";
    }
    const isExact =
      selected.length === correct.length &&
      selected.every((id) => correct.includes(id));
    if (isExact) {
      return "correct";
    }
    const hasCorrectSelection = selected.some((id) => correct.includes(id));
    return hasCorrectSelection ? "partial" : "incorrect";
  })();

  const resultStateForOption = (optionId: string) => {
    const isCorrectOption = question.correctOptionIds.includes(optionId);

    // For teacher view, always highlight correct answers in green
    if (isTeacher) {
      return isCorrectOption ? "correct" : "neutral";
    }

    if (!showResult) {
      return "neutral";
    }
    const isSelected = selectedOptionIds.includes(optionId);
    if (selectionStatus === "correct") {
      return isCorrectOption ? "correct" : "neutral";
    }
    if (selectionStatus === "incorrect") {
      if (isSelected && !isCorrectOption) {
        return "incorrect";
      }
      return isCorrectOption ? "correct" : "neutral";
    }
    if (selectionStatus === "partial") {
      if (isSelected && !isCorrectOption) {
        return "incorrect";
      }
      if (isCorrectOption) {
        return "partial";
      }
      return "neutral";
    }
    return "neutral";
  };

  // Show difficulty badge when viewing results (teacher always, student after finish)
  const showDifficultyBadge = isTeacher || showResult;

  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm">
      {/* Question header */}
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-slate-900">
          Питання {question.number}
        </h2>
        {/* Difficulty badge - shown for teacher and student after finishing */}
        {showDifficultyBadge && (
          <span
            className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${difficultyColors[question.difficulty]}`}
          >
            {difficultyLabels[question.difficulty]}
          </span>
        )}
      </div>
      <div className="mt-2">
        <MarkdownContent content={question.text} className="text-sm text-slate-700" />
      </div>

      {/* Answer options - inside white block */}
      {question.type === "open" ? (
        <div className="mt-3">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Відповідь
          </label>
          <textarea
            value={openAnswer}
            onChange={(event) => onOpenAnswerChange(event.target.value)}
            disabled={showResult}
            placeholder="Введіть відповідь"
            className={`mt-1.5 w-full rounded-lg border-2 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition ${
              showResult
                ? "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-500"
                : "border-slate-200 bg-white focus:border-[#1E73F7]"
            }`}
            rows={2}
          />
        </div>
      ) : (
        <div className="mt-3">
          <p className="text-xs text-slate-500 mb-2">
            {question.type === "multiple_choice"
              ? "Оберіть одну або кілька відповідей"
              : "Оберіть одну відповідь"}
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            {question.options.map((option) => (
              <TestOption
                key={option.id}
                id={option.id}
                text={option.text}
                isSelected={selectedOptionIds.includes(option.id)}
                onClick={() => onOptionSelect(option.id)}
                disabled={showResult}
                resultState={resultStateForOption(option.id)}
                selectionStyle={
                  question.type === "single_choice" ? "single" : "multiple"
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* Explanation - shown below the question */}
      {showExplanation && question.explanation && (
        <div className="mt-3">
          <TestExplanation explanation={question.explanation} />
        </div>
      )}
    </div>
  );
};

export default TestQuestionCard;
