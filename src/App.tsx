import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import RepoSelection from './pages/RepoSelection';
import AnalysisResults from './pages/AnalysisResults';
import AnalysisHistory from './pages/AnalysisHistory';

function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-center" />
      <Routes>
        <Route path="/" element={<RepoSelection />} />
        <Route path="/analysis/:analysisId" element={<AnalysisResults />} />
        <Route path="/history" element={<AnalysisHistory />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
