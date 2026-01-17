import { useEffect, useMemo, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal";
import TestEditModal from "../components/TestEditModal";
import { getTestById, getTestStatistics, mockTestData } from "../data/mockTests";
import TeacherSidebar from "../components/TeacherSidebar";
import { TestContainer } from "../components/test";
import SelectStudentsModal from "../components/SelectStudentsModal";
import { addMaterial, deleteMaterial, getMaterials, updateMaterial } from "../data/materialsStorage";
import { withGeneratedQuestions } from "../data/testMapper";
import { classLabelToId } from "../data/classUtils";
import { getTeacherStudents } from "../api/teacher";
import { toNumericId } from "../api/idUtils";
import type { TestQuestion } from "../types/testTypes";

const TeacherTest = () => {
  const { id, testId } = useParams();
  const navigate = useNavigate();

  // Modal states
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Force re-fetch trigger for test data after editing
  const [refreshKey, setRefreshKey] = useState(0);

  // Fetch stored test - refreshKey triggers re-fetch after save
  const storedTest = useMemo(
    () => getMaterials({ type: "test" }).find((item) => item.id === testId),
    [testId, refreshKey]
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

  // Fetch class students for the audience modal
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

  const handleDelete = useCallback(() => {
    if (!testId) return;
    const success = deleteMaterial(testId);
    if (success) {
      navigate(backToTopicHref);
    }
    setIsDeleteModalOpen(false);
  }, [testId, navigate, backToTopicHref]);

  /**
   * Handle saving edited questions
   * Updates the test in storage and triggers a re-fetch
   */
  const handleSaveQuestions = useCallback(
    async (updatedQuestions: TestQuestion[]) => {
      if (!testId) return;

      // Convert TestQuestion[] to the storage format (GeneratedQuestion-like)
      // IMPORTANT: Must use answer_options with {answer, correct} format
      // to match what mapGeneratedQuestions expects in testMapper.ts
      const storageQuestions = updatedQuestions.map((q) => ({
        question: q.text,
        type: q.type,
        difficulty: q.difficulty === "hard" ? "difficult" : q.difficulty,
        answer_options: q.options.map((opt) => ({
          answer: opt.text,
          correct: q.correctOptionIds.includes(opt.id),
        })),
        explanation: q.explanation || "",
        topic: q.topic ?? "",
        subtopics: q.subtopics ?? [],
      }));

      // Try to update existing material
      const updated = updateMaterial(testId, {
        questions: storageQuestions,
      });

      // If material doesn't exist in storage, create it with the same ID
      if (!updated && testData) {
        const newMaterial = addMaterial({
          type: "test",
          title: testData.title,
          questions: storageQuestions,
          subject: testData.subject,
          className: testData.className,
          topicName: testData.topicName,
          courseId: courseId,
          classId: classId ?? undefined,
          teacherId: id,
        });
        // Navigate to the new material's URL so refreshKey picks it up
        navigate(`/teacher/${id}/test/${newMaterial.id}`, { replace: true });
        return;
      }

      // Trigger re-fetch of test data
      setRefreshKey((prev) => prev + 1);
    },
    [testId, testData, courseId, classId, id, navigate]
  );

  if (!testData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
        <div className="text-xl text-white">Тест не знайдено</div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#1E73F7] text-slate-900 overflow-hidden flex">
      {/*
        Teacher Sidebar - Static navigation
        Per requirements: Only shows "Навчальні матеріали" and "Учні" links.
        No dynamic content is displayed regardless of current page state.
      */}
      <TeacherSidebar
        teacherName={id ? `Вчитель ${id}` : "Вчитель"}
        activeItem="materials"
        onMaterialsClick={() => navigate(`/teacher/${id}`)}
        onStudentsClick={() => navigate(`/teacher/${id}?view=students`)}
      />

      <main className="flex-1 px-10 py-4 flex flex-col h-full">
          <div className="flex items-center gap-4 mb-4 shrink-0">
            <BackButton fallbackPath={backToTopicHref} />
            <Breadcrumbs
              items={[
                { label: subjectName || "Предмет", href: backToClassHref },
                { label: testData.className || "Клас", href: backToClassHref },
                { label: testData.topicName || "Тема", href: backToTopicHref },
                { label: testData.title },
              ]}
            />
          </div>
          <div className="flex items-center gap-4 shrink-0">
            <h1 className="text-2xl font-bold text-white">
              {testData.title}
            </h1>

            {/* Edit Test button - opens the editing modal */}
            <button
              type="button"
              onClick={() => setIsEditModalOpen(true)}
              className="flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1557c0] hover:border-[#1557c0]"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
              Редагувати тест
            </button>

            {/* Delete button */}
            <button
              type="button"
              onClick={() => setIsDeleteModalOpen(true)}
              className="flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-500 hover:border-red-500"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h18" />
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
              </svg>
              Видалити
            </button>
          </div>

          {/* Test content - same layout as student view with custom scrollbar */}
          <div className="mt-4 flex-1 min-h-0 overflow-y-auto teacher-scrollbar pr-4">
             <TestContainer
               testData={testData}
               statistics={statistics}
               showStatistics={false}
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

      <ConfirmDeleteModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDelete}
        title={testData.title}
        itemType="test"
      />

      {/*
        Test Edit Modal - Full-screen editing interface
        Opens when teacher clicks "Редагувати тест" button.
        Provides add/delete/modify question functionality.
        Changes are saved to localStorage via handleSaveQuestions.
      */}
      <TestEditModal
        isOpen={isEditModalOpen}
        testId={testId ?? ""}
        testTitle={testData.title}
        questions={testData.questions}
        onSave={handleSaveQuestions}
        onClose={() => setIsEditModalOpen(false)}
      />
    </div>
  );
};

export default TeacherTest;
