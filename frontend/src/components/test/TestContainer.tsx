import { useState, useMemo, useEffect } from "react";
import type { TestData, TestStatistics, TestAnswer } from "../../types/testTypes";
import TestNavigation from "./TestNavigation";
import TestQuestionCard from "./TestQuestionCard";
import TestProgressCard from "./TestProgressCard";
import TestStatisticsCard from "./TestStatisticsCard";
import TestExplanation from "./TestExplanation";

interface TestContainerProps {
  testData: TestData;
  statistics?: TestStatistics;
  showStatistics?: boolean;
  /** 'teacher' shows pre-answered test results, 'student' lets user answer */
  viewMode?: "teacher" | "student";
  onFinish?: (result: { correctAnswers: number; totalQuestions: number }) => void;
}

const TestContainer = ({
  testData,
  statistics,
  showStatistics = false,
  viewMode = "student",
  onFinish,
}: TestContainerProps) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Map<string, TestAnswer>>(new Map());
  const [isFinished, setIsFinished] = useState(false);

  // Pre-populate answers for teacher view (simulating that students have already answered)
  useEffect(() => {
    if (viewMode === "teacher") {
      const preFilledAnswers = new Map<string, TestAnswer>();
      testData.questions.forEach((question) => {
        // Simulate 50% correct answers for demo
        const isCorrect = Math.random() > 0.5;
        preFilledAnswers.set(question.id, {
          questionId: question.id,
          selectedOptionId: isCorrect 
            ? question.correctOptionId 
            : question.options.find(o => o.id !== question.correctOptionId)?.id ?? question.options[0].id,
          isCorrect,
        });
      });
      setAnswers(preFilledAnswers);
    }
  }, [viewMode, testData.questions]);

  useEffect(() => {
    if (viewMode === "student") {
      setAnswers(new Map());
      setIsFinished(false);
    }
  }, [viewMode, testData.id]);

  const currentQuestion = testData.questions[currentQuestionIndex];
  const currentAnswer = answers.get(currentQuestion.id);

  const answeredQuestionIndices = useMemo(() => {
    const indices = new Set<number>();
    testData.questions.forEach((q, index) => {
      if (answers.has(q.id)) {
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

    const isCorrect = optionId === currentQuestion.correctOptionId;
    const newAnswer: TestAnswer = {
      questionId: currentQuestion.id,
      selectedOptionId: optionId,
      isCorrect,
    };

    setAnswers((prev) => {
      const updated = new Map(prev);
      updated.set(currentQuestion.id, newAnswer);
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

  return (
    <div className="space-y-6">
      {/* Title */}
      <h1 className="text-2xl font-bold text-white">{testData.title}</h1>

      {/* Navigation */}
      <TestNavigation
        totalQuestions={testData.questions.length}
        currentQuestionIndex={currentQuestionIndex}
        answeredQuestions={answeredQuestionIndices}
        onQuestionSelect={handleQuestionSelect}
      />

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {/* Left column - Question and Explanation */}
        <div className="flex flex-col gap-6">
          <TestQuestionCard
            question={currentQuestion}
            selectedOptionId={currentAnswer?.selectedOptionId ?? null}
            onOptionSelect={handleOptionSelect}
            showResult={viewMode === "teacher" ? !!currentAnswer : isFinished}
          />

          {/* Show explanation after answering */}
          {currentAnswer &&
            currentQuestion.explanation &&
            (viewMode === "teacher" || isFinished) && (
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

        {/* Right column - Progress and Statistics */}
        <div className="flex flex-col gap-4">
          <TestProgressCard
            correctAnswers={progressCount}
            totalQuestions={totalCount}
            label={progressLabel}
          />

          {showStatistics && statistics && (
            <TestStatisticsCard statistics={statistics} />
          )}

          {viewMode === "student" && (
            <button
              type="button"
              onClick={() => {
                if (!isFinished) {
                  onFinish?.({
                    correctAnswers: correctAnswersCount,
                    totalQuestions: testData.questions.length,
                  });
                  setIsFinished(true);
                }
              }}
              disabled={!isReadyToFinish || isFinished}
              className={`rounded-2xl px-4 py-3 text-sm font-semibold transition-all ${
                isReadyToFinish && !isFinished
                  ? "cursor-pointer bg-white text-[#1E73F7] hover:-translate-y-0.5 hover:shadow-lg"
                  : "cursor-not-allowed bg-white/60 text-slate-300"
              }`}
            >
              Завершити тест
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestContainer;
