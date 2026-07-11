"use client";

import React from "react";
import { Check, Loader2 } from "lucide-react";
import { useStore } from "@/store/useStore";

export function MissionTimeline() {
  const { isSimulating, simulationStep, isFreshUpload } = useStore();

  const getStepStatus = (step: string) => {
    if (isFreshUpload) return "pending";
    if (!isSimulating || simulationStep === "COMPLETED") return "completed";
    
    switch (step) {
      case "upload":
        return "completed";
      case "ocr":
        if (simulationStep === "INGESTING") return "active";
        return "completed";
      case "dispatch":
        if (simulationStep === "INGESTING") return "pending";
        if (simulationStep === "PLANNING") return "active";
        return "completed";
      case "analysis":
        if (simulationStep === "INGESTING" || simulationStep === "PLANNING") return "pending";
        if (simulationStep === "ANALYZING") return "active";
        return "completed";
      case "resolution":
        if (simulationStep === "INGESTING" || simulationStep === "PLANNING" || simulationStep === "ANALYZING") return "pending";
        if (simulationStep === "ARBITRATING") return "active";
        return "completed";
      case "decision":
        return "pending";
      default:
        return "pending";
    }
  };

  const renderStep = (label: string, key: string) => {
    const status = getStepStatus(key);
    
    if (status === "completed") {
      return (
        <span className="text-secondary flex items-center gap-1.5 font-bold transition-all duration-300">
          <Check className="w-3.5 h-3.5 text-secondary stroke-[3px]" /> {label}
        </span>
      );
    }
    if (status === "active") {
      return (
        <span className="bg-primary/20 text-primary px-2 py-0.5 rounded border border-primary/30 shadow-[0_0_10px_rgba(178,197,255,0.1)] flex items-center gap-1.5 font-bold animate-pulse transition-all duration-300 text-[10px]">
          <Loader2 className="w-3 h-3 text-primary animate-spin" /> {label}
        </span>
      );
    }
    return (
      <span className="text-on-surface-variant/40 font-semibold transition-all duration-300">
        {label}
      </span>
    );
  };

  return (
    <div className="glass-panel rounded-lg px-4 py-3 flex items-center justify-between overflow-x-auto whitespace-nowrap hide-scrollbar border-outline-variant/30 select-none">
      <div className="flex items-center gap-3 font-mono text-[10px] text-on-surface-variant w-full justify-between lg:justify-start lg:gap-4">
        {/* Step 1 */}
        {renderStep("Upload", "upload")}
        <span className="text-outline-variant">→</span>

        {/* Step 2 */}
        {renderStep("OCR", "ocr")}
        <span className="text-outline-variant">→</span>

        {/* Step 3 */}
        {renderStep("Dispatch", "dispatch")}
        <span className="text-outline-variant">→</span>

        {/* Step 4 */}
        {renderStep("Parallel Analysis", "analysis")}
        <span className="text-outline-variant">→</span>

        {/* Step 5 */}
        {renderStep("Resolution", "resolution")}
        <span className="text-outline-variant">→</span>

        {/* Step 6 */}
        {renderStep("Decision", "decision")}
      </div>
    </div>
  );
}
export default MissionTimeline;
