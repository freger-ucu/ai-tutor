import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App.tsx";
import { GenerationProvider } from "./context/GenerationContext.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <GenerationProvider>
        <App />
      </GenerationProvider>
    </BrowserRouter>
  </StrictMode>
);
