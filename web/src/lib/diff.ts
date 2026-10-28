/** Minimal line diff (LCS) producing paired side-by-side rows with inline marks. */

export interface DiffLine {
  text: string;
  number: number;
  /** Character range inside `text` that changed, for inline highlighting. */
  mark?: [number, number];
}

export interface DiffRow {
  kind: "same" | "change" | "left-only" | "right-only";
  left?: DiffLine;
  right?: DiffLine;
}

type Op =
  | { type: "same"; text: string; number: number }
  | { type: "del"; text: string; number: number }
  | { type: "ins"; text: string; number: number };

const lcsMatrix = (a: string[], b: string[]): number[][] => {
  const matrix: number[][] = Array.from({ length: a.length + 1 }, () =>
    new Array<number>(b.length + 1).fill(0),
  );
  for (let i = a.length - 1; i >= 0; i -= 1) {
    for (let j = b.length - 1; j >= 0; j -= 1) {
      matrix[i][j] =
        a[i] === b[j] ? matrix[i + 1][j + 1] + 1 : Math.max(matrix[i + 1][j], matrix[i][j + 1]);
    }
  }
  return matrix;
};

/** Trim the shared prefix/suffix to locate the characters that actually differ. */
function inlineMark(before: string, after: string): { left: [number, number]; right: [number, number] } {
  let start = 0;
  while (start < before.length && start < after.length && before[start] === after[start]) start += 1;

  let endBefore = before.length;
  let endAfter = after.length;
  while (endBefore > start && endAfter > start && before[endBefore - 1] === after[endAfter - 1]) {
    endBefore -= 1;
    endAfter -= 1;
  }
  return { left: [start, endBefore], right: [start, endAfter] };
}

function editScript(a: string[], b: string[]): Op[] {
  const matrix = lcsMatrix(a, b);
  const ops: Op[] = [];
  let i = 0;
  let j = 0;

  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      ops.push({ type: "same", text: a[i], number: i + 1 });
      i += 1;
      j += 1;
    } else if (matrix[i + 1][j] >= matrix[i][j + 1]) {
      ops.push({ type: "del", text: a[i], number: i + 1 });
      i += 1;
    } else {
      ops.push({ type: "ins", text: b[j], number: j + 1 });
      j += 1;
    }
  }
  while (i < a.length) {
    ops.push({ type: "del", text: a[i], number: i + 1 });
    i += 1;
  }
  while (j < b.length) {
    ops.push({ type: "ins", text: b[j], number: j + 1 });
    j += 1;
  }
  return ops;
}

export function diffLines(before: string, after: string): DiffRow[] {
  const a = before.replace(/\n+$/, "").split("\n");
  const b = after.replace(/\n+$/, "").split("\n");
  const ops = editScript(a, b);
  const rows: DiffRow[] = [];

  let index = 0;
  while (index < ops.length) {
    const op = ops[index];
    if (op.type === "same") {
      rows.push({
        kind: "same",
        left: { text: op.text, number: op.number },
        right: { text: op.text, number: op.number },
      });
      index += 1;
      continue;
    }

    // Gather the contiguous removal block and the addition block that follows.
    const removed: { text: string; number: number }[] = [];
    const added: { text: string; number: number }[] = [];
    while (index < ops.length && ops[index].type !== "same") {
      const current = ops[index];
      if (current.type === "del") removed.push({ text: current.text, number: current.number });
      else if (current.type === "ins") added.push({ text: current.text, number: current.number });
      index += 1;
    }

    // Pair removed/added lines by similarity so a rewrite reads as one change,
    // not as an unrelated deletion followed by an insertion.
    const scored: { r: number; a: number; score: number }[] = [];
    removed.forEach((left, r) => {
      added.forEach((right, a) => {
        const score = similarity(left.text, right.text);
        if (score >= 0.45) scored.push({ r, a, score });
      });
    });
    scored.sort((x, y) => y.score - x.score);

    const pairedRemoved = new Map<number, number>();
    const pairedAdded = new Set<number>();
    for (const { r, a } of scored) {
      if (pairedRemoved.has(r) || pairedAdded.has(a)) continue;
      pairedRemoved.set(r, a);
      pairedAdded.add(a);
    }

    removed.forEach((left, r) => {
      const a = pairedRemoved.get(r);
      if (a === undefined) {
        rows.push({ kind: "left-only", left: { text: left.text, number: left.number } });
        return;
      }
      const right = added[a];
      const marks = inlineMark(left.text, right.text);
      rows.push({
        kind: "change",
        left: { text: left.text, number: left.number, mark: marks.left },
        right: { text: right.text, number: right.number, mark: marks.right },
      });
    });

    added.forEach((right, a) => {
      if (pairedAdded.has(a)) return;
      rows.push({ kind: "right-only", right: { text: right.text, number: right.number } });
    });
  }

  // A blank line can split a rewrite into two blocks; re-pair across a short gap
  // so the side-by-side view shows one change instead of a stray delete.
  const merged = mergeAcrossGaps(rows);

  // Blank-line shuffling is noise in a side-by-side view.
  return merged.filter((row) => {
    if (row.kind === "same") return true;
    const leftBlank = !row.left || row.left.text.trim() === "";
    const rightBlank = !row.right || row.right.text.trim() === "";
    return !(leftBlank && rightBlank);
  });
}

function mergeAcrossGaps(rows: DiffRow[]): DiffRow[] {
  const working = rows.map((row) => ({ ...row }));
  const rightOnly = working
    .map((row, index) => ({ row, index }))
    .filter(({ row }) => row.kind === "right-only" && row.right);

  for (let i = 0; i < working.length; i += 1) {
    const left = working[i];
    if (left.kind !== "left-only" || !left.left) continue;

    let best: { index: number; score: number } | null = null;
    for (const candidate of rightOnly) {
      if (candidate.index <= i || candidate.index - i > 4) continue;
      if (candidate.row.kind !== "right-only" || !candidate.row.right) continue;
      const score = similarity(left.left.text, candidate.row.right.text);
      if (score >= 0.35 && (!best || score > best.score)) {
        best = { index: candidate.index, score };
      }
    }

    if (best) {
      const right = working[best.index].right!;
      const marks = inlineMark(left.left.text, right.text);
      working[i] = {
        kind: "change",
        left: { text: left.left.text, number: left.left.number, mark: marks.left },
        right: { text: right.text, number: right.number, mark: marks.right },
      };
      working[best.index] = { kind: "same", left: undefined, right: undefined };
    }
  }

  return working.filter((row) => row.kind !== "same" || row.left || row.right);
}

const similarity = (a: string, b: string): number => {
  const left = a.trim();
  const right = b.trim();
  if (!left || !right) return 0;
  let start = 0;
  while (start < left.length && start < right.length && left[start] === right[start]) start += 1;
  let endLeft = left.length;
  let endRight = right.length;
  while (endLeft > start && endRight > start && left[endLeft - 1] === right[endRight - 1]) {
    endLeft -= 1;
    endRight -= 1;
  }
  const shared = start + (left.length - endLeft);
  return (2 * shared) / (left.length + right.length);
};

export const countChanges = (rows: DiffRow[]) => ({
  added: rows.filter((row) => row.kind === "right-only" || row.kind === "change").length,
  removed: rows.filter((row) => row.kind === "left-only" || row.kind === "change").length,
});
