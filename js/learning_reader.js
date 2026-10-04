(() => {
  "use strict";
  const core = window.IPASProgressCore;
  const body = document.body;
  const nodes = [...document.querySelectorAll(".learning-unit")];
  const units = nodes.sort((a, b) => Number(a.dataset.order) - Number(b.dataset.order)).map((node) => ({ id: node.id, subject: node.dataset.subject, order: Number(node.dataset.order), title: node.dataset.title, topic: node.dataset.topic, node, search: node.textContent.toLocaleLowerCase("zh-Hant") }));
  const ids = units.map((unit) => unit.id);
  const links = new Map([...document.querySelectorAll("[data-target]")].map((link) => [link.dataset.target, link]));
  let state; let currentId = ids[0]; let filter = "all";
  try { state = core.hydrate(JSON.parse(localStorage.getItem(core.KEY) || "null"), ids); } catch (_) { state = core.blank(ids); }
  const text = (id, value) => { document.getElementById(id).textContent = value; };
  const bar = (id, value) => { document.getElementById(id).style.width = `${value}%`; };
  const pct = (value, total) => total ? Math.round(value / total * 1000) / 10 : 0;
  const dateText = (date) => date ? date.replaceAll("-", "/") : "";
  const html = (value) => { const span = document.createElement("span"); span.textContent = value; return span.innerHTML; };
  function announce(message, error) { const live = document.getElementById("progress-live"); live.textContent = message; live.classList.toggle("is-error", Boolean(error)); }
  function persist() { localStorage.setItem(core.KEY, JSON.stringify(core.exportPayload(state))); }
  function setCurrent(id) { if (!links.has(id)) return; currentId = id; links.forEach((link, key) => link.classList.toggle("is-active", key === id)); const unit = units.find((item) => item.id === id); text("reading-position", `閱讀位置：LU ${String(unit.order).padStart(2, "0")}`); }
  function closeMenu() { const panel = document.getElementById("toc-panel"); panel.classList.remove("is-open"); body.classList.remove("menu-open"); document.getElementById("menu-button").setAttribute("aria-expanded", "false"); document.getElementById("toc-backdrop").hidden = true; }
  function jump(id) { const target = document.getElementById(id); if (!target) return; setCurrent(id); target.scrollIntoView({ behavior: "smooth", block: "start" }); closeMenu(); }
  function render() {
    const today = core.localDate(); const summary = core.stats(state, units, today); const next = core.nextId(state, ids); const current = units.find((unit) => unit.id === next); const overall = pct(summary.completed, summary.total);
    text("overall-count", `${summary.completed} / ${summary.total} LU`); text("overall-percent", `${overall}%`); bar("overall-bar", overall); text("mobile-progress", `${summary.completed} / ${summary.total}`);
    ["Z02-01", "Z02-03"].forEach((subject) => { const item = summary.subjects[subject]; bar(`bar-${subject}`, pct(item.completed, item.total)); text(`count-${subject}`, `${item.completed} / ${item.total}`); });
    text("today-date", dateText(today)); text("today-count", `今日完成 ${summary.today.length} 個 LU`); document.getElementById("today-list").innerHTML = summary.today.map((u) => `<li><a href="#${u.id}" data-jump="${u.id}">✓ LU ${String(u.order).padStart(2, "0")} ${html(u.title)}</a></li>`).join("");
    text("current-id", current ? current.id : "64 / 64"); text("current-title", current ? current.title : "第一輪學習已完成"); text("mobile-current", current ? `LU ${String(current.order).padStart(2, "0")}` : "已完成"); document.querySelectorAll("[data-continue]").forEach((button) => { button.disabled = !current; button.dataset.target = next || ""; });
    units.forEach((unit) => { const record = state[unit.id]; const done = record.status === "COMPLETED"; const link = links.get(unit.id); const date = done ? dateText(record.completed_at.date) : "";
      unit.node.dataset.progressStatus = record.status; unit.node.querySelector(".unit-progress-state").textContent = done ? "✓ 已完成" : "○ 尚未完成"; unit.node.querySelector(".unit-progress-date").textContent = date; unit.node.querySelector(".complete-button").hidden = done; unit.node.querySelector(".cancel-button").hidden = !done;
      link.querySelector(".toc-state").textContent = done ? "✓" : "○"; link.querySelector(".toc-date").textContent = date; link.title = done ? `已完成：${date}` : "尚未完成"; link.closest("li").hidden = filter === "completed" ? !done : filter === "incomplete" ? done : false;
    }); setCurrent(currentId); runSearch();
  }
  document.addEventListener("click", (event) => { const complete = event.target.closest(".complete-button"); const cancel = event.target.closest(".cancel-button"); const jumpLink = event.target.closest("[data-jump], [data-continue]");
    if (complete) { state = core.complete(state, complete.dataset.id); persist(); render(); announce("已記錄完成日期。"); }
    if (cancel && confirm("確定要取消這個 LU 的完成紀錄嗎？")) { state = core.cancel(state, cancel.dataset.id); persist(); render(); announce("已取消完成紀錄。"); }
    if (jumpLink && (jumpLink.dataset.target || jumpLink.dataset.jump)) { event.preventDefault(); jump(jumpLink.dataset.target || jumpLink.dataset.jump); }
  });
  const search = document.getElementById("lu-search"); let timer;
  search.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(runSearch, 180); });
  function runSearch() { const query = search.value.trim().toLocaleLowerCase("zh-Hant"); const result = document.getElementById("search-results"); if (!query) { result.hidden = true; result.innerHTML = ""; return; }
    const matches = units.filter((u) => u.search.includes(query) && (filter === "all" || (filter === "completed") === (state[u.id].status === "COMPLETED"))); result.hidden = false; result.innerHTML = `<strong>搜尋結果 ${matches.length}</strong>${matches.slice(0, 30).map((u) => `<a href="#${u.id}" data-jump="${u.id}"><span>${state[u.id].status === "COMPLETED" ? "✓ 已完成" : "○ 未完成"} · LU ${String(u.order).padStart(2, "0")}</span>${html(u.title)}</a>`).join("") || "<p>沒有符合的 Learning Unit。</p>"}`;
  }
  document.querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => { filter = button.dataset.filter; document.querySelectorAll("[data-filter]").forEach((item) => item.classList.toggle("is-selected", item === button)); render(); }));
  document.getElementById("export-progress").addEventListener("click", () => { const blob = new Blob([JSON.stringify(core.exportPayload(state), null, 2)], { type: "application/json" }); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `ipas-learning-progress-${core.localDate()}.json`; link.click(); URL.revokeObjectURL(link.href); });
  const importer = document.getElementById("import-file"); document.getElementById("import-progress").addEventListener("click", () => importer.click()); importer.addEventListener("change", async () => { if (!importer.files[0]) return; try { const payload = JSON.parse(await importer.files[0].text()); const merged = core.merge(state, payload, ids); state = merged; persist(); render(); announce("匯入完成；已依最新完成日期合併。"); } catch (error) { announce(`匯入失敗：${error.message}`, true); alert(`匯入失敗：${error.message}\n目前資料未變更。`); } finally { importer.value = ""; } });
  document.getElementById("reset-progress").addEventListener("click", () => { if (!confirm("此操作會清除目前瀏覽器中的第一輪學習完成紀錄。建議先匯出。是否繼續？")) return; if (!confirm("再次確認：要重設全部 64 個 LU 的學習進度嗎？")) return; localStorage.removeItem(core.KEY); state = core.blank(ids); render(); announce("學習進度已重設。"); });
  const panel = document.getElementById("toc-panel"); const backdrop = document.getElementById("toc-backdrop"); const menuButton = document.getElementById("menu-button"); menuButton.addEventListener("click", () => { const open = !panel.classList.contains("is-open"); panel.classList.toggle("is-open", open); body.classList.toggle("menu-open", open); menuButton.setAttribute("aria-expanded", String(open)); backdrop.hidden = !open; }); document.getElementById("toc-close").addEventListener("click", closeMenu); backdrop.addEventListener("click", closeMenu); document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeMenu(); });
  const top = document.getElementById("back-to-top"); window.addEventListener("scroll", () => top.classList.toggle("is-visible", scrollY > 640), { passive: true }); top.addEventListener("click", () => scrollTo({ top: 0, behavior: "smooth" }));
  const observer = new IntersectionObserver((entries) => { const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top); if (visible[0]) setCurrent(visible[0].target.id); }, { rootMargin: "-20% 0px -72% 0px" }); units.forEach((unit) => observer.observe(unit.node)); render();
})();
