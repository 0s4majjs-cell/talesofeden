// Tales of Eden - Theme Loader (NO animation settings)
// Responsible for applying color presets & reader font settings across ALL pages.

(function () {
  const THEME_STORAGE_KEY = "toe_theme";

  const defaultTheme = {
    presetId: "eden",

    // Colors
    accent: "#4ea1ff",
    bgMainTop: "#182538",
    bgMainBottom: "#05060a",
    sidebarTop: "#111827",
    sidebarBottom: "#020308",
    cardTop: "#0b1020",
    cardBottom: "#05070c",
    readerPage: "#08121e",
    textMain: "#e9f1ff",
    textMuted: "#9aa4c3",

    // Reader styling
    readerFont: "serif",      // "serif" | "sans" | "mono"
    readerFontSize: "normal", // "small" | "normal" | "large"

    // Background style tag if you use it
    bgStyle: "nebula"
  };

  function loadTheme() {
    try {
      const raw = localStorage.getItem(THEME_STORAGE_KEY);
      if (!raw) return { ...defaultTheme };
      const parsed = JSON.parse(raw);
      return { ...defaultTheme, ...parsed };
    } catch (e) {
      console.warn("[theme-loader] Failed to parse toe_theme, using defaults:", e);
      return { ...defaultTheme };
    }
  }

  function applyTheme(theme) {
    const t = theme || loadTheme();
    const root = document.documentElement;

    // Colors
    root.style.setProperty("--color-accent", t.accent);
    root.style.setProperty("--color-bg-main-top", t.bgMainTop);
    root.style.setProperty("--color-bg-main-bottom", t.bgMainBottom);
    root.style.setProperty("--color-bg-sidebar-top", t.sidebarTop);
    root.style.setProperty("--color-bg-sidebar-bottom", t.sidebarBottom);
    root.style.setProperty("--color-card-top", t.cardTop);
    root.style.setProperty("--color-card-bottom", t.cardBottom);
    root.style.setProperty("--color-reader-page", t.readerPage);
    root.style.setProperty("--color-text-main", t.textMain);
    root.style.setProperty("--color-text-muted", t.textMuted);

    // Background style tag
    root.setAttribute("data-bg-style", t.bgStyle || "nebula");

    // Reader font
    let fontStack;
    if (t.readerFont === "mono") {
      fontStack = '"JetBrains Mono", "Cascadia Code", monospace';
    } else if (t.readerFont === "sans") {
      fontStack = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    } else {
      fontStack = '"Georgia", "Times New Roman", serif';
    }
    root.style.setProperty("--font-reader", fontStack);

    // Reader font size
    let sizeRem = "0.98rem";
    if (t.readerFontSize === "small") sizeRem = "0.9rem";
    if (t.readerFontSize === "large") sizeRem = "1.08rem";
    root.style.setProperty("--reader-font-size", sizeRem);

    // Expose so your customization page can read it
    window.__toeTheme = t;
  }

  const theme = loadTheme();
  applyTheme(theme);
})();
