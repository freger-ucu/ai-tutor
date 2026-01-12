import type { TestData, TestStatistics } from "../types/testTypes";

export const mockTestData: TestData = {
    id: "test-1",
    title: "Тест. Іменник",
    subject: "Українська мова",
    className: "8-А",
    topicName: "Іменник",
    questions: [
        {
            id: "q1",
            number: 1,
            text: "Яку синтаксичну роль найчастіше виконує іменник?",
            options: [
                { id: "q1-a", text: "Присудок" },
                { id: "q1-b", text: "Додаток або підмет" },
                { id: "q1-c", text: "Означення" },
                { id: "q1-d", text: "Обставина" },
            ],
            correctOptionId: "q1-b",
            difficulty: "medium",
            explanation: `Підмет — це головний член речення, який називає того, хто або що виконує дію, і зазвичай відповідає на питання хто? що?.
→ Книга — іменник, підмет.

Додаток — це другорядний член речення, який називає предмет, на який спрямована дія, і відповідає на питання непрямих відмінків.
→ Книгу — іменник, додаток.`,
        },
        {
            id: "q2",
            number: 2,
            text: "Яка ознака НЕ є морфологічною ознакою іменника?",
            options: [
                { id: "q2-a", text: "Рід" },
                { id: "q2-b", text: "Число" },
                { id: "q2-c", text: "Час" },
                { id: "q2-d", text: "Відмінок" },
            ],
            correctOptionId: "q2-c",
            difficulty: "easy",
            explanation: "Час — це морфологічна ознака дієслова, а не іменника. Іменники характеризуються родом, числом, відмінком і відміною.",
        },
        {
            id: "q3",
            number: 3,
            text: "Скільки відмін має іменник в українській мові?",
            options: [
                { id: "q3-a", text: "Три" },
                { id: "q3-b", text: "Чотири" },
                { id: "q3-c", text: "П'ять" },
                { id: "q3-d", text: "Шість" },
            ],
            correctOptionId: "q3-b",
            difficulty: "easy",
            explanation: "В українській мові є чотири відміни іменників, які розрізняються за родом, закінченням та особливостями відмінювання.",
        },
        {
            id: "q4",
            number: 4,
            text: "Який іменник належить до другої відміни?",
            options: [
                { id: "q4-a", text: "Земля" },
                { id: "q4-b", text: "Стіл" },
                { id: "q4-c", text: "Радість" },
                { id: "q4-d", text: "Ім'я" },
            ],
            correctOptionId: "q4-b",
            difficulty: "medium",
            explanation: "До другої відміни належать іменники чоловічого роду з нульовим закінченням (стіл, батько) та середнього роду з закінченням -о, -е (вікно, поле).",
        },
        {
            id: "q5",
            number: 5,
            text: "Що таке власні іменники?",
            options: [
                { id: "q5-a", text: "Назви предметів" },
                { id: "q5-b", text: "Назви явищ природи" },
                { id: "q5-c", text: "Індивідуальні назви" },
                { id: "q5-d", text: "Назви почуттів" },
            ],
            correctOptionId: "q5-c",
            difficulty: "easy",
            explanation: "Власні іменники — це індивідуальні назви істот, географічних об'єктів, організацій тощо. Вони пишуться з великої літери.",
        },
        {
            id: "q6",
            number: 6,
            text: "Який рід має іменник 'сонце'?",
            options: [
                { id: "q6-a", text: "Чоловічий" },
                { id: "q6-b", text: "Жіночий" },
                { id: "q6-c", text: "Середній" },
                { id: "q6-d", text: "Спільний" },
            ],
            correctOptionId: "q6-c",
            difficulty: "easy",
            explanation: "Іменник 'сонце' має середній рід, бо відповідає на питання 'що?' і має закінчення -е.",
        },
        {
            id: "q7",
            number: 7,
            text: "Яке питання ставимо до іменників у давальному відмінку?",
            options: [
                { id: "q7-a", text: "Кого? Чого?" },
                { id: "q7-b", text: "Кому? Чому?" },
                { id: "q7-c", text: "Кого? Що?" },
                { id: "q7-d", text: "Ким? Чим?" },
            ],
            correctOptionId: "q7-b",
            difficulty: "medium",
            explanation: "Давальний відмінок відповідає на питання 'кому?' для істот і 'чому?' для неістот. Наприклад: дати (кому?) братові, радіти (чому?) успіхові.",
        },
        {
            id: "q8",
            number: 8,
            text: "Яке закінчення має іменник 'книга' в орудному відмінку?",
            options: [
                { id: "q8-a", text: "-ою" },
                { id: "q8-b", text: "-ом" },
                { id: "q8-c", text: "-ею" },
                { id: "q8-d", text: "-ю" },
            ],
            correctOptionId: "q8-a",
            difficulty: "medium",
            explanation: "Іменник 'книга' в орудному відмінку має закінчення -ою: книгою. Це типове закінчення для іменників першої відміни твердої групи.",
        },
        {
            id: "q9",
            number: 9,
            text: "Який іменник є множинним (не має однини)?",
            options: [
                { id: "q9-a", text: "Діти" },
                { id: "q9-b", text: "Ножиці" },
                { id: "q9-c", text: "Книги" },
                { id: "q9-d", text: "Учні" },
            ],
            correctOptionId: "q9-b",
            difficulty: "hard",
            explanation: "Іменник 'ножиці' вживається тільки у множині — це так званий pluralia tantum. Так само: окуляри, двері, штани.",
        },
        {
            id: "q10",
            number: 10,
            text: "Яка група іменників називається збірними?",
            options: [
                { id: "q10-a", text: "Назви осіб" },
                { id: "q10-b", text: "Сукупність однорідних предметів" },
                { id: "q10-c", text: "Назви дій" },
                { id: "q10-d", text: "Назви ознак" },
            ],
            correctOptionId: "q10-b",
            difficulty: "medium",
            explanation: "Збірні іменники позначають сукупність однорідних предметів як одне ціле. Наприклад: листя, каміння, студентство, молодь.",
        },
        {
            id: "q11",
            number: 11,
            text: "До якої відміни належить іменник 'ніч'?",
            options: [
                { id: "q11-a", text: "Першої" },
                { id: "q11-b", text: "Другої" },
                { id: "q11-c", text: "Третьої" },
                { id: "q11-d", text: "Четвертої" },
            ],
            correctOptionId: "q11-c",
            difficulty: "medium",
            explanation: "До третьої відміни належать іменники жіночого роду з нульовим закінченням і м'яким або шиплячим приголосним в кінці основи: ніч, сіль, радість.",
        },
        {
            id: "q12",
            number: 12,
            text: "Який відмінок вживається з прийменником 'на' (локативне значення)?",
            options: [
                { id: "q12-a", text: "Знахідний" },
                { id: "q12-b", text: "Давальний" },
                { id: "q12-c", text: "Місцевий" },
                { id: "q12-d", text: "Орудний" },
            ],
            correctOptionId: "q12-c",
            difficulty: "hard",
            explanation: "Прийменник 'на' з локативним значенням (де?) вживається з місцевим відмінком: на столі, на дорозі, на землі.",
        },
        {
            id: "q13",
            number: 13,
            text: "Яке чергування приголосних відбувається в іменнику 'рука' — 'руці'?",
            options: [
                { id: "q13-a", text: "к → ц" },
                { id: "q13-b", text: "г → з" },
                { id: "q13-c", text: "х → с" },
                { id: "q13-d", text: "к → ч" },
            ],
            correctOptionId: "q13-a",
            difficulty: "hard",
            explanation: "У давальному та місцевому відмінках однини відбувається чергування к → ц: рука — руці, нога — нозі (г → з).",
        },
    ],
};

export const mockTestStatistics: TestStatistics = {
    totalStudents: 20,
    completedStudents: 15,
    averageScore: 75,
    description: "Статистика відповідей по класу. Lorem ipsum dolor sit amet consectetur. Nullam consequat dolor malesuada etiam habitant eget. Faucibus massa integer lorem lectus ultrices scelerisque at felis enim. Vitae eget bibendum sapien posuere sapien nisl amet blandit et.",
};

export const getTestById = (testId: string): TestData | undefined => {
    // In the future, this will fetch from the backend
    if (testId === "test-1" || testId === mockTestData.id) {
        return mockTestData;
    }
    return mockTestData; // Return mock data for any ID for now
};

export const getTestStatistics = (testId: string): TestStatistics => {
    // In the future, this will fetch from the backend
    return mockTestStatistics;
};
