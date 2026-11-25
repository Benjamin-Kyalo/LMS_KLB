import {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
} from "react";
import { getSiteContent, mergeContent } from "../config/publicSite";
import { api } from "../services/api";

const CACHE_KEY = "klb_site_content";
const SiteContentContext = createContext(null);

function storage() {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function cachedContent() {
  try {
    const raw = storage()?.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveContent(content) {
  try {
    storage()?.setItem(CACHE_KEY, JSON.stringify(content));
  } catch {
    /* Storage can be blocked; the live response still updates the UI. */
  }
}

export function SiteContentProvider({ children }) {
  const [content, setContent] = useState(() => mergeContent(
    getSiteContent(), cachedContent() || {},
  ));

  const refreshSiteContent = useCallback(async () => {
    try {
      const data = await api.get("/theming/site-content/");
      setContent(mergeContent(getSiteContent(), data));
      saveContent(data);
      return data;
    } catch {
      // Keep the last known wording and the local defaults on a failed request.
      return null;
    }
  }, []);

  useEffect(() => { refreshSiteContent(); }, [refreshSiteContent]);

  const value = useMemo(
    () => ({ content, refreshSiteContent }),
    [content, refreshSiteContent],
  );
  return <SiteContentContext.Provider value={value}>{children}</SiteContentContext.Provider>;
}

export function useSiteContent() {
  const context = useContext(SiteContentContext);
  const fallback = useMemo(
    () => ({ content: getSiteContent(), refreshSiteContent: async () => null }),
    [],
  );
  return context || fallback;
}
