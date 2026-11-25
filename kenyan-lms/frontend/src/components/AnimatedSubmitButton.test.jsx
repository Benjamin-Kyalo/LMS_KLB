import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AnimatedSubmitButton from "./AnimatedSubmitButton";

describe("AnimatedSubmitButton", () => {
  it("keeps the label readable and restores the normal class after the click animation", () => {
    render(<AnimatedSubmitButton>Sign in</AnimatedSubmitButton>);
    const button = screen.getByRole("button", { name: "Sign in" });

    expect(button.querySelector(".rolling-label-static").textContent).toBe("Sign in");
    expect(button.className).not.toContain("is-pressed");

    fireEvent.click(button);
    expect(button.querySelector(".rolling-label-static").textContent).toBe("Sign in");
    expect(button.className).toContain("is-pressed");

    fireEvent.animationEnd(button, { animationName: "authPress" });
    expect(button.className).not.toContain("is-pressed");
    expect(button.querySelector(".rolling-label-static").textContent).toBe("Sign in");
  });

  it("forwards click handlers and does not animate while disabled", () => {
    const onClick = vi.fn();
    render(<AnimatedSubmitButton disabled onClick={onClick}>Create account</AnimatedSubmitButton>);
    const button = screen.getByRole("button", { name: "Create account" });

    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
    expect(button.className).not.toContain("is-pressed");
    expect(button.querySelector(".rolling-label-static").textContent).toBe("Create account");
  });
});
