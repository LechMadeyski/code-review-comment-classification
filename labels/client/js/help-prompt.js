import { h } from "./lib.js";

export function HelpPrompt({ children }) {
  return h("span", { className: "help-prompt" }, "?", h("aside", {}, children));
}
