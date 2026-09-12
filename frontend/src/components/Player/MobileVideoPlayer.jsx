import React, { useState, useRef } from 'react';

export default function MobileVideoPlayer({ proxyUrl, blueprint }) {
    const videoRef = useRef(null);
    const [currentTime, setCurrentTime] = useState(0);

    const handleTimeUpdate = () => {
        if (videoRef.current) {
            setCurrentTime(videoRef.current.currentTime);
        }
    };

    return (
        <div className="w-full max-w-[420px] mx-auto bg-white p-4 rounded-2xl shadow-xl border border-[#8B4513]/10 relative">
            
            {/* Clean Video Presentation Stage */}
            <div className="relative w-full aspect-[9/16] bg-black rounded-xl overflow-hidden border border-[#8B4513]/20 shadow-inner">
                {/* 
                  The 480p preview video streams smoothly. 
                  All audio tracks, sound effects, screams, and spoken text are fully active.
                  We have completely unlinked/hidden the visual floating text blocks from this view 
                  per your product criteria.
                */}
                <video 
                    ref={videoRef}
                    src={proxyUrl} 
                    playsInline
                    controls
                    onTimeUpdate={handleTimeUpdate}
                    className="w-full h-full object-cover"
                />
            </div>

            {/* Quick Playback Metrics Dashboard */}
            <div className="mt-4 flex items-center justify-between gap-3 px-1">
                <button 
                    onClick={() => {
                        if (videoRef.current) {
                            videoRef.current.paused ? videoRef.current.play() : videoRef.current.pause();
                        }
                    }}
                    className="bg-[#651c1c] hover:bg-[#802828] text-white text-xs font-bold py-2 px-4 rounded-lg shadow-xs transition-colors cursor-pointer select-none"
                >
                    Toggle Play
                </button>
                <div className="text-right text-xs font-medium text-[#651c1c]/70">
                    Active Timeline: {currentTime.toFixed(1)}s
                </div>
            </div>
        </div>
    );
}
