/**
 * Content smoke test for the investigation panels.
 *
 * The four panels only appear after a replay timeline finishes, so they are not
 * covered by the route-level SSR pass. This renders each panel directly against
 * the recorded fixtures and asserts that the measured values really reach the DOM.
 *
 *   npx vite build --ssr scripts/panel-check.tsx --outDir .ssr-smoke --emptyOutDir
 *   node .ssr-smoke/panel-check.js
 */
import { renderToString } from "react-dom/server";
import { SCENARIOS } from "../src/data/scenarios";
import { RUNS } from "../src/data/runs";
import { FinancialPanel } from "../src/components/FinancialPanel";
import { DiagnosisPanel } from "../src/components/DiagnosisPanel";
import { CodeCompare } from "../src/components/CodeCompare";
import { VerificationPanel } from "../src/components/VerificationPanel";

const text = (markup: string) => markup.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");

let failures = 0;
const expect = (label: string, haystack: string, needle: string) => {
  if (haystack.includes(needle)) {
    console.log(`  ok    ${label}`);
  } else {
    failures += 1;
    console.error(`  FAIL  ${label} — missing "${needle}"`);
  }
};

for (const scenario of SCENARIOS) {
  const run = RUNS[scenario.id];
  console.log(`\n${scenario.id}`);

  const financial = text(renderToString(<FinancialPanel scenario={scenario} financial={run.financial} />));
  expect("discrepancy label", financial, "Discrepancy");
  expect("issue classification", financial, run.financial.issue_type);
  expect("expected total", financial, run.financial.expected_total.replace(/0+$/, "").slice(0, 4));
  expect("transaction ids", financial, scenario.records[0].id);

  const diagnosis = text(renderToString(<DiagnosisPanel run={run} />));
  expect("illustrative badge", diagnosis, "Illustrative");
  expect("no model call note", diagnosis, "no model call");

  const compare = text(renderToString(<CodeCompare code={run.code} />));
  expect("diff source file", compare, run.code.filename);

  const verification = text(
    renderToString(<VerificationPanel run={run} scenario={scenario} />),
  );
  expect("passing verdict", verification, `passes all ${run.verification.reference.ran}`);
  expect("test name", verification, run.verification.tests[0].name);
  expect("execution environment", verification, "Local CPython");
  expect("validator reason", verification, "Structural validation passed");
}

console.log(failures === 0 ? "\nAll panel content checks passed." : `\n${failures} check(s) failed.`);
if (failures > 0) process.exitCode = 1;
