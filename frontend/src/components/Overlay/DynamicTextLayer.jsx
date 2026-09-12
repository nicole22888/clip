import React from 'react';

export default function DynamicTextLayer({ blueprint, onUpdateBlueprint }) {
    
    const handleTextChange = (index, newText) => {
        const updated = [...blueprint];
        updated[index].text = newText;
        onUpdateBlueprint(updated);
    };

    const handleTimeChange = (index, field, value) => {
        const updated = [...blueprint];
        updated[index][field] = parseFloat(value) || 0;
        onUpdateBlueprint(updated);
    };

    return (
        <div className="w-full max-w-[420px] mx-auto bg-white p-5 rounded-2xl border border-[#8B4513]/10 shadow-xs mt-4">
            <h3 className="text-[#651c1c] text-base font-bold tracking-wide mb-3 flex items-center gap-2">
                <span>📋</span> Highlight Timelines
            </h3>
            
            <div className="space-y-3 max-h-[220px] overflow-y-auto pr-1">
                {blueprint.map((item, index) => (
                    <div 
                        key={index} 
                        className={`p-3 rounded-xl border transition-all ${
                            item.collision_detected 
                                ? 'bg-[#651c1c]/5 border-[#651c1c]/20' 
                                : 'bg-gray-50 border-gray-100'
                        }`}
                    >
                        {/* Interactive text modifier input */}
                        <div className="flex flex-col gap-1.5">
                            <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                                Subtitle Content {item.collision_detected && "⚠️ Adjusted for collision"}
                            </label>
                            <input 
                                type="text"
                                value={item.text}
                                onChange={(e) => handleTextChange(index, e.target.value)}
                                className="w-full bg-white text-gray-800 text-xs px-3 py-2 rounded-lg border border-gray-200 focus:outline-hidden focus:border-[#651c1c] font-medium transition-colors"
                            />
                        </div>

                        {/* Interactive timestamp adjusters */}
                        <div className="grid grid-cols-2 gap-2 mt-2.5">
                            <div>
                                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1">Start (s)</label>
                                <input 
                                    type="number" 
                                    step="0.1"
                                    value={item.start}
                                    onChange={(e) => handleTimeChange(index, 'start', e.target.value)}
                                    className="w-full bg-white text-gray-800 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 focus:outline-hidden focus:border-[#651c1c]"
                                />
                            </div>
                            <div>
                                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1">End (s)</label>
                                <input 
                                    type="number" 
                                    step="0.1"
                                    value={item.end}
                                    onChange={(e) => handleTimeChange(index, 'end', e.target.value)}
                                    className="w-full bg-white text-gray-800 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 focus:outline-hidden focus:border-[#651c1c]"
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
