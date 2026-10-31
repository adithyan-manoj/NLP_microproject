import { ReactNode, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X, ChevronDown, Search, AlertTriangle, Inbox, TrendingUp, TrendingDown, Check } from "lucide-react";
import { TEAMS, shots } from "./data";

export const cx = (...a: (string | false | undefined | null)[]) => a.filter(Boolean).join(" ");

/* ---------- Brand ---------- */
export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <svg width="30" height="30" viewBox="0 0 32 32" fill="none" aria-hidden>
        <rect x="0.5" y="0.5" width="31" height="31" rx="7" fill="#111923" stroke="#263442" />
        {/* stumps */}
        <path d="M11 9v14M16 9v14M21 9v14" stroke="#F4F7FA" strokeWidth="1.6" strokeLinecap="round" />
        {/* bails */}
        <path d="M10.4 8.2h5M16.6 8.2h5" stroke="#B9F36B" strokeWidth="1.6" strokeLinecap="round" />
        {/* trajectory */}
        <path d="M3 25c6 1 13-3 26-14" stroke="#55C9E8" strokeWidth="1.2" strokeDasharray="1.5 2.5" strokeLinecap="round" />
        <circle cx="26.5" cy="13" r="2.4" fill="#B9F36B" />
      </svg>
      {!compact && (
        <div className="leading-none">
          <span className="text-[19px] font-extrabold tracking-tight">Cric<span className="text-primary">Ops</span></span>
          <div className="num mt-1 text-[9px] uppercase tracking-[0.22em] text-muted-foreground">Intelligence</div>
        </div>
      )}
    </div>
  );
}

export function TeamBadge({ code, size = 40 }: { code: string; size?: number }) {
  const t = TEAMS[code];
  return (
    <div
      className="num flex shrink-0 items-center justify-center rounded-md border font-bold"
      style={{ width: size, height: size, background: t.color + "1F", borderColor: t.color + "66", color: t.color, fontSize: size * 0.3 }}
      title={t.name}
    >
      {code}
    </div>
  );
}

/* ---------- Primitives ---------- */
export function Card({ children, className, pad = true }: { children: ReactNode; className?: string; pad?: boolean }) {
  return <section className={cx("rounded-lg border border-border bg-card shadow-[var(--shadow-1)]", pad && "p-5", className)}>{children}</section>;
}

export function SectionHead({ title, sub, right, eyebrow }: { title: string; sub?: string; right?: ReactNode; eyebrow?: string }) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        {eyebrow && <div className="num mb-1 text-[10px] uppercase tracking-[0.18em] text-primary">{eyebrow}</div>}
        <h3 className="text-[15px] font-bold tracking-tight">{title}</h3>
        {sub && <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>}
      </div>
      {right}
    </div>
  );
}

const tones: Record<string, string> = {
  lime: "bg-primary/10 text-primary border-primary/25",
  cyan: "bg-[#55C9E8]/10 text-[#55C9E8] border-[#55C9E8]/25",
  pos: "bg-[#6DBE8A]/10 text-[#6DBE8A] border-[#6DBE8A]/25",
  neg: "bg-[#D9656B]/10 text-[#D9656B] border-[#D9656B]/25",
  warn: "bg-[#E5B54A]/10 text-[#E5B54A] border-[#E5B54A]/25",
  mute: "bg-secondary text-muted-foreground border-border",
};
export function Badge({ children, tone = "mute" }: { children: ReactNode; tone?: keyof typeof tones | string }) {
  return <span className={cx("num inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider", tones[tone])}>{children}</span>;
}

export function Btn({ children, variant = "primary", onClick, className, icon }: { children: ReactNode; variant?: "primary" | "ghost" | "outline"; onClick?: () => void; className?: string; icon?: ReactNode }) {
  const v = {
    primary: "bg-primary text-primary-foreground hover:brightness-110 active:brightness-95",
    outline: "border border-border bg-secondary text-foreground hover:border-[#3A4C5F]",
    ghost: "text-muted-foreground hover:bg-secondary hover:text-foreground",
  }[variant];
  return (
    <button onClick={onClick} className={cx("inline-flex h-9 items-center justify-center gap-2 rounded-md px-3.5 text-[13px] font-semibold transition focus-visible:outline-2 focus-visible:outline-ring", v, className)}>
      {icon}{children}
    </button>
  );
}

export function Tabs<T extends string>({ items, value, onChange, size = "md" }: { items: readonly T[]; value: T; onChange: (v: T) => void; size?: "sm" | "md" }) {
  return (
    <div role="tablist" className="scroll-quiet flex max-w-full gap-1 overflow-x-auto rounded-md border border-border bg-background p-0.5">
      {items.map((t) => (
        <button
          key={t}
          role="tab"
          aria-selected={value === t}
          onClick={() => onChange(t)}
          className={cx("whitespace-nowrap rounded px-3 font-semibold transition", size === "sm" ? "h-7 text-xs" : "h-8 text-[13px]", value === t ? "bg-accent text-foreground shadow-[inset_0_-2px_0_var(--lime)]" : "text-muted-foreground hover:text-foreground")}
        >
          {t}
        </button>
      ))}
    </div>
  );
}

export function UnderTabs<T extends string>({ items, value, onChange }: { items: readonly T[]; value: T; onChange: (v: T) => void }) {
  return (
    <div role="tablist" className="scroll-quiet flex gap-6 overflow-x-auto border-b border-border">
      {items.map((t) => (
        <button key={t} role="tab" aria-selected={value === t} onClick={() => onChange(t)}
          className={cx("-mb-px whitespace-nowrap border-b-2 pb-3 text-[13px] font-semibold transition", value === t ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground")}>
          {t}
        </button>
      ))}
    </div>
  );
}

export function Select({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} onBlur={() => setTimeout(() => setOpen(false), 120)} className="flex h-9 items-center gap-2 rounded-md border border-border bg-background px-3 text-[13px] transition hover:border-[#3A4C5F]" aria-haspopup="listbox" aria-expanded={open}>
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold">{value}</span>
        <ChevronDown size={14} className={cx("text-muted-foreground transition", open && "rotate-180")} />
      </button>
      {open && (
        <ul role="listbox" className="absolute left-0 top-10 z-30 min-w-full rounded-md border border-border bg-popover p-1 shadow-[var(--shadow-2)]">
          {options.map((o) => (
            <li key={o}>
              <button role="option" aria-selected={o === value} onMouseDown={() => { onChange(o); setOpen(false); }} className="flex w-full items-center justify-between gap-4 whitespace-nowrap rounded px-2.5 py-1.5 text-left text-[13px] hover:bg-accent">
                {o}{o === value && <Check size={13} className="text-primary" />}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function SearchField({ value, onChange, placeholder, className }: { value: string; onChange: (v: string) => void; placeholder: string; className?: string }) {
  return (
    <label className={cx("flex h-9 items-center gap-2 rounded-md border border-border bg-background px-3 transition focus-within:border-ring", className)}>
      <Search size={15} className="text-muted-foreground" />
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="w-full bg-transparent text-[13px] outline-none placeholder:text-muted-foreground" />
    </label>
  );
}

export function Tip({ text, children }: { text: string; children: ReactNode }) {
  return (
    <span className="group relative inline-flex">
      {children}
      <span role="tooltip" className="pointer-events-none absolute bottom-full left-1/2 z-40 mb-2 w-max max-w-[220px] -translate-x-1/2 rounded border border-border bg-popover px-2 py-1 text-[11px] font-medium opacity-0 shadow-[var(--shadow-2)] transition group-hover:opacity-100">{text}</span>
    </span>
  );
}

export function Modal({ open, onOpenChange, title, desc, children }: { open: boolean; onOpenChange: (o: boolean) => void; title: string; desc: string; children: ReactNode }) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/60" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[92vw] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-card p-6 shadow-[var(--shadow-2)]">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="text-lg font-bold">{title}</Dialog.Title>
              <Dialog.Description className="mt-1 text-[13px] text-muted-foreground">{desc}</Dialog.Description>
            </div>
            <Dialog.Close className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground" aria-label="Close"><X size={16} /></Dialog.Close>
          </div>
          <div className="mt-5">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export function Kpi({ label, value, delta, sub, accent }: { label: string; value: string; delta?: number; sub?: string; accent?: boolean }) {
  return (
    <Card className="relative overflow-hidden">
      {accent && <span className="absolute inset-y-0 left-0 w-0.5 bg-primary" />}
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      <div className="num mt-2 text-[28px] font-bold leading-none tracking-tight">{value}</div>
      <div className="mt-3 flex items-center gap-2 text-xs">
        {delta !== undefined && (
          <span className={cx("num inline-flex items-center gap-1 font-medium", delta >= 0 ? "text-[#6DBE8A]" : "text-[#D9656B]")}>
            {delta >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}{Math.abs(delta)}%
          </span>
        )}
        {sub && <span className="text-muted-foreground">{sub}</span>}
      </div>
    </Card>
  );
}

export function Skeleton({ className }: { className?: string }) { return <div className={cx("skel rounded", className)} />; }
export function SkeletonPage() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading">
      <Skeleton className="h-10 w-2/3" />
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
      <div className="grid gap-4 lg:grid-cols-3"><Skeleton className="h-72 lg:col-span-2" /><Skeleton className="h-72" /></div>
    </div>
  );
}
export function Empty({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center rounded-lg border border-dashed border-border px-6 py-10 text-center">
      <div className="mb-3 flex size-10 items-center justify-center rounded-md bg-secondary text-muted-foreground"><Inbox size={18} /></div>
      <div className="text-sm font-bold">{title}</div>
      <p className="mt-1 max-w-xs text-xs text-muted-foreground">{body}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
export function ErrorState({ title, body, onRetry }: { title: string; body: string; onRetry?: () => void }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-[#D9656B]/30 bg-[#D9656B]/5 p-4">
      <AlertTriangle size={18} className="mt-0.5 shrink-0 text-[#D9656B]" />
      <div className="flex-1"><div className="text-sm font-bold">{title}</div><p className="mt-0.5 text-xs text-muted-foreground">{body}</p></div>
      {onRetry && <Btn variant="outline" onClick={onRetry} className="h-8">Retry</Btn>}
    </div>
  );
}

/* ---------- Cricket visuals ---------- */
export function Ball({ v }: { v: string | number }) {
  const s = String(v);
  const style =
    s === "W" ? "bg-[#D9656B] border-[#D9656B] text-white"
    : s === "6" ? "bg-primary border-primary text-primary-foreground"
    : s === "4" ? "bg-[#55C9E8]/15 border-[#55C9E8] text-[#55C9E8]"
    : s === "0" ? "border-border text-muted-foreground"
    : "border-[#3A4C5F] text-foreground";
  return <span className={cx("num flex size-8 items-center justify-center rounded-full border text-[12px] font-bold", style)}>{s === "0" ? "•" : s}</span>;
}

export function ballsFor(runs: number, wk: number, seed: number): string[] {
  const slots = wk ? 5 : 6;
  const b = Array(slots).fill(0);
  const pat = [1, 4, 0, 2, 6, 1, 0, 4, 1, 2];
  let left = runs;
  for (let n = 0; n < slots && left > 0; n++) { const v = Math.min(pat[(seed + n * 3) % 10], left); b[n] = v; left -= v; }
  let g = 0;
  while (left > 0 && g++ < 60) { const n = g % slots; if (b[n] < 4) { b[n]++; left--; } }
  const out = b.map(String);
  if (wk) out.splice((seed * 2 + 2) % 6, 0, "W");
  return out;
}

export function FormChips({ s }: { s: string }) {
  const c: Record<string, string> = { W: "bg-[#6DBE8A]/15 text-[#6DBE8A] border-[#6DBE8A]/40", L: "bg-[#D9656B]/15 text-[#D9656B] border-[#D9656B]/40", D: "bg-[#E5B54A]/15 text-[#E5B54A] border-[#E5B54A]/40" };
  return <div className="flex gap-1">{s.split("").map((x, i) => <span key={i} className={cx("num flex size-6 items-center justify-center rounded border text-[11px] font-bold", c[x])}>{x}</span>)}</div>;
}

export function WagonWheel({ size = 280 }: { size?: number }) {
  const R = 130; const c = 150;
  const col = (r: number) => (r === 6 ? "#B9F36B" : r === 4 ? "#55C9E8" : "#6B7C8F");
  return (
    <svg viewBox="0 0 300 300" width={size} height={size} className="max-w-full" role="img" aria-label="Wagon wheel of scoring shots">
      <defs><radialGradient id="grass" cx="50%" cy="50%" r="50%"><stop offset="0" stopColor="#14202B" /><stop offset="1" stopColor="#0F1822" /></radialGradient></defs>
      <circle cx={c} cy={c} r={R + 8} fill="url(#grass)" stroke="#263442" strokeWidth="1.5" />
      <circle cx={c} cy={c} r={R * 0.52} fill="none" stroke="#2A3B4C" strokeDasharray="3 4" />
      {[0, 45, 90, 135].map((a) => <line key={a} x1={c} y1={c} x2={c + Math.cos((a * Math.PI) / 180) * (R + 8)} y2={c + Math.sin((a * Math.PI) / 180) * (R + 8)} stroke="#1C2937" />)}
      {[45, 90, 135, 180, 225, 270, 315, 360].map((a) => <line key={a} x1={c} y1={c} x2={c + Math.cos((a * Math.PI) / 180) * (R + 8)} y2={c + Math.sin((a * Math.PI) / 180) * (R + 8)} stroke="#1C2937" />)}
      <rect x={c - 5} y={c - 18} width="10" height="36" rx="2" fill="#2A3B4C" />
      {shots.map((s, i) => {
        const rad = ((s.a - 90) * Math.PI) / 180;
        const len = s.runs >= 4 ? (s.runs === 6 ? R + 4 : R) : s.r * R;
        return <line key={i} x1={c} y1={c} x2={c + Math.cos(rad) * len} y2={c + Math.sin(rad) * len} stroke={col(s.runs)} strokeWidth={s.runs >= 4 ? 1.6 : 1} opacity={s.runs >= 4 ? 0.95 : 0.55} strokeLinecap="round" />;
      })}
      <text x={c} y="12" textAnchor="middle" className="num" fill="#9BA9B8" fontSize="9">STRAIGHT</text>
      <text x="10" y={c + 3} fill="#9BA9B8" fontSize="9" className="num">OFF</text>
      <text x="290" y={c + 3} textAnchor="end" fill="#9BA9B8" fontSize="9" className="num">LEG</text>
    </svg>
  );
}

export function PitchMap({ data }: { data: { z: string; pct: number; w: number }[] }) {
  const max = Math.max(...data.map((d) => d.pct));
  return (
    <div className="flex gap-4">
      <div className="relative w-24 shrink-0 overflow-hidden rounded-md border border-border bg-[#14202B]">
        <div className="absolute inset-y-0 left-1/2 w-12 -translate-x-1/2 bg-[#1D2C3B]" />
        {data.map((d, i) => (
          <div key={d.z} className="relative flex h-[52px] items-center justify-center border-b border-dashed border-[#2A3B4C] last:border-0">
            <span className="rounded-full bg-primary/80" style={{ width: 10 + (d.pct / max) * 24, height: 10 + (d.pct / max) * 24, opacity: 0.35 + (d.pct / max) * 0.65 }} />
            <span className="sr-only">{i}</span>
          </div>
        ))}
      </div>
      <div className="flex-1 space-y-0">
        {data.map((d) => (
          <div key={d.z} className="flex h-[52px] flex-col justify-center border-b border-border/60 last:border-0">
            <div className="flex justify-between text-xs"><span className="font-semibold">{d.z}</span><span className="num text-muted-foreground">{d.pct}% · {d.w} wkts</span></div>
            <div className="mt-1.5 h-1 rounded bg-secondary"><div className="h-full rounded bg-primary" style={{ width: `${(d.pct / max) * 100}%` }} /></div>
          </div>
        ))}
      </div>
    </div>
  );
}

export const chartTip = { contentStyle: { background: "#17222E", border: "1px solid #263442", borderRadius: 6, fontSize: 12, color: "#F4F7FA" }, labelStyle: { color: "#9BA9B8" }, cursor: { stroke: "#3A4C5F" } };
export const axis = { stroke: "#263442", tick: { fill: "#9BA9B8", fontSize: 11 }, tickLine: false } as const;

export function Bar2({ value, max, color = "var(--lime)" }: { value: number; max: number; color?: string }) {
  return <div className="h-1.5 w-full min-w-[56px] rounded bg-secondary"><div className="h-full rounded" style={{ width: `${Math.min(100, (value / max) * 100)}%`, background: color }} /></div>;
}
