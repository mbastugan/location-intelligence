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
      textStyle: {
        fontSize: 13,
        fontWeight: 600,
        color: "#667780",
        fontFamily: "inherit",
      },
    },
    grid: { left: 52, right: 12, top: 44, bottom: 28 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: series.map((p) => p.period_start.slice(0, 4)),
      axisLine: { lineStyle: { color: "rgba(16,33,41,0.15)" } },
      axisLabel: { color: "#667780" },
    },
    yAxis: {
      type: "value",
      name: unit,
      nameTextStyle: { color: "#667780" },
      axisLabel: { color: "#667780" },
      splitLine: { lineStyle: { color: "rgba(16,33,41,0.08)" } },
    },
    series: [
      {
        type: "line",
        smooth: true,
        data: series.map((p) => p.value),
        lineStyle: { color: "#0c6b7c", width: 3 },
        itemStyle: { color: "#0c6b7c" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(12, 107, 124, 0.28)" },
              { offset: 1, color: "rgba(12, 107, 124, 0.02)" },
            ],
          },
        },
        symbolSize: 7,
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: 300, width: "100%" }} />;
}
