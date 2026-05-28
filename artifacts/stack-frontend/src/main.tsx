import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
import { setupApi } from "./lib/apiSetup";

setupApi();

createRoot(document.getElementById("root")!).render(<App />);
