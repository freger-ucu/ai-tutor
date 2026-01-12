import { useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { getMaterials } from "../data/materialsStorage";
import { getTestById, mockTestData } from "../data/mockTests";
import { students } from "../data/students";
import { TestContainer } from "../components/test";

const StudentTest = () => {
  const { studentId, testId } = useParams();

  const student = useMemo(
    () => students.find((s) => s.id === studentId),
    [studentId]
  );

  const testData = useMemo(() => {
    if (!testId) return undefined;
    
    // 1. Try to find in dynamic materials first (created by teacher)
    // We fetch all tests to find the matching ID
    const allTests = getMaterials({ type: "test" }); 
    const foundMaterial = allTests.find(m => m.id === testId);

    if (foundMaterial) {
        // Fallback: Use questions from the mock test but title from the real material
        return {
            ...mockTestData,
            id: foundMaterial.id,
            title: foundMaterial.title,
            // If topicName is missing in material, fallback to mock, but usually it's there
            topicName: foundMaterial.topicName ?? mockTestData.topicName,
            subject: "Тест", // Generic subject if not stored, or deduce from context
            questions: mockTestData.questions // Reuse mock questions since we don't save real ones yet
        };
    }

    // 2. Fallback to hardcoded/legacy mock lookup
    return getTestById(testId);
  }, [testId]);

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
        {/* Student Sidebar */}
        <aside className="fixed left-0 top-0 h-screen w-64 bg-white px-6 py-8 flex flex-col z-10">
          <div className="flex items-center gap-3">
             <div
                className="h-10 w-10 overflow-hidden rounded-full bg-slate-200"
                style={{
                  backgroundImage: "url('https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80')",
                  backgroundSize: "cover",
                }}
             />
            <div>
              <div className="text-base font-semibold text-slate-900">
                {student ? `${student.firstName} ${student.lastName}` : "Учень"}
              </div>
              {student && (
                <div className="text-xs text-slate-500">Клас: {student.className}</div>
              )}
            </div>
          </div>
          <div className="mt-10 space-y-3">
            <Link
              to={`/student/${studentId}`}
              className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-800 hover:bg-slate-100"
            >
              <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
              ← Назад
            </Link>
            <div className="flex w-full items-center gap-3 rounded-2xl bg-[#E9F1FF] px-4 py-3 text-sm font-semibold text-[#1E73F7]">
              <span className="inline-block h-5 w-5 rounded-md bg-[#1E73F7]/20" />
              {testData.title}
            </div>
          </div>
        </aside>
        <main className="ml-64 flex-1 px-10 py-10 w-full">
          <div className="text-sm font-medium text-white/80">
            {testData.subject} / {testData.className} / {testData.topicName}
          </div>
          <div className="mt-6">
            <TestContainer
              testData={testData}
              showStatistics={false}
              viewMode="student"
            />
          </div>
        </main>
      </div>
    </div>
  );
};

export default StudentTest;
