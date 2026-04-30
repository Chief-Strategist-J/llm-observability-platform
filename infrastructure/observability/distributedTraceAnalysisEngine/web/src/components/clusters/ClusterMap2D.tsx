import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface Cluster {
  id: string;
  size: number;
  avgLatency: string;
  anomalyRate: number;
  status: 'stable' | 'degrading' | 'critical';
  volume: string;
}

interface ClusterMap2DProps {
  clusters: Cluster[];
  selectedCluster?: string | null;
  onClusterSelect?: (clusterId: string) => void;
}

export function ClusterMap2D({
  clusters,
  selectedCluster,
  onClusterSelect,
}: ClusterMap2DProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts>();

  useEffect(() => {
    if (!chartRef.current) return;

    chartInstance.current = echarts.init(chartRef.current);

    // Generate 2D projection data
    const data = clusters.map((cluster, index) => {
      // Create a 2D layout - could use real projection algorithm
      const angle = (index / clusters.length) * Math.PI * 2;
      const radius = 50 + Math.random() * 100;

      return {
        name: cluster.id,
        value: [
          Math.cos(angle) * radius + 200, // x coordinate
          Math.sin(angle) * radius + 200, // y coordinate
          cluster.size, // bubble size
        ],
        normal: cluster.status === 'stable',
        anomalyRate: cluster.anomalyRate,
        avgLatency: cluster.avgLatency,
        status: cluster.status,
      };
    });

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: (params: {data: {name: string; value: number[]; anomalyRate: number; avgLatency: string; status: string}}) => {
          const data = params.data;
          return `
            <div style="padding: 8px;">
              <div style="font-weight: 600; margin-bottom: 4px;">${data.name}</div>
              <div>Size: ${data.value[2].toLocaleString()} traces</div>
              <div>Status: ${data.status}</div>
              <div>Anomaly Rate: ${data.anomalyRate}%</div>
              <div>Avg Latency: ${data.avgLatency}</div>
            </div>
          `;
        },
      },
      xAxis: {
        type: 'value',
        min: 0,
        max: 400,
        show: false,
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 400,
        show: false,
      },
      visualMap: {
        show: false,
        dimension: 2,
        min: 1000,
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
              opacity: selectedCluster === item.name ? 1 : 0.8,
              borderColor:
                selectedCluster === item.name ? '#1f2937' : 'transparent',
              borderWidth: selectedCluster === item.name ? 3 : 0,
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                opacity: 1,
                borderColor: '#1f2937',
                borderWidth: 2,
              },
            },
          })),
          emphasis: {
            focus: 'series',
          },
        },
      ],
      grid: {
        left: 0,
        right: 0,
        top: 0,
        bottom: 0,
      },
    };

    chartInstance.current.setOption(option);

    // Handle click events
    chartInstance.current.on('click', (params: echarts.ECElementEvent) => {
      if (onClusterSelect && params.data && typeof params.data === 'object' && 'name' in params.data) {
        onClusterSelect((params.data as {name: string}).name);
      }
    });

    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [clusters, selectedCluster, onClusterSelect]);

  return <div ref={chartRef} style={{ width: '100%', height: '100%' }} />;
}
