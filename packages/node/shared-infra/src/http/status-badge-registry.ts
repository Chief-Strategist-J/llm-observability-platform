export interface StatusStyle {
  label: string;
  badgeClass: string;
  dotClass: string;
}

export class StatusBadgeRegistry {
  private readonly styles = new Map<string, StatusStyle>([
    [
      "success",
      {
        label: "Success",
        badgeClass: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        dotClass: "bg-emerald-400",
      },
    ],
    [
      "healthy",
      {
        label: "Healthy",
        badgeClass: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        dotClass: "bg-emerald-400",
      },
    ],
    [
      "warning",
      {
        label: "Warning",
        badgeClass: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        dotClass: "bg-amber-400",
      },
    ],
    [
      "degraded",
      {
        label: "Degraded",
        badgeClass: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        dotClass: "bg-amber-400",
      },
    ],
    [
      "error",
      {
        label: "Error",
        badgeClass: "bg-rose-500/10 text-rose-400 border-rose-500/20",
        dotClass: "bg-rose-400",
      },
    ],
    [
      "unhealthy",
      {
        label: "Unhealthy",
        badgeClass: "bg-rose-500/10 text-rose-400 border-rose-500/20",
        dotClass: "bg-rose-400",
      },
    ],
    [
      "critical",
      {
        label: "Critical",
        badgeClass: "bg-rose-600/20 text-rose-300 border-rose-600/30",
        dotClass: "bg-rose-500 animate-pulse",
      },
    ],
  ]);

  public register(status: string, style: StatusStyle): void {
    this.styles.set(status, style);
  }

  public getStyle(status: string): StatusStyle {
    const fallback: StatusStyle = {
      label: status,
      badgeClass: "bg-slate-500/10 text-slate-400 border-slate-500/20",
      dotClass: "bg-slate-400",
    };
    return this.styles.get(status.toLowerCase()) ?? fallback;
  }
}

export const statusBadgeRegistry = new StatusBadgeRegistry();
