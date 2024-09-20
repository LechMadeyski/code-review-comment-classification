Usage:

```bash
python -m features
```

# Index of dataset features

- an unlabeled column containing instance indices
- **`meta.`** - metadata which aids in instance identification and debugging, but should **not** be used as model inputs
  - **`comment_id`** (`str`) - a unique identifier of the dataset instance
  - **`url`** (`str`) - a link to the location of the comment on Gerrit
  - **`label`** (`str`) - the correct output of the model for the instance; one of:
    - `DISCUSS` - discussion; comments which discuss the design, ask a question, or give praise
    - `DOCUMENTATION` - comments which address issues related to code comments or documentation files
    - `FALSE POSITIVE` - comments explicitly marked by the code owner as invalid concerns
    - `FUNCTION` - functional issues; defects where functionality is missing or implemented incorrectly
    - `REFACTORING` - comments which suggest an alternative solution to a problem
  - **`start_line`** (`int | None`) - the first line, selected by the comment author; 1-indexed, inclusive, `None` if comment is file-scoped
  - **`end_line`** (`int | None`) - the last line, selected by the comment author; 1-indexed, inclusive, `None` if comment is file-scoped
- **`comment.`** - the data describing the comment's location and contents
  - **`text`** (`str`) - the full textual content of the comment
  - **`side`** (`str`) - the side, on which the comment was left; one of:
    - `PARENT` - the comment was placed on the left side (old code)
    - `REVISION` - the comment was placed on the right side (new code)
  - **`len`** (`int`) - the length of `comment.text` (in characters)
- **`code.`** - the data describing the source code under which the comment was left
  - **`old.`** - metrics describing the code from before the changes were made
    - **CODE_METRICS** - see the section below
  - **`new.`** - metrics describing the code from after the changes were made
    - **CODE_METRICS** - see the section below
  - **`range.`** - the code within the range selected by the comment author; this might not form a correct AST
    - **`text`** (`str`) - the full textual content of the code within the selected range
    - **`volume`** (`float`) - the ratio of `code.range.lines` to the number of lines in the file
    - **`len`** (`int`) - the length of `code.range.text` (in characters)
    - **`lines`** (`int`) - the count of lines in `code.range.text`
  - **`context.`** - comment code context; see the section below
    - **`text`** (`str`) - the full textual content of the comment code context
    - **`volume`** (`float`) - the ratio of `code.context.lines` to the number of lines in the file
    - **CODE_METRICS** - see the section below
  - **`diff.`** - differences between the metrics of `code.new` and `code.old` (e.g. `code.diff.cyc_comp == code.new.cyc_comp - code.old.cyc_comp`)
    - **CODE_METRICS** - see the section below
- **`changes.`** - the data describing previous changes made to the comment's file
  - **`count`** - total number of prior changes made to the file
  - **`unique_authors`** - count of unique change contributors to the file
  - **`by_owner.`** - prior changes made by the current change's owner
    - **`count`** - number of prior changes to this file, made by the current change's owner
    - **`volume`** - `changes.by_owner.count / changes.count`
  - **`by_reviewer.`** - prior changes made by the current comment's author
    - **`count`** - number of prior changes to this file, made by the current comment's author
    - **`volume`** - `changes.by_reviewer.count / changes.count`

## The structure of CODE_METRICS

- **`len`** (`int`) - the length of the relevant code (in characters)
- **`lines`** (`int`) - the count of lines in the relevant code
- **`cyc_comp`** (`int`) - the cyclomatic complexity of the relevant code (sum of complexities of all functions)
- **`nodes.`** - counts of particular node types in the AST
  - **`all`** (`int`) - the total count of all statement and expression AST nodes
  - **NODE_TYPES** - see the section below
- **`volumes.`** - `nodes.SOME_TYPE / nodes.all` for every `SOME_TYPE` in NODE_TYPES
  - **NODE_TYPES** - see the section below
- **`by_owner.`** - current change owner's involvement in the file
  - **`lines`** - the count of lines in the relevant code, which were last touched by change owner (according to blame)
  - **`volume`** - `by_owner.lines / lines`
- **`by_reviewer.`** - current comment author's involvement in the file
  - **`lines`** - the count of lines in the relevant code, which were last touched by comment author (according to blame)
  - **`volume`** - `by_reviewer.lines / lines`

### The list of all NODE_TYPES

- **`.functions`** - one of: `FunctionDef`, `AsyncFunctionDef`
- **`.classes`** - `ClassDef`
- **`.loops`** - one of: `For`, `AsyncFor`, `While`
- **`.conditions`** - one of: `If`, `Match`, `Assert`
- **`.resources`** - one of: `With`, `AsyncWith`, `Try`
- **`.assigns`** - one of: `Assign`, `AugAssign`, `AnnAssign`, `Delete`
- **`.breaks`** - one of: `Return`, `Raise`, `Break`, `Continue`
- **`.imports`** - one of: `Import`, `ImportFrom`
- **`.docstrs`** - `e` is `Expr`, `e.value` is `Constant` and `e.value.value` is `str`
- **`.voidexprs`** - `Expr`, which is not a docstring
- **`.ariths`** - one of: `Add`, `Sub`, `Mul`, `MatMult`, `Div`, `Mod`, `Pow`, `FloorDiv`, `UAdd`, `USub`
- **`.logics`** - one of: `And`, `Or`, `Not`
- **`.comps`** - one of: `Eq`, `NotEq`, `Lt`, `LtE`, `Gt`, `GtE`, `Is`, `IsNot`
- **`.calls`** - `Call`
- **`.literals`** - `Constant`

## Comment code context

The comment code context (CCC) is the fragment of code which aims to be most relevant to the comment message.

In the Turzo 2023 publication, this was always equal to the last line of the comment's range, the ten lines preceding this line and the ten lines succeeding this line. It led to the inclusion of irrelevant info in the context. For instance, a common case is a comment targeting the name in a function definition. In that case the context would include up to 10 lines of the function body, but also 10 completely irrelevant lines (the ones above the function definition). The context also didn't have to form a valid Python AST, which made it hard to calculate metrics relevant to it. The related text fragment is not formatted apart from dedenting. We aim to return entire functions whenever possible, since CodeBERT was trained on such input.

The pseudocode for the proposed context extraction is as follows:

1. If the comment range is missing (the comment refers to the entire file), **return** an empty module node.
2. Create a list of all statement AST nodes, which contain the entire comment range, going from to root to the leafs.
3. If the list is empty, **return** the entire AST.
4. If the list has any functions, **return** the smallest one.
5. Find the list's element `ELEM`, which has the length (`n.end_lineno - n.lineno + 1`) closest to 20.
6. If `ELEM` statement has less than 100 lines, **return** it.
7. Find an expression node inside `ELEM`, which has the length closest to 20 and **return** it.
