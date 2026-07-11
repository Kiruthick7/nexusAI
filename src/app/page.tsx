"use client";

import React, { useEffect } from "react";
import { useStore } from "@/store/useStore";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { UploadPanel } from "@/components/dashboard/UploadPanel";
import { MissionTimeline } from "@/components/dashboard/MissionTimeline";
import { PlannerCard } from "@/components/dashboard/PlannerCard";
import { AgentCard } from "@/components/dashboard/AgentCard";
import { ArbiterCard } from "@/components/dashboard/ArbiterCard";
import { DecisionPanel } from "@/components/dashboard/DecisionPanel";
import { AuditTimeline } from "@/components/dashboard/AuditTimeline";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, HeartPulse, CheckSquare } from "lucide-react";

export default function Home() {
  const { activeTab, getActiveMission, theme, setTheme } = useStore();
  const mission = getActiveMission();

  // Initialize theme on mount
  useEffect(() => {
    // If the active mission changes, we can also suggest light or dark theme automatically
    // for demonstration match with the respective Stitch design!
    if (mission.id === "NEX-882-901") {
      setTheme("light");
    } else {
      setTheme("dark");
    }
  }, [mission.id, setTheme]);

  return (
    <div className={`flex flex-col h-screen w-full bg-background text-on-surface ${theme}`}>
      {/* Top Navbar */}
      <Navbar />

      <div className="flex h-[calc(100vh-64px)] w-full relative z-10">
        {/* Left Sidebar */}
        <Sidebar />

        {/* Main Workspace */}
        <div className="flex-1 flex flex-col overflow-hidden bg-background">
          <AnimatePresence mode="wait">
            {activeTab === "orchestration" && (
              <motion.main
                key="orchestration"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.35, ease: "easeOut" }}
                className="flex-1 flex flex-col lg:flex-row p-4 gap-4 overflow-hidden h-full"
              >
                {/* LEFT PANEL: Intake & Ingestion */}
                <UploadPanel />

                {/* CENTER PANEL: Live Orchestration Engine */}
                <div className="flex-[2] min-w-[360px] flex flex-col gap-4 h-full overflow-hidden">
                  <div className="flex items-center justify-between px-1 shrink-0">
                    <h3 className="text-[18px] font-semibold text-on-surface flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-primary animate-ping"></span>
                      Orchestration Flow
                    </h3>
                    <div className="flex items-center gap-2 select-none">
                      <span className="w-2 h-2 rounded-full bg-error pulse-dot shadow-[0_0_8px_rgba(255,180,171,0.6)]"></span>
                      <span className="font-mono text-[10px] text-error font-bold uppercase tracking-wider">
                        {mission.status === "REJECTED" ? "DUPLICATE INTAKE" : "CONFLICT DETECTED"}
                      </span>
                    </div>
                  </div>

                  {/* Stage Progress Breadcrumbs */}
                  <MissionTimeline />

                  {/* Flow Diagram Canvas */}
                  <div className="glass-panel rounded-lg flex-1 relative overflow-hidden border border-outline-variant/40 flex flex-col items-center justify-start pt-8 pb-4 px-4 shadow-sm select-none">
                    {/* SVG Connecting Flow Lines (Absolute behind) */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40 z-0">
                      {/* From Planner (Top center) to Agents (Row below) */}
                      <path
                        className="orch-line"
                        d="M 50% 80 Q 50% 120, 25% 150 T 25% 180"
                        fill="none"
                        stroke={theme === "dark" ? "#75db94" : "#515f74"}
                        strokeWidth="2"
                      />
                      <path
                        className="orch-line"
                        d="M 50% 80 Q 50% 120, 50% 150 T 50% 180"
                        fill="none"
                        stroke={theme === "dark" ? "#ffb77e" : "#006329"}
                        strokeWidth="2"
                      />
                      <path
                        className="orch-line"
                        d="M 50% 80 Q 50% 120, 75% 150 T 75% 180"
                        fill="none"
                        stroke={theme === "dark" ? "#ffb4ab" : "#ba1a1a"}
                        strokeWidth="2"
                      />
                      {/* From Agents to Arbiter (Bottom center) */}
                      <path
                        className="orch-line"
                        d="M 50% 280 Q 50% 320, 50% 350"
                        fill="none"
                        stroke={theme === "dark" ? "#b2c5ff" : "#0053db"}
                        strokeWidth="2"
                      />
                    </svg>

                    {/* Top Planner Agent Node */}
                    <PlannerCard />

                    {/* Middle Parallel Agents Row */}
                    <div className="w-full grid grid-cols-3 gap-3 relative z-10 mb-6">
                      <AgentCard agentKey="provider" />
                      <AgentCard agentKey="policy" />
                      <AgentCard agentKey="pattern" />
                    </div>

                    {/* Bottom Arbiter Resolution console */}
                    <ArbiterCard />
                  </div>
                </div>

                {/* RIGHT PANEL: Decision & Timeline */}
                <div className="flex-1 min-w-[280px] max-w-sm flex flex-col gap-4 h-full overflow-hidden">
                  <DecisionPanel />
                  <AuditTimeline />
                </div>
              </motion.main>
            )}

            {activeTab === "policy" && (
              <motion.main
                key="policy"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 p-8 text-left overflow-y-auto"
              >
                <div className="max-w-4xl mx-auto">
                  <div className="flex items-center gap-3 mb-6 border-b border-outline-variant/50 pb-4">
                    <ShieldCheck className="w-8 h-8 text-primary" />
                    <div>
                      <h1 className="text-3xl font-bold tracking-tight text-on-surface">Policy Auditor</h1>
                      <p className="text-sm text-on-surface-variant mt-1">Configure and audit corporate policy rules for automated claims adjudication.</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="glass-panel p-6 rounded-lg border border-outline-variant/55 flex flex-col gap-2">
                      <h3 className="text-sm font-bold text-on-surface uppercase tracking-wide">In-Network Max Limit</h3>
                      <p className="text-xs text-on-surface-variant">Automated trigger to escalate when an in-network provider claims amount exceeds thresholds.</p>
                      <span className="text-lg font-mono font-bold text-primary mt-2">$5,000.00 / Claim</span>
                    </div>
                    <div className="glass-panel p-6 rounded-lg border border-outline-variant/55 flex flex-col gap-2">
                      <h3 className="text-sm font-bold text-on-surface uppercase tracking-wide">Out-of-Network Max Limit</h3>
                      <p className="text-xs text-on-surface-variant">Automated trigger to escalate when an out-of-network provider claim exceeds thresholds.</p>
                      <span className="text-lg font-mono font-bold text-tertiary mt-2">$1,000.00 / Claim</span>
                    </div>
                  </div>
                </div>
              </motion.main>
            )}

            {activeTab === "health" && (
              <motion.main
                key="health"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 p-8 text-left overflow-y-auto"
              >
                <div className="max-w-4xl mx-auto">
                  <div className="flex items-center gap-3 mb-6 border-b border-outline-variant/50 pb-4">
                    <HeartPulse className="w-8 h-8 text-secondary" />
                    <div>
                      <h1 className="text-3xl font-bold tracking-tight text-on-surface">System Health</h1>
                      <p className="text-sm text-on-surface-variant mt-1">Real-time status indicators and metrics for connected LLMs, APIs, and OCR vision engines.</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 font-mono">
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/30">
                      <span className="text-[10px] text-on-surface-variant uppercase font-bold">Planner Model</span>
                      <span className="block text-lg font-bold text-secondary mt-1">ONLINE (100%)</span>
                    </div>
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/30">
                      <span className="text-[10px] text-on-surface-variant uppercase font-bold">OCR Vision Api</span>
                      <span className="block text-lg font-bold text-secondary mt-1">ONLINE (99.8%)</span>
                    </div>
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/30">
                      <span className="text-[10px] text-on-surface-variant uppercase font-bold">Arbitration Agent</span>
                      <span className="block text-lg font-bold text-secondary mt-1">ACTIVE</span>
                    </div>
                  </div>
                </div>
              </motion.main>
            )}

            {activeTab === "settings" && (
              <motion.main
                key="settings"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 p-8 text-left overflow-y-auto"
              >
                <div className="max-w-4xl mx-auto">
                  <div className="flex items-center gap-3 mb-6 border-b border-outline-variant/50 pb-4">
                    <CheckSquare className="w-8 h-8 text-on-surface-variant" />
                    <div>
                      <h1 className="text-3xl font-bold tracking-tight text-on-surface">Admin Settings</h1>
                      <p className="text-sm text-on-surface-variant mt-1">Manage project variables, administrator accounts, access credentials, and workspace mappings.</p>
                    </div>
                  </div>
                  <p className="text-xs text-on-surface-variant">Configure settings here. Integration with security backends will be completed in the next milestone.</p>
                </div>
              </motion.main>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
