import React, { useState, useRef, useEffect } from 'react';

export default function MobileVideoPlayer({ proxyUrl, blueprint }) {
    const videoRef = useRef(null);
    const containerRef = useRef(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [videoDimensions, setVideoDimensions] = useState({ width: 0, height: 0 });
    const [alertMessage, setAlertMessage] = useState(null);

    // Dynamic UI Alert System (replaces standard browser alerts)
    const triggerCustomAlert = (message) => {
        setAlertMessage(message);
        setTimeout(() => setAlertMessage(null), 4000);
    };

    // Tracks container sizes to calculate dynamic overlay mapping bounds
    useEffect(() => {
        if (!containerRef.current) return;

        const handleResize = (entries) => {
            for (let entry of entries) {
                const { width, height } = entry.contentRect;
                setVideoDimensions({ width, height });
            }
        };

        const observer = new ResizeObserver(handleResize);
        observer.observe(containerRef.current);

        return () => observer.disconnect();
    }, []);

    const handleTimeUpdate = () => {
        if (videoRef.current) {
            setCurrentTime(videoRef.current.currentTime);
        }
    };

    const handleOverlayClick = (text) => {
        triggerCustomAlert(`Selected text content: "${text}"`);
    };

    return (
        <div className="w-full max-w-[420px] mx-auto bg-white p-4 rounded-2xl shadow-xl border border-[#8B4513]/10 relative">
            
            {/* Custom Alert Notification Banner (Reddish-brown and White theme) */}
            {alertMessage && (
                <div className="absolute top-6 left-1/2 -translate-x-1/2 z-50 w-[85%] bg-[#651c1c] text-white text-sm py-2.5 px-4 rounded-xl shadow-lg border border-[#8B4513]/20 flex items-center justify-between animate-fade-in">
                    <span className="font-medium tracking-wide">{alertMessage}</span>
                    <button 
                        onClick={() => setAlertMessage(null)}
                        className="ml-2 text-white/70 hover:text-white font-bold text-xs uppercase"
                    >
                        Dismiss
                    </button>
                </div>
            )}

            {/* Render Stage Container Area */}
            <div 
                ref={containerRef}
                className="relative w-full aspect-[9/16] bg-black rounded-xl overflow-hidden border border-[#8B4513]/20 shadow-inner"
            >
                {/* Asynchronous Lightweight Stream Asset */}
                <video 
                    ref={videoRef}
                    src={proxyUrl} 
                    playsInline
                    onTimeUpdate={handleTimeUpdate}
                    className="w-full h-full object-cover"
                />

                {/* Computational Scaling Subtitle Layer */}
                {videoDimensions.width > 0 && blueprint.map((item, index) => {
                    const isVisible = currentTime >= item.start && currentTime <= item.end;
                    if (!isVisible) return null;

                    // Convert raw 1080x1920 backend logical boundaries dynamically to matching live layout pixel coordinates
                    const calculatedX = (item.x / 1080) * videoDimensions.width;
                    const calculatedY = (item.y / 1920) * videoDimensions.height;

                    return (
                        <div 
                            key={index}
                            onClick={() => handleOverlayClick(item.text)}
                            className="absolute z-10 cursor-pointer p-2 bg-[#651c1c]/80 backdrop-blur-xs rounded-lg transition-transform active:scale-95 shadow-md border border-white/20 select-none max-w-[80%]"
                            style={{
                                left: `${calculatedX}px`,
                                top: `${calculatedY}px`,
                                transform: 'translate(-50%, -50%)',
                            }}
                        >
                            <span className={`text-white font-semibold text-sm text-center block ${item.style === 'impact-bold' ? 'font-black tracking-wider uppercase text-amber-200' : ''}`}>
                                {item.text}
                            </span>
                        </div>
                    );
                })}
            </div>

            {/* Timeline Controls (Theme Integration Elements) */}
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
                    Timestamp: {currentTime.toFixed(1)}s
                </div>
            </div>
        </div>
    );
}
