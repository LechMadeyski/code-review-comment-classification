import { monaco, h, useEffect, useRef, useCallback } from "./lib.js";

/** @param {HTMLElement} container */
function createEditor(container) {
  return monaco.editor.createDiffEditor(container, {
    automaticLayout: true,
    contextmenu: false,
    diffAlgorithm: "advanced",
    domReadOnly: true,
    experimental: {
      showEmptyDecorations: true,
      showMoves: true,
    },
    folding: false,
    hideUnchangedRegions: {
      enabled: true,
    },
    ignoreTrimWhitespace: false,
    readOnly: true,
    renderFinalNewline: "on",
    renderOverviewRuler: false,
    theme: "vs-dark",
  });
}

/**
 * @param {number} startLine
 * @param {number} endLine
 */
function createCommentRangeDecorations(startLine, endLine) {
  return [
    {
      range: new monaco.Range(startLine, 0, endLine, 0),
      options: {
        isWholeLine: true,
        className: "comment-range",
      },
    },
  ];
}

/**
 * @param {string} content
 * @param {number} lineNumber
 */
function createCommentContentWidget(content, lineNumber) {
  return {
    getId: () => "comment-content",
    getDomNode: () => {
      const div = document.createElement("div");
      div.classList.add("comment-content");
      div.innerText = content;
      return div;
    },
    getPosition: () => ({
      position: {
        lineNumber,
        column: 0,
      },
      preference: [monaco.editor.ContentWidgetPositionPreference.BELOW],
    }),
  };
}

/**
 * @param {{ target: import("./api.js").TargetDto }} props
 */
export function Editor({ target }) {
  const editorRef = useRef(null);

  const divRef = useCallback((div) => {
    if (!editorRef.current) {
      editorRef.current = createEditor(div);
    }
  }, []);

  useEffect(() => {
    const original = monaco.editor.createModel(target.oldCode, "python");
    const modified = monaco.editor.createModel(target.newCode, "python");

    const editor = editorRef.current;
    const sideEditor =
      target.side === "REVISION"
        ? editor.getModifiedEditor()
        : editor.getOriginalEditor();

    editor.setModel({ original, modified });

    sideEditor.createDecorationsCollection(
      createCommentRangeDecorations(target.startLine, target.endLine)
    );
    sideEditor.addContentWidget(
      createCommentContentWidget(target.content, target.endLine)
    );
    setTimeout(() => sideEditor.revealLineInCenter(target.endLine), 100); // NOTE: Hack to ensure the editor is fully rendered
  }, [
    target.oldCode,
    target.newCode,
    target.startLine,
    target.endLine,
    target.content,
  ]);

  return h("div", {
    className: "editor",
    ref: divRef,
  });
}
