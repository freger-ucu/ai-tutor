import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import Card from "../components/Card";
import Panel from "../components/Panel";
import StudentSidebar from "../components/StudentSidebar";
import {
  getMaterials,
  getTopics,
  isVisibleToStudent,
} from "../data/materialsStorage";
import { getStudentData } from "../api/student";
import { getStudentDetails } from "../api/teacher";
import { toNumericId } from "../api/idUtils";
import { classIdToLabel } from "../data/classUtils";
import { getStudentTestCompletionMap } from "../data/studentProgress";

// Cache student class label in localStorage for stable sidebar display
const getStudentClassCache = (studentId: string | undefined): string | null => {
  if (!studentId) return null;
  try {
    return localStorage.getItem(`student_class_${studentId}`);
  } catch {
    return null;
  }
};

const setStudentClassCache = (
  studentId: string | undefined,
  classLabel: string,
) => {
  if (!studentId || !classLabel) return;
  try {
    localStorage.setItem(`student_class_${studentId}`, classLabel);
  } catch {
    // Ignore localStorage errors
  }
};

const subjects = [
  {
    id: "algebra",
    label: "Алгебра",
    icon: <span className="text-xl">√x</span>,
  },
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

const courseLabels: Record<string, string> = {
  "algebra-8": "Алгебра",
  "geometry-8": "Геометрія",
  "history-8": "Історія України",
  "ukr-lang-8": "Українська мова",
  "algebra-9": "Алгебра",
  "geometry-9": "Геометрія",
  "history-9": "Історія України",
  "ukr-lang-9": "Українська мова",
};
const subjectLabelMap: Record<string, string> = {
  algebra: "Алгебра",
  geometry: "Геометрія",
  "ukr-lang": "Українська мова",
  history: "Історія України",
};

const StudentTopic = () => {
  const { studentId, courseId, topicId } = useParams();
  const [apiSubjects, setApiSubjects] = useState<string[]>([]);
  const [studentGrade, setStudentGrade] = useState<number | null>(null);
  const [studentClassId, setStudentClassId] = useState<number | null>(null);
  const [studentError, setStudentError] = useState<string | null>(null);
  const [studentLevel, setStudentLevel] = useState<
    "weak" | "medium" | "strong" | null
  >(null);
  const [isLoading, setIsLoading] = useState(true);

  const decodedTopic = topicId ? decodeURIComponent(topicId) : "";
  const decodedCourse = courseId ? decodeURIComponent(courseId) : "";
  const courseLabel = decodedCourse
    ? (courseLabels[decodedCourse] ?? decodedCourse)
    : "";
  const subjectSlug =
    decodedCourse.split("-").slice(0, -1).join("-") || decodedCourse;
  const subjectName = subjectLabelMap[subjectSlug] ?? courseLabel ?? "";
  const backToSubjectHref = `/student/${studentId}?subject=${subjectSlug}`;

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

  // Get topic date from storage
  const topicDate = useMemo(() => {
    const topics = getTopics({ courseId: decodedCourse });
    const topic = topics.find((t) => t.title === decodedTopic);
    return topic?.createdAt;
  }, [decodedCourse, decodedTopic]);

  const formatDate = (value?: string) => {
    if (!value) return "—";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return "—";
    return parsed.toLocaleDateString("uk-UA", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  };

  const [notes, setNotes] = useState<{ id: string; title: string }[]>([]);
  const [tests, setTests] = useState<{ id: string; title: string }[]>([]);

  // Get test completion data for current student
  const testCompletionMap = useMemo(
    () => getStudentTestCompletionMap(studentId),
    [studentId],
  );

  useEffect(() => {
    const apiId = toNumericId(studentId);
    if (!apiId) {
      setStudentError("Учня не знайдено");
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
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
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [studentId]);

  // Fetch student level for visibility filtering
  // We need to get the teacher ID from existing materials to look up the correct level
  const teacherIdForLevel = useMemo(() => {
    const materials = getMaterials({
      courseId: decodedCourse,
      subject: subjectName,
      ...(studentClassId
        ? { classId: studentClassId }
        : classLabel
          ? { className: classLabel }
          : {}),
    });
    // Find first material with a valid teacherId
    for (const m of materials) {
      const tid = toNumericId(m.teacherId);
      if (tid) return tid;
    }
    return 1; // Fallback to teacher 1 if no materials found
  }, [decodedCourse, subjectName, studentClassId, classLabel]);

  useEffect(() => {
    const apiId = toNumericId(studentId);
    if (!apiId || !studentClassId || !subjectName) {
      setStudentLevel(null);
      return;
    }
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
      });
  }, [studentId, studentClassId, subjectName, teacherIdForLevel]);

  const availableSubjects = useMemo(() => {
    if (!apiSubjects.length) {
      return subjects;
    }
    const matches = subjects.filter(
      (subject) =>
        apiSubjects.includes(subject.label) || apiSubjects.includes(subject.id),
    );
    return matches.length ? matches : subjects;
  }, [apiSubjects]);

  useEffect(() => {
    // Don't fetch materials while still loading student data to prevent flickering
    if (studentError || isLoading) return;

    const apiId = toNumericId(studentId);
    // Fetch materials without teacherId filter - students should see all materials for their class
    // Use classId OR className (not both) to avoid overly strict filtering
    const materials = getMaterials({
      courseId: decodedCourse,
      subject: subjectName,
      ...(studentClassId
        ? { classId: studentClassId }
        : classLabel
          ? { className: classLabel }
          : {}),
      topicName: decodedTopic,
    });

    // Filter materials by visibility - STRICT assignment targeting
    const visibleMaterials = apiId
      ? materials.filter((m) =>
          isVisibleToStudent(m, apiId, studentLevel ?? undefined),
        )
      : materials;

    const storedNotes = visibleMaterials
      .filter((m) => m.type === "note")
      .map((m) => ({ id: m.id, title: m.title }));

    const storedTests = visibleMaterials
      .filter((m) => m.type === "test")
      .map((m) => ({ id: m.id, title: m.title }));

    setNotes(storedNotes);
    setTests(storedTests);
  }, [
    studentError,
    isLoading,
    classLabel,
    studentClassId,
    studentLevel,
    decodedCourse,
    decodedTopic,
    studentId,
    subjectName,
  ]);

  if (studentError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
        <div className="text-xl text-white">Учня не знайдено</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#1E73F7] text-slate-900">
      <div className="flex min-h-screen">
        {/* Static sidebar - always shows only subjects list */}
        <div className="hidden lg:flex">
          <StudentSidebar
            studentId={studentId || ""}
            classLabel={classLabel || undefined}
            subjects={availableSubjects}
            activeSubjectId={subjectSlug}
          />
        </div>

        <main
          className="flex-1 flex flex-col h-screen overflow-hidden lg:px-8 lg:py-10 px-4 py-6"
          data-scroll-root="mobile"
        >
          <div className="mb-4 rounded-2xl bg-white/95 px-4 py-3 shadow-md lg:hidden shrink-0">
            <div className="flex items-center justify-between gap-3">
              <Link
                to={backToSubjectHref}
                className="text-sm font-semibold text-[#1E73F7]"
              >
                ← {subjectName || "Предмет"}
              </Link>
              <Link
                to="/"
                className="rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-red-500 hover:border-red-500 hover:text-white"
              >
                Вийти
              </Link>
            </div>
            <div className="mt-2 text-sm font-semibold text-slate-800 wrap-break-word">
              {decodedTopic || "Тема"}
            </div>
            <div className="mt-1 text-xs text-slate-500">{courseLabel}</div>
          </div>
          <div className="hidden items-center gap-4 mb-6 lg:flex shrink-0">
            <BackButton fallbackPath={backToSubjectHref} />
            <Breadcrumbs
              items={[
                { label: courseLabel || subjectName, href: backToSubjectHref },
                { label: decodedTopic || "Тема" },
              ]}
            />
          </div>

          <Panel className="shrink-0">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold text-slate-900 lg:text-2xl w-full wrap-break-word">
                  {decodedTopic}
                </h1>
                <div className="mt-1 text-sm text-slate-500">{courseLabel}</div>
              </div>
              <div className="text-center">
                <div className="text-xs font-semibold uppercase text-slate-400">
                  Дата
                </div>
                <div className="mt-1 text-sm font-semibold text-slate-900">
                  {formatDate(topicDate)}
                </div>
              </div>
            </div>
          </Panel>

          <div className="mt-6 flex-1 min-h-0 grid gap-6 lg:mt-8 lg:grid-cols-[1.05fr_0.95fr]">
            <section className="flex flex-col min-h-0">
              <h2 className="text-lg font-semibold text-white lg:text-xl shrink-0">
                Конспекти
              </h2>
              <div className="mt-4 flex-1 min-h-0 overflow-y-auto flex flex-col gap-4 pr-2 scroll-smooth scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent lg:gap-5">
                {notes.length > 0 ? (
                  notes.map((item) => (
                    <Link
                      key={item.id}
                      to={`/student/${studentId}/note/${courseId}/${topicId}/${item.id}`}
                    >
                      <Card className="flex items-center gap-3 px-5 py-4 cursor-pointer border border-slate-100 shadow-md transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-xl hover:shadow-[#1E73F7]/15 hover:border-[#1E73F7]/30 active:scale-[0.98] lg:px-6 lg:py-5">
                        <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white shadow-sm transition-all duration-300">
                          <img
                            src="/src/assets/Vector.svg"
                            alt=""
                            className="h-4 w-4"
                          />
                        </span>
                        <span className="text-sm font-semibold text-slate-900 lg:text-base">
                          {item.title}
                        </span>
                      </Card>
                    </Link>
                  ))
                ) : (
                  <div className="rounded-2xl border border-white/10 px-6 py-8 text-center text-sm text-white/40">
                    Немає конспектів
                  </div>
                )}
              </div>
            </section>

            <section className="flex flex-col min-h-0">
              <h2 className="text-lg font-semibold text-white lg:text-xl shrink-0">
                Тести
              </h2>
              <div className="mt-4 flex-1 min-h-0 overflow-y-auto flex flex-col gap-4 pr-2 scroll-smooth scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent lg:gap-5">
                {tests.length > 0 ? (
                  tests.map((item) => {
                    const completion = testCompletionMap.get(item.id);
                    const barSegments = 10;
                    const correctSegments = completion?.totalQuestions
                      ? Math.round(
                          (completion.correctAnswers /
                            completion.totalQuestions) *
                            barSegments,
                        )
                      : 0;
                    const clampedCorrectSegments = Math.min(
                      barSegments,
                      Math.max(0, correctSegments),
                    );
                    const isCompleted = Boolean(completion);

                  return (
                    <Link key={item.id} to={`/student/${studentId}/test/${item.id}`}>
                      <Card className="flex flex-col gap-4 px-5 py-4 cursor-pointer border border-slate-100 shadow-md transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-xl hover:shadow-[#1E73F7]/15 hover:border-[#1E73F7]/30 active:scale-[0.98] lg:px-6 lg:py-5">
                        <div className="flex items-center gap-3 min-w-0">
                          <img
                            src="/src/assets/Group.svg"
                            alt=""
                            className="h-6 w-6 transition-transform duration-300"
                          />
                          <span className="text-sm font-semibold text-slate-900 lg:text-base wrap-break-word">
                            {item.title}
                          </span>
                        </div>
                          <div className="flex items-center justify-between gap-3">
                            <div className="flex items-center gap-1">
                              {Array.from({ length: barSegments }).map((_, index) => (
                                <span
                                  key={index}
                                  className={`h-2 w-5 rounded-full ${
                                    isCompleted
                                      ? index < clampedCorrectSegments
                                        ? "bg-[#6FDB9B]"
                                        : "bg-[#E63C3C]"
                                      : "bg-slate-200"
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                        </Card>
                      </Link>
                    );
                  })
                ) : (
                  <div className="rounded-2xl border border-white/10 px-6 py-8 text-center text-sm text-white/40">
                    Немає тестів
                  </div>
                )}
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
};

export default StudentTopic;
