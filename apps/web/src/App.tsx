import './App.css';
import Viewer from './pages/viewer/Viewer';
import HeaderMenu from './pages/common/components/HeaderMenu';

import { Routes, Route } from 'react-router-dom';
import Statistics from './pages/statistics/Statistics';
import SkillsManager from './pages/skillsManager/SkillsManager';

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={
          <>
            <header className="app-header">
              <h1>AI Job Search</h1>
              <HeaderMenu />
            </header>
            <main className="app-main">
              <Viewer />
            </main>
          </>
        } />
        <Route path="/skills-manager" element={<SkillsManager />} />
        <Route path="/statistics" element={<Statistics />} />
      </Routes>
    </div>
  );
}

export default App;
