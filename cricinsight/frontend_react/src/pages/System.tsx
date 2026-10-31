import { useState } from "react";
import { Card, SectionHead, Badge, Btn, Tabs, Select, SearchField, Tip, Modal, Skeleton, Empty, ErrorState, Kpi, Ball } from "../ui";

const swatches = [["Background", "#0B1017"], ["Surface 1", "#111923"], ["Surface 2", "#17222E"], ["Border", "#263442"], ["Text", "#F4F7FA"], ["Text muted", "#9BA9B8"], ["Lime", "#B9F36B"], ["Cyan", "#55C9E8"], ["Positive", "#6DBE8A"], ["Negative", "#D9656B"], ["Warning", "#E5B54A"]];

export default function System() {
  const [t, setT] = useState("Batting");
  const [o, setO] = useState("T20I");
  const [q, setQ] = useState("");
  const [m, setM] = useState(false);
  const [err, setErr] = useState(true);
  return (
    <div className="space-y-6">
      <header><div className="num mb-2 text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Design system · v1.0</div><h1 className="text-[34px] font-extrabold tracking-tight">Components & tokens</h1><p className="mt-1 max-w-xl text-sm text-muted-foreground">One 8-point grid, two accents, tabular numerals. Lime marks emphasis and action; cyan marks the opposing series.</p></header>
      <Card>
        <SectionHead title="Colour" />
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-6 xl:grid-cols-11">{swatches.map(([n, c]) => <div key={n}><div className="h-14 rounded-md border border-border" style={{ background: c }} /><div className="mt-2 text-[11px] font-semibold">{n}</div><div className="num text-[10px] text-muted-foreground">{c}</div></div>)}</div>
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <SectionHead title="Typography" sub="Manrope · JetBrains Mono for figures" />
          <div className="space-y-3"><div className="text-[44px] font-extrabold leading-none tracking-tight">Display 44</div><div className="text-2xl font-bold">Heading 24 / Bold</div><div className="text-[15px] font-bold">Section title 15 / Bold</div><div className="text-[13px] text-muted-foreground">Body 13 / Regular — secondary copy and table cells.</div><div className="num text-3xl font-bold">187/6 <span className="text-sm font-normal text-muted-foreground">tabular · 143.8 SR</span></div></div>
        </Card>
        <Card>
          <SectionHead title="Spacing · radius · elevation" />
          <div className="flex items-end gap-3">{[8, 16, 24, 32, 40, 48].map((s) => <div key={s} className="text-center"><div className="bg-primary/70" style={{ width: s, height: s }} /><div className="num mt-1 text-[10px] text-muted-foreground">{s}</div></div>)}</div>
          <div className="mt-5 grid grid-cols-3 gap-3 text-center text-[11px] text-muted-foreground">{[["4px", "rounded-sm"], ["8px", "rounded-lg"], ["Shadow-2", "rounded-lg shadow-[var(--shadow-2)]"]].map(([a, b]) => <div key={a} className={`border border-border bg-secondary py-5 ${b}`}>{a}</div>)}</div>
          <div className="num mt-4 text-[11px] text-muted-foreground">Breakpoints · sm 640 · md 768 · lg 1024 · xl 1280</div>
        </Card>
      </div>
      <Card>
        <SectionHead title="Controls" sub="Default, hover, focus and selected states" />
        <div className="flex flex-wrap items-center gap-3">
          <Btn>Primary</Btn><Btn variant="outline">Secondary</Btn><Btn variant="ghost">Ghost</Btn>
          <Tabs items={["Batting", "Bowling"] as const} value={t as "Batting"} onChange={setT} />
          <Select label="Format" value={o} onChange={setO} options={["T20I", "ODI", "Test"]} />
          <SearchField value={q} onChange={setQ} placeholder="Search field" className="w-48" />
          <Tip text="Strike rate = runs per 100 balls"><Badge tone="cyan">Hover me</Badge></Tip>
          <Badge tone="lime">Lime</Badge><Badge tone="pos">Positive</Badge><Badge tone="neg">Negative</Badge><Badge tone="warn">Warning</Badge>
          <Btn variant="outline" onClick={() => setM(true)}>Open modal</Btn>
          <div className="flex gap-1.5">{["1", "0", "4", "6", "W"].map((x, i) => <Ball key={i} v={x} />)}</div>
        </div>
      </Card>
      <div className="grid gap-4 lg:grid-cols-3">
        <Card><SectionHead title="Loading" /><div className="space-y-3"><Skeleton className="h-6 w-2/3" /><Skeleton className="h-24" /><Skeleton className="h-4 w-1/2" /></div></Card>
        <Card><SectionHead title="Empty" /><Empty title="No matches found" body="Try widening the date range or removing a filter." action={<Btn variant="outline" className="h-8">Clear filters</Btn>} /></Card>
        <Card><SectionHead title="Error" />{err ? <ErrorState title="Couldn't load ball-by-ball data" body="The feed timed out. Your filters are saved." onRetry={() => setErr(false)} /> : <Kpi label="Recovered" value="OK" sub="Retry succeeded" />}{!err && <Btn variant="ghost" className="mt-3" onClick={() => setErr(true)}>Reset demo</Btn>}</Card>
      </div>
      <Modal open={m} onOpenChange={setM} title="Modal dialog" desc="Focus-trapped, closes on Escape."><div className="flex justify-end"><Btn onClick={() => setM(false)}>Done</Btn></div></Modal>
    </div>
  );
}
