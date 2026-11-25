import { StrictMode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import ParticleHeadline, {
  advanceParticles,
  createParticles,
} from "./ParticleHeadline";

const HEADLINE = "Teaching and learning for every Kenyan learner";

function rect(width, height, left = 0, top = 0) {
  return {
    left,
    top,
    width,
    height,
    right: left + width,
    bottom: top + height,
    x: left,
    y: top,
    toJSON: () => ({}),
  };
}

describe("ParticleHeadline", () => {
  let contexts;
  let getContextSpy;
  let raf;
  let motionQuery;
  let observers;
  let layout;
  let originals;

  beforeEach(() => {
    originals = {
      matchMedia: window.matchMedia,
      raf: window.requestAnimationFrame,
      cancelRaf: window.cancelAnimationFrame,
      observer: window.ResizeObserver,
    };
    contexts = [];
    observers = [];
    layout = { wrapper: rect(600, 200), heading: rect(480, 120) };

    raf = {
      queue: new Map(),
      nextId: 0,
      request: vi.fn((callback) => {
        const id = (raf.nextId += 1);
        raf.queue.set(id, callback);
        return id;
      }),
      cancel: vi.fn((id) => {
        raf.queue.delete(id);
      }),
    };
    window.requestAnimationFrame = raf.request;
    window.cancelAnimationFrame = raf.cancel;

    getContextSpy = vi
      .spyOn(HTMLCanvasElement.prototype, "getContext")
      .mockImplementation(function getContext(type) {
        if (type !== "2d") return null;
        const context = {
          canvas: this,
          font: "",
          textBaseline: "",
          letterSpacing: "",
          fillStyle: "",
          shadowColor: "",
          shadowBlur: 0,
          createLinearGradient: vi.fn(() => ({ addColorStop: vi.fn() })),
          arcs: [],
          clearRect: vi.fn(() => {
            context.arcs = [];
          }),
          beginPath: vi.fn(),
          moveTo: vi.fn(),
          arc: vi.fn((x, y, radius) => context.arcs.push({ x, y, radius })),
          fill: vi.fn(),
          fillText: vi.fn(),
          measureText: vi.fn((value) => ({ width: String(value).length * 9 })),
          getImageData: vi.fn((x, y, width, height) => {
            const data = new Uint8ClampedArray(width * height * 4);
            for (let py = 0; py < height; py += 1) {
              for (let px = 0; px < width; px += 1) {
                if (px % 8 === 0 && py % 8 === 0) {
                  data[(py * width + px) * 4 + 3] = 255;
                }
              }
            }
            return { data, width, height };
          }),
          setTransform: vi.fn(),
          save: vi.fn(),
          restore: vi.fn(),
        };
        contexts.push(context);
        return context;
      });

    motionQuery = {
      matches: false,
      media: "(prefers-reduced-motion: reduce)",
      listeners: new Set(),
      addEventListener: vi.fn((type, listener) => motionQuery.listeners.add(listener)),
      removeEventListener: vi.fn((type, listener) => motionQuery.listeners.delete(listener)),
      addListener: vi.fn(),
      removeListener: vi.fn(),
    };
    window.matchMedia = vi.fn(() => motionQuery);

    class ResizeObserverStub {
      constructor(callback) {
        this.callback = callback;
        this.targets = [];
        this.disconnected = false;
        observers.push(this);
      }
      observe(target) {
        this.targets.push(target);
      }
      unobserve() {}
      disconnect() {
        this.disconnected = true;
      }
    }
    window.ResizeObserver = ResizeObserverStub;

    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function getBoundingClientRect() {
      if (this.classList?.contains("particle-headline")) return { ...layout.wrapper };
      if (this.tagName === "H1") return { ...layout.heading };
      return rect(0, 0);
    });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    window.matchMedia = originals.matchMedia;
    window.requestAnimationFrame = originals.raf;
    window.cancelAnimationFrame = originals.cancelRaf;
    window.ResizeObserver = originals.observer;
  });

  function flushFrame(time = 16) {
    const entries = [...raf.queue.entries()];
    const [id, callback] = entries[entries.length - 1] || [];
    if (!callback) return false;
    raf.queue.delete(id);
    callback(time);
    return true;
  }

  function settle(frames = 100) {
    for (let index = 0; index < frames; index += 1) flushFrame(16 * (index + 1));
  }

  function imageSampleCount() {
    return contexts.reduce(
      (total, context) => total + context.getImageData.mock.calls.length,
      0
    );
  }

  function visibleContext() {
    return contexts.find((context) =>
      context.canvas?.classList?.contains("particle-headline-canvas")
    );
  }

  function dispatchPointer(type, x, y) {
    const wrapper = document.querySelector(".particle-headline");
    const event = new Event(type, { bubbles: true });
    Object.defineProperty(event, "clientX", { value: x });
    Object.defineProperty(event, "clientY", { value: y });
    wrapper.dispatchEvent(event);
  }

  it("keeps the exact accessible headline and a fully decorative canvas", () => {
    const { container } = render(<ParticleHeadline text={HEADLINE} />);

    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading.textContent).toBe(HEADLINE);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(heading.classList.contains("is-canvas-active")).toBe(true);
    // The real heading stays visibly beneath the decorative particles; hover
    // repulsion must never make the words disappear.
    expect(heading.style.opacity).toContain("--particle-headline-base-opacity");

    const canvas = container.querySelector("canvas");
    expect(canvas.getAttribute("aria-hidden")).toBe("true");
    expect(canvas.getAttribute("focusable")).toBe("false");
    expect(canvas.tabIndex).toBe(-1);
    expect(canvas.style.pointerEvents).toBe("none");
    expect(imageSampleCount()).toBeGreaterThan(0);
    expect(visibleContext().fill).toHaveBeenCalled();
  });

  it("uses a two-tone gradient, soft halo and a left-to-right settle", () => {
    render(<ParticleHeadline text={HEADLINE} />);
    const context = visibleContext();

    expect(context.createLinearGradient).toHaveBeenCalledWith(0, 0, 480, 0);
    expect(context.shadowBlur).toBe(8);

    const particles = createParticles(
      [{ x: 0, y: 5 }, { x: 100, y: 5 }],
      { random: () => 0.5, stagger: true }
    );
    expect(particles[1].delay).toBeGreaterThan(particles[0].delay);
  });

  it("leaves the HTML text visible when there is no canvas context", () => {
    getContextSpy.mockReturnValue(null);

    render(<ParticleHeadline text="Plain fallback" />);

    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading.textContent).toBe("Plain fallback");
    expect(heading.classList.contains("is-canvas-active")).toBe(false);
    expect(raf.request).not.toHaveBeenCalled();
  });

  it("does not animate under reduced motion, and starts cleanly when it is disabled", () => {
    motionQuery.matches = true;
    render(<ParticleHeadline text={HEADLINE} />);

    expect(raf.request).not.toHaveBeenCalled();
    expect(getContextSpy).not.toHaveBeenCalled();
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading.classList.contains("is-canvas-active")).toBe(false);

    act(() => {
      motionQuery.matches = false;
      motionQuery.listeners.forEach((listener) => listener({ matches: false }));
    });
    expect(raf.queue.size).toBe(1);
    expect(heading.classList.contains("is-canvas-active")).toBe(true);

    const activeId = [...raf.queue.keys()][0];
    act(() => {
      motionQuery.matches = true;
      motionQuery.listeners.forEach((listener) => listener({ matches: true }));
    });
    expect(raf.cancel).toHaveBeenCalledWith(activeId);
    expect(raf.queue.size).toBe(0);
    expect(heading.classList.contains("is-canvas-active")).toBe(false);
    expect(visibleContext().clearRect).toHaveBeenCalled();
  });

  it("repels nearby particles and springs them back to their exact targets", () => {
    const targets = [
      { x: 100, y: 100 },
      { x: 300, y: 100 },
    ];
    const particles = createParticles(targets, { random: () => 0.5 });
    const pointer = { x: 0, y: 0, active: false };

    for (let index = 0; index < 120; index += 1) advanceParticles(particles, pointer);
    const settledX = particles[0].x;
    expect(Math.abs(settledX - 100)).toBeLessThan(1);

    pointer.x = 112;
    pointer.y = 100;
    pointer.active = true;
    for (let index = 0; index < 6; index += 1) advanceParticles(particles, pointer);
    expect(particles[0].x).toBeLessThan(settledX - 5);

    pointer.active = false;
    for (let index = 0; index < 60; index += 1) advanceParticles(particles, pointer);
    expect(Math.abs(particles[0].x - 100)).toBeLessThan(1);
    expect(Math.abs(particles[0].y - 100)).toBeLessThan(1);
  });

  it("changes the drawn particles on pointer move and smooths them back on leave", () => {
    render(<ParticleHeadline text="Pointer text" />);
    settle(100);

    const context = visibleContext();
    const before = context.arcs.map(({ x, y }) => ({ x, y }));
    expect(before.length).toBeGreaterThan(0);

    dispatchPointer("pointermove", 6, 0);
    settle(8);
    const displaced = context.arcs.map(({ x, y }) => ({ x, y }));
    expect(displaced[0].x).toBeLessThan(before[0].x - 1);

    dispatchPointer("pointerleave", 6, 0);
    settle(140);
    const returned = context.arcs.map(({ x, y }) => ({ x, y }));
    expect(Math.abs(returned[0].x - before[0].x)).toBeLessThan(1.5);
    expect(Math.abs(returned[0].y - before[0].y)).toBeLessThan(1.5);
  });

  it("re-samples on resize and when the editable text changes", () => {
    const { rerender } = render(<ParticleHeadline text="First headline" />);
    const initial = imageSampleCount();
    expect(initial).toBeGreaterThan(0);

    layout.heading = rect(520, 120);
    observers[0].callback([{ target: document.querySelector(".particle-headline") }]);
    const afterResize = imageSampleCount();
    expect(afterResize).toBeGreaterThan(initial);

    rerender(<ParticleHeadline text="Second headline" />);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Second headline");
    expect(imageSampleCount()).toBeGreaterThan(afterResize);
  });

  it("uses the window resize fallback when ResizeObserver is unavailable", () => {
    delete window.ResizeObserver;
    render(<ParticleHeadline text={HEADLINE} />);
    const initial = imageSampleCount();

    layout.heading = rect(400, 120);
    window.dispatchEvent(new Event("resize"));

    expect(imageSampleCount()).toBeGreaterThan(initial);
  });

  it("pauses for hidden documents and resumes when visible", () => {
    let hidden = false;
    Object.defineProperty(document, "hidden", {
      configurable: true,
      get: () => hidden,
    });
    try {
      render(<ParticleHeadline text={HEADLINE} />);
      const activeId = [...raf.queue.keys()][0];

      hidden = true;
      document.dispatchEvent(new Event("visibilitychange"));
      expect(raf.cancel).toHaveBeenCalledWith(activeId);
      const pendingWhileHidden = [...raf.queue.keys()];
      expect(pendingWhileHidden).toHaveLength(0);

      hidden = false;
      document.dispatchEvent(new Event("visibilitychange"));
      expect(raf.queue.size).toBe(1);
    } finally {
      delete document.hidden;
    }
  });

  it("cleans up RAF, observers and listeners on unmount (including StrictMode remounts)", () => {
    const removeSpy = vi.spyOn(EventTarget.prototype, "removeEventListener");
    const { unmount } = render(
      <StrictMode>
        <ParticleHeadline text={HEADLINE} />
      </StrictMode>
    );

    // StrictMode's first effect is fully torn down before the second one runs.
    expect(raf.cancel).toHaveBeenCalled();
    expect(raf.queue.size).toBe(1);
    const activeId = [...raf.queue.keys()][0];

    unmount();

    expect(raf.cancel).toHaveBeenCalledWith(activeId);
    expect(raf.queue.size).toBe(0);
    expect(observers.some((observer) => observer.disconnected)).toBe(true);
    expect(motionQuery.removeEventListener).toHaveBeenCalledWith(
      "change",
      expect.any(Function)
    );
    const removedTypes = removeSpy.mock.calls.map(([type]) => type);
    for (const type of [
      "pointermove",
      "pointerdown",
      "pointerleave",
      "pointercancel",
      "pointerup",
      "visibilitychange",
    ]) {
      expect(removedTypes).toContain(type);
    }
    expect(visibleContext().clearRect).toHaveBeenCalled();
  });
});
