import { useEffect, useMemo, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getMaterials } from "../data/materialsStorage";
import { getTestById, mockTestData } from "../data/mockTests";
import { TestContainer } from "../components/test";
import { withGeneratedQuestions } from "../data/testMapper";
import { markStudentTestCompleted } from "../data/studentProgress";
import { checkOpenQuestion, getStudentData, getTestFeedback } from "../api/student";
import { toNumericId } from "../api/idUtils";
import { classIdToLabel } from "../data/classUtils";

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

const escapeHtml = (value: string) =>
  value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

const formatInline = (value: string) => {
  const withCode = value.replace(
    /`([^`]+)`/g,
    "<code class=\"rounded bg-slate-100 px-1 py-0.5 text-xs font-semibold text-slate-900\">$1</code>"
  );
  const withBold = withCode.replace(
    /\*\*([^*]+)\*\*/g,
    "<strong class=\"font-semibold text-slate-900\">$1</strong>"
  );
  return withBold.replace(
    /\*([^*]+)\*/g,
    "<em class=\"italic text-slate-800\">$1</em>"
  );
};

const renderMarkdown = (markdown: string) => {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let inUl = false;
  let inOl = false;

  const closeLists = () => {
    if (inUl) {
      html += "</ul>";
      inUl = false;
    }
    if (inOl) {
      html += "</ol>";
      inOl = false;
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      closeLists();
      html += "<br />";
      continue;
    }

    const safe = formatInline(escapeHtml(trimmed));

    if (trimmed.startsWith("### ")) {
      closeLists();
      html += `<h3 class="mt-6 text-base font-semibold text-slate-900">${safe.slice(4)}</h3>`;
      continue;
    }
    if (trimmed.startsWith("## ")) {
      closeLists();
      html += `<h2 class="mt-6 text-lg font-semibold text-slate-900">${safe.slice(3)}</h2>`;
      continue;
    }
    if (trimmed.startsWith("# ")) {
      closeLists();
      html += `<h1 class="mt-6 text-xl font-bold text-slate-900">${safe.slice(2)}</h1>`;
      continue;
    }

    if (trimmed.startsWith("- ")) {
      if (!inUl) {
        closeLists();
        html += "<ul class=\"mt-3 list-disc space-y-1 pl-5\">";
        inUl = true;
      }
      html += `<li>${safe.slice(2)}</li>`;
      continue;
    }

    const orderedMatch = trimmed.match(/^(\d+)\.\s+/);
    if (orderedMatch) {
      if (!inOl) {
        closeLists();
        html += "<ol class=\"mt-3 list-decimal space-y-1 pl-5\">";
        inOl = true;
      }
      html += `<li>${safe.slice(orderedMatch[0].length)}</li>`;
      continue;
    }

    closeLists();
    html += `<p class="mt-3">${safe}</p>`;
  }

  closeLists();
  return html;
};

const StudentTest = () => {
  const { studentId, testId } = useParams();
  const navigate = useNavigate();
  const [apiSubjects, setApiSubjects] = useState<string[]>([]);
  const [studentGrade, setStudentGrade] = useState<number | null>(null);
  const [studentClassId, setStudentClassId] = useState<number | null>(null);
  const [studentError, setStudentError] = useState<string | null>(null);
  const [testFeedback, setTestFeedback] = useState<string | null>(null);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [isFeedbackLoading, setIsFeedbackLoading] = useState(false);

  const storedTest = useMemo(
    () => getMaterials({ type: "test" }).find((item) => item.id === testId),
    [testId]
  );
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

  useEffect(() => {
    setTestFeedback(null);
    setFeedbackError(null);
    setIsFeedbackLoading(false);
  }, [testId]);

  const testData = useMemo(() => {
    if (!testId) return undefined;

    const fallbackBase = getTestById(testId) ?? mockTestData;

    if (storedTest) {
      const base = {
        ...fallbackBase,
        id: storedTest.id,
        title: storedTest.title,
        subject: storedTest.subject ?? fallbackBase.subject,
        className: storedTest.className ?? fallbackBase.className,
        topicName: storedTest.topicName ?? fallbackBase.topicName,
      };
      const withGenerated = Array.isArray(storedTest.questions)
        ? withGeneratedQuestions(base, storedTest.questions)
        : base;
      return {
        ...withGenerated,
        id: storedTest.id,
        title: storedTest.title,
        subject: storedTest.subject ?? withGenerated.subject,
        className: storedTest.className ?? withGenerated.className,
        topicName: storedTest.topicName ?? withGenerated.topicName,
      };
    }

    return fallbackBase;
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
  const subjectName =
    testData?.subject ?? subjectLabelMap[subjectSlug] ?? "";
  const classLabel =
    studentGrade && studentClassId
      ? classIdToLabel(studentGrade, studentClassId)
      : studentGrade
      ? String(studentGrade)
      : "";
  const sidebarClassName = classLabel || testData?.className || "";
  const sidebarTopicName = testData?.topicName ?? "";
  const availableSubjects = apiSubjects.length
    ? subjects.filter((subject) => apiSubjects.includes(subject.label))
    : subjects;
  const sidebarMaterials = useMemo(() => {
    if (!sidebarClassName || !sidebarTopicName) {
      return [];
    }
    const filters: {
      courseId?: string;
      subject?: string;
      classId?: number;
      className?: string;
      topicName?: string;
    } = {
      className: sidebarClassName,
      topicName: sidebarTopicName,
    };
    if (courseId) {
      filters.courseId = courseId;
    }
    if (subjectName) {
      filters.subject = subjectName;
    }
    if (studentClassId) {
      filters.classId = studentClassId;
    }
    return getMaterials(filters);
  }, [courseId, sidebarClassName, sidebarTopicName, subjectName, studentClassId]);
  const sidebarNotes = sidebarMaterials.filter((item) => item.type === "note");
  const sidebarTests = sidebarMaterials.filter((item) => item.type === "test");

  if (studentError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1E73F7]">
        <div className="text-xl text-white">Учня не знайдено</div>
      </div>
    );
  }

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
                {studentId ? `Учень ${studentId}` : "Учень"}
              </div>
              <div className="text-xs text-slate-500">
                Клас: {classLabel || testData?.className || "—"}
              </div>
            </div>
          </div>
          <div className="mt-8 space-y-2">
            {availableSubjects.map((subject) => {
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
              onEvaluateOpen={async ({ question, answer }) => {
                const apiStudentId = toNumericId(studentId);
                if (!apiStudentId || !subjectName) {
                  return { correct: false, feedback: "Неможливо перевірити відповідь." };
                }
                const topic =
                  question.topic ?? testData.topicName ?? testData.title;
                return checkOpenQuestion({
                  student_id: apiStudentId,
                  subject: subjectName,
                  topic,
                  subtopics: question.subtopics ?? [],
                  question: question.text,
                  answer,
                });
              }}
              onFinish={async (result) => {
                if (studentId && testId) {
                  markStudentTestCompleted({
                    studentId,
                    testId,
                    correctAnswers: result.correctAnswers,
                    totalQuestions: result.totalQuestions,
                  });
                }

                const apiStudentId = toNumericId(studentId);
                const apiTeacherId = toNumericId(storedTest?.teacherId);
                if (!apiStudentId || !apiTeacherId || !subjectName) {
                  return;
                }
                setIsFeedbackLoading(true);
                setFeedbackError(null);
                setTestFeedback(null);

                const questions = result.answers
                  .map((answer) => {
                    const question = testData.questions.find(
                      (item) => item.id === answer.questionId
                    );
                    if (!question) {
                      return null;
                    }
                    const selectedText = answer.selectedOptionIds
                      .map(
                        (optionId) =>
                          question.options.find((option) => option.id === optionId)
                            ?.text
                      )
                      .filter((value): value is string => Boolean(value))
                      .join(", ");
                    const responseText =
                      question.type === "open"
                        ? answer.openAnswer?.trim() ?? ""
                        : selectedText;
                    return {
                      question: question.text,
                      answer: responseText,
                      correct: answer.isCorrect,
                      topic: question.topic ?? testData.topicName ?? testData.title,
                      subtopics: question.subtopics ?? [],
                    };
                  })
                  .filter((item): item is NonNullable<typeof item> => Boolean(item));

                try {
                  const feedback = await getTestFeedback({
                    student_id: apiStudentId,
                    teacher_id: apiTeacherId,
                    subject: subjectName,
                    questions,
                  });
                  setTestFeedback(feedback.feedback);
                } catch (error) {
                  console.error(error);
                  setFeedbackError("Не вдалося отримати фідбек по тесту.");
                } finally {
                  setIsFeedbackLoading(false);
                }
              }}
            />
            {(isFeedbackLoading || testFeedback || feedbackError) && (
              <div className="mt-6 rounded-2xl bg-white p-6 text-sm text-slate-700 shadow-sm">
                <div className="text-base font-semibold text-slate-900">
                  Підсумковий фідбек
                </div>
                {isFeedbackLoading && (
                  <div className="mt-3 text-slate-500">Формуємо фідбек...</div>
                )}
                {feedbackError && (
                  <div className="mt-3 text-rose-500">{feedbackError}</div>
                )}
                {testFeedback && (
                  <div
                    className="mt-3"
                    dangerouslySetInnerHTML={{
                      __html: renderMarkdown(testFeedback),
                    }}
                  />
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default StudentTest;
