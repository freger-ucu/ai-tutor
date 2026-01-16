import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BackButton from "../components/BackButton";
import Breadcrumbs from "../components/Breadcrumbs";
import MarkdownContent from "../components/MarkdownContent";
import StudentSidebar from "../components/StudentSidebar";
import { getMaterials } from "../data/materialsStorage";
import { getTestById, mockTestData } from "../data/mockTests";
import { TestContainer } from "../components/test";
import { withGeneratedQuestions } from "../data/testMapper";
import {
  getStudentTestCompletionMap,
  markStudentTestCompleted,
} from "../data/studentProgress";
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
  const [hasJustCompleted, setHasJustCompleted] = useState(false);

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
    setHasJustCompleted(false);
  }, [testId]);

  const completionMap = useMemo(
    () => getStudentTestCompletionMap(studentId),
    [studentId]
  );
  const completion = testId ? completionMap.get(testId) : undefined;
  const alreadyCompleted = Boolean(completion);
  const isViewingCompleted = alreadyCompleted && !hasJustCompleted;

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
  const subjectSlug =
    courseId.split("-").slice(0, -1).join("-") || courseId;
  const subjectName =
    testData?.subject ?? subjectLabelMap[subjectSlug] ?? "";
  const backToSubjectHref = `/student/${studentId}?subject=${subjectSlug}`;
  const backToTopicHref =
    courseId && encodedTopic
      ? `/student/${studentId}/topic/${courseId}/${encodedTopic}`
      : backToSubjectHref;

  const classLabel =
    studentGrade && studentClassId
      ? classIdToLabel(studentGrade, studentClassId)
      : studentGrade
      ? String(studentGrade)
      : "";

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
        {/* Static sidebar - always shows only subjects list */}
        <StudentSidebar
          studentId={studentId || ""}
          classLabel={classLabel || testData?.className || undefined}
          subjects={availableSubjects}
          activeSubjectId={subjectSlug}
        />
        <main className="flex-1 px-8 py-10">
          <div className="flex items-center gap-4 mb-6">
            <BackButton fallbackPath={backToTopicHref} />
            <Breadcrumbs
              items={[
                { label: subjectName || "Предмет", href: backToSubjectHref },
                { label: testData.topicName || "Тема", href: backToTopicHref },
                { label: testData.title },
              ]}
            />
          </div>
          <div>
            <TestContainer
              testData={testData}
              showStatistics={false}
              viewMode="student"
              initialAnswers={isViewingCompleted ? completion?.answers : undefined}
              forceFinished={isViewingCompleted}
              onExit={() => {
                navigate(backToTopicHref);
              }}
              feedbackNode={
                (isViewingCompleted && completion?.feedback) ||
                isFeedbackLoading ||
                testFeedback ||
                feedbackError ? (
                  <div className="h-full w-full overflow-y-auto rounded-2xl bg-white p-6 text-sm text-slate-700 shadow-sm">
                    <div className="text-base font-semibold text-slate-900">
                      Підсумковий фідбек
                    </div>
                    {isViewingCompleted && completion?.feedback && (
                      <MarkdownContent content={completion.feedback} className="mt-3" />
                    )}
                    {!isViewingCompleted && isFeedbackLoading && (
                      <div className="mt-3 text-slate-500">Формуємо фідбек...</div>
                    )}
                    {!isViewingCompleted && feedbackError && (
                      <div className="mt-3 text-rose-500">{feedbackError}</div>
                    )}
                    {!isViewingCompleted && testFeedback && (
                      <MarkdownContent content={testFeedback} className="mt-3" />
                    )}
                  </div>
                ) : null
              }
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
                setHasJustCompleted(true);
                if (studentId && testId) {
                  markStudentTestCompleted({
                    studentId,
                    testId,
                    correctAnswers: result.correctAnswers,
                    totalQuestions: result.totalQuestions,
                    answers: result.answers,
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
                  if (studentId && testId) {
                    markStudentTestCompleted({
                      studentId,
                      testId,
                      correctAnswers: result.correctAnswers,
                      totalQuestions: result.totalQuestions,
                      answers: result.answers,
                      feedback: feedback.feedback,
                    });
                  }
                } catch (error) {
                  console.error(error);
                  setFeedbackError("Не вдалося отримати фідбек по тесту.");
                } finally {
                  setIsFeedbackLoading(false);
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
