interface TestExplanationProps {
  explanation: string;
}

const TestExplanation = ({ explanation }: TestExplanationProps) => {
  return (
    <div className="rounded-2xl border-2 border-[#F5B041] bg-[#FEF9E7] p-6 shadow-sm">
      <h3 className="text-lg font-bold text-slate-900 mb-4">Пояснення</h3>
      <div className="whitespace-pre-line text-base leading-relaxed text-slate-700">
        {explanation}
      </div>
    </div>
  );
};

export default TestExplanation;
