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
}

const TestContainer = ({
  testData,
  statistics,
  showStatistics = false,
  viewMode = "student",
}: TestContainerProps) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Map<string, TestAnswer>>(new Map());

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
    if (currentAnswer) return; // Already answered

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
            showResult={!!currentAnswer}
          />

          {/* Show explanation after answering */}
          {currentAnswer && currentQuestion.explanation && (
            <TestExplanation explanation={currentQuestion.explanation} />
          )}
        </div>

        {/* Right column - Progress and Statistics */}
        <div className="flex flex-col gap-4">
          <TestProgressCard
            correctAnswers={correctAnswersCount}
            totalQuestions={totalCount}
            label={viewMode === "teacher" ? "учнів відповіли\nправильно" : "правильних\nвідповідей"}
          />

          {showStatistics && statistics && (
            <TestStatisticsCard statistics={statistics} />
          )}
        </div>
      </div>
    </div>
  );
};

export default TestContainer;

