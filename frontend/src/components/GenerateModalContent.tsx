interface GenerateModalContentProps {
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  primaryLabel: string;
  isLoading?: boolean;
  onPrimaryClick: () => void;
  onSecondaryClick?: () => void;
  secondaryLabel?: string;
  secondaryDisabled?: boolean;
}

const GenerateModalContent = ({
  placeholder,
  value,
  onChange,
  primaryLabel,
  isLoading = false,
  onPrimaryClick,
  onSecondaryClick,
  secondaryLabel = "Змінити цільову аудиторію",
  secondaryDisabled = false,
}: GenerateModalContentProps) => {
  return (
    <div className="flex flex-col gap-8">
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onPrimaryClick();
            }
        }}
        placeholder={placeholder}
        rows={4}
        className="w-full resize-none rounded-[28px] bg-[#E9F1FF] px-8 py-6 text-lg font-medium text-slate-700 placeholder-slate-500 outline-none transition focus:bg-white focus:ring-2 focus:ring-[#BFD6FF]"
      />
      <div className="flex flex-wrap items-center justify-between gap-3">
        {onSecondaryClick && (
          <button
            type="button"
            onClick={secondaryDisabled ? undefined : onSecondaryClick}
            disabled={secondaryDisabled}
            aria-disabled={secondaryDisabled}
            className={`flex items-center justify-center gap-2 rounded-full border-2 px-6 py-2.5 text-sm font-semibold transition ${
              secondaryDisabled
                ? "cursor-not-allowed border-slate-300 bg-slate-100 text-slate-400"
                : "border-[#1E73F7] bg-white text-[#1E73F7] hover:bg-[#E9F1FF]"
            }`}
          >
            {secondaryLabel}
          </button>
        )}
        <button
          type="button"
          onClick={onPrimaryClick}
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-full bg-[#1E73F7] px-7 py-3 text-sm font-semibold text-white shadow transition hover:-translate-y-0.5 hover:bg-[#1A63D6] hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-70"
        >
          {primaryLabel}
          {isLoading && (
            <span className="flex items-center gap-1">
              <span
                className="inline-block h-2 w-2 animate-bounce rounded-full bg-white"
                style={{ animationDelay: "0ms" }}
              />
              <span
                className="inline-block h-2 w-2 animate-bounce rounded-full bg-white"
                style={{ animationDelay: "150ms" }}
              />
              <span
                className="inline-block h-2 w-2 animate-bounce rounded-full bg-white"
                style={{ animationDelay: "300ms" }}
              />
            </span>
          )}
        </button>
      </div>
    </div>
  );
};

export default GenerateModalContent;
