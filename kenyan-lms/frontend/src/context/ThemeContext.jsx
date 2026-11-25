import {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
} from "react";
import { api } from "../services/api";
import {
  DEFAULT_PALETTE, applyPaletteToDocument, normalisePalette,
} from "../styles/palette";

const STORAGE_KEY = "klb_active_palette";
const ThemeContext = createContext(null);

function cachedPalette() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? normalisePalette(JSON.parse(raw)) : null;
  } catch {
    return null;
  }
}

function cachePalette(palette) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(palette));
  } catch {
    /* Private browsing may block storage; the DOM variables still apply. */
  }
}

export function ThemeProvider({ children }) {
  const [palette, setPalette] = useState(() => cachedPalette() || DEFAULT_PALETTE);
  const [loading, setLoading] = useState(true);

  const applyPalette = useCallback((value) => {
    const next = normalisePalette(value);
    setPalette(next);
    cachePalette(next);
    applyPaletteToDocument(next);
  }, []);

  const refreshTheme = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get("/theming/active/");
      applyPalette(data);
      return data;
    } catch {
      // Server error: keep the last known palette.
      applyPalette(cachedPalette() || DEFAULT_PALETTE);
      return null;
    } finally {
      setLoading(false);
    }
  }, [applyPalette]);

  useEffect(() => {
    applyPalette(cachedPalette() || DEFAULT_PALETTE);
    refreshTheme();
    const onOnline = () => refreshTheme();
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [applyPalette, refreshTheme]);

  const value = useMemo(() => ({
    palette,
    colors: palette.colors,
    loading,
    applyPalette,
    refreshTheme,
  }), [palette, loading, applyPalette, refreshTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

const FALLBACK_THEME = Object.freeze({
  palette: DEFAULT_PALETTE,
  colors: DEFAULT_PALETTE.colors,
  loading: false,
  applyPalette: () => {},
  refreshTheme: async () => null,
});

export function useTheme() {
  return useContext(ThemeContext) || FALLBACK_THEME;
}
