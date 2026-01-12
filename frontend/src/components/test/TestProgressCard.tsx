interface TestProgressCardProps {
  correctAnswers: number;
  totalQuestions: number;
  label?: string;
}

const TestProgressCard = ({
  correctAnswers,
  totalQuestions,
  label = "правильних відповідей",
}: TestProgressCardProps) => {
  const percentage = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0;

  return (
    <div className="flex items-center gap-4 rounded-2xl bg-gradient-to-br from-[#7DD3A0] to-[#4ADE80] px-6 py-4 text-white">
      <div className="relative flex h-16 w-16 items-center justify-center">
        {/* Background circle */}
        <svg className="absolute h-full w-full -rotate-90" viewBox="0 0 36 36">
          <circle
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke="rgba(255,255,255,0.3)"
            strokeWidth="3"
          />
          <circle
            cx="18"
            cy="18"
            r="15.5"
            fill="none"
            stroke="white"
            strokeWidth="3"
            strokeDasharray={`${percentage} 100`}
            strokeLinecap="round"
          />
        </svg>
        <span className="text-lg font-bold">
          {correctAnswers}/{totalQuestions}
        </span>
      </div>
      <div className="text-sm font-medium leading-tight whitespace-pre-wrap">
        {label}
      </div>
    </div>
  );
};

export default TestProgressCard;
