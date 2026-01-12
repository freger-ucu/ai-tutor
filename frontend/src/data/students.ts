export interface Student {
    id: string;
    firstName: string;
    lastName: string;
    className: string;
    teacherIds: string[];
}

export const students: Student[] = [
    {
        id: "s1",
        firstName: "Марія",
        lastName: "Петренко",
        className: "8-А",
        teacherIds: ["t1", "t2", "t3"],
    },
    {
        id: "s2",
        firstName: "Олександр",
        lastName: "Коваленко",
        className: "8-А",
        teacherIds: ["t1", "t2", "t3"],
    },
    {
        id: "s3",
        firstName: "Анна",
        lastName: "Мельник",
        className: "8-А",
        teacherIds: ["t1", "t2", "t3"],
    },
    {
        id: "s4",
        firstName: "Дмитро",
        lastName: "Бойко",
        className: "8-А",
        teacherIds: ["t1", "t2", "t3"],
    },
];
