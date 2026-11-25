import { useEffect, useRef, useState } from "react";
import "./ParticleHeadline.css";

/**
 * Particle headline
 * -----------------
 * The <h1> is always the real, accessible headline. The canvas is a purely
 * decorative enhancement layered on top of it; if anything is unavailable
 * (canvas 2d, RAF, a usable layout box, reduced motion) the HTML text stays
 * fully visible.
 *
 * A few small helpers are exported so behaviour can be tested without
 * reaching into React internals.
 */

export const PARTICLE_LIMIT = 2200;
export const PARTICLE_SPACING = 3;

const SPRING = 0.055;
const DAMPING = 0.86;
const REPEL_FORCE = 2.2;
const POINTER_RADIUS = 72;
const SCATTER_MIN = 20;
const SCATTER_SPREAD = 48;
const STAGGER_FRAMES = 9;
const HALO_BLUR = 8;
const MAX_DPR = 2;
const TAU = Math.PI * 2;
const ALPHA_THRESHOLD = 40;

function parseLength(value, fallback) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  const match = String(value || "").match(/-?\d*\.?\d+/);
  const parsed = match ? Number.parseFloat(match[0]) : Number.NaN;
  return Number.isFinite(parsed) ? parsed : fallback;
}

/** Collect evenly spaced, non-transparent sample points and cap the total. */
export function sampleTargets(
  imageData,
  {
    width = imageData?.width || 0,
    height = imageData?.height || 0,
    spacing = PARTICLE_SPACING,
    maxParticles = PARTICLE_LIMIT,
    offsetX = 0,
    offsetY = 0,
  } = {}
) {
  const data = imageData?.data;
  if (!data || width < 1 || height < 1 || spacing < 1) return [];

  const step = Math.max(1, Math.round(spacing));
  const found = [];
  for (let y = 0; y < height; y += step) {
    const row = y * width;
    for (let x = 0; x < width; x += step) {
      const alphaIndex = (row + x) * 4 + 3;
      if (alphaIndex < data.length && data[alphaIndex] > ALPHA_THRESHOLD) {
        found.push({ x: x + offsetX, y: y + offsetY });
      }
    }
  }

  if (found.length <= maxParticles) return found;

  // Thin the samples evenly rather than truncating (which would erase the
  // end of a long headline).
  const ratio = found.length / Math.max(1, maxParticles);
  const capped = [];
  for (let index = 0; index < maxParticles; index += 1) {
    capped.push(found[Math.min(found.length - 1, Math.floor(index * ratio))]);
  }
  return capped;
}

/** Start each particle near its target so the first frames form the text. */
export function createParticles(
  targets,
  {
    random = Math.random,
    scatterMin = SCATTER_MIN,
    scatterSpread = SCATTER_SPREAD,
    stagger = false,
  } = {}
) {
  const maxX = Math.max(1, ...targets.map((target) => target.x));
  return targets.map((target, index) => {
    const angle = random() * TAU;
    const distance = scatterMin + random() * scatterSpread;
    return {
      x: target.x + Math.cos(angle) * distance,
      y: target.y + Math.sin(angle) * distance,
      vx: 0,
      vy: 0,
      tx: target.x,
      ty: target.y,
      radius: 0.9 + random() * 0.8,
      // A short left-to-right delay makes the headline assemble deliberately.
      // Direct physics tests use the default of zero, so they stay deterministic.
      delay: stagger ? Math.round((target.x / maxX) * STAGGER_FRAMES) : 0,
      index,
    };
  });
}

/**
 * One physics step, applied in place for animation performance.
 * Spring towards the target + velocity damping, with a distance-based
 * repulsion while the pointer is over the hero. No random motion after the
 * initial scatter, so particles always settle back onto the exact text.
 */
export function advanceParticles(
  particles,
  pointer,
  {
    spring = SPRING,
    damping = DAMPING,
    repelForce = REPEL_FORCE,
    pointerRadius = POINTER_RADIUS,
  } = {}
) {
  const pointerActive = Boolean(pointer && pointer.active);
  const radiusSquared = pointerRadius * pointerRadius;

  for (const particle of particles) {
    if (particle.delay > 0) {
      particle.delay -= 1;
      continue;
    }
    particle.vx = (particle.vx + (particle.tx - particle.x) * spring) * damping;
    particle.vy = (particle.vy + (particle.ty - particle.y) * spring) * damping;

    if (pointerActive) {
      const dx = particle.x - pointer.x;
      const dy = particle.y - pointer.y;
      const distanceSquared = dx * dx + dy * dy;
      if (distanceSquared > 0.01 && distanceSquared < radiusSquared) {
        const distance = Math.sqrt(distanceSquared);
        const falloff = 1 - distance / pointerRadius;
        particle.vx += (dx / distance) * falloff * repelForce;
        particle.vy += (dy / distance) * falloff * repelForce;
      }
    }

    particle.x += particle.vx;
    particle.y += particle.vy;
  }

  return particles;
}

/** Wrap text the same way the browser does before drawing it offscreen. */
function wrapLines(context, text, maxWidth) {
  const paragraphs = String(text ?? "").split("\n");
  if (!Number.isFinite(maxWidth) || maxWidth <= 0) return paragraphs;

  const lines = [];
  for (const paragraph of paragraphs) {
    const words = paragraph.trim().split(/\s+/).filter(Boolean);
    if (!words.length) {
      lines.push("");
      continue;
    }
    let current = words[0];
    for (let index = 1; index < words.length; index += 1) {
      const candidate = `${current} ${words[index]}`;
      if (context.measureText(candidate).width > maxWidth && current) {
        lines.push(current);
        current = words[index];
      } else {
        current = candidate;
      }
    }
    lines.push(current);
  }
  return lines;
}

export default function ParticleHeadline({ text = "", className = "" }) {
  const wrapperRef = useRef(null);
  const headingRef = useRef(null);
  const canvasRef = useRef(null);
  const [canvasActive, setCanvasActive] = useState(false);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    const heading = headingRef.current;
    const canvas = canvasRef.current;
    if (!wrapper || !heading || !canvas) return undefined;

    let disposed = false;
    let rafId = 0;
    let particles = [];
    let cssWidth = 0;
    let cssHeight = 0;
    let dpr = 1;
    let lastBuildKey = "";
    let visibleCtx = null;
    let particleColor = "#ffffff";
    let particleHighlight = "";
    let particleAccent = "#ffffff";
    let particleGlow = "#ffffff";
    let reduced = false;
    let hidden = Boolean(document.hidden);
    let motionQuery = null;
    let resizeObserver = null;
    let usingWindowResize = false;
    const pointer = { x: 0, y: 0, active: false };

    const requestFrame = typeof window !== "undefined" ? window.requestAnimationFrame : undefined;
    const cancelFrame = typeof window !== "undefined" ? window.cancelAnimationFrame : undefined;

    if (typeof window.matchMedia === "function") {
      motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      reduced = Boolean(motionQuery?.matches);
    }

    const stopFrame = () => {
      if (rafId && typeof cancelFrame === "function") cancelFrame(rafId);
      rafId = 0;
    };

    const clearCanvas = () => {
      if (!visibleCtx) return;
      try {
        visibleCtx.save?.();
        visibleCtx.setTransform?.(1, 0, 0, 1, 0, 0);
        visibleCtx.clearRect?.(0, 0, canvas.width || 0, canvas.height || 0);
        visibleCtx.restore?.();
      } catch {
        /* A broken/decorative context should never affect the headline. */
      }
    };

    const deactivate = () => {
      stopFrame();
      clearCanvas();
      if (!disposed) setCanvasActive(false);
    };

    const ensureContext = () => {
      if (visibleCtx || !canvas.getContext) return visibleCtx;
      try {
        visibleCtx = canvas.getContext("2d") || null;
      } catch {
        visibleCtx = null;
      }
      return visibleCtx;
    };

    const drawParticles = () => {
      if (!visibleCtx || !particles.length) return;
      visibleCtx.clearRect(0, 0, cssWidth, cssHeight);

      // A restrained horizontal gradient reads as polished typography while
      // every stop stays inside the active palette. The halo is drawn in the
      // same pass so the headline lifts off its background without a blur
      // effect that would make small particles hard to read.
      const gradient = visibleCtx.createLinearGradient?.(0, 0, cssWidth, 0);
      gradient?.addColorStop?.(0, particleColor);
      if (particleHighlight) gradient?.addColorStop?.(0.52, particleHighlight);
      gradient?.addColorStop?.(1, particleAccent);
      visibleCtx.save?.();
      visibleCtx.fillStyle = gradient || particleColor;
      if ("shadowBlur" in visibleCtx) {
        visibleCtx.shadowColor = particleGlow;
        visibleCtx.shadowBlur = HALO_BLUR;
      }
      visibleCtx.beginPath();
      for (const particle of particles) {
        if (particle.delay > 0) continue;
        visibleCtx.moveTo?.(particle.x + particle.radius, particle.y);
        visibleCtx.arc(particle.x, particle.y, particle.radius, 0, TAU);
      }
      visibleCtx.fill();
      visibleCtx.restore?.();
    };

    const frame = () => {
      rafId = 0;
      if (disposed || reduced || hidden || !particles.length) return;
      advanceParticles(particles, pointer);
      drawParticles();
      if (typeof requestFrame === "function") rafId = requestFrame(frame);
    };

    const startFrame = () => {
      if (rafId || disposed || reduced || hidden || !particles.length) return;
      if (typeof requestFrame === "function") rafId = requestFrame(frame);
      else drawParticles(); // static fallback: the HTML text stays visible
    };

    const build = () => {
      if (disposed || reduced) return;

      const wrapperRect = wrapper.getBoundingClientRect();
      const headingRect = heading.getBoundingClientRect();
      const width = Math.max(0, headingRect.width || 0);
      const height = Math.max(0, headingRect.height || 0);
      // Also covers jsdom, where no layout box exists at all.
      if (width < 2 || height < 2) {
        particles = [];
        deactivate();
        return;
      }

      if (!ensureContext()) {
        particles = [];
        deactivate();
        return;
      }

      const nextDpr = Math.min(MAX_DPR, Math.max(1, window.devicePixelRatio || 1));
      const buildKey = `${Math.round(width)}x${Math.round(height)}@${nextDpr}:${String(text)}`;
      if (buildKey === lastBuildKey && particles.length) return;
      lastBuildKey = buildKey;

      cssWidth = width;
      cssHeight = height;
      dpr = nextDpr;

      const style = window.getComputedStyle ? window.getComputedStyle(heading) : {};
      const fontSize = parseLength(style.fontSize, 32);
      const font =
        style.font ||
        `${style.fontStyle || "normal"} ${style.fontWeight || "400"} ${fontSize}px ${
          style.fontFamily || "sans-serif"
        }`;

      const offscreen = document.createElement("canvas");
      offscreen.width = Math.max(1, Math.ceil(width));
      offscreen.height = Math.max(1, Math.ceil(height));
      let image = null;
      try {
        const offCtx = offscreen.getContext("2d");
        if (!offCtx) throw new Error("no 2d context");
        offCtx.font = font;
        offCtx.textBaseline = "top";
        if ("letterSpacing" in offCtx && style.letterSpacing) offCtx.letterSpacing = style.letterSpacing;
        const lines = wrapLines(offCtx, text, width - 2);
        const lineHeight = Math.max(fontSize, parseLength(style.lineHeight, fontSize * 1.1));
        lines.forEach((line, index) => offCtx.fillText?.(line, 0, index * lineHeight));
        image = offCtx.getImageData(0, 0, offscreen.width, offscreen.height);
      } catch {
        image = null;
      }

      const offsetX = headingRect.left - wrapperRect.left;
      const offsetY = headingRect.top - wrapperRect.top;
      const targets = image
        ? sampleTargets(image, {
            width: offscreen.width,
            height: offscreen.height,
            offsetX,
            offsetY,
          })
        : [];

      if (!targets.length) {
        particles = [];
        deactivate();
        return;
      }

      particles = createParticles(targets, { stagger: true });
      const readVariable = (name) =>
        String(style.getPropertyValue?.(name) || "").trim();
      particleColor =
        readVariable("--particle-headline-color") ||
        String(style.color || "").trim() ||
        "#ffffff";
      particleHighlight = readVariable("--particle-headline-highlight");
      particleAccent = readVariable("--particle-headline-accent") || particleColor;
      particleGlow = readVariable("--particle-headline-glow") || particleAccent;

      // The canvas sits exactly over the heading's layout box; because it is
      // absolutely positioned this cannot move the text or cause overflow.
      canvas.style.left = `${offsetX}px`;
      canvas.style.top = `${offsetY}px`;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      canvas.width = Math.max(1, Math.round(width * dpr));
      canvas.height = Math.max(1, Math.round(height * dpr));
      visibleCtx.setTransform?.(dpr, 0, 0, dpr, 0, 0);

      stopFrame();
      drawParticles(); // first successful paint: now it is safe to fade text
      if (!disposed && !reduced && !hidden && typeof requestFrame === "function") {
        setCanvasActive(true);
      }
      startFrame();
    };

    const onPointerMove = (event) => {
      const rect = wrapper.getBoundingClientRect();
      pointer.x = event.clientX - rect.left;
      pointer.y = event.clientY - rect.top;
      pointer.active = true;
    };
    const onPointerEnd = () => {
      pointer.active = false;
    };

    const interactionTargets = [wrapper];
    const hero = typeof wrapper.closest === "function" ? wrapper.closest(".public-hero") : null;
    if (hero && hero !== wrapper) interactionTargets.push(hero);

    interactionTargets.forEach((element) => {
      element.addEventListener("pointermove", onPointerMove, { passive: true });
      element.addEventListener("pointerdown", onPointerMove, { passive: true });
      element.addEventListener("pointerleave", onPointerEnd, { passive: true });
      element.addEventListener("pointercancel", onPointerEnd, { passive: true });
      element.addEventListener("pointerup", onPointerEnd, { passive: true });
    });

    const onResize = () => {
      lastBuildKey = "";
      build();
    };

    if (typeof window.ResizeObserver === "function") {
      resizeObserver = new window.ResizeObserver(onResize);
      resizeObserver.observe(wrapper);
    } else if (typeof window.addEventListener === "function") {
      window.addEventListener("resize", onResize, { passive: true });
      usingWindowResize = true;
    }

    const onVisibilityChange = () => {
      hidden = Boolean(document.hidden);
      if (hidden) {
        stopFrame();
      } else {
        if (!reduced && particles.length && typeof requestFrame === "function") {
          setCanvasActive(true);
        }
        startFrame();
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    const onMotionChange = (event) => {
      reduced = Boolean(event.matches);
      if (reduced) {
        deactivate();
      } else {
        lastBuildKey = "";
        build();
      }
    };

    if (motionQuery) {
      if (typeof motionQuery.addEventListener === "function") {
        motionQuery.addEventListener("change", onMotionChange);
      } else if (typeof motionQuery.addListener === "function") {
        motionQuery.addListener(onMotionChange);
      }
    }

    if (!reduced) build();

    return () => {
      disposed = true;
      stopFrame();
      if (resizeObserver) resizeObserver.disconnect();
      if (usingWindowResize) window.removeEventListener("resize", onResize);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      interactionTargets.forEach((element) => {
        element.removeEventListener("pointermove", onPointerMove);
        element.removeEventListener("pointerdown", onPointerMove);
        element.removeEventListener("pointerleave", onPointerEnd);
        element.removeEventListener("pointercancel", onPointerEnd);
        element.removeEventListener("pointerup", onPointerEnd);
      });
      if (motionQuery) {
        if (typeof motionQuery.removeEventListener === "function") {
          motionQuery.removeEventListener("change", onMotionChange);
        } else if (typeof motionQuery.removeListener === "function") {
          motionQuery.removeListener(onMotionChange);
        }
      }
      clearCanvas();
      setCanvasActive(false);
    };
  }, [text]);

  return (
    <div
      ref={wrapperRef}
      className={`particle-headline${className ? ` ${className}` : ""}`}
    >
      <h1
        ref={headingRef}
        className={`particle-headline-text${canvasActive ? " is-canvas-active" : ""}`}
        style={
          canvasActive
            ? { opacity: "var(--particle-headline-base-opacity, 0.46)" }
            : undefined
        }
      >
        {text}
      </h1>
      <canvas
        ref={canvasRef}
        className="particle-headline-canvas"
        aria-hidden="true"
        focusable="false"
        tabIndex={-1}
        style={{ pointerEvents: "none" }}
      />
    </div>
  );
}
