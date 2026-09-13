import React, { useState, useEffect } from 'react';
import { videoService } from './services/api';
import MobileVideoPlayer from './components/Player/MobileVideoPlayer';

export default function App() {
    const [file, setFile] = useState(null);
    const [prompt, setPrompt] = useState('Isolate the highest energy gaming action sequence and sync punchy cuts');
    const [voiceText, setVoiceText] = useState('Soldier, watch this insane tactical clutch play! Area secured, absolute victory!');
    const [voiceActor, setVoiceActor] = useState('en-US-AndrewNeural');
    const [pipelineTaskId, setPipelineTaskId] = useState(null);
    const [pipelineState, setPipelineState] = useState('');
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
                const data = await videoService.checkPipelineStatus(pipelineTaskId);
                setPipelineState(data.state);

                if (data.state === 'SUCCESS') {
                    clearInterval(interval);
                    triggerUiAlert("✨ Studio AI Compilation Assembled Successfully!");
                    
                    const targetResult = data.result;
                    setProxyUrl(
                        targetResult.proxy_url?.startsWith('http')
                            ? targetResult.proxy_url
                            : `${window.location.origin}${targetResult.proxy_url}`
                    );
                    setOriginalVideoPath(targetResult.original_video_path || '');
                    setBlueprint(targetResult.blueprint || []);
                } else if (data.state === 'FAILURE') {
                    clearInterval(interval);
                    triggerUiAlert(
                        `❌ Assembly pipeline processing failed${data.error ? `: ${data.error}` : '.'}`,
                        true
                    );
                }
            } catch (err) {
                console.error("Status polling failed", err);
            }
        }, 7000); // 7-second polling loop interval

        return () => clearInterval(interval);
    }, [pipelineTaskId]);

    const handleUploadSubmit = async (e) => {
        // CRITICAL: Stop the raw form engine from refreshing the page and killing file state logs
        e.preventDefault();

        if (!file) {
            triggerUiAlert("❌ Please select a video file first.", true);
            return;
        }

        setPipelineState('QUEUED');
        setProxyUrl('');
        setDownloadUrl('');
        setExportState('');
        setOriginalVideoPath('');
        setBlueprint([]);
        triggerUiAlert("🚀 Streaming payload and compiling narrator audio tracks...");
        
        try {
            // Forward parameters cleanly to our synchronized API component instance
            const data = await videoService.uploadVideo(file, prompt, voiceText, voiceActor);
            setPipelineTaskId(data.task_id);
            setPipelineState(data.status === 'queued' ? 'QUEUED' : 'STARTED');
        } catch (err) {
            setPipelineState('FAILURE');
            triggerUiAlert(`❌ Video upload failed: ${err.message}`, true);
        }
    };

    const handleTriggerExport = async () => {
        if (!originalVideoPath || !blueprint.length) {
            triggerUiAlert("❌ No completed composition is available for export.", true);
            return;
        }

        setExportState('RENDERING');
        setDownloadUrl('');
        triggerUiAlert("🚀 Processing high-resolution visual layouts into master container...");
        try {
            await videoService.requestFinalExport(originalVideoPath, blueprint);
            setExportState('SUCCESS');
            triggerUiAlert("🎉 High-fidelity render master copy completed!");
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
                                onChange={(e) => {
                                    if (e.target.files && e.target.files.length > 0) {
                                        setFile(e.target.files);
                                    }
                                }}
                                className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-amber-500/10 file:text-amber-400 hover:file:bg-amber-500/20 cursor-pointer border border-dashed border-slate-700 p-2 rounded-xl bg-slate-950/50"
                            />
                            {file && (
                                <div className="mt-2 text-[10px] text-slate-500 truncate">
                                    Selected: {file.name || file[0]?.name || 'Video selected'}
                                </div>
                            )}
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
                            {pipelineState === 'QUEUED' || pipelineState === 'STARTED' ? 'Generating Sound-reactive Compilations...' : 'Ignite CapCut Engine'}
                        </button>
                    </form>
                )}

                {pipelineState && !proxyUrl && pipelineState !== 'FAILURE' && (
                    <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-xl">
                        <div className="flex items-center justify-between mb-3">
                            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-widest">
                                Studio Pipeline
                            </h3>

                            <span className="text-[9px] font-black uppercase tracking-wider text-slate-500">
                                {pipelineTaskId ? pipelineTaskId.slice(0, 8) : 'WAITING'}
                            </span>
                        </div>

                        <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />

                            <span className="text-xs font-bold text-slate-300 uppercase">
                                {pipelineState === 'QUEUED'
                                    ? 'Queued for processing'
                                    : pipelineState === 'STARTED'
                                        ? 'Processing media'
                                        : pipelineState}
                            </span>
                        </div>

                        <div className="mt-3 h-1.5 bg-slate-950 rounded-full overflow-hidden">
                            <div className="h-full w-1/2 bg-amber-500 rounded-full animate-pulse" />
                        </div>

                        <p className="text-[10px] text-slate-500 mt-3">
                            The studio is analyzing footage, generating narration and assembling the vertical composition.
                        </p>
                    </div>
                )}

                {proxyUrl && (
                    <div className="space-y-4 w-full">
                        <MobileVideoPlayer proxyUrl={proxyUrl} blueprint={blueprint} />
                        
                        <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-xl">
                            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-widest mb-3">🎞️ Multi-Clip Assembly Timeline</h3>

                            {blueprint.length > 0 ? (
                                <div className="flex flex-col gap-2">
                                    {blueprint.map((clip, i) => (
                                        <div
                                            key={`${clip.start}-${clip.end}-${i}`}
                                            className="flex items-center justify-between bg-slate-950 p-3 rounded-xl border border-slate-800/60 text-xs"
                                        >
                                            <div className="flex flex-col gap-1 min-w-0">
                                                <span className="font-black text-slate-200">
                                                    Highlight #{i + 1}
                                                </span>

                                                <span className="text-[10px] text-slate-500">
                                                    Duration: {Number(clip.start).toFixed(1)}s → {Number(clip.end).toFixed(1)}s
                                                </span>

                                                {clip.text && (
                                                    <span className="text-[10px] text-slate-400 truncate max-w-[230px]">
                                                        {clip.text}
                                                    </span>
                                                )}
                                            </div>

                                            <span className="text-[9px] font-black uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-md border border-emerald-500/10 shrink-0 ml-3">
                                                Auto-Stitched
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-xs text-slate-500 text-center py-4">
                                    No timeline segments returned.
                                </div>
                            )}
                        </div>

                        <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-xl">
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <h3 className="text-xs font-bold text-amber-400 uppercase tracking-widest">
                                        Final Export
                                    </h3>
                                    <p className="text-[10px] text-slate-500 mt-1">
                                        Generate the high-resolution vertical master.
                                    </p>
                                </div>

                                {exportState && (
                                    <span className={`text-[9px] font-black uppercase tracking-wider px-2 py-1 rounded-md ${
                                        exportState === 'SUCCESS'
                                            ? 'text-emerald-400 bg-emerald-500/10'
                                            : exportState === 'FAILURE'
                                                ? 'text-red-400 bg-red-500/10'
                                                : 'text-amber-400 bg-amber-500/10'
                                    }`}>
                                        {exportState}
                                    </span>
                                )}
                            </div>

                            <button
                                type="button"
                                onClick={handleTriggerExport}
                                disabled={exportState === 'RENDERING'}
                                className="w-full bg-amber-500 hover:bg-amber-400 disabled:bg-slate-800 text-slate-950 text-xs font-black py-3.5 rounded-xl transition-all cursor-pointer select-none uppercase tracking-wider"
                            >
                                {exportState === 'RENDERING' ? 'Baking Master Video File...' : '🚀 Bake Final High-Res Export (1080p)'}
                            </button>

                            {downloadUrl && (
                                <a
                                    href={downloadUrl}
                                    download
                                    className="mt-3 w-full flex items-center justify-center bg-slate-950 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-black py-3.5 rounded-xl transition-all uppercase tracking-wider"
                                >
                                    📥 Download Visual Lossless Master
                                </a>
                            )}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
