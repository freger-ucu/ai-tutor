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

  // Handle keyboard navigation between questions (Enter, Arrow keys)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't navigate if user is typing in a textarea or input
      const activeElement = document.activeElement;
      if (activeElement?.tagName === "TEXTAREA" || activeElement?.tagName === "INPUT") {
        return;
      }

      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        // Navigate to next question
        if (currentQuestionIndex < testData.questions.length - 1) {
          setCurrentQuestionIndex(currentQuestionIndex + 1);
        }
      } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        if (currentQuestionIndex < testData.questions.length - 1) {
          setCurrentQuestionIndex(currentQuestionIndex + 1);
        }
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        if (currentQuestionIndex > 0) {
          setCurrentQuestionIndex(currentQuestionIndex - 1);
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
        <h1 className="text-xl font-bold text-white mb-2">{testData.title}</h1>
      )}

      {/* Navigation with prev/next buttons */}
      <div className="flex items-center justify-between gap-3 mb-3 overflow-visible">
        <div className="flex items-center gap-3">
          <TestNavigation
            totalQuestions={testData.questions.length}
            currentQuestionIndex={currentQuestionIndex}
            answeredQuestions={answeredQuestionIndices}
            onQuestionSelect={handleQuestionSelect}
            showResult={viewMode === "student" && isFinished}
            resultMap={resultMap}
            viewMode={viewMode}
          />
          {viewMode === "student" && isFinished && (
            <div className="rounded-full bg-[#6FDB9B] px-4 py-2 text-center text-xs font-semibold text-white">
              {totalQuestions > 0
                ? `${Math.round((correctAnswersCount / totalQuestions) * 100)}% правильних`
                : "0%"}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => handleQuestionSelect(currentQuestionIndex - 1)}
            disabled={currentQuestionIndex === 0}
            className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-all ${
              currentQuestionIndex === 0
                ? "cursor-not-allowed bg-white/40 text-white/60"
                : "cursor-pointer bg-white text-[#1E73F7] hover:-translate-y-0.5 hover:shadow-lg"
            }`}
          >
            ← Попереднє
          </button>
          <button
            type="button"
            onClick={() => handleQuestionSelect(currentQuestionIndex + 1)}
            disabled={currentQuestionIndex >= testData.questions.length - 1}
            className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-all ${
              currentQuestionIndex >= testData.questions.length - 1
                ? "cursor-not-allowed bg-white/40 text-white/60"
                : "cursor-pointer bg-white text-[#1E73F7] hover:-translate-y-0.5 hover:shadow-lg"
            }`}
          >
            Наступне →
          </button>
        </div>
      </div>

      {/* Question card with feedback on the side - flex to fill available space */}
      <div className="flex flex-col md:flex-row gap-3 md:gap-4 flex-1 min-h-0">
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

          {/* Mobile: Feedback below question card */}
          {feedbackNode && viewMode === "student" && isFinished && (
            <div className="mt-3 md:hidden overflow-y-auto student-scrollbar max-h-48">
              {feedbackNode}
            </div>
          )}
        </div>

        {/* Desktop: Feedback on the side - shown after test completion for student */}
        {feedbackNode && viewMode === "student" && isFinished && (
          <div className="hidden md:block w-72 shrink-0 overflow-y-auto student-scrollbar">
            {feedbackNode}
          </div>
        )}
      </div>

      {/* Statistics card (if enabled) */}
      {showStatistics && statistics && (
        <TestStatisticsCard statistics={statistics} />
      )}

      {/* Fixed finish button at bottom right */}
      {viewMode === "student" && !isFinished && (
        <button
          type="button"
          onClick={handleFinish}
          disabled={isSubmitting}
          className={`fixed bottom-6 right-6 z-50 rounded-full border px-6 py-3 text-sm font-semibold text-white transition ${
            isSubmitting
              ? "cursor-not-allowed border-red-400 bg-red-400"
              : "cursor-pointer border-red-500 bg-red-500 hover:border-red-600 hover:bg-red-600"
          }`}
        >
          {isSubmitting ? "Перевіряємо..." : "Завершити тест"}
        </button>
      )}
    </div>
  );
};

export default TestContainer;
