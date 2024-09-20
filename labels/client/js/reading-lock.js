import { useState, useEffect } from "./lib.js";

const WPM = 500;
const MIN_LOCK_MS = 1000;

/** @param {string | null} text */
const wordCount = (text) => (text ?? "").match(/\w+/g)?.length ?? 0;

/** @param {string | null} text */
const readingTimeMs = (text) =>
  Math.max((wordCount(text) / WPM) * 60_000, MIN_LOCK_MS);

/** @param {string | null} text */
export function useReadingLock(text) {
  const [locked, setLocked] = useState(true);

  useEffect(() => {
    setLocked(true);
    const timeout = setTimeout(() => setLocked(false), readingTimeMs(text));
    return () => clearTimeout(timeout);
  }, [text]);

  return locked;
}
