import React, { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Activity,
  UserRound,
  Shield,
  Palette,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  Bell,
  Sparkles,
  X,
  CheckCircle2,
  AlertCircle,
  Database,
  ExternalLink,
} from "lucide-react";
import { Logo, SearchField, SkeletonPage, Tip, cx, Badge, Card } from "./ui";
import Overview from "./pages/Overview";
import Match from "./pages/Match";
import Player from "./pages/Player";
import Team from "./pages/Team";
import System from "./pages/System";
import { sendChatQuery } from "./services/api";
import StatCards from "./components/StatCards";
import ChartRenderer from "./components/ChartRenderer";
import VerificationPipelineCard from "./components/VerificationPipelineCard";
import NLPTransparencyCard from "./components/NLPTransparencyCard";

const NAV = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "match", label: "Match Center", icon: Activity },
  { id: "player", label: "Player Analytics", icon: UserRound },
  { id: "team", label: "Team Analytics", icon: Shield },
  { id: "system", label: "Design System", icon: Palette },
];

const INDEX = [
  { t: "Arjun Mehta", s: "Player · IND", p: "player" },
  { t: "Karan Malhotra", s: "Player · IND", p: "player" },
  { t: "Rohit Sharma", s: "Player · IND (Career High: 264)", p: "player", query: "highest run scored by rohit" },
  { t: "Virat Kohli", s: "Player · IND (IPL 2022 Stats)", p: "player", query: "Show me Virat Kohli's IPL statistics in 2022." },
  { t: "India", s: "Team", p: "team" },
  { t: "Australia", s: "Team", p: "team" },
  { t: "IND vs AUS · 2nd T20I", s: "Match · 12 Mar 2025", p: "match" },
  { t: "ENG vs RSA · 3rd ODI", s: "Match · 09 Mar 2025", p: "match" },
];

export default function App() {
  const [page, setPage] = useState("overview");
  const [collapsed, setCollapsed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState("");

  // AI Analytics State
  const [isAiOpen, setIsAiOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);
  const [aiResponse, setAiResponse] = useState(null);
  const [conversationId, setConversationId] = useState(`conv_${Date.now()}`);

  useEffect(() => {
    if (window.innerWidth < 1024) setCollapsed(true);
  }, []);

  const go = (p) => {
    if (p === page) return;
    setLoading(true);
    setPage(p);
    setQ("");
    window.scrollTo(0, 0);
    document.getElementById("main")?.scrollTo(0, 0);
    setTimeout(() => setLoading(false), 350);
  };

  const handleAiQuery = async (queryText) => {
    if (!queryText || !queryText.trim()) return;
    setIsAiOpen(true);
    setAiLoading(true);
    setAiError(null);
    try {
      const resp = await sendChatQuery(queryText.trim(), { conversation_id: conversationId });
      setAiResponse(resp);
    } catch (err) {
      setAiError(err.message || "Failed to retrieve intelligence analytics.");
    } finally {
      setAiLoading(false);
    }
  };

  const hits = q ? INDEX.filter((i) => i.t.toLowerCase().includes(q.toLowerCase())) : [];

  return (
    <div className="flex h-screen w-full bg-background text-foreground font-sans">
      {/* Exact Figma Sidebar */}
      <aside
        className={cx(
          "flex shrink-0 flex-col border-r border-border bg-sidebar transition-[width] duration-200 z-30 select-none",
          collapsed ? "w-[68px]" : "w-60"
        )}
      >
        <div className={cx("flex h-16 items-center border-b border-border", collapsed ? "justify-center" : "px-5")}>
          <Logo compact={collapsed} />
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {!collapsed && (
            <div className="num px-2 pb-2 pt-1 text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-semibold">
              Analyze
            </div>
          )}
          {NAV.map((n) => {
            const I = n.icon;
            const on = page === n.id;
            return (
              <button
                key={n.id}
                onClick={() => go(n.id)}
                aria-current={on ? "page" : undefined}
                className={cx(
                  "relative flex h-10 w-full items-center gap-3 rounded-md text-[13px] font-semibold transition",
                  collapsed ? "justify-center" : "px-3",
                  on ? "bg-accent text-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                )}
              >
                {on && <span className="absolute inset-y-2 left-0 w-0.5 rounded bg-primary" />}
                <I size={17} className={on ? "text-primary" : ""} />
                {!collapsed && n.label}
              </button>
            );
          })}
        </nav>

        {!collapsed && (
          <div className="m-3 rounded-md border border-border bg-secondary/60 p-3">
            <div className="num text-[10px] uppercase tracking-widest text-primary font-bold">Model</div>
            <div className="mt-1 text-xs font-semibold">WP model v2.3</div>
            <div className="mt-0.5 text-[11px] text-muted-foreground">Ball-by-ball coverage 94%</div>
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex h-12 items-center justify-center gap-2 border-t border-border text-xs text-muted-foreground transition hover:text-foreground"
          aria-label="Toggle sidebar"
        >
          {collapsed ? <PanelLeftOpen size={16} /> : <><PanelLeftClose size={16} />Collapse</>}
        </button>
      </aside>

      {/* Main Column */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Exact Figma Header */}
        <header className="relative z-20 flex h-16 shrink-0 items-center gap-4 border-b border-border bg-background/90 px-4 md:px-8">
          <div className="relative w-full max-w-md">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (q.trim()) {
                  handleAiQuery(q);
                  setQ("");
                }
              }}
            >
              <SearchField value={q} onChange={setQ} placeholder="Search players, teams, matches…" />
            </form>

            {q && (
              <div className="absolute left-0 right-0 top-11 rounded-md border border-border bg-popover p-1 shadow-[var(--shadow-2)] z-50">
                {hits.length > 0 &&
                  hits.map((h, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        if (h.query) {
                          handleAiQuery(h.query);
                        } else {
                          go(h.p);
                        }
                        setQ("");
                      }}
                      className="flex w-full items-center justify-between rounded px-3 py-2 text-left text-[13px] hover:bg-accent transition"
                    >
                      <span className="font-semibold">{h.t}</span>
                      <span className="text-[11px] text-muted-foreground num">{h.s}</span>
                    </button>
                  ))}
                <button
                  onClick={() => {
                    handleAiQuery(q);
                    setQ("");
                  }}
                  className="flex w-full items-center justify-between rounded px-3 py-2 text-left text-[13px] hover:bg-accent text-primary transition"
                >
                  <span className="flex items-center gap-1.5 font-semibold">
                    <Sparkles size={13} /> Ask CricOps AI: &quot;{q}&quot;
                  </span>
                  <span className="text-[11px] text-muted-foreground">Press Enter</span>
                </button>
              </div>
            )}
          </div>

          <div className="ml-auto flex items-center gap-1">
            <Tip text="Notifications">
              <button
                onClick={() => handleAiQuery("What are the key recent cricket turning points?")}
                className="relative rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground transition"
                aria-label="Notifications"
              >
                <Bell size={17} />
                <span className="absolute right-2 top-2 size-1.5 rounded-full bg-primary" />
              </button>
            </Tip>

            <Tip text="Settings">
              <button
                onClick={() => go("system")}
                className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground transition"
                aria-label="Settings"
              >
                <Settings size={17} />
              </button>
            </Tip>

            <div className="ml-2 flex items-center gap-2.5 border-l border-border pl-4">
              <div className="num flex size-8 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                AS
              </div>
              <div className="hidden leading-tight md:block">
                <div className="text-[13px] font-semibold">Ananya Sharma</div>
                <div className="text-[11px] text-muted-foreground">Performance analyst</div>
              </div>
            </div>
          </div>
        </header>

        {/* Viewport */}
        <main id="main" className="scroll-quiet flex-1 overflow-y-auto">
          <div className="mx-auto max-w-[1360px] px-4 py-8 md:px-8">
            {loading ? (
              <SkeletonPage />
            ) : page === "overview" ? (
              <Overview go={go} />
            ) : page === "match" ? (
              <Match />
            ) : page === "player" ? (
              <Player />
            ) : page === "team" ? (
              <Team />
            ) : (
              <System />
            )}
          </div>
        </main>
      </div>

      {/* AI Intelligence Studio Modal (Overlay) */}
      {isAiOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="relative flex flex-col max-h-[90vh] w-full max-w-4xl rounded-xl border border-border bg-card shadow-[var(--shadow-2)] overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-border px-6 py-4 bg-secondary/50">
              <div className="flex items-center gap-2.5">
                <span className="flex size-7 items-center justify-center rounded-lg bg-primary/20 text-primary">
                  <Sparkles size={16} />
                </span>
                <div>
                  <h3 className="text-sm font-bold text-foreground">CricOps AI Intelligence Studio</h3>
                  <p className="text-[11px] text-muted-foreground">Dual-Pipeline Ground Truth & Statistical Synthesis</p>
                </div>
              </div>
              <button
                onClick={() => setIsAiOpen(false)}
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground transition"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {aiLoading ? (
                <div className="py-16 text-center space-y-3">
                  <div className="inline-block size-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                  <p className="text-sm font-medium text-foreground">Calculating deterministic statistics...</p>
                  <p className="text-xs text-muted-foreground">Querying DuckDB analytical mirror & parallel grounding verification</p>
                </div>
              ) : aiError ? (
                <div className="p-4 rounded-lg border border-destructive/40 bg-destructive/10 text-destructive text-sm">
                  {aiError}
                </div>
              ) : aiResponse ? (
                <div className="space-y-6">
                  {/* Synthesis Answer Banner */}
                  <div className="p-5 rounded-lg border border-primary/30 bg-primary/5 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="num text-[11px] uppercase tracking-wider font-bold text-primary">
                        Evidence-Grounded Synthesis
                      </span>
                      {aiResponse.provider && (
                        <Badge tone="lime">
                          {aiResponse.provider.name} · {aiResponse.provider.latency_ms}ms
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm leading-relaxed text-foreground whitespace-pre-line font-medium">
                      {aiResponse.answer}
                    </p>
                  </div>

                  {/* Computed Metric Cards */}
                  {aiResponse.metrics && aiResponse.metrics.length > 0 && (
                    <div className="space-y-2">
                      <div className="num text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
                        Deterministic Metrics
                      </div>
                      <StatCards metrics={aiResponse.metrics} />
                    </div>
                  )}

                  {/* Verification Pipeline Card */}
                  {aiResponse.verification_pipeline && (
                    <VerificationPipelineCard audit={aiResponse.verification_pipeline} />
                  )}

                  {/* Visual Chart if available */}
                  {aiResponse.chart && aiResponse.chart.series && aiResponse.chart.series.length > 0 && (
                    <ChartRenderer chartSpec={aiResponse.chart} />
                  )}

                  {/* NLP Transparency Card */}
                  {aiResponse.interpretation && (
                    <NLPTransparencyCard
                      interpretation={aiResponse.interpretation}
                      confidence={aiResponse.confidence}
                      provider={aiResponse.provider}
                    />
                  )}
                </div>
              ) : null}
            </div>

            {/* Modal Footer Quick Prompts */}
            <div className="border-t border-border px-6 py-3 bg-secondary/30 flex flex-wrap items-center justify-between gap-2">
              <div className="text-[11px] text-muted-foreground">Try asking:</div>
              <div className="flex flex-wrap gap-1.5">
                {[
                  "highest run scored by rohit",
                  "Show me Virat Kohli's IPL statistics in 2022.",
                  "Compare Virat Kohli and Rohit Sharma in ODIs",
                ].map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleAiQuery(prompt)}
                    className="text-[11px] px-2.5 py-1 rounded bg-secondary hover:bg-accent border border-border text-foreground transition"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
