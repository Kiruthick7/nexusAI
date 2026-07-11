"use client";

import React, { useEffect, useRef } from "react";
import { useStore } from "@/store/useStore";
import { Scale } from "lucide-react";

export function ArbiterCard() {
  const { getActiveMission, isSimulating, simulationStep, simulationArbiterLogs, isFreshUpload } = useStore();
  const mission = getActiveMission();
  const arbiter = mission.agents.arbiter;
  const consoleEndRef = useRef<HTMLDivElement>(null);

  // Compute active highlight states
  const isActive = !isFreshUpload && (!isSimulating || simulationStep === "ARBITRATING" || simulationStep === "COMPLETED");

  // Compute logs to show: dynamic simulated lines vs. static complete logs
  const logsToShow = isFreshUpload ? [] : (isSimulating ? simulationArbiterLogs : arbiter.logs);

  // Auto-scroll terminal logs to bottom on new append streams
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logsToShow]);

  return (
    <div
      className={`relative z-10 w-full md:w-5/6 bg-surface border-2 rounded-lg p-4 mt-auto shadow-[0_10px_30px_rgba(0,0,0,0.35)] backdrop-blur-md transition-all duration-300 ${
        isActive
          ? "border-primary/40 opacity-100 scale-100"
          : "border-outline-variant/30 opacity-30 scale-95"
      }`}
    >
      {/* Absolute badge floating centered on top border */}
      <div
        className={`absolute -top-3.5 left-1/2 -translate-x-1/2 bg-surface border-2 rounded-full px-3 py-1 flex items-center gap-1.5 shadow-sm transition-colors duration-300 ${
          isActive ? "border-primary/40" : "border-outline-variant/30"
        }`}
      >
        <Scale className={`w-3.5 h-3.5 transition-colors ${isActive ? "text-primary animate-pulse" : "text-on-surface-variant/40"}`} />
        <span className={`font-mono text-[10px] font-bold tracking-wider transition-colors ${isActive ? "text-primary" : "text-on-surface-variant/40"}`}>
          {arbiter.name}
        </span>
      </div>

      <div className="text-center mt-1.5 mb-3.5 select-none">
        <h4 className={`text-xs font-bold tracking-wider uppercase transition-colors ${isActive ? "text-error" : "text-on-surface-variant/40"}`}>
          {isActive ? arbiter.title : "IDLE QUEUE"}
        </h4>
      </div>

      {/* Terminal log console */}
      <div className="bg-surface-container p-3 rounded border border-outline-variant/30 font-mono text-[11px] text-on-surface-variant leading-relaxed text-left h-28 shadow-inner select-text overflow-y-auto log-stream">
        {isFreshUpload ? (
          <div className="text-on-surface-variant/40 italic flex items-center justify-center h-full">
            Awaiting claim receipt to initialize Arbiter...
          </div>
        ) : isActive ? (
          logsToShow.map((log, idx) => {
            const isWarn = log.startsWith("!") || log.includes("warning") || log.includes("ambiguity") || log.includes("exceeded");
            const isError = log.includes("Error") || log.includes("conflict") || log.includes("halted");
            let promptColor = "text-primary";
            let textColor = "text-on-surface-variant";

            if (isWarn) {
              promptColor = "text-tertiary";
              textColor = "text-tertiary font-medium";
            } else if (isError) {
              promptColor = "text-error";
              textColor = "text-error font-semibold";
            }

            return (
              <div key={idx} className="mb-0.5 animate-pulse-once">
                <span className={`mr-1.5 font-bold ${promptColor}`}>{log.startsWith(">") || log.startsWith("!") ? log.charAt(0) : ">"}</span>
                <span className={textColor}>
                  {log.startsWith(">") || log.startsWith("!") ? log.substring(1).trim() : log}
                </span>
              </div>
            );
          })
        ) : (
          <div className="text-on-surface-variant/40 italic flex items-center justify-center h-full">
            Waiting for orchestration dispatch triggers...
          </div>
        )}
        <div ref={consoleEndRef} />
      </div>
    </div>
  );
}
export default ArbiterCard;
