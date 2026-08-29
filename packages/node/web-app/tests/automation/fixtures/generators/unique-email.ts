export function generateUniqueEmail(prefix = 'test'): string {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 10000);
  return `${prefix}.${timestamp}.${random}@scaibu.io`;
}
