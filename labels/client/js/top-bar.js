import { h, useState, useEffect } from "./lib.js";

import { getInfo } from "./api.js";
import { HelpPrompt } from "./help-prompt.js";

/** @param {{ id: string | null, url: string | null }} props */
export function TopBar({ id, url }) {
  const [info, setInfo] = useState({
    currentAnnotatorEmail: "",
    kirpendorffAlpha: 0.0,
    totalReadyCount: 0,
    annotatedByCurrentCount: 0,
  });

  useEffect(() => {
    getInfo().then(setInfo);
  }, [id]);

  const stats = [
    `Kirpendorff's alpha: ${info.kirpendorffAlpha.toFixed(3)}`,
    `Total ready comments: ${info.totalReadyCount}`,
    `Annotated by current: ${info.annotatedByCurrentCount}`,
  ];

  return h(
    "div",
    { className: "top-bar" },
    h(
      "div",
      {},
      id ? `${id}: ` : "Loading...",
      url ? h("a", { href: url, target: "_blank" }, url.split("/").pop()) : null
    ),
    h(
      "div",
      {},
      info.currentAnnotatorEmail,
      h(
        HelpPrompt,
        {},
        h("ul", {}, ...stats.map((stat) => h("li", { key: stat }, stat)))
      )
    )
  );
}
