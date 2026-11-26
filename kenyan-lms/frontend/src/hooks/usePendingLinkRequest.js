import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";

/**
 * Looks for a guardian's pending link request for one learner.
 * A failed lookup only hides this advisory check; the main link form still works.
 */
export default function usePendingLinkRequest(guardianId, learnerId) {
  const [request, setRequest] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setRequest(null);
    if (!guardianId || !learnerId) return undefined;

    api.get(
      `/learners/link-requests/?guardian=${guardianId}&learner=${learnerId}&status=PENDING`
    ).then((data) => {
      if (!cancelled) setRequest((data?.results || [])[0] || null);
    }).catch(() => {
      if (!cancelled) setRequest(null);
    });
    return () => { cancelled = true; };
  }, [guardianId, learnerId]);

  const clear = useCallback(() => setRequest(null), []);
  return { request, clear };
}
