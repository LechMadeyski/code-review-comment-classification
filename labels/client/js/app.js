import { h, useState, useEffect, useReducer, Fragment } from "./lib.js";

import { getCurrentTarget, annotateCurrentTarget } from "./api.js";
import { TopBar } from "./top-bar.js";
import { Editor } from "./editor.js";
import { BotBar } from "./bot-bar.js";
import { useReadingLock } from "./reading-lock.js";

export function App() {
  const [target, setTarget] = useState(null);
  const [counter, increment] = useReducer((c) => c + 1, 0);

  useEffect(() => {
    setTarget(null);
    getCurrentTarget().then(setTarget);
  }, [counter]);

  const locked = useReadingLock(target?.content);

  /** @param {string} label */
  const handleLabel = (label) => {
    annotateCurrentTarget(label).then(() => increment());
  };

  return h(
    Fragment,
    {},
    h(TopBar, { id: target?.id, url: target?.url }),
    target ? h(Editor, { target }) : h("div", { className: "editor" }),
    h(BotBar, { onLabel: handleLabel, disabled: locked || !target })
  );
}
