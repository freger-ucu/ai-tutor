import type { TestStatistics } from "../../types/testTypes";

interface TestStatisticsCardProps {
  statistics: TestStatistics;
}

const TestStatisticsCard = ({ statistics }: TestStatisticsCardProps) => {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <h3 className="text-lg font-semibold text-slate-900">Статистика</h3>
      <p className="mt-3 text-sm leading-relaxed text-slate-600">
        {statistics.description}
      </p>
    </div>
  );
};

export default TestStatisticsCard;
