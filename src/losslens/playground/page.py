"""The one self-contained Playground page: inline CSS, inline JS, embedded ticks."""

from __future__ import annotations

PAGE_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LossLens Playground</title>
<style>
:root {
  color-scheme: dark;
  --bg: #070a0c;
  --panel: #0c1115;
  --panel-2: #10171c;
  --line: #1c272e;
  --line-soft: #141d23;
  --text: #d7e0e6;
  --muted: #7f909c;
  --dim: #53616b;
  --gold: #d8a84e;
  --green: #5fd38a;
  --red: #d97a7a;
  --blue: #7aa2f7;
  --orange: #e08a6a;
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
html, body { height: 100%; margin: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
  font-size: 13px;
  overflow: hidden;
}
button, input, select { font: inherit; color: inherit; }
button { cursor: pointer; }
h2 {
  margin: 0 0 8px;
  color: var(--muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .15em;
  text-transform: uppercase;
}
.app {
  display: grid;
  grid-template-rows: 50px 42px minmax(0, 1fr);
  height: 100vh;
}
.top {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 16px;
  border-bottom: 1px solid var(--line);
  background: linear-gradient(180deg, #0d1419, #090e12);
}
.brand { font-weight: 700; letter-spacing: .12em; white-space: nowrap; }
.brand span { color: var(--gold); }
.brand small {
  margin-left: 8px;
  color: var(--muted);
  font-weight: 400;
  letter-spacing: .04em;
}
.dataset {
  color: var(--muted);
  font-family: Tahoma, Arial, sans-serif;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.paused {
  margin-left: auto;
  padding: 5px 10px;
  border: 1px solid #5e4a22;
  border-radius: 4px;
  background: #171208;
  color: var(--gold);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .18em;
  white-space: nowrap;
}
.tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  border-bottom: 1px solid var(--line);
  background: #090e12;
  overflow-x: auto;
}
.tab-list { display: flex; gap: 5px; min-width: 0; }
.tab {
  max-width: 190px;
  padding: 6px 11px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #0e151a;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tab:hover { border-color: #33454f; color: var(--text); }
.tab.active {
  border-color: #6b5324;
  background: #171208;
  color: var(--gold);
}
.tab-tools { display: flex; gap: 5px; margin-left: auto; }
.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 356px;
  min-height: 0;
}
.chart-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}
.chart-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 8px 14px;
  border-bottom: 1px solid var(--line-soft);
  background: #080d10;
}
.chart-symbol {
  font-family: Tahoma, Arial, sans-serif;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: .06em;
}
.chart-sub {
  margin-top: 2px;
  color: var(--muted);
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.legend { display: flex; gap: 14px; color: var(--muted); font-size: 10px; }
.legend-item { display: inline-flex; align-items: center; gap: 5px; }
.swatch { width: 14px; height: 2px; display: inline-block; }
.swatch.bid { background: var(--green); }
.swatch.pred { background: var(--blue); }
.swatch.both { background: linear-gradient(90deg, var(--green), var(--red)); }
.canvas-wrap { position: relative; flex: 1; min-height: 0; background: var(--bg); }
#chart { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.canvas-wrap.drawing #chart { cursor: crosshair; }
.chart-hint {
  position: absolute;
  left: 14px;
  top: 10px;
  padding: 4px 8px;
  border: 1px solid #2f4468;
  border-radius: 4px;
  background: rgba(9, 16, 26, .88);
  color: var(--blue);
  font-size: 10px;
  pointer-events: none;
}
.chart-hint.hidden { display: none; }
.future-note {
  position: absolute;
  right: 98px;
  top: 10px;
  color: var(--dim);
  font-family: Tahoma, Arial, sans-serif;
  font-size: 9px;
  letter-spacing: .14em;
  pointer-events: none;
}
.chart-foot {
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 6px 14px;
  border-top: 1px solid var(--line-soft);
  color: var(--muted);
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.chart-foot span:last-child { margin-left: auto; }
.side {
  display: flex;
  flex-direction: column;
  gap: 9px;
  padding: 9px;
  border-left: 1px solid var(--line);
  background: #080c0f;
  overflow-y: auto;
}
.card {
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: linear-gradient(180deg, #0d1318, #0a0f12);
}
.row { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.btn {
  padding: 6px 9px;
  border: 1px solid #26333b;
  border-radius: 5px;
  background: #111a20;
  color: var(--text);
  font-size: 12px;
}
.btn:hover { border-color: #3a4c57; background: #162129; }
.btn:disabled { opacity: .38; cursor: not-allowed; }
.btn.small { padding: 4px 7px; font-size: 11px; }
.btn.gold { border-color: #5e4a22; background: #171208; color: var(--gold); }
.btn.buy { border-color: #2c5e42; background: #0d1a13; color: var(--green); flex: 1; }
.btn.sell { border-color: #643c34; background: #1a100e; color: var(--orange); flex: 1; }
.btn.active { box-shadow: inset 0 0 0 1px var(--gold); color: var(--gold); }
.field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 6px 0;
  color: var(--muted);
  font-size: 11px;
}
.field input, .field select {
  width: 112px;
  padding: 5px 7px;
  border: 1px solid #26333b;
  border-radius: 4px;
  background: #0a1014;
  color: var(--text);
  font-family: Tahoma, Arial, sans-serif;
  font-size: 11px;
}
.field input:focus, .field select:focus { outline: 1px solid #4a6070; }
.field-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.field-pair .field input { width: 72px; }
.quote {
  display: flex;
  gap: 10px;
  justify-content: space-between;
  margin-bottom: 6px;
  padding: 6px 8px;
  border: 1px solid var(--line-soft);
  border-radius: 5px;
  background: #0a0f12;
  color: var(--muted);
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.quote b { color: var(--text); font-size: 12px; }
.message { min-height: 15px; margin-top: 5px; color: var(--muted); font-size: 10px; }
.message.good { color: var(--green); }
.message.bad { color: var(--red); }
.message.info { color: var(--gold); }
.equity {
  display: grid;
  gap: 3px;
  margin-top: 6px;
  padding: 7px 8px;
  border: 1px solid var(--line-soft);
  border-radius: 5px;
  background: #0a0f12;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 11px;
}
.equity div { display: flex; justify-content: space-between; }
.equity span { color: var(--muted); }
.equity .total { margin-top: 3px; padding-top: 4px; border-top: 1px solid var(--line); }
.equity .total b { color: var(--gold); }
.up { color: var(--green); }
.down { color: var(--red); }
.tickets { margin-top: 7px; }
.ticket {
  margin-top: 5px;
  padding: 6px 7px;
  border: 1px solid var(--line-soft);
  border-radius: 5px;
  background: #0b1115;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.ticket-top { display: flex; justify-content: space-between; gap: 6px; }
.ticket .side { font-weight: 700; }
.ticket .side.buy { color: var(--green); }
.ticket .side.sell { color: var(--orange); }
.ticket .detail { margin-top: 3px; color: var(--muted); }
.ticket .ticket-actions { display: flex; justify-content: flex-end; margin-top: 4px; }
.fixed-move { margin-top: 8px; padding-top: 7px; border-top: 1px solid var(--line); }
.preview-row {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
  color: var(--muted);
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.prediction-stats {
  margin-top: 7px;
  padding: 6px 7px;
  border: 1px solid var(--line-soft);
  border-radius: 5px;
  background: #0a0f12;
  color: var(--muted);
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
  line-height: 1.55;
}
.meta-line { margin-top: 7px; color: var(--dim); font-size: 10px; line-height: 1.45; }
.disclaimer {
  padding: 2px 3px 0;
  color: var(--dim);
  font-size: 10px;
  line-height: 1.45;
  text-align: center;
}
.modal {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(2, 5, 7, .8);
}
.modal.hidden { display: none; }
.score-card {
  width: min(980px, 96vw);
  max-height: 88vh;
  padding: 18px;
  border: 1px solid #33454f;
  border-radius: 9px;
  background: #0b1115;
  box-shadow: 0 24px 80px rgba(0, 0, 0, .65);
}
.score-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 12px;
}
.score-head h2 { margin: 0; color: var(--text); font-size: 18px; letter-spacing: .02em; }
.eyebrow { color: var(--gold); font-size: 10px; letter-spacing: .16em; text-transform: uppercase; }
.score-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-family: Tahoma, Arial, sans-serif; }
th {
  padding: 7px 8px;
  border-bottom: 1px solid #33454f;
  color: var(--muted);
  font-size: 10px;
  font-weight: 400;
  letter-spacing: .06em;
  text-align: right;
  white-space: nowrap;
}
th:first-child, td:first-child { text-align: left; }
td { padding: 8px; border-bottom: 1px solid var(--line-soft); font-size: 11px; text-align: right; }
tr.winner td { color: var(--gold); }
.foot { margin: 12px 0 0; color: var(--dim); font-size: 10px; line-height: 1.5; }
@media (max-width: 900px) {
  body { overflow: auto; }
  .app { height: auto; min-height: 100vh; grid-template-rows: 50px auto auto; }
  .workspace { grid-template-columns: 1fr; }
  .chart-panel { height: 54vh; }
  .side { border-left: 0; border-top: 1px solid var(--line); }
}
/* MT4-native skin: classic gray chrome, Tahoma, black chart, square bevels. */
html, body {
  background: #262626;
  color: #e6e6e6;
  font-family: Tahoma, "Segoe UI", Arial, sans-serif;
  font-size: 11px;
}
.app { grid-template-rows: 30px 24px minmax(0, 1fr) 20px; }
.top {
  gap: 14px;
  padding: 0 8px;
  border-bottom: 1px solid #111;
  background: #3f3f3f;
}
.brand {
  color: #f0f0f0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .02em;
}
.brand span { color: #d8a84e; }
.brand small {
  margin-left: 7px;
  color: #b8b8b8;
  font-size: 11px;
  letter-spacing: 0;
}
.dataset {
  color: #c8c8c8;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 11px;
}
.paused {
  padding: 2px 8px;
  border: 1px solid #a05050;
  border-radius: 0;
  background: #5a1f1f;
  color: #fff;
  font-size: 10px;
  letter-spacing: .08em;
}
.tabs {
  gap: 3px;
  padding: 2px 6px;
  border-bottom: 1px solid #111;
  background: #2b2b2b;
}
.tab-list { gap: 2px; }
.tab {
  max-width: 180px;
  padding: 2px 9px;
  border: 1px solid #555;
  border-bottom-color: #222;
  border-radius: 0;
  background: #383838;
  color: #d0d0d0;
  font-size: 11px;
}
.tab:hover { border-color: #777; background: #454545; color: #fff; }
.tab.active {
  border-color: #777;
  border-top: 2px solid #d8a84e;
  background: #4a4a4a;
  color: #fff;
}
.tab-tools { gap: 3px; }
.workspace { grid-template-columns: minmax(0, 1fr) 420px; }
.chart-panel { border-right: 0; }
.chart-head {
  padding: 4px 8px;
  border-bottom: 1px solid #333;
  background: #000;
}
.chart-symbol {
  color: #fff;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}
.chart-sub {
  color: #9a9a9a;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.legend { gap: 10px; color: #b0b0b0; font-size: 10px; }
.swatch.ask { background: #ff4d4d; }
.canvas-wrap { background: #000; }
.chart-hint {
  left: 50%;
  top: 6px;
  bottom: auto;
  transform: translateX(-50%);
  padding: 1px 5px;
  border: 1px solid #2f6fb3;
  border-radius: 0;
  background: #d8e6f2;
  color: #111;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.future-note {
  right: 92px;
  top: 6px;
  color: #777;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 9px;
  letter-spacing: .08em;
}
.side {
  gap: 4px;
  padding: 4px;
  border-left: 1px solid #111;
  background: #2f2f2f;
}
.card {
  padding: 0 0 6px;
  border: 1px solid #555;
  border-radius: 0;
  background: #2f2f2f;
}
.card h2 {
  margin: 0 0 6px;
  padding: 3px 6px;
  border-bottom: 1px solid #222;
  background: #3c3c3c;
  color: #f0f0f0;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: none;
}
.card > *:not(h2) { margin-left: 6px; margin-right: 6px; }
.row { gap: 3px; }
.btn {
  padding: 3px 7px;
  border: 1px solid #666;
  border-top-color: #888;
  border-left-color: #888;
  border-bottom-color: #222;
  border-right-color: #222;
  border-radius: 0;
  background: #3c3c3c;
  color: #f0f0f0;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 11px;
}
.btn:hover { border-color: #888; background: #484848; }
.btn:active {
  border-top-color: #222;
  border-left-color: #222;
  border-bottom-color: #888;
  border-right-color: #888;
  background: #333;
}
.btn:disabled { opacity: .4; }
.btn.small { padding: 2px 5px; font-size: 10px; }
.btn.gold { border-color: #6b5324; background: #4a3a18; color: #ffd700; }
.btn.buy { border-color: #4a7fae; background: #2f5f8f; color: #fff; }
.btn.sell { border-color: #ae4a4a; background: #8f2f2f; color: #fff; }
.btn.active {
  box-shadow: none;
  border-color: #d8a84e;
  color: #ffd700;
  background: #4a3a18;
}
.field { margin: 4px 0; color: #c8c8c8; font-size: 11px; }
.field input, .field select {
  width: 108px;
  padding: 2px 4px;
  border: 1px solid #111;
  border-top-color: #585858;
  border-left-color: #585858;
  border-radius: 0;
  background: #1e1e1e;
  color: #fff;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 11px;
}
.field input:focus, .field select:focus { outline: 1px solid #888; }
.field-pair { gap: 4px; }
.field-pair .field input { width: 68px; }
.quote {
  gap: 6px;
  margin-bottom: 4px;
  padding: 3px 5px;
  border: 1px solid #111;
  border-top-color: #585858;
  border-radius: 0;
  background: #1e1e1e;
  color: #b0b0b0;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.quote b { color: #fff; font-size: 11px; }
.message { min-height: 14px; margin-top: 3px; color: #c8c8c8; font-size: 10px; }
.message.good { color: #00d000; }
.message.bad { color: #ff6060; }
.message.info { color: #ffd700; }
.equity {
  gap: 1px;
  margin-top: 4px;
  padding: 4px 5px;
  border: 1px solid #111;
  border-top-color: #585858;
  border-radius: 0;
  background: #1e1e1e;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.equity .total { border-top: 1px solid #444; }
.equity .total b { color: #ffd700; }
.up { color: #00d000; }
.down { color: #ff6060; }
.tickets { margin-top: 4px; overflow-x: auto; }
.ticket-table { width: 100%; border-collapse: collapse; font-family: Tahoma, Arial, sans-serif; }
.ticket-table th {
  padding: 2px 3px;
  border: 1px solid #444;
  background: #3a3a3a;
  color: #d8d8d8;
  font-size: 10px;
  font-weight: 700;
  text-align: right;
  white-space: nowrap;
}
.ticket-table td {
  padding: 2px 3px;
  border-bottom: 1px solid #3d3d3d;
  color: #e0e0e0;
  font-size: 10px;
  text-align: right;
  white-space: nowrap;
}
.ticket-table th:first-child, .ticket-table td:first-child,
.ticket-table th:nth-child(2), .ticket-table td:nth-child(2) { text-align: left; }
.ticket-table tr.closed { background: #2a2a2a; }
.ticket-table td.side-buy { color: #6aa9e0; }
.ticket-table td.side-sell { color: #e08a8a; }
.ticket-table .sub { color: #999; font-size: 9px; }
.ticket-table .ticket-action { padding: 1px 2px; text-align: center; }
.ticket-table .ticket-action .btn { padding: 1px 4px; font-size: 9px; }
.empty-note { padding: 5px; color: #999; font-size: 10px; }
.fixed-move { margin-top: 5px; padding-top: 4px; border-top: 1px solid #444; }
.preview-row {
  padding: 1px 0;
  color: #b0b0b0;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.prediction-stats {
  margin-top: 5px;
  padding: 4px 5px;
  border: 1px solid #111;
  border-top-color: #585858;
  border-radius: 0;
  background: #1e1e1e;
  color: #c8c8c8;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.meta-line { margin-top: 5px; color: #999; font-size: 10px; }
.disclaimer { color: #888; font-size: 10px; }
.statusbar {
  display: flex;
  align-items: center;
  height: 24px;
  border-top: 1px solid #111;
  background: #c0c0c0;
  color: #111;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 10px;
}
.statusbar span { padding: 0 8px; border-right: 1px solid #8a8a8a; line-height: 23px; }
.statusbar .status-right {
  margin-left: auto;
  border-right: 0;
  border-left: 1px solid #8a8a8a;
}
.modal { background: rgba(0, 0, 0, .75); }
.score-card {
  border: 1px solid #777;
  border-radius: 0;
  background: #2f2f2f;
  box-shadow: none;
}
.score-head h2 {
  color: #fff;
  font-family: Tahoma, Arial, sans-serif;
  font-size: 15px;
  letter-spacing: 0;
}
.eyebrow { color: #ffd700; font-size: 10px; letter-spacing: .04em; }
table { font-family: Tahoma, Arial, sans-serif; }
th { border-bottom: 1px solid #666; color: #d0d0d0; font-size: 10px; }
td { border-bottom: 1px solid #444; font-size: 11px; }
tr.winner td { color: #ffd700; }
.foot { color: #999; font-size: 10px; }
.side { scrollbar-color: #4a4a4a #2b2b2b; scrollbar-width: thin; }
.side::-webkit-scrollbar { width: 14px; height: 14px; }
.side::-webkit-scrollbar-track { background: #2b2b2b; border-left: 1px solid #111; }
.side::-webkit-scrollbar-thumb { background: #4a4a4a; border: 1px solid #666; }
.score-scroll { scrollbar-color: #4a4a4a #2b2b2b; scrollbar-width: thin; }
.score-scroll::-webkit-scrollbar { height: 14px; }
.score-scroll::-webkit-scrollbar-track { background: #2b2b2b; }
.score-scroll::-webkit-scrollbar-thumb { background: #4a4a4a; border: 1px solid #666; }
.ticket-table tbody tr:hover { background: #3a3a3a; }
@media (max-width: 900px) {
  .app { height: auto; min-height: 100vh; grid-template-rows: 30px auto auto auto; }
  .workspace { grid-template-columns: 1fr; }
  .chart-panel { height: 54vh; }
  .side { border-left: 0; border-top: 1px solid #111; }
  .statusbar { position: sticky; bottom: 0; }
}
/* MT4 classic chrome, using the same tokens as the app template. */
html, body { background: #f0f0f0; color: #111; }
.top { background: #f0f0f0; border-bottom: 1px solid #a0a0a0; }
.brand { color: #111; }
.brand span { color: #2f6fb3; }
.brand small { color: #666; }
.dataset { color: #666; }
.paused { border-color: #700000; background: #c00000; color: #ffffff; }
.tabs { background: #f0f0f0; border-bottom: 1px solid #a0a0a0; }
.tab { background: #fbfbfb; border: 1px solid #9a9a9a; color: #111; }
.tab:hover { background: #e8f1fa; border-color: #888888; color: #000000; }
.tab.active {
  background: #ffffff;
  border-color: #9a9a9a;
  border-top: 2px solid #2f6fb3;
  color: #000000;
  font-weight: 700;
}
.side { background: #f0f0f0; border-left: 1px solid #a0a0a0; }
.card { background: #f0f0f0; border: 1px solid #a0a0a0; }
.card h2 { background: #e4e4e4; border-bottom: 1px solid #a0a0a0; color: #111; }
.btn {
  background: #fbfbfb;
  color: #111;
  border: 1px solid #9a9a9a;
  border-top-color: #ffffff;
  border-left-color: #ffffff;
  border-bottom-color: #666666;
  border-right-color: #666666;
}
.btn:hover { background: #e8f1fa; border-color: #9a9a9a; }
.btn:active {
  background: #d8e6f2;
  border-top-color: #666666;
  border-left-color: #666666;
  border-bottom-color: #ffffff;
  border-right-color: #ffffff;
}
.btn.gold { background: #2f6fb3; border-color: #245786; color: #ffffff; }
.btn.buy { background: #2f6fb3; border-color: #245786; color: #ffffff; }
.btn.sell { background: #a53a3a; border-color: #7a2626; color: #ffffff; }
.btn.active {
  background: #2f6fb3;
  border-color: #245786;
  color: #ffffff;
  box-shadow: none;
}
.field { color: #111; }
.field input, .field select {
  background: #ffffff;
  color: #000000;
  border: 1px solid #b0b0b0;
  border-top-color: #888888;
  border-left-color: #888888;
}
.field input:focus, .field select:focus { outline: 1px solid #2f6fb3; }
.quote { background: #ffffff; border: 1px solid #a0a0a0; color: #666666; }
.quote b { color: #000000; }
.message { color: #333333; }
.message.good { color: #008000; }
.message.bad { color: #c00000; }
.message.info { color: #2f6fb3; }
.equity { background: #ffffff; border: 1px solid #a0a0a0; color: #111; }
.equity span { color: #666666; }
.equity .total { border-top: 1px solid #c0c0c0; }
.equity .total b { color: #000000; }
.up { color: #008000; }
.down { color: #c00000; }
.ticket-table th { background: #e4e4e4; border: 1px solid #a0a0a0; color: #111; }
.tickets { background: #ffffff; border: 1px solid #a0a0a0; }
.ticket-table td { border-bottom: 1px solid #e0e0e0; color: #111; }
.ticket-table tr.closed { background: #f7f7f7; }
.ticket-table td.side-buy { color: #2f6fb3; }
.ticket-table td.side-sell { color: #a53a3a; }
.ticket-table .sub { color: #666666; }
.ticket-table tbody tr:hover { background: #e8f1fa; }
.empty-note { color: #666666; }
.fixed-move { border-top: 1px solid #c0c0c0; }
.preview-row { color: #333333; }
.prediction-stats { background: #ffffff; border: 1px solid #a0a0a0; color: #333333; }
.meta-line { color: #666666; }
.disclaimer { color: #666666; }
.statusbar {
  height: 20px;
  background: #f0f0f0;
  color: #666666;
  border-top: 1px solid #a0a0a0;
}
.statusbar span { border-right: 1px solid #a0a0a0; line-height: 19px; }
.statusbar .status-right { border-left: 1px solid #a0a0a0; border-right: 0; }
.score-card { background: #f0f0f0; border: 1px solid #777777; }
.score-card table { background: #ffffff; }
.score-card th { background: #e4e4e4; }
.score-head {
  margin: -18px -18px 12px;
  padding: 5px 8px;
  background: #2f6fb3;
  color: #ffffff;
}
.score-head h2 { color: #ffffff; }
.score-head .btn { background: #fbfbfb; color: #111; }
.eyebrow { color: #ffffff; }
.tr.winner td { color: #2f6fb3; font-weight: 700; }
th { border-bottom: 1px solid #a0a0a0; color: #111; }
td { border-bottom: 1px solid #c0c0c0; color: #111; }
.foot { color: #666666; }
.side { scrollbar-color: #a0a0a0 #f0f0f0; }
.side::-webkit-scrollbar-track { background: #f0f0f0; border-left: 1px solid #a0a0a0; }
.side::-webkit-scrollbar-thumb { background: #c0c0c0; border: 1px solid #9a9a9a; }
.score-scroll { scrollbar-color: #a0a0a0 #f0f0f0; }
.score-scroll::-webkit-scrollbar-track { background: #f0f0f0; }
.score-scroll::-webkit-scrollbar-thumb { background: #c0c0c0; border: 1px solid #9a9a9a; }
</style>
</head>
<body>
<div class="app">
  <header class="top">
    <div class="brand">LOSS<span>LENS</span><small>Playground</small></div>
    <div class="dataset" id="dataset-line"></div>
    <div class="paused" id="paused-badge">PAUSED</div>
  </header>
  <nav class="tabs" aria-label="Scenarios">
    <div class="tab-list" id="tabs"></div>
    <div class="tab-tools">
      <button class="btn small" id="add-tab">+ Add</button>
      <button class="btn small" id="rename-tab">Rename</button>
      <button class="btn small" id="duplicate-tab">Duplicate</button>
      <button class="btn small" id="delete-tab">Delete</button>
    </div>
  </nav>
  <main class="workspace">
    <section class="chart-panel">
      <div class="chart-head">
        <div>
          <div class="chart-symbol" id="chart-symbol">XAUUSD</div>
          <div class="chart-sub" id="chart-sub">Tick chart</div>
        </div>
        <div class="legend">
          <span class="legend-item"><i class="swatch bid"></i>Bid</span>
          <span class="legend-item"><i class="swatch ask"></i>Ask</span>
          <span class="legend-item"><i class="swatch pred"></i>Prediction</span>
          <span class="legend-item"><i class="swatch both"></i>Both ways</span>
        </div>
      </div>
      <div class="canvas-wrap" id="canvas-wrap">
        <canvas id="chart"></canvas>
        <div class="chart-hint hidden" id="chart-hint">Draw mode: click future ticks</div>
        <div class="future-note">FUTURE HIDDEN</div>
      </div>
    </section>
    <aside class="side">
      <section class="card">
        <h2>Playback</h2>
        <div class="row">
          <button class="btn" id="next1">Next tick</button>
          <button class="btn" id="next10">Next 10</button>
          <button class="btn" id="next100">Next 100</button>
          <button class="btn" id="reset">Reset</button>
        </div>
        <div class="meta-line">Space reveals one tick. No auto-play.
          Every tab shares this cursor.</div>
      </section>
      <section class="card">
        <h2>Freeze &amp; trade</h2>
        <div class="quote">
          <span>Bid <b id="bid">-</b></span>
          <span>Ask <b id="ask">-</b></span>
          <span>Spread <b id="spread">-</b></span>
        </div>
        <label class="field">Volume
          <input id="lots" type="number" min="0.01" step="0.01" value="0.01">
        </label>
        <div class="field-pair">
          <label class="field">SL
            <input id="sl" type="number" step="0.01" placeholder="none">
          </label>
          <label class="field">TP
            <input id="tp" type="number" step="0.01" placeholder="none">
          </label>
        </div>
        <div class="row">
          <button class="btn buy" id="buy">Buy</button>
          <button class="btn sell" id="sell">Sell</button>
        </div>
        <div class="message" id="message"></div>
        <div class="tickets">
          <table class="ticket-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>Size</th>
                <th>Price</th>
                <th>S/L</th>
                <th>T/P</th>
                <th>Profit</th>
                <th></th>
              </tr>
            </thead>
            <tbody id="ticket-body"></tbody>
          </table>
          <div class="empty-note" id="ticket-empty">No open positions.</div>
        </div>
        <div class="equity">
          <div><span>Balance</span><b id="balance">$10,000.00</b></div>
          <div><span>Floating</span><b id="floating">$0.00</b></div>
          <div class="total"><span>Equity</span><b id="equity">$10,000.00</b></div>
        </div>
        <div class="fixed-move">
          <label class="field">Fixed move +/-$
            <input id="move-size" type="number" min="0.01" step="0.01" value="1.00">
          </label>
          <div id="move-preview"></div>
        </div>
      </section>
      <section class="card">
        <h2>Prediction</h2>
        <div class="row">
          <button class="btn" id="draw-toggle">Draw mode</button>
          <button class="btn" id="both-ways">Both ways</button>
          <button class="btn" id="pred-undo">Undo</button>
          <button class="btn" id="pred-clear">Clear</button>
        </div>
        <div class="prediction-stats" id="pred-stats">No prediction points.</div>
      </section>
      <section class="card">
        <h2>Grid &amp; session</h2>
        <label class="field">Price grid
          <select id="grid-step">
            <option value="0.01">0.01</option>
            <option value="0.05">0.05</option>
            <option value="0.10" selected>0.10</option>
            <option value="0.25">0.25</option>
            <option value="0.50">0.50</option>
            <option value="1.00">1.00</option>
            <option value="custom">Custom</option>
          </select>
        </label>
        <label class="field" id="custom-wrap" hidden>Custom step
          <input id="grid-custom" type="number" min="0.001" step="0.001" value="0.10">
        </label>
        <div class="row">
          <button class="btn gold" id="run-end">Run to end</button>
        </div>
        <div class="row">
          <button class="btn small" id="export-json">Export JSON</button>
          <button class="btn small" id="import-json">Import JSON</button>
        </div>
        <input id="import-file" type="file" accept=".json,application/json" hidden>
        <div class="meta-line" id="storage-note">Scenarios auto-save in this browser.</div>
      </section>
      <div class="disclaimer">A local thinking tool. No broker, no account, no network.</div>
    </aside>
  </main>
  <footer class="statusbar">
    <span id="cursor-line">Tick 1 / 1</span>
    <span id="time-line">00:00:00 UTC</span>
    <span id="reveal-line">1 of 1 revealed</span>
    <span class="status-right">PAUSED · LOCAL FILE</span>
  </footer>
</div>
<div class="modal hidden" id="scoreboard" role="dialog" aria-modal="true">
  <div class="score-card">
    <div class="score-head">
      <div>
        <div class="eyebrow">Run to end</div>
        <h2>Scoreboard</h2>
      </div>
      <button class="btn" id="score-close">Close</button>
    </div>
    <div class="score-scroll">
      <table>
        <thead>
          <tr>
            <th>Scenario</th>
            <th>Final equity</th>
            <th>Max drawdown</th>
            <th>Tickets</th>
            <th>Win rate</th>
            <th>Prediction MAE</th>
            <th>Direction hit</th>
          </tr>
        </thead>
        <tbody id="score-body"></tbody>
      </table>
    </div>
    <p class="foot">Sorted by final equity. Win rate counts closed tickets only.
      MAE and direction use every prediction point the cursor has reached.</p>
  </div>
</div>
<script id="tick-data" type="application/json">__TICK_DATA__</script>
<script>
(function () {
  "use strict";

  const DATA = JSON.parse(document.getElementById("tick-data").textContent);
  const TICKS = DATA.ticks;
  const N = TICKS.length;
  const START_BALANCE = Number(DATA.startBalance) || 10000;
  const CONTRACT_SIZE = Number(DATA.contractSize) || 100;
  const STORAGE_FORMAT = "losslens.playground";
  const STORAGE_VERSION = 1;
  const STORAGE_KEY = "losslens.playground.v1." + DATA.datasetId;
  const STEP_CHOICES = [0.01, 0.05, 0.10, 0.25, 0.50, 1.00];
  const C = {
    bg: "#000000",
    grid: "rgba(160, 160, 160, 0.22)",
    gridStrong: "#444444",
    axis: "#a0a0a0",
    dim: "#666666",
    bid: "#00c000",
    ask: "#ff4040",
    cursor: "#2f6fb3",
    predict: "#4a9eff",
    ghostUp: "#00c000",
    ghostDown: "#ff4040",
    buy: "#2f6fb3",
    sell: "#a53a3a",
    future: "rgba(255, 255, 255, 0.012)"
  };

  const $ = function (id) { return document.getElementById(id); };
  const canvas = $("chart");
  const ctx = canvas.getContext("2d");
  const el = {
    datasetLine: $("dataset-line"),
    tabs: $("tabs"),
    chartSymbol: $("chart-symbol"),
    chartSub: $("chart-sub"),
    cursorLine: $("cursor-line"),
    timeLine: $("time-line"),
    revealLine: $("reveal-line"),
    bid: $("bid"),
    ask: $("ask"),
    spread: $("spread"),
    lots: $("lots"),
    sl: $("sl"),
    tp: $("tp"),
    message: $("message"),
    balance: $("balance"),
    floating: $("floating"),
    equity: $("equity"),
    ticketBody: $("ticket-body"),
    ticketEmpty: $("ticket-empty"),
    moveSize: $("move-size"),
    movePreview: $("move-preview"),
    drawToggle: $("draw-toggle"),
    bothWays: $("both-ways"),
    predUndo: $("pred-undo"),
    predClear: $("pred-clear"),
    predStats: $("pred-stats"),
    chartHint: $("chart-hint"),
    canvasWrap: $("canvas-wrap"),
    gridStep: $("grid-step"),
    gridCustom: $("grid-custom"),
    customWrap: $("custom-wrap"),
    storageNote: $("storage-note"),
    scoreboard: $("scoreboard"),
    scoreBody: $("score-body")
  };

  const state = {
    cursor: 0,
    gridStep: 0.10,
    lotSize: 0.01,
    moveSize: 1.00,
    drawMode: false,
    bothWays: false,
    scenarios: [],
    activeId: ""
  };
  const view = { width: 1, height: 1 };
  let plot = null;
  let priceMin = 0;
  let priceMax = 1;
  let timeMin = 0;
  let timeMax = 1;
  let idCounter = 0;
  let saveDisabled = false;

  function clamp(value, low, high) {
    return Math.max(low, Math.min(high, value));
  }

  function isFiniteNumber(value) {
    return typeof value === "number" && Number.isFinite(value);
  }

  function pad2(value) {
    return value < 10 ? "0" + value : String(value);
  }

  function makeId(prefix) {
    idCounter += 1;
    return prefix + idCounter.toString(36) + "-" + Date.now().toString(36);
  }

  function emptyScenario(name) {
    return {
      id: makeId("s"),
      name: name,
      tickets: [],
      prediction: emptyPrediction()
    };
  }

  function emptyPrediction() {
    return { anchorIndex: null, anchorPrice: null, points: [] };
  }

  function currentTick() {
    return TICKS[state.cursor];
  }

  function activeScenario() {
    let scenario = null;
    for (let i = 0; i < state.scenarios.length; i += 1) {
      if (state.scenarios[i].id === state.activeId) {
        scenario = state.scenarios[i];
        break;
      }
    }
    if (scenario === null) {
      scenario = state.scenarios[0];
      state.activeId = scenario.id;
    }
    return scenario;
  }

  function stepDecimals(step) {
    const text = String(step);
    const dot = text.indexOf(".");
    if (dot < 0) {
      return 2;
    }
    return clamp(text.length - dot - 1, 2, 4);
  }

  function formatPrice(value) {
    return Number(value).toFixed(stepDecimals(state.gridStep));
  }

  function formatMoney(value) {
    const negative = value < -0.0000001;
    const text = Math.abs(value).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
    return (negative ? "-$" : "$") + text;
  }

  function formatLots(value) {
    return String(Math.round(value * 1000) / 1000);
  }

  function formatClock(ts) {
    const date = new Date(ts);
    return pad2(date.getUTCHours()) + ":" + pad2(date.getUTCMinutes()) + ":" +
      pad2(date.getUTCSeconds());
  }

  function formatShortTime(ts) {
    const date = new Date(ts);
    return pad2(date.getUTCHours()) + ":" + pad2(date.getUTCMinutes());
  }

  function snapPrice(price) {
    const step = state.gridStep;
    return Number((Math.round(price / step) * step).toFixed(6));
  }

  function setMessage(text, kind) {
    el.message.textContent = text;
    el.message.className = "message" + (kind ? " " + kind : "");
  }

  function ticketPnl(ticket, exitPrice) {
    const direction = ticket.side === "buy" ? 1 : -1;
    return (exitPrice - ticket.entry) * direction * ticket.lots * CONTRACT_SIZE;
  }

  function floatingAt(scenario, bid, ask) {
    let total = 0;
    for (let i = 0; i < scenario.tickets.length; i += 1) {
      const ticket = scenario.tickets[i];
      if (ticket.status !== "open") {
        continue;
      }
      total += ticketPnl(ticket, ticket.side === "buy" ? bid : ask);
    }
    return total;
  }

  function floatingNow(scenario) {
    const tick = currentTick();
    return floatingAt(scenario, tick[1], tick[2]);
  }

  function balanceOf(scenario) {
    let total = START_BALANCE;
    for (let i = 0; i < scenario.tickets.length; i += 1) {
      const ticket = scenario.tickets[i];
      if (ticket.status === "closed") {
        total += ticket.realized;
      }
    }
    return total;
  }

  function equityOf(scenario) {
    return balanceOf(scenario) + floatingNow(scenario);
  }

  function scoredPoints(scenario) {
    const prediction = scenario.prediction;
    const points = prediction.points;
    const scored = [];
    const fallbackIndex = prediction.anchorIndex === null ? 0 : prediction.anchorIndex;
    const anchorIndex = clamp(Math.round(fallbackIndex), 0, N - 1);
    for (let i = 0; i < points.length; i += 1) {
      const point = points[i];
      if (point.i > state.cursor) {
        break;
      }
      const previous = i > 0 ? points[i - 1] : null;
      const previousPredicted = previous ? previous.price : prediction.anchorPrice;
      const previousActual = previous ? TICKS[previous.i][1] : TICKS[anchorIndex][1];
      const actual = TICKS[point.i][1];
      const predictedBase = isFiniteNumber(previousPredicted) ? previousPredicted : actual;
      const predictedDirection = Math.sign(point.price - predictedBase);
      const actualDirection = Math.sign(actual - previousActual);
      scored.push({
        point: point,
        actual: actual,
        error: Math.abs(point.price - actual),
        hit: predictedDirection !== 0 && predictedDirection === actualDirection
      });
    }
    return scored;
  }

  function predictionStats(scenario) {
    const scored = scoredPoints(scenario);
    if (scored.length === 0) {
      return { count: 0, mae: null, hitRate: null, hits: 0 };
    }
    let errorSum = 0;
    let hits = 0;
    for (let i = 0; i < scored.length; i += 1) {
      errorSum += scored[i].error;
      if (scored[i].hit) {
        hits += 1;
      }
    }
    return {
      count: scored.length,
      mae: errorSum / scored.length,
      hitRate: hits / scored.length,
      hits: hits
    };
  }

  function ticketStats(scenario) {
    let closed = 0;
    let wins = 0;
    for (let i = 0; i < scenario.tickets.length; i += 1) {
      const ticket = scenario.tickets[i];
      if (ticket.status === "closed") {
        closed += 1;
        if (ticket.realized > 0) {
          wins += 1;
        }
      }
    }
    return {
      total: scenario.tickets.length,
      closed: closed,
      wins: wins,
      winRate: closed === 0 ? null : wins / closed
    };
  }

  function maxDrawdownOf(scenario) {
    let peak = START_BALANCE;
    let worst = 0;
    const tickets = scenario.tickets;
    for (let k = 0; k < N; k += 1) {
      const tick = TICKS[k];
      let realized = 0;
      let floating = 0;
      for (let i = 0; i < tickets.length; i += 1) {
        const ticket = tickets[i];
        if (ticket.status === "closed" && ticket.closeIndex <= k) {
          realized += ticket.realized;
        } else if (ticket.openIndex <= k) {
          floating += ticketPnl(ticket, ticket.side === "buy" ? tick[1] : tick[2]);
        }
      }
      const equity = START_BALANCE + realized + floating;
      if (equity > peak) {
        peak = equity;
      }
      const drawdown = peak - equity;
      if (drawdown > worst) {
        worst = drawdown;
      }
    }
    return worst;
  }

  function settle(ticket, price, reason, index) {
    ticket.status = "closed";
    ticket.closeIndex = index;
    ticket.closePrice = price;
    ticket.closeReason = reason;
    ticket.realized = ticketPnl(ticket, price);
  }

  function openTicket(side) {
    const lots = Number(el.lots.value);
    if (!isFiniteNumber(lots) || lots <= 0) {
      setMessage("Lot size must be a positive number.", "bad");
      return;
    }
    const slResult = optionalPrice(el.sl, "SL");
    if (!slResult.ok) {
      return;
    }
    const tpResult = optionalPrice(el.tp, "TP");
    if (!tpResult.ok) {
      return;
    }
    const tick = currentTick();
    const entry = side === "buy" ? tick[2] : tick[1];
    if (slResult.value !== null) {
      if (side === "buy" && slResult.value >= entry) {
        setMessage("A buy needs SL below its ask entry.", "bad");
        return;
      }
      if (side === "sell" && slResult.value <= entry) {
        setMessage("A sell needs SL above its bid entry.", "bad");
        return;
      }
    }
    if (tpResult.value !== null) {
      if (side === "buy" && tpResult.value <= entry) {
        setMessage("A buy needs TP above its ask entry.", "bad");
        return;
      }
      if (side === "sell" && tpResult.value >= entry) {
        setMessage("A sell needs TP below its bid entry.", "bad");
        return;
      }
    }
    const scenario = activeScenario();
    const ticket = {
      id: makeId("t"),
      side: side,
      lots: lots,
      entry: entry,
      sl: slResult.value,
      tp: tpResult.value,
      openIndex: state.cursor,
      status: "open",
      closeIndex: null,
      closePrice: null,
      closeReason: null,
      realized: 0
    };
    scenario.tickets.push(ticket);
    checkStops(ticket, tick, state.cursor);
    state.lotSize = lots;
    if (ticket.status === "closed") {
      setMessage("Ticket closed by " + ticket.closeReason + " on the entry tick.", "info");
    } else {
      setMessage(
        side === "buy" ? "Buy opened at the ask." : "Sell opened at the bid.",
        "good"
      );
    }
    refreshAll();
    saveState();
  }

  function optionalPrice(input, label) {
    const raw = input.value.trim();
    if (raw === "") {
      return { ok: true, value: null };
    }
    const value = Number(raw);
    if (!isFiniteNumber(value) || value <= 0) {
      setMessage(label + " must be a positive price, or blank.", "bad");
      return { ok: false, value: null };
    }
    return { ok: true, value: value };
  }

  function closeTicket(ticketId) {
    const scenario = activeScenario();
    for (let i = 0; i < scenario.tickets.length; i += 1) {
      const ticket = scenario.tickets[i];
      if (ticket.id === ticketId && ticket.status === "open") {
        const tick = currentTick();
        const price = ticket.side === "buy" ? tick[1] : tick[2];
        settle(ticket, price, "manual", state.cursor);
        setMessage("Ticket closed at the current " + (ticket.side === "buy" ? "bid" : "ask") +
          ".", "good");
        refreshAll();
        saveState();
        return;
      }
    }
  }

  function checkStops(ticket, tick, index) {
    if (ticket.side === "buy") {
      if (ticket.sl !== null && tick[1] <= ticket.sl) {
        settle(ticket, ticket.sl, "SL", index);
        return;
      }
      if (ticket.tp !== null && tick[1] >= ticket.tp) {
        settle(ticket, ticket.tp, "TP", index);
      }
      return;
    }
    if (ticket.sl !== null && tick[2] >= ticket.sl) {
      settle(ticket, ticket.sl, "SL", index);
      return;
    }
    if (ticket.tp !== null && tick[2] <= ticket.tp) {
      settle(ticket, ticket.tp, "TP", index);
    }
  }

  function advance(count) {
    const target = clamp(state.cursor + count, 0, N - 1);
    if (target === state.cursor) {
      setMessage("Already at the last tick.", "info");
      return;
    }
    for (let k = state.cursor + 1; k <= target; k += 1) {
      const tick = TICKS[k];
      for (let s = 0; s < state.scenarios.length; s += 1) {
        const tickets = state.scenarios[s].tickets;
        for (let t = 0; t < tickets.length; t += 1) {
          if (tickets[t].status === "open") {
            checkStops(tickets[t], tick, k);
          }
        }
      }
    }
    state.cursor = target;
    setMessage("", "");
    refreshAll();
    saveState();
  }

  function resetPlayground() {
    const hasData = state.scenarios.some(function (scenario) {
      return scenario.tickets.length > 0 || scenario.prediction.points.length > 0;
    });
    if (hasData) {
      const ok = window.confirm(
        "Reset playback? This clears every scenario's tickets and predictions."
      );
      if (!ok) {
        return;
      }
    }
    state.cursor = 0;
    state.drawMode = false;
    state.bothWays = false;
    for (let i = 0; i < state.scenarios.length; i += 1) {
      state.scenarios[i].tickets = [];
      state.scenarios[i].prediction = emptyPrediction();
    }
    setMessage("Playback reset. Tickets and predictions cleared.", "info");
    refreshAll();
    saveState();
  }

  function addScenario() {
    const scenario = emptyScenario("Scenario " + (state.scenarios.length + 1));
    state.scenarios.push(scenario);
    state.activeId = scenario.id;
    setMessage("Scenario added.", "good");
    refreshAll();
    saveState();
  }

  function renameScenario() {
    const scenario = activeScenario();
    const name = window.prompt("Scenario name", scenario.name);
    if (name === null) {
      return;
    }
    const trimmed = name.trim().slice(0, 40);
    if (trimmed === "") {
      setMessage("A scenario needs a name.", "bad");
      return;
    }
    scenario.name = trimmed;
    setMessage("Scenario renamed.", "good");
    refreshAll();
    saveState();
  }

  function duplicateScenario() {
    const source = activeScenario();
    const copy = {
      id: makeId("s"),
      name: (source.name + " copy").slice(0, 40),
      tickets: source.tickets.map(function (ticket) {
        return {
          id: makeId("t"),
          side: ticket.side,
          lots: ticket.lots,
          entry: ticket.entry,
          sl: ticket.sl,
          tp: ticket.tp,
          openIndex: ticket.openIndex,
          status: ticket.status,
          closeIndex: ticket.closeIndex,
          closePrice: ticket.closePrice,
          closeReason: ticket.closeReason,
          realized: ticket.realized
        };
      }),
      prediction: JSON.parse(JSON.stringify(source.prediction))
    };
    state.scenarios.push(copy);
    state.activeId = copy.id;
    setMessage("Scenario duplicated.", "good");
    refreshAll();
    saveState();
  }

  function deleteScenario() {
    if (state.scenarios.length === 1) {
      setMessage("Keep at least one scenario.", "info");
      return;
    }
    const index = state.scenarios.findIndex(function (scenario) {
      return scenario.id === state.activeId;
    });
    const scenario = state.scenarios[index];
    const ok = window.confirm("Delete scenario \"" + scenario.name + "\"?");
    if (!ok) {
      return;
    }
    state.scenarios.splice(index, 1);
    const next = state.scenarios[Math.max(0, index - 1)];
    state.activeId = next.id;
    setMessage("Scenario deleted.", "info");
    refreshAll();
    saveState();
  }

  function toggleDrawMode() {
    state.drawMode = !state.drawMode;
    setMessage(
      state.drawMode ? "Draw mode on: click future ticks." : "Draw mode off.",
      state.drawMode ? "info" : ""
    );
    refreshAll();
  }

  function addPredictionPoint(index, price) {
    if (state.cursor >= N - 1) {
      setMessage("The cursor is at the last tick; reset to draw again.", "info");
      return;
    }
    const target = clamp(index, state.cursor + 1, N - 1);
    const scenario = activeScenario();
    const prediction = scenario.prediction;
    if (prediction.anchorIndex === null) {
      prediction.anchorIndex = state.cursor;
      prediction.anchorPrice = currentTick()[1];
    }
    let existing = -1;
    for (let i = 0; i < prediction.points.length; i += 1) {
      if (prediction.points[i].i === target) {
        existing = i;
        break;
      }
    }
    if (existing >= 0) {
      prediction.points[existing].price = price;
    } else {
      prediction.points.push({ i: target, price: price });
      prediction.points.sort(function (a, b) { return a.i - b.i; });
    }
    setMessage(
      "Prediction " + formatPrice(price) + " at " + formatClock(TICKS[target][0]) + " UTC.",
      "good"
    );
    refreshAll();
    saveState();
  }

  function undoPrediction() {
    const prediction = activeScenario().prediction;
    if (prediction.points.length === 0) {
      return;
    }
    prediction.points.pop();
    if (prediction.points.length === 0) {
      prediction.anchorIndex = null;
      prediction.anchorPrice = null;
    }
    setMessage("Last prediction point removed.", "info");
    refreshAll();
    saveState();
  }

  function clearPrediction() {
    const scenario = activeScenario();
    if (scenario.prediction.points.length === 0) {
      return;
    }
    scenario.prediction = emptyPrediction();
    setMessage("Prediction cleared.", "info");
    refreshAll();
    saveState();
  }

  function toggleBothWays() {
    state.bothWays = !state.bothWays;
    refreshAll();
  }

  function applyGridFromControls() {
    if (el.gridStep.value === "custom") {
      el.customWrap.hidden = false;
      const value = Number(el.gridCustom.value);
      if (isFiniteNumber(value) && value > 0) {
        state.gridStep = value;
      }
    } else {
      el.customWrap.hidden = true;
      state.gridStep = Number(el.gridStep.value);
    }
    refreshAll();
    saveState();
  }

  function applyCustomGrid() {
    const value = Number(el.gridCustom.value);
    if (!isFiniteNumber(value) || value <= 0) {
      setMessage("Custom grid step must be above zero.", "bad");
      return;
    }
    if (value > 1000) {
      setMessage("Custom grid step is too large.", "bad");
      return;
    }
    state.gridStep = value;
    setMessage("Grid step set to " + String(value) + ".", "info");
    refreshAll();
    saveState();
  }

  function applyGridControls() {
    if (el.gridStep.value === "custom" && !el.customWrap.hidden) {
      if (document.activeElement !== el.gridCustom) {
        el.gridCustom.value = String(state.gridStep);
      }
      return;
    }
    let matched = "";
    for (let i = 0; i < STEP_CHOICES.length; i += 1) {
      if (Math.abs(STEP_CHOICES[i] - state.gridStep) < 0.0000001) {
        matched = STEP_CHOICES[i].toFixed(2);
        break;
      }
    }
    if (matched === "") {
      el.gridStep.value = "custom";
      el.customWrap.hidden = false;
      if (document.activeElement !== el.gridCustom) {
        el.gridCustom.value = String(state.gridStep);
      }
    } else {
      el.gridStep.value = matched;
      el.customWrap.hidden = true;
    }
  }

  function updateMoveSize() {
    const value = Number(el.moveSize.value);
    if (!isFiniteNumber(value) || value <= 0) {
      return;
    }
    state.moveSize = value;
    refreshMovePreview();
    if (state.bothWays) {
      renderChart();
    }
    saveState();
  }

  function serializeState() {
    return {
      format: STORAGE_FORMAT,
      version: STORAGE_VERSION,
      datasetId: DATA.datasetId,
      tickCount: N,
      cursor: state.cursor,
      gridStep: state.gridStep,
      lotSize: state.lotSize,
      moveSize: state.moveSize,
      activeId: state.activeId,
      scenarios: state.scenarios.map(function (scenario) {
        return {
          id: scenario.id,
          name: scenario.name,
          tickets: scenario.tickets,
          prediction: scenario.prediction
        };
      })
    };
  }

  function saveState() {
    if (saveDisabled) {
      return;
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(serializeState()));
      el.storageNote.textContent = "Scenarios auto-save in this browser.";
    } catch (error) {
      saveDisabled = true;
      el.storageNote.textContent = "Auto-save unavailable; use Export JSON.";
    }
  }

  function sanitizeTicket(raw, cursor) {
    if (!raw || (raw.side !== "buy" && raw.side !== "sell")) {
      return null;
    }
    const lots = Number(raw.lots);
    const entry = Number(raw.entry);
    const openIndex = Math.round(Number(raw.openIndex));
    if (!isFiniteNumber(lots) || lots <= 0 || !isFiniteNumber(entry)) {
      return null;
    }
    if (!isFiniteNumber(openIndex) || openIndex < 0 || openIndex > cursor) {
      return null;
    }
    const status = raw.status === "closed" ? "closed" : "open";
    const ticket = {
      id: typeof raw.id === "string" ? raw.id : makeId("t"),
      side: raw.side,
      lots: lots,
      entry: entry,
      sl: isFiniteNumber(raw.sl) ? raw.sl : null,
      tp: isFiniteNumber(raw.tp) ? raw.tp : null,
      openIndex: openIndex,
      status: status,
      closeIndex: null,
      closePrice: null,
      closeReason: null,
      realized: 0
    };
    if (status === "closed") {
      const closeIndex = Math.round(Number(raw.closeIndex));
      const closePrice = Number(raw.closePrice);
      const realized = Number(raw.realized);
      if (!isFiniteNumber(closeIndex) || closeIndex < openIndex || closeIndex > cursor) {
        return null;
      }
      if (!isFiniteNumber(closePrice) || !isFiniteNumber(realized)) {
        return null;
      }
      ticket.closeIndex = closeIndex;
      ticket.closePrice = closePrice;
      ticket.closeReason = typeof raw.closeReason === "string" ? raw.closeReason : "manual";
      ticket.realized = realized;
    }
    return ticket;
  }

  function sanitizePrediction(raw, cursor) {
    if (!raw || typeof raw !== "object") {
      return emptyPrediction();
    }
    const points = [];
    if (Array.isArray(raw.points)) {
      const limit = Math.min(raw.points.length, 3000);
      for (let i = 0; i < limit; i += 1) {
        const item = raw.points[i];
        if (!item || typeof item !== "object") {
          continue;
        }
        const index = Math.round(Number(item.i));
        const price = Number(item.price);
        if (!isFiniteNumber(index) || index < 1 || index >= N) {
          continue;
        }
        if (!isFiniteNumber(price)) {
          continue;
        }
        points.push({ i: index, price: price });
      }
    }
    points.sort(function (a, b) { return a.i - b.i; });
    const deduped = [];
    for (let i = 0; i < points.length; i += 1) {
      const last = deduped.length > 0 ? deduped[deduped.length - 1] : null;
      if (last !== null && last.i === points[i].i) {
        last.price = points[i].price;
      } else {
        deduped.push(points[i]);
      }
    }
    let anchorIndex = null;
    if (isFiniteNumber(Number(raw.anchorIndex))) {
      anchorIndex = clamp(Math.round(Number(raw.anchorIndex)), 0, cursor);
    }
    let anchorPrice = null;
    if (isFiniteNumber(Number(raw.anchorPrice))) {
      anchorPrice = Number(raw.anchorPrice);
    }
    if (deduped.length > 0 && anchorPrice === null) {
      anchorPrice = TICKS[anchorIndex === null ? 0 : anchorIndex][1];
    }
    return { anchorIndex: anchorIndex, anchorPrice: anchorPrice, points: deduped };
  }

  function sanitizeScenario(raw, cursor) {
    if (!raw || typeof raw !== "object") {
      return null;
    }
    let name = "Scenario";
    if (typeof raw.name === "string" && raw.name.trim() !== "") {
      name = raw.name.trim().slice(0, 40);
    }
    const tickets = [];
    if (Array.isArray(raw.tickets)) {
      const limit = Math.min(raw.tickets.length, 500);
      for (let i = 0; i < limit; i += 1) {
        const ticket = sanitizeTicket(raw.tickets[i], cursor);
        if (ticket !== null) {
          tickets.push(ticket);
        }
      }
    }
    return {
      id: typeof raw.id === "string" ? raw.id : makeId("s"),
      name: name,
      tickets: tickets,
      prediction: sanitizePrediction(raw.prediction, cursor)
    };
  }

  function applySession(parsed) {
    if (!parsed || parsed.format !== STORAGE_FORMAT) {
      throw new Error("this is not a playground scenario file");
    }
    if (parsed.version !== STORAGE_VERSION) {
      throw new Error("this scenario file version is not supported");
    }
    if (parsed.datasetId !== DATA.datasetId) {
      throw new Error("this scenario file belongs to a different dataset");
    }
    if (parsed.tickCount !== N) {
      throw new Error("this scenario file has a different tick count");
    }
    if (!Array.isArray(parsed.scenarios) || parsed.scenarios.length === 0) {
      throw new Error("this scenario file has no scenarios");
    }
    const cursor = clamp(Math.round(Number(parsed.cursor) || 0), 0, N - 1);
    const scenarios = [];
    const limit = Math.min(parsed.scenarios.length, 40);
    for (let i = 0; i < limit; i += 1) {
      const scenario = sanitizeScenario(parsed.scenarios[i], cursor);
      if (scenario !== null) {
        scenarios.push(scenario);
      }
    }
    if (scenarios.length === 0) {
      throw new Error("this scenario file has no usable scenarios");
    }
    state.cursor = cursor;
    state.scenarios = scenarios;
    state.activeId = scenarios[0].id;
    for (let i = 0; i < scenarios.length; i += 1) {
      if (scenarios[i].id === parsed.activeId) {
        state.activeId = scenarios[i].id;
        break;
      }
    }
    const grid = Number(parsed.gridStep);
    if (isFiniteNumber(grid) && grid > 0 && grid <= 1000) {
      state.gridStep = grid;
    }
    const lot = Number(parsed.lotSize);
    if (isFiniteNumber(lot) && lot > 0) {
      state.lotSize = lot;
    }
    const move = Number(parsed.moveSize);
    if (isFiniteNumber(move) && move > 0) {
      state.moveSize = move;
    }
  }

  function loadSavedState() {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return;
      }
      applySession(JSON.parse(raw));
    } catch (error) {
      state.cursor = 0;
      state.scenarios = [emptyScenario("Scenario 1")];
      state.activeId = state.scenarios[0].id;
      el.storageNote.textContent = "Saved session ignored; starting fresh.";
    }
  }

  function exportSession() {
    const text = JSON.stringify(serializeState(), null, 2);
    const blob = new Blob([text], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const windowName = DATA.window.from.replace(":", "") + "-" +
      DATA.window.to.replace(":", "");
    link.href = url;
    link.download = "losslens-playground-" + DATA.symbol.toLowerCase() + "-" +
      DATA.day + "-" + windowName + ".json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    setMessage("Scenario file exported.", "good");
  }

  function importFile(file) {
    const reader = new FileReader();
    reader.onload = function () {
      try {
        const parsed = JSON.parse(String(reader.result));
        applySession(parsed);
        setMessage("Scenario file imported.", "good");
        el.lots.value = formatLots(state.lotSize);
        el.moveSize.value = state.moveSize.toFixed(2);
        refreshAll();
        saveState();
      } catch (error) {
        const text = error instanceof Error ? error.message : "invalid scenario file";
        setMessage("Import failed: " + text + ".", "bad");
      }
      $("import-file").value = "";
    };
    reader.onerror = function () {
      setMessage("Import failed: the file could not be read.", "bad");
      $("import-file").value = "";
    };
    reader.readAsText(file);
  }

  function refreshTabs() {
    el.tabs.innerHTML = "";
    for (let i = 0; i < state.scenarios.length; i += 1) {
      const scenario = state.scenarios[i];
      const button = document.createElement("button");
      button.className = "tab" + (scenario.id === state.activeId ? " active" : "");
      button.type = "button";
      button.textContent = scenario.name;
      button.addEventListener("click", function () {
        state.activeId = scenario.id;
        refreshAll();
        saveState();
      });
      el.tabs.appendChild(button);
    }
  }

  function ticketCell(text) {
    const cell = document.createElement("td");
    cell.textContent = text;
    return cell;
  }

  function ticketRow(ticket) {
    const row = document.createElement("tr");
    if (ticket.status === "closed") {
      row.className = "closed";
    }
    row.appendChild(ticketCell(formatClock(TICKS[ticket.openIndex][0])));
    const side = ticketCell(ticket.side);
    side.className = "side-" + ticket.side;
    row.appendChild(side);
    row.appendChild(ticketCell(formatLots(ticket.lots)));
    const price = ticketCell(formatPrice(ticket.entry));
    if (ticket.status === "closed") {
      const sub = document.createElement("div");
      sub.className = "sub";
      sub.textContent = "-> " + formatPrice(ticket.closePrice);
      price.appendChild(sub);
    }
    row.appendChild(price);
    row.appendChild(ticketCell(ticket.sl === null ? "-" : formatPrice(ticket.sl)));
    row.appendChild(ticketCell(ticket.tp === null ? "-" : formatPrice(ticket.tp)));
    const pnl = document.createElement("td");
    if (ticket.status === "open") {
      const tick = currentTick();
      const live = ticketPnl(ticket, ticket.side === "buy" ? tick[1] : tick[2]);
      pnl.className = live >= 0 ? "up" : "down";
      pnl.textContent = formatMoney(live);
    } else {
      pnl.className = ticket.realized >= 0 ? "up" : "down";
      pnl.textContent = formatMoney(ticket.realized);
    }
    row.appendChild(pnl);
    const action = document.createElement("td");
    action.className = "ticket-action";
    if (ticket.status === "open") {
      const close = document.createElement("button");
      close.className = "btn small";
      close.type = "button";
      close.textContent = "Close";
      close.setAttribute("aria-label", "Close ticket");
      close.addEventListener("click", function () { closeTicket(ticket.id); });
      action.appendChild(close);
    } else {
      action.textContent = ticket.closeReason;
    }
    row.appendChild(action);
    return row;
  }

  function refreshTickets() {
    el.ticketBody.innerHTML = "";
    const scenario = activeScenario();
    const rows = scenario.tickets.slice().sort(function (a, b) {
      return b.openIndex - a.openIndex;
    });
    if (rows.length === 0) {
      el.ticketEmpty.hidden = false;
      el.ticketEmpty.textContent = "No open positions.";
      return;
    }
    el.ticketEmpty.hidden = true;
    for (let i = 0; i < rows.length; i += 1) {
      el.ticketBody.appendChild(ticketRow(rows[i]));
    }
  }

  function refreshEquity() {
    const scenario = activeScenario();
    const tick = currentTick();
    const balance = balanceOf(scenario);
    const floating = floatingAt(scenario, tick[1], tick[2]);
    el.balance.textContent = formatMoney(balance);
    el.floating.textContent = formatMoney(floating);
    el.floating.className = floating >= 0 ? "up" : "down";
    el.equity.textContent = formatMoney(balance + floating);
  }

  function refreshMovePreview() {
    el.movePreview.innerHTML = "";
    const scenario = activeScenario();
    const tick = currentTick();
    const move = Math.abs(state.moveSize);
    let openCount = 0;
    for (let i = 0; i < scenario.tickets.length; i += 1) {
      if (scenario.tickets[i].status === "open") {
        openCount += 1;
      }
    }
    if (openCount === 0) {
      const note = document.createElement("div");
      note.className = "meta-line";
      note.textContent = "No open tickets to preview.";
      el.movePreview.appendChild(note);
      return;
    }
    const up = floatingAt(scenario, tick[1] + move, tick[2] + move);
    const down = floatingAt(scenario, tick[1] - move, tick[2] - move);
    el.movePreview.appendChild(previewRow("At +$" + move.toFixed(2), up));
    el.movePreview.appendChild(previewRow("At -$" + move.toFixed(2), down));
  }

  function previewRow(label, value) {
    const row = document.createElement("div");
    row.className = "preview-row";
    const name = document.createElement("span");
    name.textContent = label;
    const amount = document.createElement("b");
    amount.className = value >= 0 ? "up" : "down";
    amount.textContent = formatMoney(value);
    row.appendChild(name);
    row.appendChild(amount);
    return row;
  }

  function refreshPrediction() {
    const scenario = activeScenario();
    const count = scenario.prediction.points.length;
    const stats = predictionStats(scenario);
    el.drawToggle.classList.toggle("active", state.drawMode);
    el.drawToggle.setAttribute("aria-pressed", state.drawMode ? "true" : "false");
    el.bothWays.classList.toggle("active", state.bothWays);
    el.bothWays.setAttribute("aria-pressed", state.bothWays ? "true" : "false");
    el.predUndo.disabled = count === 0;
    el.predClear.disabled = count === 0;
    el.chartHint.classList.toggle("hidden", !state.drawMode);
    el.canvasWrap.classList.toggle("drawing", state.drawMode);
    if (count === 0) {
      el.predStats.textContent = "No prediction points. Turn on Draw mode and click ahead.";
      return;
    }
    const mae = stats.mae === null ? "-" : formatPrice(stats.mae);
    const hit = stats.hitRate === null ? "-" : Math.round(stats.hitRate * 100) + "%";
    el.predStats.textContent = "Points " + count + " · reached " + stats.count +
      " · MAE " + mae + " · direction " + hit;
  }

  function refreshAll() {
    const tick = currentTick();
    el.datasetLine.textContent = DATA.symbol + " · " + DATA.day + " · " +
      DATA.window.from + "-" + DATA.window.to + " UTC";
    el.chartSymbol.textContent = DATA.symbol + ",Ticks";
    el.chartSub.textContent = DATA.day + "  " + DATA.window.from + "-" +
      DATA.window.to + " UTC";
    el.bid.textContent = formatPrice(tick[1]);
    el.ask.textContent = formatPrice(tick[2]);
    el.spread.textContent = (tick[2] - tick[1]).toFixed(2);
    el.cursorLine.textContent = "Tick " + (state.cursor + 1) + " / " + N;
    el.timeLine.textContent = formatClock(tick[0]) + " UTC";
    el.revealLine.textContent = (state.cursor + 1) + " of " + N + " revealed";
    $("next1").disabled = state.cursor >= N - 1;
    $("next10").disabled = state.cursor >= N - 1;
    $("next100").disabled = state.cursor >= N - 1;
    refreshTabs();
    refreshTickets();
    refreshEquity();
    refreshPrediction();
    refreshMovePreview();
    applyGridControls();
    renderChart();
  }

  function computeDomains() {
    timeMin = TICKS[0][0];
    timeMax = TICKS[N - 1][0];
    if (timeMax <= timeMin) {
      timeMax = timeMin + 1000;
    }
    let low = Infinity;
    let high = -Infinity;
    for (let i = 0; i <= state.cursor; i += 1) {
      const bid = TICKS[i][1];
      const ask = TICKS[i][2];
      if (bid < low) {
        low = bid;
      }
      if (bid > high) {
        high = bid;
      }
      if (ask < low) {
        low = ask;
      }
      if (ask > high) {
        high = ask;
      }
    }
    const scenario = activeScenario();
    const points = scenario.prediction.points;
    for (let i = 0; i < points.length; i += 1) {
      if (points[i].price < low) {
        low = points[i].price;
      }
      if (points[i].price > high) {
        high = points[i].price;
      }
    }
    if (!Number.isFinite(low) || !Number.isFinite(high)) {
      low = 0;
      high = 1;
    }
    if (high - low < 0.0000001) {
      low -= state.gridStep * 4;
      high += state.gridStep * 4;
    }
    const padding = Math.max((high - low) * 0.08, state.gridStep);
    low -= padding;
    high += padding;
    priceMin = Math.floor(low / state.gridStep) * state.gridStep;
    priceMax = Math.ceil(high / state.gridStep) * state.gridStep;
    if (priceMax <= priceMin) {
      priceMax = priceMin + state.gridStep * 4;
    }
  }

  function computePlot() {
    const rightPad = view.width < 540 ? 78 : 92;
    plot = {
      x: 10,
      y: 14,
      w: Math.max(10, view.width - 10 - rightPad),
      h: Math.max(10, view.height - 14 - 28)
    };
  }

  function xOfTime(ts) {
    return plot.x + (ts - timeMin) / (timeMax - timeMin) * plot.w;
  }

  function xOfIndex(index) {
    return xOfTime(TICKS[index][0]);
  }

  function yOfPrice(price) {
    return plot.y + (priceMax - price) / (priceMax - priceMin) * plot.h;
  }

  function withPlotClip(draw) {
    ctx.save();
    ctx.beginPath();
    ctx.rect(plot.x, plot.y, plot.w, plot.h);
    ctx.clip();
    draw();
    ctx.restore();
  }

  function drawGrid() {
    const priceLabels = [];
    const timeLabels = [];
    const step = state.gridStep;
    const first = Math.ceil(priceMin / step) * step;
    let total = Math.floor((priceMax - first) / step) + 1;
    if (!Number.isFinite(total) || total < 1) {
      total = 1;
    }
    let displayStep = step;
    if (total > 6000) {
      displayStep = step * Math.ceil(total / 6000);
      total = Math.floor((priceMax - first) / displayStep) + 1;
    }
    const pixelGap = plot.h / Math.max(1, total);
    const labelEvery = Math.max(1, Math.ceil(22 / Math.max(1, pixelGap)));
    withPlotClip(function () {
      for (let i = 0; i < total; i += 1) {
        const price = first + i * displayStep;
        const y = yOfPrice(price);
        ctx.beginPath();
        ctx.strokeStyle = i % 5 === 0 ? C.gridStrong : C.grid;
        ctx.lineWidth = 1;
        ctx.moveTo(plot.x, Math.round(y) + 0.5);
        ctx.lineTo(plot.x + plot.w, Math.round(y) + 0.5);
        ctx.stroke();
        if (i % labelEvery === 0) {
          priceLabels.push({ y: y, price: price });
        }
      }
      const span = timeMax - timeMin;
      const intervals = [
        30 * 1000, 60 * 1000, 5 * 60 * 1000, 15 * 60 * 1000, 30 * 60 * 1000,
        60 * 60 * 1000, 3 * 60 * 60 * 1000, 6 * 60 * 60 * 1000,
        12 * 60 * 60 * 1000, 24 * 60 * 60 * 1000
      ];
      let interval = intervals[intervals.length - 1];
      for (let i = 0; i < intervals.length; i += 1) {
        if (span / intervals[i] <= 8) {
          interval = intervals[i];
          break;
        }
      }
      const firstTime = Math.ceil(timeMin / interval) * interval;
      for (let t = firstTime; t <= timeMax; t += interval) {
        const x = xOfTime(t);
        ctx.beginPath();
        ctx.strokeStyle = C.grid;
        ctx.lineWidth = 1;
        ctx.moveTo(Math.round(x) + 0.5, plot.y);
        ctx.lineTo(Math.round(x) + 0.5, plot.y + plot.h);
        ctx.stroke();
        timeLabels.push({ x: x, ts: t });
      }
    });
    ctx.font = "10px Tahoma, Arial, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillStyle = C.axis;
    const bidY = yOfPrice(currentTick()[1]);
    const askY = yOfPrice(currentTick()[2]);
    for (let i = 0; i < priceLabels.length; i += 1) {
      const label = priceLabels[i];
      if (label.y < plot.y + 5 || label.y > plot.y + plot.h - 5) {
        continue;
      }
      if (Math.abs(label.y - bidY) < 12 || Math.abs(label.y - askY) < 12) {
        continue;
      }
      ctx.fillText(formatPrice(label.price), plot.x + plot.w + 8, label.y);
    }
    ctx.font = "10px Tahoma, Arial, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = C.dim;
    for (let i = 0; i < timeLabels.length; i += 1) {
      const label = timeLabels[i];
      if (label.x < plot.x + 20 || label.x > plot.x + plot.w - 20) {
        continue;
      }
      ctx.fillText(formatShortTime(label.ts), label.x, plot.y + plot.h + 9);
    }
  }

  function drawFutureShade() {
    const x = xOfIndex(state.cursor);
    ctx.save();
    ctx.beginPath();
    ctx.rect(plot.x, plot.y, plot.w, plot.h);
    ctx.clip();
    if (x < plot.x + plot.w) {
      ctx.fillStyle = C.future;
      ctx.fillRect(x, plot.y, plot.x + plot.w - x, plot.h);
    }
    ctx.restore();
  }

  function drawTicketLevels() {
    const scenario = activeScenario();
    const tickets = scenario.tickets;
    withPlotClip(function () {
      for (let i = 0; i < tickets.length; i += 1) {
        const ticket = tickets[i];
        if (ticket.status !== "open") {
          continue;
        }
        const color = ticket.side === "buy" ? C.buy : C.sell;
        ctx.setLineDash([5, 4]);
        ctx.lineWidth = 1;
        ctx.strokeStyle = color + "77";
        const y = yOfPrice(ticket.entry);
        if (y >= plot.y && y <= plot.y + plot.h) {
          ctx.beginPath();
          ctx.moveTo(plot.x, y);
          ctx.lineTo(plot.x + plot.w, y);
          ctx.stroke();
          ctx.fillStyle = color;
          ctx.font = "10px Tahoma, Arial, sans-serif";
          ctx.textAlign = "left";
          ctx.textBaseline = "bottom";
          ctx.fillText(ticket.side.toUpperCase() + " " + formatLots(ticket.lots) +
            " @ " + formatPrice(ticket.entry), plot.x + 4, y - 2);
        }
        const levels = [
          { value: ticket.sl, color: "#ff4d4d" },
          { value: ticket.tp, color: "#00ff00" }
        ];
        for (let j = 0; j < levels.length; j += 1) {
          if (levels[j].value === null) {
            continue;
          }
          const ly = yOfPrice(levels[j].value);
          if (ly < plot.y || ly > plot.y + plot.h) {
            continue;
          }
          ctx.setLineDash([2, 4]);
          ctx.strokeStyle = levels[j].color;
          ctx.globalAlpha = 0.55;
          ctx.beginPath();
          ctx.moveTo(plot.x, ly);
          ctx.lineTo(plot.x + plot.w, ly);
          ctx.stroke();
          ctx.globalAlpha = 1;
        }
      }
      ctx.setLineDash([]);
    });
  }

  function drawBidLine() {
    if (state.cursor < 0) {
      return;
    }
    withPlotClip(function () {
      ctx.beginPath();
      for (let i = 0; i <= state.cursor; i += 1) {
        const x = xOfIndex(i);
        const y = yOfPrice(TICKS[i][1]);
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.lineWidth = 1.2;
      ctx.lineJoin = "round";
      ctx.strokeStyle = C.bid;
      ctx.stroke();
    });
  }

  function drawPrediction() {
    const scenario = activeScenario();
    const prediction = scenario.prediction;
    if (prediction.points.length === 0) {
      return;
    }
    const anchorIndex = prediction.anchorIndex === null ? 0 : prediction.anchorIndex;
    const anchorPrice = isFiniteNumber(prediction.anchorPrice)
      ? prediction.anchorPrice
      : TICKS[anchorIndex][1];
    const scores = scoredPoints(scenario);
    const scoreMap = new Map();
    for (let i = 0; i < scores.length; i += 1) {
      scoreMap.set(scores[i].point, scores[i]);
    }
    withPlotClip(function () {
      ctx.beginPath();
      ctx.moveTo(xOfIndex(anchorIndex), yOfPrice(anchorPrice));
      for (let i = 0; i < prediction.points.length; i += 1) {
        const point = prediction.points[i];
        ctx.lineTo(xOfIndex(point.i), yOfPrice(point.price));
      }
      ctx.setLineDash([6, 4]);
      ctx.lineWidth = 1.6;
      ctx.strokeStyle = C.predict;
      ctx.stroke();
      ctx.setLineDash([]);
      for (let i = 0; i < prediction.points.length; i += 1) {
        const point = prediction.points[i];
        const score = scoreMap.get(point);
        const x = xOfIndex(point.i);
        const y = yOfPrice(point.price);
        ctx.beginPath();
        ctx.arc(x, y, 3.2, 0, Math.PI * 2);
        if (score) {
          ctx.fillStyle = score.hit ? C.ghostUp : C.ghostDown;
          ctx.fill();
        } else {
          ctx.strokeStyle = C.predict;
          ctx.lineWidth = 1.3;
          ctx.stroke();
        }
      }
    });
  }

  function ghostPaths() {
    const scenario = activeScenario();
    const tick = currentTick();
    const startX = xOfIndex(state.cursor);
    const startY = yOfPrice(tick[1]);
    const startPrice = tick[1];
    const up = [{ x: startX, y: startY, price: startPrice }];
    const down = [{ x: startX, y: startY, price: startPrice }];
    const future = [];
    for (let i = 0; i < scenario.prediction.points.length; i += 1) {
      const point = scenario.prediction.points[i];
      if (point.i > state.cursor) {
        future.push(point);
      }
    }
    if (future.length > 0) {
      for (let i = 0; i < future.length; i += 1) {
        const price = snapPrice(future[i].price);
        up.push({
          x: xOfIndex(future[i].i),
          y: yOfPrice(price),
          price: price
        });
        const mirrored = startPrice - (price - startPrice);
        down.push({
          x: xOfIndex(future[i].i),
          y: yOfPrice(mirrored),
          price: mirrored
        });
      }
    } else {
      const upPrice = snapPrice(startPrice + state.moveSize);
      const downPrice = snapPrice(startPrice - state.moveSize);
      const endX = plot.x + plot.w - 2;
      up.push({ x: endX, y: yOfPrice(upPrice), price: upPrice });
      down.push({ x: endX, y: yOfPrice(downPrice), price: downPrice });
    }
    return { up: up, down: down, fromPrediction: future.length > 0 };
  }

  function drawGhostPath(path, color) {
    if (path.length < 2) {
      return;
    }
    ctx.beginPath();
    for (let i = 0; i < path.length; i += 1) {
      if (i === 0) {
        ctx.moveTo(path[i].x, path[i].y);
      } else {
        ctx.lineTo(path[i].x, path[i].y);
      }
    }
    ctx.setLineDash([3, 5]);
    ctx.lineWidth = 1.4;
    ctx.strokeStyle = color;
    ctx.stroke();
    ctx.setLineDash([]);
    const last = path[path.length - 1];
    ctx.beginPath();
    ctx.arc(last.x, last.y, 3, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  }

  function drawPill(x, y, text, color, textColor) {
    ctx.font = "10px Tahoma, Arial, sans-serif";
    const width = ctx.measureText(text).width + 12;
    let left = x - width;
    left = clamp(left, plot.x + 2, plot.x + plot.w - width - 2);
    const top = clamp(y - 8, plot.y + 2, plot.y + plot.h - 18);
    ctx.fillStyle = color;
    ctx.fillRect(left, top, width, 16);
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = 1;
    ctx.strokeRect(left + 0.5, top + 0.5, width - 1, 15);
    ctx.fillStyle = textColor;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(text, left + 6, top + 8);
  }

  function drawGhosts() {
    if (!state.bothWays) {
      return;
    }
    const scenario = activeScenario();
    const tick = currentTick();
    const paths = ghostPaths();
    withPlotClip(function () {
      if (!paths.fromPrediction) {
        drawGhostPath(paths.up, C.ghostUp);
      }
      drawGhostPath(paths.down, C.ghostDown);
    });
    const spread = tick[2] - tick[1];
    const upLast = paths.up[paths.up.length - 1];
    const downLast = paths.down[paths.down.length - 1];
    const upPnl = floatingAt(scenario, upLast.price, upLast.price + spread);
    const downPnl = floatingAt(scenario, downLast.price, downLast.price + spread);
    drawPill(upLast.x, upLast.y + 15, "UP " + formatMoney(upPnl), C.ghostUp, "#000000");
    drawPill(downLast.x, downLast.y + 15, "DOWN " + formatMoney(downPnl), C.ghostDown,
      "#ffffff");
  }

  function drawCursor() {
    const x = xOfIndex(state.cursor);
    withPlotClip(function () {
      ctx.beginPath();
      ctx.setLineDash([2, 3]);
      ctx.strokeStyle = "rgba(200, 200, 200, 0.65)";
      ctx.lineWidth = 1;
      ctx.moveTo(Math.round(x) + 0.5, plot.y);
      ctx.lineTo(Math.round(x) + 0.5, plot.y + plot.h);
      ctx.stroke();
      ctx.setLineDash([]);
    });
    const label = "NOW";
    ctx.font = "10px Tahoma, Arial, sans-serif";
    const width = ctx.measureText(label).width + 10;
    let left = x - width / 2;
    left = clamp(left, plot.x + 1, plot.x + plot.w - width - 1);
    ctx.fillStyle = "#2f6fb3";
    ctx.fillRect(left, plot.y + 2, width, 14);
    ctx.strokeStyle = "#245786";
    ctx.strokeRect(left + 0.5, plot.y + 2.5, width - 1, 13);
    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, left + width / 2, plot.y + 9);
  }

  function drawPriceTag(top, text, background, textColor) {
    ctx.font = "10px Tahoma, Arial, sans-serif";
    const width = ctx.measureText(text).width + 10;
    const left = plot.x + plot.w + 4;
    const clampedTop = clamp(top, plot.y + 1, plot.y + plot.h - 17);
    ctx.fillStyle = background;
    ctx.fillRect(left, clampedTop, width, 16);
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = 1;
    ctx.strokeRect(left + 0.5, clampedTop + 0.5, width - 1, 15);
    ctx.fillStyle = textColor;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(text, left + 5, clampedTop + 8);
    return clampedTop;
  }

  function drawLastPrice() {
    const tick = currentTick();
    const x = xOfIndex(state.cursor);
    const bidY = yOfPrice(tick[1]);
    const askY = yOfPrice(tick[2]);
    withPlotClip(function () {
      ctx.beginPath();
      ctx.strokeStyle = C.ask;
      ctx.lineWidth = 1;
      ctx.moveTo(plot.x, Math.round(askY) + 0.5);
      ctx.lineTo(plot.x + plot.w, Math.round(askY) + 0.5);
      ctx.stroke();
      ctx.beginPath();
      ctx.strokeStyle = C.bid;
      ctx.lineWidth = 1;
      ctx.moveTo(plot.x, Math.round(bidY) + 0.5);
      ctx.lineTo(plot.x + plot.w, Math.round(bidY) + 0.5);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(x, bidY, 3.2, 0, Math.PI * 2);
      ctx.fillStyle = C.bid;
      ctx.fill();
    });
    let bidTop = clamp(bidY - 8, plot.y + 1, plot.y + plot.h - 17);
    let askTop = clamp(askY - 8, plot.y + 1, plot.y + plot.h - 17);
    if (Math.abs(askTop - bidTop) < 17) {
      askTop = bidTop - 17;
      if (askTop < plot.y + 1) {
        askTop = bidTop + 17;
      }
    }
    drawPriceTag(bidTop, formatPrice(tick[1]), C.bid, "#000000");
    drawPriceTag(askTop, formatPrice(tick[2]), C.ask, "#ffffff");
  }

  function drawFrame() {
    ctx.strokeStyle = "#444444";
    ctx.lineWidth = 1;
    ctx.strokeRect(plot.x + 0.5, plot.y + 0.5, plot.w - 1, plot.h - 1);
  }

  function renderChart() {
    if (view.width < 2 || view.height < 2) {
      return;
    }
    computeDomains();
    computePlot();
    ctx.clearRect(0, 0, view.width, view.height);
    ctx.fillStyle = C.bg;
    ctx.fillRect(0, 0, view.width, view.height);
    if (plot.w < 20 || plot.h < 20) {
      return;
    }
    drawGrid();
    drawFutureShade();
    drawTicketLevels();
    drawBidLine();
    drawPrediction();
    drawGhosts();
    drawCursor();
    drawLastPrice();
    drawFrame();
  }

  function resizeCanvas() {
    const wrap = $("canvas-wrap");
    const rect = wrap.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.floor(rect.width));
    const height = Math.max(1, Math.floor(rect.height));
    if (canvas.width !== Math.floor(width * dpr) ||
        canvas.height !== Math.floor(height * dpr)) {
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
    }
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    view.width = width;
    view.height = height;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    renderChart();
  }

  function nearestTickIndex(time) {
    let low = 0;
    let high = N - 1;
    while (low < high) {
      const mid = Math.floor((low + high) / 2);
      if (TICKS[mid][0] < time) {
        low = mid + 1;
      } else {
        high = mid;
      }
    }
    if (low > 0) {
      const before = TICKS[low - 1][0];
      const after = TICKS[low][0];
      if (time - before < after - time) {
        return low - 1;
      }
    }
    return low;
  }

  function canvasClick(event) {
    if (!state.drawMode || plot === null) {
      return;
    }
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    if (x < plot.x || x > plot.x + plot.w || y < plot.y || y > plot.y + plot.h) {
      return;
    }
    const time = timeMin + (x - plot.x) / plot.w * (timeMax - timeMin);
    const index = nearestTickIndex(time);
    if (index <= state.cursor) {
      setMessage("Draw ahead of the cursor; step forward or click farther right.", "info");
      return;
    }
    const price = snapPrice(
      priceMin + (plot.y + plot.h - y) / plot.h * (priceMax - priceMin)
    );
    addPredictionPoint(index, price);
  }

  function runToEnd() {
    if (state.cursor < N - 1) {
      advance(N - 1 - state.cursor);
    }
    showScoreboard();
  }

  function showScoreboard() {
    const rows = [];
    for (let i = 0; i < state.scenarios.length; i += 1) {
      const scenario = state.scenarios[i];
      const stats = predictionStats(scenario);
      const tickets = ticketStats(scenario);
      rows.push({
        name: scenario.name,
        equity: equityOf(scenario),
        drawdown: maxDrawdownOf(scenario),
        tickets: tickets.total,
        winRate: tickets.winRate,
        mae: stats.mae,
        hitRate: stats.hitRate
      });
    }
    rows.sort(function (a, b) {
      if (Math.abs(b.equity - a.equity) > 0.0001) {
        return b.equity - a.equity;
      }
      return a.name.localeCompare(b.name);
    });
    el.scoreBody.innerHTML = "";
    for (let i = 0; i < rows.length; i += 1) {
      const row = document.createElement("tr");
      if (i === 0 && rows.length > 1) {
        row.className = "winner";
      }
      const cells = [
        rows[i].name,
        formatMoney(rows[i].equity),
        formatMoney(rows[i].drawdown),
        String(rows[i].tickets),
        rows[i].winRate === null ? "-" : (rows[i].winRate * 100).toFixed(1) + "%",
        rows[i].mae === null ? "-" : formatPrice(rows[i].mae),
        rows[i].hitRate === null ? "-" : (rows[i].hitRate * 100).toFixed(1) + "%"
      ];
      for (let j = 0; j < cells.length; j += 1) {
        const cell = document.createElement("td");
        cell.textContent = cells[j];
        row.appendChild(cell);
      }
      el.scoreBody.appendChild(row);
    }
    el.scoreboard.classList.remove("hidden");
  }

  function closeScoreboard() {
    el.scoreboard.classList.add("hidden");
  }

  function bindEvents() {
    $("next1").addEventListener("click", function () { advance(1); });
    $("next10").addEventListener("click", function () { advance(10); });
    $("next100").addEventListener("click", function () { advance(100); });
    $("reset").addEventListener("click", resetPlayground);
    $("buy").addEventListener("click", function () { openTicket("buy"); });
    $("sell").addEventListener("click", function () { openTicket("sell"); });
    $("add-tab").addEventListener("click", addScenario);
    $("rename-tab").addEventListener("click", renameScenario);
    $("duplicate-tab").addEventListener("click", duplicateScenario);
    $("delete-tab").addEventListener("click", deleteScenario);
    el.drawToggle.addEventListener("click", toggleDrawMode);
    el.predUndo.addEventListener("click", undoPrediction);
    el.predClear.addEventListener("click", clearPrediction);
    el.bothWays.addEventListener("click", toggleBothWays);
    el.gridStep.addEventListener("change", applyGridFromControls);
    el.gridCustom.addEventListener("change", applyCustomGrid);
    el.moveSize.addEventListener("input", updateMoveSize);
    canvas.addEventListener("click", canvasClick);
    $("run-end").addEventListener("click", runToEnd);
    $("score-close").addEventListener("click", closeScoreboard);
    el.scoreboard.addEventListener("click", function (event) {
      if (event.target === el.scoreboard) {
        closeScoreboard();
      }
    });
    $("export-json").addEventListener("click", exportSession);
    $("import-json").addEventListener("click", function () { $("import-file").click(); });
    $("import-file").addEventListener("change", function () {
      const input = $("import-file");
      if (input.files && input.files.length > 0) {
        importFile(input.files[0]);
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.code !== "Space" && event.key !== " ") {
        return;
      }
      if (event.repeat) {
        return;
      }
      if (!el.scoreboard.classList.contains("hidden")) {
        return;
      }
      const tag = event.target && event.target.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA" || tag === "BUTTON") {
        return;
      }
      event.preventDefault();
      advance(1);
    });
    window.addEventListener("resize", resizeCanvas);
    if (window.ResizeObserver) {
      const observer = new ResizeObserver(resizeCanvas);
      observer.observe($("canvas-wrap"));
    }
  }

  function init() {
    state.scenarios = [emptyScenario("Scenario 1")];
    state.activeId = state.scenarios[0].id;
    loadSavedState();
    el.lots.value = formatLots(state.lotSize);
    el.moveSize.value = state.moveSize.toFixed(2);
    bindEvents();
    refreshAll();
    resizeCanvas();
  }

  if (!Array.isArray(TICKS) || TICKS.length === 0) {
    document.body.textContent = "This playground has no ticks.";
    return;
  }
  init();
}());
</script>
</body>
</html>
"""


def render_page(payload: str) -> str:
    """Return the page with the JSON data in its one script slot."""
    return PAGE_TEMPLATE.replace("__TICK_DATA__", payload, 1)
