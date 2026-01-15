import { useState, useMemo, useEffect, useRef, type ReactNode } from "react";
import type {
  TestData,
  TestStatistics,
  TestAnswer,
  TestQuestion,
} from "../../types/testTypes";
import TestNavigation from "./TestNavigation";
import TestQuestionCard from "./TestQuestionCard";
import TestStatisticsCard from "./TestStatisticsCard";
import TestExplanation from "./TestExplanation";

interface TestContainerProps {
  testData: TestData;
  statistics?: TestStatistics;
  showStatistics?: boolean;
  /** 'teacher' shows pre-answered test results, 'student' lets user answer */
  viewMode?: "teacher" | "student";
  initialAnswers?: TestAnswer[];
  forceFinished?: boolean;
  onEvaluateOpen?: (payload: {
    question: TestQuestion;
    answer: string;
  }) => Promise<{ correct: boolean; feedback?: string }>;
  onExit?: () => void;
  feedbackNode?: ReactNode;
  onFinish?: (result: {
    correctAnswers: number;
    totalQuestions: number;
    answers: TestAnswer[];
  }) => void | Promise<void>;
}

const TestContainer = ({
  testData,
  statistics,
  showStatistics = false,
  viewMode = "student",
  initialAnswers,
  forceFinished = false,
  onEvaluateOpen,
  onExit,
  feedbackNode,
  onFinish,
}: TestContainerProps) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Map<string, TestAnswer>>(new Map());
  const [isFinished, setIsFinished] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackMaxHeight, setFeedbackMaxHeight] = useState<number | null>(null);
  const leftColumnRef = useRef<HTMLDivElement | null>(null);

  const areSetsEqual = (a: string[], b: string[]) => {
    if (a.length !== b.length) return false;
    const normalizedA = [...a].sort();
    const normalizedB = [...b].sort();
    return normalizedA.every((value, index) => value === normalizedB[index]);
  };

  const isChoiceCorrect = (question: TestQuestion, selectedIds: string[]) => {
    if (!selectedIds.length || !question.correctOptionIds?.length) {
      return false;
    }
    return areSetsEqual(selectedIds, question.correctOptionIds);
  };

  const getQuestionStatus = (
    question: TestQuestion,
    answer?: TestAnswer
  ): "correct" | "incorrect" | "partial" | "neutral" => {
    if (!answer) {
      return "neutral";
    }
    if (question.type === "open") {
      return answer.isCorrect ? "correct" : "incorrect";
    }
    const selected = answer.selectedOptionIds ?? [];
    const correct = question.correctOptionIds ?? [];
    if (!selected.length || !correct.length) {
      return "neutral";
    }
    const isExact =
      selected.length === correct.length &&
      selected.every((id) => correct.includes(id));
    if (isExact) {
      return "correct";
    }
    const hasCorrectSelection = selected.some((id) => correct.includes(id));
    return hasCorrectSelection ? "partial" : "incorrect";
  };

  const toIncorrectSelection = (question: TestQuestion) => {
    const incorrectOptions = question.options
      .map((option) => option.id)
      .filter((id) => !question.correctOptionIds.includes(id));
    if (incorrectOptions.length) {
      return [incorrectOptions[0]];
    }
    if (question.options.length) {
      return [question.options[0].id];
    }
    return [];
  };

  // Pre-populate answers for teacher view with correct options from test data
  useEffect(() => {
    if (viewMode === "teacher") {
      const preFilledAnswers = new Map<string, TestAnswer>();
      testData.questions.forEach((question) => {
        const selectedOptionIds =
          question.type === "open"
            ? []
            : question.correctOptionIds;
        preFilledAnswers.set(question.id, {
          questionId: question.id,
          selectedOptionIds,
          openAnswer: question.type === "open" ? "—" : undefined,
          isCorrect: true,
        });
      });
      setAnswers(preFilledAnswers);
    }
  }, [viewMode, testData.questions]);

  useEffect(() => {
    if (viewMode === "student") {
      if (forceFinished) {
        return;
      }
      setAnswers(new Map());
      setIsFinished(false);
      setIsSubmitting(false);
    }
  }, [viewMode, testData.id, forceFinished]);

  useEffect(() => {
    if (viewMode !== "student" || !forceFinished) {
      return;
    }
    const nextAnswers = new Map<string, TestAnswer>();
    (initialAnswers ?? []).forEach((answer) => {
      nextAnswers.set(answer.questionId, answer);
    });
    setAnswers(nextAnswers);
    setIsFinished(true);
    setIsSubmitting(false);
  }, [viewMode, forceFinished, initialAnswers, testData.id]);

  useEffect(() => {
    setCurrentQuestionIndex(0);
  }, [testData.id]);

  useEffect(() => {
    const node = leftColumnRef.current;
    if (!node) {
      return;
    }
    const syncHeight = () => {
      const nextHeight = Math.round(node.getBoundingClientRect().height);
      setFeedbackMaxHeight((prev) => (prev === nextHeight ? prev : nextHeight));
    };
    syncHeight();

    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(syncHeight);
      observer.observe(node);
      return () => observer.disconnect();
    }

    window.addEventListener("resize", syncHeight);
    return () => window.removeEventListener("resize", syncHeight);
  }, [currentQuestionIndex, isFinished, testData.id]);

  const currentQuestion = testData.questions[currentQuestionIndex];
  const currentAnswer = answers.get(currentQuestion.id);

  const answeredQuestionIndices = useMemo(() => {
    const indices = new Set<number>();
    testData.questions.forEach((q, index) => {
      const answer = answers.get(q.id);
      const isAnswered =
        q.type === "open"
          ? Boolean(answer?.openAnswer?.trim())
          : Boolean(answer?.selectedOptionIds?.length);
      if (isAnswered) {
        indices.add(index);
      }
    });
    return indices;
  }, [answers, testData.questions]);

  const correctAnswersCount = useMemo(() => {
    // For teacher view, we show how many students answered correctly
    if (viewMode === "teacher") {
      // Simulate that 10 out of 20 students answered correctly
      return 10;
    }

    // For student view, we show how many questions they answered correctly
    let count = 0;
    answers.forEach((answer) => {
      if (answer.isCorrect) count++;
    });
    return count;
  }, [answers, viewMode]);

  const totalCount = useMemo(() => {
    if (viewMode === "teacher") {
      return 20; // Total students
    }
    return testData.questions.length; // Total questions
  }, [viewMode, testData.questions.length]);

  const handleOptionSelect = (optionId: string) => {
    // Teacher view is read-only
    if (viewMode === "teacher") return;
    if (isFinished) return;

    if (currentQuestion.type === "open") {
      return;
    }
    setAnswers((prev) => {
      const updated = new Map(prev);
      const previous = updated.get(currentQuestion.id);
      const currentSelected = previous?.selectedOptionIds ?? [];
      const nextSelected =
        currentQuestion.type === "multiple_choice"
          ? currentSelected.includes(optionId)
            ? currentSelected.filter((id) => id !== optionId)
            : [...currentSelected, optionId]
          : [optionId];
      updated.set(currentQuestion.id, {
        questionId: currentQuestion.id,
        selectedOptionIds: nextSelected,
        isCorrect: isChoiceCorrect(currentQuestion, nextSelected),
      });
      return updated;
    });
  };

  const handleOpenAnswerChange = (value: string) => {
    if (viewMode === "teacher") return;
    if (isFinished) return;
    if (currentQuestion.type !== "open") return;

    setAnswers((prev) => {
      const updated = new Map(prev);
      updated.set(currentQuestion.id, {
        questionId: currentQuestion.id,
        selectedOptionIds: [],
        openAnswer: value,
        isCorrect: false,
      });
      return updated;
    });
  };

  const handleQuestionSelect = (index: number) => {
    setCurrentQuestionIndex(index);
  };

  const totalQuestions = testData.questions.length;
  const answeredCount = answeredQuestionIndices.size;
  const isReadyToFinish =
    viewMode === "student" ? answeredCount === totalQuestions : false;
  const progressCount =
    viewMode === "student" && !isFinished ? answeredCount : correctAnswersCount;
  const progressLabel =
    viewMode === "teacher"
      ? "учнів відповіли\nправильно"
      : isFinished
        ? "правильних\nвідповідей"
        : "відповідей\nобрано";

  const resultMap = useMemo(() => {
    const map = new Map<number, "correct" | "incorrect" | "partial">();
    if (viewMode !== "student" || !isFinished) {
      return map;
    }
    testData.questions.forEach((question, index) => {
      const status = getQuestionStatus(question, answers.get(question.id));
      if (status !== "neutral") {
        map.set(index, status);
      }
    });
    return map;
  }, [answers, isFinished, testData.questions, viewMode]);

  const handleFinish = async () => {
    if (isFinished || !isReadyToFinish || isSubmitting) {
      return;
    }
    setIsSubmitting(true);
    let updatedAnswers = new Map(answers);

    if (viewMode === "student" && onEvaluateOpen) {
      const openQuestions = testData.questions.filter(
        (question) => question.type === "open"
      );
      const evaluations = await Promise.all(
        openQuestions.map(async (question) => {
          const answer = updatedAnswers.get(question.id);
          const openAnswer = answer?.openAnswer?.trim();
          if (!openAnswer) {
            return null;
          }
          try {
            const result = await onEvaluateOpen({
              question,
              answer: openAnswer,
            });
            return { questionId: question.id, result };
          } catch (error) {
            console.error(error);
            return {
              questionId: question.id,
              result: { correct: false, feedback: "Не вдалося перевірити відповідь." },
            };
          }
        })
      );

      evaluations.forEach((evaluation) => {
        if (!evaluation) return;
        const existing = updatedAnswers.get(evaluation.questionId);
        if (!existing) return;
        updatedAnswers.set(evaluation.questionId, {
          ...existing,
          isCorrect: evaluation.result.correct,
          feedback: evaluation.result.feedback,
        });
      });
    }

    const correctAnswers = Array.from(updatedAnswers.values()).filter(
      (answer) => answer.isCorrect
    ).length;

    setAnswers(updatedAnswers);
    setIsFinished(true);
    setIsSubmitting(false);
    await onFinish?.({
      correctAnswers,
      totalQuestions: testData.questions.length,
      answers: Array.from(updatedAnswers.values()),
    });
  };

  return (
    <div className="space-y-6">
      {/* Title + Actions */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <h1 className="text-2xl font-bold text-white">{testData.title}</h1>
      </div>

      {/* Navigation */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <TestNavigation
          totalQuestions={testData.questions.length}
          currentQuestionIndex={currentQuestionIndex}
          answeredQuestions={answeredQuestionIndices}
          onQuestionSelect={handleQuestionSelect}
          showResult={viewMode === "student" && isFinished}
          resultMap={resultMap}
        />
        {viewMode === "student" && !isFinished && (
          <button
            type="button"
            onClick={isFinished ? onExit : handleFinish}
            disabled={(!isReadyToFinish && !isFinished) || isSubmitting}
            className={`w-full rounded-2xl px-6 py-3 text-sm font-semibold text-white transition-all lg:w-[280px] ${
              (isReadyToFinish || isFinished) && !isSubmitting
                ? "cursor-pointer bg-[#E63C3C] hover:-translate-y-0.5 hover:shadow-lg"
                : "cursor-not-allowed bg-[#E63C3C]/60"
            }`}
          >
            {isSubmitting ? "Перевіряємо..." : "Завершити тест"}
          </button>
        )}
        {viewMode === "student" && isFinished && (
          <div className="w-full rounded-2xl bg-[#6FDB9B] px-6 py-3 text-center text-sm font-semibold text-white lg:w-[280px]">
            {totalCount > 0
              ? `${Math.round((correctAnswersCount / totalCount) * 100)}% правильних відповідей`
              : "0% правильних відповідей"}
          </div>
        )}
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {/* Left column - Question and Explanation */}
        <div ref={leftColumnRef} className="flex flex-col gap-6">
          <TestQuestionCard
            question={currentQuestion}
            selectedOptionIds={currentAnswer?.selectedOptionIds ?? []}
            openAnswer={currentAnswer?.openAnswer ?? ""}
            onOptionSelect={handleOptionSelect}
            onOpenAnswerChange={handleOpenAnswerChange}
            showResult={viewMode === "teacher" ? !!currentAnswer : isFinished}
          />

          {/* Show explanation after answering */}
          {currentAnswer &&
            currentQuestion.explanation &&
            viewMode === "student" &&
            isFinished && (
              <TestExplanation explanation={currentQuestion.explanation} />
            )}

          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => handleQuestionSelect(currentQuestionIndex - 1)}
              disabled={currentQuestionIndex === 0}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                currentQuestionIndex === 0
                  ? "cursor-not-allowed bg-white/60 text-slate-300"
                  : "cursor-pointer bg-white text-[#1E73F7] hover:-translate-y-0.5 hover:shadow-lg"
              }`}
            >
              ← Попереднє
            </button>
            <button
              type="button"
              onClick={() => handleQuestionSelect(currentQuestionIndex + 1)}
              disabled={currentQuestionIndex >= testData.questions.length - 1}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                currentQuestionIndex >= testData.questions.length - 1
                  ? "cursor-not-allowed bg-white/60 text-slate-300"
                  : "cursor-pointer bg-white text-[#1E73F7] hover:-translate-y-0.5 hover:shadow-lg"
              }`}
            >
              Наступне →
            </button>
          </div>
        </div>

        {/* Right column - Progress/Explanation */}
        <div
          className="flex h-full flex-col gap-4 min-h-0 overflow-hidden"
          style={feedbackMaxHeight ? { height: feedbackMaxHeight } : undefined}
        >
          {viewMode === "teacher" ? (
            currentQuestion.explanation ? (
              <TestExplanation explanation={currentQuestion.explanation} />
            ) : (
              <div className="rounded-2xl border-2 border-white/60 bg-white/80 p-6 text-sm text-slate-600">
                Пояснення для цього питання ще не додано.
              </div>
            )
          ) : (
            <>
              {isFinished && feedbackNode && (
                <div className="h-full min-h-0 overflow-hidden">
                  {feedbackNode}
                </div>
              )}
              {showStatistics && statistics && (
                <TestStatisticsCard statistics={statistics} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestContainer;
