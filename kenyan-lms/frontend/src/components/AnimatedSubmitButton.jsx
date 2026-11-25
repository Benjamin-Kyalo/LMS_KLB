import { useState } from "react";
import RollingLabel from "./RollingLabel";

/**
 * Submit button with a short press animation that always clears itself.
 *
 * The label is a real text node, and the animation only moves/scales the
 * button. It never fades text out, so the normal state is readable before the
 * click, during the animation and after `animationend` restores the base class.
 */
export default function AnimatedSubmitButton({
  children,
  className = "",
  disabled = false,
  onClick,
  onAnimationEnd,
  onPointerDown,
  ...props
}) {
  const [pressed, setPressed] = useState(false);

  function startPress() {
    if (!disabled) setPressed(true);
  }

  function finishPress(event) {
    // The only animation attached to this button is the press feedback.
    setPressed(false);
    onAnimationEnd?.(event);
  }

  const classes = [
    "auth-submit",
    pressed ? "is-pressed" : "",
    className,
  ].filter(Boolean).join(" ");

  return (
    <button
      {...props}
      type={props.type || "submit"}
      className={classes}
      disabled={disabled}
      onPointerDown={(event) => {
        if (disabled) return;
        startPress();
        onPointerDown?.(event);
      }}
      onClick={(event) => {
        if (disabled) return;
        startPress();
        onClick?.(event);
      }}
      onAnimationEnd={finishPress}
    >
      <span className="auth-submit-label">
        <RollingLabel>{children}</RollingLabel>
      </span>
    </button>
  );
}
