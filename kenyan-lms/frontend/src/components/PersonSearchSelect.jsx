import { useCallback, useEffect, useId, useRef, useState } from "react";
import { api } from "../services/api";
import FormField from "./FormField";

const SEARCH_DELAY_MS = 250;
const MAX_RESULTS = 8;

function rows(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.results)) return data.results;
  return [];
}

/**
 * Server-backed person picker for guardian/learner linking.
 * Searches as the user types, lets them choose a result by mouse or keyboard,
 * and shows the selected record's identifying details before submission.
 */
export default function PersonSearchSelect({
  label,
  endpoint,
  placeholder,
  hint,
  selected,
  onSelect,
  nameKey,
  identifierKey,
  identifierLabel,
  extraDetails = [],
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const listId = useId();
  const containerRef = useRef(null);
  const onSelectRef = useRef(onSelect);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);

  const choose = useCallback((record) => {
    onSelectRef.current(record);
    setQuery("");
    setResults([]);
    setOpen(false);
    setActiveIndex(-1);
  }, []);

  useEffect(() => {
    const needle = query.trim();
    if (needle.length < 2) {
      setResults([]);
      setSearching(false);
      setSearchError(null);
      setOpen(false);
      return undefined;
    }
    let cancelled = false;
    setSearching(true);
    const timer = setTimeout(async () => {
      try {
        const data = await api.get(`${endpoint}?search=${encodeURIComponent(needle)}`);
        if (cancelled) return;
        const matches = rows(data);
        // A typed exact identifier/name is an unambiguous selection.
        const exact = matches.find((item) => [
          item[nameKey], item[identifierKey], item.username,
        ].filter(Boolean).some((value) => String(value).toLowerCase() === needle.toLowerCase()));
        if (exact) {
          choose(exact);
          return;
        }
        setResults(matches.slice(0, MAX_RESULTS));
        setSearchError(null);
        setOpen(true);
      } catch (err) {
        if (cancelled) return;
        setResults([]);
        setSearchError(err.message || "Could not search. Please try again.");
        setOpen(true);
      } finally {
        if (!cancelled) setSearching(false);
      }
    }, SEARCH_DELAY_MS);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [query, endpoint, nameKey, identifierKey, choose]);

  useEffect(() => {
    function onPointerDown(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
        setActiveIndex(-1);
      }
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  function onKeyDown(event) {
    if (event.key === "ArrowDown" && results.length) {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => Math.min(index + 1, results.length - 1));
    } else if (event.key === "ArrowUp" && results.length) {
      event.preventDefault();
      setActiveIndex((index) => Math.max(index - 1, 0));
    } else if (event.key === "Enter" && open && activeIndex >= 0) {
      event.preventDefault();
      choose(results[activeIndex]);
    } else if (event.key === "Escape") {
      setOpen(false);
      setActiveIndex(-1);
    }
  }

  const selectedName = selected ? selected[nameKey] || selected.username : "";

  return (
    <div className="person-picker" ref={containerRef}>
      {selected ? (
        <fieldset className="form-section">
          <legend>Selected {label.toLowerCase()}</legend>
          <dl className="detail-list">
            <div>
              <dt>Name</dt>
              <dd>{selectedName || "—"}</dd>
            </div>
            <div>
              <dt>{identifierLabel}</dt>
              <dd className="mono">{selected[identifierKey] || "—"}</dd>
            </div>
            {extraDetails.map(({ label: detailLabel, key, mono }) => (
              <div key={key}>
                <dt>{detailLabel}</dt>
                <dd className={mono ? "mono" : undefined}>{selected[key] || "—"}</dd>
              </div>
            ))}
          </dl>
          <button type="button" className="ghost small" onClick={() => onSelect(null)}>
            Change {label.toLowerCase()}
          </button>
        </fieldset>
      ) : (
        <FormField label={`Find ${label.toLowerCase()}`} hint={hint}>
          <input
            type="text"
            role="combobox"
            aria-expanded={open}
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={activeIndex >= 0 ? `${listId}-option-${activeIndex}` : undefined}
            value={query}
            onChange={(event) => { setQuery(event.target.value); setOpen(true); setActiveIndex(-1); }}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            autoComplete="off"
          />
        </FormField>
      )}

      {open && !selected && (
        <div className="person-picker-results">
          {searching && <p className="muted" role="status">Searching…</p>}
          {searchError && <div className="notice error" role="alert">{searchError}</div>}
          {!searching && !searchError && results.length === 0 && (
            <p className="muted" role="status">No matches found. Try a name or number.</p>
          )}
          {!searching && results.length > 0 && (
            <ul id={listId} role="listbox" aria-label={`${label} search results`}>
              {results.map((item, index) => (
                <li
                  key={item.id}
                  id={`${listId}-option-${index}`}
                  role="option"
                  aria-selected={index === activeIndex}
                  className={index === activeIndex ? "is-active" : undefined}
                  onMouseEnter={() => setActiveIndex(index)}
                  onClick={() => choose(item)}
                >
                  <strong>{item[nameKey] || item.username || "Unnamed"}</strong>{" "}
                  <span className="mono">{item[identifierKey] || "no number"}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
