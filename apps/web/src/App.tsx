import './App.css';
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import LoadingFallback from './components/LoadingFallback';

const Viewer = lazy(() => import('./pages/viewer/Viewer'));
const Statistics = lazy(() => import('./pages/statistics/Statistics'));
const SkillsManager = lazy(() => import('./pages/skillsManager/SkillsManager'));
const Settings = lazy(() => import('./pages/settings/Settings'));

function App() {
  return (
    <div className="app">
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<Viewer />} />
          <Route path="/skills-manager" element={<SkillsManager />} />
          <Route path="/statistics" element={<Statistics />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </div>
  );
}

export default App;
