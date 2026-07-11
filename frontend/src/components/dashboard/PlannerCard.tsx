"use client";

import React from "react";
import { useStore } from "@/store/useStore";
import { Bot } from "lucide-react";

export function PlannerCard() {
  const { getActiveMission, isSimulating, simulationStep, isFreshUpload } = useStore();
  const mission = getActiveMission();
  const planner = mission.agents.planner;

  // Compute active highlight states
  const isActive = !isFreshUpload && (!isSimulating || simulationStep !== "INGESTING");
  const isPulse = !isFreshUpload && isSimulating && simulationStep === "PLANNING";

  return (
    <div
      className={`relative z-10 flex flex-col items-center mb-8 transition-all duration-300 ${
        isActive ? "opacity-100 scale-100" : "opacity-40 scale-95"
      }`}
    >
      <div
        className={`w-14 h-14 bg-surface-container-highest border-2 rounded-xl flex items-center justify-center transition-all duration-300 ${
          isPulse
            ? "border-primary animate-pulse shadow-[0_0_25px_#b2c5ff]"
            : isActive
            ? "border-primary shadow-[0_0_20px_rgba(178,197,255,0.25)]"
            : "border-outline-variant"
        }`}
      >
        <Bot className={`w-7 h-7 transition-colors ${isActive ? "text-primary" : "text-on-surface-variant/40"}`} />
      </div>
      <div className="flex flex-col items-center mt-2.5">
        <span className="font-mono text-[11px] text-on-surface bg-surface px-2.5 py-0.5 rounded border border-outline-variant/60 font-bold tracking-wide shadow-sm">
          {planner.name}
        </span>
        <span className="text-[10px] text-on-surface-variant font-medium mt-1">
          {isPulse ? "Analyzing dispatch routes..." : planner.role}
        </span>
      </div>
    </div>
  );
}
export default PlannerCard;
