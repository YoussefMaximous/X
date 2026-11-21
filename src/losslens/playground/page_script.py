"""The inline JavaScript for the Playground page."""

from __future__ import annotations

SCRIPT = r"""
(function () {
  "use strict";

  const DATA = JSON.parse(document.getElementById("tick-data").textContent);
  const REAL_TICKS = DATA.ticks;
  const REAL_N = REAL_TICKS.length;
  let TICKS = REAL_TICKS;
  let N = REAL_N;
  const START_BALANCE = Number(DATA.startBalance) || 10000;
  const CONTRACT_SIZE = Number(DATA.contractSize) || 100;
  const DIGITS = Number(DATA.digits) || 2;
  const WINDOW_FROM = Number(DATA.fromMs);
  const WINDOW_TO = Number(DATA.toMs);
  const WARMUP_MS = Math.min(5 * 60 * 1000, (WINDOW_TO - WINDOW_FROM) * 0.25);
  const STORAGE_FORMAT = "losslens.playground";
  const STORAGE_VERSION = 1;
  const STORAGE_KEY = "losslens.playground.v1." + DATA.datasetId;
  const EXPERT = DATA.expert || null;
  const EXPERT_REPORT = EXPERT && EXPERT.report ? EXPERT.report : null;
  const EXPERT_INPUTS = EXPERT && Array.isArray(EXPERT.inputs) ? EXPERT.inputs : [];
  const EXPERT_TRADES = EXPERT_REPORT && Array.isArray(EXPERT_REPORT.trades)
    ? EXPERT_REPORT.trades : [];
  const C = {
    bg: "#000000",
    grid: "#1a1a1a",
    gridStrong: "#2a2a2a",
    axis: "#a8a8a8",
    text: "#d0d0d0",
    ohlc: "#b0b0b0",
    up: "#00c000",
    down: "#ff4040",
    accent: "#2f6fb3",
    predict: "#4a9eff",
    ghostUp: "#00c000",
    ghostDown: "#ff4040",
    buy: "#2f6fb3",
    sell: "#a53a3a",
    ask: "#ff9090",
    custom: "#e0e0e0",
    future: "rgba(255, 255, 255, 0.014)",
    hover: "#808080"
  };
  const PERIODS = {
    tick: { kind: "tick", label: "Tick line", short: "Tick" },
    t1: { kind: "tickbar", count: 1, label: "1 tick / bar", short: "1T" },
    t10: { kind: "tickbar", count: 10, label: "10 ticks / bar", short: "10T" },
    t100: { kind: "tickbar", count: 100, label: "100 ticks / bar", short: "100T" },
    t500: { kind: "tickbar", count: 500, label: "500 ticks / bar", short: "500T" },
    t1000: { kind: "tickbar", count: 1000, label: "1,000 ticks / bar", short: "1K" },
    m1: { kind: "timebar", ms: 60000, label: "1 minute", short: "M1" },
    m5: { kind: "timebar", ms: 300000, label: "5 minutes", short: "M5" },
    m15: { kind: "timebar", ms: 900000, label: "15 minutes", short: "M15" },
    m30: { kind: "timebar", ms: 1800000, label: "30 minutes", short: "M30" },
    h1: { kind: "timebar", ms: 3600000, label: "1 hour", short: "H1" }
  };

  const $ = function (id) { return document.getElementById(id); };
  const canvas = $("chart");
  const ctx = canvas.getContext("2d");
  const el = {
    periodButtons: $("period-buttons"),
    grid: $("grid-step"),
    zoomout: $("zoomout"),
    zoomin: $("zoomin"),
    follow: $("follow"),
    reset: $("reset"),
    next1: $("next1"),
    next10: $("next10"),
    next100: $("next100"),
    nextbar: $("nextbar"),
    progress: $("progress-fill"),
    replayStatus: $("replay-status"),
    futureTag: $("future-tag"),
    drawTicks: $("draw-ticks"),
    clearTicks: $("clear-ticks"),
    datasetLine: $("dataset-line"),
    wsymbol: $("wsymbol"),
    bid: $("bid"),
    ask: $("ask"),
    spread: $("spread"),
    dwPeriod: $("dw-period"),
    dwTime: $("dw-time"),
    dwLabelTime: $("dw-label-time"),
    dwLabelOpen: $("dw-label-open"),
    dwLabelHigh: $("dw-label-high"),
    dwLabelLow: $("dw-label-low"),
    dwLabelClose: $("dw-label-close"),
    dwLabelChange: $("dw-label-change"),
    dwLabelTicks: $("dw-label-ticks"),
    dwOpen: $("dw-open"),
    dwHigh: $("dw-high"),
    dwLow: $("dw-low"),
    dwClose: $("dw-close"),
    dwChange: $("dw-change"),
    dwTicks: $("dw-ticks"),
    rpTime: $("rp-time"),
    rpTick: $("rp-tick"),
    rpRevealed: $("rp-revealed"),
    rpWindow: $("rp-window"),
    terminalSummary: $("terminal-summary"),
    lots: $("lots"),
    sl: $("sl"),
    tp: $("tp"),
    buy: $("buy"),
    sell: $("sell"),
    tradeMessage: $("trade-message"),
    openBody: $("open-body"),
    openEmpty: $("open-empty"),
    balance: $("balance"),
    floating: $("floating"),
    equity: $("equity"),
    historyBody: $("history-body"),
    historyEmpty: $("history-empty"),
    expertEmpty: $("expert-empty"),
    expertContent: $("expert-content"),
    expertName: $("expert-name"),
    expertSource: $("expert-source"),
    expertSummary: $("expert-summary"),
    expertVisible: $("expert-visible"),
    expertInputsTable: $("expert-inputs-table"),
    expertInputsBody: $("expert-inputs-body"),
    expertInputsEmpty: $("expert-inputs-empty"),
    downloadSet: $("download-set"),
    expertTradesTable: $("expert-trades-table"),
    expertTradesBody: $("expert-trades-body"),
    expertTradesEmpty: $("expert-trades-empty"),
    expertFutureCount: $("expert-future-count"),
    expertWhatIf: $("expert-whatif"),
    expertNote: $("expert-note"),
    predStats: $("pred-stats"),
    predUndo: $("pred-undo"),
    predClear: $("pred-clear"),
    moveSize: $("move-size"),
    movePreview: $("move-preview"),
    scenarioList: $("scenario-list"),
    scenarioSummary: $("scenario-summary-body"),
    statusCenter: $("statuscenter"),
    statusRight: $("statusright"),
    sessionSymbol: $("session-symbol"),
    sessionDay: $("session-day"),
    sessionWindow: $("session-window"),
    sessionTicks: $("session-ticks"),
    sessionTape: $("session-tape"),
    sessionExpert: $("session-expert"),
    storageNote: $("storage-note"),
    scoreboard: $("scoreboard"),
    scoreBody: $("score-body"),
    scoreNote: $("score-note")
  };

  const state = {
    cursor: 0,
    period: "t100",
    gridStep: 0.10,
    lotSize: 0.01,
    moveSize: 1.00,
    drawMode: false,
    bothWays: false,
    scenarios: [],
    activeId: "",
    viewStart: 0,
    viewCount: 40,
    follow: true,
    hover: null,
    dragging: null,
    dragMoved: false,
    expertVisible: true,
    excludedExpertTickets: new Set(),
    customTicks: [],
    customBranch: null,
    customSpread: 0,
    tickDrawMode: false,
    tickStroke: null,
    message: ""
  };
  let bars = [];

  function clamp(value, low, high) {
    return Math.max(low, Math.min(high, value));
  }

  function pad2(value) {
    return value < 10 ? "0" + value : String(value);
  }

  function priceDigits() {
    const text = String(state.gridStep);
    const dot = text.indexOf(".");
    const stepDigits = dot < 0 ? 0 : text.length - dot - 1;
    return Math.min(5, Math.max(DIGITS, stepDigits));
  }

  function formatPrice(value) {
    return Number(value).toFixed(priceDigits());
  }

  function formatMoney(value) {
    const negative = value < -0.0000001;
    const text = Math.abs(value).toLocaleString("en-US", {
      minimumFractionDigits: 2, maximumFractionDigits: 2
    });
    return (negative ? "-$" : "$") + text;
  }

  function formatLots(value) {
    return String(Math.round(value * 1000) / 1000);
  }

  function formatTime(ts, withSeconds) {
    const date = new Date(ts);
    const text = pad2(date.getUTCHours()) + ":" + pad2(date.getUTCMinutes());
    return withSeconds ? text + ":" + pad2(date.getUTCSeconds()) : text;
  }

  function timeWithSeconds() {
    const spec = periodSpec();
    return spec.kind === "tick" || spec.kind === "tickbar";
  }

  function currentTick() {
    return TICKS[state.cursor];
  }

  function currentBid() {
    return currentTick()[1];
  }

  function currentAsk() {
    return currentTick()[2];
  }

  function currentTs() {
    return currentTick()[0];
  }

  function periodSpec() {
    return PERIODS[state.period] || PERIODS.t100;
  }

  function isTickMode() {
    return periodSpec().kind === "tick";
  }

  function isBarMode() {
    return !isTickMode();
  }

  function startCursorIndex() {
    const end = WINDOW_FROM + WARMUP_MS;
    let low = 0;
    let high = N - 1;
    let found = 0;
    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      if (TICKS[mid][0] <= end) {
        found = mid;
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }
    return clamp(found, 0, N - 1);
  }

  function nearestTickIndexByTime(ts) {
    let low = 0;
    let high = N - 1;
    while (low < high) {
      const mid = Math.floor((low + high) / 2);
      if (TICKS[mid][0] < ts) {
        low = mid + 1;
      } else {
        high = mid;
      }
    }
    if (low > 0) {
      const before = TICKS[low - 1][0];
      const after = TICKS[low][0];
      if (ts - before < after - ts) {
        return low - 1;
      }
    }
    return low;
  }

  function lastTickIndexBefore(ts) {
    let low = 0;
    let high = N;
    while (low < high) {
      const mid = Math.floor((low + high) / 2);
      if (TICKS[mid][0] < ts) {
        low = mid + 1;
      } else {
        high = mid;
      }
    }
    return low - 1;
  }

  function buildBars(spec, upto) {
    const result = [];
    if (spec.kind === "tickbar") {
      let bar = null;
      for (let i = 0; i <= upto; i += 1) {
        const ts = TICKS[i][0];
        const bid = TICKS[i][1];
        if (bar === null || bar.v >= spec.count) {
          bar = {
            t: ts,
            o: bid,
            h: bid,
            l: bid,
            c: bid,
            ac: TICKS[i][2],
            v: 1,
            first: i,
            last: i
          };
          result.push(bar);
        } else {
          bar.h = Math.max(bar.h, bid);
          bar.l = Math.min(bar.l, bid);
          bar.c = bid;
          bar.ac = TICKS[i][2];
          bar.v += 1;
          bar.last = i;
        }
      }
      return result;
    }
    let bar = null;
    let key = null;
    for (let i = 0; i <= upto; i += 1) {
      const ts = TICKS[i][0];
      const bid = TICKS[i][1];
      const bucket = Math.floor(ts / spec.ms) * spec.ms;
      if (bar === null || bucket !== key) {
        bar = {
          t: bucket,
          o: bid,
          h: bid,
          l: bid,
          c: bid,
          ac: TICKS[i][2],
          v: 1,
          first: i,
          last: i
        };
        key = bucket;
        result.push(bar);
      } else {
        bar.h = Math.max(bar.h, bid);
        bar.l = Math.min(bar.l, bid);
        bar.c = bid;
        bar.ac = TICKS[i][2];
        bar.v += 1;
        bar.last = i;
      }
    }
    return result;
  }

  function rebuildSeries() {
    const spec = periodSpec();
    bars = spec.kind === "tick" ? [] : buildBars(spec, state.cursor);
  }

  function rebuildTape() {
    if (state.customTicks.length && state.customBranch !== null) {
      TICKS = REAL_TICKS.slice(0, state.customBranch + 1).concat(state.customTicks);
    } else {
      TICKS = REAL_TICKS;
    }
    N = TICKS.length;
    if (state.cursor > N - 1) {
      state.cursor = Math.max(0, N - 1);
    }
  }

  function customEndIndex() {
    if (state.customTicks.length) {
      return TICKS.length - 1;
    }
    return state.customBranch === null ? state.cursor : state.customBranch;
  }

  function customPreviewTicks() {
    if (!state.customTicks.length || state.customBranch === null) {
      return [];
    }
    const out = [];
    const start = state.customBranch + 1;
    for (let i = 0; i < state.customTicks.length; i += 1) {
      const index = start + i;
      if (index > state.cursor) {
        out.push({ index: index, tick: state.customTicks[i] });
      }
    }
    return out;
  }

  function fitCustomView() {
    if (!state.customTicks.length) {
      return;
    }
    const end = N - 1;
    const start = Math.max(0, state.cursor - 15);
    const count = clamp(end - start + 1 + 15, minViewCount(), maxViewCount());
    state.viewCount = count;
    state.viewStart = clamp(end - count + 1, 0, maxViewStart());
    state.follow = false;
  }

  function toggleTickDraw() {
    if (state.tickDrawMode) {
      state.tickDrawMode = false;
      state.tickStroke = null;
      setMessage("Draw ticks off. Step forward to replay the drawn tape.");
      refreshAll();
      return;
    }
    state.tickDrawMode = true;
    state.drawMode = false;
    if (!state.customTicks.length) {
      state.customBranch = state.cursor;
      state.customSpread = Math.max(0, currentAsk() - currentBid());
    }
    setPeriod("tick");
    setMessage("Draw ticks: drag a gold path into the future. Clear ticks restores the real tape.");
    refreshAll();
    saveState();
  }

  function startTickStroke(event) {
    const rect = canvas.getBoundingClientRect();
    const box = plotBox();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    if (x < box.left || x > box.left + box.width || y < box.top || y > box.top + box.height) {
      return;
    }
    if (state.customBranch === null) {
      state.customBranch = state.cursor;
      state.customSpread = Math.max(0, currentAsk() - currentBid());
    }
    state.tickStroke = { viewStart: state.viewStart, viewCount: state.viewCount };
    state.follow = false;
    addTickStrokePoint(event);
    event.preventDefault();
  }

  function addTickStrokePoint(event) {
    if (!state.tickStroke) {
      return;
    }
    const rect = canvas.getBoundingClientRect();
    const box = plotBox();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    if (x < box.left || x > box.left + box.width || y < box.top || y > box.top + box.height) {
      return;
    }
    const raw = state.tickStroke.viewStart +
      (x - box.left) / box.width * state.tickStroke.viewCount;
    const end = customEndIndex();
    const limit = state.tickStroke.viewStart + state.tickStroke.viewCount - 1;
    const target = clamp(Math.floor(raw), end + 1, limit);
    if (target <= end) {
      return;
    }
    const range = priceRange();
    const bid = snapPrice(range.low + (box.top + box.height - y) / box.height *
      (range.high - range.low));
    const branch = state.customBranch;
    const branchTick = REAL_TICKS[branch];
    const lastTick = state.customTicks.length
      ? state.customTicks[state.customTicks.length - 1] : branchTick;
    const spread = state.customSpread >= 0 ? state.customSpread
      : Math.max(0, currentAsk() - currentBid());
    const total = target - end;
    for (let j = 1; j <= total; j += 1) {
      const fraction = j / total;
      const price = lastTick[1] + (bid - lastTick[1]) * fraction;
      const ts = lastTick[0] + j * 250;
      state.customTicks.push([
        ts,
        Number(price.toFixed(6)),
        Number((price + spread).toFixed(6))
      ]);
    }
    rebuildTape();
    refreshAll();
  }

  function endTickStroke() {
    if (!state.tickStroke) {
      return;
    }
    state.tickStroke = null;
    if (state.customTicks.length) {
      fitCustomView();
      setMessage("Drawn ticks added. Step forward to replay them; " +
        "Clear ticks restores the real tape.");
    } else {
      setMessage("Drag into the future to add ticks.");
    }
    refreshAll();
    saveState();
  }

  function clearCustomTicks() {
    if (!state.customTicks.length) {
      return;
    }
    const branch = state.customBranch;
    const ok = window.confirm("Clear the drawn ticks? This restores the real tape and clears " +
      "all scenario tickets and prediction.");
    if (!ok) {
      return;
    }
    state.customTicks = [];
    state.customBranch = null;
    state.customSpread = 0;
    state.tickDrawMode = false;
    state.tickStroke = null;
    rebuildTape();
    state.cursor = branch === null ? Math.min(state.cursor, N - 1)
      : Math.min(state.cursor, branch);
    for (const scenario of state.scenarios) {
      scenario.tickets = [];
      scenario.prediction = emptyPrediction();
    }
    state.message = "Drawn ticks cleared; real tape restored. Tickets and prediction cleared.";
    rebuildSeries();
    refitFollow();
    refreshAll();
    saveState();
  }

  function seriesLength() {
    return isTickMode() ? state.cursor + 1 : bars.length;
  }

  function customFutureSlots() {
    if (!state.customTicks.length) {
      return 0;
    }
    const pending = Math.max(0, N - (state.cursor + 1));
    if (isTickMode()) {
      return pending;
    }
    const spec = periodSpec();
    if (spec.kind === "tickbar") {
      return Math.ceil(pending / spec.count);
    }
    if (!bars.length) {
      return 0;
    }
    return Math.max(0, Math.ceil((TICKS[N - 1][0] - bars[bars.length - 1].t) / spec.ms));
  }

  function futureSlots(len) {
    let base;
    if (isTickMode()) {
      base = Math.max(40, Math.round(Math.min(len, 700) * 0.18));
    } else {
      base = Math.max(3, Math.min(12, Math.ceil(len * 0.25)));
    }
    return base + customFutureSlots();
  }

  function minViewCount() {
    return isTickMode() ? 30 : 8;
  }

  function maxViewCount() {
    return isTickMode() ? 900 : 90;
  }

  function refitFollow() {
    const len = seriesLength();
    const future = futureSlots(len);
    let count = Math.min(maxViewCount(), Math.max(minViewCount(), len + future));
    const reserved = Math.min(future, Math.max(0, count - 10));
    let start = Math.max(0, len - (count - reserved));
    start = clamp(start, 0, Math.max(0, len + future - count));
    state.viewStart = start;
    state.viewCount = count;
    state.follow = true;
  }

  function maxViewStart() {
    return Math.max(0, seriesLength() + futureSlots(seriesLength()) - state.viewCount);
  }

  function setPeriod(key) {
    if (!PERIODS[key]) {
      return;
    }
    state.period = key;
    syncPeriodButtons();
    rebuildSeries();
    refitFollow();
    state.hover = null;
    refreshAll();
    saveState();
  }

  function syncPeriodButtons() {
    document.querySelectorAll("#period-buttons button").forEach(function (button) {
      button.classList.toggle("active", button.dataset.period === state.period);
    });
  }

  function currentSeriesIndex() {
    return isTickMode() ? state.cursor : Math.max(0, bars.length - 1);
  }

  function barIndexForTick(tickIndex) {
    if (!isBarMode() || !bars.length) {
      return tickIndex;
    }
    const spec = periodSpec();
    if (spec.kind === "tickbar") {
      return Math.floor(tickIndex / spec.count);
    }
    if (tickIndex > bars[bars.length - 1].last) {
      const last = bars[bars.length - 1];
      return bars.length - 1 + (TICKS[tickIndex][0] - last.t) / spec.ms;
    }
    let low = 0;
    let high = bars.length - 1;
    let found = 0;
    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      if (bars[mid].first <= tickIndex) {
        found = mid;
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }
    return found;
  }

  function xForTick(tickIndex) {
    return xForSeries(barIndexForTick(tickIndex));
  }

  function tickIndexAtX(x) {
    const box = plotBox();
    const raw = state.viewStart + (x - box.left) / box.width * state.viewCount;
    const spec = periodSpec();
    if (spec.kind === "tick") {
      return clamp(Math.floor(raw), 0, N - 1);
    }
    if (spec.kind === "tickbar") {
      return clamp(Math.floor(raw) * spec.count, 0, N - 1);
    }
    const first = bars.length ? bars[0].t : WINDOW_FROM;
    const time = first + (Math.floor(raw) + 0.5) * spec.ms;
    return clamp(nearestTickIndexByTime(time), 0, N - 1);
  }

  function periodBarCount() {
    return isTickMode() ? 0 : bars.length;
  }

  function currentBar() {
    return bars.length ? bars[bars.length - 1] : null;
  }

  function addRow(tableBody, cells, classes) {
    const row = document.createElement("tr");
    for (let i = 0; i < cells.length; i += 1) {
      const cell = document.createElement("td");
      const item = cells[i];
      if (item && typeof item === "object" && item.node) {
        cell.appendChild(item.node);
      } else {
        cell.textContent = item === null || item === undefined ? "" : String(item);
      }
      if (classes && classes[i]) {
        cell.className = classes[i];
      }
      row.appendChild(cell);
    }
    tableBody.appendChild(row);
    return row;
  }

  function makeCellText(text) {
    return text === null || text === undefined ? "" : String(text);
  }

  function plotBox() {
    const width = Math.max(1, canvas.clientWidth);
    const height = Math.max(1, canvas.clientHeight);
    const left = 8;
    const right = 80;
    const top = 20;
    const bottom = 24;
    return {
      left: left,
      right: right,
      top: top,
      bottom: bottom,
      width: Math.max(1, width - left - right),
      height: Math.max(1, height - top - bottom),
      fullWidth: width,
      fullHeight: height
    };
  }

  function xForSeries(index) {
    const box = plotBox();
    return box.left + (index - state.viewStart + 0.5) * (box.width / state.viewCount);
  }

  function seriesIndexAtX(x) {
    const box = plotBox();
    return state.viewStart + (x - box.left) / box.width * state.viewCount;
  }

  function addPrice(low, high, price) {
    return [Math.min(low, price), Math.max(high, price)];
  }

  function predictionPoints() {
    return activeScenario().prediction.points;
  }

  function expertRevealTs(trade) {
    if (trade.found && trade.closeTsMs !== null) {
      return trade.closeTsMs;
    }
    return trade.closeUtcMs === undefined ? null : trade.closeUtcMs;
  }

  function expertVisibleTrades() {
    if (!EXPERT_REPORT || !state.expertVisible || state.customTicks.length) {
      return [];
    }
    const now = currentTs();
    return EXPERT_TRADES.filter(function (trade) {
      return trade.found && trade.inWindow && trade.closeTsMs !== null &&
        trade.closeTsMs <= now && !state.excludedExpertTickets.has(String(trade.ticket));
    });
  }

  function visibleExpertPrices() {
    const box = plotBox();
    const out = [];
    for (const trade of expertVisibleTrades()) {
      const x = xForTick(nearestTickIndexByTime(trade.closeTsMs));
      if (x >= box.left && x <= box.left + box.width) {
        out.push(trade.closePrice);
      }
    }
    return out;
  }

  function priceRange() {
    const box = plotBox();
    let low = Infinity;
    let high = -Infinity;
    if (isTickMode()) {
      const start = Math.max(0, Math.floor(state.viewStart));
      const end = Math.min(state.cursor, Math.ceil(state.viewStart + state.viewCount) - 1);
      for (let i = start; i <= end; i += 1) {
        const pair = addPrice(low, high, TICKS[i][1]);
        low = pair[0];
        high = pair[1];
        const ask = addPrice(low, high, TICKS[i][2]);
        low = ask[0];
        high = ask[1];
      }
    } else {
      const start = Math.max(0, Math.floor(state.viewStart));
      const end = Math.min(bars.length - 1, Math.ceil(state.viewStart + state.viewCount) - 1);
      for (let i = start; i <= end; i += 1) {
        low = Math.min(low, bars[i].l);
        high = Math.max(high, bars[i].h);
        low = Math.min(low, bars[i].ac);
        high = Math.max(high, bars[i].ac);
      }
      low = Math.min(low, currentAsk());
      high = Math.max(high, currentAsk());
    }
    const points = predictionPoints();
    for (const point of points) {
      const x = xForTick(point.i);
      if (x >= box.left && x <= box.left + box.width) {
        low = Math.min(low, point.price);
        high = Math.max(high, point.price);
      }
    }
    for (const price of visibleExpertPrices()) {
      low = Math.min(low, price);
      high = Math.max(high, price);
    }
    for (const item of customPreviewTicks()) {
      const x = xForTick(item.index);
      if (x >= box.left && x <= box.left + box.width) {
        low = Math.min(low, item.tick[1]);
        high = Math.max(high, item.tick[1]);
      }
    }
    if (!Number.isFinite(low) || !Number.isFinite(high)) {
      low = currentBid() - 1;
      high = currentBid() + 1;
    }
    if (high - low < 0.0000001) {
      low -= 0.5;
      high += 0.5;
    }
    const pad = Math.max((high - low) * 0.08, state.gridStep);
    low -= pad;
    high += pad;
    low = Math.floor(low / state.gridStep) * state.gridStep;
    high = Math.ceil(high / state.gridStep) * state.gridStep;
    if (high <= low) {
      high = low + state.gridStep * 4;
    }
    return { low: low, high: high };
  }

  function drawGrid(box, range, y, bidY, askY) {
    const step = state.gridStep;
    const first = Math.ceil(range.low / step) * step;
    let total = Math.floor((range.high - first) / step) + 1;
    if (!Number.isFinite(total) || total < 1) {
      total = 1;
    }
    let displayStep = step;
    if (total > 4000) {
      displayStep = step * Math.ceil(total / 4000);
      total = Math.floor((range.high - first) / displayStep) + 1;
    }
    const gap = box.height / Math.max(1, total);
    const labelEvery = Math.max(1, Math.ceil(22 / Math.max(1, gap)));
    ctx.font = "11px Tahoma, Arial, sans-serif";
    for (let i = 0; i < total; i += 1) {
      const price = first + i * displayStep;
      const py = y(price);
      ctx.beginPath();
      ctx.strokeStyle = i % 5 === 0 ? C.gridStrong : C.grid;
      ctx.lineWidth = 1;
      ctx.moveTo(box.left, Math.round(py) + 0.5);
      ctx.lineTo(box.left + box.width, Math.round(py) + 0.5);
      ctx.stroke();
      if (i % labelEvery !== 0) {
        continue;
      }
      if (Math.abs(py - bidY) < 12) {
        continue;
      }
      if (py < box.top + 4 || py > box.top + box.height - 4) {
        continue;
      }
      ctx.fillStyle = C.axis;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(formatPrice(price), box.left + box.width + 7, py);
    }
    const spec = periodSpec();
    const stepIndex = Math.max(1, Math.ceil(state.viewCount / 8));
    const firstIndex = Math.ceil(state.viewStart / stepIndex) * stepIndex;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let i = firstIndex; i < state.viewStart + state.viewCount; i += stepIndex) {
      if (i < 0 || i >= seriesLength()) {
        continue;
      }
      const x = xForSeries(i);
      if (x < box.left || x > box.left + box.width) {
        continue;
      }
      ctx.beginPath();
      ctx.strokeStyle = C.grid;
      ctx.lineWidth = 1;
      ctx.moveTo(Math.round(x) + 0.5, box.top);
      ctx.lineTo(Math.round(x) + 0.5, box.top + box.height);
      ctx.stroke();
      const ts = isTickMode() ? TICKS[i][0] : bars[i].t;
      const label = formatTime(ts, spec.kind === "tick" || spec.kind === "tickbar");
      ctx.fillStyle = C.axis;
      ctx.fillText(label, x, box.top + box.height + 5);
    }
  }

  function drawBars(box, y) {
    const start = Math.max(0, Math.floor(state.viewStart));
    const end = Math.min(bars.length - 1, Math.ceil(state.viewStart + state.viewCount) - 1);
    const bodyWidth = clamp(box.width / state.viewCount * 0.68, 1, 14);
    for (let i = start; i <= end; i += 1) {
      const bar = bars[i];
      const cx = xForSeries(i);
      if (cx < box.left - bodyWidth || cx > box.left + box.width + bodyWidth) {
        continue;
      }
      const up = bar.c >= bar.o;
      const color = up ? C.up : C.down;
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(Math.round(cx) + 0.5, y(bar.h));
      ctx.lineTo(Math.round(cx) + 0.5, y(bar.l));
      ctx.stroke();
      const top = Math.min(y(bar.o), y(bar.c));
      const height = Math.max(1, Math.abs(y(bar.c) - y(bar.o)));
      ctx.fillRect(cx - bodyWidth / 2, top, bodyWidth, height);
    }
  }

  function drawTickLine(box, y) {
    const start = Math.max(0, Math.floor(state.viewStart));
    const end = Math.min(state.cursor, Math.ceil(state.viewStart + state.viewCount) - 1);
    if (end < start) {
      return;
    }
    ctx.beginPath();
    for (let i = start; i <= end; i += 1) {
      const x = xForSeries(i);
      const py = y(TICKS[i][1]);
      if (i === start) {
        ctx.moveTo(x, py);
      } else {
        ctx.lineTo(x, py);
      }
    }
    ctx.strokeStyle = C.up;
    ctx.lineWidth = 1.2;
    ctx.stroke();
  }

  function drawAskLine(box, y) {
    if (isTickMode()) {
      const start = Math.max(0, Math.floor(state.viewStart));
      const end = Math.min(state.cursor, Math.ceil(state.viewStart + state.viewCount) - 1);
      if (end < start) {
        return;
      }
      ctx.beginPath();
      for (let i = start; i <= end; i += 1) {
        const x = xForSeries(i);
        const py = y(TICKS[i][2]);
        if (i === start) {
          ctx.moveTo(x, py);
        } else {
          ctx.lineTo(x, py);
        }
      }
    } else {
      const start = Math.max(0, Math.floor(state.viewStart));
      const end = Math.min(bars.length - 1, Math.ceil(state.viewStart + state.viewCount) - 1);
      if (end < start) {
        return;
      }
      ctx.beginPath();
      for (let i = start; i <= end; i += 1) {
        const x = xForSeries(i);
        const py = y(bars[i].ac);
        if (i === start) {
          ctx.moveTo(x, py);
        } else {
          ctx.lineTo(x, py);
        }
      }
    }
    ctx.strokeStyle = C.ask;
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  function drawExpertMarkers(box, y) {
    const trades = expertVisibleTrades();
    for (const trade of trades) {
      const index = nearestTickIndexByTime(trade.closeTsMs);
      const x = xForTick(index);
      if (x < box.left || x > box.left + box.width) {
        continue;
      }
      const py = y(trade.closePrice);
      if (py < box.top || py > box.top + box.height) {
        continue;
      }
      const buy = trade.kind.toLowerCase().indexOf("buy") === 0;
      ctx.fillStyle = buy ? C.down : C.up;
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1;
      ctx.beginPath();
      if (buy) {
        ctx.moveTo(x, py + 8);
        ctx.lineTo(x - 5, py + 1);
        ctx.lineTo(x + 5, py + 1);
      } else {
        ctx.moveTo(x, py - 8);
        ctx.lineTo(x - 5, py - 1);
        ctx.lineTo(x + 5, py - 1);
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(x, py, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = buy ? C.down : C.up;
      ctx.fill();
      ctx.strokeStyle = "#ffffff";
      ctx.stroke();
    }
  }

  function drawCurrentPrices(box, y) {
    const bid = currentBid();
    const bidY = y(bid);
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.left, box.top, box.width, box.height);
    ctx.clip();
    ctx.beginPath();
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = "#707070";
    ctx.lineWidth = 1;
    ctx.moveTo(box.left, Math.round(bidY) + 0.5);
    ctx.lineTo(box.left + box.width, Math.round(bidY) + 0.5);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
    drawPriceTag(box, clamp(bidY - 8, box.top + 1, box.top + box.height - 17),
      formatPrice(bid), C.up, "#000000");
  }

  function drawPriceTag(box, top, text, background, color) {
    ctx.font = "11px Tahoma, Arial, sans-serif";
    const width = box.right - 4;
    const left = box.left + box.width + 2;
    ctx.fillStyle = background;
    ctx.fillRect(left, top, width, 16);
    ctx.strokeStyle = background;
    ctx.lineWidth = 1;
    ctx.strokeRect(left + 0.5, top + 0.5, width - 1, 15);
    ctx.fillStyle = color;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, left + width / 2, top + 8);
  }

  function scoredPoints() {
    const prediction = activeScenario().prediction;
    const points = prediction.points;
    const scored = [];
    const anchorIndex = prediction.anchorIndex === null
      ? 0 : clamp(Math.round(prediction.anchorIndex), 0, N - 1);
    for (let i = 0; i < points.length; i += 1) {
      const point = points[i];
      if (point.i > state.cursor) {
        break;
      }
      const previous = i > 0 ? points[i - 1] : null;
      const previousPredicted = previous ? previous.price : prediction.anchorPrice;
      const previousActual = previous ? TICKS[previous.i][1] : TICKS[anchorIndex][1];
      const actual = TICKS[point.i][1];
      const base = Number.isFinite(previousPredicted) ? previousPredicted : actual;
      const predictedDirection = Math.sign(point.price - base);
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

  function predictionStats() {
    const scored = scoredPoints();
    if (!scored.length) {
      return { count: 0, mae: null, hitRate: null };
    }
    let sum = 0;
    let hits = 0;
    for (const item of scored) {
      sum += item.error;
      if (item.hit) {
        hits += 1;
      }
    }
    return { count: scored.length, mae: sum / scored.length, hitRate: hits / scored.length };
  }

  function drawCustomPreview(box, y) {
    const items = customPreviewTicks();
    if (!items.length) {
      return;
    }
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.left, box.top, box.width, box.height);
    ctx.clip();
    ctx.beginPath();
    ctx.moveTo(xForSeries(currentSeriesIndex()), y(currentBid()));
    for (const item of items) {
      ctx.lineTo(xForTick(item.index), y(item.tick[1]));
    }
    ctx.setLineDash([4, 4]);
    ctx.lineWidth = 1.4;
    ctx.strokeStyle = C.custom;
    ctx.stroke();
    ctx.setLineDash([]);
    for (const item of items) {
      ctx.beginPath();
      ctx.arc(xForTick(item.index), y(item.tick[1]), 1.8, 0, Math.PI * 2);
      ctx.fillStyle = C.custom;
      ctx.fill();
    }
    ctx.restore();
  }

  function drawPrediction(box, y) {
    const scenario = activeScenario();
    const prediction = scenario.prediction;
    if (!prediction.points.length) {
      return;
    }
    const anchorIndex = prediction.anchorIndex === null ? 0 : prediction.anchorIndex;
    const anchorPrice = Number.isFinite(prediction.anchorPrice)
      ? prediction.anchorPrice : TICKS[anchorIndex][1];
    const scores = scoredPoints();
    const scoreMap = new Map();
    for (const item of scores) {
      scoreMap.set(item.point, item);
    }
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.left, box.top, box.width, box.height);
    ctx.clip();
    ctx.beginPath();
    ctx.moveTo(xForTick(anchorIndex), y(anchorPrice));
    for (const point of prediction.points) {
      ctx.lineTo(xForTick(point.i), y(point.price));
    }
    ctx.setLineDash([5, 4]);
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = C.predict;
    ctx.stroke();
    ctx.setLineDash([]);
    for (const point of prediction.points) {
      const score = scoreMap.get(point);
      ctx.beginPath();
      ctx.arc(xForTick(point.i), y(point.price), 3, 0, Math.PI * 2);
      if (score) {
        ctx.fillStyle = score.hit ? C.ghostUp : C.ghostDown;
        ctx.fill();
      } else {
        ctx.strokeStyle = C.predict;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  function drawPill(x, y, text, background, color) {
    ctx.font = "10px Tahoma, Arial, sans-serif";
    const width = ctx.measureText(text).width + 12;
    const left = clamp(x - width, plotBox().left + 2, plotBox().left + plotBox().width - width - 2);
    const top = clamp(y - 8, plotBox().top + 2, plotBox().top + plotBox().height - 18);
    ctx.fillStyle = background;
    ctx.fillRect(left, top, width, 16);
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = 1;
    ctx.strokeRect(left + 0.5, top + 0.5, width - 1, 15);
    ctx.fillStyle = color;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(text, left + 6, top + 8);
  }

  function drawPredictionPreview(box, y, range) {
    if (!state.drawMode || state.tickDrawMode || !state.hover || !state.hover.future) {
      return;
    }
    const price = snapPrice(range.low + (box.top + box.height - state.hover.y) / box.height *
      (range.high - range.low));
    const x = xForSeries(state.hover.seriesIndex);
    const points = predictionPoints();
    let startX = xForSeries(currentSeriesIndex());
    let startY = y(currentBid());
    if (points.length) {
      const last = points[points.length - 1];
      startX = xForTick(last.i);
      startY = y(last.price);
    }
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.left, box.top, box.width, box.height);
    ctx.clip();
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(x, y(price));
    ctx.setLineDash([2, 3]);
    ctx.lineWidth = 1.1;
    ctx.strokeStyle = C.predict;
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.arc(x, y(price), 3.2, 0, Math.PI * 2);
    ctx.strokeStyle = C.predict;
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.restore();
    drawPill(x, y(price) - 18, "ADD " + formatPrice(price), C.predict, "#ffffff");
  }

  function drawGhosts(box, y) {
    if (!state.bothWays) {
      return;
    }
    const scenario = activeScenario();
    const future = [];
    for (const point of scenario.prediction.points) {
      if (point.i > state.cursor) {
        future.push(point);
      }
    }
    const startX = xForSeries(currentSeriesIndex());
    const startY = y(currentBid());
    const up = [{ x: startX, y: startY, price: currentBid() }];
    const down = [{ x: startX, y: startY, price: currentBid() }];
    if (future.length) {
      for (const point of future) {
        const price = point.price;
        up.push({ x: xForTick(point.i), y: y(price), price: price });
        const mirror = currentBid() - (price - currentBid());
        down.push({ x: xForTick(point.i), y: y(mirror), price: mirror });
      }
    } else {
      const rightX = box.left + box.width - 2;
      const upPrice = snapPrice(currentBid() + state.moveSize);
      const downPrice = snapPrice(currentBid() - state.moveSize);
      up.push({ x: rightX, y: y(upPrice), price: upPrice });
      down.push({ x: rightX, y: y(downPrice), price: downPrice });
    }
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.left, box.top, box.width, box.height);
    ctx.clip();
    ctx.setLineDash([3, 5]);
    ctx.lineWidth = 1.3;
    ctx.strokeStyle = C.ghostDown;
    if (future.length === 0) {
      ctx.strokeStyle = C.ghostUp;
      ctx.beginPath();
      for (let i = 0; i < up.length; i += 1) {
        if (i === 0) {
          ctx.moveTo(up[i].x, up[i].y);
        } else {
          ctx.lineTo(up[i].x, up[i].y);
        }
      }
      ctx.stroke();
      ctx.strokeStyle = C.ghostDown;
    }
    ctx.beginPath();
    for (let i = 0; i < down.length; i += 1) {
      if (i === 0) {
        ctx.moveTo(down[i].x, down[i].y);
      } else {
        ctx.lineTo(down[i].x, down[i].y);
      }
    }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
    const spread = currentAsk() - currentBid();
    const upLast = up[up.length - 1];
    const downLast = down[down.length - 1];
    const upPnl = floatingAt(scenario, upLast.price, upLast.price + spread);
    const downPnl = floatingAt(scenario, downLast.price, downLast.price + spread);
    drawPill(upLast.x, upLast.y + 14, "UP " + formatMoney(upPnl), C.up, "#000000");
    drawPill(downLast.x, downLast.y + 14, "DOWN " + formatMoney(downPnl), C.down, "#ffffff");
  }

  function drawCursor(box) {
    const x = xForSeries(currentSeriesIndex());
    if (x < box.left || x > box.left + box.width) {
      return;
    }
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.left, box.top, box.width, box.height);
    ctx.clip();
    ctx.beginPath();
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = "rgba(47, 111, 179, 0.8)";
    ctx.lineWidth = 1;
    ctx.moveTo(Math.round(x) + 0.5, box.top);
    ctx.lineTo(Math.round(x) + 0.5, box.top + box.height);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
    ctx.font = "9px Tahoma, Arial, sans-serif";
    const width = ctx.measureText("NOW").width + 10;
    let left = x - width / 2;
    left = clamp(left, box.left + 1, box.left + box.width - width - 1);
    ctx.fillStyle = C.accent;
    ctx.fillRect(left, box.top + 2, width, 14);
    ctx.strokeStyle = "#245786";
    ctx.strokeRect(left + 0.5, box.top + 2.5, width - 1, 13);
    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("NOW", left + width / 2, box.top + 9);
  }

  function hoverPrice() {
    if (!state.hover || state.hover.future) {
      return null;
    }
    if (isTickMode()) {
      return TICKS[state.hover.seriesIndex][1];
    }
    const bar = bars[state.hover.seriesIndex];
    return bar ? bar.c : null;
  }

  function drawHover(box, y) {
    if (!state.hover) {
      return;
    }
    const x = xForSeries(state.hover.seriesIndex);
    if (x < box.left || x > box.left + box.width) {
      return;
    }
    const price = hoverPrice();
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.left, box.top, box.width, box.height);
    ctx.clip();
    ctx.setLineDash([2, 3]);
    ctx.strokeStyle = C.hover;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(Math.round(x) + 0.5, box.top);
    ctx.lineTo(Math.round(x) + 0.5, box.top + box.height);
    if (price !== null) {
      const py = y(price);
      ctx.moveTo(box.left, Math.round(py) + 0.5);
      ctx.lineTo(box.left + box.width, Math.round(py) + 0.5);
    }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
    if (price !== null) {
      const py = y(price);
      drawPriceTag(box, clamp(py - 8, box.top + 1, box.top + box.height - 17),
        formatPrice(price), "#d0d0d0", "#111111");
    }
  }

  function drawOverlay(box) {
    const spec = periodSpec();
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.font = "bold 11px Tahoma, Arial, sans-serif";
    ctx.fillStyle = C.text;
    ctx.fillText(DATA.symbol + ", " + spec.short, box.left + 4, 4);
    ctx.font = "10px Tahoma, Arial, sans-serif";
    if (isTickMode()) {
      const tick = currentTick();
      ctx.fillStyle = C.ask;
      ctx.fillText("B " + formatPrice(tick[1]) + "   A " + formatPrice(tick[2]) +
        "   S " + formatPrice(tick[2] - tick[1]), box.left + 4, 19);
      return;
    }
    let shown = currentBar();
    if (state.hover && !state.hover.future && bars[state.hover.seriesIndex]) {
      shown = bars[state.hover.seriesIndex];
    }
    if (!shown) {
      return;
    }
    ctx.fillStyle = C.ohlc;
    ctx.fillText("O " + formatPrice(shown.o) + "   H " + formatPrice(shown.h) +
      "   L " + formatPrice(shown.l) + "   C " + formatPrice(shown.c) +
      "   V " + shown.v, box.left + 4, 19);
    ctx.fillStyle = C.ask;
    ctx.fillText("B " + formatPrice(shown.c) + "   A " + formatPrice(shown.ac) +
      "   S " + formatPrice(shown.ac - shown.c), box.left + 4, 32);
  }

  function draw() {
    const box = plotBox();
    const range = priceRange();
    const y = function (price) {
      return box.top + (range.high - price) / (range.high - range.low) * box.height;
    };
    ctx.fillStyle = C.bg;
    ctx.fillRect(0, 0, box.fullWidth, box.fullHeight);
    if (box.width <= 0 || box.height <= 0) {
      return;
    }
    const slot = box.width / state.viewCount;
    const futureX = box.left + (seriesLength() - state.viewStart) * slot;
    if (futureX < box.left + box.width) {
      ctx.fillStyle = C.future;
      ctx.fillRect(Math.max(box.left, futureX), box.top,
        box.left + box.width - Math.max(box.left, futureX), box.height);
    }
    drawGrid(box, range, y, y(currentBid()), y(currentAsk()));
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.left, box.top, box.width, box.height);
    ctx.clip();
    if (isTickMode()) {
      drawTickLine(box, y);
    } else {
      drawBars(box, y);
    }
    drawAskLine(box, y);
    drawCustomPreview(box, y);
    drawExpertMarkers(box, y);
    drawPrediction(box, y);
    drawPredictionPreview(box, y, range);
    drawGhosts(box, y);
    ctx.restore();
    drawCurrentPrices(box, y);
    drawCursor(box);
    drawHover(box, y);
    drawOverlay(box);
    ctx.strokeStyle = "#333333";
    ctx.lineWidth = 1;
    ctx.strokeRect(box.left + 0.5, box.top + 0.5, box.width - 1, box.height - 1);
  }

  function resize() {
    const parent = canvas.parentElement;
    const rect = parent.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.floor(rect.width));
    const height = Math.max(1, Math.floor(rect.height));
    canvas.width = Math.max(1, Math.floor(width * dpr));
    canvas.height = Math.max(1, Math.floor(height * dpr));
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }

  function snapPrice(price) {
    return Number((Math.round(price / state.gridStep) * state.gridStep).toFixed(6));
  }

  function hoverAt(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    const box = plotBox();
    const mx = clientX - rect.left;
    const my = clientY - rect.top;
    if (mx < box.left || mx > box.left + box.width || my < box.top || my > box.top + box.height) {
      return null;
    }
    const raw = seriesIndexAtX(mx);
    let index = Math.floor(raw);
    const len = seriesLength();
    const lastSlot = len + futureSlots(len) - 1;
    index = clamp(index, 0, lastSlot);
    return { seriesIndex: index, future: index >= len, x: xForSeries(index), y: my };
  }

  function refreshDataWindow() {
    const spec = periodSpec();
    el.dwPeriod.textContent = spec.label;
    if (isTickMode()) {
      let tick = currentTick();
      let index = state.cursor;
      if (state.hover && !state.hover.future) {
        tick = TICKS[state.hover.seriesIndex];
        index = state.hover.seriesIndex;
      }
      el.dwLabelTime.textContent = "Tick time";
      el.dwLabelOpen.textContent = "Bid";
      el.dwLabelHigh.textContent = "Ask";
      el.dwLabelLow.textContent = "Spread";
      el.dwLabelClose.textContent = "Tick";
      el.dwLabelChange.textContent = "Revealed";
      el.dwLabelTicks.textContent = "Window";
      el.dwTime.textContent = formatTime(tick[0], true) + " UTC";
      el.dwOpen.textContent = formatPrice(tick[1]);
      el.dwHigh.textContent = formatPrice(tick[2]);
      el.dwLow.textContent = (tick[2] - tick[1]).toFixed(DIGITS);
      el.dwClose.textContent = (index + 1).toLocaleString();
      el.dwChange.textContent = (state.cursor + 1).toLocaleString() + " / " + N.toLocaleString();
      el.dwTicks.textContent = DATA.window.from + "-" + DATA.window.to;
      return;
    }
    el.dwLabelTime.textContent = "Bar time";
    el.dwLabelOpen.textContent = "Open";
    el.dwLabelHigh.textContent = "High";
    el.dwLabelLow.textContent = "Low";
    el.dwLabelClose.textContent = "Close";
    el.dwLabelChange.textContent = "Change";
    el.dwLabelTicks.textContent = "Ticks";
    let bar = currentBar();
    if (state.hover && !state.hover.future && bars[state.hover.seriesIndex]) {
      bar = bars[state.hover.seriesIndex];
    }
    if (!bar) {
      el.dwTime.textContent = "-";
      el.dwOpen.textContent = "-";
      el.dwHigh.textContent = "-";
      el.dwLow.textContent = "-";
      el.dwClose.textContent = "-";
      el.dwChange.textContent = "-";
      el.dwTicks.textContent = "-";
      return;
    }
    const change = bar.c - bar.o;
    el.dwTime.textContent = formatTime(bar.t, spec.kind === "tickbar") + " UTC";
    el.dwOpen.textContent = formatPrice(bar.o);
    el.dwHigh.textContent = formatPrice(bar.h);
    el.dwLow.textContent = formatPrice(bar.l);
    el.dwClose.textContent = formatPrice(bar.c);
    el.dwChange.textContent = (change >= 0 ? "+" : "") + change.toFixed(DIGITS);
    el.dwTicks.textContent = spec.kind === "tickbar" ? bar.v + " / " + spec.count : String(bar.v);
  }

  function refreshStatus() {
    const spec = periodSpec();
    let center = DATA.symbol + " · " + spec.label + " · " + seriesLength() +
      (isTickMode() ? " ticks" : " bars") + " · tick " + (state.cursor + 1) +
      " / " + N + " · view " + state.viewCount + (isTickMode() ? " ticks" : " bars") +
      (state.customTicks.length ? " · drawn" : "");
    if (state.hover) {
      if (state.hover.future) {
        center = "Future hidden · click ahead only while drawing";
      } else {
        const ts = isTickMode() ? TICKS[state.hover.seriesIndex][0]
          : bars[state.hover.seriesIndex].t;
        center = DATA.symbol + " · " + formatTime(ts, timeWithSeconds()) +
          " · " + (isTickMode() ? formatPrice(TICKS[state.hover.seriesIndex][1])
            : formatPrice(bars[state.hover.seriesIndex].c));
      }
    } else if (state.message) {
      center = state.message;
    }
    el.statusCenter.textContent = center;
    el.statusRight.textContent = state.customTicks.length
      ? REAL_N.toLocaleString() + " real + " + state.customTicks.length.toLocaleString() +
        " drawn"
      : N.toLocaleString() + " Dukascopy ticks · UTC";
  }

  function refreshTapeTag() {
    if (state.tickDrawMode) {
      el.futureTag.textContent = "DRAW TICKS";
    } else if (state.customTicks.length) {
      el.futureTag.textContent = "DRAWN TAPE";
    } else {
      el.futureTag.textContent = "FUTURE";
    }
  }

  function refreshReplay() {
    const ts = currentTs();
    el.replayStatus.textContent = "Tick " + (state.cursor + 1).toLocaleString() +
      " / " + N.toLocaleString() + " · " + formatTime(ts, true) + " UTC";
    el.progress.style.width = ((state.cursor + 1) / N * 100).toFixed(2) + "%";
    el.rpTime.textContent = formatTime(ts, true) + " UTC";
    el.rpTick.textContent = (state.cursor + 1).toLocaleString() + " / " + N.toLocaleString();
    el.rpRevealed.textContent = (state.cursor + 1).toLocaleString() + " of " +
      N.toLocaleString();
    el.rpWindow.textContent = DATA.window.from + "-" + DATA.window.to + " UTC";
    el.nextbar.disabled = isTickMode();
    el.follow.classList.toggle("active", state.follow);
    el.zoomout.disabled = state.viewCount >= maxViewCount();
    el.zoomin.disabled = state.viewCount <= minViewCount();
  }

  function ticketPnl(ticket, exitPrice) {
    const direction = ticket.side === "buy" ? 1 : -1;
    return (exitPrice - ticket.entry) * direction * ticket.lots * CONTRACT_SIZE;
  }

  function floatingAt(scenario, bid, ask) {
    let total = 0;
    for (const ticket of scenario.tickets) {
      if (ticket.status !== "open") {
        continue;
      }
      total += ticketPnl(ticket, ticket.side === "buy" ? bid : ask);
    }
    return total;
  }

  function floatingNow(scenario) {
    return floatingAt(scenario, currentBid(), currentAsk());
  }

  function balanceOf(scenario) {
    let total = START_BALANCE;
    for (const ticket of scenario.tickets) {
      if (ticket.status === "closed") {
        total += ticket.realized;
      }
    }
    return total;
  }

  function equityOf(scenario) {
    return balanceOf(scenario) + floatingNow(scenario);
  }

  function openTicket(side) {
    const lots = Number(el.lots.value);
    if (!Number.isFinite(lots) || lots <= 0) {
      setMessage("Volume must be a positive number.");
      return;
    }
    const sl = optionalPrice(el.sl, "S/L");
    if (!sl.ok) {
      return;
    }
    const tp = optionalPrice(el.tp, "T/P");
    if (!tp.ok) {
      return;
    }
    const entry = side === "buy" ? currentAsk() : currentBid();
    if (sl.value !== null) {
      if (side === "buy" && sl.value >= entry) {
        setMessage("A buy needs S/L below its ask entry.");
        return;
      }
      if (side === "sell" && sl.value <= entry) {
        setMessage("A sell needs S/L above its bid entry.");
        return;
      }
    }
    if (tp.value !== null) {
      if (side === "buy" && tp.value <= entry) {
        setMessage("A buy needs T/P above its ask entry.");
        return;
      }
      if (side === "sell" && tp.value >= entry) {
        setMessage("A sell needs T/P below its bid entry.");
        return;
      }
    }
    const scenario = activeScenario();
    const ticket = {
      id: makeId("t"), side: side, lots: lots, entry: entry, sl: sl.value, tp: tp.value,
      openIndex: state.cursor, status: "open", closeIndex: null, closePrice: null,
      closeReason: null, realized: 0
    };
    scenario.tickets.push(ticket);
    checkStops(ticket, currentTick(), state.cursor);
    state.lotSize = lots;
    if (ticket.status === "closed") {
      setMessage("Ticket closed by " + ticket.closeReason + " on the entry tick.");
    } else {
      setMessage(side === "buy" ? "Buy opened at the ask." : "Sell opened at the bid.");
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
    if (!Number.isFinite(value) || value <= 0) {
      setMessage(label + " must be a positive price, or blank.");
      return { ok: false, value: null };
    }
    return { ok: true, value: value };
  }

  function closeTicket(ticketId) {
    const scenario = activeScenario();
    for (const ticket of scenario.tickets) {
      if (ticket.id !== ticketId || ticket.status !== "open") {
        continue;
      }
      const price = ticket.side === "buy" ? currentBid() : currentAsk();
      settle(ticket, price, "manual", state.cursor);
      setMessage("Ticket closed at the current " + (ticket.side === "buy" ? "bid" : "ask") + ".");
      refreshAll();
      saveState();
      return;
    }
  }

  function settle(ticket, price, reason, index) {
    ticket.status = "closed";
    ticket.closeIndex = index;
    ticket.closePrice = price;
    ticket.closeReason = reason;
    ticket.realized = ticketPnl(ticket, price);
  }

  function checkStops(ticket, tick, index) {
    if (ticket.side === "buy") {
      if (ticket.sl !== null && tick[1] <= ticket.sl) {
        settle(ticket, ticket.sl, "S/L", index);
        return;
      }
      if (ticket.tp !== null && tick[1] >= ticket.tp) {
        settle(ticket, ticket.tp, "T/P", index);
      }
      return;
    }
    if (ticket.sl !== null && tick[2] >= ticket.sl) {
      settle(ticket, ticket.sl, "S/L", index);
      return;
    }
    if (ticket.tp !== null && tick[2] <= ticket.tp) {
      settle(ticket, ticket.tp, "T/P", index);
    }
  }

  function advanceTo(target) {
    const goal = clamp(target, state.cursor, N - 1);
    if (goal === state.cursor) {
      setMessage("Already at the last tick.");
      return;
    }
    const oldCursor = state.cursor;
    state.message = "";
    el.tradeMessage.textContent = "";
    for (let k = oldCursor + 1; k <= goal; k += 1) {
      const tick = TICKS[k];
      for (const scenario of state.scenarios) {
        for (const ticket of scenario.tickets) {
          if (ticket.status === "open") {
            checkStops(ticket, tick, k);
          }
        }
      }
    }
    state.cursor = goal;
    let closed = 0;
    for (const scenario of state.scenarios) {
      for (const ticket of scenario.tickets) {
        if (ticket.status === "closed" && ticket.closeIndex !== null &&
            ticket.closeIndex > oldCursor && ticket.closeIndex <= goal) {
          closed += 1;
        }
      }
    }
    if (closed) {
      state.message = closed + (closed === 1 ? " ticket closed" : " tickets closed") +
        " by S/L or T/P.";
    }
    rebuildSeries();
    if (state.follow) {
      refitFollow();
    }
    state.hover = null;
    refreshAll();
    saveState();
  }

  function advance(count) {
    advanceTo(state.cursor + count);
  }

  function nextBar() {
    if (isTickMode()) {
      advance(10);
      return;
    }
    const spec = periodSpec();
    if (spec.kind === "tickbar") {
      const complete = (state.cursor + 1) % spec.count;
      const step = complete === 0 ? spec.count : spec.count - complete;
      advance(step);
      return;
    }
    const bucket = Math.floor(currentTs() / spec.ms) * spec.ms;
    let targetTime = bucket + spec.ms;
    let target = lastTickIndexBefore(targetTime);
    if (target <= state.cursor) {
      targetTime += spec.ms;
      target = lastTickIndexBefore(targetTime);
    }
    advanceTo(target);
  }

  function resetReplay() {
    const hasData = state.scenarios.some(function (scenario) {
      return scenario.tickets.length > 0 || scenario.prediction.points.length > 0;
    });
    if (hasData || state.excludedExpertTickets.size) {
      const ok = window.confirm("Reset the replay? This clears every scenario's tickets and " +
        "prediction and returns to the first 5 minutes.");
      if (!ok) {
        return;
      }
    }
    state.cursor = startCursorIndex();
    state.drawMode = false;
    state.bothWays = false;
    state.excludedExpertTickets = new Set();
    state.expertVisible = true;
    for (const scenario of state.scenarios) {
      scenario.tickets = [];
      scenario.prediction = emptyPrediction();
    }
    state.message = "Reset to the first 5 minutes. Tickets and prediction cleared.";
    rebuildSeries();
    refitFollow();
    refreshAll();
    saveState();
  }

  function makeId(prefix) {
    return prefix + Math.random().toString(36).slice(2, 8) + Date.now().toString(36);
  }

  function emptyPrediction() {
    return { anchorIndex: null, anchorPrice: null, points: [] };
  }

  function makeScenario(name) {
    return { id: makeId("s"), name: name, tickets: [], prediction: emptyPrediction() };
  }

  function activeScenario() {
    let found = null;
    for (const scenario of state.scenarios) {
      if (scenario.id === state.activeId) {
        found = scenario;
        break;
      }
    }
    if (found === null) {
      found = state.scenarios[0];
      state.activeId = found.id;
    }
    return found;
  }

  function addScenario() {
    const scenario = makeScenario("Scenario " + (state.scenarios.length + 1));
    state.scenarios.push(scenario);
    state.activeId = scenario.id;
    setMessage("Scenario added.");
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
    if (!trimmed) {
      setMessage("A scenario needs a name.");
      return;
    }
    scenario.name = trimmed;
    refreshAll();
    saveState();
  }

  function duplicateScenario() {
    const source = activeScenario();
    const copy = {
      id: makeId("s"),
      name: (source.name + " copy").slice(0, 40),
      tickets: source.tickets.map(function (ticket) {
        return Object.assign({}, ticket, { id: makeId("t") });
      }),
      prediction: JSON.parse(JSON.stringify(source.prediction))
    };
    state.scenarios.push(copy);
    state.activeId = copy.id;
    setMessage("Scenario duplicated.");
    refreshAll();
    saveState();
  }

  function deleteScenario() {
    if (state.scenarios.length === 1) {
      setMessage("Keep at least one scenario.");
      return;
    }
    const index = state.scenarios.findIndex(function (scenario) {
      return scenario.id === state.activeId;
    });
    const scenario = state.scenarios[index];
    if (!window.confirm("Delete scenario \"" + scenario.name + "\"?")) {
      return;
    }
    state.scenarios.splice(index, 1);
    state.activeId = state.scenarios[Math.max(0, index - 1)].id;
    refreshAll();
    saveState();
  }

  function toggleDraw() {
    state.drawMode = !state.drawMode;
    if (state.drawMode) {
      state.tickDrawMode = false;
    }
    setMessage(state.drawMode ? "Draw prediction on. Click future chart points."
      : "Draw prediction off.");
    refreshAll();
  }

  function toggleBoth() {
    state.bothWays = !state.bothWays;
    refreshAll();
  }

  function addPredictionPoint(index, price) {
    if (state.cursor >= N - 1) {
      setMessage("The cursor is at the last tick; reset to draw again.");
      return;
    }
    const target = clamp(index, state.cursor + 1, N - 1);
    const scenario = activeScenario();
    const prediction = scenario.prediction;
    if (prediction.anchorIndex === null) {
      prediction.anchorIndex = state.cursor;
      prediction.anchorPrice = currentBid();
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
    setMessage("Prediction " + formatPrice(price) + " at " + formatTime(TICKS[target][0], true) +
      " UTC.");
    refreshAll();
    saveState();
  }

  function undoPrediction() {
    const prediction = activeScenario().prediction;
    if (!prediction.points.length) {
      return;
    }
    prediction.points.pop();
    if (!prediction.points.length) {
      prediction.anchorIndex = null;
      prediction.anchorPrice = null;
    }
    setMessage("Last prediction point removed.");
    refreshAll();
    saveState();
  }

  function clearPrediction() {
    const scenario = activeScenario();
    if (!scenario.prediction.points.length) {
      return;
    }
    scenario.prediction = emptyPrediction();
    setMessage("Prediction cleared.");
    refreshAll();
    saveState();
  }

  function handleDrawClick(event) {
    if (!state.drawMode) {
      return;
    }
    const rect = canvas.getBoundingClientRect();
    const box = plotBox();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    if (x < box.left || x > box.left + box.width || y < box.top || y > box.top + box.height) {
      return;
    }
    if (state.cursor >= N - 1) {
      setMessage("The cursor is at the last tick; reset to draw again.");
      return;
    }
    const target = tickIndexAtX(x);
    if (target <= state.cursor) {
      setMessage("Draw ahead of the cursor; step forward or click farther right.");
      return;
    }
    const range = priceRange();
    const price = snapPrice(range.low + (box.top + box.height - y) / box.height *
      (range.high - range.low));
    addPredictionPoint(target, price);
  }

  function zoomBy(factor, anchorX) {
    const box = plotBox();
    const fraction = clamp((anchorX - box.left) / box.width, 0, 1);
    const anchor = state.viewStart + fraction * state.viewCount;
    const count = clamp(Math.round(state.viewCount * factor), minViewCount(), maxViewCount());
    state.viewCount = count;
    state.viewStart = clamp(Math.round(anchor - fraction * count), 0, maxViewStart());
    state.follow = false;
    state.hover = null;
    refreshReplay();
    refreshDataWindow();
    refreshStatus();
    draw();
  }

  function zoomIn() {
    zoomBy(0.8, plotBox().left + plotBox().width / 2);
  }

  function zoomOut() {
    zoomBy(1.25, plotBox().left + plotBox().width / 2);
  }

  function followCursor() {
    refitFollow();
    state.hover = null;
    refreshReplay();
    refreshDataWindow();
    refreshStatus();
    draw();
  }

  function panBy(delta) {
    state.viewStart = clamp(state.viewStart + delta, 0, maxViewStart());
    state.follow = false;
    state.hover = null;
    refreshReplay();
    refreshDataWindow();
    refreshStatus();
    draw();
  }

  function onWheel(event) {
    event.preventDefault();
    event.stopPropagation();
    const rect = canvas.getBoundingClientRect();
    const factor = event.deltaY > 0 ? 1.2 : 0.8;
    zoomBy(factor, event.clientX - rect.left);
  }

  function onMouseDown(event) {
    if (state.tickDrawMode) {
      startTickStroke(event);
      return;
    }
    const rect = canvas.getBoundingClientRect();
    state.dragging = {
      x: event.clientX,
      start: state.viewStart,
      boxWidth: plotBox().width
    };
    state.dragMoved = false;
    canvas.style.cursor = "grabbing";
    event.preventDefault();
  }

  function onMouseMove(event) {
    if (state.tickStroke) {
      addTickStrokePoint(event);
      return;
    }
    if (state.dragging) {
      const dx = event.clientX - state.dragging.x;
      if (Math.abs(dx) > 2) {
        state.dragMoved = true;
        const slots = Math.round(dx / (state.dragging.boxWidth / state.viewCount));
        state.viewStart = clamp(state.dragging.start - slots, 0, maxViewStart());
        state.follow = false;
        state.hover = null;
        refreshReplay();
        refreshStatus();
        draw();
      }
      return;
    }
    state.hover = hoverAt(event.clientX, event.clientY);
    refreshDataWindow();
    refreshStatus();
    draw();
  }

  function onMouseUp(event) {
    if (state.tickStroke) {
      endTickStroke();
      return;
    }
    const wasDragging = state.dragging !== null;
    const moved = state.dragMoved;
    state.dragging = null;
    state.dragMoved = false;
    canvas.style.cursor = "crosshair";
    if (wasDragging && !moved && state.drawMode) {
      handleDrawClick(event);
    }
  }

  function onMouseLeave() {
    if (state.dragging === null) {
      state.hover = null;
      refreshDataWindow();
      refreshStatus();
      draw();
    }
  }

  function setMessage(text) {
    state.message = text;
    el.tradeMessage.textContent = text;
    refreshStatus();
  }

  function serializeState() {
    return {
      format: STORAGE_FORMAT,
      version: STORAGE_VERSION,
      datasetId: DATA.datasetId,
      tickCount: REAL_N,
      cursor: state.cursor,
      period: state.period,
      gridStep: state.gridStep,
      lotSize: state.lotSize,
      moveSize: state.moveSize,
      activeId: state.activeId,
      expertVisible: state.expertVisible,
      excludedExpertTickets: Array.from(state.excludedExpertTickets),
      customBranch: state.customBranch,
      customTicks: state.customTicks,
      customSpread: state.customSpread,
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
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(serializeState()));
      el.storageNote.textContent = "Scenarios auto-save in this browser.";
    } catch (error) {
      el.storageNote.textContent = "Auto-save unavailable; use Export scenarios.";
    }
  }

  function finiteOrNull(value) {
    return typeof value === "number" && Number.isFinite(value) ? value : null;
  }

  function sanitizeTicket(raw, cursor) {
    if (!raw || (raw.side !== "buy" && raw.side !== "sell")) {
      return null;
    }
    const lots = Number(raw.lots);
    const entry = Number(raw.entry);
    const openIndex = Math.round(Number(raw.openIndex));
    if (!Number.isFinite(lots) || lots <= 0 || !Number.isFinite(entry)) {
      return null;
    }
    if (!Number.isFinite(openIndex) || openIndex < 0 || openIndex > cursor) {
      return null;
    }
    const status = raw.status === "closed" ? "closed" : "open";
    const ticket = {
      id: typeof raw.id === "string" ? raw.id : makeId("t"),
      side: raw.side,
      lots: lots,
      entry: entry,
      sl: finiteOrNull(raw.sl),
      tp: finiteOrNull(raw.tp),
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
      if (!Number.isFinite(closeIndex) || closeIndex < openIndex || closeIndex > cursor) {
        return null;
      }
      if (!Number.isFinite(closePrice) || !Number.isFinite(realized)) {
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
        if (!Number.isFinite(index) || index < 1 || index >= N) {
          continue;
        }
        if (!Number.isFinite(price)) {
          continue;
        }
        points.push({ i: index, price: price });
      }
    }
    points.sort(function (a, b) { return a.i - b.i; });
    const deduped = [];
    for (const point of points) {
      const last = deduped.length ? deduped[deduped.length - 1] : null;
      if (last && last.i === point.i) {
        last.price = point.price;
      } else {
        deduped.push(point);
      }
    }
    let anchorIndex = null;
    if (Number.isFinite(Number(raw.anchorIndex))) {
      anchorIndex = clamp(Math.round(Number(raw.anchorIndex)), 0, cursor);
    }
    let anchorPrice = Number.isFinite(Number(raw.anchorPrice)) ? Number(raw.anchorPrice) : null;
    if (deduped.length && anchorPrice === null) {
      anchorPrice = TICKS[anchorIndex === null ? 0 : anchorIndex][1];
    }
    return { anchorIndex: anchorIndex, anchorPrice: anchorPrice, points: deduped };
  }

  function sanitizeScenario(raw, cursor) {
    if (!raw || typeof raw !== "object") {
      return null;
    }
    let name = "Scenario";
    if (typeof raw.name === "string" && raw.name.trim()) {
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

  function restoreSession(parsed) {
    if (!parsed || parsed.format !== STORAGE_FORMAT) {
      throw new Error("this is not a Playground scenario file");
    }
    if (parsed.version !== STORAGE_VERSION) {
      throw new Error("this scenario file version is not supported");
    }
    if (parsed.datasetId !== DATA.datasetId) {
      throw new Error("this scenario file belongs to a different dataset");
    }
    if (parsed.tickCount !== REAL_N) {
      throw new Error("this scenario file has a different tick count");
    }
    if (!Array.isArray(parsed.scenarios) || !parsed.scenarios.length) {
      throw new Error("this scenario file has no scenarios");
    }
    state.customTicks = [];
    state.customBranch = null;
    state.customSpread = 0;
    if (Array.isArray(parsed.customTicks) && parsed.customTicks.length) {
      const branch = Math.round(Number(parsed.customBranch));
      if (Number.isFinite(branch) && branch >= 0 && branch < REAL_N) {
        const ticks = [];
        let lastTs = REAL_TICKS[branch][0];
        let usable = true;
        const limit = Math.min(parsed.customTicks.length, 20000);
        for (let i = 0; i < limit; i += 1) {
          const raw = parsed.customTicks[i];
          if (!Array.isArray(raw) || raw.length < 3) {
            usable = false;
            break;
          }
          const ts = Number(raw[0]);
          const bid = Number(raw[1]);
          const ask = Number(raw[2]);
          if (!Number.isFinite(ts) || !Number.isFinite(bid) || !Number.isFinite(ask) ||
              ts <= lastTs || bid <= 0 || ask < bid) {
            usable = false;
            break;
          }
          ticks.push([ts, bid, ask]);
          lastTs = ts;
        }
        if (usable && ticks.length) {
          state.customTicks = ticks;
          state.customBranch = branch;
          state.customSpread = Number(parsed.customSpread) || (ticks[0][2] - ticks[0][1]);
        }
      }
    }
    rebuildTape();
    const cursor = clamp(Math.round(Number(parsed.cursor) || 0), 0, N - 1);
    const scenarios = [];
    const limit = Math.min(parsed.scenarios.length, 40);
    for (let i = 0; i < limit; i += 1) {
      const scenario = sanitizeScenario(parsed.scenarios[i], cursor);
      if (scenario !== null) {
        scenarios.push(scenario);
      }
    }
    if (!scenarios.length) {
      throw new Error("this scenario file has no usable scenarios");
    }
    state.cursor = cursor;
    state.period = PERIODS[parsed.period] ? parsed.period : state.period;
    state.scenarios = scenarios;
    state.activeId = scenarios[0].id;
    for (const scenario of scenarios) {
      if (scenario.id === parsed.activeId) {
        state.activeId = scenario.id;
        break;
      }
    }
    const grid = Number(parsed.gridStep);
    if (Number.isFinite(grid) && grid > 0 && grid <= 1000) {
      state.gridStep = grid;
    }
    const lot = Number(parsed.lotSize);
    if (Number.isFinite(lot) && lot > 0) {
      state.lotSize = lot;
    }
    const move = Number(parsed.moveSize);
    if (Number.isFinite(move) && move > 0) {
      state.moveSize = move;
    }
    state.expertVisible = parsed.expertVisible !== false;
    state.excludedExpertTickets = new Set();
    if (Array.isArray(parsed.excludedExpertTickets)) {
      const known = new Set(EXPERT_TRADES.map(function (trade) { return String(trade.ticket); }));
      for (const ticket of parsed.excludedExpertTickets) {
        const text = String(ticket);
        if (known.has(text)) {
          state.excludedExpertTickets.add(text);
        }
      }
    }
  }

  function loadSavedState() {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return false;
      }
      restoreSession(JSON.parse(raw));
      return true;
    } catch (error) {
      state.scenarios = [makeScenario("Scenario 1")];
      state.activeId = state.scenarios[0].id;
      el.storageNote.textContent = "Saved session ignored; starting fresh.";
      return false;
    }
  }

  function exportSession() {
    const text = JSON.stringify(serializeState(), null, 2);
    const blob = new Blob([text], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const name = DATA.symbol.toLowerCase() + "-" + DATA.day + "-" +
      DATA.window.from.replace(":", "") + "-" + DATA.window.to.replace(":", "");
    link.href = url;
    link.download = "losslens-playground-" + name + ".json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    setMessage("Scenario file exported.");
  }

  function importFile(file) {
    const reader = new FileReader();
    reader.onload = function () {
      try {
        restoreSession(JSON.parse(String(reader.result)));
        el.lots.value = formatLots(state.lotSize);
        el.moveSize.value = state.moveSize.toFixed(2);
        syncPeriodButtons();
        applyGridSelect();
        rebuildSeries();
        refitFollow();
        refreshAll();
        saveState();
        setMessage("Scenario file imported.");
      } catch (error) {
        setMessage("Import failed: " + (error instanceof Error ? error.message : "invalid file"));
      }
      $("import-file").value = "";
    };
    reader.onerror = function () {
      setMessage("Import failed: the file could not be read.");
      $("import-file").value = "";
    };
    reader.readAsText(file);
  }

  function ticketStats(scenario) {
    let closed = 0;
    let wins = 0;
    for (const ticket of scenario.tickets) {
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
      winRate: closed ? wins / closed : null
    };
  }

  function maxDrawdownOf(scenario) {
    let peak = START_BALANCE;
    let worst = 0;
    for (let k = 0; k < N; k += 1) {
      const tick = TICKS[k];
      let realized = 0;
      let floating = 0;
      for (const ticket of scenario.tickets) {
        if (ticket.status === "closed" && ticket.closeIndex <= k) {
          realized += ticket.realized;
        } else if (ticket.openIndex <= k) {
          floating += ticketPnl(ticket, ticket.side === "buy" ? tick[1] : tick[2]);
        }
      }
      const equity = START_BALANCE + realized + floating;
      peak = Math.max(peak, equity);
      worst = Math.max(worst, peak - equity);
    }
    return worst;
  }

  function expertIncluded(trade) {
    return !state.excludedExpertTickets.has(String(trade.ticket));
  }

  function expertWindowProfit(revealedOnly) {
    let sum = 0;
    let count = 0;
    let wins = 0;
    for (const trade of EXPERT_TRADES) {
      const reveal = expertRevealTs(trade);
      if (!trade.inWindow || reveal === null) {
        continue;
      }
      if (revealedOnly && reveal > currentTs()) {
        continue;
      }
      if (!expertIncluded(trade)) {
        continue;
      }
      sum += trade.profit;
      count += 1;
      if (trade.profit > 0) {
        wins += 1;
      }
    }
    return { sum: sum, count: count, winRate: count ? wins / count : null };
  }

  function expertReportTradesRevealed() {
    return EXPERT_TRADES.filter(function (trade) {
      const reveal = expertRevealTs(trade);
      return trade.inWindow && reveal !== null && reveal <= currentTs();
    }).sort(function (a, b) { return expertRevealTs(a) - expertRevealTs(b); });
  }

  function buildExpertInputs() {
    if (!EXPERT_INPUTS.length) {
      el.expertInputsTable.classList.add("hidden");
      el.expertInputsEmpty.classList.remove("hidden");
      el.downloadSet.disabled = true;
      return;
    }
    el.expertInputsTable.classList.remove("hidden");
    el.expertInputsEmpty.classList.add("hidden");
    el.downloadSet.disabled = false;
    el.expertInputsBody.innerHTML = "";
    for (const item of EXPERT_INPUTS) {
      const row = document.createElement("tr");
      row.dataset.name = item.name;
      const name = document.createElement("td");
      name.textContent = item.name;
      row.appendChild(name);
      const values = [item.value || "", item.start || "", item.step || "", item.stop || ""];
      const classes = ["v", "s1", "s2", "s3"];
      for (let i = 0; i < values.length; i += 1) {
        const cell = document.createElement("td");
        cell.className = "input-cell";
        const input = document.createElement("input");
        input.className = classes[i];
        input.value = values[i];
        input.spellcheck = false;
        cell.appendChild(input);
        row.appendChild(cell);
      }
      el.expertInputsBody.appendChild(row);
    }
  }

  function downloadSet() {
    const lines = ["; saved by loss-lens"];
    for (const row of el.expertInputsBody.querySelectorAll("tr")) {
      const name = row.dataset.name;
      const value = row.querySelector(".v").value;
      const start = row.querySelector(".s1").value;
      const step = row.querySelector(".s2").value;
      const stop = row.querySelector(".s3").value;
      lines.push(name + "=" + value);
      if (start || step || stop) {
        lines.push(name + ",F=0");
        lines.push(name + ",1=" + (start || "0"));
        lines.push(name + ",2=" + (step || "0"));
        lines.push(name + ",3=" + (stop || "0"));
      }
    }
    const blob = new Blob([lines.join("\n") + "\n"], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = EXPERT && EXPERT.inputsFile ? EXPERT.inputsFile : "expert.set";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    setMessage("Expert .set downloaded.");
  }

  function summaryItem(label, value, className) {
    const span = document.createElement("span");
    span.textContent = label + " ";
    const bold = document.createElement("b");
    bold.textContent = value;
    if (className) {
      bold.className = className;
    }
    span.appendChild(bold);
    return span;
  }

  function refreshExpert() {
    if (!EXPERT) {
      el.expertEmpty.classList.remove("hidden");
      el.expertContent.classList.add("hidden");
      el.sessionExpert.textContent = "None";
      return;
    }
    el.expertEmpty.classList.add("hidden");
    el.expertContent.classList.remove("hidden");
    el.expertName.textContent = EXPERT.name || "Expert";
    const sources = [];
    if (EXPERT.inputsFile) {
      sources.push(EXPERT.inputsFile);
    }
    if (EXPERT.reportFile) {
      sources.push(EXPERT.reportFile);
    }
    el.expertSource.textContent = sources.length ? " · " + sources.join(" · ") : "";
    el.sessionExpert.textContent = EXPERT.name +
      (EXPERT_REPORT ? " · report loaded" : " · inputs only");
    el.expertVisible.checked = state.expertVisible;
    el.expertVisible.disabled = !EXPERT_REPORT || state.customTicks.length > 0;
    el.expertSummary.innerHTML = "";
    if (EXPERT_REPORT) {
      el.expertSummary.appendChild(summaryItem("Report",
        EXPERT_REPORT.totalTrades + " trades · net " +
        formatMoney(EXPERT_REPORT.totalNetProfit), ""));
      el.expertSummary.appendChild(summaryItem("In this window",
        EXPERT_REPORT.windowTradeCount + " closes · " +
        EXPERT_REPORT.foundWindowTrades + " placed", ""));
      el.expertSummary.appendChild(summaryItem("Window start",
        formatMoney(EXPERT_REPORT.windowStartBalance), ""));
      if (state.customTicks.length) {
        el.expertSummary.appendChild(summaryItem("Tape", "drawn ticks", ""));
        el.expertFutureCount.textContent = "";
        el.expertTradesBody.innerHTML = "";
        el.expertTradesTable.classList.add("hidden");
        el.expertTradesEmpty.classList.remove("hidden");
        el.expertTradesEmpty.textContent = "Drawn tape active. Clear the drawn ticks to " +
          "inspect the real report closes and what-if.";
        el.expertWhatIf.innerHTML = "";
        el.expertNote.textContent = "The expert report is tied to the real tape. Draw ticks " +
          "is for your own hypothetical tape; clear it to return to the expert view.";
        return;
      }
      el.expertSummary.appendChild(summaryItem("What-if so far",
        formatMoney(EXPERT_REPORT.windowStartBalance + expertWindowProfit(true).sum), ""));
      const future = EXPERT_TRADES.filter(function (trade) {
        const reveal = expertRevealTs(trade);
        return reveal !== null && reveal > currentTs();
      }).length;
      el.expertFutureCount.textContent = future
        ? future + " not revealed yet" : "all revealed";
      const revealed = expertReportTradesRevealed();
      el.expertTradesBody.innerHTML = "";
      if (!revealed.length) {
        el.expertTradesTable.classList.add("hidden");
        el.expertTradesEmpty.classList.remove("hidden");
      } else {
        el.expertTradesTable.classList.remove("hidden");
        el.expertTradesEmpty.classList.add("hidden");
        for (const trade of revealed) {
          const row = document.createElement("tr");
          const number = document.createElement("td");
          number.textContent = String(trade.ticket);
          row.appendChild(number);
          const time = document.createElement("td");
          time.textContent = formatTime(expertRevealTs(trade), true) + " UTC";
          if (!trade.found) {
            const sub = document.createElement("div");
            sub.className = "sub";
            sub.textContent = "not placed on a tick";
            time.appendChild(sub);
          }
          row.appendChild(time);
          const type = document.createElement("td");
          type.textContent = trade.kind;
          type.className = trade.kind.toLowerCase().indexOf("buy") === 0
            ? "side-buy" : "side-sell";
          row.appendChild(type);
          const size = document.createElement("td");
          size.textContent = formatLots(trade.size);
          row.appendChild(size);
          const close = document.createElement("td");
          close.textContent = formatPrice(trade.closePrice);
          row.appendChild(close);
          const profit = document.createElement("td");
          profit.textContent = formatMoney(trade.profit);
          profit.className = trade.profit >= 0 ? "up" : "down";
          row.appendChild(profit);
          const balance = document.createElement("td");
          balance.textContent = formatMoney(trade.balance);
          row.appendChild(balance);
          const use = document.createElement("td");
          const check = document.createElement("input");
          check.type = "checkbox";
          check.checked = expertIncluded(trade);
          check.addEventListener("change", function () {
            if (check.checked) {
              state.excludedExpertTickets.delete(String(trade.ticket));
            } else {
              state.excludedExpertTickets.add(String(trade.ticket));
            }
            refreshAll();
            saveState();
          });
          use.appendChild(check);
          row.appendChild(use);
          el.expertTradesBody.appendChild(row);
        }
      }
      el.expertWhatIf.innerHTML = "";
      const profit = expertWindowProfit(true);
      el.expertWhatIf.appendChild(summaryItem("Revealed closes",
        String(profit.count) + " included", ""));
      el.expertWhatIf.appendChild(summaryItem("Included P&L",
        formatMoney(profit.sum), profit.sum >= 0 ? "up" : "down"));
      el.expertWhatIf.appendChild(summaryItem("What-if final",
        formatMoney(EXPERT_REPORT.windowStartBalance + profit.sum), ""));
      el.expertNote.textContent = "The report gives close times and prices only. Down " +
        "triangles are closed buys, up triangles closed sells. Uncheck a trade to remove it " +
        "from the what-if; the real ticks stay untouched. The Playground never runs MT4.";
    } else {
      el.expertFutureCount.textContent = "";
      el.expertTradesBody.innerHTML = "";
      el.expertTradesTable.classList.add("hidden");
      el.expertTradesEmpty.classList.remove("hidden");
      el.expertTradesEmpty.textContent = "No tester report loaded. Build with --report.";
      el.expertWhatIf.innerHTML = "";
      el.expertNote.textContent = "Inputs only. Add a tester report to see the expert's " +
        "closes on the chart.";
    }
  }

  function refreshTickets() {
    const scenario = activeScenario();
    el.openBody.innerHTML = "";
    const open = scenario.tickets.filter(function (ticket) {
      return ticket.status === "open";
    }).sort(function (a, b) { return b.openIndex - a.openIndex; });
    el.openEmpty.classList.toggle("hidden", open.length > 0);
    for (const ticket of open) {
      const profit = ticketPnl(ticket, ticket.side === "buy" ? currentBid() : currentAsk());
      const close = document.createElement("button");
      close.type = "button";
      close.className = "btn";
      close.textContent = "Close";
      close.addEventListener("click", function () { closeTicket(ticket.id); });
      const row = addRow(el.openBody, [
        formatTime(TICKS[ticket.openIndex][0], true),
        ticket.side,
        formatLots(ticket.lots),
        formatPrice(ticket.entry),
        ticket.sl === null ? "-" : formatPrice(ticket.sl),
        ticket.tp === null ? "-" : formatPrice(ticket.tp),
        formatMoney(profit),
        { node: close }
      ], [
        "", ticket.side === "buy" ? "side-buy" : "side-sell", "", "", "", "",
        profit >= 0 ? "up" : "down", ""
      ]);
      row.lastChild.style.textAlign = "center";
    }
    const balance = balanceOf(scenario);
    const floating = floatingNow(scenario);
    el.balance.textContent = formatMoney(balance);
    el.floating.textContent = formatMoney(floating);
    el.floating.className = floating >= 0 ? "up" : "down";
    el.equity.textContent = formatMoney(balance + floating);
    el.historyBody.innerHTML = "";
    const closed = scenario.tickets.filter(function (ticket) {
      return ticket.status === "closed";
    }).sort(function (a, b) { return b.closeIndex - a.closeIndex; });
    el.historyEmpty.classList.toggle("hidden", closed.length > 0);
    for (const ticket of closed) {
      addRow(el.historyBody, [
        formatTime(TICKS[ticket.openIndex][0], true),
        ticket.side,
        formatLots(ticket.lots),
        formatPrice(ticket.entry),
        formatPrice(ticket.closePrice),
        ticket.sl === null ? "-" : formatPrice(ticket.sl),
        ticket.tp === null ? "-" : formatPrice(ticket.tp),
        formatMoney(ticket.realized),
        ticket.closeReason
      ], [
        "", ticket.side === "buy" ? "side-buy" : "side-sell", "", "", "", "", "",
        ticket.realized >= 0 ? "up" : "down", ""
      ]);
    }
  }

  function refreshPrediction() {
    const scenario = activeScenario();
    const count = scenario.prediction.points.length;
    const stats = predictionStats();
    document.querySelectorAll('[data-action="draw"]').forEach(function (button) {
      button.classList.toggle("active", state.drawMode);
    });
    document.querySelectorAll('[data-action="both"]').forEach(function (button) {
      button.classList.toggle("active", state.bothWays);
    });
    el.drawTicks.classList.toggle("active", state.tickDrawMode);
    el.clearTicks.disabled = state.customTicks.length === 0;
    el.predUndo.disabled = count === 0;
    el.predClear.disabled = count === 0;
    if (count === 0) {
      el.predStats.textContent = "No prediction points. Turn on Draw prediction and click ahead.";
    } else {
      const mae = stats.mae === null ? "-" : formatPrice(stats.mae);
      const hit = stats.hitRate === null ? "-" : Math.round(stats.hitRate * 100) + "%";
      el.predStats.textContent = "Points " + count + " · reached " + stats.count +
        " · MAE " + mae + " · direction " + hit;
    }
    el.movePreview.innerHTML = "";
    let open = 0;
    for (const ticket of scenario.tickets) {
      if (ticket.status === "open") {
        open += 1;
      }
    }
    if (!open) {
      el.movePreview.textContent = "No open tickets to preview.";
    } else {
      const move = Math.abs(state.moveSize);
      const up = floatingAt(scenario, currentBid() + move, currentAsk() + move);
      const down = floatingAt(scenario, currentBid() - move, currentAsk() - move);
      const upRow = document.createElement("div");
      upRow.textContent = "At +$" + move.toFixed(2) + ": ";
      const upValue = document.createElement("b");
      upValue.textContent = formatMoney(up);
      upValue.className = up >= 0 ? "up" : "down";
      upRow.appendChild(upValue);
      el.movePreview.appendChild(upRow);
      const downRow = document.createElement("div");
      downRow.textContent = "At -$" + move.toFixed(2) + ": ";
      const downValue = document.createElement("b");
      downValue.textContent = formatMoney(down);
      downValue.className = down >= 0 ? "up" : "down";
      downRow.appendChild(downValue);
      el.movePreview.appendChild(downRow);
    }
  }

  function refreshScenarios() {
    el.scenarioList.innerHTML = "";
    for (const scenario of state.scenarios) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = scenario.name;
      button.classList.toggle("active", scenario.id === state.activeId);
      button.addEventListener("click", function () {
        state.activeId = scenario.id;
        refreshAll();
        saveState();
      });
      el.scenarioList.appendChild(button);
    }
    el.scenarioSummary.innerHTML = "";
    for (const scenario of state.scenarios) {
      const open = scenario.tickets.filter(function (ticket) {
        return ticket.status === "open";
      }).length;
      const closed = scenario.tickets.length - open;
      const reached = scoredPointsFor(scenario).length;
      addRow(el.scenarioSummary, [
        scenario.name,
        formatMoney(equityOf(scenario)),
        String(open),
        String(closed),
        String(scenario.prediction.points.length),
        String(reached)
      ]);
    }
    const active = activeScenario();
    el.terminalSummary.textContent = active.name + " · Equity " + formatMoney(equityOf(active));
  }

  function scoredPointsFor(scenario) {
    const previous = state.activeId;
    state.activeId = scenario.id;
    const scored = scoredPoints();
    state.activeId = previous;
    return scored;
  }

  function setTerminalTab(tab) {
    document.querySelectorAll("#tabs [data-tab]").forEach(function (button) {
      button.classList.toggle("active", button.dataset.tab === tab);
    });
    document.querySelectorAll(".tab-pane").forEach(function (pane) {
      pane.classList.toggle("active", pane.id === "pane-" + tab);
    });
  }

  function applyGridSelect() {
    const presets = ["0.01", "0.05", "0.10", "0.25", "0.50", "1.00"];
    const text = state.gridStep.toFixed(2);
    el.grid.value = presets.indexOf(text) >= 0 ? text : "custom";
  }

  function onGridChange() {
    const value = el.grid.value;
    if (value === "custom") {
      const text = window.prompt("Custom price grid step", String(state.gridStep));
      if (text === null) {
        applyGridSelect();
        return;
      }
      const number = Number(text);
      if (!Number.isFinite(number) || number <= 0 || number > 1000) {
        setMessage("Custom grid step must be above zero and at most 1000.");
        applyGridSelect();
        return;
      }
      state.gridStep = number;
    } else {
      state.gridStep = Number(value);
    }
    applyGridSelect();
    refreshAll();
    saveState();
  }

  function refreshSession() {
    el.sessionSymbol.textContent = DATA.symbol;
    el.sessionDay.textContent = DATA.day;
    el.sessionWindow.textContent = DATA.window.from + "-" + DATA.window.to + " UTC";
    el.sessionTicks.textContent = N.toLocaleString();
    el.sessionTape.textContent = state.customTicks.length
      ? "Drawn · " + state.customTicks.length.toLocaleString() + " ticks"
      : "Real ticks";
    el.sessionExpert.textContent = EXPERT ? (EXPERT.name || "Expert") : "None";
  }

  function refreshAll() {
    const tick = currentTick();
    el.datasetLine.textContent = DATA.symbol + " · " + DATA.day + " · " +
      DATA.window.from + "-" + DATA.window.to + " UTC";
    el.wsymbol.textContent = DATA.symbol;
    el.bid.textContent = formatPrice(tick[1]);
    el.ask.textContent = formatPrice(tick[2]);
    el.spread.textContent = (tick[2] - tick[1]).toFixed(DIGITS);
    refreshReplay();
    refreshDataWindow();
    refreshStatus();
    refreshTapeTag();
    refreshTickets();
    refreshExpert();
    refreshPrediction();
    refreshScenarios();
    refreshSession();
    syncPeriodButtons();
    applyGridSelect();
    draw();
  }

  function showScoreboard() {
    const rows = [];
    for (const scenario of state.scenarios) {
      const stats = predictionStatsFor(scenario);
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
    if (EXPERT_REPORT && !state.customTicks.length) {
      const profit = expertWindowProfit(false);
      rows.push({
        name: "Expert report (window, $10k)",
        equity: START_BALANCE + profit.sum,
        drawdown: null,
        tickets: profit.count,
        winRate: profit.winRate,
        mae: null,
        hitRate: null
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
      const row = rows[i];
      const tr = document.createElement("tr");
      if (i === 0 && rows.length > 1) {
        tr.style.fontWeight = "bold";
      }
      const cells = [
        row.name,
        formatMoney(row.equity),
        row.drawdown === null ? "—" : formatMoney(row.drawdown),
        String(row.tickets),
        row.winRate === null ? "—" : (row.winRate * 100).toFixed(1) + "%",
        row.mae === null ? "—" : formatPrice(row.mae),
        row.hitRate === null ? "—" : (row.hitRate * 100).toFixed(1) + "%"
      ];
      for (const text of cells) {
        const cell = document.createElement("td");
        cell.textContent = text;
        tr.appendChild(cell);
      }
      el.scoreBody.appendChild(tr);
    }
    el.scoreNote.textContent = "User scenarios start at $10,000. The expert row uses the " +
      "report's in-window P&L normalized to $10,000; its max drawdown and prediction scores " +
      "are not computed. Win rate counts closed or included trades.";
    el.scoreboard.classList.remove("hidden");
  }

  function predictionStatsFor(scenario) {
    const previous = state.activeId;
    state.activeId = scenario.id;
    const stats = predictionStats();
    state.activeId = previous;
    return stats;
  }

  function runToEnd() {
    if (state.cursor < N - 1) {
      advanceTo(N - 1);
    }
    showScoreboard();
  }

  function closeScoreboard() {
    el.scoreboard.classList.add("hidden");
  }

  function closeMenus() {
    document.querySelectorAll(".menu.open").forEach(function (menu) {
      menu.classList.remove("open");
    });
  }

  function handleCommand(command, value) {
    if (command === "export") {
      exportSession();
    } else if (command === "import") {
      $("import-file").click();
    } else if (command === "reset") {
      resetReplay();
    } else if (command === "follow") {
      followCursor();
    } else if (command === "zoomin") {
      zoomIn();
    } else if (command === "zoomout") {
      zoomOut();
    } else if (command === "both") {
      toggleBoth();
    } else if (command === "draw") {
      toggleDraw();
    } else if (command === "drawticks") {
      toggleTickDraw();
    } else if (command === "clearticks") {
      clearCustomTicks();
    } else if (command === "undo") {
      undoPrediction();
    } else if (command === "clear") {
      clearPrediction();
    } else if (command === "runend") {
      runToEnd();
    } else if (command === "period") {
      setPeriod(value);
    } else if (command === "expert") {
      setTerminalTab("expert");
    } else if (command === "help") {
      setTerminalTab("help");
    }
  }

  function bindMenus() {
    document.querySelectorAll(".menu > button").forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.stopPropagation();
        const menu = button.parentElement;
        const open = menu.classList.contains("open");
        closeMenus();
        if (!open) {
          menu.classList.add("open");
        }
      });
    });
    document.querySelectorAll("[data-command]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.stopPropagation();
        handleCommand(button.dataset.command, button.dataset.value);
        closeMenus();
      });
    });
    document.addEventListener("click", function () { closeMenus(); });
  }

  function bindTabs() {
    document.querySelectorAll("#tabs [data-tab]").forEach(function (button) {
      button.addEventListener("click", function () {
        setTerminalTab(button.dataset.tab);
      });
    });
  }

  function bindEvents() {
    document.querySelectorAll("#period-buttons button").forEach(function (button) {
      button.addEventListener("click", function () { setPeriod(button.dataset.period); });
    });
    el.grid.addEventListener("change", onGridChange);
    el.zoomout.addEventListener("click", zoomOut);
    el.zoomin.addEventListener("click", zoomIn);
    el.follow.addEventListener("click", followCursor);
    el.reset.addEventListener("click", resetReplay);
    el.next1.addEventListener("click", function () { advance(1); });
    el.next10.addEventListener("click", function () { advance(10); });
    el.next100.addEventListener("click", function () { advance(100); });
    el.nextbar.addEventListener("click", nextBar);
    el.buy.addEventListener("click", function () { openTicket("buy"); });
    el.sell.addEventListener("click", function () { openTicket("sell"); });
    document.querySelectorAll('[data-action="draw"]').forEach(function (button) {
      button.addEventListener("click", toggleDraw);
    });
    document.querySelectorAll('[data-action="both"]').forEach(function (button) {
      button.addEventListener("click", toggleBoth);
    });
    el.drawTicks.addEventListener("click", toggleTickDraw);
    el.clearTicks.addEventListener("click", clearCustomTicks);
    el.predUndo.addEventListener("click", undoPrediction);
    el.predClear.addEventListener("click", clearPrediction);
    el.moveSize.addEventListener("input", function () {
      const value = Number(el.moveSize.value);
      if (Number.isFinite(value) && value > 0) {
        state.moveSize = value;
        refreshPrediction();
        if (state.bothWays) {
          draw();
        }
        saveState();
      }
    });
    $("open-expert").addEventListener("click", function () { setTerminalTab("expert"); });
    $("add-scenario").addEventListener("click", addScenario);
    $("rename-scenario").addEventListener("click", renameScenario);
    $("duplicate-scenario").addEventListener("click", duplicateScenario);
    $("delete-scenario").addEventListener("click", deleteScenario);
    $("run-end").addEventListener("click", runToEnd);
    $("export-json").addEventListener("click", exportSession);
    $("import-json").addEventListener("click", function () { $("import-file").click(); });
    $("import-file").addEventListener("change", function () {
      const input = $("import-file");
      if (input.files && input.files.length) {
        importFile(input.files[0]);
      }
    });
    $("reset-replay").addEventListener("click", resetReplay);
    el.expertVisible.addEventListener("change", function () {
      state.expertVisible = el.expertVisible.checked;
      refreshAll();
      saveState();
    });
    el.downloadSet.addEventListener("click", downloadSet);
    $("score-close").addEventListener("click", closeScoreboard);
    el.scoreboard.addEventListener("click", function (event) {
      if (event.target === el.scoreboard) {
        closeScoreboard();
      }
    });
    canvas.addEventListener("wheel", onWheel, { passive: false });
    canvas.addEventListener("mousedown", onMouseDown);
    canvas.addEventListener("mousemove", onMouseMove);
    canvas.addEventListener("dblclick", followCursor);
    canvas.addEventListener("mouseup", onMouseUp);
    window.addEventListener("mouseup", onMouseUp);
    canvas.addEventListener("mouseleave", onMouseLeave);
    window.addEventListener("resize", resize);
    document.addEventListener("keydown", function (event) {
      const tag = event.target && event.target.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA" || tag === "BUTTON") {
        return;
      }
      if (event.key === "Escape") {
        closeMenus();
        closeScoreboard();
        return;
      }
      if (event.code === "Space" || event.key === " ") {
        event.preventDefault();
        if (!event.repeat && el.scoreboard.classList.contains("hidden")) {
          advance(1);
        }
      } else if (event.key === "d" || event.key === "D") {
        toggleDraw();
      } else if (event.key === "t" || event.key === "T") {
        toggleTickDraw();
      } else if (event.key === "b" || event.key === "B") {
        toggleBoth();
      } else if (event.key === "+" || event.key === "=") {
        zoomIn();
      } else if (event.key === "-") {
        zoomOut();
      } else if (event.key === "ArrowLeft") {
        panBy(-Math.max(1, Math.round(state.viewCount / 10)));
      } else if (event.key === "ArrowRight") {
        panBy(Math.max(1, Math.round(state.viewCount / 10)));
      } else if (event.key === "End") {
        followCursor();
      } else if (event.key === "?") {
        setTerminalTab("help");
      }
    });
    if (window.ResizeObserver) {
      const observer = new ResizeObserver(resize);
      observer.observe($("chartarea"));
    }
  }

  function init() {
    state.scenarios = [makeScenario("Scenario 1")];
    state.activeId = state.scenarios[0].id;
    const loaded = loadSavedState();
    if (!loaded) {
      state.cursor = startCursorIndex();
      state.period = "t100";
    }
    rebuildTape();
    rebuildSeries();
    refitFollow();
    buildExpertInputs();
    bindMenus();
    bindTabs();
    bindEvents();
    el.lots.value = formatLots(state.lotSize);
    el.moveSize.value = state.moveSize.toFixed(2);
    syncPeriodButtons();
    applyGridSelect();
    setTerminalTab(loaded ? "trade" : "help");
    refreshAll();
    resize();
  }

  if (!Array.isArray(TICKS) || TICKS.length === 0) {
    document.body.textContent = "This Playground has no ticks.";
    return;
  }
  init();
}());
"""
