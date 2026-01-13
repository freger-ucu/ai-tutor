import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { teachers } from "../data/teachers";
import { getTestById, getTestStatistics, mockTestData } from "../data/mockTests";
import TeacherSidebar from "../components/TeacherSidebar";
import { TestContainer } from "../components/test";
import SelectStudentsModal from "../components/SelectStudentsModal";
import { getMaterials } from "../data/materialsStorage";
import { withGeneratedQuestions } from "../data/testMapper";
import { classLabelToId } from "../data/classUtils";

const TeacherTest = () => {
  const { id, testId } = useParams();

  const teacher = useMemo(
    () => teachers.find((item) => item.id === id),
    [id]
  );

  const storedTest = useMemo(
    () => getMaterials({ type: "test" }).find((item) => item.id === testId),
    [testId]
  );
  const testData = useMemo(() => {
    const base = getTestById(testId ?? "");
    if (!storedTest) {
      return base;
    }
    const fallback = base ?? mockTestData;
    if (!storedTest.questions || !Array.isArray(storedTest.questions)) {
      return {
        ...fallback,
        id: storedTest.id,
        title: storedTest.title,
        topicName: storedTest.topicName ?? fallback.topicName,
        className: storedTest.className ?? fallback.className,
      };
    }
    const withGenerated = withGeneratedQuestions(fallback, storedTest.questions);
    return {
      ...withGenerated,
      id: storedTest.id,
      title: storedTest.title,
      topicName: storedTest.topicName ?? fallback.topicName,
      className: storedTest.className ?? fallback.className,
    };
  }, [testId, storedTest]);
  const statistics = useMemo(() => getTestStatistics(testId ?? ""), [testId]);

  const [isAudienceModalOpen, setIsAudienceModalOpen] = useState(false);
  const classNumberMatch = testData?.className?.match(/(\d+)/);
  const classNumber = classNumberMatch ? Number(classNumberMatch[1]) : null;
  const classId = testData?.className
    ? classLabelToId(testData.className)
    : null;
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
    courseId && classId && encodedTopic
      ? `/teacher/${id}/topic/${courseId}/${classId}/${encodedTopic}`
      : id
      ? `/teacher/${id}`
      : "/";
  const backToClassHref = id ? `/teacher/${id}` : "/";
  const sidebarMaterials = useMemo(() => {
    if (!id || !testData?.className || !testData?.topicName) {
      return [];
    }
    const filters: {
      teacherId?: string;
      courseId?: string;
      className?: string;
      topicName?: string;
    } = {
      teacherId: id,
      className: testData.className,
      topicName: testData.topicName,
    };
    if (courseId) {
      filters.courseId = courseId;
    }
    return getMaterials(filters);
  }, [id, courseId, testData?.className, testData?.topicName]);
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
    <div className="h-screen bg-[#1E73F7] text-slate-900 overflow-hidden flex">
      <TeacherSidebar
        teacherName={
          teacher ? `${teacher.firstName} ${teacher.lastName}` : "Вчитель"
        }
        activeItem="materials"
        afterPrimaryNav={
          <div className="space-y-2">
            <Link
              to={backToClassHref}
              className="flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-800 hover:bg-slate-100"
            >
              <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-slate-200" />
              <span>Назад до класу</span>
            </Link>
            <Link
              to={backToTopicHref}
              className="flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-800 hover:bg-slate-100"
            >
              <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-slate-200" />
              <span>Назад до теми</span>
            </Link>
          </div>
        }
      >
        <div className="space-y-4">
          {sidebarNotes.map((item) => (
            <Link
              key={item.id}
              to={`/teacher/${id}/note/${courseId}/${classId}/${encodedTopic}/${item.id}`}
              className="flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 text-slate-700 hover:bg-slate-100"
            >
              <span className="mt-0.5 inline-block h-5 w-5 rounded-md bg-slate-200" />
              <span>{item.title}</span>
            </Link>
          ))}
          {sidebarTests.map((item) => (
            <Link
              key={item.id}
              to={`/teacher/${id}/test/${item.id}`}
              className={`flex w-full items-start justify-start gap-3 rounded-2xl px-4 py-3 ${
                item.id === testId
                  ? "text-[#1E73F7]"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              <span
                className={`mt-0.5 inline-block h-5 w-5 rounded-md ${
                  item.id === testId ? "bg-[#1E73F7]/20" : "bg-slate-200"
                }`}
              />
              <span>{item.title}</span>
            </Link>
          ))}
        </div>
      </TeacherSidebar>

      <main className="flex-1 px-10 py-8 flex flex-col h-full">
          <h1 className="mt-2 text-2xl font-bold text-white shrink-0">
             {testData.title}
          </h1>

          {/* Main Card */}
          <div className="mt-4 flex-1 rounded-[32px] bg-white p-8 shadow-xl overflow-y-auto min-h-0">
             <TestContainer
               testData={testData}
               statistics={statistics}
               showStatistics={true}
               viewMode="teacher"
             />
          </div>

          {/* Footer Actions */}
          <div className="mt-6 flex items-center justify-between shrink-0">
             <button className="flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-bold text-[#1E73F7] shadow transition hover:-translate-y-0.5 hover:shadow-lg cursor-pointer">
                <svg width="16" height="20" viewBox="0 0 16 20" fill="currentColor">
                    <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM14 18H2V2H9V7H14V18Z" opacity="0.5"/>
                    <path d="M10 0H2C0.9 0 0 0.9 0 2V18C0 19.1 0.9 20 2 20H14C15.1 20 16 19.1 16 18V6L10 0ZM9 7V2L14 7H9Z"/>
                </svg>
                Завантажити в PDF
             </button>

             <button 
                onClick={() => setIsAudienceModalOpen(true)}
                className="flex items-center gap-2 rounded-full border-2 border-white bg-transparent px-6 py-3 text-sm font-bold text-white transition hover:bg-white/10 cursor-pointer"
             >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 12C21 16.9706 16.9706 21 12 21C9.69637 21 7.59565 20.1344 6.00003 18.7077M3 12C3 7.02944 7.02944 3 12 3C14.3036 3 16.4044 3.86558 18 5.29231" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M21 3V8H16" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M3 21V16H8" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                 </svg>
                 <span>Змінити цільову аудиторію</span>
             </button>
          </div>
      </main>

      <SelectStudentsModal
        isOpen={isAudienceModalOpen}
        onClose={() => setIsAudienceModalOpen(false)}
        classNameFilter={testData.className}
        onSave={(selection) => {
            console.log("Saved selection", selection);
            setIsAudienceModalOpen(false);
        }}
      />
    </div>
  );
};

export default TeacherTest;
