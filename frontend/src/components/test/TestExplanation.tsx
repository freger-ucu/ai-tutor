interface TestExplanationProps {
  explanation: string;
}

const TestExplanation = ({ explanation }: TestExplanationProps) => {
  return (
    <div className="rounded-2xl border-2 border-[#F5DEB3] bg-[#FFF8E7] p-6">
      <h3 className="text-lg font-semibold text-slate-900">Пояснення</h3>
      <div className="mt-3 whitespace-pre-line text-sm leading-relaxed text-slate-700">
        {explanation}
      </div>
    </div>
  );
};

export default TestExplanation;
