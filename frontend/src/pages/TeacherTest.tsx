import { useMemo } from "react";
import { useParams } from "react-router-dom";
import { teachers } from "../data/teachers";
import { getTestById, getTestStatistics } from "../data/mockTests";
import TeacherSidebar from "../components/TeacherSidebar";
import { TestContainer } from "../components/test";

const TeacherTest = () => {
  const { id, testId } = useParams();

  const teacher = useMemo(
    () => teachers.find((item) => item.id === id),
    [id]
  );

  const testData = useMemo(() => getTestById(testId ?? ""), [testId]);
  const statistics = useMemo(() => getTestStatistics(testId ?? ""), [testId]);

  if (!testData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
        <div className="text-xl text-white">Тест не знайдено</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        <TeacherSidebar
          teacherName={
            teacher ? `${teacher.firstName} ${teacher.lastName}` : "Вчитель"
          }
          activeItem="materials"
        >
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
              <span>Конспект. Іменник</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
              <span>Додатково</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
              <span>Конспект. Іменник</span>
            </div>
            <div className="flex items-center gap-3 text-[#1E73F7]">
              <span className="inline-block h-5 w-5 rounded-md bg-[#1E73F7]/20" />
              <span>{testData.title}</span>
            </div>
          </div>
        </TeacherSidebar>
        <main className="flex-1 px-10 py-10">
          <div className="text-sm font-medium text-white/80">
            {testData.subject} / {testData.className} / {testData.topicName}
          </div>
          <div className="mt-6">
            <TestContainer
              testData={testData}
              statistics={statistics}
              showStatistics={true}
              viewMode="teacher"
            />
          </div>
        </main>
      </div>
    </div>
  );
};

export default TeacherTest;
