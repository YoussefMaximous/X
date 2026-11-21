"""The static HTML and CSS for the Playground."""

from __future__ import annotations

PAGE_BODY = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LossLens Playground</title>
<style>
  :root {
    --panel: #f0f0f0;
    --panel-dark: #e4e4e4;
    --line: #a0a0a0;
    --text: #111;
    --muted: #666;
    --accent: #2f6fb3;
    --chart: #000;
    --up: #00c000;
    --down: #ff4040;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; overflow: hidden; background: var(--panel); }
  body { font: 11px Tahoma, Arial, sans-serif; color: var(--text); }
  button, input, select { font: 11px Tahoma, Arial, sans-serif; }
  button { cursor: pointer; }
  #app { display: grid; grid-template-rows: 22px 30px 30px minmax(0, 1fr) 220px 20px;
    height: 100vh; }
  #menubar { display: flex; align-items: center; gap: 2px; padding: 0 6px;
    background: var(--panel); border-bottom: 1px solid var(--line); }
  .menu { position: relative; }
  .menu > button { height: 20px; padding: 0 8px; border: 0; background: transparent;
    color: var(--text); }
  .menu > button:hover, .menu.open > button { background: #d8e6f2; }
  .dropdown { display: none; position: absolute; top: 20px; left: 0; min-width: 190px;
    padding: 2px; z-index: 40; background: var(--panel); border: 1px solid #777;
    box-shadow: 0 6px 18px rgba(0, 0, 0, .25); }
  .menu.open .dropdown { display: block; }
  .dropdown button { display: block; width: 100%; padding: 3px 8px; border: 0;
    background: transparent; color: var(--text); text-align: left; }
  .dropdown button:hover { background: #d8e6f2; }
  .dropdown .separator { height: 1px; margin: 2px 4px; background: #c0c0c0; }
  #brand { margin-left: auto; color: var(--muted); font-weight: bold; letter-spacing: .3px; }
  #dataset-line { margin-left: 10px; color: var(--muted); font-size: 10px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  #paused-badge { margin-left: 8px; padding: 1px 6px; border: 1px solid #700;
    background: #a00000; color: #fff; font-weight: bold; letter-spacing: .06em; }
  #toolbar { display: flex; align-items: center; gap: 4px; padding: 0 6px;
    background: var(--panel); border-bottom: 1px solid var(--line); overflow: hidden; }
  #toolbar .label { color: var(--muted); margin: 0 2px; white-space: nowrap; }
  #toolbar button, #replaybar button, .btn { height: 22px; min-width: 28px; padding: 0 7px;
    border: 1px solid #9a9a9a; background: #fbfbfb; color: var(--text); white-space: nowrap; }
  #toolbar button:hover, #replaybar button:hover, .btn:hover { background: #e8f1fa; }
  #toolbar button.active, .btn.active { background: var(--accent); border-color: #245786;
    color: #fff; font-weight: bold; }
  #toolbar select { height: 22px; border: 1px solid #9a9a9a; background: #fbfbfb;
    color: var(--text); padding: 0 3px; }
  #period-select { width: 150px; }
  #grid-step { width: 76px; }
  .separator { width: 1px; height: 18px; background: #c0c0c0; margin: 0 3px; }
  #toolbar-hint { margin-left: auto; color: var(--muted); font-size: 10px;
    white-space: nowrap; }
  #replaybar { display: flex; align-items: center; gap: 4px; padding: 0 6px;
    background: var(--panel-dark); border-bottom: 1px solid var(--line); }
  #replaybar button { height: 22px; }
  #progress-track { flex: 1; height: 12px; min-width: 120px; border: 1px solid #9a9a9a;
    background: #fff; }
  #progress-fill { height: 100%; width: 0; background: var(--accent); }
  #replay-status { color: var(--text); white-space: nowrap; }
  #replay-hint { color: var(--muted); white-space: nowrap; }
  #main { display: grid; grid-template-columns: 190px minmax(0, 1fr); min-height: 0; }
  #watch { background: #fff; border-right: 1px solid var(--line); overflow-y: auto; }
  #watch h2 { margin: 0; padding: 4px 6px; font-size: 11px; background: var(--panel-dark);
    border-bottom: 1px solid var(--line); border-top: 1px solid #c8c8c8; }
  #watch h2:first-child { border-top: 0; }
  .watch-table { width: 100%; border-collapse: collapse; }
  .watch-table th { padding: 3px 6px; color: var(--muted); font-weight: normal;
    text-align: right; border-bottom: 1px solid #e0e0e0; }
  .watch-table th:first-child, .watch-table td:first-child { text-align: left; }
  .watch-table td { padding: 4px 6px; text-align: right; border-bottom: 1px solid #f0f0f0; }
  .watch-table td:first-child { font-weight: bold; }
  .watch-row { display: flex; justify-content: space-between; padding: 3px 6px;
    border-bottom: 1px solid #f0f0f0; color: var(--muted); }
  .watch-row b { color: var(--text); font-weight: normal; }
  .data-window { padding: 3px 6px; }
  .data-window div { display: flex; justify-content: space-between; padding: 1px 0; }
  .data-window span { color: var(--muted); }
  .data-window b { font-weight: normal; font-variant-numeric: tabular-nums; }
  .watch-note { padding: 6px; color: var(--muted); line-height: 1.45; font-size: 10px; }
  #chartarea { position: relative; background: var(--chart); min-width: 0; min-height: 0; }
  #chart { display: block; width: 100%; height: 100%; cursor: crosshair; }
  #future-tag { position: absolute; right: 82px; top: 5px; color: #666; font-size: 9px;
    letter-spacing: .12em; pointer-events: none; }
  #terminal { display: grid; grid-template-rows: 24px minmax(0, 1fr); background: #fff;
    border-top: 1px solid var(--line); min-height: 0; }
  #tabs { display: flex; align-items: stretch; background: var(--panel);
    border-bottom: 1px solid var(--line); overflow-x: auto; }
  #tabs .terminal-title { display: flex; align-items: center; padding: 0 8px;
    color: var(--muted); font-weight: bold; border-right: 1px solid var(--line); }
  #tabs button { padding: 0 10px; border: 0; border-right: 1px solid var(--line);
    background: transparent; color: var(--text); white-space: nowrap; }
  #tabs button:hover { background: #e8f1fa; }
  #tabs button.active { background: #fff; border-bottom: 1px solid #fff;
    margin-bottom: -1px; font-weight: bold; }
  #terminal-summary { margin-left: auto; display: flex; align-items: center; gap: 12px;
    padding: 0 8px; color: var(--muted); font-size: 10px; white-space: nowrap; }
  #terminalbody { min-height: 0; overflow: auto; background: #fff; }
  .tab-pane { display: none; padding: 6px 8px; }
  .tab-pane.active { display: block; }
  .order-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
    padding: 3px 0 5px; border-bottom: 1px solid #e0e0e0; }
  .order-row label { display: flex; align-items: center; gap: 3px; color: var(--muted); }
  .order-row input { width: 72px; height: 21px; padding: 0 4px; border: 1px solid #9a9a9a;
    background: #fff; color: var(--text); }
  #trade-message { color: var(--muted); }
  .btn.buy { background: #2f6fb3; border-color: #245786; color: #fff; }
  .btn.sell { background: #a53a3a; border-color: #7a2626; color: #fff; }
  .btn.primary { background: var(--accent); border-color: #245786; color: #fff; }
  .data-table { width: 100%; border-collapse: collapse; background: #fff;
    font-variant-numeric: tabular-nums; }
  .data-table th { padding: 2px 5px; border: 1px solid #c8c8c8; background: var(--panel-dark);
    color: var(--text); font-weight: normal; text-align: right; white-space: nowrap; }
  .data-table td { padding: 2px 5px; border-bottom: 1px solid #e0e0e0; text-align: right;
    white-space: nowrap; }
  .data-table th:first-child, .data-table td:first-child,
  .data-table th:nth-child(2), .data-table td:nth-child(2) { text-align: left; }
  .data-table tr.closed { background: #fafafa; }
  .data-table td.up { color: #008000; }
  .data-table td.down { color: #c00000; }
  .up { color: #008000; }
  .down { color: #c00000; }
  .data-table td.side-buy { color: #1a4f8a; }
  .data-table td.side-sell { color: #8a1a1a; }
  .data-table .sub { color: var(--muted); font-size: 9px; }
  .empty { padding: 8px 2px; color: var(--muted); }
  .summary-row { display: flex; justify-content: flex-end; gap: 18px; padding: 4px 2px;
    border-top: 1px solid #c0c0c0; margin-top: 4px; }
  .summary-row span { color: var(--muted); }
  .summary-row b { font-weight: normal; font-variant-numeric: tabular-nums; }
  .scroll-x { overflow-x: auto; }
  .expert-head { display: flex; align-items: center; justify-content: space-between;
    gap: 10px; padding: 2px 0 5px; border-bottom: 1px solid #e0e0e0; }
  .expert-head b { font-size: 12px; }
  .expert-head .source { color: var(--muted); margin-left: 6px; }
  .expert-summary { display: flex; flex-wrap: wrap; gap: 6px 18px; padding: 5px 0;
    color: var(--muted); }
  .expert-summary b { color: var(--text); font-weight: normal; }
  .expert-section { margin-top: 6px; }
  .expert-section h3 { margin: 0 0 4px; font-size: 11px; color: var(--text);
    display: flex; align-items: center; gap: 8px; }
  .expert-section h3 .muted { color: var(--muted); font-weight: normal; }
  .check { display: inline-flex; align-items: center; gap: 4px; color: var(--muted); }
  .input-cell input { width: 90px; height: 20px; padding: 0 3px; border: 1px solid #b0b0b0;
    background: #fff; color: var(--text); }
  #expert-inputs-table { width: 720px; table-layout: fixed; }
  #expert-inputs-table th:first-child, #expert-inputs-table td:first-child { width: 220px; }
  #expert-inputs-table th:nth-child(n+2), #expert-inputs-table td:nth-child(n+2) {
    width: 125px; }
  .prediction-actions { display: flex; gap: 4px; flex-wrap: wrap; padding: 2px 0 5px; }
  .stats-box { padding: 4px 6px; border: 1px solid #c8c8c8; background: var(--panel);
    color: var(--text); margin: 3px 0; }
  .field { display: inline-flex; align-items: center; gap: 4px; color: var(--muted);
    margin: 3px 10px 3px 0; }
  .field input { width: 80px; height: 20px; padding: 0 3px; border: 1px solid #b0b0b0; }
  .note { color: var(--muted); line-height: 1.45; margin: 5px 0 0; }
  .scenario-list { display: flex; gap: 3px; flex-wrap: wrap; padding: 2px 0 5px; }
  .scenario-list button { height: 22px; padding: 0 9px; border: 1px solid #9a9a9a;
    background: #fbfbfb; color: var(--text); }
  .scenario-list button.active { background: var(--accent); border-color: #245786;
    color: #fff; font-weight: bold; }
  .session-grid { display: grid; grid-template-columns: 140px minmax(0, 1fr) 140px minmax(0, 1fr);
    gap: 3px 8px; padding: 3px 0 7px; }
  .session-grid span { color: var(--muted); }
  .session-grid b { font-weight: normal; overflow: hidden; text-overflow: ellipsis;
    white-space: nowrap; }
  .help-grid { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
    gap: 18px; }
  .help-grid h3 { margin: 2px 0 5px; font-size: 11px; }
  .help-grid ol { margin: 0; padding-left: 18px; line-height: 1.55; }
  .help-grid p { margin: 0 0 6px; line-height: 1.5; }
  .help-grid table { width: 100%; border-collapse: collapse; }
  .help-grid td { padding: 1px 4px; border-bottom: 1px solid #e8e8e8; }
  .help-grid td:first-child { width: 92px; color: var(--muted); }
  #status { display: flex; align-items: center; gap: 12px; padding: 0 8px;
    background: var(--panel); border-top: 1px solid var(--line); color: var(--muted); }
  #status { min-width: 0; }
  #statuscenter { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  #status .right { margin-left: auto; white-space: nowrap; }
  .modal { position: fixed; inset: 0; z-index: 60; display: flex; align-items: center;
    justify-content: center; background: rgba(0, 0, 0, .35); }
  .modal.hidden { display: none; }
  #score-dialog { width: 860px; max-width: calc(100vw - 40px); max-height: calc(100vh - 60px);
    display: flex; flex-direction: column; background: var(--panel); border: 1px solid #777;
    box-shadow: 0 8px 24px rgba(0, 0, 0, .35); }
  #score-title { display: flex; align-items: center; padding: 5px 8px; background: var(--accent);
    color: #fff; font-weight: bold; }
  #score-title button { margin-left: auto; width: 22px; height: 20px; border: 1px solid #245786;
    background: #fff; color: #111; }
  #score-body-wrap { padding: 8px; overflow: auto; }
  .hidden { display: none !important; }
  @media (max-width: 1000px) {
    #main { grid-template-columns: 1fr; }
    #watch { display: none; }
    #toolbar-hint { display: none; }
  }
</style>
</head>
<body>
<div id="app">
  <div id="menubar">
    <div class="menu" data-menu="file">
      <button type="button">File</button>
      <div class="dropdown">
        <button type="button" data-command="export">Export scenarios...</button>
        <button type="button" data-command="import">Import scenarios...</button>
        <div class="separator"></div>
        <button type="button" data-command="reset">Reset replay</button>
      </div>
    </div>
    <div class="menu" data-menu="view">
      <button type="button">View</button>
      <div class="dropdown">
        <button type="button" data-command="follow">Follow the cursor</button>
        <button type="button" data-command="zoomin">Zoom in</button>
        <button type="button" data-command="zoomout">Zoom out</button>
        <div class="separator"></div>
        <button type="button" data-command="both">Both ways</button>
      </div>
    </div>
    <div class="menu" data-menu="charts">
      <button type="button">Charts</button>
      <div class="dropdown">
        <button type="button" data-command="period" data-value="tick">Tick line</button>
        <button type="button" data-command="period" data-value="t1">1 tick / bar</button>
        <button type="button" data-command="period" data-value="t10">10 ticks / bar</button>
        <button type="button" data-command="period" data-value="t100">100 ticks / bar</button>
        <button type="button" data-command="period" data-value="t500">500 ticks / bar</button>
        <button type="button" data-command="period" data-value="t1000">1,000 ticks / bar</button>
        <div class="separator"></div>
        <button type="button" data-command="period" data-value="m1">1 minute</button>
        <button type="button" data-command="period" data-value="m5">5 minutes</button>
        <button type="button" data-command="period" data-value="m15">15 minutes</button>
        <button type="button" data-command="period" data-value="m30">30 minutes</button>
        <button type="button" data-command="period" data-value="h1">1 hour</button>
      </div>
    </div>
    <div class="menu" data-menu="tools">
      <button type="button">Tools</button>
      <div class="dropdown">
        <button type="button" data-command="draw">Draw mode</button>
        <button type="button" data-command="undo">Undo prediction point</button>
        <button type="button" data-command="clear">Clear prediction</button>
        <button type="button" data-command="both">Both ways</button>
        <div class="separator"></div>
        <button type="button" data-command="runend">Run to end</button>
        <button type="button" data-command="expert">Expert</button>
      </div>
    </div>
    <div class="menu" data-menu="help">
      <button type="button">Help</button>
      <div class="dropdown">
        <button type="button" data-command="help">Quick start</button>
        <button type="button" data-command="help">Keyboard</button>
      </div>
    </div>
    <span id="brand">LOSS-LENS</span>
    <span id="dataset-line"></span>
    <span id="paused-badge">PAUSED</span>
  </div>
  <div id="toolbar">
    <span class="label">Period</span>
    <select id="period-select" aria-label="Chart period">
      <optgroup label="Tick bars (real ticks)">
        <option value="tick">Tick line</option>
        <option value="t1">1 tick / bar</option>
        <option value="t10">10 ticks / bar</option>
        <option value="t100" selected>100 ticks / bar</option>
        <option value="t500">500 ticks / bar</option>
        <option value="t1000">1,000 ticks / bar</option>
      </optgroup>
      <optgroup label="Time bars (built from ticks)">
        <option value="m1">1 minute</option>
        <option value="m5">5 minutes</option>
        <option value="m15">15 minutes</option>
        <option value="m30">30 minutes</option>
        <option value="h1">1 hour</option>
      </optgroup>
    </select>
    <span class="separator"></span>
    <button type="button" id="zoomout" title="Zoom out">-</button>
    <button type="button" id="zoomin" title="Zoom in">+</button>
    <button type="button" id="follow" class="active" title="Keep the cursor in view">Follow</button>
    <span class="separator"></span>
    <span class="label">Grid</span>
    <select id="grid-step" aria-label="Price grid step">
      <option value="0.01">0.01</option>
      <option value="0.05">0.05</option>
      <option value="0.10" selected>0.10</option>
      <option value="0.25">0.25</option>
      <option value="0.50">0.50</option>
      <option value="1.00">1.00</option>
      <option value="custom">Custom</option>
    </select>
    <span class="separator"></span>
    <button type="button" id="draw-toggle" data-action="draw">Draw mode</button>
    <button type="button" id="both-ways" data-action="both">Both ways</button>
    <button type="button" id="open-expert">Expert</button>
    <span id="toolbar-hint">Wheel zoom &middot; drag to pan</span>
  </div>
  <div id="replaybar">
    <button type="button" id="reset">Reset</button>
    <button type="button" id="next1">Next tick</button>
    <button type="button" id="next10">Next 10</button>
    <button type="button" id="next100">Next 100</button>
    <button type="button" id="nextbar">Next bar</button>
    <div id="progress-track"><div id="progress-fill"></div></div>
    <span id="replay-status">Tick 1 / 1</span>
    <span id="replay-hint">Space = next tick &middot; first 5 min revealed</span>
  </div>
  <div id="main">
    <aside id="watch">
      <h2>Market Watch</h2>
      <table class="watch-table">
        <thead><tr><th>Symbol</th><th>Bid</th><th>Ask</th></tr></thead>
        <tbody><tr><td id="wsymbol">XAUUSD</td><td id="bid">-</td><td id="ask">-</td></tr></tbody>
      </table>
      <div class="watch-row"><span>Spread</span><b id="spread">-</b></div>
      <h2>Data Window</h2>
      <div class="data-window">
        <div><span>Period</span><b id="dw-period">-</b></div>
        <div><span id="dw-label-time">Bar time</span><b id="dw-time">-</b></div>
        <div><span id="dw-label-open">Open</span><b id="dw-open">-</b></div>
        <div><span id="dw-label-high">High</span><b id="dw-high">-</b></div>
        <div><span id="dw-label-low">Low</span><b id="dw-low">-</b></div>
        <div><span id="dw-label-close">Close</span><b id="dw-close">-</b></div>
        <div><span id="dw-label-change">Change</span><b id="dw-change">-</b></div>
        <div><span id="dw-label-ticks">Ticks</span><b id="dw-ticks">-</b></div>
      </div>
      <h2>Replay</h2>
      <div class="data-window">
        <div><span>Cursor</span><b id="rp-time">-</b></div>
        <div><span>Tick</span><b id="rp-tick">-</b></div>
        <div><span>Revealed</span><b id="rp-revealed">-</b></div>
        <div><span>Window</span><b id="rp-window">-</b></div>
      </div>
      <div class="watch-note" id="watch-note">Source: Dukascopy ticks stored on this PC.</div>
    </aside>
    <section id="chartarea">
      <canvas id="chart"></canvas>
      <div id="future-tag">FUTURE</div>
    </section>
  </div>
  <div id="terminal">
    <div id="tabs">
      <span class="terminal-title">Terminal</span>
      <button type="button" data-tab="trade" class="active">Trade</button>
      <button type="button" data-tab="history">History</button>
      <button type="button" data-tab="expert">Expert</button>
      <button type="button" data-tab="prediction">Prediction</button>
      <button type="button" data-tab="scenarios">Scenarios</button>
      <button type="button" data-tab="session">Session</button>
      <button type="button" data-tab="help">Help</button>
      <span id="terminal-summary"></span>
    </div>
    <div id="terminalbody">
      <div id="pane-trade" class="tab-pane active">
        <div class="order-row">
          <label>Volume <input id="lots" type="number" min="0.01" step="0.01" value="0.01"></label>
          <label>S/L <input id="sl" type="number" step="0.01" placeholder="none"></label>
          <label>T/P <input id="tp" type="number" step="0.01" placeholder="none"></label>
          <button type="button" id="buy" class="btn buy">Buy</button>
          <button type="button" id="sell" class="btn sell">Sell</button>
          <span id="trade-message"></span>
        </div>
        <table class="data-table" id="open-table">
          <thead><tr><th>Time</th><th>Type</th><th>Size</th><th>Price</th><th>S/L</th>
            <th>T/P</th><th>Profit</th><th></th></tr></thead>
          <tbody id="open-body"></tbody>
        </table>
        <div id="open-empty" class="empty">No open positions. Buy or Sell freezes this tick.</div>
        <div class="summary-row">
          <span>Balance <b id="balance">$10,000.00</b></span>
          <span>Floating P/L <b id="floating">$0.00</b></span>
          <span>Equity <b id="equity">$10,000.00</b></span>
        </div>
      </div>
      <div id="pane-history" class="tab-pane">
        <table class="data-table" id="history-table">
          <thead><tr><th>Time</th><th>Type</th><th>Size</th><th>Open</th><th>Close</th>
            <th>S/L</th><th>T/P</th><th>Profit</th><th>Reason</th></tr></thead>
          <tbody id="history-body"></tbody>
        </table>
        <div id="history-empty" class="empty">No closed tickets yet.</div>
      </div>
      <div id="pane-expert" class="tab-pane">
        <div id="expert-empty" class="empty">
          No expert loaded. Build the page with --inputs &lt;expert.set|expert.mq4&gt; and
          --report &lt;tester.htm&gt;. The Playground does not run MT4; the report comes from
          the existing runner.
        </div>
        <div id="expert-content" class="hidden">
          <div class="expert-head">
            <div><b id="expert-name">Expert</b><span id="expert-source" class="source"></span></div>
            <label class="check"><input id="expert-visible" type="checkbox" checked>
              Show closes on chart</label>
          </div>
          <div id="expert-summary" class="expert-summary"></div>
          <div class="expert-section">
            <h3>Inputs
              <button type="button" id="download-set" class="btn">Download .set</button>
            </h3>
            <div class="scroll-x">
              <table class="data-table" id="expert-inputs-table">
                <thead><tr><th>Input</th><th>Value</th><th>Start</th><th>Step</th><th>Stop</th></tr></thead>
                <tbody id="expert-inputs-body"></tbody>
              </table>
            </div>
            <div id="expert-inputs-empty" class="empty">No inputs loaded.</div>
          </div>
          <div class="expert-section">
            <h3>Report closes <span id="expert-future-count" class="muted"></span></h3>
            <div class="scroll-x">
              <table class="data-table" id="expert-trades-table">
                <thead><tr><th>#</th><th>Close (UTC)</th><th>Type</th><th>Size</th>
                  <th>Close</th><th>Profit</th><th>Balance</th><th>Use</th></tr></thead>
                <tbody id="expert-trades-body"></tbody>
              </table>
            </div>
            <div id="expert-trades-empty" class="empty">No expert closes revealed yet.</div>
          </div>
          <div id="expert-whatif" class="summary-row"></div>
          <p id="expert-note" class="note"></p>
        </div>
      </div>
      <div id="pane-prediction" class="tab-pane">
        <div class="prediction-actions">
          <button type="button" class="btn" data-action="draw">Draw mode</button>
          <button type="button" class="btn" data-action="both">Both ways</button>
          <button type="button" id="pred-undo" class="btn">Undo</button>
          <button type="button" id="pred-clear" class="btn">Clear</button>
        </div>
        <div id="pred-stats" class="stats-box">No prediction points.</div>
        <label class="field">Fixed move &plusmn;$ <input id="move-size" type="number"
          min="0.01" step="0.01" value="1.00"></label>
        <div id="move-preview"></div>
        <p class="note">Draw mode: click future points. They snap to the grid. Both ways mirrors
          the drawn path down. The real ticks score every reached point.</p>
      </div>
      <div id="pane-scenarios" class="tab-pane">
        <div id="scenario-list" class="scenario-list"></div>
        <div class="prediction-actions">
          <button type="button" id="add-scenario" class="btn">+ Add</button>
          <button type="button" id="rename-scenario" class="btn">Rename</button>
          <button type="button" id="duplicate-scenario" class="btn">Duplicate</button>
          <button type="button" id="delete-scenario" class="btn">Delete</button>
          <button type="button" id="run-end" class="btn primary">Run to end</button>
        </div>
        <div class="scroll-x">
          <table class="data-table" id="scenario-summary">
            <thead><tr><th>Scenario</th><th>Equity</th><th>Open</th><th>Closed</th>
              <th>Prediction points</th><th>Reached</th></tr></thead>
            <tbody id="scenario-summary-body"></tbody>
          </table>
        </div>
        <p class="note">All scenarios share the replay cursor. Each has its own tickets and
          prediction. Run to end scores them and adds the expert report row if one is loaded.</p>
      </div>
      <div id="pane-session" class="tab-pane">
        <div class="session-grid">
          <span>Symbol</span><b id="session-symbol">-</b>
          <span>Day</span><b id="session-day">-</b>
          <span>Window</span><b id="session-window">-</b>
          <span>Ticks</span><b id="session-ticks">-</b>
          <span>Source</span><b>Dukascopy ticks in the local store</b>
          <span>Expert</span><b id="session-expert">-</b>
        </div>
        <div class="prediction-actions">
          <button type="button" id="export-json" class="btn">Export scenarios</button>
          <button type="button" id="import-json" class="btn">Import scenarios</button>
          <input id="import-file" type="file" accept=".json,application/json" hidden>
          <button type="button" id="reset-replay" class="btn">Reset replay</button>
        </div>
        <div id="storage-note" class="note"></div>
        <p class="note">Nothing leaves this PC. No server, no account, no network.</p>
      </div>
      <div id="pane-help" class="tab-pane">
        <div class="help-grid">
          <div>
            <h3>Quick start</h3>
            <ol>
              <li>Pick a period: a tick bar uses the real Dukascopy ticks; a time bar builds
                candles from the same ticks.</li>
              <li>Press <b>Space</b> or <b>Next tick</b>. The chart follows the cursor. Use the
                wheel to zoom, drag to pan, and <b>Follow</b> to return.</li>
              <li>Open the <b>Trade</b> tab below and freeze this tick: <b>Buy</b> at the ask,
                <b>Sell</b> at the bid. S/L and T/P are optional and are checked on every
                revealed tick.</li>
              <li>Turn on <b>Draw mode</b> and click future points. <b>Both ways</b> mirrors the
                path. The chart shows MAE and direction once the ticks arrive.</li>
              <li>Add scenarios. They share the cursor; each has its own tickets and prediction.
                <b>Run to end</b> opens the scoreboard.</li>
              <li>Load an expert <b>.set/.mq4</b> and tester report with
                <b>--inputs</b> and <b>--report</b>. The Expert tab can toggle the closes and
                uncheck a trade to remove it from the what-if.</li>
            </ol>
            <p class="note">The replay starts with the first 5 minutes revealed so the chart has
              shape. Reset returns there and clears the scenarios.</p>
          </div>
          <div>
            <h3>Keyboard</h3>
            <table>
              <tr><td>Space</td><td>Next tick</td></tr>
              <tr><td>D</td><td>Draw mode on/off</td></tr>
              <tr><td>B</td><td>Both ways on/off</td></tr>
              <tr><td>+ / -</td><td>Zoom in / out</td></tr>
              <tr><td>Left / Right</td><td>Pan the chart</td></tr>
              <tr><td>End</td><td>Follow the cursor</td></tr>
              <tr><td>?</td><td>Open this Help tab</td></tr>
              <tr><td>Esc</td><td>Close a menu or the scoreboard</td></tr>
            </table>
            <h3>What the colours mean</h3>
            <p>Green is up or bid; red is down or ask. Blue is the Playground's editing layer:
              the replay cursor, the prediction and the active control. Expert closes are grey
              triangles: down for a closed buy, up for a closed sell.</p>
            <p class="note">The report gives close times and prices only. Entry markers need a
              journal or a decision log, which is not part of this build.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div id="status">
    <span>Local only &middot; nothing is sent</span>
    <span id="statuscenter"></span>
    <span class="right" id="statusright"></span>
  </div>
</div>
<div id="scoreboard" class="modal hidden">
  <div id="score-dialog">
    <div id="score-title"><span>Run to end &mdash; scoreboard</span>
      <button type="button" id="score-close">X</button></div>
    <div id="score-body-wrap">
      <table class="data-table" id="score-table">
        <thead><tr><th>Scenario</th><th>Final equity</th><th>Max drawdown</th><th>Tickets</th>
          <th>Win rate</th><th>Prediction MAE</th><th>Direction hit</th></tr></thead>
        <tbody id="score-body"></tbody>
      </table>
      <p id="score-note" class="note"></p>
    </div>
  </div>
</div>
<script id="tick-data" type="application/json">__TICK_DATA__</script>
<script>__SCRIPT__</script>
</body>
</html>
"""
