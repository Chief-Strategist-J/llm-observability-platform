export interface CallerInfo {
  functionName: string;
  filePath: string;
  lineNumber: number;
}

export function getCallerInfo(depth = 2): CallerInfo {
  const err = new Error();
  const stack = err.stack?.split('\n') || [];
  const frame = stack[depth] || stack[1] || '';
  const match = frame.match(/at\s+(?:(.+?)\s+\()?\(?(.+?):(\d+):(\d+)\)?/);

  return {
    functionName: match?.[1] || 'anonymous',
    filePath: match?.[2] || 'unknown',
    lineNumber: match?.[3] ? parseInt(match[3], 10) : 0,
  };
}
