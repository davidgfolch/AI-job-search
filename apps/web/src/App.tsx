import './App.css';
import Viewer from './pages/Viewer';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Job Search</h1>
      </header>
      <main className="app-main">
        <Viewer />
      </main>
    </div>
  );
}

export default App;
