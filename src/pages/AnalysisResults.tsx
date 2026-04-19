  import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
  import { useParams } from 'react-router-dom';
  import Navbar from '../components/Navbar';
  import { fetchFiles, fetchFile } from '../api';
  import { buildTree, type TreeNode } from '../utils/fileTree';
  import './AnalysisResults.css';

  type FileTreeNodeProps = {
    node: TreeNode;
    pathPrefix: string;
    selectedFile: string | null;
    onSelectFile: (path: string) => void;
    expanded: Set<string>;
    onToggleExpand: (key: string) => void;
    depth: number;
  };

  function FileTreeNode({
    node,
    pathPrefix,
    selectedFile,
    onSelectFile,
    expanded,
    onToggleExpand,
    depth,
  }: FileTreeNodeProps) {
    const folderKey = pathPrefix ? `${pathPrefix}/${node.name}` : node.name;
    const isExpanded = node.isFile ? false : expanded.has(folderKey);

    if (node.isFile) {
      return (
        <div
          role="button"
          tabIndex={0}
          className={`file-item ${selectedFile === node.path ? 'file-item-selected' : ''}`}
          title={node.path}
          onClick={() => onSelectFile(node.path)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onSelectFile(node.path);
            }
          }}
          style={{ paddingLeft: `${1.25 + depth * 1.25}rem` }}
        >
          <span className="file-item-icon file-item-icon-file" aria-hidden />
          {node.name}
        </div>
      );
    }

    const hasChildren = node.children.length > 0;
    return (
      <div className="file-tree-folder" data-depth={depth}>
        <div
          role="button"
          tabIndex={0}
          className="file-tree-folder-header"
          style={{ paddingLeft: `${1.25 + depth * 1.25}rem` }}
          onClick={() => hasChildren && onToggleExpand(folderKey)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              hasChildren && onToggleExpand(folderKey);
            }
          }}
          aria-expanded={hasChildren ? isExpanded : undefined}
        >
          <span
            className={`file-tree-chevron ${hasChildren && isExpanded ? 'file-tree-chevron-open' : ''}`}
            aria-hidden
          />
          <span className="file-item-icon file-item-icon-folder" aria-hidden />
          <span className="file-tree-folder-name">{node.name}</span>
        </div>
        {hasChildren && isExpanded && (
          <div className="file-tree-folder-children">
            {node.children.map((child) => (
              <FileTreeNode
                key={child.isFile ? child.path : folderKey + '/' + child.name}
                node={child}
                pathPrefix={folderKey}
                selectedFile={selectedFile}
                onSelectFile={onSelectFile}
                expanded={expanded}
                onToggleExpand={onToggleExpand}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  const AnalysisResults: React.FC = () => {
    const { analysisId } = useParams<{ analysisId: string }>();

    const [files, setFiles] = useState<string[]>([]);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [content, setContent] = useState<string>('');
    const [loadingFiles, setLoadingFiles] = useState(false);
    const [loadingContent, setLoadingContent] = useState(false);
    const [questionInput, setQuestionInput] = useState('');
    const [chatItems, setChatItems] = useState<Array<{ question: string; answer: string; sources: string[]; isLoading?: boolean }>>([]);
    const [chatLoading, setChatLoading] = useState(false);
    const [chatExpanded, setChatExpanded] = useState(false);
    const [copiedAnswerIdx, setCopiedAnswerIdx] = useState<number | null>(null);
    const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
    const chatAbortRef = useRef<AbortController | null>(null);

    const handleCopyAnswer = useCallback((text: string, idx: number) => {
      navigator.clipboard.writeText(text).then(() => {
        setCopiedAnswerIdx(idx);
        setTimeout(() => setCopiedAnswerIdx(null), 2000);
      });
    }, []);

    const treeNodes = useMemo(() => buildTree(files), [files]);
    const toggleExpand = useCallback((key: string) => {
      setExpandedFolders((prev) => {
        const next = new Set(prev);
        if (next.has(key)) next.delete(key);
        else next.add(key);
        return next;
      });
    }, []);

    // Load file list when analysis changes; clear viewer so we don't show previous analysis's content
    useEffect(() => {
      if (!analysisId) return;

      setSelectedFile(null);
      setContent('');
      setLoadingFiles(true);
      fetchFiles(analysisId)
        .then((res: unknown) => {
          // Normalize response: ensure files is always an array
          let normalizedFiles: string[] = [];
          if (Array.isArray(res)) {
            normalizedFiles = res;
          } else if (res && typeof res === 'object' && res !== null && 'files' in res) {
            const filesValue = (res as { files?: unknown }).files;
            normalizedFiles = Array.isArray(filesValue) ? filesValue : [];
          }
          // Don't show transform logs or VERAMOD-generated summaries in the UI (still in download)
          const hiddenInUI = [
            'transform.log',
            'transform_failed.log',
            'architecture.md',
            'dependencies.md',
            'entrypoints.md',
            'repo_summary.md',
          ];
          setFiles(normalizedFiles.filter((f) => !hiddenInUI.includes(f)));
        })
        .catch((err: unknown) => {
          console.error('Failed to load files', err);
          setFiles([]);
        })
        .finally(() => setLoadingFiles(false));
    }, [analysisId]);

    // Load file content
    const handleFileSelect = async (fileName: string) => {
      if (!analysisId || fileName === '/analysis') return;

      setSelectedFile(fileName);
      setLoadingContent(true);
      setContent('');

      try {
        const res = await fetchFile(analysisId, fileName);
        setContent(res.content || '');
      } catch (err: unknown) {
        console.error('Failed to load file content', err);
        setContent('Failed to load file.');
      } finally {
        setLoadingContent(false);
      }
    };

    const handleDownload = async () => {
      if (!analysisId) return;
      try {
        const res = await fetch(`http://localhost:8000/analysis/${analysisId}/download`);
        if (!res.ok) {
          throw new Error('Failed to download analysis');
        }
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis-${analysisId}.zip`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Download failed', err);
      }
    };

    const CHAT_SESSION_KEY = (id: string) => `veramod_chat_session_${id}`;
    const getOrCreateSessionId = useCallback((id: string): string => {
      const key = CHAT_SESSION_KEY(id);
      let sessionId = localStorage.getItem(key);
      if (!sessionId) {
        sessionId = crypto.randomUUID();
        localStorage.setItem(key, sessionId);
      }
      return sessionId;
    }, []);

    const handleSubmitQuestion = async () => {
      if (!analysisId) return;
      const msg = questionInput.trim();
      if (!msg || chatLoading) return;

      chatAbortRef.current?.abort();
      const controller = new AbortController();
      chatAbortRef.current = controller;
      const timeoutMs = 60000;
      let timeoutId: ReturnType<typeof setTimeout> | null = setTimeout(() => controller.abort(), timeoutMs);

      setQuestionInput('');
      setChatItems((prev) => [
        ...prev,
        { question: msg, answer: '', sources: [], isLoading: true },
      ]);
      setChatLoading(true);

      try {
        const sessionId = getOrCreateSessionId(analysisId);
        const res = await fetch(`http://localhost:8000/analysis/${analysisId}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg, session_id: sessionId }),
          signal: controller.signal,
        });
        if (timeoutId != null) {
          clearTimeout(timeoutId);
          timeoutId = null;
        }
        if (!res.ok) {
          throw new Error('Chat request failed');
        }
        const data = (await res.json()) as { answer?: string; sources?: string[] };
        setChatItems((prev) => {
          const next = [...prev];
          const idx = next.findIndex((i) => i.isLoading);
          if (idx !== -1) {
            next[idx] = {
              ...next[idx],
              answer: data.answer ?? '',
              sources: Array.isArray(data.sources) ? data.sources : [],
              isLoading: false,
            };
          }
          return next;
        });
      } catch (err) {
        if (timeoutId != null) clearTimeout(timeoutId);
        const isAborted = err instanceof Error && err.name === 'AbortError';
        if (!isAborted) {
          console.error('Chat failed', err);
        }
        setChatItems((prev) => {
          const next = [...prev];
          const idx = next.findIndex((i) => i.isLoading);
          if (idx !== -1) {
            next[idx] = {
              ...next[idx],
              answer: isAborted ? 'Response cancelled.' : 'Unable to fetch answer right now.',
              sources: [],
              isLoading: false,
            };
          }
          return next;
        });
      } finally {
        chatAbortRef.current = null;
        setChatLoading(false);
      }
    };

    const handleStopChat = useCallback(() => {
      chatAbortRef.current?.abort();
    }, []);

    const handleChatKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSubmitQuestion();
      }
    };

    return (
      <div className="analysis-results-page">
        <Navbar />

        <div className="analysis-top-row">
          <div className="analysis-top-text">
            Analysis artifacts are ready
            {analysisId && (
              <span className="analysis-top-id" title="Current analysis"> ({analysisId})</span>
            )}
          </div>
          <button className="analysis-download-button" onClick={handleDownload}>Download Analysis</button>
        </div>

        <div className="analysis-workspace">
          {/* LEFT */}
          <div className="analysis-pane analysis-pane-left">
            <div className="pane-title">ANALYSIS FILES</div>

            <div className="file-tree">
              {loadingFiles && (
                <div className="file-item">Loading files...</div>
              )}

              {!loadingFiles && Array.isArray(files) && files.length === 0 && (
                <div className="file-item">No files</div>
              )}

              {!loadingFiles &&
                treeNodes.length > 0 &&
                treeNodes.map((node) => (
                  <FileTreeNode
                    key={node.isFile ? node.path : node.name}
                    node={node}
                    pathPrefix=""
                    selectedFile={selectedFile}
                    onSelectFile={handleFileSelect}
                    expanded={expandedFolders}
                    onToggleExpand={toggleExpand}
                    depth={0}
                  />
                ))}
            </div>
          </div>

          {/* CENTER */}
          <div className="analysis-pane analysis-pane-center">
            <div className="pane-title">DOCUMENT VIEWER</div>

            <div className="document-viewer-content">
              {!selectedFile && (
                <div className="document-empty">
                  Select a file to view analysis.
                </div>
              )}

              {loadingContent && (
                <div className="document-empty">Loading document...</div>
              )}

              {!loadingContent && selectedFile && (
                <div className="document-content">
                  <pre className="document-text">{content}</pre>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT */}
          <div className={`analysis-pane analysis-pane-right ${chatExpanded ? 'analysis-pane-right--expanded' : ''}`}>
            <div className="pane-title pane-title-with-action">
              <span>ASK QUESTIONS</span>
              <button
                type="button"
                className="chat-expand-button"
                onClick={() => setChatExpanded((e) => !e)}
                title={chatExpanded ? 'Collapse chat' : 'Expand chat'}
                aria-label={chatExpanded ? 'Collapse chat' : 'Expand chat'}
              >
                {chatExpanded ? '⊟' : '⊞'}
              </button>
            </div>
            <div className="chat-content">
              {chatItems.length === 0 ? (
                <div className="chat-empty">No messages yet. Ask a question to get started.</div>
              ) : (
                <div className="chat-messages">
                  {chatItems.map((item, idx) => (
                    <React.Fragment key={idx}>
                      <div className="chat-bubble chat-bubble--user">
                        <span className="chat-bubble-label">You</span>
                        <div className="chat-bubble-text">{item.question}</div>
                      </div>
                      <div className="chat-bubble chat-bubble--assistant">
                        <div className="chat-bubble-header">
                          <span className="chat-bubble-label">Assistant</span>
                          {!item.isLoading && (
                            <button
                              type="button"
                              className="chat-copy-button"
                              onClick={() => handleCopyAnswer(item.answer, idx)}
                              title={copiedAnswerIdx === idx ? 'Copied' : 'Copy response'}
                              aria-label={copiedAnswerIdx === idx ? 'Copied' : 'Copy response'}
                            >
                              {copiedAnswerIdx === idx ? (
                                <svg className="chat-copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                                  <polyline points="20 6 9 17 4 12" />
                                </svg>
                              ) : (
                                <svg className="chat-copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                                </svg>
                              )}
                            </button>
                          )}
                        </div>
                        {item.isLoading ? (
                          <div className="chat-bubble-loading">
                            <span className="chat-bubble-loading-dot" />
                            <span className="chat-bubble-loading-dot" />
                            <span className="chat-bubble-loading-dot" />
                          </div>
                        ) : (
                          <>
                            <div className="chat-bubble-text">{item.answer}</div>
                            {item.sources && item.sources.length > 0 && (
                              <div className="chat-bubble-sources">
                                <span className="chat-bubble-sources-label">Sources:</span>
                                <ul className="chat-bubble-sources-list" aria-label="Sources">
                                  {item.sources.map((src, i) => (
                                    <li key={i}>{src}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </React.Fragment>
                  ))}
                </div>
              )}

              <div className="chat-input-container">
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Ask a question about the analysis..."
                  value={questionInput}
                  onChange={(e) => setQuestionInput(e.target.value)}
                  onKeyDown={handleChatKeyDown}
                  disabled={!analysisId || chatLoading}
                />
                {chatLoading ? (
                  <button
                    type="button"
                    className="chat-stop-button"
                    onClick={handleStopChat}
                    title="Stop generating"
                    aria-label="Stop generating"
                  >
                    <svg className="chat-stop-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                      <rect x="6" y="6" width="12" height="12" rx="2" />
                    </svg>
                  </button>
                ) : (
                  <button
                    type="button"
                    className="chat-submit-button"
                    onClick={handleSubmitQuestion}
                    disabled={!analysisId || questionInput.trim().length === 0}
                  >
                    Submit
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  export default AnalysisResults;
