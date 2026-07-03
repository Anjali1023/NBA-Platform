import { useEffect, useMemo, useState } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8001";

const glassCard = {
  background: "rgba(255,255,255,0.05)",
  backdropFilter: "blur(12px)",
  WebkitBackdropFilter: "blur(12px)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: "16px",
};

const neonGreen = "#00ff9d";
const neonBlue = "#00d4ff";
const neonPurple = "#a855f7";

export default function App() {
  const [customerId, setCustomerId] = useState("ACME-001");
  const [inputType, setInputType] = useState("meeting_transcript");
  const [transcript, setTranscript] = useState(
    "We are getting frustrated with slow support and the onboarding felt confusing. We are considering switching to a competitor because pricing also feels high. We need a better plan for adoption before renewal next quarter."
  );
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [sessionId, setSessionId] = useState("");
  const [interactionId, setInteractionId] = useState("");
  const [approvedStates, setApprovedStates] = useState({});
  const [history, setHistory] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [playbooks, setPlaybooks] = useState([]);
  const [kbStatus, setKbStatus] = useState({ connected: false, document_count: 0 });
  const [conversations, setConversations] = useState([]);
  const [platformSummary, setPlatformSummary] = useState({
    total_customers: 0, total_interactions: 0, approval_rate: 0, avg_confidence: 0,
  });
  const [activeNav, setActiveNav] = useState("Dashboard");
  const [error, setError] = useState("");
  const [agentSteps, setAgentSteps] = useState([]);

  const inputTypeOptions = [
    {
      value: "meeting_transcript",
      label: "Meeting Transcript",
      helper: "Multi-speaker dialogue. The Retrieval/Risk agents focus on the customer's lines.",
      placeholder:
        "We are getting frustrated with slow support and the onboarding felt confusing. We are considering switching to a competitor because pricing also feels high. We need a better plan for adoption before renewal next quarter.",
      example:
        "Rep: How has onboarding been going?\nCustomer: Honestly frustrating — we're still confused about the reporting dashboard, and support hasn't resolved our last two tickets.",
    },
    {
      value: "customer_email",
      label: "Customer Email",
      helper: "From/To/Subject headers are parsed out automatically; the Subject line is treated as a strong signal.",
      placeholder:
        "Subject: Renewal concerns ahead of next month\n\nHi team,\n\nWe've had three open support tickets for two weeks with no resolution. Leadership is asking if we should look at competitors before our renewal. Can we get an update and discuss pricing flexibility?\n\nThanks,\nJordan",
      example:
        "From: jordan@acmecorp.com\nTo: support@yourcompany.com\nSubject: Renewal concerns ahead of next month\n\nWe've had three open support tickets for two weeks with no resolution...",
    },
    {
      value: "crm_note",
      label: "CRM Note",
      helper: "Short 'Field: value' lines (Status, Stage, ARR, Next Step) are extracted as direct signals, not prose.",
      placeholder:
        "Status: At Risk\nStage: Renewal\nARR: 120000\nNext Step: Executive call\n\nCustomer flagged repeated support delays and is evaluating a competitor before renewal.",
      example:
        "Status: At Risk\nStage: Renewal\nNext Step: Executive call\n\nMentioned competitor evaluation during last call.",
    },
  ];

  const activeInputType = inputTypeOptions.find((opt) => opt.value === inputType) || inputTypeOptions[0];

  const navItems = [
    { icon: "⬡", label: "Dashboard" },
    { icon: "👥", label: "Customers" },
    { icon: "💬", label: "Conversations" },
    { icon: "💡", label: "Recommendations" },
    { icon: "📋", label: "Playbooks" },
    { icon: "🧠", label: "Knowledge Base" },
    { icon: "📊", label: "Reports" },
    { icon: "⚙️", label: "Settings" },
  ];

  const agents = [
    { name: "Planner Agent", color: neonGreen },
    { name: "Ingestion Agent", color: neonBlue },
    { name: "Retrieval Agent", color: neonPurple },
    { name: "Risk Agent", color: "#f59e0b" },
    { name: "Recommendation Agent", color: neonGreen },
    { name: "Memory Layer", color: neonBlue },
  ];

  const stats = useMemo(() => [
    { label: "Total Customers", value: platformSummary.total_customers || "0", change: "", color: "#ef4444" },
    { label: "Total Interactions", value: platformSummary.total_interactions || "0", change: "", color: neonGreen },
    { label: "Actions Recommended", value: recommendations.length || "0", change: "", color: neonBlue },
    { label: "Avg. Confidence Score", value: recommendations.length ? (recommendations.reduce((a, r) => a + (r.confidence || 0), 0) / recommendations.length).toFixed(2) : "0.00", change: "", color: neonPurple },
  ], [recommendations, platformSummary]);

  useEffect(() => {
    if (customerId) {
      loadHistory();
    }
  }, [customerId]);

  // Whenever this customer's history loads, restore the Dashboard's Risk
  // Analysis panel and the original text/type they were analyzed with, from
  // their single most recent interaction (history is ordered newest-first).
  // This is what makes clicking a customer in Customers/Conversations show
  // their real last analysis instead of a blank Dashboard.
  useEffect(() => {
    if (!history || history.length === 0) {
      // No saved interactions for this customer — don't leave a previous
      // customer's risk analysis/transcript showing on screen.
      setRiskAnalysis(null);
      setRecommendations([]);
      setInteractionId("");
      setApprovedStates({});
      return;
    }
    const latest = history[0];

    setRiskAnalysis({
      churn_risk_score: latest.risk_score ?? 0,
      urgency: latest.urgency || "",
      expansion_opportunity: !!latest.expansion_opportunity,
      key_signals: Array.isArray(latest.key_signals) ? latest.key_signals : [],
    });
    const latestRecs = _normalizeRecs(latest.recommendations);
    setRecommendations(latestRecs);
    setInteractionId(latest.id || "");
    if (latest.input_text) setTranscript(latest.input_text);
    if (latest.input_type) setInputType(latest.input_type);
    // Rebuild the approved/rejected badges from the actual saved data for
    // this interaction, rather than reusing whatever was left over from the
    // previously viewed customer/analysis (that was the source of cards
    // showing "Approved" for an interaction nobody had approved yet).
    const restored = {};
    latestRecs.forEach((r, i) => {
      if (r && r.approved === true) restored[i] = "approved";
      else if (r && r.approved === false && r.status === "rejected") restored[i] = "rejected";
    });
    setApprovedStates(restored);
  }, [history]);

  useEffect(() => {
    loadCustomers();
    loadPlaybooks();
    loadKbStatus();
    loadConversations();
    loadPlatformSummary();
  }, []);

  const _normalizeRecs = (recs) => {
    if (Array.isArray(recs)) return recs;
    if (typeof recs === "string") {
      try {
        const parsed = JSON.parse(recs);
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [];
      }
    }
    return [];
  };

  const loadHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/customer/${customerId}/history`);
      setHistory(res.data || []);
    } catch {
      setHistory([]);
    }
  };

  const loadCustomers = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/customers`);
      setCustomers(res.data || []);
    } catch {
      // Keep whatever customer list we already had rather than wiping it
      // out on a transient network error.
    }
  };

  const loadPlaybooks = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/playbooks`);
      setPlaybooks(res.data || []);
    } catch {
      setPlaybooks([]);
    }
  };

  const loadKbStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/knowledge-base/status`);
      setKbStatus(res.data || { connected: false, document_count: 0 });
    } catch {
      setKbStatus({ connected: false, document_count: 0 });
    }
  };

  const loadConversations = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/conversations`);
      setConversations(res.data || []);
    } catch {
      setConversations([]);
    }
  };

  const loadPlatformSummary = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/reports/summary`);
      setPlatformSummary(res.data || platformSummary);
    } catch {
      // keep previous summary on transient failure
    }
  };

  const refreshAllData = async () => {
    await Promise.all([
      loadCustomers(),
      loadPlaybooks(),
      loadKbStatus(),
      loadConversations(),
      loadPlatformSummary(),
    ]);
  };

  const formatRelativeTime = (isoString) => {
    if (!isoString || isoString === "now") return "just now";
    const then = new Date(isoString).getTime();
    if (Number.isNaN(then)) return isoString;
    const diffMs = Date.now() - then;
    const minutes = Math.floor(diffMs / 60000);
    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    setRecommendations([]);
    setRiskAnalysis(null);
    setAgentSteps([]);
    setInteractionId("");
    // A fresh analysis always starts as a brand new, unapproved interaction —
    // clear any leftover Approved/Rejected UI state from whatever was shown
    // before, so card 1/2/3 don't inherit a previous interaction's status.
    setApprovedStates({});
    const sid = `session-${Date.now()}`;
    setSessionId(sid);

    const steps = [
      "🔵 Planner Agent — decomposing task...",
      `📥 Ingestion Agent — processing ${activeInputType.label.toLowerCase()}...`,
      "🔍 Retrieval Agent — searching knowledge base...",
      "📊 Risk Agent — analyzing churn signals...",
      "💡 Recommendation Agent — generating actions...",
    ];

    // Fire the real request immediately instead of waiting ~2.5s for a fake
    // step-by-step animation to finish first. The animation still plays, but
    // concurrently with the actual call — whichever finishes first wins, so
    // a fast backend response is no longer held back by the UI delay.
    let cancelled = false;
    const animate = async () => {
      for (let i = 0; i < steps.length; i += 1) {
        if (cancelled) return;
        await new Promise((resolve) => setTimeout(resolve, 350));
        if (cancelled) return;
        setAgentSteps((prev) => [...prev, steps[i]]);
      }
    };
    const animationPromise = animate();

    try {
      const res = await axios.post(`${API_BASE}/api/analyze`, {
        customer_id: customerId,
        input_text: transcript,
        session_id: sid,
        input_type: inputType,
      });
      // The real response already arrived — stop the animation where it is
      // and immediately show all remaining steps plus the result, instead of
      // waiting for the animation loop to catch up.
      cancelled = true;
      setAgentSteps(steps);
      setRecommendations(res.data.recommendations || []);
      setRiskAnalysis(res.data.risk_analysis || null);
      setInteractionId(res.data.interaction_id || "");
      setAgentSteps((prev) => [...prev, "✅ Analysis complete!"]);
      await loadHistory();
      await refreshAllData();
    } catch (err) {
      cancelled = true;
      const detail =
        err?.response?.data?.detail ||
        err?.response?.statusText ||
        err?.message ||
        "Unknown error";
      setError(`Backend error (${err?.response?.status || "no response"}): ${detail}`);
      setAgentSteps((prev) => [...prev, "❌ Error connecting to backend"]);
    }
    await animationPromise;
    setLoading(false);
  };

  const handleApproval = async (index, approved) => {
    if (!interactionId) {
      setError(
        "No interaction_id was returned from the last analyze call, so this approval can't be saved. Re-run Analyze first."
      );
      return;
    }
    try {
      await axios.post(`${API_BASE}/api/approve/${interactionId}`, {
        approved,
        feedback: approved ? "Approved by CSM" : "Rejected by CSM",
        rec_index: index,
      });
      setApprovedStates((prev) => ({ ...prev, [index]: approved ? "approved" : "rejected" }));
      setError("");
      await loadHistory();
      await loadPlatformSummary();
      await loadConversations();
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.response?.statusText ||
        err?.message ||
        "Unknown error";
      setError(`Approval failed (${err?.response?.status || "no response"}): ${detail}`);
    }
  };

  const handleNavClick = (label) => {
    setActiveNav(label);
    if (label === "Recommendations") loadHistory();
    if (label === "Conversations") loadConversations();
    if (label === "Customers") loadCustomers();
  };

  const getPriorityColor = (p) => {
    if (!p) return neonBlue;
    if (p.toLowerCase() === "high") return "#ef4444";
    if (p.toLowerCase() === "medium") return "#f59e0b";
    return neonGreen;
  };

  const getRiskColor = (score) => {
    if (score >= 70) return "#ef4444";
    if (score >= 40) return "#f59e0b";
    return neonGreen;
  };

  const renderDashboard = () => (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
        {stats.map((s) => (
          <div key={s.label} style={{ ...glassCard, padding: "20px 24px" }}>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginBottom: 8 }}>{s.label}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: s.color, textShadow: `0 0 20px ${s.color}40` }}>{s.value}</div>
            {s.change && <div style={{ fontSize: 11, color: neonGreen, marginTop: 4 }}>↑ {s.change} vs last month</div>}
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
        <div style={{ ...glassCard, padding: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: neonBlue, boxShadow: `0 0 8px ${neonBlue}` }} />
            <h2 style={{ fontSize: 15, fontWeight: 600, color: "#fff", margin: 0 }}>Analyze Customer Interaction</h2>
          </div>

          <label style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", display: "block", marginBottom: 6 }}>Customer ID</label>
          <input value={customerId} onChange={(e) => setCustomerId(e.target.value)}
            style={{
              width: "100%", padding: "10px 14px", borderRadius: 10, fontSize: 13,
              background: "rgba(255,255,255,0.05)", border: "1px solid rgba(0,212,255,0.3)",
              color: "#fff", outline: "none", marginBottom: 16, boxSizing: "border-box",
            }} />

          <label style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", display: "block", marginBottom: 6 }}>Interaction Type</label>
          <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
            {inputTypeOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setInputType(opt.value)}
                style={{
                  flex: 1, padding: "8px 10px", borderRadius: 8, fontSize: 12, fontWeight: 600,
                  cursor: "pointer",
                  border: `1px solid ${inputType === opt.value ? neonBlue : "rgba(255,255,255,0.15)"}`,
                  background: inputType === opt.value ? "rgba(0,212,255,0.12)" : "transparent",
                  color: inputType === opt.value ? neonBlue : "rgba(255,255,255,0.5)",
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)", marginBottom: 14, lineHeight: 1.5 }}>
            {activeInputType.helper}{" "}
            <span
              onClick={() => setTranscript(activeInputType.example)}
              style={{ color: neonBlue, cursor: "pointer", textDecoration: "underline" }}
            >
              Load example
            </span>
          </div>

          <label style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", display: "block", marginBottom: 6 }}>
            {activeInputType.label} text
          </label>
          <textarea value={transcript} onChange={(e) => setTranscript(e.target.value)} rows={6}
            placeholder={activeInputType.placeholder}
            style={{
              width: "100%", padding: "10px 14px", borderRadius: 10, fontSize: 13,
              background: "rgba(255,255,255,0.05)", border: "1px solid rgba(0,212,255,0.2)",
              color: "#e2e8f0", outline: "none", resize: "vertical", boxSizing: "border-box",
              lineHeight: 1.6,
            }} />

          <button onClick={handleAnalyze} disabled={loading} style={{
            marginTop: 16, width: "100%", padding: "12px",
            background: loading ? "rgba(0,212,255,0.2)" : `linear-gradient(135deg, ${neonBlue}, ${neonPurple})`,
            border: "none", borderRadius: 10, color: "#fff", fontSize: 14, fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
            boxShadow: loading ? "none" : `0 0 20px rgba(0,212,255,0.4)`,
            transition: "all 0.3s",
          }}>
            {loading ? "🤖 Agents Processing..." : "⚡ Analyze with AI Agents"}
          </button>

          {agentSteps.length > 0 && (
            <div style={{ marginTop: 16, padding: 14, borderRadius: 10, background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.05)" }}>
              {agentSteps.map((step, i) => (
                <div key={i} style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", marginBottom: 4, lineHeight: 1.6 }}>{step}</div>
              ))}
            </div>
          )}

          {error && (
            <div style={{ marginTop: 12, padding: 12, borderRadius: 10, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", fontSize: 12, color: "#ef4444" }}>
              ⚠️ {error}
            </div>
          )}
        </div>

        <div style={{ ...glassCard, padding: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#ef4444", boxShadow: "0 0 8px #ef4444" }} />
            <h2 style={{ fontSize: 15, fontWeight: 600, color: "#fff", margin: 0 }}>Risk Analysis</h2>
          </div>

          {!riskAnalysis ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: 200, color: "rgba(255,255,255,0.2)" }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>📊</div>
              <div style={{ fontSize: 13 }}>Run analysis to see risk insights</div>
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span style={{ fontSize: 13, color: "rgba(255,255,255,0.6)" }}>Churn Risk Score</span>
                  <span style={{ fontSize: 20, fontWeight: 700, color: getRiskColor(riskAnalysis.churn_risk_score) }}>
                    {riskAnalysis.churn_risk_score || 0}%
                  </span>
                </div>
                <div style={{ height: 8, borderRadius: 4, background: "rgba(255,255,255,0.1)", overflow: "hidden" }}>
                  <div style={{
                    height: "100%", width: `${riskAnalysis.churn_risk_score || 0}%`,
                    background: `linear-gradient(90deg, ${neonBlue}, ${getRiskColor(riskAnalysis.churn_risk_score)})`,
                    borderRadius: 4, boxShadow: `0 0 10px ${getRiskColor(riskAnalysis.churn_risk_score)}`,
                    transition: "width 1s ease",
                  }} />
                </div>
              </div>

              <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
                <span style={{ padding: "4px 12px", borderRadius: 99, fontSize: 11, fontWeight: 600, background: `rgba(239,68,68,0.15)`, border: "1px solid rgba(239,68,68,0.4)", color: "#ef4444" }}>
                  Urgency: {riskAnalysis.urgency || "N/A"}
                </span>
                {riskAnalysis.expansion_opportunity && (
                  <span style={{ padding: "4px 12px", borderRadius: 99, fontSize: 11, fontWeight: 600, background: `rgba(0,255,157,0.15)`, border: `1px solid ${neonGreen}40`, color: neonGreen }}>
                    🚀 Expansion Signal
                  </span>
                )}
              </div>

              {riskAnalysis.key_signals && (
                <div>
                  <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginBottom: 8 }}>KEY SIGNALS</div>
                  {riskAnalysis.key_signals.map((signal, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 8 }}>
                      <div style={{ width: 6, height: 6, borderRadius: "50%", background: neonBlue, marginTop: 5, flexShrink: 0 }} />
                      <span style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", lineHeight: 1.5 }}>{signal}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div style={{ ...glassCard, padding: 24, marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: neonGreen, boxShadow: `0 0 8px ${neonGreen}` }} />
          <h2 style={{ fontSize: 15, fontWeight: 600, color: "#fff", margin: 0 }}>Recommended Next Actions</h2>
          <span style={{ marginLeft: "auto", fontSize: 12, color: "rgba(255,255,255,0.3)" }}>Agentic guidance • {recommendations.length} actions</span>
        </div>

        {recommendations.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px 0", color: "rgba(255,255,255,0.2)" }}>
            <div style={{ fontSize: 36, marginBottom: 10 }}>💡</div>
            <div style={{ fontSize: 13 }}>Submit an interaction to generate recommended actions</div>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
            {recommendations.map((rec, i) => (
              <div key={i} style={{
                background: "rgba(255,255,255,0.03)",
                border: `1px solid ${getPriorityColor(rec.priority)}30`,
                borderRadius: 12, padding: 18,
                boxShadow: approvedStates[i] === "approved" ? `0 0 20px ${neonGreen}30` : "none",
                transition: "all 0.3s",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <span style={{
                    padding: "3px 10px", borderRadius: 99, fontSize: 10, fontWeight: 700,
                    background: `${getPriorityColor(rec.priority)}20`,
                    border: `1px solid ${getPriorityColor(rec.priority)}50`,
                    color: getPriorityColor(rec.priority), textTransform: "uppercase",
                  }}>{rec.priority || "medium"}</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: neonBlue }}>{Math.round((rec.confidence || 0) * 100)}%</span>
                </div>

                {rec.source && (
                  <div style={{
                    fontSize: 9, marginBottom: 10, color: rec.source === "gemini" ? neonGreen : "#f59e0b",
                    textTransform: "uppercase", letterSpacing: 0.5,
                  }}>
                    {rec.source === "gemini" ? "● Gemini-generated" : `● Fallback (${rec.source.replace("fallback_", "")})`}
                  </div>
                )}

                <div style={{ height: 3, borderRadius: 2, background: "rgba(255,255,255,0.1)", marginBottom: 12, overflow: "hidden" }}>
                  <div style={{
                    height: "100%", width: `${(rec.confidence || 0) * 100}%`,
                    background: `linear-gradient(90deg, ${neonBlue}, ${neonGreen})`,
                    boxShadow: `0 0 6px ${neonBlue}`,
                  }} />
                </div>

                <div style={{ fontSize: 13, fontWeight: 600, color: "#fff", marginBottom: 8, lineHeight: 1.4 }}>{rec.action}</div>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.45)", lineHeight: 1.6, marginBottom: 12 }}>{rec.reasoning?.slice(0, 120)}...</div>

                {rec.evidence && rec.evidence.slice(0, 2).map((e, j) => (
                  <div key={j} style={{
                    fontSize: 10, padding: "3px 8px", borderRadius: 6, marginBottom: 4,
                    background: "rgba(0,212,255,0.08)", border: "1px solid rgba(0,212,255,0.2)",
                    color: "rgba(255,255,255,0.5)", lineHeight: 1.4,
                  }}>{e?.slice(0, 60)}...</div>
                ))}

                {rec.timeline && (
                  <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", marginTop: 8, marginBottom: 12 }}>⏱ {rec.timeline}</div>
                )}

                {!approvedStates[i] ? (
                  <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                    <button onClick={() => handleApproval(i, true)} style={{
                      flex: 1, padding: "8px", borderRadius: 8, border: `1px solid ${neonGreen}`,
                      background: `rgba(0,255,157,0.1)`, color: neonGreen, fontSize: 12,
                      fontWeight: 600, cursor: "pointer",
                    }}>✓ Approve</button>
                    <button onClick={() => handleApproval(i, false)} style={{
                      flex: 1, padding: "8px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.15)",
                      background: "transparent", color: "rgba(255,255,255,0.4)", fontSize: 12,
                      fontWeight: 600, cursor: "pointer",
                    }}>✗ Reject</button>
                  </div>
                ) : (
                  <div style={{
                    marginTop: 12, padding: "8px", borderRadius: 8, textAlign: "center",
                    background: approvedStates[i] === "approved" ? `rgba(0,255,157,0.15)` : "rgba(239,68,68,0.1)",
                    border: `1px solid ${approvedStates[i] === "approved" ? neonGreen : "#ef4444"}40`,
                    color: approvedStates[i] === "approved" ? neonGreen : "#ef4444",
                    fontSize: 12, fontWeight: 600,
                  }}>
                    {approvedStates[i] === "approved" ? "✓ Approved" : "✗ Rejected"}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ ...glassCard, padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: neonPurple, boxShadow: `0 0 8px ${neonPurple}` }} />
          <h2 style={{ fontSize: 15, fontWeight: 600, color: "#fff", margin: 0 }}>Past Interactions — {customerId}</h2>
        </div>

        {history.length === 0 ? (
          <div style={{ textAlign: "center", padding: "20px 0", color: "rgba(255,255,255,0.2)", fontSize: 13 }}>
            No past interactions yet for {customerId}
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
            {history.map((item, i) => (
              <div key={i} style={{ padding: 16, borderRadius: 12, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#fff" }}>{new Date(item.created_at || Date.now()).toLocaleString()}</div>
                  <div style={{ fontSize: 11, color: item.approved ? neonGreen : "#f87171" }}>{item.approved ? "✓ Approved" : "✗ Pending"}</div>
                </div>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.45)", marginBottom: 8 }}>{Array.isArray(item.recommendations) ? item.recommendations.length : 0} recommendations</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {Array.isArray(item.recommendations) && item.recommendations.slice(0, 3).map((rec, idx) => (
                    <span key={`${rec.action || idx}-${idx}`} style={{ fontSize: 11, padding: "4px 8px", borderRadius: 999, background: "rgba(0,212,255,0.1)", color: "rgba(255,255,255,0.7)" }}>
                      {rec.action || rec.title || "Recommendation"}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );

  const renderSection = () => {
    switch (activeNav) {
      case "Customers":
        return (
          <div style={{ ...glassCard, padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: "#fff", margin: 0 }}>Customer Overview</h2>
              <button onClick={loadCustomers} style={{
                padding: "6px 14px", borderRadius: 8, border: "1px solid rgba(0,212,255,0.3)",
                background: "rgba(0,212,255,0.08)", color: neonBlue, fontSize: 12, cursor: "pointer",
              }}>↻ Refresh</button>
            </div>
            {customers.length === 0 ? (
              <div style={{ textAlign: "center", padding: "30px 0", color: "rgba(255,255,255,0.3)", fontSize: 13 }}>
                No customers yet — run an analysis on any Customer ID from the Dashboard and it will appear here automatically.
              </div>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse", color: "rgba(255,255,255,0.85)" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                    <th style={{ textAlign: "left", padding: "10px 8px", fontSize: 12, color: "rgba(255,255,255,0.4)", textTransform: "uppercase" }}>Customer ID</th>
                    <th style={{ textAlign: "left", padding: "10px 8px", fontSize: 12, color: "rgba(255,255,255,0.4)", textTransform: "uppercase" }}>Risk Level</th>
                    <th style={{ textAlign: "left", padding: "10px 8px", fontSize: 12, color: "rgba(255,255,255,0.4)", textTransform: "uppercase" }}>Last Interaction</th>
                    <th style={{ textAlign: "left", padding: "10px 8px", fontSize: 12, color: "rgba(255,255,255,0.4)", textTransform: "uppercase" }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {customers.map((item) => (
                    <tr
                      key={item.id}
                      onClick={() => { setCustomerId(item.id); setActiveNav("Dashboard"); }}
                      style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", cursor: "pointer" }}
                    >
                      <td style={{ padding: "12px 8px" }}>{item.id}</td>
                      <td style={{ padding: "12px 8px" }}>{item.risk}</td>
                      <td style={{ padding: "12px 8px" }}>{formatRelativeTime(item.last_interaction)}</td>
                      <td style={{ padding: "12px 8px" }}>{item.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        );
      case "Conversations":
        return (
          <div style={{ ...glassCard, padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: "#fff", margin: 0 }}>Recent Transcripts</h2>
              <button onClick={loadConversations} style={{
                padding: "6px 14px", borderRadius: 8, border: "1px solid rgba(0,212,255,0.3)",
                background: "rgba(0,212,255,0.08)", color: neonBlue, fontSize: 12, cursor: "pointer",
              }}>↻ Refresh</button>
            </div>
            {conversations.length === 0 ? (
              <div style={{ textAlign: "center", padding: "30px 0", color: "rgba(255,255,255,0.3)", fontSize: 13 }}>
                No conversations yet — analyze a transcript, email, or CRM note from the Dashboard and it will show up here.
              </div>
            ) : (
              <div style={{ display: "grid", gap: 12 }}>
                {conversations.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => { setCustomerId(item.customer_id); setActiveNav("Dashboard"); }}
                    style={{ padding: 16, borderRadius: 12, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", cursor: "pointer" }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={{ fontSize: 14, fontWeight: 600, color: "#fff" }}>{item.customer_id}</span>
                        {(() => {
                          const badge = {
                            meeting_transcript: { label: "Meeting Transcript", color: neonBlue },
                            customer_email: { label: "Customer Email", color: neonGreen },
                            crm_note: { label: "CRM Note", color: neonPurple },
                          }[item.input_type] || { label: "Meeting Transcript", color: neonBlue };
                          return (
                            <span style={{
                              fontSize: 11, padding: "2px 8px", borderRadius: 999,
                              background: `${badge.color}1F`, color: badge.color, fontWeight: 500,
                            }}>
                              {badge.label}
                            </span>
                          );
                        })()}
                        {item.risk_score != null && (
                          <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 999, background: item.risk_score >= 60 ? "rgba(239,68,68,0.15)" : item.risk_score >= 35 ? "rgba(245,158,11,0.15)" : "rgba(0,255,157,0.12)", color: item.risk_score >= 60 ? "#f87171" : item.risk_score >= 35 ? "#fbbf24" : "#00ff9d" }}>
                            Risk: {item.risk_score}%
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: 11, color: "rgba(255,255,255,0.35)" }}>{formatRelativeTime(item.created_at)}</div>
                    </div>
                    <div style={{ fontSize: 13, color: item.has_text ? "rgba(255,255,255,0.65)" : "rgba(255,255,255,0.3)", fontStyle: item.has_text ? "normal" : "italic", lineHeight: 1.5 }}>
                      {item.has_text ? item.summary : "No content saved"}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      case "Recommendations":
        return (
          <div style={{ ...glassCard, padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: 18, fontWeight: 700, color: "#fff", marginBottom: 4 }}>Past Recommendations</h2>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.35)" }}>
                  Customer: <span style={{ color: neonBlue }}>{customerId}</span> — change Customer ID on the Dashboard to see another customer.
                </div>
              </div>
              <button onClick={loadHistory} style={{
                padding: "6px 14px", borderRadius: 8, border: "1px solid rgba(0,212,255,0.3)",
                background: "rgba(0,212,255,0.08)", color: neonBlue, fontSize: 12, cursor: "pointer",
              }}>↻ Refresh</button>
            </div>
            {history.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px 0", color: "rgba(255,255,255,0.3)", fontSize: 13 }}>
                No historical recommendations yet for <span style={{ color: neonBlue }}>{customerId}</span>.<br />
                <span style={{ fontSize: 12, marginTop: 6, display: "block" }}>Analyze a transcript on the Dashboard to generate recommendations.</span>
              </div>
            ) : (
              <div style={{ display: "grid", gap: 16 }}>
                {history.map((item, index) => (
                  <div key={`${item.id || index}`} style={{ padding: 20, borderRadius: 12, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: "#fff" }}>{new Date(item.created_at || Date.now()).toLocaleString()}</div>
                        {item.input_type && (
                          <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 999, background: "rgba(0,212,255,0.1)", color: neonBlue }}>
                            {(item.input_type || "").replace(/_/g, " ")}
                          </span>
                        )}
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        {item.risk_score != null && (
                          <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 999, background: item.risk_score >= 60 ? "rgba(239,68,68,0.15)" : item.risk_score >= 35 ? "rgba(245,158,11,0.15)" : "rgba(0,255,157,0.12)", color: item.risk_score >= 60 ? "#f87171" : item.risk_score >= 35 ? "#fbbf24" : "#00ff9d" }}>
                            Risk {item.risk_score}%
                          </span>
                        )}
                        {(() => {
                          const recs = Array.isArray(item.recommendations) ? item.recommendations : [];
                          const approvedCount = recs.filter((r) => r && r.approved === true).length;
                          const rejectedCount = recs.filter((r) => r && r.approved === false && r.status === "rejected").length;
                          const label =
                            approvedCount === 0 && rejectedCount === 0
                              ? "Pending"
                              : `${approvedCount}/${recs.length || 0} Approved`;
                          const color = approvedCount > 0 ? neonGreen : rejectedCount > 0 ? "#f87171" : "rgba(255,255,255,0.4)";
                          return (
                            <div style={{ fontSize: 12, fontWeight: 600, color }}>{label}</div>
                          );
                        })()}
                      </div>
                    </div>
                    {item.input_text && (
                      <div style={{ fontSize: 12, color: "rgba(255,255,255,0.45)", background: "rgba(255,255,255,0.03)", borderRadius: 8, padding: "8px 12px", marginBottom: 12, borderLeft: "2px solid rgba(0,212,255,0.3)", fontStyle: "italic", lineHeight: 1.5 }}>
                        "{(item.input_text || "").length > 180 ? (item.input_text || "").slice(0, 180) + "…" : item.input_text}"
                      </div>
                    )}
                    {Array.isArray(item.recommendations) && item.recommendations.length > 0 ? (
                      <div style={{ display: "grid", gap: 8 }}>
                        {item.recommendations.map((rec, idx) => (
                          <div key={`${rec.action || idx}-${idx}`} style={{
                            padding: "10px 14px", borderRadius: 8,
                            background: rec.approved === true ? "rgba(0,255,157,0.05)" : rec.approved === false && rec.status === "rejected" ? "rgba(239,68,68,0.04)" : "rgba(255,255,255,0.04)",
                            border: rec.approved === true ? `1px solid ${neonGreen}40` : rec.approved === false && rec.status === "rejected" ? "1px solid #ef444440" : "1px solid rgba(255,255,255,0.07)",
                            display: "flex", alignItems: "flex-start", gap: 10,
                          }}>
                            <div style={{ minWidth: 6, height: 6, borderRadius: "50%", background: getPriorityColor(rec.priority), marginTop: 5, flexShrink: 0 }} />
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: 13, fontWeight: 600, color: "#fff", marginBottom: 3 }}>{rec.action || rec.title || "Recommendation"}</div>
                              {rec.rationale && <div style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", lineHeight: 1.4 }}>{rec.rationale}</div>}
                              {rec.expected_outcome && <div style={{ fontSize: 11, color: neonGreen, marginTop: 4 }}>→ {rec.expected_outcome}</div>}
                            </div>
                            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4, minWidth: 70 }}>
                              {rec.priority && <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 999, background: `${getPriorityColor(rec.priority)}22`, color: getPriorityColor(rec.priority), fontWeight: 600, textTransform: "uppercase" }}>{rec.priority}</span>}
                              {rec.confidence != null && <span style={{ fontSize: 10, color: "rgba(255,255,255,0.35)" }}>{Math.round(rec.confidence * 100)}% conf.</span>}
                              {rec.approved === true ? (
                                <span style={{ fontSize: 10, fontWeight: 700, color: neonGreen, padding: "2px 6px", borderRadius: 999, background: "rgba(0,255,157,0.12)", border: `1px solid ${neonGreen}40` }}>✓ Approved</span>
                              ) : rec.approved === false && rec.status === "rejected" ? (
                                <span style={{ fontSize: 10, fontWeight: 700, color: "#f87171", padding: "2px 6px", borderRadius: 999, background: "rgba(239,68,68,0.12)", border: "1px solid #ef444440" }}>✗ Rejected</span>
                              ) : (
                                <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)" }}>Pending</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ fontSize: 12, color: "rgba(255,255,255,0.3)", fontStyle: "italic" }}>No recommendations stored for this interaction.</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      case "Playbooks":
        return (
          <div style={{ ...glassCard, padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: "#fff", margin: 0 }}>Loaded Playbooks</h2>
              <button onClick={loadPlaybooks} style={{
                padding: "6px 14px", borderRadius: 8, border: "1px solid rgba(0,212,255,0.3)",
                background: "rgba(0,212,255,0.08)", color: neonBlue, fontSize: 12, cursor: "pointer",
              }}>↻ Refresh</button>
            </div>
            {playbooks.length === 0 ? (
              <div style={{ textAlign: "center", padding: "30px 0", color: "rgba(255,255,255,0.3)", fontSize: 13 }}>
                No documents found in ChromaDB. Run the knowledge loader on the backend, then refresh.
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 14 }}>
                {playbooks.map((item) => (
                  <div key={item.id} style={{ padding: 16, borderRadius: 12, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                    <div style={{ fontSize: 13, color: neonBlue, marginBottom: 6, textTransform: "capitalize" }}>{item.category}</div>
                    <div style={{ fontSize: 15, fontWeight: 600, color: "#fff", marginBottom: 6 }}>{item.title}</div>
                    <div style={{ fontSize: 13, color: "rgba(255,255,255,0.55)" }}>{item.text}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      case "Knowledge Base":
        return (
          <div style={{ ...glassCard, padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: "#fff", margin: 0 }}>Knowledge Base Status</h2>
              <button onClick={loadKbStatus} style={{
                padding: "6px 14px", borderRadius: 8, border: "1px solid rgba(0,212,255,0.3)",
                background: "rgba(0,212,255,0.08)", color: neonBlue, fontSize: 12, cursor: "pointer",
              }}>↻ Refresh</button>
            </div>
            <div style={{ display: "grid", gap: 12 }}>
              <div style={{ padding: 16, borderRadius: 12, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: 6 }}>ChromaDB Status</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: kbStatus.connected ? neonGreen : "#ef4444" }}>
                  {kbStatus.connected ? "Connected" : "Disconnected"}
                </div>
              </div>
              <div style={{ padding: 16, borderRadius: 12, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: 6 }}>Document Count</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: "#fff" }}>{kbStatus.document_count} documents</div>
              </div>
            </div>
          </div>
        );
      case "Reports":
        return (
          <div style={{ ...glassCard, padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: "#fff", margin: 0 }}>Operational Reports</h2>
              <button onClick={loadPlatformSummary} style={{
                padding: "6px 14px", borderRadius: 8, border: "1px solid rgba(0,212,255,0.3)",
                background: "rgba(0,212,255,0.08)", color: neonBlue, fontSize: 12, cursor: "pointer",
              }}>↻ Refresh</button>
            </div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.35)", marginBottom: 16 }}>
              Platform-wide totals across all {platformSummary.total_customers} customer{platformSummary.total_customers === 1 ? "" : "s"}.
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
              <div style={{ padding: 16, borderRadius: 12, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: 6 }}>Total Interactions</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: "#fff" }}>{platformSummary.total_interactions}</div>
              </div>
              <div style={{ padding: 16, borderRadius: 12, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: 6 }}>Approval Rate</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: neonGreen }}>{platformSummary.approval_rate}%</div>
              </div>
              <div style={{ padding: 16, borderRadius: 12, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: 6 }}>Avg Confidence (all-time)</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: neonBlue }}>{platformSummary.avg_confidence?.toFixed ? platformSummary.avg_confidence.toFixed(2) : platformSummary.avg_confidence}</div>
              </div>
            </div>
          </div>
        );
      case "Settings":
        return (
          <div style={{ ...glassCard, padding: 24 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: "#fff", marginBottom: 16 }}>Environment Configuration</h2>
            <div style={{ display: "grid", gap: 12 }}>
              {[
                { label: "SUPABASE_URL", value: import.meta.env.VITE_SUPABASE_URL || "https://your-project.supabase.co" },
                { label: "SUPABASE_KEY", value: "••••••••••••••••" },
                { label: "GOOGLE_API_KEY", value: "••••••••••••••••" },
                { label: "CHROMA_HOST", value: import.meta.env.VITE_CHROMA_HOST || "localhost" },
                { label: "CHROMA_PORT", value: import.meta.env.VITE_CHROMA_PORT || "8001" },
              ].map((field) => (
                <div key={field.label} style={{ padding: 14, borderRadius: 12, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                  <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", marginBottom: 6 }}>{field.label}</div>
                  <div style={{ fontSize: 14, color: "#fff" }}>{field.value}</div>
                </div>
              ))}
            </div>
          </div>
        );
      default:
        return renderDashboard();
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0a0a1a 0%, #0d1117 40%, #0a1628 100%)",
      display: "flex",
      fontFamily: "'Inter', 'Segoe UI', sans-serif",
      color: "#e2e8f0",
    }}>
      <div style={{ position: "fixed", top: "10%", left: "20%", width: 400, height: 400, background: "radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%)", borderRadius: "50%", pointerEvents: "none", zIndex: 0 }} />
      <div style={{ position: "fixed", bottom: "20%", right: "15%", width: 500, height: 500, background: "radial-gradient(circle, rgba(168,85,247,0.06) 0%, transparent 70%)", borderRadius: "50%", pointerEvents: "none", zIndex: 0 }} />

      <div style={{ width: 220, minHeight: "100vh", position: "fixed", left: 0, top: 0, background: "rgba(10,10,26,0.9)", backdropFilter: "blur(20px)", borderRight: "1px solid rgba(0,212,255,0.15)", display: "flex", flexDirection: "column", padding: "24px 0", zIndex: 10 }}>
        <div style={{ padding: "0 20px 32px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: `linear-gradient(135deg, ${neonBlue}, ${neonPurple})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, fontWeight: 700 }}>N</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#fff" }}>NBA Platform</div>
              <div style={{ fontSize: 10, color: neonBlue }}>Next Best Action</div>
            </div>
          </div>
        </div>

        {navItems.map((item) => (
          <button key={item.label} onClick={() => handleNavClick(item.label)} style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "11px 20px", cursor: "pointer",
            background: activeNav === item.label ? "rgba(0,212,255,0.1)" : "transparent",
            border: "none",
            borderLeft: activeNav === item.label ? `3px solid ${neonBlue}` : "3px solid transparent",
            color: activeNav === item.label ? neonBlue : "rgba(255,255,255,0.5)",
            fontSize: 13, fontWeight: activeNav === item.label ? 600 : 400,
            transition: "all 0.2s",
            textAlign: "left",
          }}>
            <span style={{ fontSize: 16 }}>{item.icon}</span>
            {item.label}
          </button>
        ))}

        <div style={{ marginTop: "auto", padding: "20px 20px 0" }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: "rgba(255,255,255,0.3)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>Agent Status</div>
          {agents.map((agent) => (
            <div key={agent.name} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: agent.color, boxShadow: `0 0 6px ${agent.color}` }} />
              <span style={{ fontSize: 11, color: "rgba(255,255,255,0.5)" }}>{agent.name}</span>
              <span style={{ marginLeft: "auto", fontSize: 10, color: agent.color }}>Online</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginLeft: 220, flex: 1, padding: "28px 32px", position: "relative", zIndex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: "#fff", margin: 0 }}>{activeNav}</h1>
            <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", margin: "4px 0 0" }}>AI-powered next best actions for your customers</p>
          </div>
          <div style={{ padding: "8px 16px", borderRadius: 8, background: "rgba(0,255,157,0.1)", border: `1px solid ${neonGreen}`, fontSize: 12, color: neonGreen, fontWeight: 600 }}>
            🟢 All Systems Operational
          </div>
        </div>

        {renderSection()}
      </div>
    </div>
  );
}