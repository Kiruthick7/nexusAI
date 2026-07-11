"use client";

import React from "react";
import { useStore } from "@/store/useStore";
import { CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";

interface AgentCardProps {
  agentKey: "provider" | "policy" | "pattern";
}

export function AgentCard({ agentKey }: AgentCardProps) {
  const { getActiveMission, isSimulating, simulationAgents } = useStore();
  const mission = getActiveMission();
  const staticAgent = mission.agents[agentKey];

  // Resolve status based on simulation modes
  const liveStatus = isSimulating ? simulationAgents[agentKey] : staticAgent.status;

  // Render variables
  let opacity = "opacity-100 scale-100";
  let borderColor = "border-outline-variant/60";
  let badgeColor = "bg-surface-variant text-on-surface-variant border-outline-variant/40";
  let textColor = "text-on-surface-variant";
  let glowColor = "";
  let StatusIcon = CheckCircle2;
  let displayMessage = staticAgent.message;

  if (liveStatus === "idle") {
    opacity = "opacity-30 scale-95";
    displayMessage = "Waiting in queue...";
  } else if (liveStatus === "loading") {
    borderColor = "border-primary/40 animate-pulse ring-1 ring-primary/20";
    badgeColor = "bg-primary/15 text-primary border-primary/20";
    textColor = "text-primary animate-pulse";
    glowColor = "shadow-[0_0_15px_rgba(178,197,255,0.15)]";
    StatusIcon = Loader2;
    displayMessage = "Analyzing records...";
  } else if (liveStatus === "success") {
    borderColor = "border-secondary/30";
    badgeColor = "bg-secondary/10 text-secondary border-secondary/20";
    textColor = "text-secondary";
    StatusIcon = CheckCircle2;
  } else if (liveStatus === "warning" || liveStatus === "pending") {
    borderColor = "border-tertiary/30";
    badgeColor = "bg-tertiary/10 text-tertiary border-tertiary/20";
    textColor = "text-tertiary";
    StatusIcon = Loader2; // Spinner!
  } else if (liveStatus === "error") {
    borderColor = "border-error/50 ring-1 ring-error/30";
    badgeColor = "bg-error/10 text-error border-error/30";
    textColor = "text-error font-semibold";
    glowColor = "shadow-[0_0_15px_rgba(255,180,171,0.15)]";
    StatusIcon = AlertTriangle;
  }

  return (
    <div
      className={`bg-surface-container-low border rounded-lg p-3.5 flex flex-col gap-2.5 relative overflow-hidden transition-all duration-300 shadow-sm ${borderColor} ${glowColor} ${opacity}`}
    >
      {/* Top semantic accent stripe */}
      <div
        className={`absolute top-0 left-0 w-full h-1 transition-all duration-300 ${
          liveStatus === "idle"
            ? "bg-outline-variant/40"
            : liveStatus === "loading"
            ? "bg-primary/40 animate-pulse"
            : liveStatus === "success"
            ? "bg-secondary/50"
            : liveStatus === "error"
            ? "bg-error"
            : "bg-tertiary/50"
        }`}
      ></div>

      <div className="flex justify-between items-center text-left">
        <span className="text-xs font-bold text-on-surface">{staticAgent.name}</span>
        {liveStatus !== "idle" && (
          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${badgeColor}`}>
            {staticAgent.confidence}%
          </span>
        )}
      </div>

      <div className={`flex items-center gap-1.5 text-xs mt-1 ${textColor} text-left`}>
        {liveStatus === "loading" || liveStatus === "pending" || (liveStatus === "warning" && agentKey === "policy") ? (
          <StatusIcon className="w-4 h-4 animate-spin shrink-0" />
        ) : (
          <StatusIcon className="w-4 h-4 shrink-0" />
        )}
        <span className="truncate" title={displayMessage}>
          {displayMessage}
        </span>
      </div>
    </div>
  );
}
export default AgentCard;
