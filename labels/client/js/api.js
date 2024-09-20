/**
 * @typedef {{
 *   url: string,
 *   startLine: number,
 *   endLine: number,
 *   content: string,
 *   side: "PARENT" | "REVISION",
 *   oldCode: string,
 *   newCode: string,
 * }} TargetDto
 */

/**
 * @typedef {{
 *   currentAnnotatorEmail: string,
 *   kirpendorffAlpha: number,
 *   totalReadyCount: number,
 *   annotatedByCurrentCount: number
 * }} InfoDto
 */

/**
 * @typedef {"DISCUSS" | "DOCUMENTATION" | "FALSE POSITIVE" | "FUNCTION" | "REFACTORING" | "SKIP"} SkippableLabel
 */

/** @param {string} url */
const get = (url) => () => fetch(url).then((res) => res.json());

/** @type {() => Promise<TargetDto>} */
export const getCurrentTarget = get("/api/target");

/** @type {() => Promise<InfoDto>} */
export const getInfo = get("/api/info");

/** @type {(label: SkippableLabel) => Promise<void>} */
export const annotateCurrentTarget = (label) =>
  fetch(`/api/target?label=${label}`, { method: "PUT" });
