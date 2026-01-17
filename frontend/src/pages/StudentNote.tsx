import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import LectureContent from "../components/LectureContent";
import StudentSidebar from "../components/StudentSidebar";
import { getMaterials, isVisibleToStudent } from "../data/materialsStorage";
import { getStudentData } from "../api/student";
import { getStudentDetails } from "../api/teacher";
import { toNumericId } from "../api/idUtils";
import { classIdToLabel } from "../data/classUtils";

// Cache student class label in localStorage for stable sidebar display
const getStudentClassCache = (studentId: string | undefined): string | null => {
  if (!studentId) return null;
  try {
    return localStorage.getItem(`student_class_${studentId}`);
  } catch {
    return null;
  }
};

const setStudentClassCache = (studentId: string | undefined, classLabel: string) => {
  if (!studentId || !classLabel) return;
  try {
    localStorage.setItem(`student_class_${studentId}`, classLabel);
  } catch {
    // Ignore localStorage errors
  }
};

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
const subjectLabelMap: Record<string, string> = {
  algebra: "Алгебра",
  history: "Історія України",
  "ukr-lang": "Українська мова",
};


const StudentNote = () => {
  const { studentId, courseId, topicId, noteId } = useParams();
  const [apiSubjects, setApiSubjects] = useState<string[]>([]);
  const [studentGrade, setStudentGrade] = useState<number | null>(null);
  const [studentClassId, setStudentClassId] = useState<number | null>(null);
  const [studentError, setStudentError] = useState<string | null>(null);
  const [studentLevel, setStudentLevel] = useState<"weak" | "medium" | "strong" | null>(null);
  const [isLevelLoading, setIsLevelLoading] = useState(true);

  const decodedCourse = courseId ? decodeURIComponent(courseId) : "";
  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const subjectSlug = decodedCourse.split("-").slice(0, -1).join("-") || decodedCourse;
  const subjectName = subjectLabelMap[subjectSlug] ?? decodedCourse;
  const encodedTopic = decodedTopic ? encodeURIComponent(decodedTopic) : "";
  const backToSubjectHref = `/student/${studentId}?subject=${subjectSlug}`;
  const backToTopicHref =
    courseId && encodedTopic
      ? `/student/${studentId}/topic/${courseId}/${encodedTopic}`
      : backToSubjectHref;

  // Use cached classLabel for stable sidebar display, update cache when data is loaded
  const cachedClassLabel = getStudentClassCache(studentId);
  const computedClassLabel =
    studentGrade && studentClassId
      ? classIdToLabel(studentGrade, studentClassId)
      : studentGrade
      ? String(studentGrade)
      : "";

  // Update cache when we have a valid classLabel
  useEffect(() => {
    if (computedClassLabel) {
      setStudentClassCache(studentId, computedClassLabel);
    }
  }, [studentId, computedClassLabel]);

  // Use cached value while loading, computed value when available
  const classLabel = computedClassLabel || cachedClassLabel || "";

  const noteMaterial = useMemo(
    () => getMaterials({ type: "note" }).find((item) => item.id === noteId),
    [noteId]
  );
  const noteTitle = noteMaterial?.title ?? "Конспект";
  const availableSubjects = useMemo(() => {
    if (!apiSubjects.length) {
      return subjects;
    }
    const matches = subjects.filter(
      (subject) =>
        apiSubjects.includes(subject.label) || apiSubjects.includes(subject.id)
    );
    return matches.length ? matches : subjects;
  }, [apiSubjects]);

  useEffect(() => {
    const apiId = toNumericId(studentId);
    if (!apiId) {
      setStudentError("Учня не знайдено");
      return;
    }
    getStudentData(apiId)
      .then((response) => {
        setApiSubjects(response.subjects);
        setStudentGrade(response.class_number);
        setStudentClassId(response.class_id);
        setStudentError(null);
      })
      .catch((error) => {
        console.error(error);
        setStudentError("Учня не знайдено");
      });
  }, [studentId]);

  // Get teacher ID from the material to look up the correct level
  const teacherIdForLevel = useMemo(() => {
    const tid = toNumericId(noteMaterial?.teacherId);
    return tid ?? 1; // Fallback to teacher 1
  }, [noteMaterial?.teacherId]);

  // Fetch student level for visibility check
  useEffect(() => {
    const apiId = toNumericId(studentId);
    if (!apiId || !studentClassId || !subjectName) {
      setStudentLevel(null);
      setIsLevelLoading(false);
      return;
    }
    setIsLevelLoading(true);
    getStudentDetails({
      class_id: studentClassId,
      subject: subjectName,
      teacher_id: teacherIdForLevel,
      student_id: apiId,
    })
      .then((response) => {
        setStudentLevel(response.level);
      })
      .catch(() => {
        setStudentLevel(null);
      })
      .finally(() => {
        setIsLevelLoading(false);
      });
  }, [studentId, studentClassId, subjectName, teacherIdForLevel]);

  // Check if student can see this material
  const accessDenied = useMemo(() => {
    if (!noteMaterial) return null; // Material doesn't exist - different error
    if (isLevelLoading) return null; // Still loading

    const apiId = toNumericId(studentId);
    if (!apiId) return null;

    const canSee = isVisibleToStudent(noteMaterial, apiId, studentLevel ?? undefined);
    if (canSee) return null;

    // Determine reason for denial
    if (noteMaterial.assignmentScope === "levels" && noteMaterial.assignedLevels?.length) {
      const levelNames: Record<string, string> = {
        weak: "початкового",
        medium: "середнього",
        strong: "високого",
      };
      const levelList = noteMaterial.assignedLevels.map(l => levelNames[l] || l).join(", ");
      return `Цей конспект призначений для учнів ${levelList} рівня.`;
    }
    if (noteMaterial.assignmentScope === "students") {
      return "Цей конспект призначений для інших учнів.";
    }
    return "У вас немає доступу до цього конспекту.";
  }, [noteMaterial, studentId, studentLevel, isLevelLoading]);

  if (studentError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
        <div className="text-xl text-white">Учня не знайдено</div>
      </div>
    );
  }

  if (accessDenied) {
    return (
      <div className="h-screen bg-[#1E73F7] text-slate-900 overflow-hidden flex">
        <StudentSidebar
          studentId={studentId || ""}
          classLabel={classLabel || undefined}
          subjects={availableSubjects}
          activeSubjectId={subjectSlug}
        />
        <main className="flex-1 px-8 py-10 flex flex-col h-full overflow-hidden">
          <div className="flex items-center gap-4 mb-4 shrink-0">
            <BackButton fallbackPath={backToTopicHref} />
            <Breadcrumbs
              items={[
                { label: subjectName, href: backToSubjectHref },
                { label: decodedTopic || "Тема", href: backToTopicHref },
                { label: noteTitle },
              ]}
            />
          </div>
          <div className="flex-1 flex items-center justify-center">
            <div className="rounded-[28px] bg-white p-8 shadow-sm max-w-md text-center">
              <div className="text-5xl mb-4">🔒</div>
              <h2 className="text-xl font-bold text-slate-900 mb-2">Доступ обмежено</h2>
              <p className="text-slate-600">{accessDenied}</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#1E73F7] text-slate-900 overflow-hidden flex">
        {/* Static sidebar - always shows only subjects list */}
        <StudentSidebar
          studentId={studentId || ""}
          classLabel={classLabel || undefined}
          subjects={availableSubjects}
          activeSubjectId={subjectSlug}
        />

        <main className="flex-1 px-8 py-10 flex flex-col h-full overflow-hidden">
          <div className="flex items-center gap-4 mb-4 shrink-0">
            <BackButton fallbackPath={backToTopicHref} />
            <Breadcrumbs
              items={[
                { label: subjectName, href: backToSubjectHref },
                { label: decodedTopic || "Тема", href: backToTopicHref },
                { label: noteTitle },
              ]}
            />
          </div>
          <h1 className="text-2xl font-bold text-white shrink-0">
            Конспект. {noteTitle}
          </h1>

          <div className="mt-5 flex-1 min-h-0 rounded-[28px] bg-white p-6 shadow-sm overflow-y-auto note-scrollbar">
            <div className="rounded-[20px] bg-white">
              <div className="break-words">
                {noteMaterial?.content ? (
                  <LectureContent
                    content={noteMaterial.content}
                    sources={noteMaterial.sources ?? []}
                    userRole="student"
                    title={noteTitle}
                  />
                ) : (
                  <div className="space-y-6">
                    <p>
                      <strong>Іменник</strong> — самостійна частина мови, що
                      називає предмети, істот, явища, поняття і відповідає на
                      питання хто? що?
                    </p>

                    <div>
                      <strong>Значення іменників:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>істоти: учень, кіт</li>
                        <li>неістоти: стіл, дощ</li>
                        <li>абстрактні поняття: дружба, сміливість</li>
                      </ul>
                    </div>

                    <div>
                      <strong>Граматичні ознаки:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>Рід: чоловічий (день), жіночий (ніч), середній (вікно)</li>
                        <li>Число: однина (книга), множина (книги)</li>
                        <li>
                          Відмінки (7): називний, родовий, давальний,
                          знахідний, орудний, місцевий, кличний
                        </li>
                        <li>Відміни: I, II, III, IV</li>
                      </ul>
                    </div>

                    <div>
                      <strong>Власні й загальні іменники:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>власні: Київ, Марія (пишуться з великої літери)</li>
                        <li>загальні: місто, дівчина</li>
                      </ul>
                    </div>

                    <div>
                      <strong>Конкретні й абстрактні:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>конкретні: олівець, дерево</li>
                        <li>абстрактні: радість, знання</li>
                      </ul>
                    </div>

                    <div>
                      <strong>Синтаксична роль у реченні:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>підмет: Книга лежить на столі.</li>
                        <li>додаток: Я читаю книгу.</li>
                      </ul>
                    </div>

                    <div>
                      <strong>Правопис:</strong>
                      <ul className="list-disc pl-5 mt-1 space-y-1">
                        <li>з великої літери — власні назви</li>
                        <li>не з іменниками: не друг, неспокій</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

        </main>
    </div>
  );
};

export default StudentNote;
