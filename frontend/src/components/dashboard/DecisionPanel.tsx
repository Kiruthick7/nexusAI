"use client";

import React from "react";
import { useStore } from "@/store/useStore";
import { Ban, AlertCircle, Play, Pause, Loader2, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function DecisionPanel() {
  const {
    getActiveMission,
    isVoicePlaying,
    toggleVoicePlayback,
    voiceProgress,
    isSimulating,
    simulationStep,
  } = useStore();
  const mission = getActiveMission();

  const isCompleted = !isSimulating || simulationStep === "COMPLETED";

  // Create mock voice waveforms bar heights
  const bars = [8, 12, 16, 24, 18, 10, 14, 20, 12, 8, 14, 22, 16, 10];

  return (
    <div className="flex-1 min-w-[280px] max-w-sm flex flex-col gap-4 h-full overflow-y-auto log-stream pl-2">
      <AnimatePresence mode="wait">
        {isCompleted ? (
          <motion.div
            key="resolved"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="flex flex-col gap-4"
          >
            {/* Adjudication Decision Banner */}
            <div
              className={`glass-panel rounded-lg border-2 p-5 relative overflow-hidden shadow-sm transition-all duration-300 ${
                mission.status === "REJECTED"
                  ? "border-error/40 bg-error-container/10 shadow-[0_0_20px_rgba(147,0,10,0.1)]"
                  : "border-tertiary/40 bg-tertiary-container/10 shadow-[0_0_20px_rgba(255,183,126,0.1)]"
              }`}
            >
              <div className={`absolute top-0 left-0 w-1 h-full ${mission.status === "REJECTED" ? "bg-error" : "bg-tertiary"}`}></div>
              <div className="flex items-start gap-3">
                <div
                  className={`p-2 rounded-full border mt-0.5 shrink-0 ${
                    mission.status === "REJECTED"
                      ? "bg-error/15 border-error/30 text-error"
                      : "bg-tertiary/15 border-tertiary/30 text-tertiary"
                  }`}
                >
                  {mission.status === "REJECTED" ? <Ban className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                </div>
                <div className="text-left">
                  <h2
                    className={`text-2xl font-bold tracking-tight mb-0.5 ${
                      mission.status === "REJECTED" ? "text-error" : "text-tertiary"
                    }`}
                  >
                    {mission.status}
                  </h2>
                  <div
                    className={`inline-block px-1.5 py-0.5 border rounded text-[9px] font-mono font-bold tracking-wider uppercase ${
                      mission.status === "REJECTED"
                        ? "bg-error/10 border-error/30 text-error"
                        : "bg-tertiary/10 border-tertiary/30 text-tertiary"
                    }`}
                  >
                    {mission.statusSubtext}
                  </div>
                </div>
              </div>

              <p className="text-xs text-on-surface-variant mt-4 leading-relaxed border-t border-outline-variant/30 pt-3 text-left">
                {mission.status === "REJECTED"
                  ? "Potential duplicate submission detected within 30-day window. Invoice highly similar to NEX-8102 previously approved on Sep 14."
                  : "Claim requires manual review due to unresolvable policy conflict regarding out-of-network coverage."}
              </p>
            </div>

            {/* Mission Metadata Details */}
            <div className="glass-panel rounded-lg p-4 flex flex-col gap-3">
              <div className="flex justify-between items-center border-b border-outline-variant/60 pb-2 select-none">
                <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                  Run Metrics
                </span>
                <span className="font-mono text-xs text-primary font-bold">{mission.id}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-left">
                <div className="bg-surface-container-lowest p-2 rounded border border-outline-variant/30 flex flex-col">
                  <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">
                    Duration
                  </span>
                  <span className="font-mono text-sm font-semibold text-on-surface mt-0.5">
                    {mission.duration}
                  </span>
                </div>
                <div className="bg-surface-container-lowest p-2 rounded border border-outline-variant/30 flex flex-col">
                  <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">
                    Agents Used
                  </span>
                  <span className="font-mono text-sm font-semibold text-on-surface mt-0.5">
                    {mission.agentsUsed}
                  </span>
                </div>
              </div>

              {/* Dynamic AI Voice Summary Player */}
              <button
                onClick={toggleVoicePlayback}
                className="w-full mt-1.5 bg-surface-container-high hover:bg-surface-bright border border-outline-variant/60 p-2.5 rounded-lg flex items-center justify-between transition-all group"
              >
                <div className="flex items-center gap-2 text-left">
                  <div className="w-7 h-7 rounded-full bg-primary text-on-primary flex items-center justify-center shrink-0 shadow-sm">
                    {isVoicePlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[11px] font-bold text-on-surface">Voice Summary</span>
                    <span className="text-[9px] text-on-surface-variant uppercase font-mono">
                      {isVoicePlaying ? "Playing" : "Listen (1:24)"}
                    </span>
                  </div>
                </div>

                {/* Interactive animated speech waves */}
                <div className="flex items-end gap-[2px] h-6 pr-1 select-none">
                  {bars.map((height, idx) => {
                    const activeHeight = isVoicePlaying
                      ? Math.max(4, Math.sin((voiceProgress + idx * 2) * 0.4) * (height / 2) + height / 2)
                      : height / 3;

                    return (
                      <div
                        key={idx}
                        style={{ height: `${activeHeight}px` }}
                        className={`w-[2px] rounded-full transition-all duration-150 ${
                          isVoicePlaying ? "bg-primary pulse-dot" : "bg-outline-variant/60"
                        }`}
                      ></div>
                    );
                  })}
                </div>
              </button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="running"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="glass-panel rounded-lg border border-outline-variant/40 p-8 flex flex-col items-center justify-center text-center gap-4 min-h-[300px] shadow-sm select-none"
          >
            <div className="relative flex items-center justify-center">
              <Loader2 className="w-10 h-10 text-primary animate-spin" />
              <Sparkles className="absolute w-4 h-4 text-primary animate-pulse" />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm font-bold text-on-surface uppercase tracking-wider animate-pulse">
                Orchestrating...
              </span>
              <span className="text-xs text-on-surface-variant max-w-[200px] leading-relaxed">
                Evaluating claim factors under parallel LLM agent vectors.
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
export default DecisionPanel;
