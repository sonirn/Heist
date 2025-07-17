import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentStep, setCurrentStep] = useState('script');
  const [script, setScript] = useState('');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [selectedVoice, setSelectedVoice] = useState('');
  const [voices, setVoices] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [generationId, setGenerationId] = useState('');
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [generationStatus, setGenerationStatus] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [videoLibrary, setVideoLibrary] = useState([]);
  const [loadingLibrary, setLoadingLibrary] = useState(false);
  const [showLibrary, setShowLibrary] = useState(false);
  const wsRef = useRef(null);
  const sseRef = useRef(null);
  const pollingIntervalRef = useRef(null);

  // Load voices on component mount
  useEffect(() => {
    loadVoices();
  }, []);

  // Enhanced real-time updates with robust fallback system
  useEffect(() => {
    if (generationId && isGenerating) {
      connectRealTimeUpdates();
    }
    return () => {
      disconnectAll();
    };
  }, [generationId, isGenerating]);

  const connectRealTimeUpdates = async () => {
    // Try connections in order of preference: SSE -> WebSocket -> Polling
    let connected = false;
    
    // Try SSE first (most reliable for status updates)
    try {
      await connectSSE();
      connected = true;
      console.log('Connected via SSE');
    } catch (error) {
      console.warn('SSE connection failed, trying WebSocket...', error);
    }
    
    // If SSE fails, try WebSocket
    if (!connected) {
      try {
        await connectWebSocket();
        connected = true;
        console.log('Connected via WebSocket');
      } catch (error) {
        console.warn('WebSocket connection failed, using polling...', error);
      }
    }
    
    // Always start polling as backup (with longer intervals if real-time connection exists)
    startPolling(connected ? 3000 : 1000); // 3s if connected, 1s if not
  };

  const disconnectAll = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
    }
    stopPolling();
  };

  const startPolling = (interval = 1000) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    console.log(`Starting polling with ${interval}ms interval`);
    pollingIntervalRef.current = setInterval(async () => {
      if (generationId && isGenerating) {
        try {
          const response = await fetch(`${BACKEND_URL}/api/generate/${generationId}`);
          if (response.ok) {
            const data = await response.json();
            setProgress(data.progress || 0);
            setProgressMessage(data.message || '');
            setGenerationStatus(data.status || '');
            
            if (data.status === 'completed') {
              // Construct download URL from generation ID
              const downloadUrl = data.video_url || `${BACKEND_URL}/api/download/${generationId}`;
              setVideoUrl(downloadUrl);
              setIsGenerating(false);
              setCurrentStep('result');
              stopPolling();
            } else if (data.status === 'failed') {
              setError(data.message || 'Generation failed');
              setIsGenerating(false);
              stopPolling();
            }
          }
        } catch (error) {
          console.error('Polling error:', error);
          // Don't stop polling on error, just log it
        }
      }
    }, interval);
  };

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const loadVoices = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/voices`);
      if (response.ok) {
        const voicesData = await response.json();
        setVoices(voicesData);
        if (voicesData.length > 0) {
          setSelectedVoice(voicesData[0].voice_id);
        }
      }
    } catch (error) {
      console.error('Failed to load voices:', error);
      // Set default voice if loading fails
      setVoices([{ voice_id: 'default', name: 'Default Voice' }]);
      setSelectedVoice('default');
    }
  };

  const loadVideoLibrary = async () => {
    setLoadingLibrary(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/videos/library`);
      if (response.ok) {
        const libraryData = await response.json();
        setVideoLibrary(libraryData.videos || []);
      } else {
        setError('Failed to load video library');
      }
    } catch (error) {
      console.error('Failed to load video library:', error);
      setError('Failed to load video library');
    } finally {
      setLoadingLibrary(false);
    }
  };

  const downloadVideo = async (generationId, filename) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/download/${generationId}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || `video_${generationId}.mp4`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        setError('Failed to download video');
      }
    } catch (error) {
      console.error('Failed to download video:', error);
      setError('Failed to download video');
    }
  };

  const connectSSE = () => {
    return new Promise((resolve, reject) => {
      if (sseRef.current) {
        sseRef.current.close();
      }

      const sseUrl = `${BACKEND_URL}/api/sse/${generationId}`;
      console.log('Attempting SSE connection to:', sseUrl);
      sseRef.current = new EventSource(sseUrl);

      const timeout = setTimeout(() => {
        reject(new Error('SSE connection timeout'));
      }, 5000); // 5 second timeout

      sseRef.current.onopen = () => {
        clearTimeout(timeout);
        console.log('SSE connection established');
        resolve();
      };

      sseRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setProgress(data.progress || 0);
          setProgressMessage(data.message || '');
          setGenerationStatus(data.status || '');
          
          if (data.status === 'completed') {
            // Construct download URL from generation ID
            const downloadUrl = data.video_url || `${BACKEND_URL}/api/download/${generationId}`;
            setVideoUrl(downloadUrl);
            setIsGenerating(false);
            setCurrentStep('result');
          } else if (data.status === 'failed') {
            setError(data.message || 'Generation failed');
            setIsGenerating(false);
          }
        } catch (e) {
          console.error('SSE data parsing error:', e);
        }
      };

      sseRef.current.onerror = (error) => {
        clearTimeout(timeout);
        console.error('SSE error:', error);
        reject(error);
      };
    });
  };

  const connectWebSocket = () => {
    return new Promise((resolve, reject) => {
      if (wsRef.current) {
        wsRef.current.close();
      }

      const wsUrl = `${BACKEND_URL.replace('http', 'ws')}/api/ws/${generationId}`;
      console.log('Attempting WebSocket connection to:', wsUrl);
      wsRef.current = new WebSocket(wsUrl);

      const timeout = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'));
      }, 5000); // 5 second timeout

      wsRef.current.onopen = () => {
        clearTimeout(timeout);
        console.log('WebSocket connection established');
        resolve();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setProgress(data.progress || 0);
          setProgressMessage(data.message || '');
          setGenerationStatus(data.status || '');
          
          if (data.status === 'completed') {
            // Construct download URL from generation ID
            const downloadUrl = data.video_url || `${BACKEND_URL}/api/download/${generationId}`;
            setVideoUrl(downloadUrl);
            setIsGenerating(false);
            setCurrentStep('result');
          } else if (data.status === 'failed') {
            setError(data.message || 'Generation failed');
            setIsGenerating(false);
          }
        } catch (e) {
          console.error('WebSocket data parsing error:', e);
        }
      };

      wsRef.current.onerror = (error) => {
        clearTimeout(timeout);
        console.error('WebSocket error:', error);
        reject(error);
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket connection closed');
      };
    });
  };

  const handleScriptSubmit = async () => {
    if (!script.trim()) {
      setError('Please enter a script');
      return;
    }

    try {
      setError('');
      
      // Create project
      const projectResponse = await fetch(`${BACKEND_URL}/api/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          script: script.trim(),
          aspect_ratio: aspectRatio,
          voice_id: selectedVoice,
          voice_name: voices.find(v => v.voice_id === selectedVoice)?.name || 'Default'
        }),
      });

      if (!projectResponse.ok) {
        throw new Error('Failed to create project');
      }

      const projectData = await projectResponse.json();
      setProjectId(projectData.project_id);
      setCurrentStep('settings');
    } catch (error) {
      console.error('Error creating project:', error);
      setError('Failed to create project. Please try again.');
    }
  };

  const handleGenerateVideo = async () => {
    if (!projectId) {
      setError('No project found. Please start over.');
      return;
    }

    try {
      setError('');
      setIsGenerating(true);
      setProgress(0);
      setProgressMessage('Starting generation...');
      setCurrentStep('generating');

      // Start generation
      const response = await fetch(`${BACKEND_URL}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: projectId,
          script: script.trim(),
          aspect_ratio: aspectRatio,
          voice_id: selectedVoice
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start generation');
      }

      const data = await response.json();
      setGenerationId(data.generation_id);
      setGenerationStatus(data.status);
    } catch (error) {
      console.error('Error starting generation:', error);
      setError('Failed to start generation. Please try again.');
      setIsGenerating(false);
    }
  };

  const handleStartOver = () => {
    setCurrentStep('script');
    setScript('');
    setProjectId('');
    setGenerationId('');
    setProgress(0);
    setProgressMessage('');
    setGenerationStatus('');
    setVideoUrl('');
    setIsGenerating(false);
    setError('');
    
    if (wsRef.current) {
      wsRef.current.close();
    }
    stopPolling();
  };

  const renderScriptStep = () => (
    <div className="step-container">
      <div className="step-header">
        <h2>✍️ Write Your Script</h2>
        <p>Enter the script you want to convert to video</p>
      </div>
      
      <div className="script-input-container">
        <textarea
          value={script}
          onChange={(e) => setScript(e.target.value)}
          placeholder="Enter your script here... 

For example:
Welcome to our product demo. Today we'll show you how our revolutionary app transforms the way you work. 

First, let's see the beautiful dashboard where all your projects come together in one place.

Next, we'll explore the powerful automation features that save you hours every day.

Finally, we'll demonstrate the real-time collaboration tools that keep your team connected."
          className="script-textarea"
          rows={12}
        />
        
        <div className="script-stats">
          <span>Characters: {script.length}</span>
          <span>Words: {script.trim().split(/\s+/).filter(word => word.length > 0).length}</span>
          <span>Est. Duration: {Math.ceil(script.trim().split(/\s+/).filter(word => word.length > 0).length / 150)} min</span>
        </div>
      </div>

      <div className="action-buttons">
        <button 
          onClick={handleScriptSubmit}
          disabled={!script.trim()}
          className="primary-button"
        >
          Continue to Settings →
        </button>
      </div>
    </div>
  );

  const renderSettingsStep = () => (
    <div className="step-container">
      <div className="step-header">
        <h2>⚙️ Video Settings</h2>
        <p>Configure your video preferences</p>
      </div>

      <div className="settings-grid">
        <div className="setting-group">
          <label>Aspect Ratio</label>
          <div className="aspect-ratio-selector">
            <button
              onClick={() => setAspectRatio('16:9')}
              className={`aspect-button ${aspectRatio === '16:9' ? 'active' : ''}`}
            >
              <div className="aspect-preview landscape"></div>
              <span>16:9 Landscape</span>
            </button>
            <button
              onClick={() => setAspectRatio('9:16')}
              className={`aspect-button ${aspectRatio === '9:16' ? 'active' : ''}`}
            >
              <div className="aspect-preview portrait"></div>
              <span>9:16 Portrait</span>
            </button>
          </div>
        </div>

        <div className="setting-group">
          <label>Enhanced Features</label>
          <div className="enhanced-features">
            <div className="feature-item">
              <div className="feature-icon">🎭</div>
              <div className="feature-text">
                <strong>Automatic Character Detection</strong>
                <p>AI analyzes your script and identifies characters automatically</p>
              </div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🎤</div>
              <div className="feature-text">
                <strong>Intelligent Voice Assignment</strong>
                <p>Each character gets a unique voice based on their personality</p>
              </div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🎬</div>
              <div className="feature-text">
                <strong>Professional Post-Production</strong>
                <p>Movie-level editing with color grading and effects</p>
              </div>
            </div>
          </div>
        </div>

        <div className="setting-group">
          <label>Script Preview</label>
          <div className="script-preview">
            {script.substring(0, 200)}...
          </div>
        </div>
      </div>

      <div className="action-buttons">
        <button 
          onClick={() => setCurrentStep('script')}
          className="secondary-button"
        >
          ← Back to Script
        </button>
        <button 
          onClick={handleGenerateVideo}
          className="primary-button"
        >
          Generate Video 🎬
        </button>
      </div>
    </div>
  );

  const renderGeneratingStep = () => (
    <div className="step-container">
      <div className="step-header">
        <h2>🎬 Generating Your Video</h2>
        <p>This may take a few minutes. You can safely leave this page - your video will continue processing in the background.</p>
      </div>

      <div className="progress-container">
        <div className="progress-circle">
          <div 
            className="progress-fill" 
            style={{ '--progress': `${progress}%` }}
          ></div>
          <div className="progress-text">
            {Math.round(progress)}%
          </div>
        </div>

        <div className="progress-details">
          <div className="progress-status">
            Status: <span className={`status-${generationStatus}`}>{generationStatus}</span>
          </div>
          <div className="progress-message">
            {progressMessage}
          </div>
        </div>

        <div className="progress-steps">
          <div className={`progress-step ${progress > 5 ? 'completed' : progress > 0 ? 'active' : ''}`}>
            <div className="step-icon">🎭</div>
            <span>Character Detection</span>
          </div>
          <div className={`progress-step ${progress > 15 ? 'completed' : progress > 5 ? 'active' : ''}`}>
            <div className="step-icon">🎤</div>
            <span>Voice Assignment</span>
          </div>
          <div className={`progress-step ${progress > 50 ? 'completed' : progress > 25 ? 'active' : ''}`}>
            <div className="step-icon">🎥</div>
            <span>Video Generation</span>
          </div>
          <div className={`progress-step ${progress > 70 ? 'completed' : progress > 60 ? 'active' : ''}`}>
            <div className="step-icon">🎙️</div>
            <span>Audio Creation</span>
          </div>
          <div className={`progress-step ${progress > 90 ? 'completed' : progress > 80 ? 'active' : ''}`}>
            <div className="step-icon">🎬</div>
            <span>Post-Production</span>
          </div>
          <div className={`progress-step ${progress > 98 ? 'completed' : progress > 95 ? 'active' : ''}`}>
            <div className="step-icon">✨</div>
            <span>Final Quality Check</span>
          </div>
        </div>
      </div>

      <div className="generation-info">
        <div className="info-card">
          <h3>Enhanced AI Production Process</h3>
          <ul>
            <li>AI analyzes your script and identifies unique characters</li>
            <li>Each character gets an intelligently assigned voice</li>
            <li>Video clips are generated and validated for quality</li>
            <li>Professional post-production with color grading and effects</li>
            <li>Final quality supervision ensures movie-level output</li>
          </ul>
        </div>
      </div>
    </div>
  );

  const renderResultStep = () => (
    <div className="step-container">
      <div className="step-header">
        <h2>🎉 Your Video is Ready!</h2>
        <p>Your script has been successfully converted to video</p>
      </div>

      <div className="video-result">
        {videoUrl && (
          <div className="video-player">
            <video
              controls
              className="result-video"
              src={videoUrl}
              poster="/api/placeholder/800/450"
            >
              Your browser does not support the video tag.
            </video>
          </div>
        )}

        <div className="video-info">
          <div className="video-stats">
            <div className="stat">
              <span className="stat-label">Aspect Ratio:</span>
              <span className="stat-value">{aspectRatio}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Voice System:</span>
              <span className="stat-value">Multi-Character AI</span>
            </div>
            <div className="stat">
              <span className="stat-label">Quality:</span>
              <span className="stat-value">Professional Grade</span>
            </div>
            <div className="stat">
              <span className="stat-label">Status:</span>
              <span className="stat-value success">Completed</span>
            </div>
          </div>

          <div className="video-actions">
            <a
              href={videoUrl}
              download="generated-video.mp4"
              className="download-button"
            >
              📥 Download Video
            </a>
          </div>
        </div>
      </div>

      <div className="action-buttons">
        <button 
          onClick={handleStartOver}
          className="primary-button"
        >
          Create Another Video
        </button>
      </div>
    </div>
  );

  const renderVideoLibrary = () => {
    return (
      <div className="step-content">
        <div className="step-header">
          <h2>📚 Video Library</h2>
          <p>Browse and download your previously generated videos</p>
          <button 
            onClick={() => setShowLibrary(false)}
            className="back-button"
          >
            ← Back to Generator
          </button>
        </div>

        <div className="library-stats">
          <div className="stat-item">
            <span className="stat-number">{videoLibrary.length}</span>
            <span className="stat-label">Videos</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">{videoLibrary.reduce((acc, video) => acc + video.file_size_mb, 0).toFixed(1)} MB</span>
            <span className="stat-label">Total Size</span>
          </div>
          <div className="stat-item">
            <button 
              onClick={loadVideoLibrary}
              className="refresh-button"
              disabled={loadingLibrary}
            >
              {loadingLibrary ? '⟳' : '🔄'} Refresh
            </button>
          </div>
        </div>

        {loadingLibrary ? (
          <div className="loading-library">
            <div className="loading-spinner"></div>
            <p>Loading video library...</p>
          </div>
        ) : videoLibrary.length === 0 ? (
          <div className="empty-library">
            <div className="empty-icon">📹</div>
            <h3>No videos generated yet</h3>
            <p>Generate your first video to see it here!</p>
            <button 
              onClick={() => setShowLibrary(false)}
              className="primary-button"
            >
              Generate Video
            </button>
          </div>
        ) : (
          <div className="video-grid">
            {videoLibrary.map((video, index) => (
              <div key={video.generation_id} className="video-card">
                <div className="video-thumbnail">
                  <div className="video-icon">🎬</div>
                  <div className="video-info">
                    <div className="video-title">Video #{videoLibrary.length - index}</div>
                    <div className="video-size">{video.file_size_mb} MB</div>
                  </div>
                </div>
                
                <div className="video-details">
                  <div className="video-script">
                    <strong>Script:</strong> {video.script_preview}
                  </div>
                  <div className="video-meta">
                    <div className="video-date">
                      Created: {new Date(video.created_at).toLocaleDateString()} at {new Date(video.created_at).toLocaleTimeString()}
                    </div>
                    <div className="video-id">
                      ID: {video.generation_id.slice(-8)}
                    </div>
                  </div>
                </div>
                
                <div className="video-actions">
                  <button 
                    onClick={() => downloadVideo(video.generation_id, `video_${index + 1}_${video.generation_id}.mp4`)}
                    className="download-button"
                  >
                    📥 Download
                  </button>
                  <button 
                    onClick={() => window.open(`${BACKEND_URL}/api/download/${video.generation_id}`, '_blank')}
                    className="view-button"
                  >
                    👀 View
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderCurrentStep = () => {
    if (showLibrary) {
      return renderVideoLibrary();
    }
    
    switch (currentStep) {
      case 'script':
        return renderScriptStep();
      case 'settings':
        return renderSettingsStep();
      case 'generating':
        return renderGeneratingStep();
      case 'result':
        return renderResultStep();
      default:
        return renderScriptStep();
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🎬 Script to Video</h1>
          <p>Transform your scripts into engaging videos with AI</p>
          <div className="header-actions">
            <button 
              onClick={() => {
                setShowLibrary(true);
                loadVideoLibrary();
              }}
              className="library-button"
            >
              📚 Video Library
            </button>
          </div>
        </div>
      </header>

      <nav className="step-nav">
        <div className="nav-container">
          <div className={`nav-step ${currentStep === 'script' ? 'active' : currentStep !== 'script' ? 'completed' : ''}`}>
            <span className="step-number">1</span>
            <span className="step-label">Script</span>
          </div>
          <div className="nav-connector"></div>
          <div className={`nav-step ${currentStep === 'settings' ? 'active' : ['generating', 'result'].includes(currentStep) ? 'completed' : ''}`}>
            <span className="step-number">2</span>
            <span className="step-label">Settings</span>
          </div>
          <div className="nav-connector"></div>
          <div className={`nav-step ${currentStep === 'generating' ? 'active' : currentStep === 'result' ? 'completed' : ''}`}>
            <span className="step-number">3</span>
            <span className="step-label">Generate</span>
          </div>
          <div className="nav-connector"></div>
          <div className={`nav-step ${currentStep === 'result' ? 'active' : ''}`}>
            <span className="step-number">4</span>
            <span className="step-label">Result</span>
          </div>
        </div>
      </nav>

      <main className="app-main">
        {error && (
          <div className="error-message">
            <div className="error-content">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
              <button 
                onClick={() => setError('')}
                className="error-close"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {renderCurrentStep()}
      </main>

      <footer className="app-footer">
        <p>Powered by AI • Wan 2.1 • Stable Audio • ElevenLabs • Gemini</p>
      </footer>
    </div>
  );
}

export default App;