export type DifficultyLevel = "easy" | "medium" | "hard";

export interface TestOption {
    id: string;
    text: string;
}

export interface TestQuestion {
    id: string;
    number: number;
    text: string;
    options: TestOption[];
    correctOptionId: string;
    difficulty: DifficultyLevel;
    explanation?: string;
}

export interface TestData {
    id: string;
    title: string;
    subject: string;
    className: string;
    topicName: string;
    questions: TestQuestion[];
}

export interface TestAnswer {
    questionId: string;
    selectedOptionId: string | null;
    isCorrect: boolean;
}

export interface TestState {
    currentQuestionIndex: number;
    answers: TestAnswer[];
    isCompleted: boolean;
}

export interface TestStatistics {
    totalStudents: number;
    completedStudents: number;
    averageScore: number;
    description: string;
}
