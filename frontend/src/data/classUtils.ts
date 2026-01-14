export const classLabelToId = (label: string) => {
  const match = label.match(/(\d+)/);
  if (!match) {
    return null;
  }
  const grade = Number(match[1]);
  if (Number.isNaN(grade)) {
    return null;
  }
  return grade;
};

export const classIdToLabel = (classNumber: number, classId: number) => {
  return `${classNumber || classId}`;
};
