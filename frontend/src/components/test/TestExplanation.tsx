import MarkdownContent from "../MarkdownContent";

interface TestExplanationProps {
  explanation: string;
}

const TestExplanation = ({ explanation }: TestExplanationProps) => {
  return (
    <div className="rounded-xl border-2 border-[#F5B041] bg-[#FEF9E7] p-3 shadow-sm">
      <h3 className="text-sm font-bold text-slate-900 mb-2">Пояснення</h3>
      <MarkdownContent content={explanation} className="text-xs text-slate-700" />
    </div>
  );
};

export default TestExplanation;
