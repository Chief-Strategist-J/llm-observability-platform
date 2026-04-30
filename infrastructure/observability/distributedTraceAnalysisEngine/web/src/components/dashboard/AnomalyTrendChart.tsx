import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { api } from '../../api';
import { usePolling } from '../../hooks';

export function AnomalyTrendChart() {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts>();

  // Fetch real anomaly trend data
  const { data: traces, loading } = usePolling(
    () => api.results(100, 0),
    5000
  );

  useEffect(() => {
    if (!chartRef.current || loading || !traces) return;

    chartInstance.current = echarts.init(chartRef.current);

    // Process real trace data for trend visualization
    const anomalyData = traces.results
      .filter(trace => trace.is_anomalous || (trace.confidence && trace.confidence > 0.5))
      .map(trace => trace.confidence || 0)
      .slice(0, 30); // Last 30 data points

    const times = anomalyData.map((_, index) => {
      const time = new Date(Date.now() - (29 - index) * 5 * 60 * 1000);
      return time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    });

    const option = {
      title: {
        text: 'Anomaly Trend',
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 600,
          color: '#1f2937',
        },
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: Array<{value: number; name: string}>) => {
          const data = params[0];
          return `
            <div style="padding: 8px;">
              <div style="font-weight: 600; margin-bottom: 4px;">${data.name}</div>
              <div>Anomaly Score: ${(data.value * 100).toFixed(1)}%</div>
            </div>
          `;
        },
      },
      xAxis: {
        type: 'category',
        data: times,
        axisLabel: {
          rotate: 45,
          interval: 4,
        },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 1,
        axisLabel: {
          formatter: (value: number) => `${(value * 100).toFixed(0)}%`,
        },
      },
      series: [
        {
          data: anomalyData,
          type: 'line',
          smooth: true,
          lineStyle: {
            color: '#3b82f6',
            width: 2,
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0.05)' },
              ],
            },
          },
          emphasis: {
            focus: 'series',
          },
          markLine: {
            silent: true,
            data: [
              {
                yAxis: 0.7,
                label: {
                  formatter: 'Threshold: 70%',
                  position: 'end',
                },
                lineStyle: {
                  color: '#ef4444',
                  type: 'dashed',
                  width: 2,
                },
              },
            ],
          },
        },
      ],
      grid: {
        left: 60,
        right: 40,
        top: 60,
        bottom: 80,
      },
    };

    chartInstance.current.setOption(option);

    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [loading, traces]);

  return (
    <div
      style={{
        background: '#ffffff',
        borderRadius: 12,
        border: '1px solid #e2e8f0',
        padding: 20,
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
      }}
    >
      <div ref={chartRef} style={{ width: '100%', height: 300 }} />
    </div>
  );
}
