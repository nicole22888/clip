import React, { useState, useEffect } from 'react';
import { videoService } from './services/api';
import MobileVideoPlayer from './components/Player/MobileVideoPlayer';
import DynamicTextLayer from './components/Overlay/DynamicTextLayer';

export default function App() {
    const [file, setFile] = useState(null);
    const [prompt, setPrompt] = useState('Find the best action moments');
    const [pipelineTaskId, setPipelineTaskId] = useState(null);
    const [pipelineState, setPipelineState] = useState('');
    const [exportTaskId, setExportTaskId] = useState(null);
    const [exportState, setExportState] = useState('');
    const [downloadUrl, setDownloadUrl] = useState('');
    
    // Core working pipeline states
    const [proxyUrl, setProxyUrl] = useState('');
    const [originalVideoPath, setOriginalVideoPath] = useState('');
    const [blueprint, setBlueprint] = useState([]);

    // Polls the pipeline processing chain progress
    useEffect(() => {
        if (!pipelineTaskId) return;

        const interval = setInterval(async () => {
            try {
                const data = await videoService.checkPipelineStatus(pipelineTaskId);
                setPipelineState(data.state);

                if (data.state === 'SUCCESS') {
                    clearInterval(interval);
                    setProxyUrl(`http://localhost:8000${data.result.proxy_url}`);
                    setOriginalVideoPath(data.result.original_video_path);
                    setBlueprint(data.result.blueprint);
                } else if (data.state === 'FAILURE') {
                    clearInterval(interval);
                }
            } catch (err) {
                console.error("Status polling failed", err);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [pipelineTaskId]);

    // Polls high-resolution asset export rendering completion
    useEffect(() => {
        if (!exportTaskId) return;

        const interval = setInterval(async () => {
            try {
                const data = await videoService.checkExportStatus(exportTaskId);
                setExportState(data.state);

                if (data.state === 'SUCCESS') {
                    clearInterval(interval);
                    setDownloadUrl(`http://localhost:8000${data.download_url}`);
                } else if (data.state === 'FAILURE') {
                    clearInterval(interval);
                }
            } catch (err) {
                console.error("Export polling failed", err);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [exportTaskId]);

    const handleUploadSubmit = async (e) => {
        e.preventDefault();
        if (!file) return;
        
        setPipelineState('QUEUED');
        setProxyUrl('');
        setDownloadUrl('');
        
        try {
            const data = await videoService.uploadVideo(file, prompt);
            setPipelineTaskId(data.task_id);
        } catch (err) {
            setPipelineState('FAILURE');
        }
    };

    const handleTriggerExport = async () => {
        setExportState('RENDERING');
        try {
            const data = await videoService.requestFinalExport(originalVideoPath, blueprint);
            setExportTaskId(data.task_id);
        } catch (err) {
            setExportState('FAILURE');
        }
    };

    return (
        <div className="min-h-screen bg-white text-gray-800 font-sans antialiased flex flex-col items-center py-8 px-4">
            
            {/* Header branding lock */}
            <header className="w-full max-w-[420px] text-center mb-8">
                <h1 className="text-3xl font-black tracking-tight text-[#651c1c] uppercase">Clipper</h1>
                <p className="text-xs font-semibold text-gray-400 mt-1 uppercase tracking-widest">Self-Hosted Mobile AI Studio</p>
            </header>

            <main className="w-full max-w-[420px] flex flex-col gap-6">
                
                {/* 1. Ingestion Form Controls */}
                {!proxyUrl && (
                    <form onSubmit={handleUploadSubmit} className="bg-gray-50 border border-gray-100 p-5 rounded-2xl shadow-xs">
                        <div className="flex flex-col gap-4">
                            <div>
                                <label className="text-xs font-bold text-[#651c1c] uppercase tracking-wider block mb-2">Select Footage</label>
                                <input 
                                    type="file" 
                                    accept="video/*"
                                    onChange={(e) => setFile(e.target.files[0])}
                                    className="w-full text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-[#651c1c]/10 file:text-[#651c1c] hover:file:bg-[#651c1c]/20 cursor-pointer"
                                />
                            </div>

                            <div>
                                <label className="text-xs font-bold text-[#651c1c] uppercase tracking-wider block mb-2">AI Directorial Prompt</label>
                                <textarea 
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    rows="2"
                                    className="w-full bg-white text-xs p-3 rounded-xl border border-gray-200 focus:outline-hidden focus:border-[#651c1c] font-medium"
                                />
                            </div>

                            <button 
                                type="submit"
                                disabled={!file || pipelineState === 'QUEUED' || pipelineState === 'STARTED'}
                                className="w-full bg-[#651c1c] hover:bg-[#802828] disabled:bg-gray-300 text-white text-xs font-bold py-3 rounded-xl transition-colors cursor-pointer select-none shadow-xs uppercase tracking-wider"
                            >
                                {pipelineState === 'QUEUED' || pipelineState === 'STARTED' ? `Processing Pipeline (${pipelineState})...` : 'Ignite AI Assembly'}
                            </button>
                        </div>
                    </form>
                )}

                {/* 2. Interactive Editing Core Workbench */}
                {proxyUrl && (
                    <div className="animate-fade-in space-y-4">
                        <MobileVideoPlayer proxyUrl={proxyUrl} blueprint={blueprint} />
                        
                        <DynamicTextLayer blueprint={blueprint} onUpdateBlueprint={setBlueprint} />

                        <div className="bg-gray-50 p-4 rounded-2xl border border-gray-100 flex flex-col gap-3">
                            <button
                                onClick={handleTriggerExport}
                                disabled={exportState === 'RENDERING'}
                                className="w-full bg-[#651c1c] hover:bg-[#802828] text-white text-xs font-bold py-3 rounded-xl uppercase tracking-wider transition-colors shadow-sm"
                            >
                                {exportState === 'RENDERING' ? 'Baking High-Res Video...' : '🚀 Export Master Copy (HQ)'}
                            </button>

                            {downloadUrl && (
                                <a 
                                    href={downloadUrl}
                                    download
                                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-center text-xs font-bold py-3 rounded-xl uppercase tracking-wider transition-colors block shadow-xs"
                                >
                                    📥 Download Final 9:16 Video
                                </a>
                            )}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
