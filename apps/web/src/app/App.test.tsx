import { render, screen } from "@testing-library/react";

import { App } from "./App";

describe("App", () => {
  it("renders the project name and tagline", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "3d-scan" })).toBeInTheDocument();
    expect(screen.getByText(/print-ready 3MF/i)).toBeInTheDocument();
  });
});
