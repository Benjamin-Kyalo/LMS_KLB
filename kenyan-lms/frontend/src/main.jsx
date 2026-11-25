import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { ThemeProvider } from "./context/ThemeContext";
import { SiteContentProvider } from "./context/SiteContentContext";
import "./styles/global.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ThemeProvider>
      <SiteContentProvider>
        <App />
      </SiteContentProvider>
    </ThemeProvider>
  </StrictMode>
);
