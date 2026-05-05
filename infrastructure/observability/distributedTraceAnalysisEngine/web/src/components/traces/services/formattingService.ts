// Formatting service interface (Port)
export interface IFormattingService {
  formatDuration(durationNs: number): string;
  getServiceHue(serviceName: string): number;
}

// Formatting service implementation
export class FormattingService implements IFormattingService {
  formatDuration(durationNs: number): string {
    if (durationNs < 1_000) {
      return `${durationNs}ns`;
    } else if (durationNs < 1_000_000) {
      return `${(durationNs / 1_000).toFixed(2)}µs`;
    } else if (durationNs < 1_000_000_000) {
      return `${(durationNs / 1_000_000).toFixed(2)}ms`;
    } else {
      return `${(durationNs / 1_000_000_000).toFixed(2)}s`;
    }
  }

  getServiceHue(serviceName: string): number {
    let hash = 0;
    for (let i = 0; i < serviceName.length; i++) {
      hash = serviceName.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash % 360);
  }
}
