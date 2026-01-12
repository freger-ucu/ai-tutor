import type { TestQuestion, DifficultyLevel } from "../../types/testTypes";
import TestOption from "./TestOption";

interface TestQuestionCardProps {
  question: TestQuestion;
  selectedOptionId: string | null;
  onOptionSelect: (optionId: string) => void;
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
  selectedOptionId,
  onOptionSelect,
  showResult = false,
}: TestQuestionCardProps) => {
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
      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        {question.options.map((option) => (
          <TestOption
            key={option.id}
            id={option.id}
            text={option.text}
            isSelected={selectedOptionId === option.id}
            onClick={() => onOptionSelect(option.id)}
            disabled={showResult}
          />
        ))}
      </div>
    </div>
  );
};

export default TestQuestionCard;
