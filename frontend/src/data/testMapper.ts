import type { TestData, TestQuestion, TestOption, DifficultyLevel } from "../types/testTypes";

interface GeneratedAnswerOption {
  answer: string;
  correct: boolean;
}

interface GeneratedQuestion {
  question: string;
  type: "single_choice" | "multiple_choice" | "open";
  difficulty: "easy" | "medium" | "difficult";
  answer_options: GeneratedAnswerOption[] | null;
  explanation: string;
  topic: string;
  subtopics: string[];
}

const toDifficulty = (difficulty: GeneratedQuestion["difficulty"]): DifficultyLevel => {
  if (difficulty === "difficult") {
    return "hard";
  }
  return difficulty;
};

const toOptionsFromGenerated = (options: GeneratedAnswerOption[] | null): TestOption[] => {
  if (!options || options.length === 0) {
    return [
      {
        id: "open",
        text: "Відкрите питання",
      },
    ];
  }
  return options.map((option, index) => ({
    id: `opt-${index + 1}`,
    text: option.answer,
  }));
};

const toCorrectOptionId = (
  options: GeneratedAnswerOption[] | null,
  mapped: TestOption[]
) => {
  if (!options || options.length === 0) {
    return mapped[0]?.id ?? "open";
  }
  const correctIndex = options.findIndex((option) => option.correct);
  if (correctIndex === -1) {
    return mapped[0]?.id ?? "opt-1";
  }
  return mapped[correctIndex]?.id ?? mapped[0]?.id ?? "opt-1";
};

export const mapGeneratedQuestions = (questions: GeneratedQuestion[]): TestQuestion[] => {
  return questions.map((question, index) => {
    const options = toOptionsFromGenerated(question.answer_options);
    return {
      id: `gen-${index + 1}`,
      number: index + 1,
      text: question.question,
      options,
      correctOptionId: toCorrectOptionId(question.answer_options, options),
      difficulty: toDifficulty(question.difficulty),
      explanation: question.explanation,
    };
  });
};

export const withGeneratedQuestions = (base: TestData, questions?: unknown) => {
  if (!questions || !Array.isArray(questions)) {
    return base;
  }
  const mapped = mapGeneratedQuestions(questions as GeneratedQuestion[]);
  if (!mapped.length) {
    return base;
  }
  return {
    ...base,
    questions: mapped,
  };
};
