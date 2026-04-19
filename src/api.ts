const API_BASE = 'http://localhost:8000';

export type Repo = {
  full_name: string;
  private: boolean;
};

export async function fetchRepos(): Promise<{ repos: Repo[] }> {
  const res = await fetch(`${API_BASE}/repos`);
  if (!res.ok) {
    throw new Error('Failed to fetch repos');
  }
  return res.json();
}

export async function runAnalysis(repo: string, initiatedBy?: string): Promise<{ analysis_id: string }> {
  const body: { repo: string; initiated_by?: string } = { repo };
  if (initiatedBy != null && initiatedBy !== '') body.initiated_by = initiatedBy;
  const res = await fetch(`${API_BASE}/analysis/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error('Failed to start analysis');
  }
  return res.json();
}

export async function fetchFiles(analysisId: string): Promise<{ files: string[] }> {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}/files`);
  if (!res.ok) {
    throw new Error('Failed to fetch files');
  }
  return res.json();
}

export async function fetchFile(analysisId: string, fileName: string): Promise<{ content: string }> {
  const params = new URLSearchParams({ path: fileName });
  const res = await fetch(`${API_BASE}/analysis/${analysisId}/file?${params.toString()}`);
  if (!res.ok) {
    throw new Error('Failed to fetch file');
  }
  return res.json();
}

export interface AnalysisMetadata {
  analysis_id: string;
  repo: string;
  created_at: string;
  status: string;
  initiated_by?: string | null;
}

export async function fetchAnalyses(): Promise<{ analyses: AnalysisMetadata[] }> {
  const res = await fetch(`${API_BASE}/analysis`);
  if (!res.ok) {
    throw new Error('Failed to fetch analyses');
  }
  return res.json();
}
