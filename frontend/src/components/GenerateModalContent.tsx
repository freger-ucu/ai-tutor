interface AudienceSelectionDisplay {
  levels: ("weak" | "medium" | "strong")[];
  students: number[];
}

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
  errorText?: string;
  audienceSelection?: AudienceSelectionDisplay | null;
}

const levelLabels: Record<string, string> = {
  weak: "Низький",
  medium: "Середній",
  strong: "Високий",
};

const levelColors: Record<string, string> = {
  weak: "bg-pink-100 text-pink-700",
  medium: "bg-yellow-100 text-yellow-700",
  strong: "bg-green-100 text-green-700",
};

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
  errorText,
  audienceSelection,
}: GenerateModalContentProps) => {
  // Determine what audience is selected
  const hasLevels = audienceSelection && audienceSelection.levels.length > 0;
  const hasStudents = audienceSelection && audienceSelection.students.length > 0;

  const renderAudienceInfo = () => {
    if (!audienceSelection) {
      return (
        <span className="text-slate-500">Весь клас</span>
      );
    }

    if (hasStudents) {
      const displayCount = Math.min(audienceSelection.students.length, 5);
      const remaining = audienceSelection.students.length - displayCount;
      return (
        <div className="flex items-center -space-x-2">
          {audienceSelection.students.slice(0, displayCount).map((studentId, index) => (
            <div
              key={studentId}
              className="group relative"
              style={{ zIndex: displayCount - index }}
            >
              <div className="h-8 w-8 overflow-hidden rounded-full border-2 border-white transition-transform hover:scale-110 hover:z-10">
                <img
                  src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${studentId}`}
                  alt={`Учень ${studentId}`}
                  className="h-full w-full object-cover"
                />
              </div>
              {/* Tooltip on hover */}
              <div className="pointer-events-none absolute -top-9 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-slate-800 px-2.5 py-1.5 text-xs font-medium text-white opacity-0 transition-opacity group-hover:opacity-100 z-50">
                Учень {studentId}
                <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
              </div>
            </div>
          ))}
          {remaining > 0 && (
            <div
              className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white text-xs font-semibold"
              style={{
                backgroundColor: "rgba(30, 115, 247, 0.1)",
                color: "rgba(0, 0, 0, 0.5)",
              }}
            >
              +{remaining}
            </div>
          )}
        </div>
      );
    }

    if (hasLevels) {
      return (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-slate-500">Рівні:</span>
          {audienceSelection.levels.map((level) => (
            <span
              key={level}
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${levelColors[level]}`}
            >
              {levelLabels[level]}
            </span>
          ))}
        </div>
      );
    }

    return (
      <span className="text-slate-500">Весь клас</span>
    );
  };
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
      {errorText ? (
        <div className="text-sm font-semibold text-rose-600">{errorText}</div>
      ) : null}
      <div className="flex items-center justify-between gap-4">
        {/* Audience selection display */}
        {onSecondaryClick && (
          <div className="flex items-center gap-3 rounded-[20px] bg-slate-50 px-4 py-3">
            <div className="flex items-center gap-2 text-sm">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-slate-400"
              >
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
              <span className="font-medium text-slate-700">Цільова аудиторія:</span>
              {renderAudienceInfo()}
            </div>
            <button
              type="button"
              onClick={secondaryDisabled ? undefined : onSecondaryClick}
              disabled={secondaryDisabled}
              aria-disabled={secondaryDisabled}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                secondaryDisabled
                  ? "cursor-not-allowed text-slate-400"
                  : "text-[#1E73F7] hover:bg-[#E9F1FF]"
              }`}
            >
              Змінити
            </button>
          </div>
        )}
        <button
          type="button"
          onClick={onPrimaryClick}
          disabled={isLoading}
          className="flex items-center justify-center gap-2 rounded-full border border-[#1E73F7] bg-[#1E73F7] px-7 py-3 text-sm font-semibold text-white transition hover:bg-[#1557c0] hover:border-[#1557c0] disabled:cursor-not-allowed disabled:opacity-70 shrink-0"
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
