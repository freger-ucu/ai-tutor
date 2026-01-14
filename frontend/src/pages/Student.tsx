import { useState, useMemo, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getMaterials, getTopics } from "../data/materialsStorage";
import PillButton from "../components/PillButton";
import { getStudentData } from "../api/student";
import { toNumericId } from "../api/idUtils";
import { getStudentCompletedTestIds } from "../data/studentProgress";
import { classIdToLabel } from "../data/classUtils";

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
  const [activeSubjectId, setActiveSubjectId] = useState("ukr-lang");
  const [apiSubjects, setApiSubjects] = useState<string[]>([]);
  const [studentGrade, setStudentGrade] = useState<number | null>(null);
  const [studentClassId, setStudentClassId] = useState<number | null>(null);
  const [studentError, setStudentError] = useState<string | null>(null);

  useEffect(() => {
    const apiId = toNumericId(studentId);
    if (!apiId) {
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

  const availableSubjects = apiSubjects.length
    ? Subjects.filter((subject) => apiSubjects.includes(subject.label))
    : Subjects;

  useEffect(() => {
    if (!availableSubjects.length) {
      return;
    }
    if (!availableSubjects.find((subject) => subject.id === activeSubjectId)) {
      setActiveSubjectId(availableSubjects[0].id);
    }
  }, [availableSubjects, activeSubjectId]);

  const gradeSuffix = studentGrade ?? 8;
  const courseIdMap: Record<string, string> = {
    "ukr-lang": `ukr-lang-${gradeSuffix}`,
    algebra: `algebra-${gradeSuffix}`,
    history: `history-${gradeSuffix}`,
  };
  const activeSubjectLabel =
    Subjects.find((subject) => subject.id === activeSubjectId)?.label ?? "";
  const classLabel =
    studentGrade && studentClassId
      ? classIdToLabel(studentGrade, studentClassId)
      : studentGrade
      ? String(studentGrade)
      : "";

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
    const targetCourseId = courseIdMap[activeSubjectId] || activeSubjectId;
    const className = classLabel;
    if (!className) {
      return [];
    }

    const fetchedTopics = getTopics({
      courseId: targetCourseId,
      subject: activeSubjectLabel,
      classId: studentClassId ?? undefined,
      className,
    });
    const tests = getMaterials({
      courseId: targetCourseId,
      subject: activeSubjectLabel,
      classId: studentClassId ?? undefined,
      className,
      type: "test",
    });
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
  }, [activeSubjectId, classLabel, studentClassId, studentId, activeSubjectLabel]);
  
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
    <div className="min-h-screen bg-[#1E73F7] font-sans text-slate-900">
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="fixed left-0 top-0 h-screen w-64 bg-white flex flex-col z-10">
          <div className="px-6 py-8">
            <div className="flex items-center gap-3">
               {/* Avatar */}
              <div
                className="h-10 w-10 overflow-hidden rounded-full bg-slate-200"
                style={{
                  backgroundImage: "url('https://images.unsplash.com/photo-1599566150163-29194dcaad36?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80')",
                  backgroundSize: "cover",
                }}
              />
              <div className="text-sm font-bold text-slate-900">
                {studentId ? `Учень ${studentId}` : "Учень"}
              </div>
            </div>
          </div>

          <div className="mt-4 flex-1 space-y-1 px-4">
            {availableSubjects.map((subject) => {
              const isActive = activeSubjectId === subject.id;
              return (
                <button
                  key={subject.id}
                  onClick={() => setActiveSubjectId(subject.id)}
                  className={`flex w-full items-center gap-4 rounded-xl px-4 py-3 text-sm font-semibold transition-all ${
                    isActive
                      ? "bg-[#E9F1FF] text-[#1E73F7]"
                      : "text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  <div className={`flex items-center justify-center ${isActive ? "text-[#1E73F7]" : "text-slate-900"}`}>
                    {subject.icon}
                  </div>
                  {subject.label}
                </button>
              );
            })}
          </div>
        </aside>

        {/* Main Content */}
        <div className="ml-64 w-full p-10">
          <h1 className="text-2xl font-semibold text-white">Теми</h1>

          <div className="mt-6 space-y-4">
            {topics.map((topic) => (
              <div
                key={topic.id}
                className="flex flex-wrap items-center justify-between gap-6 rounded-[24px] bg-white px-8 py-5 shadow-sm"
              >
                <div className="min-w-[180px] font-semibold text-slate-900">
                  {topic.title}
                </div>

                <div className="min-w-[220px]">
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
                    <div className="text-sm font-semibold text-slate-700">
                      {topic.percent}%
                    </div>
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {topic.completedTests}/{topic.totalTests} тестів
                  </div>
                </div>

                <div className="min-w-[160px]">
                  <div className="text-xs font-semibold uppercase text-[#1E73F7]">
                    Дата
                  </div>
                  <div className="mt-2 text-sm font-semibold text-slate-900">
                    {formatDate(topic.createdAt)}
                  </div>
                </div>

                <PillButton
                  label="Переглянути"
                  className="bg-[#E9F1FF] text-[#1E73F7] hover:bg-[#D4E4FF]"
                  onClick={() => handleTopicClick(topic.title)}
                />
              </div>
            ))}

            {topics.length === 0 && (
              <div className="rounded-2xl border border-white/10 px-6 py-8 text-center text-sm text-white/60">
                Немає тем
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Student;
