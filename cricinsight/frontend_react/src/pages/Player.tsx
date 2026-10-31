import { useState } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, Legend, ReferenceLine } from "recharts";
import { Card, SectionHead, Badge, TeamBadge, UnderTabs, Tabs, Select, chartTip, axis, WagonWheel, PitchMap, Bar2, Empty, Tip, cx } from "../ui";
import { PLAYER, form, trend, dist, byOpp, byVenue, byInns, zones, phases, bowlEcon, wktTypes, compareSets } from "../data";

const TABS = ["Batting", "Bowling", "Splits", "Compare"] as const;
type Tab = (typeof TABS)[number];
const PLAYERS = ["Arjun Mehta", "Karan Malhotra"];

export default function Player() {
  const [who, setWho] = useState(PLAYERS[0]);
  const isBat = who === PLAYERS[0];
  const [tab, setTab] = useState<Tab>("Batting");
  const [split, setSplit] = useState<"Opposition" | "Venue" | "Innings">("Opposition");
  const [metric, setMetric] = useState<"avg" | "sr">("avg");
  const [vs, setVs] = useState("Dawson");
  const c = PLAYER.career;
  const stats: [string, string][] = isBat
    ? [["Matches", "94"], ["Runs", c.runs.toLocaleString()], ["Average", "41.6"], ["Strike rate", "143.8"], ["High score", c.hs], ["100s / 50s", "3 / 27"], ["4s / 6s", "301 / 142"]]
    : [["Matches", "81"], ["Wickets", "142"], ["Economy", "7.42"], ["Bowl avg", "17.9"], ["Best", "5/19"], ["4w / 5w", "6 / 2"], ["Dot ball %", "46%"]];

  const rows = split === "Opposition" ? byOpp : split === "Venue" ? byVenue : byInns;
  const cmp = Object.keys(compareSets["Mehta"]).map((k) => ({ k, Mehta: compareSets["Mehta"][k], [vs]: compareSets[vs][k] }));

  return (
    <div className="space-y-6">
      <Card pad={false} className="overflow-hidden">
        <div className="flex flex-col gap-6 p-6 md:flex-row md:items-center">
          <div className="relative flex size-28 shrink-0 items-center justify-center rounded-lg border border-border bg-[#14202B]">
            <span className="num text-6xl font-extrabold text-[#1F2E3E]">{isBat ? 18 : 93}</span>
            <div className="absolute bottom-2 left-2"><TeamBadge code="IND" size={28} /></div>
          </div>
          <div className="flex-1">
            <div className="mb-1 flex flex-wrap gap-2"><Badge tone="lime">{isBat ? "Top-order batter" : "Right-arm fast"}</Badge><Badge>India</Badge><Badge tone="pos">In form</Badge></div>
            <h1 className="text-[34px] font-extrabold leading-tight tracking-tight">{who}</h1>
            <p className="text-[13px] text-muted-foreground">{isBat ? PLAYER.style : "Right-hand bat · Right-arm fast"} · Age {isBat ? 28 : 30} · {isBat ? PLAYER.born : "Chandigarh, Punjab"}</p>
          </div>
          <Select label="Player" value={who} options={PLAYERS} onChange={(v) => { setWho(v); setTab(v === PLAYERS[0] ? "Batting" : "Bowling"); }} />
        </div>
        <div className="grid grid-cols-2 gap-px border-t border-border bg-border sm:grid-cols-4 lg:grid-cols-7">
          {stats.map(([k, v], i) => (
            <div key={k} className="bg-card px-5 py-4"><div className="text-[11px] text-muted-foreground">{k}</div><div className={cx("num mt-1 text-2xl font-bold", i === 2 && "text-primary")}>{v}</div></div>
          ))}
        </div>
      </Card>

      <UnderTabs items={TABS} value={tab} onChange={setTab} />

      {tab === "Batting" && !isBat && <Empty title="Limited batting sample" body="Karan Malhotra has batted in 12 innings, below the 30-innings threshold for reliable batting analytics." />}
      {tab === "Batting" && isBat && (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <SectionHead title="Recent form" sub="Last 10 innings · newest right" right={<div className="flex gap-3 text-[11px] text-muted-foreground"><span><i className="mr-1 inline-block size-2 rounded-sm bg-primary" />50+</span><span><i className="mr-1 inline-block size-2 rounded-sm bg-[#55C9E8]" />20–49</span><span><i className="mr-1 inline-block size-2 rounded-sm bg-[#3A4C5F]" />&lt;20</span></div>} />
            <div className="h-52">
              <ResponsiveContainer><BarChart data={form}>
                <CartesianGrid key="c114" stroke="#1C2937" vertical={false} /><XAxis key="c115" dataKey="opp" {...axis} /><YAxis key="c116" {...axis} width={30} /><Tooltip key="c117" {...chartTip} cursor={{ fill: "#17222E" }} formatter={(v) => [`${v} runs`, "Score"]} />
                <ReferenceLine key="c118" y={41.6} stroke="#E5B54A" strokeDasharray="4 4" label={{ value: "Avg 41.6", fill: "#E5B54A", fontSize: 10, position: "insideTopLeft" }} />
                <Bar key="bar-7" dataKey="r" radius={[3, 3, 0, 0]}>{form.map((f) => <Cell key={f.i} fill={f.r >= 50 ? "#B9F36B" : f.r >= 20 ? "#55C9E8" : "#3A4C5F"} />)}</Bar>
              </BarChart></ResponsiveContainer>
            </div>
          </Card>
          <Card>
            <SectionHead title="Runs distribution" sub="Share of innings by score band" />
            <div className="space-y-2.5">{dist.map((d) => (
              <div key={d.b} className="flex items-center gap-3 text-xs"><span className="num w-12 text-muted-foreground">{d.b}</span><div className="flex-1"><Bar2 value={d.n} max={20} color={d.b === "100+" ? "#B9F36B" : "#55C9E8"} /></div><span className="num w-6 text-right font-semibold">{d.n}</span></div>
            ))}</div>
          </Card>

          <Card className="lg:col-span-2">
            <SectionHead title="Average and strike-rate trend" sub="By calendar year" right={<Tabs size="sm" items={["avg", "sr"] as const} value={metric} onChange={setMetric} />} />
            <div className="h-56">
              <ResponsiveContainer><LineChart data={trend}>
                <CartesianGrid key="c119" stroke="#1C2937" vertical={false} /><XAxis key="c120" dataKey="y" {...axis} /><YAxis key="c121" {...axis} width={34} domain={metric === "avg" ? [20, 55] : [115, 160]} /><Tooltip key="c122" {...chartTip} />
                <Line key="line-8" dataKey={metric} name={metric === "avg" ? "Average" : "Strike rate"} stroke={metric === "avg" ? "#B9F36B" : "#55C9E8"} strokeWidth={2.5} dot={{ r: 3, fill: "#0B1017", strokeWidth: 2 }} />
              </LineChart></ResponsiveContainer>
            </div>
          </Card>
          <Card>
            <SectionHead title="Scoring zones" sub="% of runs by region" />
            <div className="flex h-3 overflow-hidden rounded-sm">{zones.map((z, i) => <div key={z[0]} style={{ width: `${z[1]}%`, background: ["#B9F36B", "#55C9E8", "#E5B54A", "#5E7287"][i] }} />)}</div>
            <div className="mt-3 grid grid-cols-2 gap-2">{zones.map((z, i) => <div key={z[0]} className="flex items-center gap-2 text-xs"><i className="size-2 rounded-full" style={{ background: ["#B9F36B", "#55C9E8", "#E5B54A", "#5E7287"][i] }} /><span className="text-muted-foreground">{z[0]}</span><span className="num ml-auto font-bold">{z[1]}%</span></div>)}</div>
          </Card>

          <Card className="lg:col-span-1">
            <SectionHead title="Wagon wheel" sub="46 scoring shots · last 10 innings" />
            <div className="flex justify-center"><WagonWheel size={260} /></div>
            <div className="mt-3 flex justify-center gap-4 text-[11px] text-muted-foreground"><span><i className="mr-1 inline-block h-0.5 w-3 bg-primary align-middle" />Six</span><span><i className="mr-1 inline-block h-0.5 w-3 bg-[#55C9E8] align-middle" />Four</span><span><i className="mr-1 inline-block h-0.5 w-3 bg-[#6B7C8F] align-middle" />1–3</span></div>
          </Card>
          <Card className="lg:col-span-2" pad={false}>
            <div className="p-5 pb-3"><SectionHead title="By phase of innings" sub="Batting output across the three T20 phases" /></div>
            <div className="grid divide-y divide-border border-t border-border sm:grid-cols-3 sm:divide-x sm:divide-y-0">
              {phases.map((p) => (
                <div key={p.p} className="p-5"><div className="num text-[10px] uppercase tracking-widest text-muted-foreground">{p.p}</div>
                  <div className="num mt-3 text-3xl font-bold">{p.sr}</div><div className="text-[11px] text-muted-foreground">Strike rate</div>
                  <div className="mt-3"><Bar2 value={p.sr} max={190} color={p.sr > 160 ? "#B9F36B" : "#55C9E8"} /></div>
                  <div className="num mt-3 flex justify-between text-xs"><span className="text-muted-foreground">Average</span><b>{p.avg}</b></div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {tab === "Bowling" && isBat && (
        <Empty title="Part-time bowler" body="Arjun Mehta has bowled 34 overs in his career. Switch to Karan Malhotra to explore bowling analytics." />
      )}
      {tab === "Bowling" && !isBat && (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card>
            <SectionHead title="Economy by phase" sub="Runs conceded per over" />
            <div className="h-52"><ResponsiveContainer><BarChart data={bowlEcon}>
              <CartesianGrid key="c123" stroke="#1C2937" vertical={false} /><XAxis key="c124" dataKey="p" {...axis} /><YAxis key="c125" {...axis} width={26} domain={[0, 14]} /><Tooltip key="c126" {...chartTip} cursor={{ fill: "#17222E" }} />
              <ReferenceLine key="c127" y={8} stroke="#E5B54A" strokeDasharray="4 4" />
              <Bar key="bar-9" dataKey="v" name="Economy" radius={[3, 3, 0, 0]}>{bowlEcon.map((b) => <Cell key={b.p} fill={b.v > 10 ? "#D9656B" : "#55C9E8"} />)}</Bar>
            </BarChart></ResponsiveContainer></div>
          </Card>
          <Card>
            <SectionHead title="Wicket distribution" sub="How the 39 T20I wickets fell" />
            <div className="h-52"><ResponsiveContainer><BarChart data={wktTypes} layout="vertical">
              <XAxis key="c128" type="number" {...axis} /><YAxis key="c129" type="category" dataKey="n" {...axis} width={58} /><Tooltip key="c130" {...chartTip} cursor={{ fill: "#17222E" }} />
              <Bar key="bar-10" dataKey="v" name="Wickets" fill="#B9F36B" radius={[0, 3, 3, 0]} />
            </BarChart></ResponsiveContainer></div>
          </Card>
          <Card>
            <SectionHead title="Recent spells" sub="Last 5 matches" />
            <div className="divide-y divide-border/60">
              {[["AUS", "3/31", "7.75"], ["AUS", "1/29", "7.25"], ["ENG", "2/34", "8.50"], ["ENG", "0/41", "10.25"], ["RSA", "4/22", "5.50"]].map((s, i) => (
                <div key={i} className="flex items-center gap-3 py-2.5"><TeamBadge code={s[0]} size={26} /><span className="flex-1 text-[13px] font-semibold">vs {s[0]}</span><span className="num text-sm font-bold">{s[1]}</span><span className="num w-12 text-right text-xs text-muted-foreground">{s[2]}</span></div>
              ))}
            </div>
          </Card>
          <Card className="lg:col-span-3">
            <SectionHead title="Pitch map" sub="Where deliveries land · % of balls by length" />
            <PitchMap data={[{ z: "Yorker", pct: 14, w: 7 }, { z: "Full", pct: 22, w: 9 }, { z: "Good length", pct: 38, w: 16 }, { z: "Short", pct: 20, w: 6 }, { z: "Bouncer", pct: 6, w: 1 }]} />
          </Card>
        </div>
      )}

      {tab === "Splits" && (
        <Card pad={false}>
          <div className="flex flex-wrap items-center justify-between gap-3 p-5"><SectionHead title="Performance splits" sub={isBat ? "Batting returns, T20I career" : "Showing batting splits for primary role"} /><Tabs items={["Opposition", "Venue", "Innings"] as const} value={split} onChange={setSplit} /></div>
          <div className="overflow-x-auto"><table className="w-full min-w-[560px] text-[13px]">
            <thead><tr className="border-y border-border bg-background/50 text-[10px] uppercase tracking-wider text-muted-foreground"><th className="px-5 py-2 text-left font-medium">{split}</th>{["Inns", "Runs", "Avg", "SR"].map((h) => <th key={h} className="px-2 py-2 text-right font-medium">{h}</th>)}<th className="w-40 px-5" /></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r[0]} className="border-b border-border/60 last:border-0 hover:bg-accent/40">
                <td className="px-5 py-3 font-semibold">{r[0]}</td><td className="num px-2 text-right text-muted-foreground">{r[1]}</td><td className="num px-2 text-right font-bold">{r[2]}</td>
                <td className={cx("num px-2 text-right", r[3] >= 45 ? "text-[#6DBE8A]" : r[3] < 30 ? "text-[#D9656B]" : "")}>{r[3]}</td><td className="num px-2 text-right">{r[4]}</td>
                <td className="px-5"><Bar2 value={r[3]} max={60} color={r[3] >= 45 ? "#B9F36B" : r[3] < 30 ? "#D9656B" : "#55C9E8"} /></td>
              </tr>))}</tbody>
          </table></div>
        </Card>
      )}

      {tab === "Compare" && (
        <Card>
          <SectionHead title="Player comparison" sub="Arjun Mehta vs selected player · T20I, last 24 months" right={<Select label="Compare with" value={vs} options={["Dawson", "Hayes"]} onChange={setVs} />} />
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="h-72"><ResponsiveContainer><RadarChart data={cmp.map((d) => ({ ...d, Mehta: (d.Mehta as number) / (d.k === "Average" ? 0.6 : d.k === "Strike rate" ? 2 : 1), [vs]: (d[vs] as number) / (d.k === "Average" ? 0.6 : d.k === "Strike rate" ? 2 : 1) }))}>
              <PolarGrid key="c131" stroke="#263442" /><PolarAngleAxis key="c132" dataKey="k" tick={{ fill: "#9BA9B8", fontSize: 11 }} />
              <Radar key="radar-11" dataKey="Mehta" stroke="#B9F36B" fill="#B9F36B" fillOpacity={0.15} strokeWidth={2} /><Radar key="radar-12" dataKey={vs} stroke="#55C9E8" fill="#55C9E8" fillOpacity={0.1} strokeWidth={2} />
              <Legend key="c133" iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11 }} />
            </RadarChart></ResponsiveContainer></div>
            <div className="space-y-3">
              {cmp.map((d) => {
                const a = d.Mehta as number; const b = d[vs] as number; const lowerBetter = d.k === "Dot %";
                const aw = lowerBetter ? a < b : a > b;
                return (
                  <div key={d.k}><div className="mb-1 flex items-center justify-between text-xs"><span className={cx("num font-bold", aw && "text-primary")}>{a}</span><span className="text-muted-foreground">{d.k}</span><span className={cx("num font-bold", !aw && "text-[#55C9E8]")}>{b}</span></div>
                    <div className="flex gap-1"><div className="flex h-1.5 flex-1 justify-end rounded bg-secondary"><div className="rounded bg-primary" style={{ width: `${(a / (a + b)) * 100}%` }} /></div><div className="flex h-1.5 flex-1 rounded bg-secondary"><div className="rounded bg-[#55C9E8]" style={{ width: `${(b / (a + b)) * 100}%` }} /></div></div></div>
                );
              })}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
