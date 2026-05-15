from __future__ import annotations

import json
import os
from typing import TypedDict

import streamlit as st
import streamlit.components.v1 as components

from ..models import SimulationFrame

DEFAULT_ANIMATION_DELAY_MS = int(float(os.getenv("MLFQ_ANIMATION_DELAY", "0.15")) * 1000)
COLOR_MAP = {
    "Q0": "#ef4444",
    "Q1": "#f59e0b",
    "Q2": "#22c55e",
    "N/A": "#6b7280",
}


class GanttPayloadEntry(TypedDict):
    task: str
    start: int
    finish: int
    queue: str


class FramePayload(TypedDict):
    time_current: int
    status: str
    running_pid: str | None
    running_queue: str
    queue_snapshot: dict[str, list[str]]
    completed_pids: list[str]
    gantt_log: list[GanttPayloadEntry]


def _frame_to_payload(frame: SimulationFrame) -> FramePayload:
    return {
        "time_current": frame.time_current,
        "status": frame.status,
        "running_pid": frame.running_pid,
        "running_queue": frame.running_queue,
        "queue_snapshot": frame.queue_snapshot,
        "completed_pids": frame.completed_pids,
        "gantt_log": [
            {
                "task": entry.Task,
                "start": entry.Start,
                "finish": entry.Finish,
                "queue": entry.Queue,
            }
            for entry in frame.gantt_log
        ],
    }


def _max_finish_from_payload(payload: list[FramePayload]) -> int:
    max_finish = 1
    for frame in payload:
        for item in frame["gantt_log"]:
            max_finish = max(max_finish, item["finish"])
    return max_finish


def _build_animation_document(
    frames: list[SimulationFrame],
    delay_ms: int,
) -> str:
    payload: list[FramePayload] = [_frame_to_payload(frame) for frame in frames]
    payload_json = json.dumps(payload, ensure_ascii=False)
    color_map_json = json.dumps(COLOR_MAP)
    max_finish = _max_finish_from_payload(payload)
    max_tick = max((frame["time_current"] for frame in payload), default=1)

    return f"""
<div id="mlfq-animation-root">
  <style>
    #mlfq-animation-root {{
      font-family: system-ui, sans-serif;
      border: 1px solid #e5e7eb;
      border-radius: 16px;
      padding: 16px;
      background: #ffffff;
    }}
    #mlfq-animation-root .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-bottom: 16px;
    }}
    #mlfq-animation-root button,
    #mlfq-animation-root select {{
      border: 1px solid #d1d5db;
      border-radius: 10px;
      padding: 8px 12px;
      background: #ffffff;
      font-size: 14px;
    }}
    #mlfq-animation-root .status {{
      margin-bottom: 12px;
      padding: 12px 14px;
      background: #eff6ff;
      color: #1d4ed8;
      border-radius: 12px;
      min-height: 20px;
    }}
    #mlfq-animation-root .meta {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    #mlfq-animation-root .meta-card {{
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 12px;
      background: #f9fafb;
    }}
    #mlfq-animation-root .label {{
      font-size: 12px;
      color: #6b7280;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    #mlfq-animation-root .value {{
      font-size: 20px;
      font-weight: 700;
      color: #111827;
    }}
    #mlfq-animation-root .queues {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    #mlfq-animation-root .queue-card {{
      border-radius: 14px;
      border: 1px solid #e5e7eb;
      padding: 12px;
      background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
      min-height: 92px;
    }}
    #mlfq-animation-root .queue-title {{
      font-weight: 700;
      margin-bottom: 8px;
      color: #111827;
    }}
    #mlfq-animation-root .queue-items {{
      font-size: 14px;
      color: #374151;
      line-height: 1.5;
      white-space: pre-wrap;
    }}
    #mlfq-animation-root .chart-wrap {{
      border: 1px solid #e5e7eb;
      border-radius: 14px;
      padding: 12px;
      background: #ffffff;
    }}
    #mlfq-animation-root svg {{
      width: 100%;
      height: 320px;
      display: block;
    }}
    #mlfq-animation-root .legend {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 12px;
      font-size: 13px;
      color: #374151;
    }}
    #mlfq-animation-root .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    #mlfq-animation-root .legend-color {{
      width: 12px;
      height: 12px;
      border-radius: 3px;
      display: inline-block;
    }}
    #mlfq-animation-root .hint {{
      margin-top: 12px;
      font-size: 13px;
      color: #6b7280;
    }}
  </style>

  <div class="controls">
    <button id="playBtn">Pause</button>
    <button id="replayBtn">Replay</button>
    <label>Speed
      <select id="speedSelect">
        <option value="1.8">Fast</option>
        <option value="1.0" selected>Normal</option>
        <option value="0.6">Slow</option>
      </select>
    </label>
    <input id="frameSlider" type="range" min="0" max="{max(len(payload) - 1, 0)}" value="0" style="flex:1; min-width:180px;" />
  </div>

  <div class="status" id="statusBox">Preparing animation...</div>

  <div class="meta">
    <div class="meta-card"><div class="label">Current Tick</div><div class="value" id="tickValue">0</div></div>
    <div class="meta-card"><div class="label">Running</div><div class="value" id="runningValue">—</div></div>
    <div class="meta-card"><div class="label">Completed</div><div class="value" id="completedValue">0</div></div>
  </div>

  <div class="queues">
    <div class="queue-card"><div class="queue-title">Q0</div><div class="queue-items" id="queue-q0">—</div></div>
    <div class="queue-card"><div class="queue-title">Q1</div><div class="queue-items" id="queue-q1">—</div></div>
    <div class="queue-card"><div class="queue-title">Q2</div><div class="queue-items" id="queue-q2">—</div></div>
    <div class="queue-card"><div class="queue-title">Completed</div><div class="queue-items" id="queue-completed">—</div></div>
  </div>

  <div class="chart-wrap">
    <svg id="ganttSvg" viewBox="0 0 1200 320" preserveAspectRatio="none" aria-label="MLFQ animation chart"></svg>
    <div class="legend" id="legendBox"></div>
    <div class="hint">Renderer dùng numeric timeline. Không còn phụ thuộc vào Plotly time-axis nên animation không bị “nhảy về 1970”.</div>
  </div>

  <script>
    const frames = {payload_json};
    const colorMap = {color_map_json};
    const maxFinish = {max_finish};
    const maxTick = {max_tick};
    const svg = document.getElementById("ganttSvg");
    const slider = document.getElementById("frameSlider");
    const playBtn = document.getElementById("playBtn");
    const replayBtn = document.getElementById("replayBtn");
    const speedSelect = document.getElementById("speedSelect");
    const statusBox = document.getElementById("statusBox");
    const tickValue = document.getElementById("tickValue");
    const runningValue = document.getElementById("runningValue");
    const completedValue = document.getElementById("completedValue");
    const queueQ0 = document.getElementById("queue-q0");
    const queueQ1 = document.getElementById("queue-q1");
    const queueQ2 = document.getElementById("queue-q2");
    const queueCompleted = document.getElementById("queue-completed");
    const legendBox = document.getElementById("legendBox");

    const lanes = [];
    frames.forEach((frame) => {{
      frame.gantt_log.forEach((entry) => {{
        if (!lanes.includes(entry.task)) lanes.push(entry.task);
      }});
    }});

    const laneHeight = 36;
    const leftPad = 120;
    const topPad = 24;
    const chartWidth = 1000;
    const scale = chartWidth / Math.max(maxFinish, 1);

    function buildLegend() {{
      legendBox.innerHTML = "";
      Object.entries(colorMap).forEach(([queue, color]) => {{
        const item = document.createElement("div");
        item.className = "legend-item";
        item.innerHTML = `<span class="legend-color" style="background:${{color}}"></span><span>${{queue}}</span>`;
        legendBox.appendChild(item);
      }});
    }}

    function axisLabel(value) {{
      return value.toString();
    }}

    function drawChart(frame) {{
      svg.innerHTML = "";
      const totalHeight = Math.max(280, lanes.length * laneHeight + 48);
      svg.setAttribute("viewBox", `0 0 1200 ${{totalHeight}}`);

      lanes.forEach((lane, index) => {{
        const y = topPad + index * laneHeight;
        const laneLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
        laneLabel.setAttribute("x", "12");
        laneLabel.setAttribute("y", String(y + 18));
        laneLabel.setAttribute("fill", "#374151");
        laneLabel.setAttribute("font-size", "13");
        laneLabel.textContent = lane;
        svg.appendChild(laneLabel);

        const guide = document.createElementNS("http://www.w3.org/2000/svg", "line");
        guide.setAttribute("x1", String(leftPad));
        guide.setAttribute("x2", String(leftPad + chartWidth));
        guide.setAttribute("y1", String(y + 26));
        guide.setAttribute("y2", String(y + 26));
        guide.setAttribute("stroke", "#f3f4f6");
        guide.setAttribute("stroke-width", "1");
        svg.appendChild(guide);
      }});

      const axisY = topPad + lanes.length * laneHeight + 16;
      const axis = document.createElementNS("http://www.w3.org/2000/svg", "line");
      axis.setAttribute("x1", String(leftPad));
      axis.setAttribute("x2", String(leftPad + chartWidth));
      axis.setAttribute("y1", String(axisY));
      axis.setAttribute("y2", String(axisY));
      axis.setAttribute("stroke", "#111827");
      axis.setAttribute("stroke-width", "1.5");
      svg.appendChild(axis);

      const tickCount = Math.min(10, Math.max(maxFinish, 1));
      const tickStep = Math.max(1, Math.ceil(maxFinish / tickCount));
      for (let tick = 0; tick <= maxFinish; tick += tickStep) {{
        const x = leftPad + tick * scale;
        const tickLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
        tickLine.setAttribute("x1", String(x));
        tickLine.setAttribute("x2", String(x));
        tickLine.setAttribute("y1", String(axisY));
        tickLine.setAttribute("y2", String(axisY + 6));
        tickLine.setAttribute("stroke", "#111827");
        tickLine.setAttribute("stroke-width", "1");
        svg.appendChild(tickLine);

        const tickLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
        tickLabel.setAttribute("x", String(x));
        tickLabel.setAttribute("y", String(axisY + 20));
        tickLabel.setAttribute("text-anchor", "middle");
        tickLabel.setAttribute("fill", "#4b5563");
        tickLabel.setAttribute("font-size", "12");
        tickLabel.textContent = axisLabel(tick);
        svg.appendChild(tickLabel);
      }}

      frame.gantt_log.forEach((entry) => {{
        const laneIndex = lanes.indexOf(entry.task);
        if (laneIndex === -1) return;
        const y = topPad + laneIndex * laneHeight + 6;
        const x = leftPad + entry.start * scale;
        const width = Math.max(4, (entry.finish - entry.start) * scale);

        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", String(x));
        rect.setAttribute("y", String(y));
        rect.setAttribute("width", String(width));
        rect.setAttribute("height", "20");
        rect.setAttribute("rx", "6");
        rect.setAttribute("fill", colorMap[entry.queue] || "#9ca3af");
        rect.setAttribute("opacity", "0.92");
        svg.appendChild(rect);
      }});
    }}

    function renderFrame(index) {{
      const frame = frames[index];
      if (!frame) return;
      slider.value = index;
      statusBox.textContent = frame.status;
      tickValue.textContent = `${{frame.time_current}} / ${{maxTick}}`;
      runningValue.textContent = frame.running_pid ? `${{frame.running_pid}} (${{frame.running_queue}})` : "—";
      completedValue.textContent = String(frame.completed_pids.length);
      queueQ0.textContent = frame.queue_snapshot.Q0.length ? frame.queue_snapshot.Q0.join("\\n") : "—";
      queueQ1.textContent = frame.queue_snapshot.Q1.length ? frame.queue_snapshot.Q1.join("\\n") : "—";
      queueQ2.textContent = frame.queue_snapshot.Q2.length ? frame.queue_snapshot.Q2.join("\\n") : "—";
      queueCompleted.textContent = frame.completed_pids.length ? frame.completed_pids.join("\\n") : "—";
      drawChart(frame);
    }}

    let currentIndex = 0;
    let isPlaying = true;
    let timerId = null;

    function scheduleNext() {{
      if (!isPlaying) return;
      if (currentIndex >= frames.length - 1) {{
        playBtn.textContent = "Play";
        isPlaying = false;
        return;
      }}
      const speed = Number(speedSelect.value || "1");
      const delay = Math.max(25, Math.round({DEFAULT_ANIMATION_DELAY_MS} / speed));
      timerId = window.setTimeout(() => {{
        currentIndex += 1;
        renderFrame(currentIndex);
        scheduleNext();
      }}, delay);
    }}

    playBtn.addEventListener("click", () => {{
      if (isPlaying) {{
        isPlaying = false;
        playBtn.textContent = "Play";
        if (timerId !== null) window.clearTimeout(timerId);
        return;
      }}
      isPlaying = true;
      playBtn.textContent = "Pause";
      scheduleNext();
    }});

    replayBtn.addEventListener("click", () => {{
      if (timerId !== null) window.clearTimeout(timerId);
      currentIndex = 0;
      renderFrame(currentIndex);
      isPlaying = true;
      playBtn.textContent = "Pause";
      scheduleNext();
    }});

    slider.addEventListener("input", (event) => {{
      const nextIndex = Number(event.target.value);
      currentIndex = nextIndex;
      renderFrame(currentIndex);
      if (timerId !== null) window.clearTimeout(timerId);
      if (isPlaying) scheduleNext();
    }});

    speedSelect.addEventListener("change", () => {{
      if (isPlaying) {{
        if (timerId !== null) window.clearTimeout(timerId);
        scheduleNext();
      }}
    }});

    buildLegend();
    renderFrame(0);
    scheduleNext();
  </script>
</div>
"""


def render_simulation_animation(frames: list[SimulationFrame]) -> None:
    if not frames:
        return

    st.subheader("Animation mô phỏng")
    html = _build_animation_document(frames, DEFAULT_ANIMATION_DELAY_MS)
    height = max(760, 420 + len(frames[-1].queue_snapshot) * 24)
    components.html(html, height=height, scrolling=False)
