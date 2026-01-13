import { useMemo } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getMaterials } from "../data/materialsStorage";
import { getTestById, mockTestData } from "../data/mockTests";
import { students } from "../data/students";
import { TestContainer } from "../components/test";
import { withGeneratedQuestions } from "../data/testMapper";
import { markStudentTestCompleted } from "../data/studentProgress";

const subjects = [
  { id: "algebra", label: "Алгебра", icon: <span className="text-xl">√x</span> },
  {
    id: "history",
    label: "Історія України",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M5 16L3 5L8.5 10L12 4L15.5 10L21 5L19 16H5M19 19C19 19.6 18.6 20 18 20H6C5.4 20 5 19.6 5 19V18H19V19Z" />
      </svg>
    ),
  },
  {
    id: "ukr-lang",
    label: "Українська мова",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 2H4C2.9 2 2 2.9 2 4V16C2 17.1 2.9 18 4 18H8V21C8 21.6 8.4 22 9 22H15C15.6 22 16 21.6 16 21V18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2M6 6H8V8H6V6M6 10H8V12H6V10M16 14H12V10H16V14M12 6H18V8H12V6M18 10V12H16V10H18Z" />
      </svg>
    ),
  },
];

const StudentTest = () => {
  const { studentId, testId } = useParams();
  const navigate = useNavigate();

  const student = useMemo(
    () => students.find((s) => s.id === studentId),
    [studentId]
  );

  const storedTest = useMemo(
    () => getMaterials({ type: "test" }).find((item) => item.id === testId),
    [testId]
  );

  const testData = useMemo(() => {
    if (!testId) return undefined;
    
    // 1. Try to find in dynamic materials first (created by teacher)
    // We fetch all tests to find the matching ID
    const foundMaterial = storedTest;

    if (foundMaterial) {
        const hasQuestions = Array.isArray(foundMaterial.questions);
        const withGenerated = hasQuestions
          ? withGeneratedQuestions(mockTestData, foundMaterial.questions)
          : mockTestData;
        return {
            ...withGenerated,
            id: foundMaterial.id,
            title: foundMaterial.title,
            topicName: foundMaterial.topicName ?? mockTestData.topicName,
            className: foundMaterial.className ?? mockTestData.className,
            subject: "Тест",
        };
    }

    // 2. Fallback to hardcoded/legacy mock lookup
    return getTestById(testId);
  }, [testId, storedTest]);

  const classNumberMatch = testData?.className?.match(/(\d+)/);
  const classNumber = classNumberMatch ? Number(classNumberMatch[1]) : null;
  const subjectSlugMap: Record<string, string> = {
    Алгебра: "algebra",
    Геометрія: "geometry",
    "Українська мова": "ukr-lang",
    "Історія України": "history",
  };
  const courseId =
    storedTest?.courseId ??
    (testData?.subject && classNumber
      ? `${subjectSlugMap[testData.subject] ?? testData.subject.toLowerCase().replace(/\s+/g, "-")}-${classNumber}`
      : "");
  const encodedTopic = testData?.topicName
    ? encodeURIComponent(testData.topicName)
    : "";
  const backToTopicHref =
    courseId && encodedTopic
      ? `/student/${studentId}/topic/${courseId}/${encodedTopic}`
      : `/student/${studentId}`;
  const subjectSlug =
    courseId.split("-").slice(0, -1).join("-") || courseId;
  const sidebarClassName = student?.className ?? testData?.className ?? "";
  const sidebarTopicName = testData?.topicName ?? "";
  const sidebarMaterials = useMemo(() => {
    if (!sidebarClassName || !sidebarTopicName) {
      return [];
    }
    const filters: {
      courseId?: string;
      className?: string;
      topicName?: string;
    } = {
      className: sidebarClassName,
      topicName: sidebarTopicName,
    };
    if (courseId) {
      filters.courseId = courseId;
    }
    return getMaterials(filters);
  }, [courseId, sidebarClassName, sidebarTopicName]);
  const sidebarNotes = sidebarMaterials.filter((item) => item.type === "note");
  const sidebarTests = sidebarMaterials.filter((item) => item.type === "test");

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
        <aside className="fixed left-0 top-0 h-screen w-72 bg-white px-6 py-8 flex flex-col z-10">
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
          <div className="mt-8 space-y-2">
            {subjects.map((subject) => {
              const isActive = subjectSlug === subject.id;
              return (
                <button
                  key={subject.id}
                  type="button"
                  onClick={() => navigate(`/student/${studentId}`)}
                  className={`flex w-full items-center gap-4 rounded-xl px-4 py-3 text-sm font-semibold transition-all ${
                    isActive
                      ? "bg-[#E9F1FF] text-[#1E73F7]"
                      : "text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  <div
                    className={`flex items-center justify-center ${
                      isActive ? "text-[#1E73F7]" : "text-slate-900"
                    }`}
                  >
                    {subject.icon}
                  </div>
                  {subject.label}
                </button>
              );
            })}
          </div>

          <div className="mt-6">
            <Link
              to={backToTopicHref}
              className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              <span className="inline-block h-5 w-5 rounded-md bg-slate-200" />
              Назад до теми
            </Link>
          </div>

          <div className="mt-4 border-t border-slate-200 pt-6 space-y-4 text-sm">
            {sidebarNotes.map((item) => (
              <Link
                key={item.id}
                to={`/student/${studentId}/note/${courseId}/${encodedTopic}/${item.id}`}
                className="flex items-center gap-3 rounded-xl px-4 py-3 font-semibold text-slate-800 hover:bg-slate-50"
              >
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#1E73F7]/15 text-[#1E73F7]">
                  <svg width="14" height="16" viewBox="0 0 16 20" fill="currentColor">
                    <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM14 18H2V2H9V7H14V18Z" opacity="0.5"/>
                    <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM9 7V2L14 7H9Z"/>
                  </svg>
                </span>
                {item.title}
              </Link>
            ))}
            {sidebarTests.map((item) => (
              <Link
                key={item.id}
                to={`/student/${studentId}/test/${item.id}`}
                className="flex items-center gap-3 rounded-xl px-4 py-3 text-slate-700 hover:bg-slate-50"
              >
                <img src="/src/assets/Group.svg" alt="" className="h-4 w-4" />
                Тест. {item.title}
              </Link>
            ))}
          </div>
        </aside>
        <main className="ml-72 flex-1 px-10 py-10 w-full">
          <div className="mt-6">
            <TestContainer
              testData={testData}
              showStatistics={false}
              viewMode="student"
              onFinish={(result) => {
                if (studentId && testId) {
                  markStudentTestCompleted({
                    studentId,
                    testId,
                    correctAnswers: result.correctAnswers,
                    totalQuestions: result.totalQuestions,
                  });
                }
              }}
            />
          </div>
        </main>
      </div>
    </div>
  );
};

export default StudentTest;
