interface GenerateModalContentProps {
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  primaryLabel: string;
  isLoading?: boolean;
  onPrimaryClick: () => void;
  onSecondaryClick?: () => void;
}

const GenerateModalContent = ({
  placeholder,
  value,
  onChange,
  primaryLabel,
  isLoading = false,
  onPrimaryClick,
  onSecondaryClick,
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
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onSecondaryClick}
          className="rounded-full bg-[#E9F1FF] px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-[#DDEBFF] cursor-pointer"
        >
          Змінити цільову аудиторію
        </button>
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
