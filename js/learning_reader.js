(() => {
  const body = document.body;
  const menuButton = document.getElementById("menu-button");
  const panel = document.getElementById("toc-panel");
  const closeButton = document.getElementById("toc-close");
  const backdrop = document.getElementById("toc-backdrop");
  const backToTop = document.getElementById("back-to-top");
  const tocLinks = [...document.querySelectorAll(".toc-group a")];

  const setMenu = (open) => {
    panel.classList.toggle("is-open", open);
    body.classList.toggle("menu-open", open);
    menuButton.setAttribute("aria-expanded", String(open));
    backdrop.hidden = !open;
    if (open) closeButton.focus();
  };

  menuButton.addEventListener("click", () => setMenu(!panel.classList.contains("is-open")));
  closeButton.addEventListener("click", () => setMenu(false));
  backdrop.addEventListener("click", () => setMenu(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && panel.classList.contains("is-open")) {
      setMenu(false);
      menuButton.focus();
    }
  });
  tocLinks.forEach((link) => link.addEventListener("click", () => {
    if (window.matchMedia("(max-width: 900px)").matches) setMenu(false);
  }));

  const updateBackToTop = () => backToTop.classList.toggle("is-visible", window.scrollY > 640);
  window.addEventListener("scroll", updateBackToTop, { passive: true });
  updateBackToTop();
  backToTop.addEventListener("click", () => {
    try { window.scrollTo({ top: 0, behavior: "smooth" }); }
    catch (_) { window.scrollTo(0, 0); }
  });

  const linkById = new Map(tocLinks.map((link) => [link.dataset.target, link]));
  const observer = new IntersectionObserver((entries) => {
    const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
    if (!visible.length) return;
    tocLinks.forEach((link) => link.classList.remove("is-active"));
    const active = linkById.get(visible[0].target.id);
    if (active) {
      active.classList.add("is-active");
      if (!window.matchMedia("(max-width: 900px)").matches) active.scrollIntoView({ block: "nearest" });
    }
  }, { rootMargin: "-20% 0px -72% 0px" });
  document.querySelectorAll(".learning-unit").forEach((unit) => observer.observe(unit));
})();
