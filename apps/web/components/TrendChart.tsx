"use client";

import ReactECharts from "echarts-for-react";

type Point = { period_start: string; value: number };

export function TrendChart({
  title,
  series,
  unit,
}: {
  title: string;
  series: Point[];
  unit: string;
}) {
  const option = {
    title: {
      text: title,
      left: 0,
      textStyle: { fontSize: 14, fontWeight: 600, color: "#1c2a32" },
    },
    grid: { left: 48, right: 16, top: 48, bottom: 32 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: series.map((p) => p.period_start.slice(0, 4)),
      axisLabel: { color: "#5b6b75" },
    },
    yAxis: {
      type: "value",
      name: unit,
      nameTextStyle: { color: "#5b6b75" },
      axisLabel: { color: "#5b6b75" },
      splitLine: { lineStyle: { color: "#e6ecef" } },
    },
    series: [
      {
        type: "line",
        smooth: true,
        data: series.map((p) => p.value),
        lineStyle: { color: "#0f5c6e", width: 3 },
        itemStyle: { color: "#0f5c6e" },
        areaStyle: { color: "rgba(15, 92, 110, 0.12)" },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: 280, width: "100%" }} />;
}
