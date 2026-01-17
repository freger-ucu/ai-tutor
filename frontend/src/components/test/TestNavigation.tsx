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
    <div className="flex gap-1.5 items-center overflow-x-auto overflow-y-visible flex-nowrap p-1">
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

        // For unanswered questions when not showing results - show with subtle dashed border
        const unansweredClass = !isAnswered && !showResult
          ? "border border-dashed border-white/50 bg-transparent text-white/80"
          : "";

        return (
          <button
            key={index}
            type="button"
            onClick={() => onQuestionSelect(index)}
            className={`flex w-8 h-8 shrink-0 cursor-pointer items-center justify-center rounded-lg text-xs font-semibold transition-all duration-200 ${
              resultClass
                ? `${resultClass} ${isCurrent ? "scale-110 ring-2 ring-white shadow-lg z-10" : ""}`
                : isCurrent
                  ? "bg-white text-[#1E73F7] scale-110 ring-2 ring-white shadow-lg z-10"
                  : isAnswered
                    ? "bg-white/90 text-[#1E73F7] hover:bg-white hover:scale-105"
                    : unansweredClass || "bg-white/40 text-white hover:bg-white/60 hover:scale-105"
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
