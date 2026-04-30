// Common style constants to eliminate duplication (DRY compliance)

export const COLORS = {
  PRIMARY: '#1f2937',
  SECONDARY: '#6b7280',
  SUCCESS: '#10b981',
  WARNING: '#f59e0b',
  ERROR: '#dc2626',
  BORDER: '#e2e8f0',
  BACKGROUND: '#ffffff',
  MUTED: '#f9fafb',
  TEXT_MUTED: '#6b7280',
} as const;

export const SPACING = {
  XS: '4px',
  SM: '8px',
  MD: '12px',
  LG: '16px',
  XL: '20px',
  XXL: '24px',
} as const;

export const BORDER_RADIUS = {
  SM: '4px',
  MD: '8px',
  LG: '12px',
} as const;

export const FONT_SIZES = {
  XS: '12px',
  SM: '14px',
  MD: '16px',
  LG: '18px',
  XL: '20px',
} as const;

export const FONT_WEIGHTS = {
  NORMAL: '400',
  MEDIUM: '500',
  SEMIBOLD: '600',
  BOLD: '700',
} as const;

export const BOX_SHADOW = {
  LIGHT: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
  MEDIUM: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
  HEAVY: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
} as const;

// Common style objects
export const cardStyles = {
  base: {
    background: COLORS.BACKGROUND,
    borderRadius: BORDER_RADIUS.LG,
    border: `1px solid ${COLORS.BORDER}`,
    boxShadow: BOX_SHADOW.LIGHT,
  },
  padding: (padding: string = SPACING.XL) => ({
    padding,
  }),
  hover: {
    transition: 'all 0.2s ease-in-out',
    cursor: 'pointer',
  },
};

export const textStyles = {
  heading: {
    fontSize: FONT_SIZES.XL,
    fontWeight: FONT_WEIGHTS.SEMIBOLD,
    color: COLORS.PRIMARY,
    margin: 0,
  },
  subheading: {
    fontSize: FONT_SIZES.MD,
    fontWeight: FONT_WEIGHTS.SEMIBOLD,
    color: COLORS.PRIMARY,
    margin: 0,
  },
  body: {
    fontSize: FONT_SIZES.SM,
    color: COLORS.SECONDARY,
    margin: 0,
  },
  muted: {
    fontSize: FONT_SIZES.XS,
    color: COLORS.TEXT_MUTED,
    margin: 0,
  },
};

export const layoutStyles = {
  flex: {
    display: 'flex',
  },
  flexCenter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  flexColumn: {
    display: 'flex',
    flexDirection: 'column',
  },
  grid: (columns: string, gap: string = SPACING.LG) => ({
    display: 'grid',
    gridTemplateColumns: columns,
    gap,
  }),
};
