export type DifficultyLevel = "easy" | "medium" | "hard";
export type QuestionType = "single_choice" | "multiple_choice" | "open";

export interface TestOption {
    id: string;
    text: string;
}

export interface TestQuestion {
    id: string;
    number: number;
    text: string;
    options: TestOption[];
    correctOptionIds: string[];
    difficulty: DifficultyLevel;
    explanation?: string;
    type: QuestionType;
    topic?: string;
    subtopics?: string[];
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
    selectedOptionIds: string[];
    openAnswer?: string;
    isCorrect: boolean;
    feedback?: string;
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
