export interface Student {
    id: string;
    apiId: number;
    firstName: string;
    lastName: string;
    className: string;
    teacherIds: string[];
}

export const students: Student[] = [
    {
        id: "s1",
        apiId: 1,
        firstName: "Марія",
        lastName: "Петренко",
        className: "9",
        teacherIds: ["t1", "t2", "t3"],
    },
    {
        id: "s2",
        apiId: 2,
        firstName: "Олександр",
        lastName: "Коваленко",
        className: "9",
        teacherIds: ["t1", "t2", "t3"],
    },
    {
        id: "s3",
        apiId: 3,
        firstName: "Анна",
        lastName: "Мельник",
        className: "8",
        teacherIds: ["t1", "t2", "t3"],
    },
    {
        id: "s4",
        apiId: 4,
        firstName: "Дмитро",
        lastName: "Бойко",
        className: "8",
        teacherIds: ["t1", "t2", "t3"],
    },
];
