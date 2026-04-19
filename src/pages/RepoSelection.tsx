import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchUserAttributes } from 'aws-amplify/auth';
import toast from 'react-hot-toast';
import Navbar from '../components/Navbar';
import ParticleBackground from '../components/ParticleBackground';
import { useAuth } from '../contexts/AuthContext';
import { fetchRepos, fetchAnalyses, runAnalysis, Repo } from '../api';
import './RepoSelection.css';

const RepoSelection: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading, error: authError, signIn, clearError } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [repos, setRepos] = useState<Repo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [signInLoading, setSignInLoading] = useState(false);
  const [reposInProgress, setReposInProgress] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      fetchRepos()
        .then((data) => setRepos(data.repos))
        .catch((err) => {
          console.error('Failed to load repos', err);
        });
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const loadInProgress = () => {
      fetchAnalyses()
        .then((data) => {
          const inProgress = new Set(
            data.analyses.filter((a) => a.status === 'in_progress').map((a) => a.repo)
          );
          setReposInProgress(inProgress);
        })
        .catch(() => {});
    };
    loadInProgress();
    const interval = setInterval(loadInProgress, 10000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) clearError();
  }, [isAuthenticated, clearError]);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password || signInLoading) return;
    setSignInLoading(true);
    try {
      await signIn(username.trim(), password);
      setPassword('');
    } catch {
      // error set in AuthContext
    } finally {
      setSignInLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!selectedRepo || isLoading) return;
    setIsLoading(true);
    try {
      let initiatedBy: string | undefined;
      try {
        const attrs = await fetchUserAttributes();
        initiatedBy = (attrs as { email?: string })?.email ?? undefined;
      } catch {
        initiatedBy = undefined;
      }
      const { analysis_id } = await runAnalysis(selectedRepo, initiatedBy);
      toast.success('Analysis complete! Notification sent.');
      navigate(`/analysis/${analysis_id}`);
    } catch (err) {
      console.error('Failed to start analysis', err);
      setIsLoading(false);
    }
  };

  const showSignIn = !authLoading && !isAuthenticated;
  const showRepoSelect = !authLoading && isAuthenticated;

  return (
    <div className="repo-selection-page">
      <ParticleBackground />
      <Navbar />
      <div className="repo-selection-content">
        <div className="repo-selection-card-wrap">
          <div className="repo-selection-card">
            {authLoading && (
              <>
                <label className="repo-selection-label">Loading…</label>
                <div className="repo-selection-divider" aria-hidden />
              </>
            )}
            {showSignIn && (
              <>
                <label className="repo-selection-label">Sign In</label>
                <div className="repo-selection-divider" aria-hidden />
                <form className="repo-selection-signin-form" onSubmit={handleSignIn}>
                  <input
                    type="text"
                    className="repo-selection-input"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    autoComplete="username"
                    disabled={signInLoading}
                  />
                  <input
                    type="password"
                    className="repo-selection-input"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    disabled={signInLoading}
                  />
                  {authError && (
                    <p className="repo-selection-error" role="alert">
                      {authError}
                    </p>
                  )}
                  <div className="repo-selection-row">
                    <button
                      type="submit"
                      className="repo-selection-button repo-selection-signin-button"
                      disabled={!username.trim() || !password || signInLoading}
                    >
                      {signInLoading ? 'Signing in…' : 'Sign In'}
                    </button>
                  </div>
                </form>
              </>
            )}
            {showRepoSelect && (
              <>
                <label className="repo-selection-label">Select Repository</label>
                <div className="repo-selection-divider" aria-hidden />
                <div className="repo-selection-row">
                  <select
                    className="repo-selection-dropdown"
                    value={selectedRepo}
                    onChange={(e) => setSelectedRepo(e.target.value)}
                  >
                    <option value="">Select a repository...</option>
                    {repos.map((repo) => (
                      <option key={repo.full_name} value={repo.full_name}>
                        {repo.full_name}
                      </option>
                    ))}
                  </select>
                  <button
                    className="repo-selection-button"
                    disabled={
                      !selectedRepo ||
                      isLoading ||
                      reposInProgress.has(selectedRepo)
                    }
                    onClick={handleRunAnalysis}
                  >
                    {isLoading
                      ? 'Running Analysis...'
                      : reposInProgress.has(selectedRepo)
                        ? 'Analysis in progress'
                        : 'Run Analysis'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RepoSelection;
