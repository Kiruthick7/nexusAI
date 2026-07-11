"use client";

import React from "react";
import { useStore } from "@/store/useStore";
import { Ban, AlertCircle, Play, Pause, Loader2, Sparkles, ShieldCheck } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function DecisionPanel() {
  const {
    getActiveMission,
    isVoicePlaying,
    toggleVoicePlayback,
    voiceProgress,
    isSimulating,
    simulationStep,
    isFreshUpload,
    overrideMissionStatus,
  } = useStore();
  const mission = getActiveMission();

  const isCompleted = !isFreshUpload && (!isSimulating || simulationStep === "COMPLETED");

  // Create mock voice waveforms bar heights
  const bars = [8, 12, 16, 24, 18, 10, 14, 20, 12, 8, 14, 22, 16, 10];

  return (
    <div className="flex-1 min-w-[280px] max-w-sm flex flex-col gap-4 h-full overflow-y-auto log-stream pl-2">
      <AnimatePresence mode="wait">
        {isFreshUpload ? (
          <motion.div
            key="fresh"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="flex flex-col gap-4"
          >
            {/* Pending Adjudication Decision Banner */}
            <div className="glass-panel rounded-lg border-2 border-outline-variant/40 p-5 relative overflow-hidden bg-surface-container-low/30 shadow-sm text-left select-none">
              <div className="absolute top-0 left-0 w-1 h-full bg-outline-variant/60"></div>
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-full border border-outline-variant/50 bg-surface-container mt-0.5 shrink-0 text-on-surface-variant/40">
                  <Sparkles className="w-5 h-5 animate-pulse text-primary" />
                </div>
                <div>
                  <h2 className="text-xl font-bold tracking-tight mb-1 text-on-surface/60">
                    Decision Pending
                  </h2>
                  <div className="inline-block px-1.5 py-0.5 border border-outline-variant/40 bg-surface-container-high rounded text-[9px] font-mono font-bold tracking-wider uppercase text-on-surface-variant/60">
                    AWAITING UPLOAD
                  </div>
                </div>
              </div>

              <p className="text-xs text-on-surface-variant/60 mt-4 leading-relaxed border-t border-outline-variant/30 pt-3 text-left">
                The final claim decision, agent arbitration, and run metrics will compile in real time once your receipt is uploaded.
              </p>
            </div>

            {/* Run Metrics Placeholder */}
            <div className="glass-panel rounded-lg p-4 flex flex-col gap-3 opacity-60 select-none">
              <div className="flex justify-between items-center border-b border-outline-variant/60 pb-2">
                <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                  Run Metrics
                </span>
                <span className="font-mono text-xs text-on-surface-variant/40">NEX-xxxx</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-left">
                <div className="bg-surface-container-lowest p-2 rounded border border-outline-variant/30 flex flex-col">
                  <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">
                    Duration
                  </span>
                  <span className="font-mono text-sm font-semibold text-on-surface-variant/30 mt-0.5">
                    --
                  </span>
                </div>
                <div className="bg-surface-container-lowest p-2 rounded border border-outline-variant/30 flex flex-col">
                  <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">
                    Agents Used
                  </span>
                  <span className="font-mono text-sm font-semibold text-on-surface-variant/30 mt-0.5">
                    --
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        ) : isCompleted ? (
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
                  : mission.status === "APPROVED"
                  ? "border-secondary/40 bg-secondary-container/10 shadow-[0_0_20px_rgba(117,219,148,0.15)]"
                  : "border-tertiary/40 bg-tertiary-container/10 shadow-[0_0_20px_rgba(255,183,126,0.1)]"
              }`}
            >
              <div
                className={`absolute top-0 left-0 w-1 h-full ${
                  mission.status === "REJECTED"
                    ? "bg-error"
                    : mission.status === "APPROVED"
                    ? "bg-secondary"
                    : "bg-tertiary"
                }`}
              ></div>
              <div className="flex items-start gap-3">
                <div
                  className={`p-2 rounded-full border mt-0.5 shrink-0 ${
                    mission.status === "REJECTED"
                      ? "bg-error/15 border-error/30 text-error"
                      : mission.status === "APPROVED"
                      ? "bg-secondary/15 border-secondary/30 text-secondary"
                      : "bg-tertiary/15 border-tertiary/30 text-tertiary"
                  }`}
                >
                  {mission.status === "REJECTED" ? (
                    <Ban className="w-5 h-5" />
                  ) : mission.status === "APPROVED" ? (
                    <ShieldCheck className="w-5 h-5" />
                  ) : (
                    <AlertCircle className="w-5 h-5" />
                  )}
                </div>
                <div className="text-left">
                  <h2
                    className={`text-2xl font-bold tracking-tight mb-0.5 ${
                      mission.status === "REJECTED"
                        ? "text-error"
                        : mission.status === "APPROVED"
                        ? "text-secondary"
                        : "text-tertiary"
                    }`}
                  >
                    {mission.status}
                  </h2>
                  <div
                    className={`inline-block px-1.5 py-0.5 border rounded text-[9px] font-mono font-bold tracking-wider uppercase ${
                      mission.status === "REJECTED"
                        ? "bg-error/10 border-error/30 text-error"
                        : mission.status === "APPROVED"
                        ? "bg-secondary/10 border-secondary/30 text-secondary"
                        : "bg-tertiary/10 border-tertiary/30 text-tertiary"
                    }`}
                  >
                    {mission.statusSubtext}
                  </div>
                </div>
              </div>

              <p className="text-xs text-on-surface-variant mt-4 leading-relaxed border-t border-outline-variant/30 pt-3 text-left">
                {mission.status === "REJECTED"
                  ? "Potential duplicate submission detected within 30-day window. Invoice highly similar to previous approval."
                  : mission.status === "APPROVED"
                  ? "Claim approved. Specialist checks verified provider registry database, guidelines, and historical patterns without anomalies."
                  : "Claim requires manual review due to verification warnings or spend limit warning thresholds."}
              </p>

              {mission.status === "ESCALATED" && (
                <div className="flex gap-2 mt-4 pt-3 border-t border-outline-variant/20">
                  <button
                    onClick={() => overrideMissionStatus(mission.id, "APPROVED")}
                    className="flex-1 h-8 rounded bg-secondary/15 hover:bg-secondary/25 border border-secondary/30 text-secondary text-[10px] font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1 cursor-pointer select-none active:scale-95"
                  >
                    <ShieldCheck className="w-3.5 h-3.5" /> Approve Claim
                  </button>
                  <button
                    onClick={() => overrideMissionStatus(mission.id, "REJECTED")}
                    className="flex-1 h-8 rounded bg-error/15 hover:bg-error/25 border border-error/30 text-error text-[10px] font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1 cursor-pointer select-none active:scale-95"
                  >
                    <Ban className="w-3.5 h-3.5" /> Reject Claim
                  </button>
                </div>
              )}
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
