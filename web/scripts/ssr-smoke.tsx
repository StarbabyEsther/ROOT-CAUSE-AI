/**
 * Render smoke test: renders every page to static HTML with Node.
 * Catches runtime errors (undefined access, bad hooks, broken imports) without a browser.
 *
 *   npx vite build --ssr scripts/ssr-smoke.tsx --outDir .ssr-smoke --emptyOutDir
 *   node .ssr-smoke/ssr-smoke.js
 */
import { renderToString } from "react-dom/server";
import { Route, Routes, StaticRouter } from "react-router";
import Home from "../src/pages/Home";
import Lab from "../src/pages/Lab";
import Investigation from "../src/pages/Investigation";
import Architecture from "../src/pages/Architecture";
import About from "../src/pages/About";
import NotFound from "../src/pages/NotFound";
import { Layout } from "../src/components/Layout";

const ROUTES = [
  { url: "/", path: "/", element: <Home /> },
  { url: "/lab", path: "/lab", element: <Lab /> },
  { url: "/lab/duplicate_transaction", path: "/lab/:scenarioId", element: <Investigation /> },
  { url: "/lab/incorrect_refund", path: "/lab/:scenarioId", element: <Investigation /> },
  { url: "/lab/monetary_precision", path: "/lab/:scenarioId", element: <Investigation /> },
  { url: "/architecture", path: "/architecture", element: <Architecture /> },
  { url: "/about", path: "/about", element: <About /> },
  { url: "/nope", path: "*", element: <NotFound /> },
];

let failures = 0;

for (const route of ROUTES) {
  try {
    const html = renderToString(
      <StaticRouter location={route.url}>
        <Routes>
          <Route element={<Layout />}>
            <Route path={route.path} element={route.element} />
          </Route>
        </Routes>
      </StaticRouter>,
    );
    const text = html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
    if (text.length < 200) throw new Error(`suspiciously short output: ${text}`);
    console.log(`ok   ${route.url.padEnd(30)} ${String(html.length).padStart(6)} chars | ${text.slice(0, 60)}`);
  } catch (error) {
    failures += 1;
    console.error(`FAIL ${route.url}`, error);
  }
}

console.log(failures === 0 ? "\nAll routes rendered." : `\n${failures} route(s) failed.`);
if (failures > 0) process.exitCode = 1;
