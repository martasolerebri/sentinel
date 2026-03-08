const BASE_URL = (() => {
  if (window.SFE_API_URL) return window.SFE_API_URL.replace(/\/$/, "");
  const { hostname } = window.location;
  const isLocal = hostname === "localhost" || hostname === "127.0.0.1";
  return isLocal
    ? `http://${hostname}:8000`
    : "https://your-deployment-url.example.com";
})();

const VALID_PERIODS = ["week", "month", "quarter", "half-year", "year"];

async function fetchDashboardData(period = "month") {
  if (!VALID_PERIODS.includes(period)) throw new Error(`Invalid period: "${period}"`);
  const res = await fetch(`${BASE_URL}/api/dashboard?period=${encodeURIComponent(period)}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function fetchSummary(period = "month") {
  if (!VALID_PERIODS.includes(period)) throw new Error(`Invalid period: "${period}"`);
  const res = await fetch(`${BASE_URL}/api/summary?period=${encodeURIComponent(period)}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function fetchTopExpenses(period = "month", n = 5) {
  if (!VALID_PERIODS.includes(period)) throw new Error(`Invalid period: "${period}"`);
  const res = await fetch(`${BASE_URL}/api/top-expenses?period=${encodeURIComponent(period)}&n=${n}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function fetchGoal() {
  const res = await fetch(`${BASE_URL}/api/goal`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function createGoal(name, target_amount, current_amount, deadline) {
  const apiKey = localStorage.getItem("sfe_api_key");
  const res = await fetch(`${BASE_URL}/api/goal`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json", 
      ...(apiKey && { Authorization: `Bearer ${apiKey}` }) 
    },
    body: JSON.stringify({ name, target_amount, current_amount, deadline }),
  });
  
  if (!res.ok) { 
    const err = await res.json().catch(() => ({})); 
    throw new Error(err.detail || `HTTP ${res.status}`); 
  }
  return res.json();
}

async function fetchInsights(period = "month") {
  const apiKey = localStorage.getItem("sfe_api_key");
  if (!apiKey) throw new Error("API key required.");
  const res = await fetch(`${BASE_URL}/api/insights?period=${encodeURIComponent(period)}`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  
  if (!res.ok) { 
    const err = await res.json().catch(() => ({})); 
    throw new Error(err.detail || `HTTP ${res.status}`); 
  }
  return res.json();
}

async function sendChatMessage(message, user_id) {
  const apiKey = localStorage.getItem("sfe_api_key");
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json", 
      ...(apiKey && { Authorization: `Bearer ${apiKey}` }) 
    },
    body: JSON.stringify({ message, user_id }),
  });
  
  if (!res.ok) { 
    const err = await res.json().catch(() => ({})); 
    throw new Error(err.detail || `HTTP ${res.status}`); 
  }
  return res.json();
}

function getUserId() {
  let uid = localStorage.getItem("sfe_user_id");
  if (!uid) {
    uid = "sfe_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    localStorage.setItem("sfe_user_id", uid);
  }
  return uid;
}