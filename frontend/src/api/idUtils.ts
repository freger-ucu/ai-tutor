export const toNumericId = (value?: string) => {
  if (!value) {
    return null;
  }
  const numeric = Number(value);
  if (!Number.isNaN(numeric)) {
    return numeric;
  }

  const match = value.match(/\d+/);
  if (!match) {
    return null;
  }
  return Number(match[0]);
};
