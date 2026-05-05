export interface ThemeColors {
  background: string;
  nodeBackground: string;
  nodeBackgroundSelected: string;
  nodeBorder: string;
  nodeBorderSelected: string;
  nodeBorderError: string;
  nodeText: string;
  nodeTextSecondary: string;
  nodeAccent: string;
  badgeBackground: string;
  badgeBorder: string;
  badgeText: string;
  badgeTextError: string;
  badgeBackgroundError: string;
  badgeBorderError: string;
  panelBackground: string;
  panelBorder: string;
  panelHeader: string;
  panelHeaderText: string;
  controlsBackground: string;
  controlsBorder: string;
  minimapBackground: string;
  minimapBorder: string;
  minimapMask: string;
  gridColor: string;
  edgeColor: string;
  edgeLabelColor: string;
  statBackground: string;
  statBorder: string;
  statLabelText: string;
  statValueText: string;
}

export const darkTheme: ThemeColors = {
  background: '#080a0f',
  nodeBackground: 'rgba(15,17,23,0.92)',
  nodeBackgroundSelected: 'rgba(255,255,255,0.06)',
  nodeBorder: 'hsla(var(--service-hue),40%,40%,0.35)',
  nodeBorderSelected: 'hsla(var(--service-hue),70%,60%,0.8)',
  nodeBorderError: 'rgba(248,113,113,0.6)',
  nodeText: 'hsl(var(--service-hue),70%,72%)',
  nodeTextSecondary: 'rgba(203,213,225,0.75)',
  nodeAccent: 'hsl(var(--service-hue),65%,55%)',
  badgeBackground: 'hsla(var(--service-hue),50%,10%,0.95)',
  badgeBorder: 'hsla(var(--service-hue),50%,35%,0.6)',
  badgeText: 'hsl(var(--service-hue),70%,65%)',
  badgeTextError: '#fca5a5',
  badgeBackgroundError: 'rgba(127,29,29,0.9)',
  badgeBorderError: 'rgba(248,113,113,0.4)',
  panelBackground: 'rgba(10,12,18,0.97)',
  panelBorder: 'hsla(var(--service-hue),40%,40%,0.4)',
  panelHeader: 'hsla(var(--service-hue),30%,10%,0.6)',
  panelHeaderText: 'hsl(var(--service-hue),70%,65%)',
  controlsBackground: 'rgba(10,12,18,0.9)',
  controlsBorder: 'rgba(51,65,85,0.5)',
  minimapBackground: 'rgba(10,12,18,0.9)',
  minimapBorder: 'rgba(51,65,85,0.5)',
  minimapMask: 'rgba(0,0,0,0.6)',
  gridColor: 'rgba(51,65,85,0.25)',
  edgeColor: 'rgba(100,116,139,0.5)',
  edgeLabelColor: 'rgba(148,163,184,0.6)',
  statBackground: 'rgba(15,17,23,0.9)',
  statBorder: 'rgba(51,65,85,0.6)',
  statLabelText: 'rgba(100,116,139,0.7)',
  statValueText: '#e2e8f0',
};

export const lightTheme: ThemeColors = {
  background: '#f8fafc',
  nodeBackground: 'rgba(255,255,255,0.95)',
  nodeBackgroundSelected: 'rgba(59,130,246,0.08)',
  nodeBorder: 'hsla(var(--service-hue),40%,50%,0.4)',
  nodeBorderSelected: 'hsla(var(--service-hue),70%,50%,0.8)',
  nodeBorderError: 'rgba(239,68,68,0.6)',
  nodeText: 'hsl(var(--service-hue),60%,35%)',
  nodeTextSecondary: 'rgba(71,85,105,0.8)',
  nodeAccent: 'hsl(var(--service-hue),65%,50%)',
  badgeBackground: 'hsla(var(--service-hue),50%,95%,0.9)',
  badgeBorder: 'hsla(var(--service-hue),50%,70%,0.6)',
  badgeText: 'hsl(var(--service-hue),70%,40%)',
  badgeTextError: '#dc2626',
  badgeBackgroundError: 'rgba(254,226,226,0.9)',
  badgeBorderError: 'rgba(239,68,68,0.4)',
  panelBackground: 'rgba(255,255,255,0.98)',
  panelBorder: 'hsla(var(--service-hue),40%,50%,0.4)',
  panelHeader: 'hsla(var(--service-hue),30%,95%,0.8)',
  panelHeaderText: 'hsl(var(--service-hue),70%,40%)',
  controlsBackground: 'rgba(255,255,255,0.9)',
  controlsBorder: 'rgba(203,213,225,0.6)',
  minimapBackground: 'rgba(255,255,255,0.9)',
  minimapBorder: 'rgba(203,213,225,0.6)',
  minimapMask: 'rgba(0,0,0,0.1)',
  gridColor: 'rgba(203,213,225,0.3)',
  edgeColor: 'rgba(100,116,139,0.4)',
  edgeLabelColor: 'rgba(71,85,105,0.7)',
  statBackground: 'rgba(255,255,255,0.9)',
  statBorder: 'rgba(203,213,225,0.6)',
  statLabelText: 'rgba(107,114,128,0.8)',
  statValueText: '#1e293b',
};

export type Theme = 'dark' | 'light';

export function getTheme(theme: Theme): ThemeColors {
  return theme === 'dark' ? darkTheme : lightTheme;
}
