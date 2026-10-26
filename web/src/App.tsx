import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";

// Route-level code splitting keeps the first paint light; the hero ships before
// the investigation dashboard is needed.
const Home = lazy(() => import("./pages/Home"));
const Lab = lazy(() => import("./pages/Lab"));
const Investigation = lazy(() => import("./pages/Investigation"));
const Architecture = lazy(() => import("./pages/Architecture"));
const About = lazy(() => import("./pages/About"));
const NotFound = lazy(() => import("./pages/NotFound"));

function RouteFallback() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <div className="flex items-center gap-3 text-[0.75rem] text-ink-faint">
        <span className="h-3 w-3 animate-spin rounded-full border border-cyan-400/30 border-t-cyan-400" />
        Loading
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="lab" element={<Lab />} />
          <Route path="lab/:scenarioId" element={<Investigation />} />
          <Route path="architecture" element={<Architecture />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
