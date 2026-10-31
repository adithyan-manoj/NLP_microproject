export type Team = { code: string; name: string; color: string };
export const TEAMS: Record<string, Team> = {
  IND: { code: "IND", name: "India", color: "#3B82C4" },
  AUS: { code: "AUS", name: "Australia", color: "#E5B54A" },
  ENG: { code: "ENG", name: "England", color: "#C2506B" },
  RSA: { code: "RSA", name: "South Africa", color: "#4DAA7A" },
  NZL: { code: "NZL", name: "New Zealand", color: "#8C9BAD" },
  PAK: { code: "PAK", name: "Pakistan", color: "#2F9E6B" },
};

export const MATCHES = [
  { id: 1, a: "IND", b: "AUS", fmt: "T20I", venue: "Wankhede Stadium, Mumbai", date: "12 Mar 2025", sa: "187/6", sb: "181/8", oa: "20.0", ob: "20.0", result: "India won by 6 runs", winner: "IND" },
  { id: 2, a: "ENG", b: "RSA", fmt: "ODI", venue: "Lord's, London", date: "09 Mar 2025", sa: "301/7", sb: "296/9", oa: "50.0", ob: "50.0", result: "England won by 5 runs", winner: "ENG" },
  { id: 3, a: "NZL", b: "PAK", fmt: "T20I", venue: "Eden Park, Auckland", date: "06 Mar 2025", sa: "164/9", sb: "165/4", oa: "20.0", ob: "18.3", result: "Pakistan won by 6 wickets", winner: "PAK" },
  { id: 4, a: "AUS", b: "ENG", fmt: "Test", venue: "MCG, Melbourne", date: "02 Mar 2025", sa: "412 & 188/4d", sb: "331 & 201", oa: "", ob: "", result: "Australia won by 68 runs", winner: "AUS" },
];

export const overRunsA = [6,9,11,8,7,12,9,6,10,8,7,13,9,6,11,10,9,12,11,13];
export const overRunsB = [7,8,6,9,10,8,9,7,8,6,9,11,8,10,7,8,12,13,11,14];
export const wktsA = [0,1,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,1,0,0];
export const wktsB = [0,0,1,0,0,1,0,1,0,0,0,0,1,0,1,0,1,0,1,1];
const cum = (a: number[]) => a.reduce<number[]>((acc, v) => [...acc, (acc[acc.length - 1] ?? 0) + v], []);
export const progression = Array.from({ length: 20 }, (_, i) => ({
  over: i + 1,
  IND: cum(overRunsA)[i], AUS: cum(overRunsB)[i],
  wIND: cum(wktsA)[i], wAUS: cum(wktsB)[i],
  rA: overRunsA[i], rB: overRunsB[i], kA: wktsA[i], kB: wktsB[i],
}));

export const batA = [
  ["Arjun Mehta", "c Hayes b Garrick", 62, 38, 6, 3],
  ["Rohan Iyer", "b Whitlock", 18, 14, 2, 0],
  ["Kabir Nair", "c Dawson b Brandt", 41, 27, 4, 2],
  ["Vikram Sethi", "lbw b Ashby", 29, 18, 3, 1],
  ["Dev Kapoor", "run out (Calder)", 12, 8, 1, 0],
  ["Aman Bhatt", "c Pryce b Fenwick", 4, 4, 0, 0],
  ["Ishan Rao", "not out", 11, 6, 1, 1],
  ["Sahil Menon", "not out", 1, 1, 0, 0],
] as const;
export const batB = [
  ["Cole Hayes", "c Nair b Malhotra", 44, 31, 5, 2],
  ["Ethan Pryce", "b Verma", 22, 15, 3, 1],
  ["Mitch Dawson", "c Mehta b Malhotra", 55, 33, 4, 4],
  ["Tom Calder", "lbw b Joshi", 19, 14, 2, 1],
  ["Sam Rennick", "c Iyer b Kapoor", 14, 10, 1, 0],
  ["Ryan Ashby", "b Malhotra", 9, 7, 1, 0],
  ["Zac Fenwick", "c Rao b Verma", 3, 4, 0, 0],
  ["Will Harker", "run out (Sethi)", 8, 6, 1, 0],
  ["Liam Garrick", "not out", 2, 2, 0, 0],
] as const;
export const bowlA = [ // India bowling vs AUS
  ["Karan Malhotra", "4", 0, 31, 3, 11], ["Sandeep Verma", "4", 0, 38, 2, 9], ["Aman Joshi", "4", 0, 35, 1, 9],
  ["Ishan Rao", "4", 0, 44, 1, 7], ["Dev Kapoor", "3", 0, 27, 1, 6], ["Vikram Sethi", "1", 0, 6, 0, 2],
] as const;
export const bowlB = [ // Australia bowling vs IND
  ["Liam Garrick", "4", 0, 34, 2, 10], ["Jack Whitlock", "4", 0, 41, 1, 8], ["Noah Brandt", "4", 0, 29, 1, 11],
  ["Ryan Ashby", "4", 0, 48, 1, 7], ["Zac Fenwick", "3", 0, 27, 1, 6], ["Tom Calder", "1", 0, 8, 0, 1],
] as const;
export const partsA = [["Mehta – Iyer", 41, 4.2], ["Mehta – Nair", 58, 5.4], ["Nair – Sethi", 47, 7.1], ["Sethi – Kapoor", 24, 3.0], ["Kapoor – Bhatt", 9, 2.2], ["Rao – Menon", 8, 1.1]] as const;
export const partsB = [["Hayes – Pryce", 36, 4.0], ["Hayes – Dawson", 51, 6.3], ["Dawson – Calder", 38, 4.5], ["Dawson – Rennick", 22, 3.1], ["Rennick – Ashby", 15, 2.5], ["Ashby – Fenwick", 6, 1.4]] as const;

// win probability (IND perspective) — model output per over of AUS chase
export const winProb = [58, 57, 62, 60, 59, 66, 64, 70, 66, 71, 69, 63, 60, 66, 61, 64, 55, 44, 49, 61, 100].map((v, i) => ({ over: i, ind: v, aus: 100 - v }));

export const AI_INSIGHTS = [
  { tag: "Turning point", tone: "lime", title: "Over 18 swung the chase by 11%", body: "Malhotra conceded only 6 off 4 legal deliveries and removed Rennick; AUS win probability fell from 56% to 45%." },
  { tag: "Pattern", tone: "cyan", title: "Mehta scored 71% of runs through the off side", body: "Against pace in the powerplay his strike rate climbed to 181, with only 3 dot balls in 14 deliveries." },
  { tag: "Risk", tone: "warn", title: "Death-over economy is trending up", body: "India conceded 11.4 per over in overs 17–20 across the last five T20Is, 2.1 above the squad's 12-month average." },
];

export const PLAYER = {
  name: "Arjun Mehta", team: "IND", role: "Top-order batter", style: "Right-hand bat · Off-break", age: 28, born: "Jaipur, Rajasthan", jersey: 18,
  career: { mat: 94, inns: 90, runs: 3412, avg: 41.6, sr: 143.8, hs: "112*", h: 3, f: 27, fours: 301, sixes: 142 },
};
export const form = [62, 8, 41, 77, 23, 0, 54, 31, 112, 18].map((r, i) => ({ i: i + 1, r, opp: ["AUS","AUS","ENG","ENG","RSA","RSA","NZL","PAK","PAK","SL"][i] }));
export const trend = [
  { y: "2020", avg: 29.1, sr: 126 }, { y: "2021", avg: 33.4, sr: 131 }, { y: "2022", avg: 38.2, sr: 137 },
  { y: "2023", avg: 44.9, sr: 146 }, { y: "2024", avg: 47.3, sr: 151 }, { y: "2025", avg: 41.6, sr: 144 },
];
export const dist = [
  { b: "0", n: 8 }, { b: "1–9", n: 14 }, { b: "10–19", n: 16 }, { b: "20–29", n: 14 }, { b: "30–49", n: 19 }, { b: "50–99", n: 16 }, { b: "100+", n: 3 },
];
export const byOpp = [["Australia", 11, 512, 51.2, 152], ["England", 9, 371, 46.4, 139], ["South Africa", 8, 244, 30.5, 141], ["New Zealand", 7, 305, 43.6, 148], ["Pakistan", 10, 468, 52.0, 146], ["Sri Lanka", 8, 198, 24.8, 129]] as const;
export const byVenue = [["Wankhede, Mumbai", 10, 487, 54.1, 158], ["Eden Gardens, Kolkata", 7, 261, 37.3, 133], ["MCG, Melbourne", 6, 233, 38.8, 147], ["Lord's, London", 5, 118, 23.6, 122], ["Dubai Intl.", 9, 402, 50.3, 141]] as const;
export const byInns = [["Batting first", 48, 1892, 43.0, 141], ["Chasing", 42, 1520, 40.0, 147]] as const;
// wagon wheel shots: angle deg (0 = straight down ground), radius 0-1, runs
export const shots = Array.from({ length: 46 }, (_, i) => {
  const a = (i * 137.5) % 360; const rr = ((i * 53) % 100) / 100;
  const runs = rr > 0.9 ? 6 : rr > 0.62 ? 4 : rr > 0.4 ? 2 : 1;
  return { a, r: 0.28 + rr * 0.68, runs };
});
export const zones = [["Off side", 46], ["Straight", 18], ["Leg side", 24], ["Behind", 12]] as const;
export const phases = [
  { p: "Powerplay (1–6)", sr: 139, avg: 38.2, ec: 7.9 }, { p: "Middle (7–15)", sr: 134, avg: 44.1, ec: 8.1 }, { p: "Death (16–20)", sr: 171, avg: 52.8, ec: 11.4 },
];
export const bowlEcon = [{ p: "PP", v: 7.9 }, { p: "Mid", v: 8.1 }, { p: "Death", v: 11.4 }];
export const wktTypes = [{ n: "Bowled", v: 9 }, { n: "Caught", v: 21 }, { n: "LBW", v: 6 }, { n: "Stumped", v: 2 }, { n: "Run out", v: 1 }];
export const compareSets = {
  "Dawson": { Average: 36.8, "Strike rate": 152, "Boundary %": 58, "Dot %": 31, "Conversion": 41, "Death SR": 182 },
  "Mehta": { Average: 41.6, "Strike rate": 144, "Boundary %": 52, "Dot %": 27, "Conversion": 47, "Death SR": 171 },
  "Hayes": { Average: 33.2, "Strike rate": 138, "Boundary %": 49, "Dot %": 34, "Conversion": 35, "Death SR": 160 },
} as Record<string, Record<string, number>>;

export const teamBase = {
  T20I: { p: 128, w: 82, l: 41, nr: 5, ars: 8.9, rpo: 7.6, form: "WWLWWWLWWW", avgS: 178, avgC: 151 },
  ODI: { p: 96, w: 61, l: 31, nr: 4, ars: 5.9, rpo: 5.3, form: "WLWWWLWWLW", avgS: 289, avgC: 254 },
  Test: { p: 54, w: 27, l: 15, nr: 12, ars: 3.7, rpo: 3.1, form: "WDWLWDDWWL", avgS: 372, avgC: 301 },
};
export const teamTrend = Array.from({ length: 12 }, (_, i) => ({ m: ["Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar"][i], bat: [168,172,159,181,176,190,184,171,188,179,193,187][i], bowl: [162,155,170,149,158,141,153,160,146,152,138,144][i] }));
export const teamOpp = [["Australia", 22, 14, 8, 61], ["England", 19, 11, 8, 58], ["South Africa", 17, 12, 5, 71], ["New Zealand", 18, 13, 5, 72], ["Pakistan", 21, 15, 6, 71], ["Sri Lanka", 16, 12, 4, 75]] as const;
export const teamVenue = [["Wankhede, Mumbai", 14, 11, 3, 79], ["Eden Gardens, Kolkata", 12, 9, 3, 75], ["MCG, Melbourne", 8, 3, 5, 38], ["Lord's, London", 7, 3, 4, 43], ["Dubai Intl.", 15, 11, 4, 73]] as const;
