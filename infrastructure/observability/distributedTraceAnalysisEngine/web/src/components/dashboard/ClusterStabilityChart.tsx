import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { getClusters } from '../../utils/dataTransformations';
import { usePolling } from '../../hooks';

export function ClusterStabilityChart() {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts>();

  // Fetch real cluster data
  const { data: clusters, loading: clustersLoading } = usePolling(
    () => getClusters(),
    5000
  );

  useEffect(() => {
    if (!chartRef.current || clustersLoading || !clusters) return;

    chartInstance.current = echarts.init(chartRef.current);

    // Transform real cluster data for bubble map
    const data = clusters.map((cluster) => {
      // Create 2D projection based on anomaly rate and latency
      const anomalyRate = cluster.anomalyRate;
      const latencyValue = parseFloat(cluster.avgLatency.replace(/[ms]/g, ''));
      const latencyMs = cluster.avgLatency.includes('s')
        ? latencyValue * 1000
        : latencyValue;

      // Position clusters based on their metrics
      const x = anomalyRate * 4; // Anomaly rate on x-axis
      const y = Math.min(latencyMs / 10, 80); // Latency on y-axis (scaled)

      return {
        name: cluster.id,
        value: [x, y, cluster.size / 100], // [x, y, size scaled]
        normal: cluster.status === 'stable',
        anomalyRate: cluster.anomalyRate,
        avgLatency: cluster.avgLatency,
      };
    });

    const option = {
      title: {
        text: 'Cluster Stability',
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 600,
          color: '#1f2937',
        },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: {data: {name: string; value: number[]; normal: boolean}}) => {
          const data = params.data;
          return `
            <div style="padding: 8px;">
              <div style="font-weight: 600; margin-bottom: 4px;">${data.name}</div>
              <div>Volume: ${data.value[2].toLocaleString()} traces/min</div>
              <div>Status: ${data.normal ? 'Normal' : 'Anomalous'}</div>
            </div>
          `;
        },
      },
      xAxis: {
        type: 'value',
        name: 'Latency Drift',
        nameLocation: 'middle',
        nameGap: 30,
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%',
        },
      },
      yAxis: {
        type: 'value',
        name: 'Error Rate',
        nameLocation: 'middle',
        nameGap: 40,
        min: 0,
        max: 100,
        axisLabel: {
          formatter: '{value}%',
        },
      },
      visualMap: {
        show: false,
        dimension: 2,
        min: 2000,
        max: 6000,
        inRange: {
          symbolSize: [20, 70],
        },
      },
      series: [
        {
          type: 'scatter',
          data: data.map(item => ({
            name: item.name,
            value: item.value,
            itemStyle: {
              color: item.normal ? '#10b981' : '#ef4444',
              opacity: 0.8,
            },
          })),
          emphasis: {
            focus: 'series',
            itemStyle: {
              opacity: 1,
              borderColor: '#1f2937',
              borderWidth: 2,
            },
          },
        },
      ],
      grid: {
        left: 60,
        right: 40,
        top: 60,
        bottom: 60,
      },
    };

    chartInstance.current.setOption(option);

    // Handle resize
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [clusters, clustersLoading]);

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
      <div
        style={{
          marginTop: 12,
          fontSize: '12px',
          color: '#6b7280',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#10b981',
            }}
          />
          <span>Normal cluster</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#ef4444',
            }}
          />
          <span>Anomalous cluster</span>
        </div>
        <div>Bubble size = trace volume</div>
      </div>
    </div>
  );
}
