import './App.css';
import Viewer from './pages/viewer/Viewer';
import { Routes, Route } from 'react-router-dom';
import Statistics from './pages/statistics/Statistics';
import SkillsManager from './pages/skillsManager/SkillsManager';

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<Viewer />} />
        <Route path="/skills-manager" element={<SkillsManager />} />
        <Route path="/statistics" element={<Statistics />} />
      </Routes>
    </div>
  );
}

export default App;
