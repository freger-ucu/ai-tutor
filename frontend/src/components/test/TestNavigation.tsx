interface TestNavigationProps {
  totalQuestions: number;
  currentQuestionIndex: number;
  answeredQuestions: Set<number>;
  onQuestionSelect: (index: number) => void;
  showResult?: boolean;
  resultMap?: Map<number, "correct" | "incorrect" | "partial">;
}

const TestNavigation = ({
  totalQuestions,
  currentQuestionIndex,
  answeredQuestions,
  onQuestionSelect,
  showResult = false,
  resultMap,
}: TestNavigationProps) => {
  return (
    <div className="flex flex-wrap gap-2">
      {Array.from({ length: totalQuestions }, (_, index) => {
        const isCurrent = index === currentQuestionIndex;
        const isAnswered = answeredQuestions.has(index);
        const result = showResult ? resultMap?.get(index) : undefined;
        const resultClass =
          result === "correct"
            ? "bg-[#80E6B6] text-slate-900"
            : result === "incorrect"
            ? "bg-[#FFBFE1] text-slate-900"
            : result === "partial"
            ? "bg-[#FFD9B3] text-slate-900"
            : "";

        return (
          <button
            key={index}
            type="button"
            onClick={() => onQuestionSelect(index)}
            className={`flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg text-sm font-semibold transition-all ${
              resultClass
                ? resultClass
                : isCurrent
                  ? "bg-[#1E73F7] text-white ring-2 ring-white"
                  : isAnswered
                    ? "bg-white/90 text-[#1E73F7]"
                    : "border border-white/50 bg-white/10 text-white hover:bg-white/20"
            }`}
          >
            {index + 1}
          </button>
        );
      })}
    </div>
  );
};

export default TestNavigation;
