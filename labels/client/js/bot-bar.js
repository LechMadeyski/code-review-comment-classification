import { h } from "./lib.js";

import { HelpPrompt } from "./help-prompt.js";

/** @type {{ id: import("./api.js").SkippableLabel, name: string, help: string[] }[]} */
const LABELS = [
  {
    id: "DISCUSS",
    name: "discussion",
    help: [
      "If reviewers ask anything to the code author for clarification.",
      "Review comments that praise, complement or thank the developer.",
    ],
  },
  {
    id: "DOCUMENTATION",
    name: "documentation",
    help: [
      "Review comments that address issues related to code comments or documentation files for aiding code comprehension.",
    ],
  },
  {
    id: "FALSE POSITIVE",
    name: "false positive",
    help: [
      "A CR comment is considered a false positive if the code owner explicitly mentions the comment as an invalid concern.",
    ],
  },
  {
    id: "FUNCTION",
    name: "functional",
    help: [
      "Defects where a code functionality is missing or implemented incorrectly.",
      "Defects where there exist control flow problems or logical mistakes.",
      "All types of user data sanitization issues or issues related to exception handling.",
      "Any kind of variable, memory, or file issues while handling or manipulating them.",
      "Any kind of synchronization issues while using threads.",
      "Any kind of support system related issues (e.g., configuration problem or version mismatch).",
      "Any types of interfacing issues such as issues in import statements or database access issues.",
    ],
  },
  {
    id: "REFACTORING",
    name: "refactoring",
    help: [
      "Review comments that suggest an alternative approach for problem-solving.",
      "Review comments that address issues within outputs (including error messages) shown to the users.",
      "Code organization or refactoring issues presented in the catalog of Martin Fowler.",
      "Review comments that address the violation of the variable naming convention.",
      "Any kind of formatting (indentation, blank line, or code spacing-related) issues.",
    ],
  },
  {
    id: "SKIP",
    name: "SKIP",
    help: [
      "The context given to the annotator is not sufficient to label the comment.",
      "This label should be used even if the annotator is only a bit unsure, to maintain good data quality.",
      "It is possible, or even likely, that you might want to skip most of the comments.",
    ],
  },
];

export function BotBar({ onLabel, disabled }) {
  return h(
    "div",
    { className: "bot-bar" },
    ...LABELS.map((label) =>
      h(
        "div",
        { key: label.id },
        h(
          "button",
          {
            ["data-label"]: label.id,
            className: "label-button",
            disabled: disabled && label.id !== "SKIP",
            onClick: () => onLabel(label.id),
          },
          label.name
        ),
        h(
          HelpPrompt,
          {},
          h("ul", {}, ...label.help.map((text) => h("li", { key: text }, text)))
        )
      )
    )
  );
}
