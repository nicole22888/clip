import React, { useState, useEffect } from 'react';
import axios from 'axios';
import MobileVideoPlayer from './components/Player/MobileVideoPlayer';

export default function App() {
    const [file, setFile] = useState(null);
    const [prompt, setPrompt] = useState('Isolate the highest energy gaming action sequence and sync punchy cuts');
    const [voiceText, setVoiceText] = useState('Soldier, watch this insane tactical clutch play! Area secured, absolute victory!');
    const [voiceActor, setVoiceActor] = useState('en-US-AndrewNeural'); // Default to Commander Voice
    const [pipelineTaskId, setPipelineTaskId] = useState(null);
    const [pipelineState, setPipelineState] = useState('');
    const [exportTaskId, setExportTaskId] = useState(null);
    const [exportState, setExportState] = useState('');
    const [downloadUrl, setDownloadUrl] = useState('');
    
    const [proxyUrl, setProxyUrl] = useState('');
    const [originalVideoPath, setOriginalVideoPath] = useState('');
    const [blueprint, setBlueprint] = useState([]);
    const [uiAlert, setUiAlert] = useState(null);

    const triggerUiAlert = (msg, isError = false) => {
        setUiAlert({ text: msg, isError });
        setTimeout(() => setUiAlert(null), 5000);
    };

    useEffect(() => {
        if (!pipelineTaskId) return;

        const interval = setInterval(async () => {
            try {
                const response = await axios.get(`/api/video/status/${pipelineTaskId}`);
                const data = response.data;
                setPipelineState(data.state);

                if (data.state === 'SUCCESS') {
                    clearInterval(interval);
                    triggerUiAlert("✨ Studio AI Compilation Assembled Successfully!");
                    
                    const targetResult = data.result;
                    setProxyUrl(`${window.location.origin}${targetResult.proxy_url}`);
                    setOriginalVideoPath(targetResult.original_video_path);
                    setBlueprint(targetResult.blueprint || []);
                } else if (data.state === 'FAILURE') {
                    clearInterval(interval);
                    triggerUiAlert("❌ Assembly pipeline processing failed.", true);
                }
            } catch (err) {
                console.error("Status polling failed", err);
            }
        }, 1500);

        return () => clearInterval(interval);
    }, [pipelineTaskId]);

    const handleUploadSubmit = async (e) => {
        e.preventDefault();
        setPipelineState('QUEUED');
        setProxyUrl('');
        setDownloadUrl('');
        triggerUiAlert("Ingesting media and engineering neural character tracks...");
        
        try {
            const formData = new FormData();
            if (file && file[0]) {
                formData.append('video', file[0]);
            }
            formData.append('prompt', prompt);
            formData.append('voice_text', voiceText);
            formData.append('voice_actor', voiceActor);

            const response = await axios.post('/api/video/process', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setPipelineTaskId(response.data.task_id);
        } catch (err) {
            setPipelineState('FAILURE');
            triggerUiAlert(`❌ Local connection failed: ${err.message}`, true);
        }
    };

    const handleTriggerExport = async () => {
        setExportState('RENDERING');
        triggerUiAlert("Processing high-resolution visual layouts into master container...");
        try {
            await axios.post('/api/export/render', {
                original_video_path: originalVideoPath,
                blueprint: blueprint.map(b => ({
                    text: b.text, start: b.start, end: b.end, x: b.x, y: b.y, style: b.style
                }))
            });
            setExportState('SUCCESS');
            triggerUiAlert(" High-fidelity render master copy completed!");
            setDownloadUrl(`${window.location.origin}/api/outputs/final_studio_master.mp4`);
        } catch (err) {
            setExportState('FAILURE');
            triggerUiAlert(`❌ Render error: ${err.message}`, true);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased flex flex-col items-center py-8 px-4 relative selection:bg-amber-500 selection:text-slate-900">
            
            {uiAlert && (
                <div className={`absolute top-4 z-50 w-[90%] max-w-[400px] text-white text-xs font-bold py-3.5 px-4 rounded-xl shadow-2xl flex items-center justify-between border border-white/10 ${uiAlert.isError ? 'bg-red-900' : 'bg-amber-600'}`}>
                    <span>{uiAlert.text}</span>
                    <button onClick={() => setUiAlert(null)} className="opacity-70 font-bold ml-4 uppercase text-[10px]">Close</button>
                </div>
            )}

            <header className="w-full max-w-[420px] text-center mb-8">
                <span className="text-[10px] font-black uppercase tracking-widest bg-amber-500/10 text-amber-400 px-2.5 py-1 rounded-full border border-amber-500/20">Whop Premium Edition</span>
                <h1 className="text-4xl font-black tracking-tighter text-white mt-3 uppercase">Clipper<span className="text-amber-400">.Studio</span></h1>
                <p className="text-xs font-semibold text-slate-400 mt-1 uppercase tracking-wider">Automated Character Audio Video Studio</p>
            </header>

            <main className="w-full max-w-[420px] flex flex-col gap-6">
                {!proxyUrl && (
                    <form onSubmit={handleUploadSubmit} className="bg-slate-900 border border-slate-800/80 p-5 rounded-2xl shadow-xl space-y-4">
                        <div>
                            <label className="text-[10px] font-bold text-amber-400 uppercase tracking-widest block mb-2">1. Select Footage File</label>
                            <input 
                                type="file" 
                                accept="video/*"
                                onChange={(e) => setFile(e.target.files)}
                                className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-amber-500/10 file:text-amber-400 hover:file:bg-amber-500/20 cursor-pointer border border-dashed border-slate-700 p-2 rounded-xl bg-slate-950/50"
                            />
                        </div>

                        <div>
                            <label className="text-[10px] font-bold text-amber-400 uppercase tracking-widest block mb-2">2. Character Voice Profile</label>
                            <select 
                                value={voiceActor}
                                onChange={(e) => setVoiceActor(e.target.value)}
                                className="w-full bg-slate-950 text-xs p-3 rounded-xl border border-slate-800 focus:outline-none focus:border-amber-400 font-bold text-slate-200 cursor-pointer"
                            >
                                <option value="en-US-AndrewNeural">🪖 Battlefield Commander (Male - Deep & Rugged)</option>
                                <option value="en-US-ChristopherNeural">🎙️ Esports Arena Announcer (Male - Hype & Sharp)</option>
                                <option value="en-GB-RyanNeural">🎭 Cinematic Narrator (Male - British & Dramatic)</option>
                                <option value="en-US-EmmaNeural">⚡ Action Commentator (Female - Fast & Energetic)</option>
                            </select>
                        </div>

                        <div>
                            <label className="text-[10px] font-bold text-amber-400 uppercase tracking-widest block mb-2">3. Narrator Script Text</label>
                            <textarea 
                                value={voiceText}
                                onChange={(e) => setVoiceText(e.target.value)}
                                rows="2"
                                placeholder="Type the character's exact words here..."
                                className="w-full bg-slate-950 text-xs p-3 rounded-xl border border-slate-800 focus:outline-none focus:border-amber-400 font-medium text-slate-200 placeholder:text-slate-600 resize-none"
                            />
                        </div>

                        <div>
                            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2">4. Directorial Cutting Instructions</label>
                            <textarea 
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                rows="2"
                                className="w-full bg-slate-950 text-xs p-3 rounded-xl border border-slate-800 focus:outline-none focus:border-slate-500 font-medium text-slate-400 resize-none"
                            />
                        </div>

                        <button 
                            type="submit"
                            disabled={pipelineState === 'QUEUED' || pipelineState === 'STARTED'}
                            className="w-full bg-amber-500 hover:bg-amber-400 disabled:bg-slate-800 text-slate-950 text-xs font-black py-3.5 rounded-xl transition-all cursor-pointer select-none uppercase tracking-wider"
                        >
                            {pipelineState === 'QUEUED' || pipelineState === 'STARTED' ? 'Generating Sound-reactive Compilations...' : 'Ignite'}
                        </button>
                    </form>
                )}

                {proxyUrl && (
                    <div className="space-y-4 w-full">
                        <MobileVideoPlayer proxyUrl={proxyUrl} blueprint={blueprint} />

                        🎞️ Multi-Clip Assembly
                        {blueprint.map((clip, i) => (
                            <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-3">
                                <div className="text-xs font-bold text-amber-400">Highlight #{i + 1}</div>
                                <div className="text-xs text-slate-400">
                                    Duration: {clip.start.toFixed(1)}s → {clip.end.toFixed(1)}s
                                </div>
                                <div className="text-[10px] text-slate-500 uppercase tracking-wider mt-1">
                                    Auto-Stitched
                                </div>
                            </div>
                        ))}

                        <button
                            onClick={handleTriggerExport}
                            disabled={exportState === 'RENDERING'}
                            className="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black py-3.5 rounded-xl uppercase tracking-wider transition-all"
                        >
                            {exportState === 'RENDERING' ? 'Baking Master Video File...' : '🚀 Bake Final High-Res Export (1080p)'}
                        </button>

                        {downloadUrl && (
                            <a
                                href={downloadUrl}
                                download
                                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-center text-xs font-black py-3.5 rounded-xl uppercase tracking-wider transition-all block"
                            >
                                📥 Download
                            </a>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
