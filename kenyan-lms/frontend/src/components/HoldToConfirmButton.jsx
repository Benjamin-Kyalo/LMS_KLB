import { useEffect, useRef, useState } from "react";

/**
 * Destructive action with a short press-and-hold fill.
 *
 * Pointer users hold the button to confirm. Keyboard and assistive-technology
 * users can activate it normally with Enter or Space, so the hold gesture is
 * never the only path to the action. The label stays visible throughout.
 */
export default function HoldToConfirmButton({
  children,
  className = "",
  disabled = false,
  holdMs = 650,
  onConfirm,
  title,
  ...props
}) {
  const [holding, setHolding] = useState(false);
  const [progress, setProgress] = useState(0);
  const frame = useRef(null);
  const completed = useRef(false);

  useEffect(() => () => {
    if (frame.current !== null) cancelAnimationFrame(frame.current);
  }, []);

  function stop() {
    if (frame.current !== null) {
      cancelAnimationFrame(frame.current);
      frame.current = null;
    }
    setHolding(false);
    setProgress(0);
  }

  function start(event) {
    if (disabled || completed.current) return;
    if (typeof event.button === "number" && event.button !== 0) return;
    stop();
    const startedAt = performance.now();
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    setHolding(true);

    function step(now) {
      const value = Math.min(1, (now - startedAt) / holdMs);
      if (!reduceMotion) setProgress(value);
      if (value >= 1) {
        frame.current = null;
        completed.current = true;
        setHolding(false);
        setProgress(0);
        onConfirm?.();
        return;
      }
      frame.current = requestAnimationFrame(step);
    }

    frame.current = requestAnimationFrame(step);
  }

  function handleClick(event) {
    // A pointer click after a completed hold must not confirm twice.
    if (completed.current) {
      completed.current = false;
      event.preventDefault();
      return;
    }
    // Enter and Space produce detail 0. They are the accessible fallback for
    // users who cannot perform a timed hold.
    if (event.detail === 0) onConfirm?.();
  }

  const classes = [
    "hold-confirm",
    holding ? "is-holding" : "",
    className,
  ].filter(Boolean).join(" ");

  const label = typeof children === "string" ? children : "Confirm";
  const defaultTitle = `Hold to ${label.toLowerCase()}, or press Enter or Space to confirm.`;

  return (
    <button
      {...props}
      type={props.type || "button"}
      className={classes}
      disabled={disabled}
      title={title || defaultTitle}
      aria-label={props["aria-label"] || `${label}. ${defaultTitle}`}
      aria-busy={holding || undefined}
      style={{ "--hold-progress": progress, ...props.style }}
      onPointerDown={(event) => {
        start(event);
      }}
      onPointerUp={stop}
      onPointerLeave={stop}
      onPointerCancel={stop}
      onBlur={stop}
      onClick={handleClick}
    >
      <span>{children}</span>
    </button>
  );
}
