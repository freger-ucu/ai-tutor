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
    <div className="flex gap-2 items-center p-4 overflow-x-auto overflow-y-visible flex-nowrap">
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

        // For unanswered questions when not showing results - show with dashed border
        const unansweredClass = !isAnswered && !showResult
          ? "border-2 border-dashed border-white/60 bg-transparent text-white"
          : "";

        return (
          <button
            key={index}
            type="button"
            onClick={() => onQuestionSelect(index)}
            className={`flex w-10 h-10 shrink-0 cursor-pointer items-center justify-center rounded-xl text-sm font-semibold transition-all duration-200 ${
              resultClass
                ? `${resultClass} ${isCurrent ? "scale-110 ring-2 ring-white shadow-lg z-10" : ""}`
                : isCurrent
                  ? "bg-white text-[#1E73F7] scale-110 ring-2 ring-white shadow-lg z-10"
                  : isAnswered
                    ? "bg-white/90 text-[#1E73F7] hover:bg-white hover:scale-105"
                    : unansweredClass || "border border-slate-200 bg-white text-[#1E73F7] hover:bg-slate-50 hover:scale-105"
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
