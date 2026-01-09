import './App.css';
import Viewer from './pages/Viewer';
import HeaderMenu from './components/HeaderMenu';

import { Routes, Route } from 'react-router-dom';
import Statistics from './pages/Statistics';

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
        <Route path="/statistics" element={<Statistics />} />
      </Routes>
    </div>
  );
}

export default App;
