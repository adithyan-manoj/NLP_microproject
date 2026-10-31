import { useState } from "react";
import { Download, MapPin, Calendar, Trophy, Sparkles, Link2 } from "lucide-react";
import { ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart, ReferenceLine, Cell, BarChart, Scatter } from "recharts";
import { Card, SectionHead, Badge, TeamBadge, UnderTabs, Tabs, Select, Btn, Modal, Ball, ballsFor, chartTip, axis, Bar2, cx, Tip, Empty } from "../ui";
import { TEAMS, batA, batB, bowlA, bowlB, partsA, partsB, progression, winProb, AI_INSIGHTS, overRunsA, overRunsB, wktsA, wktsB } from "../data";

const TABS = ["Summary", "Scorecard", "Partnerships", "Run rate & wickets", "Over by over", "Win probability", "AI insights"] as const;
type Tab = (typeof TABS)[number];

function BatTable({ rows, extras, total, fow }: { rows: readonly (readonly [string, string, number, number, number, number])[]; extras: string; total: string; fow: string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[620px] text-[13px]">
        <thead><tr className="border-y border-border bg-background/50 text-[10px] uppercase tracking-wider text-muted-foreground">
          <th className="px-5 py-2 text-left font-medium">Batter</th><th className="px-2 py-2 text-left font-medium">Dismissal</th>
          {["R", "B", "4s", "6s", "SR"].map((h) => <th key={h} className="px-2 py-2 text-right font-medium">{h}</th>)}<th className="w-28 px-5 py-2" />
        </tr></thead>
        <tbody>
          {rows.map((r) => {
            const sr = (r[2] / r[3]) * 100; const no = r[1] === "not out";
            return (
              <tr key={r[0]} className="border-b border-border/60 hover:bg-accent/40">
                <td className="px-5 py-3 font-bold">{r[0]}{no && <span className="ml-1 text-primary">*</span>}</td>
                <td className={cx("px-2 py-3 text-xs", no ? "font-semibold text-primary" : "text-muted-foreground")}>{r[1]}</td>
                <td className={cx("num px-2 py-3 text-right text-[15px] font-bold", r[2] >= 50 && "text-primary")}>{r[2]}</td>
                <td className="num px-2 py-3 text-right text-muted-foreground">{r[3]}</td>
                <td className="num px-2 py-3 text-right">{r[4]}</td><td className="num px-2 py-3 text-right">{r[5]}</td>
                <td className="num px-2 py-3 text-right">{sr.toFixed(1)}</td>
                <td className="px-5 py-3"><Bar2 value={sr} max={220} color={sr > 160 ? "#B9F36B" : sr > 120 ? "#55C9E8" : "#3A4C5F"} /></td>
              </tr>
            );
          })}
          <tr className="border-b border-border/60"><td className="px-5 py-2.5 text-xs text-muted-foreground">Extras</td><td colSpan={7} className="num px-2 py-2.5 text-xs text-muted-foreground">{extras}</td></tr>
          <tr className="bg-secondary/60"><td className="px-5 py-3 font-bold">Total</td><td className="px-2 text-xs text-muted-foreground">20 overs · RR {(parseInt(total) / 20).toFixed(2)}</td><td colSpan={6} className="num px-5 py-3 text-right text-lg font-extrabold">{total}</td></tr>
        </tbody>
      </table>
      <p className="border-t border-border px-5 py-3 text-xs leading-relaxed text-muted-foreground"><span className="font-semibold text-foreground">Fall of wickets · </span><span className="num">{fow}</span></p>
    </div>
  );
}

function BowlTable({ rows }: { rows: readonly (readonly [string, string, number, number, number, number])[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] text-[13px]">
        <thead><tr className="border-y border-border bg-background/50 text-[10px] uppercase tracking-wider text-muted-foreground">
          <th className="px-5 py-2 text-left font-medium">Bowler</th>{["O", "M", "R", "W", "Econ", "Dots"].map((h) => <th key={h} className="px-2 py-2 text-right font-medium">{h}</th>)}<th className="w-28 px-5" /></tr></thead>
        <tbody>
          {rows.map((r) => {
            const ec = r[3] / Number(r[1]);
            return (
              <tr key={r[0]} className="border-b border-border/60 last:border-0 hover:bg-accent/40">
                <td className="px-5 py-3 font-bold">{r[0]}</td>
                <td className="num px-2 text-right">{r[1]}</td><td className="num px-2 text-right text-muted-foreground">{r[2]}</td><td className="num px-2 text-right">{r[3]}</td>
                <td className={cx("num px-2 text-right text-[15px] font-bold", r[4] >= 3 && "text-primary")}>{r[4]}</td>
                <td className={cx("num px-2 text-right", ec < 8 ? "text-[#6DBE8A]" : ec > 10 ? "text-[#D9656B]" : "")}>{ec.toFixed(2)}</td>
                <td className="num px-2 text-right text-muted-foreground">{r[5]}</td>
                <td className="px-5"><Bar2 value={r[5]} max={12} color="#55C9E8" /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function Match() {
  const [tab, setTab] = useState<Tab>("Summary");
  const [inn, setInn] = useState<"IND" | "AUS">("IND");
  const [phase, setPhase] = useState("All overs");
  const [sel, setSel] = useState(18);
  const [exp, setExp] = useState(false);
  const [copied, setCopied] = useState(false);

  const range = phase === "Powerplay (1–6)" ? [1, 6] : phase === "Middle (7–15)" ? [7, 15] : phase === "Death (16–20)" ? [16, 20] : [1, 20];
  const overData = progression.filter((p) => p.over >= range[0] && p.over <= range[1]);
  const phaseSum = (a: number[], f: number, t: number) => a.slice(f - 1, t).reduce((x, y) => x + y, 0);

  return (
    <div className="space-y-6">
      {/* Scoreboard header */}
      <Card pad={false} className="overflow-hidden">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-border px-5 py-3 text-xs text-muted-foreground">
          <Badge tone="lime">T20I</Badge><span className="font-semibold text-foreground">Border-Gavaskar Series · 2nd T20I</span>
          <span className="flex items-center gap-1"><MapPin size={12} />Wankhede Stadium, Mumbai</span>
          <span className="flex items-center gap-1"><Calendar size={12} />12 Mar 2025 · Day/Night</span>
          <span className="ml-auto flex gap-2">
            <Btn variant="outline" className="h-8" icon={<Link2 size={13} />} onClick={() => { setCopied(true); setTimeout(() => setCopied(false), 1800); }}>{copied ? "Link copied" : "Share"}</Btn>
            <Btn className="h-8" icon={<Download size={13} />} onClick={() => setExp(true)}>Export report</Btn>
          </span>
        </div>
        <div className="grid items-center gap-6 px-5 py-6 md:grid-cols-[1fr_auto_1fr] md:px-8">
          {[{ c: "IND", s: "187/6", o: "20.0 ov", w: true }, null, { c: "AUS", s: "181/8", o: "20.0 ov", w: false }].map((t, i) =>
            t ? (
              <div key={i} className={cx("flex items-center gap-4", i === 2 && "md:flex-row-reverse md:text-right")}>
                <TeamBadge code={t.c} size={56} />
                <div>
                  <div className="flex items-center gap-2 text-sm font-semibold">{TEAMS[t.c].name}{t.w && <Trophy size={13} className="text-primary" />}</div>
                  <div className={cx("num text-[40px] font-extrabold leading-none tracking-tight", !t.w && "text-muted-foreground")}>{t.s}</div>
                  <div className="num mt-1 text-xs text-muted-foreground">{t.o} · RR {(parseInt(t.s) / 20).toFixed(2)}</div>
                </div>
              </div>
            ) : (
              <div key={i} className="text-center"><div className="num text-[11px] uppercase tracking-[0.2em] text-muted-foreground">vs</div></div>
            )
          )}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border bg-primary/[0.06] px-5 py-3">
          <span className="text-sm font-bold text-primary">India won by 6 runs</span>
          <span className="text-xs text-muted-foreground">Player of the match · <span className="font-semibold text-foreground">Arjun Mehta</span> 62 (38)</span>
        </div>
      </Card>

      <UnderTabs items={TABS} value={tab} onChange={setTab} />

      {tab === "Summary" && (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <SectionHead title="Match summary" sub="Cumulative runs by over — markers show wickets" />
            <div className="h-64">
              <ResponsiveContainer>
                <AreaChart data={progression}>
                  <CartesianGrid key="c134" stroke="#1C2937" vertical={false} /><XAxis key="c135" dataKey="over" {...axis} /><YAxis key="c136" {...axis} width={32} /><Tooltip key="c137" {...chartTip} />
                  <Area key="area-13" dataKey="IND" stroke="#B9F36B" strokeWidth={2} fill="#B9F36B" fillOpacity={0.08} />
                  <Area key="area-14" dataKey="AUS" stroke="#55C9E8" strokeWidth={2} fill="none" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
          <Card>
            <SectionHead title="Top performers" />
            <div className="space-y-4">
              {[["IND", "Arjun Mehta", "62 (38)", "3 sixes · SR 163.2"], ["IND", "Karan Malhotra", "3/31", "4 ov · Econ 7.75"], ["AUS", "Mitch Dawson", "55 (33)", "4 sixes · SR 166.7"], ["AUS", "Liam Garrick", "2/34", "Dismissed Mehta"]].map((p) => (
                <div key={p[1]} className="flex items-center gap-3"><TeamBadge code={p[0]} size={32} /><div className="flex-1"><div className="text-[13px] font-semibold">{p[1]}</div><div className="text-[11px] text-muted-foreground">{p[3]}</div></div><div className="num text-base font-bold">{p[2]}</div></div>
              ))}
            </div>
          </Card>
          <Card className="lg:col-span-3">
            <SectionHead title="Phase breakdown" sub="Runs and wickets by phase of play" />
            <div className="grid gap-px overflow-hidden rounded-md border border-border bg-border md:grid-cols-3">
              {[["Powerplay", 1, 6], ["Middle", 7, 15], ["Death", 16, 20]].map(([n, f, t]) => (
                <div key={n as string} className="bg-card p-4">
                  <div className="num mb-3 text-[10px] uppercase tracking-widest text-muted-foreground">{n} · Ov {f}–{t}</div>
                  {[["IND", overRunsA, wktsA], ["AUS", overRunsB, wktsB]].map(([c, r, w]) => (
                    <div key={c as string} className="mb-2 flex items-center gap-3 last:mb-0"><span className="num w-8 text-xs font-bold" style={{ color: TEAMS[c as string].color }}>{c as string}</span>
                      <span className="num text-lg font-bold">{phaseSum(r as number[], f as number, t as number)}/{phaseSum(w as number[], f as number, t as number)}</span>
                      <span className="num ml-auto text-xs text-muted-foreground">RR {(phaseSum(r as number[], f as number, t as number) / ((t as number) - (f as number) + 1)).toFixed(1)}</span></div>
                  ))}
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {tab === "Scorecard" && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <Tabs items={["IND", "AUS"] as const} value={inn} onChange={setInn} />
            <span className="text-xs text-muted-foreground">{inn === "IND" ? "1st innings · India batting" : "2nd innings · Australia chasing 188"}</span>
          </div>
          <Card pad={false}>
            <div className="flex items-center justify-between p-5 pb-4"><div className="flex items-center gap-3"><TeamBadge code={inn} size={32} /><h3 className="text-[15px] font-bold">{TEAMS[inn].name} innings</h3></div><span className="num text-xl font-extrabold">{inn === "IND" ? "187/6" : "181/8"}</span></div>
            <BatTable rows={inn === "IND" ? batA : batB} extras={inn === "IND" ? "9 (b 1, lb 2, w 5, nb 1)" : "5 (b 0, lb 1, w 3, nb 1)"} total={inn === "IND" ? "187/6" : "181/8"}
              fow={inn === "IND" ? "1-41 (Iyer, 4.2) · 2-99 (Mehta, 10.4) · 3-146 (Nair, 15.1) · 4-170 (Sethi, 17.4) · 5-174 (Kapoor, 18.2) · 6-176 (Bhatt, 18.5)" : "1-36 (Pryce, 4.0) · 2-87 (Hayes, 9.3) · 3-125 (Calder, 13.2) · 4-147 (Dawson, 16.1) · 5-162 (Rennick, 17.5) · 6-171 (Ashby, 18.4) · 7-174 (Fenwick, 19.1) · 8-179 (Harker, 19.5)"} />
          </Card>
          <Card pad={false}>
            <div className="p-5 pb-4"><h3 className="text-[15px] font-bold">Bowling · {TEAMS[inn === "IND" ? "AUS" : "IND"].name}</h3></div>
            <BowlTable rows={inn === "IND" ? bowlB : bowlA} />
          </Card>
        </div>
      )}

      {tab === "Partnerships" && (
        <div className="grid gap-4 lg:grid-cols-2">
          {[["IND", partsA, "#B9F36B"], ["AUS", partsB, "#55C9E8"]].map(([c, p, col]) => (
            <Card key={c as string}>
              <SectionHead title={`${TEAMS[c as string].name} partnerships`} sub="Runs per wicket stand" />
              <div className="space-y-3">
                {(p as typeof partsA).map((x, i) => (
                  <div key={i}>
                    <div className="mb-1 flex items-baseline justify-between text-xs"><span><span className="num mr-2 text-muted-foreground">{i + 1}{["st", "nd", "rd"][i] ?? "th"}</span><span className="font-semibold">{x[0]}</span></span><span className="num"><b className="text-sm">{x[1]}</b> <span className="text-muted-foreground">· RR {(x[1] / (Math.floor(x[2]) + (x[2] % 1) * 10 / 6) ).toFixed(1)}</span></span></div>
                    <div className="h-2 rounded-sm bg-secondary"><div className="h-full rounded-sm" style={{ width: `${(x[1] / 60) * 100}%`, background: col as string }} /></div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}

      {tab === "Run rate & wickets" && (
        <Card>
          <SectionHead title="Run-rate progression and wicket timeline" sub="Bars: runs per over · Line: cumulative run rate · Red markers: wickets" right={<div className="flex gap-2"><Tabs size="sm" items={["IND", "AUS"] as const} value={inn} onChange={setInn} /><Select label="Phase" value={phase} onChange={setPhase} options={["All overs", "Powerplay (1–6)", "Middle (7–15)", "Death (16–20)"]} /></div>} />
          <div className="h-80">
            <ResponsiveContainer>
              <ComposedChart data={overData.map((d) => ({ ...d, runs: inn === "IND" ? d.rA : d.rB, wk: (inn === "IND" ? d.kA : d.kB) ? (inn === "IND" ? d.rA : d.rB) + 2 : null, crr: +((inn === "IND" ? d.IND : d.AUS) / d.over).toFixed(2) }))}>
                <CartesianGrid key="c138" stroke="#1C2937" vertical={false} /><XAxis key="c139" dataKey="over" {...axis} /><YAxis key="c140" yAxisId="l" {...axis} width={28} /><YAxis key="c141" yAxisId="r" orientation="right" {...axis} width={28} domain={[0, 12]} />
                <Tooltip key="c142" {...chartTip} cursor={{ fill: "#17222E" }} />
                <Bar key="bar-15" yAxisId="l" dataKey="runs" name="Runs" radius={[2, 2, 0, 0]} fill={inn === "IND" ? "#B9F36B" : "#55C9E8"} fillOpacity={0.85} />
                <Line key="line-16" yAxisId="r" dataKey="crr" name="Run rate" stroke="#F4F7FA" strokeWidth={1.5} dot={false} />
                <Scatter key="scatter-17" yAxisId="l" dataKey="wk" name="Wicket" fill="#D9656B" shape="circle" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {progression.filter((p) => (inn === "IND" ? p.kA : p.kB)).map((p) => <Badge key={p.over} tone="neg">W · Over {p.over}</Badge>)}
          </div>
        </Card>
      )}

      {tab === "Over by over" && (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2" pad={false}>
            <div className="flex flex-wrap items-center justify-between gap-3 p-5 pb-3"><SectionHead title="Ball-by-ball" sub="Select an over — • dot, W wicket, 4 and 6 highlighted" /><Tabs size="sm" items={["IND", "AUS"] as const} value={inn} onChange={setInn} /></div>
            <div className="max-h-[520px] overflow-y-auto scroll-quiet">
              {progression.map((p) => {
                const r = inn === "IND" ? p.rA : p.rB; const k = inn === "IND" ? p.kA : p.kB;
                return (
                  <button key={p.over} onClick={() => setSel(p.over)} className={cx("flex w-full items-center gap-4 border-t border-border/60 px-5 py-2.5 text-left transition hover:bg-accent/40", sel === p.over && "bg-accent/60")}>
                    <span className="num w-14 text-xs text-muted-foreground">Over {p.over}</span>
                    <div className="flex flex-1 gap-1.5">{ballsFor(r, k, p.over).map((b, i) => <Ball key={i} v={b} />)}</div>
                    <span className="num w-14 text-right text-sm font-bold">{r}{k ? <span className="text-[#D9656B]">/{k}</span> : ""}</span>
                  </button>
                );
              })}
            </div>
          </Card>
          <Card>
            <SectionHead title={`Over ${sel} focus`} sub={TEAMS[inn].name + " batting"} />
            <div className="num text-5xl font-extrabold">{inn === "IND" ? progression[sel - 1].rA : progression[sel - 1].rB}<span className="text-lg text-muted-foreground"> runs</span></div>
            <div className="mt-4 h-40">
              <ResponsiveContainer><BarChart data={progression.map((p) => ({ o: p.over, r: inn === "IND" ? p.rA : p.rB }))}>
                <XAxis key="c143" dataKey="o" {...axis} interval={3} /><Tooltip key="c144" {...chartTip} cursor={{ fill: "#17222E" }} />
                <Bar key="bar-18" dataKey="r" radius={[2, 2, 0, 0]}>{progression.map((p) => <Cell key={p.over} fill={p.over === sel ? "#B9F36B" : "#2F4155"} />)}</Bar>
              </BarChart></ResponsiveContainer>
            </div>
            <div className="mt-3 flex gap-2 text-xs text-muted-foreground"><Badge tone="lime">{inn === "IND" ? progression[sel - 1].IND : progression[sel - 1].AUS} cum.</Badge><Badge tone="cyan">Over {sel} of 20</Badge></div>
          </Card>
        </div>
      )}

      {tab === "Win probability" && (
        <Card>
          <SectionHead title="Win probability · Australia chase" sub="Output from CricOps WP model v2.3 · trained on 3,900 T20I matches · refreshed each delivery" right={<Badge tone="pos">Model available</Badge>} />
          <div className="h-72">
            <ResponsiveContainer>
              <AreaChart data={winProb}>
                <CartesianGrid key="c145" stroke="#1C2937" vertical={false} /><XAxis key="c146" dataKey="over" {...axis} /><YAxis key="c147" {...axis} width={34} unit="%" domain={[0, 100]} />
                <ReferenceLine key="c148" y={50} stroke="#3A4C5F" strokeDasharray="4 4" />
                <Tooltip key="c149" {...chartTip} formatter={(v: number) => `${v}%`} />
                <Area key="area-19" type="monotone" dataKey="ind" name="India" stroke="#B9F36B" strokeWidth={2} fill="#B9F36B" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">Largest swing: <span className="font-semibold text-foreground">Over 18</span> (−11 pts for India after Dawson–Rennick 14-run over). Win probability is shown only where the model has full ball-by-ball coverage.</p>
        </Card>
      )}

      {tab === "AI insights" && (
        <div className="grid gap-4 md:grid-cols-3">
          {AI_INSIGHTS.map((a, i) => (
            <Card key={i}><div className="mb-3 flex items-center gap-2 text-primary"><Sparkles size={14} /><Badge tone={a.tone}>{a.tag}</Badge></div><h4 className="text-[15px] font-bold leading-snug">{a.title}</h4><p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">{a.body}</p></Card>
          ))}
          <div className="md:col-span-3"><Empty title="Ask about this match" body="Natural-language queries like “How did Dawson score against spin?” are coming to this panel." /></div>
        </div>
      )}

      <Modal open={exp} onOpenChange={setExp} title="Export match report" desc="IND vs AUS · 2nd T20I · includes scorecards and charts.">
        <div className="space-y-2">
          {["PDF report", "CSV · ball-by-ball data", "PNG · charts only"].map((o, i) => (
            <label key={o} className="flex cursor-pointer items-center gap-3 rounded-md border border-border p-3 text-[13px] font-semibold has-[:checked]:border-primary"><input type="radio" name="x" defaultChecked={i === 0} className="accent-[#B9F36B]" />{o}</label>
          ))}
        </div>
        <div className="mt-5 flex justify-end gap-2"><Btn variant="ghost" onClick={() => setExp(false)}>Cancel</Btn><Btn onClick={() => setExp(false)} icon={<Download size={14} />}>Download</Btn></div>
      </Modal>
    </div>
  );
}
