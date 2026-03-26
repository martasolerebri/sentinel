let activePeriod  = "month";
let donutChart    = null;
let wakeRetries   = 0;
let wakeTimer     = null;
const WAKE_MAX_RETRIES = 8;
const WAKE_DELAY_MS    = 8000;

const PERIOD_LABELS = {
  "week": "Week", "month": "Month", "quarter": "Quarter",
  "half-year": "Half-year", "year": "Year"
};

const TOOL_LABELS = {
  analyze_spending:     "Analysing spending…",
  get_category_trend:   "Fetching category trend…",
  get_top_expenses:     "Finding top expenses…",
  check_savings_goal:   "Checking savings goal…",
  get_financial_health: "Evaluating financial health…",
};

const CATEGORY_COLORS = {
  Housing:       "#0A84FF", 
  Groceries:     "#30D158", 
  "Eating Out":  "#32ADE6", 
  Transport:     "#BF5AF2", 
  Entertainment: "#5E5CE6", 
  Utilities:     "#00C7BE", 
  Subscriptions: "#64D2FF",
  Health:        "#A2845E", 
  Shopping:      "#FB7185", 
  Other:         "#636366",
};

const CATEGORY_COLORS_HOVER = Object.fromEntries(
  Object.entries(CATEGORY_COLORS).map(([k, v]) => [k, v + "CC"])
);

function formatCurrency(value) {
  return new Intl.NumberFormat("en-GB", {
    style: "currency", currency: "GBP",
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  }).format(value);
}

function renderSummary(summary) {
  const map = {
    income:  document.getElementById("summaryIncome"),
    spent:   document.getElementById("summaryExpenses"),
    savings: document.getElementById("summarySavings"),
  };
  for (const [key, el] of Object.entries(map)) {
    if (!el) continue;
    el.textContent = formatCurrency(summary[key]);
  }
}

function renderChart(spendingByCategory) {
  const canvas = document.getElementById("spendingChart");
  if (!canvas) return;
  if (donutChart) { donutChart.destroy(); donutChart = null; }

  const labels = Object.keys(spendingByCategory);
  const values = Object.values(spendingByCategory);
  const colors = labels.map(c => CATEGORY_COLORS[c] ?? "#6B7280");
  const total  = values.reduce((a, b) => a + b, 0);

  renderCategoryTable(labels, values, colors);

  const centerPlugin = {
    id: "donutCenter",
    afterDraw(chart) {
      const { ctx, chartArea: { top, bottom, left, right } } = chart;
      const cx = (left + right) / 2, cy = (top + bottom) / 2;
      ctx.save();
      
      ctx.font = '600 17px -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif';
      ctx.fillStyle = "#FFFFFF";
      ctx.textAlign = "center"; 
      ctx.textBaseline = "middle";
      ctx.fillText(formatCurrency(total), cx, cy - 6);
      
      ctx.font = '500 9px -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif';
      ctx.fillStyle = "rgba(203, 213, 225, 0.6)"; 
      ctx.fillText("TOTAL SPENT", cx, cy + 12);
      
      ctx.restore();
    },
  };

  donutChart = new Chart(canvas.getContext("2d"), {
    type: "doughnut",
    plugins: [centerPlugin],
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        hoverBackgroundColor: colors,
        borderWidth: 0.6,
        borderColor: "#0A0A12",
        hoverOffset: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: "60%",
      layout: { padding: 16 },
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: false,
          callbacks: { label: ctx => ` ${ctx.label}: ${formatCurrency(ctx.parsed)}` },
        },
      },
      animation: { animateRotate: true, duration: 900, easing: "easeInOutQuart" },
    },
  });
}

function renderCategoryTable(labels, values, colors) {
  const tbody = document.getElementById("categoryTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";
  labels.forEach((name, i) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>
        <div class="category-name">
          <span class="category-dot" style="background:${colors[i]}"></span>
          <span style="color:${colors[i]}">${name}</span>
        </div>
      </td>
      <td>${formatCurrency(values[i])}</td>
    `;
    tbody.appendChild(row);
  });
}

function renderTopExpenses(expenses) {
  const list = document.getElementById("topExpensesList");
  if (!list) return;
  list.innerHTML = "";

  if (!expenses.length) {
    list.innerHTML = `<li class="top-expenses-loading">No expenses found for this period.</li>`;
    return;
  }

  expenses.forEach((item, idx) => {
    const color = CATEGORY_COLORS[item.category] ?? "#6B7280";
    const li = document.createElement("li");
    li.className = "top-expense-item";
    li.innerHTML = `
      <span class="expense-rank">${idx + 1}</span>
      <span class="expense-dot" style="background:${color}"></span>
      <span class="expense-info">
        <span class="expense-merchant">${item.merchant}</span>
        <span class="expense-meta">
          <span class="expense-category" style="color:${color}">${item.category}</span>
          <span class="expense-date">${item.date}</span>
          ${item.anomaly ? `<span class="anomaly-badge">⚠ anomaly</span>` : ""}
        </span>
      </span>
      <span class="expense-amount">${formatCurrency(item.amount)}</span>
    `;
    list.appendChild(li);
  });
}

function renderGoal(goal) {
  const el = id => document.getElementById(id);

  el("goalPercentage").textContent = `${goal.percentage}%`;
  el("goalName").textContent       = goal.name;

  const [y, m, d] = goal.deadline.split("-").map(Number);
  el("goalDate").textContent = new Date(y, m - 1, d).toLocaleDateString("en-GB", {
    weekday: "long", year: "numeric", month: "long", day: "numeric"
  });

  el("goalProgressBar").style.width = `${Math.min(goal.percentage, 100)}%`;

  const saved = el("goalCurrentAmount");
  saved.textContent = formatCurrency(goal.current_amount);
  saved.dataset.raw = goal.current_amount;

  const target = el("goalTargetAmount");
  target.textContent = formatCurrency(goal.target_amount);
  target.dataset.raw = goal.target_amount;

  const remaining = el("goalRemaining");
  remaining.textContent = formatCurrency(goal.remaining);
  remaining.dataset.raw = goal.remaining;

  const daysLeft = el("goalDaysLeft");
  daysLeft.textContent = goal.days_remaining >= 0 ? `${goal.days_remaining}d` : "Expired";
  daysLeft.dataset.raw = goal.deadline;

  const container = document.getElementById("goalContainer");
  if (container) container.style.opacity = "1";
}

async function loadInsights(period) {
  const body = document.getElementById("insightsBody");
  if (!body) return;

  if (!localStorage.getItem("sfe_api_key")) {
    body.innerHTML = `
      <div class="insights-unlock">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        <span>AI Insights require a <strong>Google AI API key</strong>.</span>
        <button class="pill-btn" onclick="showApiKeyModal()">Unlock AI</button>
      </div>`;
    return;
  }

  body.innerHTML = `<p class="insights-loading"><span class="spinner"></span> Generating insights…</p>`;
  try {
    const data = await fetchInsights(period);
    body.innerHTML = `<p style="color:var(--text-secondary);line-height:1.75;">${data.narrative}</p>`;
  } catch (err) {
    body.innerHTML = `<p class="insights-error">⚠ ${err.message}</p>`;
  }
}

function changePeriod(period) {
  activePeriod = period;
  document.querySelectorAll("[data-period]").forEach(btn => {
    btn.classList.toggle("filter-btn--active", btn.dataset.period === period);
  });
  initDashboard();
}

function showGlobalError(msg) {
  const el = document.getElementById("globalError");
  if (!el) return;
  el.textContent = `⚠ Error: ${msg}`;
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 8000);
}

function showWakeupBanner(attempt) {
  const banner = document.getElementById("wakeupBanner");
  if (!banner) return;
  banner.style.display = "flex";
  const msg = document.getElementById("wakeupMsg");
  const retry = document.getElementById("wakeupRetry");
  if (msg) msg.textContent = attempt === 0
    ? "The backend is waking up — this can take ~30 seconds on first visit."
    : "Still waking up, please wait…";
  if (retry) retry.textContent = `Attempt ${attempt + 1} of ${WAKE_MAX_RETRIES}`;
}

function hideWakeupBanner() {
  const banner = document.getElementById("wakeupBanner");
  if (banner) banner.style.display = "none";
  if (wakeTimer) { clearTimeout(wakeTimer); wakeTimer = null; }
}

function addChatBubble(text, type) {
  const msgs = document.getElementById("chatMensajes");
  if (!msgs) return null;
  const div = document.createElement("div");
  div.className = `chat-bubble chat-bubble--${type}`;
  if (text) {
    div.textContent = text;
  } else {
    div.classList.add("chat-typing");
    div.innerHTML = "<span></span><span></span><span></span>";
  }
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div;
}

function addToolIndicator(toolName) {
  const msgs = document.getElementById("chatMensajes");
  if (!msgs) return null;
  const div = document.createElement("div");
  div.className = "chat-tool-indicator";
  const label = toolName ? (TOOL_LABELS[toolName] || "Querying database…") : "Thinking…";
  div.innerHTML = `<span style="font-size:.8rem">⚙</span><span class="tool-text">${label}</span>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div;
}

async function sendMessage() {
  const input   = document.getElementById("chatInput");
  const sendBtn = document.getElementById("chatBtnSend");
  const text    = input?.value.trim();
  if (!text) return;

  input.value = "";
  input.disabled = true;
  sendBtn.disabled = true;

  addChatBubble(text, "user");
  const waitingBubble = addChatBubble("", "agent");
  const toolIndicator = addToolIndicator(null);
  if (toolIndicator) toolIndicator.classList.add("chat-tool-pending");

  try {
    const data = await sendChatMessage(text, getUserId());

    if (toolIndicator) {
      if (data.tool_used) {
        const span = toolIndicator.querySelector(".tool-text");
        if (span) span.textContent = TOOL_LABELS[data.tool_used] || "Database queried.";
        toolIndicator.classList.remove("chat-tool-pending");
        toolIndicator.classList.add("chat-tool-done");
        setTimeout(() => { toolIndicator.style.maxHeight = "0"; toolIndicator.style.opacity = "0"; }, 2000);
      } else {
        toolIndicator.remove();
      }
    }

    if (waitingBubble) {
      waitingBubble.classList.remove("chat-typing");
      waitingBubble.innerHTML = "";
      waitingBubble.textContent = data.response || "No response from the agent.";
    }

  } catch (err) {
    if (toolIndicator) toolIndicator.remove();
    if (waitingBubble) {
      waitingBubble.classList.remove("chat-typing");
      waitingBubble.classList.add("chat-bubble--error");
      waitingBubble.textContent = `⚠ Error contacting agent: ${err.message}`;
    }
  } finally {
    input.disabled = false;
    sendBtn.disabled = false;
    input?.focus();
  }
}

async function initDashboard() {
  try {
    const [dashData, summary, topExpenses] = await Promise.all([
      fetchDashboardData(activePeriod),
      fetchSummary(activePeriod),
      fetchTopExpenses(activePeriod, 5),
    ]);

    hideWakeupBanner();
    wakeRetries = 0;

    if (!dashData?.spending_by_category)
      throw new Error("Unexpected response from /api/dashboard.");

    renderSummary(summary);
    renderChart(dashData.spending_by_category);
    renderTopExpenses(topExpenses);

    document.querySelectorAll("[data-period]").forEach(btn => {
      btn.classList.toggle("filter-btn--active", btn.dataset.period === activePeriod);
    });

    fetchGoal()
      .then(renderGoal)
      .catch(err => {
        const container = document.getElementById("goalContainer");
        if (!container) return;
        if (err.message.includes("404")) {
          const body = container.querySelector(".goal-body");
          if (body) body.innerHTML = `
            <div style="padding:1.5rem 0;text-align:center;">
              <p style="color:var(--text-muted);font-size:.82rem;margin-bottom:1rem;">No savings goal defined yet.</p>
              <button class="modal-btn" style="width:auto;padding:.55rem 1.5rem;font-size:.78rem;" onclick="openGoalModal()">+ Create goal</button>
            </div>`;
        }
      });

    loadInsights(activePeriod);

  } catch (err) {
    const isWakeup = err instanceof TypeError || err.message.includes("503");
    if (isWakeup && wakeRetries < WAKE_MAX_RETRIES) {
      showWakeupBanner(wakeRetries);
      wakeRetries++;
      wakeTimer = setTimeout(() => initDashboard(), WAKE_DELAY_MS);
    } else {
      console.error("Sentinel:", err.message);
      showGlobalError(err.message);
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();

  const chatInput = document.getElementById("chatInput");
  if (chatInput) {
    chatInput.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
  }

  setTimeout(() => {
    addChatBubble(
      "👋🏻 Hi! I'm your Sentinel assistant. Ask me about your spending, savings goal, top expenses or financial health.",
      "agent"
    );
  }, 1200);
});