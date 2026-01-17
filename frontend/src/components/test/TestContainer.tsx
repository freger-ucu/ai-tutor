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
  /** Feedback node shown on the side after test completion */
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
  const containerRef = useRef<HTMLDivElement | null>(null);

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

  // Handle Enter key navigation between questions
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        // Don't navigate if user is typing in a textarea
        const activeElement = document.activeElement;
        if (activeElement?.tagName === "TEXTAREA") {
          return;
        }
        e.preventDefault();
        // Navigate to next question
        if (currentQuestionIndex < testData.questions.length - 1) {
          setCurrentQuestionIndex(currentQuestionIndex + 1);
        }
      }
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener("keydown", handleKeyDown);
      return () => container.removeEventListener("keydown", handleKeyDown);
    }
  }, [currentQuestionIndex, testData.questions.length]);

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
  // Student can finish test at any time - unanswered questions count as incorrect
  const isReadyToFinish = viewMode === "student";

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
    if (isFinished || isSubmitting) {
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
    <div ref={containerRef} tabIndex={-1} className="flex flex-col outline-none h-full">
      {/* Title - only shown for students */}
      {viewMode === "student" && (
        <h1 className="hidden lg:block text-lg font-bold text-white mb-2 lg:text-xl">
          {testData.title}
        </h1>
      )}

      {/* Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3 overflow-visible">
        <div className="hidden lg:block">
          <TestNavigation
            totalQuestions={testData.questions.length}
            currentQuestionIndex={currentQuestionIndex}
            answeredQuestions={answeredQuestionIndices}
            onQuestionSelect={handleQuestionSelect}
            showResult={viewMode === "student" && isFinished}
            resultMap={resultMap}
          />
        </div>
        <div className="flex w-full items-center justify-between rounded-xl bg-white/10 px-3 py-2 text-xs font-semibold text-white lg:hidden">
          <span>Питання {currentQuestionIndex + 1} з {totalQuestions}</span>
          <span>{answeredCount}/{totalQuestions} відповіли</span>
        </div>
        {viewMode === "student" && !isFinished && (
          <button
            type="button"
            onClick={handleFinish}
            disabled={isSubmitting}
            className={`hidden w-full rounded-xl px-4 py-2 text-xs font-semibold text-white transition-all lg:inline-flex lg:w-[220px] ${
              isSubmitting
                ? "cursor-not-allowed bg-[#E63C3C]/60"
                : "cursor-pointer bg-[#E63C3C] hover:-translate-y-0.5 hover:shadow-lg"
            }`}
          >
            {isSubmitting ? "Перевіряємо..." : "Завершити тест"}
          </button>
        )}
        {viewMode === "student" && isFinished && (
          <div className="hidden w-full rounded-xl bg-[#6FDB9B] px-4 py-2 text-center text-xs font-semibold text-white lg:block lg:w-[220px]">
            {totalQuestions > 0
              ? `${Math.round((correctAnswersCount / totalQuestions) * 100)}% правильних відповідей`
              : "0% правильних відповідей"}
          </div>
        )}
      </div>

      {/* Question card with feedback on the side - flex to fill available space */}
      <div className="flex gap-4 flex-1 min-h-0">
        <div className="flex-1 min-w-0 flex flex-col">
          {/* Scrollable question area */}
          <div className="flex-1 min-h-0 overflow-y-auto student-scrollbar">
            <TestQuestionCard
              key={currentQuestion.id}
              question={currentQuestion}
              selectedOptionIds={currentAnswer?.selectedOptionIds ?? []}
              openAnswer={currentAnswer?.openAnswer ?? ""}
              onOptionSelect={handleOptionSelect}
              onOpenAnswerChange={handleOpenAnswerChange}
              showResult={viewMode === "student" && isFinished}
              viewMode={viewMode}
              showExplanation={viewMode === "teacher" || (viewMode === "student" && isFinished)}
            />
          </div>

          {/* Navigation buttons - attached to bottom of question card */}
          <div className="flex flex-col gap-3 pt-3 shrink-0 lg:flex-row lg:items-center lg:justify-between">
            <button
              type="button"
              onClick={() => handleQuestionSelect(currentQuestionIndex - 1)}
              disabled={currentQuestionIndex === 0}
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-all duration-300 ease-in-out ${
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
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-all duration-300 ease-in-out ${
                currentQuestionIndex >= testData.questions.length - 1
                  ? "cursor-not-allowed bg-white/60 text-slate-300"
                  : "cursor-pointer bg-white text-[#1E73F7] hover:-translate-y-0.5 hover:shadow-lg"
              }`}
            >
              Наступне →
            </button>
            {viewMode === "student" && !isFinished && (
              <button
                type="button"
                onClick={handleFinish}
                disabled={isSubmitting}
                className={`w-full rounded-xl px-4 py-2 text-xs font-semibold text-white transition-all lg:hidden ${
                  isSubmitting
                    ? "cursor-not-allowed bg-[#E63C3C]/60"
                    : "cursor-pointer bg-[#E63C3C]"
                }`}
              >
                {isSubmitting ? "Перевіряємо..." : "Завершити тест"}
              </button>
            )}
            {viewMode === "student" && isFinished && (
              <div className="w-full rounded-xl bg-[#6FDB9B] px-4 py-2 text-center text-xs font-semibold text-white lg:hidden">
                {totalQuestions > 0
                  ? `${Math.round((correctAnswersCount / totalQuestions) * 100)}% правильних відповідей`
                  : "0% правильних відповідей"}
              </div>
            )}
          </div>
        </div>

        {/* Feedback on the side - shown after test completion for student */}
        {feedbackNode && viewMode === "student" && isFinished && (
          <div className="w-72 shrink-0 overflow-y-auto student-scrollbar">
            {feedbackNode}
          </div>
        )}
      </div>

      {/* Statistics card (if enabled) */}
      {showStatistics && statistics && (
        <TestStatisticsCard statistics={statistics} />
      )}
    </div>
  );
};

export default TestContainer;
