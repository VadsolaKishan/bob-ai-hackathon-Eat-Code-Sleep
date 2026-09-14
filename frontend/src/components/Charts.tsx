import React, { useEffect, useRef } from 'react';
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

Chart.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler
);

export { Chart };

// ─── Risk Distribution Doughnut ────────────────────────────────────────────────

interface RiskDistChartProps {
  distribution: Record<string, number>;
}

export function RiskDistributionChart({ distribution }: RiskDistChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    chartRef.current?.destroy();

    const labels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
    const data = labels.map(l => distribution[l] ?? 0);

    chartRef.current = new Chart(canvasRef.current, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: ['#ef444433', '#f9731633', '#f59e0b33', '#10b98133'],
          borderColor: ['#ef4444', '#f97316', '#f59e0b', '#10b981'],
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { color: '#94a3b8', font: { size: 11 } } },
          tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} assets` } },
        },
        cutout: '65%',
      },
    });

    return () => chartRef.current?.destroy();
  }, [distribution]);

  return <canvas ref={canvasRef} style={{ maxHeight: '180px' }} />;
}

// ─── Risk Scores Bar Chart ──────────────────────────────────────────────────────

interface RiskBarChartProps {
  labels: string[];
  scores: number[];
  riskLevels: string[];
}

export function RiskBarChart({ labels, scores, riskLevels }: RiskBarChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  const COLORS: Record<string, string> = { CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#f59e0b', LOW: '#10b981' };

  useEffect(() => {
    if (!canvasRef.current) return;
    chartRef.current?.destroy();

    chartRef.current = new Chart(canvasRef.current, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Risk Score',
          data: scores.map(s => Math.round(s * 100)),
          backgroundColor: riskLevels.map(l => (COLORS[l] ?? '#3b82f6') + '55'),
          borderColor: riskLevels.map(l => COLORS[l] ?? '#3b82f6'),
          borderWidth: 1.5,
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(99,179,237,0.06)' } },
          y: { max: 100, ticks: { color: '#94a3b8', font: { size: 10 }, callback: v => v + '%' }, grid: { color: 'rgba(99,179,237,0.06)' } },
        },
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y}%` } } },
      },
    });

    return () => chartRef.current?.destroy();
  }, [labels, scores, riskLevels]);

  return <canvas ref={canvasRef} style={{ maxHeight: '200px' }} />;
}

// ─── Sensor Line Chart ──────────────────────────────────────────────────────────

interface SensorChartProps {
  timestamps: string[];
  temperature: number[];
  vibration: number[];
  pd: number[];
}

export function SensorLineChart({ timestamps, temperature, vibration, pd }: SensorChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  const labels = timestamps.map(t => new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));

  useEffect(() => {
    if (!canvasRef.current) return;
    chartRef.current?.destroy();

    chartRef.current = new Chart(canvasRef.current, {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: 'Temp (°C)', data: temperature, borderColor: '#ef4444', backgroundColor: '#ef444411', fill: true, tension: 0.3 },
          { label: 'Vibration (mm/s)', data: vibration, borderColor: '#f59e0b', backgroundColor: '#f59e0b11', fill: true, tension: 0.3, yAxisID: 'y1' },
          { label: 'PD (pC/10)', data: pd.map(v => v / 10), borderColor: '#8b5cf6', backgroundColor: '#8b5cf611', fill: true, tension: 0.3 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(99,179,237,0.06)' } },
          y: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(99,179,237,0.06)' } },
          y1: { display: false, position: 'right' },
        },
        plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } },
      },
    });

    return () => chartRef.current?.destroy();
  }, [labels.join(',')]);

  return <canvas ref={canvasRef} style={{ maxHeight: '220px' }} />;
}

// ─── Weather Risk Bar Chart ─────────────────────────────────────────────────────

interface WeatherChartProps {
  labels: string[];
  scores: number[];
}

export function WeatherRiskChart({ labels, scores }: WeatherChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    chartRef.current?.destroy();

    chartRef.current = new Chart(canvasRef.current, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Weather Risk %',
          data: scores.map(s => Math.round(s * 100)),
          backgroundColor: scores.map(s => s >= 0.7 ? '#ef444433' : s >= 0.4 ? '#f9731633' : s >= 0.2 ? '#f59e0b33' : '#10b98133'),
          borderColor: scores.map(s => s >= 0.7 ? '#ef4444' : s >= 0.4 ? '#f97316' : s >= 0.2 ? '#f59e0b' : '#10b981'),
          borderWidth: 1.5,
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(99,179,237,0.06)' } },
          y: { max: 100, ticks: { color: '#94a3b8', font: { size: 10 }, callback: v => v + '%' }, grid: { color: 'rgba(99,179,237,0.06)' } },
        },
        plugins: { legend: { display: false } },
      },
    });

    return () => chartRef.current?.destroy();
  }, [labels.join(',')]);

  return <canvas ref={canvasRef} style={{ maxHeight: '200px' }} />;
}
