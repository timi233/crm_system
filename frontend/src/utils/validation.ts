export function isEmail(value: string): boolean {
  // Simple email validation placeholder
  return /^[^@]+@[^@]+\.[^@]+$/.test(value)
}
