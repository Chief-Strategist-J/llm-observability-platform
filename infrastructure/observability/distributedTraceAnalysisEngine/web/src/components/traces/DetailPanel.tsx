import { Span } from '../../types/trace';
import { getTheme, Theme } from './TraceDAGView.themes';
import { ServiceFactory } from './interfaces/traceFactories';

interface DetailPanelProps {
  span: Span;
  onClose: () => void;
  theme: Theme;
}

export function DetailPanel({ span, onClose, theme }: DetailPanelProps) {
  const colors = getTheme(theme);
  
  // Use services for formatting and mapping (SRP Rule 1 - Single Responsibility)
  const formattingService = ServiceFactory.createFormattingService();
  const mapperService = ServiceFactory.createSpanDetailMapperService();
  
  const serviceHue = formattingService.getServiceHue(span.service_name);
  const rows = mapperService.mapSpanToDetailRows(span, formattingService);

  return (
    <div
      style={{
        position: 'absolute',
        top: 16,
        right: 16,
        width: 280,
        background: colors.panelBackground,
        border: `1px solid ${colors.panelBorder.replace('var(--service-hue)', serviceHue.toString())}`,
        borderRadius: 8,
        padding: 16,
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        zIndex: 1000,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
          paddingBottom: 8,
          borderBottom: `1px solid ${colors.border}`,
        }}
      >
        <div
          style={{
            fontSize: '14px',
            fontWeight: 600,
            color: colors.text,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: `hsl(${serviceHue}, 70%, 50%)`,
            }}
          />
          {span.service_name}
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: colors.text,
            cursor: 'pointer',
            fontSize: '16px',
            padding: 0,
            lineHeight: 1,
          }}
        >
          ×
        </button>
      </div>

      <div style={{ fontSize: '12px', color: colors.text }}>
        {rows.map(([label, value], idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '6px 0',
              borderBottom: idx < rows.length - 1 ? `1px solid ${colors.border}` : 'none',
            }}
          >
            <span style={{ color: colors.muted }}>{label}:</span>
            <span style={{ fontFamily: 'monospace', color: colors.text }}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
