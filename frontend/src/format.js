const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Use the date as the author wrote it, not as the viewer's timezone rewrites it.
export function dateParts(iso) {
  if (!iso) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return null;
  return { y: +m[1], m: +m[2], d: +m[3] };
}

export function fmtDate(iso, style = "long") {
  const p = dateParts(iso);
  if (!p) return "an unrecorded night";
  if (style === "short") return `${p.d} ${SHORT[p.m - 1]} ${p.y}`;
  return `${p.d} ${MONTHS[p.m - 1]} ${p.y}`;
}

export function fmtTime(iso) {
  const m = /T(\d{2}):(\d{2})/.exec(iso || "");
  return m ? `${m[1]}:${m[2]}` : "";
}

export function fmtYear(iso) {
  const p = dateParts(iso);
  return p ? String(p.y) : "—";
}

export function fmtNum(n) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("en-US").format(n);
}

export function span(startIso, endIso) {
  const a = dateParts(startIso);
  const b = dateParts(endIso);
  if (!a || !b) return "unknown years";
  if (a.y === b.y) return `${a.y}`;
  return `${a.y} — ${b.y}`;
}

export function ageLabel(days) {
  if (days === null || days === undefined) return "—";
  if (days < 1) return "less than a day";
  if (days < 60) return `${days} day${days === 1 ? "" : "s"}`;
  if (days < 730) return `${Math.round(days / 30)} months`;
  return `${(days / 365).toFixed(days < 3650 ? 1 : 0)} years`;
}

export function shortPath(path, max = 34) {
  if (!path || path.length <= max) return path;
  return "…" + path.slice(-(max - 1));
}

export function plural(n, one, many = `${one}s`) {
  return `${fmtNum(n)} ${n === 1 ? one : many}`;
}

export function roman(n) {
  const table = [
    [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"],
  ];
  let out = "";
  let v = n;
  for (const [value, glyph] of table) {
    while (v >= value) {
      out += glyph;
      v -= value;
    }
  }
  return out;
}
