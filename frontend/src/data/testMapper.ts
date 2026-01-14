import type { TestData, TestQuestion, TestOption, DifficultyLevel } from "../types/testTypes";
import type { QuestionType } from "../types/testTypes";

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
    return [];
  }
  return options.map((option, index) => ({
    id: `opt-${index + 1}`,
    text: option.answer,
  }));
};

const toCorrectOptionIds = (
  options: GeneratedAnswerOption[] | null,
  mapped: TestOption[]
) => {
  if (!options || options.length === 0) {
    return [];
  }
  const correctIndices = options
    .map((option, index) => (option.correct ? index : -1))
    .filter((index) => index >= 0);
  if (!correctIndices.length) {
    return [];
  }
  return correctIndices
    .map((index) => mapped[index]?.id)
    .filter((value): value is string => Boolean(value));
};

export const mapGeneratedQuestions = (questions: GeneratedQuestion[]): TestQuestion[] => {
  return questions.map((question, index) => {
    const options = toOptionsFromGenerated(question.answer_options);
    const type = question.type as QuestionType;
    return {
      id: `gen-${index + 1}`,
      number: index + 1,
      text: question.question,
      options,
      correctOptionIds: toCorrectOptionIds(question.answer_options, options),
      difficulty: toDifficulty(question.difficulty),
      explanation: question.explanation,
      type,
      topic: question.topic,
      subtopics: question.subtopics ?? [],
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
