import MarkdownContent from "../MarkdownContent";

interface TestOptionProps {
  id: string;
  text: string;
  isSelected: boolean;
  onClick: () => void;
  disabled?: boolean;
  resultState?: "correct" | "incorrect" | "partial" | "neutral";
  selectionStyle?: "single" | "multiple";
}

const TestOption = ({
  text,
  isSelected,
  onClick,
  disabled = false,
  resultState = "neutral",
  selectionStyle = "multiple",
}: TestOptionProps) => {
  const resultStyles: Record<
    "correct" | "incorrect" | "partial",
    { container: string; indicator: string; checkColor: string }
  > = {
    correct: {
      container: "border-[#A8E6CF] bg-[#E8F8EF] text-slate-900",
      indicator: "border-slate-700 bg-slate-700",
      checkColor: "text-white",
    },
    incorrect: {
      container: "border-[#FFD0E5] bg-[#FFF5F9] text-slate-900",
      indicator: "border-slate-700 bg-slate-700",
      checkColor: "text-white",
    },
    partial: {
      container: "border-[#FFE4C4] bg-[#FFF8F0] text-slate-900",
      indicator: "border-slate-700 bg-slate-700",
      checkColor: "text-white",
    },
  };
  const resolvedResult =
    resultState !== "neutral" ? resultStyles[resultState] : null;

  const isSingle = selectionStyle === "single";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex w-full cursor-pointer items-center gap-4 rounded-2xl border px-6 py-5 text-left text-base font-medium transition-all ${
        resolvedResult
          ? resolvedResult.container
          : isSelected
            ? "border-[#1E73F7] bg-[#E9F1FF] text-slate-900"
            : "border-slate-200 bg-[#F8FAFC] text-slate-700 hover:border-slate-300 hover:bg-white"
      } ${disabled ? "cursor-not-allowed" : ""} ${
        disabled && !resolvedResult ? "opacity-70" : ""
      }`}
    >
      <span
        className={`flex h-5 w-5 shrink-0 items-center justify-center border transition-all ${
          isSingle ? "rounded-full" : "rounded-md"
        } ${
          resolvedResult && isSelected
            ? resolvedResult.indicator
            : isSelected
              ? "border-slate-700 bg-slate-700"
              : "border-slate-400 bg-white"
        }`}
      >
        {isSelected &&
          (isSingle ? (
            <span className="h-2.5 w-2.5 rounded-full bg-white" />
          ) : (
            <svg
              className={`h-3 w-3 ${resolvedResult ? resolvedResult.checkColor : "text-white"}`}
              fill="none"
              stroke="currentColor"
              strokeWidth={2.5}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 13l4 4L19 7"
              />
            </svg>
          ))}
      </span>
      <span className="leading-relaxed flex-1">
        <MarkdownContent content={text} className="[&>p]:mt-0" />
      </span>
    </button>
  );
};

export default TestOption;
