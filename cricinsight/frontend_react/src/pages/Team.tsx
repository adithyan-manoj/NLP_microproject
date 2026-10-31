import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, PieChart, Pie, Cell } from "recharts";
import { Card, SectionHead, Kpi, Badge, TeamBadge, Select, Tabs, FormChips, chartTip, axis, cx, Tip } from "../ui";
import { TEAMS, teamBase, teamTrend, teamOpp, teamVenue } from "../data";

const RIVALS: Record<string, { w: number; bat: number; bowl: number; rr: number; pp: number; death: number }> = {
  AUS: { w: 62, bat: 171, bowl: 158, rr: 8.5, pp: 8.4, death: 10.9 },
  ENG: { w: 58, bat: 183, bowl: 166, rr: 9.1, pp: 9.0, death: 11.2 },
  RSA: { w: 55, bat: 165, bowl: 154, rr: 8.2, pp: 7.8, death: 10.4 },
};

function WL({ w, l, nr }: { w: number; l: number; nr: number }) {
  const t = w + l + nr || 1;
  return (
    <div className="flex h-2 overflow-hidden rounded-sm bg-secondary">
      <div className="bg-[#6DBE8A]" style={{ width: `${(w / t) * 100}%` }} /><div className="bg-[#D9656B]" style={{ width: `${(l / t) * 100}%` }} /><div className="bg-[#5E7287]" style={{ width: `${(nr / t) * 100}%` }} />
    </div>
  );
}

export default function Team() {
  const [fmt, setFmt] = useState<keyof typeof teamBase>("T20I");
  const [period, setPeriod] = useState("All time");
  const [venue, setVenue] = useState("All venues");
  const [rival, setRival] = useState("AUS");
  const [tab, setTab] = useState<"Opposition" | "Venue">("Opposition");

  const b = teamBase[fmt];
  const pf = period === "Last 12 months" ? 0.18 : period === "Last 3 years" ? 0.55 : 1;
  const vf = venue === "Home" ? 0.42 : venue === "Away" ? 0.38 : venue === "Neutral" ? 0.2 : 1;
  const boost = venue === "Home" ? 8 : venue === "Away" ? -6 : 0;
  const p = Math.max(4, Math.round(b.p * pf * vf));
  const nrN = Math.round(b.nr * pf * vf);
  const winPct = Math.min(95, Math.round((b.w / b.p) * 100 + boost + (period === "Last 12 months" ? 5 : 0)));
  const w = Math.round(((p - nrN) * winPct) / 100);
  const l = p - nrN - w;
  const r = RIVALS[rival];

  const compare: [string, number, number, boolean][] = [
    ["Win %", winPct, r.w, true], ["Avg 1st-inns score", b.avgS, r.bat, true], ["Avg runs conceded", 151, r.bowl, false], ["Run rate", +(b.rpo + 1).toFixed(1), r.rr, true], ["Powerplay RR", 8.8, r.pp, true], ["Death econ.", 10.2, r.death, false],
  ];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex items-center gap-4">
          <TeamBadge code="IND" size={64} />
          <div>
            <div className="num text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Team analytics · ICC Full Member</div>
            <h1 className="text-[34px] font-extrabold leading-tight tracking-tight">India</h1>
            <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground"><span>Captain <b className="text-foreground">Kabir Nair</b></span><span>Coach <b className="text-foreground">R. Deshpande</b></span><Badge tone="lime">Rank #1 {fmt}</Badge></div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Tabs items={["T20I", "ODI", "Test"] as const} value={fmt} onChange={setFmt} />
          <Select label="Period" value={period} onChange={setPeriod} options={["All time", "Last 3 years", "Last 12 months"]} />
          <Select label="Venue" value={venue} onChange={setVenue} options={["All venues", "Home", "Away", "Neutral"]} />
        </div>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr_1fr_1fr]">
        <Card className="flex items-center gap-5">
          <div className="relative size-28 shrink-0">
            <ResponsiveContainer><PieChart><Pie key="c150" data={[{ v: w }, { v: l }, { v: nrN }]} dataKey="v" innerRadius={38} outerRadius={52} startAngle={90} endAngle={-270} stroke="none" paddingAngle={2}>
              {["#6DBE8A", "#D9656B", "#5E7287"].map((c) => <Cell key={c} fill={c} />)}</Pie></PieChart></ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center"><span className="num text-2xl font-extrabold">{winPct}%</span><span className="text-[10px] text-muted-foreground">win rate</span></div>
          </div>
          <div className="flex-1 space-y-2 text-xs">
            {[["Won", w, "#6DBE8A"], ["Lost", l, "#D9656B"], ["NR / Draw", nrN, "#5E7287"]].map(([n, v, c]) => <div key={n as string} className="flex items-center gap-2"><i className="size-2 rounded-full" style={{ background: c as string }} /><span className="text-muted-foreground">{n}</span><span className="num ml-auto font-bold">{v}</span></div>)}
            <div className="num border-t border-border pt-2 text-muted-foreground">Played <b className="text-foreground">{p}</b></div>
          </div>
        </Card>
        <Kpi label="Avg 1st-innings score" value={String(Math.round(b.avgS))} delta={4.1} sub="batting first" />
        <Kpi label="Avg chase target" value={String(b.avgC)} delta={-2.3} sub="conceded" />
        <Card><div className="text-xs font-medium text-muted-foreground">Form guide · last 10</div><div className="mt-3"><FormChips s={b.form} /></div><div className="mt-3 text-xs text-muted-foreground">Oldest → newest. Current streak <b className="text-[#6DBE8A]">3 W</b></div></Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <SectionHead title="Scoring trends" sub="Average runs scored vs conceded per innings, by month" />
          <div className="h-64"><ResponsiveContainer><LineChart data={teamTrend}>
            <CartesianGrid key="c151" stroke="#1C2937" vertical={false} /><XAxis key="c152" dataKey="m" {...axis} /><YAxis key="c153" {...axis} width={32} domain={[120, 200]} /><Tooltip key="c154" {...chartTip} />
            <Legend key="c155" iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: "#9BA9B8" }} />
            <Line key="line-20" dataKey="bat" name="Scored" stroke="#B9F36B" strokeWidth={2.5} dot={false} /><Line key="line-21" dataKey="bowl" name="Conceded" stroke="#55C9E8" strokeWidth={2.5} dot={false} />
          </LineChart></ResponsiveContainer></div>
        </Card>
        <Card pad={false}>
          <div className="p-5 pb-3"><SectionHead title="Batting & bowling" sub="Team-level indicators" /></div>
          {[["Batting", [["Run rate", b.rpo.toFixed(2)], ["Boundary %", "58.2%"], ["Powerplay RR", "8.84"], ["Dot-ball %", "31.4%"]]], ["Bowling", [["Economy", (b.rpo - 0.4).toFixed(2)], ["Bowling SR", "16.8"], ["Death econ.", "10.20"], ["Wkts / match", "7.4"]]]].map(([h, rows]) => (
            <div key={h as string} className="border-t border-border"><div className="num bg-background/50 px-5 py-1.5 text-[10px] uppercase tracking-widest text-muted-foreground">{h as string}</div>
              {(rows as string[][]).map((x) => <div key={x[0]} className="flex justify-between border-t border-border/60 px-5 py-2.5 text-[13px] first:border-0"><span className="text-muted-foreground">{x[0]}</span><span className="num font-bold">{x[1]}</span></div>)}</div>
          ))}
        </Card>
      </div>

      <Card>
        <SectionHead title="Team comparison" sub="India vs selected opponent · filters applied" right={<Select label="vs" value={rival} onChange={setRival} options={["AUS", "ENG", "RSA"]} />} />
        <div className="mb-4 flex items-center justify-between"><div className="flex items-center gap-2"><TeamBadge code="IND" size={28} /><b className="text-sm">India</b></div><div className="flex items-center gap-2"><b className="text-sm">{TEAMS[rival].name}</b><TeamBadge code={rival} size={28} /></div></div>
        <div className="space-y-4">
          {compare.map(([k, a, bb, hi]) => {
            const aw = hi ? a >= bb : a <= bb;
            return (
              <div key={k}><div className="mb-1.5 flex items-center justify-between text-xs"><span className={cx("num text-sm font-bold", aw && "text-primary")}>{a}</span><span className="text-muted-foreground">{k}</span><span className={cx("num text-sm font-bold", !aw && "text-[#55C9E8]")}>{bb}</span></div>
                <div className="flex gap-1"><div className="flex h-2 flex-1 justify-end rounded-sm bg-secondary"><div className={cx("rounded-sm", aw ? "bg-primary" : "bg-[#3A4C5F]")} style={{ width: `${(a / (a + bb)) * 100}%` }} /></div><div className="flex h-2 flex-1 rounded-sm bg-secondary"><div className={cx("rounded-sm", !aw ? "bg-[#55C9E8]" : "bg-[#3A4C5F]")} style={{ width: `${(bb / (a + bb)) * 100}%` }} /></div></div></div>
            );
          })}
        </div>
      </Card>

      <Card pad={false}>
        <div className="flex flex-wrap items-center justify-between gap-3 p-5"><SectionHead title="Performance splits" sub="Won – lost record with win percentage" /><Tabs items={["Opposition", "Venue"] as const} value={tab} onChange={setTab} /></div>
        <div className="overflow-x-auto"><table className="w-full min-w-[560px] text-[13px]">
          <thead><tr className="border-y border-border bg-background/50 text-[10px] uppercase tracking-wider text-muted-foreground"><th className="px-5 py-2 text-left font-medium">{tab}</th>{["P", "W", "L", "Win %"].map((h) => <th key={h} className="px-2 py-2 text-right font-medium">{h}</th>)}<th className="w-48 px-5" /></tr></thead>
          <tbody>{(tab === "Opposition" ? teamOpp : teamVenue).map((r) => (
            <tr key={r[0]} className="border-b border-border/60 last:border-0 hover:bg-accent/40">
              <td className="px-5 py-3 font-semibold">{r[0]}</td><td className="num px-2 text-right text-muted-foreground">{r[1]}</td><td className="num px-2 text-right text-[#6DBE8A]">{r[2]}</td><td className="num px-2 text-right text-[#D9656B]">{r[3]}</td>
              <td className="num px-2 text-right font-bold">{r[4]}%</td><td className="px-5"><WL w={r[2]} l={r[3]} nr={0} /></td>
            </tr>))}</tbody>
        </table></div>
      </Card>
    </div>
  );
}
