import {
  createContext, useContext, useEffect, useMemo, useState,
} from "react";
import { api, request } from "../services/api";
import {
  flushOutbox, getClientConfig, lowBandwidthStatus, setClientConfig, subscribe,
} from "../services/lowBandwidth";

const LowBandwidthContext = createContext(null);

// Public config is fetched once per page load. It is not cached: an operator
// can disable the feature without asking every browser to clear local data.
export function LowBandwidthProvider({ children }) {
  const [config, setConfig] = useState(getClientConfig());
  const [online, setOnline] = useState(
    typeof navigator === "undefined" ? true : navigator.onLine !== false,
  );
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let active = true;
    api.get("/core/client-config/")
      .then((data) => {
        setClientConfig(data);
        if (active) setConfig(data);
      })
      .catch(() => { /* Without config, the app stays fully online-only. */ });
    const unsubscribe = subscribe(() => setRevision((value) => value + 1));
    return () => { active = false; unsubscribe(); };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const wentOnline = () => {
      setOnline(true);
      flushOutbox(request).catch(() => {});
    };
    const wentOffline = () => setOnline(false);
    window.addEventListener("online", wentOnline);
    window.addEventListener("offline", wentOffline);
    return () => {
      window.removeEventListener("online", wentOnline);
      window.removeEventListener("offline", wentOffline);
    };
  }, []);

  const value = useMemo(() => ({
    config,
    online,
    revision,
    status: lowBandwidthStatus(),
    flush: () => flushOutbox(request),
  }), [config, online, revision]);

  return (
    <LowBandwidthContext.Provider value={value}>{children}</LowBandwidthContext.Provider>
  );
}

export function useLowBandwidth() {
  const context = useContext(LowBandwidthContext);
  if (context) return context;
  return {
    config: null, online: true, revision: 0,
    status: { cached_reads: 0, queued_writes: 0, conflicts: 0 },
    flush: async () => ({ sent: 0, conflicts: 0, kept: 0 }),
  };
}
