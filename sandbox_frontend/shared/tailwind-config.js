// Loom Blueprint Workbench — Shared Tailwind Configuration
// Single source of truth for design tokens. Used by all workspace pages.
// Extracted from per-page duplicates per methodology finding.shell-duplication.0001.
(function () {
  if (window.__loomTailwindInjected) return;
  window.__loomTailwindInjected = true;

  // Safely merge if tailwind.config already exists (from script tag)
  var existing = window.tailwind && window.tailwind.config ? window.tailwind.config : {};

  tailwind.config = {
    darkMode: "class",
    theme: {
      extend: {
        colors: {
          "on-secondary-fixed-variant": "#00531a",
          "surface-container-highest": "#353437",
          "tertiary": "#ffb868",
          "on-tertiary-fixed-variant": "#673d00",
          "error": "#ffb4ab",
          "tertiary-fixed-dim": "#ffb868",
          "tertiary-fixed": "#ffddbb",
          "outline-variant": "#414754",
          "on-secondary-container": "#004615",
          "background": "#131315",
          "secondary": "#47e266",
          "on-tertiary": "#482900",
          "tertiary-container": "#ce7f00",
          "surface-variant": "#353437",
          "surface": "#131315",
          "on-error-container": "#ffdad6",
          "inverse-primary": "#005db8",
          "on-surface-variant": "#c0c6d6",
          "on-secondary-fixed": "#002106",
          "surface-container": "#1f1f21",
          "on-primary": "#003064",
          "on-primary-fixed": "#001b3e",
          "on-primary-fixed-variant": "#00468d",
          "inverse-surface": "#e4e2e4",
          "primary-fixed": "#d6e3ff",
          "surface-bright": "#39393b",
          "surface-container-lowest": "#0e0e10",
          "surface-container-low": "#1b1b1d",
          "on-tertiary-container": "#3f2300",
          "secondary-fixed-dim": "#47e266",
          "error-container": "#93000a",
          "outline": "#8b91a0",
          "surface-container-high": "#2a2a2c",
          "on-surface": "#e4e2e4",
          "surface-tint": "#aac7ff",
          "primary-container": "#3e90ff",
          "inverse-on-surface": "#303032",
          "on-primary-container": "#002957",
          "secondary-fixed": "#6cff82",
          "primary": "#aac7ff",
          "on-background": "#e4e2e4",
          "primary-fixed-dim": "#aac7ff",
          "on-tertiary-fixed": "#2b1700",
          "on-error": "#690005",
          "surface-dim": "#131315",
          "secondary-container": "#09bf49",
          "on-secondary": "#003910"
        },
        borderRadius: {
          DEFAULT: "0.25rem",
          lg: "12px",
          xl: "16px",
          "2xl": "12px",
          full: "9999px"
        },
        spacing: {
          "stack-sm": "4px",
          "unit": "8px",
          "panel-padding": "12px",
          "stack-md": "8px",
          "container-margin": "24px",
          "stack-lg": "16px",
          "gutter": "16px",
          "sidebar-width": "48px",
          "inspector-width": "320px",
          "toolbar-height": "48px"
        },
        fontFamily: {
          "label-caps": ["Geist"],
          "headline-lg": ["Geist"],
          "body-sm": ["Geist"],
          "display-lg": ["Geist"],
          "body-lg": ["Geist"],
          "title-md": ["Geist"],
          "mono-precision": ["JetBrains Mono", "jetbrainsMono", "monospace"],
          "sans": ["Geist", "Inter", "system-ui", "sans-serif"],
          "mono": ["JetBrains Mono", "monospace"]
        },
        fontSize: {
          "label-caps": ["12px", { lineHeight: "1.2", letterSpacing: "0.05em", fontWeight: "600" }],
          "headline-lg": ["32px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "600" }],
          "body-sm": ["14px", { lineHeight: "1.5", letterSpacing: "0em", fontWeight: "400" }],
          "display-lg": ["48px", { lineHeight: "1.1", letterSpacing: "-0.03em", fontWeight: "700" }],
          "body-lg": ["16px", { lineHeight: "1.5", letterSpacing: "-0.01em", fontWeight: "400" }],
          "title-md": ["20px", { lineHeight: "1.4", letterSpacing: "-0.01em", fontWeight: "600" }],
          "mono-precision": ["13px", { lineHeight: "1", letterSpacing: "0em", fontWeight: "500" }],
          "headline-lg-mobile": ["24px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "600" }]
        }
      }
    }
  };

  // Merge existing config overrides if present
  if (existing.theme && existing.theme.extend) {
    for (var key in existing.theme.extend) {
      if (existing.theme.extend.hasOwnProperty(key)) {
        tailwind.config.theme.extend[key] = Object.assign(
          {},
          tailwind.config.theme.extend[key],
          existing.theme.extend[key]
        );
      }
    }
  }
})();
