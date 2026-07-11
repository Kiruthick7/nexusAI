"use client";

import React, { useEffect, useRef } from "react";
import { useStore } from "@/store/useStore";

export function AuditTimeline() {
  const { getActiveMission, isSimulating, simulationAuditTrail } = useStore();
  const mission = getActiveMission();
  const timelineEndRef = useRef<HTMLDivElement>(null);

  // Compute audit trail based on simulation modes
  const trailToShow = isSimulating ? simulationAuditTrail : mission.auditTrail;

  // Auto-scroll timeline logs to bottom as new event ticks are pushed
  useEffect(() => {
    if (timelineEndRef.current) {
      timelineEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [trailToShow]);

  return (
    <div className="glass-panel rounded-lg p-4 mt-1 flex-1 flex flex-col text-left">
      <h4 className="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/60 pb-2 mb-3.5 select-none">
        Audit Log
      </h4>
      
      {/* Timeline items container */}
      <div className="flex-1 flex flex-col gap-0 relative pl-4 border-l border-outline-variant/30 ml-2 py-1 max-h-[144px] overflow-y-auto log-stream">
        {trailToShow.length > 0 ? (
          trailToShow.map((event, idx) => {
            let dotColor = "bg-outline-variant";
            let dotShadow = "";
            let textColor = "text-on-surface";
            let timeColor = "text-on-surface-variant";

            if (event.status === "success") {
              dotColor = "bg-secondary";
            } else if (event.status === "info") {
              dotColor = "bg-primary pulse-dot";
            } else if (event.status === "error") {
              dotColor = "bg-error";
              dotShadow = "shadow-[0_0_8px_rgba(255,180,171,0.8)]";
              textColor = "text-error font-semibold";
              timeColor = "text-error/80";
            }

            return (
              <div key={idx} className="relative pb-4 last:pb-0 animate-pulse-once">
                {/* Timeline bubble bullet node */}
                <div
                  className={`absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full border-2 border-surface-container transition-all duration-300 ${dotColor} ${dotShadow}`}
                ></div>
                <span className={`font-mono text-[9px] block mb-0.5 tracking-wide ${timeColor}`}>
                  {event.time}
                </span>
                <span className={`text-xs block leading-normal ${textColor}`}>
                  {event.title}
                </span>
              </div>
            );
          })
        ) : (
          <div className="text-on-surface-variant/40 italic flex items-center justify-center h-full text-xs">
            Ingestion logs loading...
          </div>
        )}
        <div ref={timelineEndRef} />
      </div>
    </div>
  );
}
export default AuditTimeline;
