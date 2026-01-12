interface TestOptionProps {
  id: string;
  text: string;
  isSelected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

const TestOption = ({
  text,
  isSelected,
  onClick,
  disabled = false,
}: TestOptionProps) => {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex w-full cursor-pointer items-center gap-4 rounded-xl border-2 px-5 py-4 text-left text-sm font-medium transition-all ${
        isSelected
          ? "border-[#1E73F7] bg-[#E9F1FF] text-slate-900"
          : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
      } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
    >
      <span
        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition-all ${
          isSelected
            ? "border-[#1E73F7] bg-[#1E73F7]"
            : "border-slate-300 bg-white"
        }`}
      >
        {isSelected && (
          <svg
            className="h-3 w-3 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={3}
              d="M5 13l4 4L19 7"
            />
          </svg>
        )}
      </span>
      <span>{text}</span>
    </button>
  );
};

export default TestOption;
