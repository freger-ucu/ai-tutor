/**
 * Fallback content for when the LLM API is unavailable.
 * This allows the UI to be populated with placeholder data
 * for testing layout and flow.
 */

import type { GeneratedNotesResponse, GeneratedQuestion } from "../api/teacher";

/**
 * Logs a warning to the console when fallback data is being used.
 */
export const logFallbackWarning = (type: "notes" | "test", context?: string) => {
  console.warn(
    `⚠️ [FALLBACK] Using fallback ${type} data${context ? ` for: ${context}` : ""}. ` +
    `The LLM API is unavailable. This is placeholder content for UI testing.`
  );
};

/**
 * Default lesson notes content used when API fails.
 * Contains structured educational content with markdown formatting.
 */
export const DEFAULT_LESSON_NOTES: Omit<GeneratedNotesResponse, "title"> = {
  contents: `## Вступ

Ця тема є важливою частиною навчальної програми. У цьому конспекті ми розглянемо основні поняття та принципи.

## Основні поняття

### Визначення

**Ключове поняття** — це фундаментальна ідея, яка лежить в основі розуміння теми. Воно допомагає учням структурувати знання та встановлювати зв'язки між різними аспектами предмета.

### Характеристики

1. **Перша характеристика** — опис першої важливої властивості
2. **Друга характеристика** — опис другої важливої властивості  
3. **Третя характеристика** — опис третьої важливої властивості

## Практичне застосування

Розглянемо приклад застосування цих знань:

> **Приклад:** Якщо ми маємо ситуацію А, то застосовуємо правило Б для отримання результату В.

### Формула (якщо застосовно)

$$E = mc^2$$

Де:
- $E$ — енергія
- $m$ — маса
- $c$ — швидкість світла

## Важливі моменти для запам'ятовування

- ✅ Перший ключовий момент
- ✅ Другий ключовий момент  
- ✅ Третій ключовий момент
- ⚠️ Типова помилка, якої слід уникати

## Висновки

Підсумовуючи, основні ідеї цієї теми включають розуміння базових понять та їх практичне застосування. Для глибшого засвоєння матеріалу рекомендується виконати практичні вправи.

---

*Це демонстраційний контент. Замініть на реальний матеріал після відновлення з'єднання з API.*`,

  teacher_notes: `### Нотатки для вчителя

**Методичні рекомендації:**
- Почніть урок з короткого повторення попереднього матеріалу
- Використовуйте візуальні приклади для пояснення абстрактних понять
- Залучайте учнів до обговорення через запитання

**Типові труднощі учнів:**
- Плутають поняття А з поняттям Б
- Забувають враховувати умову В при розв'язанні задач

**Додаткові ресурси:**
- Підручник, розділ 5, с. 45-52
- Відеоматеріали на освітній платформі

**Оцінювання:**
- Перевірте розуміння через короткий тест (5-7 хвилин)
- Домашнє завдання: вправи 1-5, с. 53

---

*Це демонстраційний контент для тестування UI.*`,

  sources: [
    { name: "Демо підручник", pages: "1-10" },
    { name: "Методичний посібник", pages: "15-20" },
  ],
};

/**
 * Default test questions used when API fails.
 * Contains a variety of question types and difficulties.
 */
export const DEFAULT_TEST_QUESTIONS: GeneratedQuestion[] = [
  {
    question: "Яке з наведених тверджень найкраще описує основне поняття цієї теми?",
    type: "single_choice",
    difficulty: "easy",
    answer_options: [
      { answer: "Правильне визначення основного поняття", correct: true },
      { answer: "Неповне визначення, що пропускає важливий аспект", correct: false },
      { answer: "Визначення суміжного, але іншого поняття", correct: false },
      { answer: "Неправильне твердження з типовою помилкою", correct: false },
    ],
    explanation: "Правильна відповідь найточніше відображає суть поняття, враховуючи всі ключові характеристики. Інші варіанти містять типові помилки або неточності.",
    topic: "Основні поняття",
    subtopics: ["Визначення", "Характеристики"],
    focus: "Розуміння базових понять",
  },
  {
    question: "Виберіть усі правильні характеристики досліджуваного явища:",
    type: "multiple_choice",
    difficulty: "medium",
    answer_options: [
      { answer: "Перша правильна характеристика", correct: true },
      { answer: "Друга правильна характеристика", correct: true },
      { answer: "Неправильна характеристика (типова помилка)", correct: false },
      { answer: "Третя правильна характеристика", correct: true },
      { answer: "Характеристика іншого явища", correct: false },
    ],
    explanation: "Правильними є характеристики 1, 2 та 4, які безпосередньо стосуються досліджуваного явища. Варіант 3 містить типову помилку, а варіант 5 описує інше явище.",
    topic: "Властивості та характеристики",
    subtopics: ["Аналіз", "Порівняння"],
    focus: "Уміння розрізняти характеристики",
  },
  {
    question: "Розв'яжіть задачу: Якщо початкове значення дорівнює 100, а зміна становить 25%, яким буде кінцеве значення?",
    type: "single_choice",
    difficulty: "medium",
    answer_options: [
      { answer: "125", correct: true },
      { answer: "75", correct: false },
      { answer: "25", correct: false },
      { answer: "100", correct: false },
    ],
    explanation: "100 + (100 × 0.25) = 100 + 25 = 125. Збільшення на 25% означає додавання чверті від початкового значення.",
    topic: "Практичні обчислення",
    subtopics: ["Відсотки", "Розрахунки"],
    focus: "Застосування формул",
  },
  {
    question: "Поясніть своїми словами, чому важливо розуміти цю тему для подальшого навчання.",
    type: "open",
    difficulty: "difficult",
    answer_options: null,
    explanation: "Очікувана відповідь повинна містити: 1) зв'язок з іншими темами курсу; 2) практичне застосування знань; 3) роль у формуванні критичного мислення. Оцінюйте повноту аргументації та логічність викладу.",
    topic: "Міжпредметні зв'язки",
    subtopics: ["Синтез знань", "Критичне мислення"],
    focus: "Глибоке розуміння матеріалу",
  },
  {
    question: "Встановіть правильну послідовність кроків для розв'язання типової задачі:",
    type: "single_choice",
    difficulty: "medium",
    answer_options: [
      { answer: "1) Аналіз умови → 2) Вибір методу → 3) Виконання → 4) Перевірка", correct: true },
      { answer: "1) Виконання → 2) Аналіз умови → 3) Перевірка → 4) Вибір методу", correct: false },
      { answer: "1) Вибір методу → 2) Виконання → 3) Аналіз умови → 4) Перевірка", correct: false },
      { answer: "1) Перевірка → 2) Виконання → 3) Вибір методу → 4) Аналіз умови", correct: false },
    ],
    explanation: "Правильний алгоритм розв'язання починається з аналізу умови, потім обирається метод, виконується розв'язання і завершується перевіркою результату.",
    topic: "Алгоритми розв'язання",
    subtopics: ["Послідовність дій", "Методологія"],
    focus: "Процедурні знання",
  },
  {
    question: "Який з графіків правильно ілюструє залежність між змінними X та Y?",
    type: "single_choice",
    difficulty: "difficult",
    answer_options: [
      { answer: "Графік А: пряма пропорційна залежність", correct: true },
      { answer: "Графік Б: обернена пропорційна залежність", correct: false },
      { answer: "Графік В: експоненційне зростання", correct: false },
      { answer: "Графік Г: періодична функція", correct: false },
    ],
    explanation: "Згідно з теоретичними положеннями, змінні X та Y пов'язані прямою пропорційною залежністю, що відображається лінійним графіком через початок координат.",
    topic: "Графічне представлення",
    subtopics: ["Аналіз графіків", "Інтерпретація даних"],
    focus: "Візуалізація залежностей",
  },
];

/**
 * Builds a complete fallback notes response with a dynamic title.
 */
export const buildFallbackNotes = (
  topicDefinition: string,
  topicName: string
): GeneratedNotesResponse => {
  const fallbackTitle = topicDefinition.trim() || topicName || "Конспект уроку";
  logFallbackWarning("notes", fallbackTitle);
  
  return {
    title: `${fallbackTitle}`,
    ...DEFAULT_LESSON_NOTES,
  };
};

/**
 * Builds a complete fallback test response with a dynamic title.
 * This is an enhanced version with more detailed questions.
 */
export const buildFallbackTest = (
  topicDefinition: string,
  topicName: string
): { title: string; questions: GeneratedQuestion[] } => {
  const fallbackTitle = topicDefinition.trim() || topicName || "Тест";
  logFallbackWarning("test", fallbackTitle);
  
  return {
    title: `Тест. ${fallbackTitle}`,
    questions: DEFAULT_TEST_QUESTIONS.map((q) => ({
      ...q,
      topic: q.topic || fallbackTitle,
    })),
  };
};
