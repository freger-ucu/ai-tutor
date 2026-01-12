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
        teacherIds: ["t1", "t2", "t3"], // Has all 3 teachers
    },
];
