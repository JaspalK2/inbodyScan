export interface ParsedName {
  firstName: string;
  lastName: string | null;
}

export function parseGoogleName(fullName: string): ParsedName {
  if (!fullName) {
    return { firstName: "", lastName: null };
  }
  const idx = fullName.indexOf(" ");
  if (idx === -1) {
    return { firstName: fullName, lastName: null };
  }
  return {
    firstName: fullName.slice(0, idx),
    lastName: fullName.slice(idx + 1),
  };
}
