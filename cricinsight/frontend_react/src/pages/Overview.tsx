import { useState } from "react";
import { ArrowRight, MapPin, Sparkles, Clock, Eye } from "lucide-react";
import { AreaChart, Area, LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { Card, SectionHead, Kpi, Badge, TeamBadge, Tabs, chartTip, axis, Bar2, cx } from "../ui";
import { MATCHES, progression, AI_INSIGHTS, TEAMS } from "../data";

export function MatchCard({ m, onOpen }: { m: (typeof MATCHES)[number]; onOpen: () => void }) {
  const row = (code: string, score: string, ov: string) => (
    <div className="flex items-center gap-3">
      <TeamBadge code={code} size={36} />
      <div className={cx("flex-1 text-sm font-semibold", m.winner !== code && "text-muted-foreground")}>{TEAMS[code].name}</div>
      <div className="text-right">
        <span className={cx("num text-lg font-bold", m.winner !== code && "text-muted-foreground")}>{score}</span>
        {ov && <span className="num ml-1.5 text-[11px] text-muted-foreground">({ov})</span>}
      </div>
    </div>
  );
  return (
    <Card pad={false} className="group flex flex-col transition hover:border-[#3A4C5F]">
      <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
        <div className="flex items-center gap-2"><Badge tone={m.fmt === "T20I" ? "lime" : m.fmt === "ODI" ? "cyan" : "warn"}>{m.fmt}</Badge><span className="num text-[11px] text-muted-foreground">{m.date}</span></div>
        <Badge tone="mute">Final</Badge>
      </div>
      <div className="space-y-3 px-4 py-4">{row(m.a, m.sa, m.oa)}{row(m.b, m.sb, m.ob)}</div>
      <div className="mt-auto border-t border-border px-4 py-3">
        <div className="text-[13px] font-semibold text-primary">{m.result}</div>
        <div className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground"><MapPin size={11} />{m.venue}</div>
        <button onClick={onOpen} className="mt-3 flex items-center gap-1.5 text-xs font-semibold text-foreground transition hover:text-primary">View analysis <ArrowRight size={13} className="transition group-hover:translate-x-0.5" /></button>
      </div>
    </Card>
  );
}

export default function Overview({ go }: { go: (p: string) => void }) {
  const [chart, setChart] = useState<"Runs" | "Wickets">("Runs");
  const [ind, setInd] = useState<"Batting" | "Bowling">("Batting");
  const bat = [["Arjun Mehta", "IND", 3412, 143.8, 41.6], ["Mitch Dawson", "AUS", 2988, 152.1, 36.8], ["Cole Hayes", "AUS", 2731, 138.4, 33.2], ["Harry Stokely", "ENG", 2655, 141.0, 38.0]] as const;
  const bowl = [["Karan Malhotra", "IND", 142, 7.4, 17.9], ["Liam Garrick", "AUS", 131, 7.9, 19.2], ["Imran Qadir", "PAK", 126, 7.2, 20.4], ["Jonas Pretorius", "RSA", 119, 8.1, 18.8]] as const;
  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="num mb-2 text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Overview · Season 2024–25</div>
          <h1 className="max-w-2xl text-[34px] font-extrabold leading-[1.1] tracking-tight md:text-[44px]">Cricket intelligence,<br /><span className="text-muted-foreground">beyond the scoreboard.</span></h1>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground"><Clock size={13} />Data refreshed 14 min ago</div>
      </header>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi label="Matches analyzed" value="4,812" delta={8.2} sub="vs last quarter" accent />
        <Kpi label="Teams covered" value="86" delta={3.6} sub="international + domestic" />
        <Kpi label="Players analyzed" value="12,406" delta={5.1} sub="with 10+ innings" />
        <Kpi label="Deliveries processed" value="2.84M" delta={11.4} sub="ball-by-ball" />
      </div>

      <div>
        <SectionHead eyebrow="Fixtures" title="Recent match analysis" sub="Latest completed matches with full ball-by-ball breakdown" right={<button onClick={() => go("match")} className="text-xs font-semibold text-primary hover:underline">All matches</button>} />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{MATCHES.map((m) => <MatchCard key={m.id} m={m} onOpen={() => go("match")} />)}</div>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <SectionHead title="Progression · IND vs AUS" sub="Cumulative by over, 2nd T20I" right={<Tabs size="sm" items={["Runs", "Wickets"] as const} value={chart} onChange={setChart} />} />
          <div className="h-64">
            <ResponsiveContainer>
              {chart === "Runs" ? (
                <AreaChart data={progression}>
                  <defs><linearGradient id="gi" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#B9F36B" stopOpacity={0.22} /><stop offset="1" stopColor="#B9F36B" stopOpacity={0} /></linearGradient></defs>
                  <CartesianGrid key="c101" stroke="#1C2937" vertical={false} />
                  <XAxis key="c102" dataKey="over" {...axis} /><YAxis key="c103" {...axis} width={32} />
                  <Tooltip key="c104" {...chartTip} />
                  <Area key="area-1" dataKey="IND" stroke="#B9F36B" strokeWidth={2} fill="url(#gi)" />
                  <Area key="area-2" dataKey="AUS" stroke="#55C9E8" strokeWidth={2} fill="none" />
                </AreaChart>
              ) : (
                <LineChart data={progression}>
                  <CartesianGrid key="c105" stroke="#1C2937" vertical={false} />
                  <XAxis key="c106" dataKey="over" {...axis} /><YAxis key="c107" {...axis} width={32} allowDecimals={false} />
                  <Tooltip key="c108" {...chartTip} />
                  <Line key="line-3" type="stepAfter" dataKey="wIND" name="IND wkts" stroke="#B9F36B" strokeWidth={2} dot={false} />
                  <Line key="line-4" type="stepAfter" dataKey="wAUS" name="AUS wkts" stroke="#55C9E8" strokeWidth={2} dot={false} />
                </LineChart>
              )}
            </ResponsiveContainer>
          </div>
          <div className="mt-2 flex gap-4 text-xs text-muted-foreground"><span className="flex items-center gap-1.5"><i className="size-2 rounded-full bg-primary" />India</span><span className="flex items-center gap-1.5"><i className="size-2 rounded-full bg-[#55C9E8]" />Australia</span></div>
        </Card>

        <Card className="relative overflow-hidden">
          <div className="mb-4 flex items-center gap-2"><span className="flex size-6 items-center justify-center rounded bg-primary/15 text-primary"><Sparkles size={13} /></span><h3 className="text-[15px] font-bold">AI Insights</h3><Badge tone="lime">Live</Badge></div>
          <div className="space-y-4">
            {AI_INSIGHTS.map((a, i) => (
              <div key={i} className={cx("border-l-2 pl-3", a.tone === "lime" ? "border-primary" : a.tone === "cyan" ? "border-[#55C9E8]" : "border-[#E5B54A]")}>
                <div className="num text-[10px] uppercase tracking-widest text-muted-foreground">{a.tag}</div>
                <div className="mt-0.5 text-[13px] font-bold leading-snug">{a.title}</div>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{a.body}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card>
          <SectionHead title="Team performance" sub="Avg 1st-innings score, last 12 months" />
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={[{ t: "IND", bat: 178, bowl: 151 }, { t: "AUS", bat: 171, bowl: 158 }, { t: "ENG", bat: 183, bowl: 166 }, { t: "RSA", bat: 165, bowl: 154 }, { t: "PAK", bat: 169, bowl: 160 }]} barGap={3}>
                <CartesianGrid key="c109" stroke="#1C2937" vertical={false} /><XAxis key="c110" dataKey="t" {...axis} /><YAxis key="c111" {...axis} width={30} domain={[120, 200]} />
                <Tooltip key="c112" {...chartTip} cursor={{ fill: "#17222E" }} />
                <Legend key="c113" iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: "#9BA9B8" }} />
                <Bar key="bar-5" dataKey="bat" name="Scored" fill="#B9F36B" radius={[2, 2, 0, 0]} /><Bar key="bar-6" dataKey="bowl" name="Conceded" fill="#3A4C5F" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="xl:col-span-2" pad={false}>
          <div className="p-5 pb-3"><SectionHead title="Leaders" sub="T20I, last 24 months" right={<Tabs size="sm" items={["Batting", "Bowling"] as const} value={ind} onChange={setInd} />} /></div>
          <table className="w-full text-[13px]">
            <thead><tr className="border-y border-border bg-background/50 text-left text-[10px] uppercase tracking-wider text-muted-foreground">
              <th className="px-5 py-2 font-medium">Player</th><th className="py-2 text-right font-medium">{ind === "Batting" ? "Runs" : "Wkts"}</th><th className="py-2 text-right font-medium">{ind === "Batting" ? "SR" : "Econ"}</th><th className="py-2 text-right font-medium">{ind === "Batting" ? "Avg" : "SR"}</th><th className="hidden w-40 px-5 py-2 sm:table-cell" /></tr></thead>
            <tbody>
              {(ind === "Batting" ? bat : bowl).map((r, i) => (
                <tr key={r[0]} className="border-b border-border/60 last:border-0 hover:bg-accent/40">
                  <td className="px-5 py-3"><div className="flex items-center gap-3"><span className="num w-4 text-muted-foreground">{i + 1}</span><TeamBadge code={r[1]} size={26} /><span className="font-semibold">{r[0]}</span></div></td>
                  <td className="num py-3 text-right font-bold">{r[2].toLocaleString()}</td><td className="num py-3 text-right">{r[3]}</td><td className="num py-3 text-right text-muted-foreground">{r[4]}</td>
                  <td className="hidden px-5 py-3 sm:table-cell"><Bar2 value={r[2]} max={ind === "Batting" ? 3600 : 150} color={ind === "Batting" ? "#B9F36B" : "#55C9E8"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <SectionHead title="Recently analyzed" sub="Pick up where you left off" />
          <ul className="divide-y divide-border/60">
            {MATCHES.slice(0, 3).map((m) => (
              <li key={m.id}><button onClick={() => go("match")} className="flex w-full items-center gap-3 py-3 text-left transition hover:opacity-80">
                <div className="flex -space-x-2"><TeamBadge code={m.a} size={28} /><TeamBadge code={m.b} size={28} /></div>
                <div className="flex-1"><div className="text-[13px] font-semibold">{TEAMS[m.a].name} vs {TEAMS[m.b].name}</div><div className="text-[11px] text-muted-foreground">{m.fmt} · {m.date}</div></div>
                <span className="num text-[11px] text-muted-foreground">Viewed {["2h", "yesterday", "3d"][m.id - 1]} ago</span>
              </button></li>
            ))}
          </ul>
        </Card>
        <Card>
          <SectionHead title="Recently viewed players" sub="Quick access to profiles" />
          <ul className="divide-y divide-border/60">
            {[["Arjun Mehta", "IND", "Top-order batter", "62 (38)"], ["Karan Malhotra", "IND", "Right-arm pace", "3/31"], ["Mitch Dawson", "AUS", "Middle-order batter", "55 (33)"]].map((p) => (
              <li key={p[0]}><button onClick={() => go("player")} className="flex w-full items-center gap-3 py-3 text-left transition hover:opacity-80">
                <TeamBadge code={p[1]} size={32} />
                <div className="flex-1"><div className="text-[13px] font-semibold">{p[0]}</div><div className="text-[11px] text-muted-foreground">{p[2]}</div></div>
                <div className="text-right"><div className="num text-[13px] font-bold">{p[3]}</div><div className="flex items-center justify-end gap-1 text-[10px] text-muted-foreground"><Eye size={10} />last match</div></div>
              </button></li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
