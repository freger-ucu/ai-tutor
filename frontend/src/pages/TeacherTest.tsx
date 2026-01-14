import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import { getTestById, getTestStatistics, mockTestData } from "../data/mockTests";
import TeacherSidebar from "../components/TeacherSidebar";
import { TestContainer } from "../components/test";
import SelectStudentsModal from "../components/SelectStudentsModal";
import { getMaterials } from "../data/materialsStorage";
import { withGeneratedQuestions } from "../data/testMapper";
import { classLabelToId } from "../data/classUtils";
import { getTeacherStudents } from "../api/teacher";
import { toNumericId } from "../api/idUtils";

const TeacherTest = () => {
  const { id, testId } = useParams();

  const storedTest = useMemo(
    () => getMaterials({ type: "test" }).find((item) => item.id === testId),
    [testId]
  );
  const testData = useMemo(() => {
    const fallbackBase = getTestById(testId ?? "") ?? mockTestData;
    if (!storedTest) {
      return fallbackBase;
    }
    const base = {
      ...fallbackBase,
      id: storedTest.id,
      title: storedTest.title,
      subject: storedTest.subject ?? fallbackBase.subject,
      topicName: storedTest.topicName ?? fallbackBase.topicName,
      className: storedTest.className ?? fallbackBase.className,
    };
    const withGenerated = Array.isArray(storedTest.questions)
      ? withGeneratedQuestions(base, storedTest.questions)
      : base;
    return {
      ...withGenerated,
      id: storedTest.id,
      title: storedTest.title,
      subject: storedTest.subject ?? withGenerated.subject,
      topicName: storedTest.topicName ?? withGenerated.topicName,
      className: storedTest.className ?? withGenerated.className,
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
  const subjectLabelMap: Record<string, string> = {
    algebra: "Алгебра",
    geometry: "Геометрія",
    "ukr-lang": "Українська мова",
    history: "Історія України",
  };
  const courseId =
    storedTest?.courseId ??
    (testData?.subject && classNumber
      ? `${subjectSlugMap[testData.subject] ?? testData.subject.toLowerCase().replace(/\s+/g, "-")}-${classNumber}`
      : "");
  const subjectSlug =
    courseId.split("-").slice(0, -1).join("-") || courseId;
  const subjectName =
    testData?.subject ?? subjectLabelMap[subjectSlug] ?? "";
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
      subject?: string;
      classId?: number;
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
    if (subjectName) {
      filters.subject = subjectName;
    }
    if (classId) {
      filters.classId = classId;
    }
    return getMaterials(filters);
  }, [id, courseId, testData?.className, testData?.topicName, subjectName, classId]);
  const sidebarNotes = sidebarMaterials.filter((item) => item.type === "note");
  const sidebarTests = sidebarMaterials.filter((item) => item.type === "test");
  const [classStudents, setClassStudents] = useState<number[]>([]);
  useEffect(() => {
    const apiTeacherId = toNumericId(id) ?? 0;
    if (!apiTeacherId || !classId || !subjectName) {
      setClassStudents([]);
      return;
    }
    getTeacherStudents({
      class_id: classId,
      teacher_id: apiTeacherId,
      subject: subjectName,
    })
      .then((response) => {
        setClassStudents(response.students.map((student) => student.student_id));
      })
      .catch((error) => {
        console.error(error);
        setClassStudents([]);
      });
  }, [id, classId, subjectName]);

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
          id ? `Вчитель ${id}` : "Вчитель"
        }
        activeItem="materials"
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
          <div className="flex items-center gap-4 mb-4 shrink-0">
            <BackButton fallbackPath={backToTopicHref} />
            <Breadcrumbs
              items={[
                { label: "Матеріали", href: backToClassHref },
                { label: testData.className || "Клас", href: backToTopicHref },
                { label: testData.topicName || "Тема", href: backToTopicHref },
                { label: testData.title },
              ]}
            />
          </div>
          <h1 className="text-2xl font-bold text-white shrink-0">
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

      </main>

      <SelectStudentsModal
        isOpen={isAudienceModalOpen}
        onClose={() => setIsAudienceModalOpen(false)}
        students={classStudents.map((studentId) => ({ id: studentId }))}
        onSave={(selection) => {
            console.log("Saved selection", selection);
            setIsAudienceModalOpen(false);
        }}
      />
    </div>
  );
};

export default TeacherTest;
