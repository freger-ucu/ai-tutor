import { useState, useMemo, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { getMaterials, getTopics, isVisibleToStudent } from "../data/materialsStorage";
import StudentSidebar from "../components/StudentSidebar";
import { getStudentData } from "../api/student";
import { getStudentDetails } from "../api/teacher";
import { toNumericId } from "../api/idUtils";
import { getStudentCompletedTestIds } from "../data/studentProgress";
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

const Subjects = [
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

const Student = () => {
  const { studentId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const subjectParam = searchParams.get("subject");
  // Default to first subject (Subjects[0].id) if no URL param
  const [activeSubjectId, setActiveSubjectId] = useState(subjectParam || Subjects[0].id);
  const [apiSubjects, setApiSubjects] = useState<string[]>([]);
  const [studentGrade, setStudentGrade] = useState<number | null>(null);
  const [studentClassId, setStudentClassId] = useState<number | null>(null);
  const [studentError, setStudentError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [studentLevel, setStudentLevel] = useState<"weak" | "medium" | "strong" | null>(null);

  // Sync activeSubjectId with URL param (only when URL changes externally)
  useEffect(() => {
    if (subjectParam && subjectParam !== activeSubjectId) {
      setActiveSubjectId(subjectParam);
    }
  }, [subjectParam]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const apiId = toNumericId(studentId);
    if (!apiId) {
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

  const availableSubjects = useMemo(() => {
    if (!apiSubjects.length) {
      return Subjects;
    }
    const matches = Subjects.filter(
      (subject) =>
        apiSubjects.includes(subject.label) || apiSubjects.includes(subject.id)
    );
    return matches.length ? matches : Subjects;
  }, [apiSubjects]);

  // Validate activeSubjectId against available subjects (only after loading)
  useEffect(() => {
    if (isLoading || !availableSubjects.length) {
      return;
    }
    if (!availableSubjects.find((subject) => subject.id === activeSubjectId)) {
      const newSubject = availableSubjects[0].id;
      setActiveSubjectId(newSubject);
      setSearchParams({ subject: newSubject });
    }
  }, [availableSubjects, activeSubjectId, setSearchParams, isLoading]);

  const gradeSuffix = studentGrade ?? 8;
  const courseIdMap: Record<string, string> = {
    "ukr-lang": `ukr-lang-${gradeSuffix}`,
    algebra: `algebra-${gradeSuffix}`,
    history: `history-${gradeSuffix}`,
  };
  const activeSubjectLabel =
    Subjects.find((subject) => subject.id === activeSubjectId)?.label ?? "";

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

  // Get teacher ID from existing materials to look up the correct level
  const teacherIdForLevel = useMemo(() => {
    const targetCourseId = courseIdMap[activeSubjectId] || activeSubjectId;
    const materials = getMaterials({
      courseId: targetCourseId,
      subject: activeSubjectLabel,
      ...(studentClassId ? { classId: studentClassId } : classLabel ? { className: classLabel } : {}),
    });
    for (const m of materials) {
      const tid = toNumericId(m.teacherId);
      if (tid) return tid;
    }
    return 1; // Fallback to teacher 1 if no materials found
  }, [activeSubjectId, activeSubjectLabel, studentClassId, classLabel]);

  // Fetch student level for visibility filtering
  useEffect(() => {
    const apiId = toNumericId(studentId);
    if (!apiId || !studentClassId || !activeSubjectLabel) {
      setStudentLevel(null);
      return;
    }
    getStudentDetails({
      class_id: studentClassId,
      subject: activeSubjectLabel,
      teacher_id: teacherIdForLevel,
      student_id: apiId,
    })
      .then((response) => {
        setStudentLevel(response.level);
      })
      .catch(() => {
        setStudentLevel(null);
      });
  }, [studentId, studentClassId, activeSubjectLabel, teacherIdForLevel]);

  const formatDate = (value?: string) => {
    if (!value) {
      return "—";
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return "—";
    }
    return parsed.toLocaleDateString("uk-UA", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  };

  const topics = useMemo(() => {
    // Don't compute topics while loading to prevent flickering
    if (isLoading) {
      return [];
    }
    const targetCourseId = courseIdMap[activeSubjectId] || activeSubjectId;
    const className = classLabel;
    if (!className) {
      return [];
    }

    // Fetch topics and materials without teacherId filter - students should see all content for their class
    // Use classId OR className (not both) to avoid overly strict filtering
    const classFilter = studentClassId ? { classId: studentClassId } : className ? { className } : {};
    const fetchedTopics = getTopics({
      courseId: targetCourseId,
      subject: activeSubjectLabel,
      ...classFilter,
    });
    const allTests = getMaterials({
      courseId: targetCourseId,
      subject: activeSubjectLabel,
      ...classFilter,
      type: "test",
    });

    // Filter tests by visibility - only show tests assigned to this student
    const apiId = toNumericId(studentId);
    const tests = apiId
      ? allTests.filter((test) => isVisibleToStudent(test, apiId, studentLevel ?? undefined))
      : allTests;

    const testsByTopic = new Map<string, typeof tests>();
    tests.forEach((test) => {
      if (!test.topicName) {
        return;
      }
      const existing = testsByTopic.get(test.topicName) ?? [];
      testsByTopic.set(test.topicName, [...existing, test]);
    });

    const completedTestIds = getStudentCompletedTestIds(studentId);

    return fetchedTopics.map((topic) => {
      const topicTests = testsByTopic.get(topic.title) ?? [];
      const totalTests = topicTests.length;
      const completedTests = topicTests.filter((test) =>
        completedTestIds.has(test.id)
      ).length;
      const percent = totalTests
        ? Math.round((completedTests / totalTests) * 100)
        : 0;
      return {
        ...topic,
        totalTests,
        completedTests,
        percent,
      };
    });
  }, [activeSubjectId, classLabel, studentClassId, studentId, activeSubjectLabel, isLoading, studentLevel]);
  
  const handleSubjectChange = (nextSubjectId: string) => {
    setActiveSubjectId(nextSubjectId);
    setSearchParams({ subject: nextSubjectId });
  };

  const handleTopicClick = (topicTitle: string) => {
    const targetCourseId = courseIdMap[activeSubjectId] || activeSubjectId;
    navigate(`/student/${studentId}/topic/${targetCourseId}/${encodeURIComponent(topicTitle)}`);
  };

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
        <div className="hidden lg:flex">
          <StudentSidebar
            studentId={studentId || ""}
            classLabel={classLabel || undefined}
            subjects={availableSubjects}
            activeSubjectId={activeSubjectId}
          />
        </div>

        {/* Main Content */}
        <main
          className="flex-1 px-4 py-6 overflow-y-auto lg:px-8 lg:py-10 lg:overflow-visible"
          data-scroll-root="mobile"
        >
          <div className="mb-6 rounded-2xl bg-white/95 px-4 py-3 shadow-md lg:hidden">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-semibold text-slate-700">
                {studentId ? `Учень ${studentId}` : "Учень"}
              </div>
              <button
                type="button"
                onClick={() => navigate("/")}
                className="rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-red-500 hover:border-red-500 hover:text-white"
              >
                Вийти
              </button>
            </div>
            <div className="mt-3 relative">
              <select
                value={activeSubjectId}
                onChange={(event) => handleSubjectChange(event.target.value)}
                className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 pr-10 text-sm font-semibold text-slate-700 shadow-sm focus:border-[#1E73F7] focus:outline-none focus:ring-2 focus:ring-[#1E73F7]/20"
              >
                {availableSubjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.label}
                  </option>
                ))}
              </select>
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m6 9 6 6 6-6" />
                </svg>
              </span>
            </div>
          </div>
          <h1 className="text-xl font-semibold text-white lg:text-2xl">Теми</h1>

          <div className="mt-6 space-y-4">
            {topics.map((topic) => (
              <div
                key={topic.id}
                onClick={() => handleTopicClick(topic.title)}
                className="flex flex-wrap items-center justify-between gap-6 rounded-[24px] bg-white px-5 py-4 shadow-sm cursor-pointer transition-all duration-200 hover:shadow-lg hover:-translate-y-1 hover:bg-slate-50/80 lg:px-8 lg:py-5"
              >
                <div className="w-full min-w-0 font-semibold text-slate-900 break-words lg:min-w-[180px] lg:w-auto">
                  {topic.title}
                </div>

                <div className="flex items-center gap-6">
                  <div>
                    <div className="text-xs font-semibold uppercase text-[#1E73F7]">
                      Тестів пройдено
                    </div>
                    <div className="mt-2 flex items-center gap-3">
                      <div className="h-2.5 w-40 rounded-full bg-[#E9F1FF]">
                        <div
                          className="h-full rounded-full bg-[#1E73F7]"
                          style={{ width: `${topic.percent}%` }}
                        />
                      </div>
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      {topic.completedTests}/{topic.totalTests} тестів
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="w-12 text-right text-sm font-semibold tabular-nums text-slate-700">
                      {topic.percent}%
                    </div>
                    <div>
                      <div className="text-xs font-semibold uppercase text-[#1E73F7]">
                        Дата
                      </div>
                      <div className="mt-2 text-sm font-semibold text-slate-900">
                        {formatDate(topic.createdAt)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {topics.length === 0 && (
              <div className="rounded-2xl border border-white/10 px-6 py-8 text-center text-sm text-white/60">
                Немає тем
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Student;
