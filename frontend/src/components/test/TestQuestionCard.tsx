import type { TestQuestion, DifficultyLevel } from "../../types/testTypes";
import TestOption from "./TestOption";

interface TestQuestionCardProps {
  question: TestQuestion;
  selectedOptionIds: string[];
  openAnswer?: string;
  onOptionSelect: (optionId: string) => void;
  onOpenAnswerChange: (value: string) => void;
  showResult?: boolean;
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
}: TestQuestionCardProps) => {
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
    if (!showResult) {
      return "neutral";
    }
    const isCorrectOption = question.correctOptionIds.includes(optionId);
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

  return (
    <div className="rounded-[22px] bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Питання {question.number}
        </h2>
        <span
          className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${difficultyColors[question.difficulty]}`}
        >
          {difficultyLabels[question.difficulty]}
        </span>
      </div>
      <p className="mt-4 text-sm text-slate-700">{question.text}</p>
      {question.type === "open" ? (
        <div className="mt-6">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Відповідь
          </label>
          <textarea
            value={openAnswer}
            onChange={(event) => onOpenAnswerChange(event.target.value)}
            disabled={showResult}
            placeholder="Введіть відповідь"
            className={`mt-3 w-full rounded-xl border-2 px-4 py-3 text-sm text-slate-800 shadow-sm outline-none transition ${
              showResult
                ? "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-500"
                : "border-slate-200 focus:border-[#1E73F7]"
            }`}
            rows={4}
          />
        </div>
      ) : (
        <>
          <p className="mt-4 text-xs text-slate-400">
            {question.type === "multiple_choice"
              ? "Оберіть одну або кілька відповідей"
              : "Оберіть одну відповідь"}
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
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
        </>
      )}
    </div>
  );
};

export default TestQuestionCard;
