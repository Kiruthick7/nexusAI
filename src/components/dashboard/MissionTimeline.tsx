"use client";

import React from "react";
import { Check, Loader2 } from "lucide-react";

export function MissionTimeline() {

  return (
    <div className="glass-panel rounded-lg px-4 py-3.5 flex items-center justify-between overflow-x-auto whitespace-nowrap hide-scrollbar border-outline-variant/30">
      <div className="flex items-center gap-3 font-mono text-[10px] text-on-surface-variant w-full justify-between lg:justify-start lg:gap-4">
        {/* Step 1 */}
        <span className="text-secondary flex items-center gap-1.5 font-bold">
          <Check className="w-3.5 h-3.5 text-secondary stroke-[3px]" /> Upload
        </span>
        <span className="text-outline-variant">→</span>

        {/* Step 2 */}
        <span className="text-secondary flex items-center gap-1.5 font-bold">
          <Check className="w-3.5 h-3.5 text-secondary stroke-[3px]" /> OCR
        </span>
        <span className="text-outline-variant">→</span>

        {/* Step 3 */}
        <span className="text-secondary flex items-center gap-1.5 font-bold">
          <Check className="w-3.5 h-3.5 text-secondary stroke-[3px]" /> Dispatch
        </span>
        <span className="text-outline-variant">→</span>

        {/* Step 4 */}
        <span className="bg-primary/20 text-primary px-2 py-1 rounded border border-primary/30 shadow-[0_0_10px_rgba(178,197,255,0.1)] flex items-center gap-1.5 font-bold">
          <Loader2 className="w-3.5 h-3.5 text-primary animate-spin" /> Parallel Analysis
        </span>
        <span className="text-outline-variant">→</span>

        {/* Step 5 */}
        <span className="text-on-surface-variant/70 font-semibold">Resolution</span>
        <span className="text-outline-variant">→</span>

        {/* Step 6 */}
        <span className="text-on-surface-variant/70 font-semibold">Decision</span>
      </div>
    </div>
  );
}
export default MissionTimeline;
