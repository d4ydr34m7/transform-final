import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { fetchAnalyses, AnalysisMetadata } from '../api';
import './AnalysisHistory.css';

const AnalysisHistory: React.FC = () => {
  const [analyses, setAnalyses] = useState<AnalysisMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchAnalyses()
      .then((data) => {
        setAnalyses(data.analyses);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load analyses', err);
        setIsLoading(false);
      });
  }, []);

  const handleRowClick = (analysisId: string) => {
    navigate(`/analysis/${analysisId}`);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch {
      return dateString;
    }
  };

  return (
    <div className="analysis-history-page">
      <Navbar />
      <div className="analysis-history-content">
        <h1 className="analysis-history-title">Analysis History</h1>
        
        {isLoading ? (
          <div className="analysis-history-loading">Loading analyses...</div>
        ) : analyses.length === 0 ? (
          <div className="analysis-history-empty">No analyses found.</div>
        ) : (
          <table className="analysis-history-table">
            <thead>
              <tr>
                <th>Analysis ID</th>
                <th>Repository</th>
                <th>Created At</th>
                <th>Status</th>
                <th>Initiated by</th>
              </tr>
            </thead>
            <tbody>
              {analyses.map((analysis) => (
                <tr
                  key={analysis.analysis_id}
                  onClick={() => handleRowClick(analysis.analysis_id)}
                  className="analysis-history-row"
                >
                  <td>{analysis.analysis_id}</td>
                  <td>{analysis.repo}</td>
                  <td>{formatDate(analysis.created_at)}</td>
                  <td>{analysis.status}</td>
                  <td>{analysis.initiated_by ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AnalysisHistory;
