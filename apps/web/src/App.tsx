import './App.css';
import Viewer from './pages/Viewer';

import { Routes, Route, Link } from 'react-router-dom';
import Statistics from './pages/Statistics';

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={
          <>
            <header className="app-header">
              <h1>AI Job Search</h1>
              <Link to="/statistics" target="_blank" className="header-link">Statistics</Link>
            </header>
            <main className="app-main">
              <Viewer />
            </main>
          </>
        } />
        <Route path="/statistics" element={<Statistics />} />
      </Routes>
    </div>
  );
}

export default App;
