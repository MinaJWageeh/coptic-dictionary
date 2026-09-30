import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it, vi } from "vitest";
import { ResourceForm } from "./resource-form";
import { getResource } from "@/lib/resource-config";

describe("ResourceForm", () => {
  it("validates admin dictionary form before submit", async () => {
    const resource = getResource("dictionary");
    if (!resource) throw new Error("dictionary resource missing");
    const onSubmit = vi.fn();

    render(
      React.createElement(ResourceForm, {
        fields: resource.fields,
        schema: resource.schema,
        submitLabel: "Create",
        onSubmit
      })
    );

    await userEvent.click(screen.getByRole("button", { name: /Create/ }));

    expect((await screen.findAllByText("Required")).length).toBeGreaterThan(0);
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
