export interface CallerInfo {
  functionName: string;
  filePath: string;
  lineNumber: number;
}

export function getCallerInfo(fallbackDepth = 3): CallerInfo {
  const err = new Error();
  const stack = err.stack?.split('\n') || [];

  // Dynamic stack scanning: find first frame outside http-client infrastructure boundary
  let targetFrame = '';
  for (let i = 2; i < stack.length; i++) {
    const frame = stack[i];
    if (frame && !frame.includes('http-client.ts') && !frame.includes('caller-info.ts')) {
      targetFrame = frame;
      break;
    }
  }

  if (!targetFrame) {
    targetFrame = stack[fallbackDepth] || stack[1] || '';
  }

  const match = targetFrame.match(/at\s+(?:(.+?)\s+\()?\(?(.+?):(\d+):(\d+)\)?/);
  const rawPath = match?.[2] || 'unknown';

  // Normalize to repo-relative path to prevent internal user/infra directory leakage in OpenTelemetry telemetry
  let repoRelativePath = rawPath;
  if (rawPath.includes('/packages/')) {
    repoRelativePath = 'packages/' + rawPath.split('/packages/')[1];
  } else if (rawPath.includes('/src/')) {
    repoRelativePath = 'src/' + rawPath.split('/src/')[1];
  } else {
    repoRelativePath = rawPath.replace(/^.*[\\\/]/, '');
  }

  return {
    functionName: match?.[1] || 'anonymous',
    filePath: repoRelativePath,
    lineNumber: match?.[3] ? parseInt(match[3], 10) : 0,
  };
}
