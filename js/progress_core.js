(function (root, factory) {
  root.IPASProgressCore = factory();
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const VERSION = 1;
  const KEY = "ipas-learning-progress-v1";
  const STATUSES = ["NOT_STARTED", "IN_PROGRESS", "COMPLETED"];
  const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
  function localDate(date) { const v = date || new Date(); const p = (n) => String(n).padStart(2, "0"); return `${v.getFullYear()}-${p(v.getMonth() + 1)}-${p(v.getDate())}`; }
  function validDate(value) { if (!DATE_RE.test(value || "")) return false; const [y, m, d] = value.split("-").map(Number); const v = new Date(y, m - 1, d); return v.getFullYear() === y && v.getMonth() === m - 1 && v.getDate() === d; }
  function blank(ids) { return Object.fromEntries(ids.map((id) => [id, { status: "NOT_STARTED", completed_at: null }])); }
  function normalizeRecord(record) {
    const value = record || {};
    if (!STATUSES.includes(value.status)) throw new Error("包含非法的學習狀態。");
    if (value.status === "COMPLETED") {
      const done = typeof value.completed_at === "string" ? { date: value.completed_at, timestamp: `${value.completed_at}T00:00:00` } : value.completed_at;
      if (!done || !validDate(done.date) || Number.isNaN(Date.parse(done.timestamp))) throw new Error("完成日期或時間格式不合法。");
      return { status: value.status, completed_at: { date: done.date, timestamp: done.timestamp } };
    }
    if (value.completed_at !== null && value.completed_at !== undefined) throw new Error("未完成狀態不得包含完成日期。");
    return { status: value.status, completed_at: null };
  }
  function validate(payload, ids) {
    if (!payload || payload.version !== VERSION || !payload.units || Array.isArray(payload.units)) throw new Error("進度檔版本或結構不正確。");
    const allowed = new Set(ids); const units = {};
    Object.entries(payload.units).forEach(([id, record]) => { if (!allowed.has(id)) throw new Error(`不存在的 Learning Unit：${id}`); units[id] = normalizeRecord(record); });
    return { version: VERSION, updated_at: payload.updated_at || null, units };
  }
  function hydrate(payload, ids) { const state = blank(ids); if (payload) Object.assign(state, validate(payload, ids).units); return state; }
  function merge(current, incoming, ids) {
    const next = hydrate({ version: VERSION, units: current }, ids); const imported = validate(incoming, ids).units;
    Object.entries(imported).forEach(([id, value]) => { const old = next[id];
      if (value.status === "COMPLETED" && (old.status !== "COMPLETED" || value.completed_at.date > old.completed_at.date || (value.completed_at.date === old.completed_at.date && value.completed_at.timestamp > old.completed_at.timestamp))) next[id] = value;
      else if (old.status !== "COMPLETED" && value.status === "IN_PROGRESS") next[id] = value;
    }); return next;
  }
  function complete(state, id, now) { const v = now || new Date(); return Object.assign({}, state, { [id]: { status: "COMPLETED", completed_at: { date: localDate(v), timestamp: v.toISOString() } } }); }
  function cancel(state, id) { return Object.assign({}, state, { [id]: { status: "NOT_STARTED", completed_at: null } }); }
  function nextId(state, ids) { return ids.find((id) => state[id].status === "IN_PROGRESS") || ids.find((id) => state[id].status === "NOT_STARTED") || null; }
  function stats(state, units, today) { const completed = units.filter((u) => state[u.id].status === "COMPLETED"); const subjects = {};
    units.forEach((u) => { subjects[u.subject] ||= { completed: 0, total: 0 }; subjects[u.subject].total += 1; if (state[u.id].status === "COMPLETED") subjects[u.subject].completed += 1; });
    return { completed: completed.length, total: units.length, subjects, today: completed.filter((u) => state[u.id].completed_at.date === today) }; }
  function exportPayload(state, now) { return { version: VERSION, updated_at: (now || new Date()).toISOString(), units: state }; }
  return { VERSION, KEY, STATUSES, localDate, validDate, blank, validate, hydrate, merge, complete, cancel, nextId, stats, exportPayload };
}));
