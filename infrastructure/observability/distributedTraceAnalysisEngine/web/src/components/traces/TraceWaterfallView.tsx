import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { Span } from '../../types/trace';

interface TraceWaterfallViewProps {
  spans: Span[];
}

export function TraceWaterfallView({ spans }: TraceWaterfallViewProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts>();

  useEffect(() => {
    if (!chartRef.current || !spans || spans.length === 0) return;

    // Dispose existing chart if it exists
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    // Initialize chart with explicit options
    chartInstance.current = echarts.init(chartRef.current, null, {
      renderer: 'canvas',
      useDirtyRect: false
    });

    // Process spans for waterfall chart
    const processedSpans = spans.map((span, _index) => {
      // Backend returns simple strings, no need for type checking
      const spanId = span.span_id;
      const parentSpanId = span.parent_span_id;

      return {
        name: span.service_name,
        operation: span.operation_name,
        startTime: span.start_time_ns,
        duration: span.duration_ns,
        spanId,
        parentSpanId,
        level: getSpanLevel(span, spans),
        service_name: span.service_name,
      };
    });

    // Sort by start time
    processedSpans.sort((a, b) => a.startTime - b.startTime);

    // Find the earliest start time
    const minTime = Math.min(...processedSpans.map(s => s.startTime));
    const maxTime = Math.max(
      ...processedSpans.map(s => s.startTime + s.duration)
    );
    const totalDuration = maxTime - minTime;

    // Create series data for waterfall
    const seriesData = processedSpans.map((span, index) => {
      const relativeStart = ((span.startTime - minTime) / totalDuration) * 100;
      const relativeDuration = (span.duration / totalDuration) * 100;

      return {
        name: span.operation,
        value: [
          span.level,
          relativeStart,
          relativeStart + relativeDuration,
          index,
        ],
        itemStyle: {
          color: getSpanColor(span.service_name),
        },
      };
    });

    const option = {
      tooltip: {
        formatter: (params: {data: {value: number[]}}) => {
          const data = params.data;
          const span = processedSpans[data.value[3]];
          return `
            <div style="padding: 8px;">
              <div style="font-weight: 600; margin-bottom: 4px;">${span.name}</div>
              <div style="font-size: 12px; color: #6b7280;">${span.operation}</div>
              <div style="font-size: 12px;">Duration: ${(span.duration / 1_000_000).toFixed(1)}ms</div>
            </div>
          `;
        },
      },
      grid: {
        left: 120,
        right: 40,
        top: 20,
        bottom: 40,
      },
      xAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: {
          formatter: (value: number) => {
            const timeMs = ((value / 100) * totalDuration) / 1_000_000;
            return `${timeMs.toFixed(0)}ms`;
          },
        },
      },
      yAxis: {
        type: 'category',
        data: processedSpans.map(span => span.operation),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          fontSize: 11,
          color: '#374151',
        },
      },
      series: [
        {
          type: 'custom',
          renderItem: (_params: unknown, api: {value: (index: number) => number; size: () => number[]; coord: (value: number[]) => number[]; visual: (opts: unknown) => void}) => {
            const categoryIndex = api.value(0);
            const start = api.value(1);
            const end = api.value(2);
            const height = (api.size()[0] / processedSpans.length) * 0.6;

            const coordX = api.coord([start, categoryIndex]);
            const coordWidth = api.coord([end, categoryIndex])[0] - coordX[0];

            return {
              type: 'rect',
              shape: {
                x: coordX[0],
                y: coordX[1] - height / 2,
                width: coordWidth,
                height: height,
              },
              style: {
                fill: api.visual('color'),
                stroke: '#e5e7eb',
                lineWidth: 1,
              },
            };
          },
          data: seriesData,
          encode: {
            x: [1, 2],
            y: 0,
          },
        },
      ],
    };

    try {
      chartInstance.current.setOption(option);
      
      // Force a resize after setting options
      setTimeout(() => {
        chartInstance.current?.resize();
      }, 100);
    } catch (error) {
      console.error('Error setting waterfall chart options:', error);
    }

    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [spans]);

  const getSpanLevel = (span: Span, allSpans: Span[]): number => {
    let level = 0;
    let currentSpan = span;

    while (currentSpan.parent_span_id) {
      level++;
      const parentId =
        typeof currentSpan.parent_span_id === 'string'
          ? currentSpan.parent_span_id
          : currentSpan.parent_span_id['0'];
      currentSpan =
        allSpans.find(s => {
          const id = typeof s.span_id === 'string' ? s.span_id : s.span_id['0'];
          return id === parentId;
        }) || currentSpan;

      if (level > 10) break; // Prevent infinite loops
    }

    return level;
  };

  const getSpanColor = (serviceName: string): string => {
    const colors = [
      '#3b82f6',
      '#10b981',
      '#f59e0b',
      '#ef4444',
      '#8b5cf6',
      '#06b6d4',
      '#84cc16',
      '#f97316',
      '#ec4899',
      '#6366f1',
    ];

    let hash = 0;
    for (let i = 0; i < serviceName.length; i++) {
      hash = serviceName.charCodeAt(i) + ((hash << 5) - hash);
    }

    return colors[Math.abs(hash) % colors.length];
  };

  return <div ref={chartRef} style={{ width: '100%', height: '100%' }} />;
}
