"use client";

import React, { useState } from "react";
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
import { mockMissions } from "@/mock/missions";
import {
  ShieldCheck,
  CheckSquare,
  Shield,
  FileText,
  Search,
  SlidersHorizontal,
  Cpu,
  Database,
  Cloud,
  FileImage,
  RefreshCw,
  Sparkles,
  Lock,
  ArrowRight,
  Server,
  PlayCircle
} from "lucide-react";

export default function Home() {
  const { activeTab, getActiveMission, theme, setActiveTab, setActiveMissionId, dataMode, setDataMode } = useStore();
  const mission = getActiveMission();

  // Local state for search/filters in Claims History
  const [historySearch, setHistorySearch] = useState("");
  const [historyStatusFilter, setHistoryStatusFilter] = useState<"ALL" | "APPROVED" | "REJECTED" | "ESCALATED">("ALL");

  // Local state for Receipt Parser mock interactions
  const [isParsing, setIsParsing] = useState(false);
  const [hoveredBox, setHoveredBox] = useState<string | null>(null);



  // Handle parsing trigger simulation
  const handleParseReceipt = () => {
    setIsParsing(true);
    setTimeout(() => {
      setIsParsing(false);
    }, 1500);
  };

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
            {/* 1. Orchestration & Mission Control */}
            {(activeTab === "orchestration" || activeTab === "claims") && (
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
                    {/* SVG Connecting Flow Lines */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40 z-0">
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

            {/* 2. Policy Auditor */}
            {activeTab === "policy" && (
              <motion.main
                key="policy"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 p-6 text-left overflow-y-auto"
              >
                <div className="max-w-5xl mx-auto">
                  <div className="flex items-center gap-3 mb-6 border-b border-outline-variant/30 pb-4">
                    <ShieldCheck className="w-8 h-8 text-primary" />
                    <div>
                      <h1 className="text-2xl font-bold tracking-tight text-on-surface">Policy Auditor</h1>
                      <p className="text-xs text-on-surface-variant mt-1">Configure and audit corporate policy rules for automated claims adjudication.</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="glass-panel p-5 rounded-lg border border-outline-variant/40 flex flex-col gap-2">
                      <h3 className="text-xs font-bold text-on-surface uppercase tracking-wide">In-Network Max Limit</h3>
                      <p className="text-xs text-on-surface-variant">Automated trigger to escalate when an in-network provider claims amount exceeds thresholds.</p>
                      <span className="text-lg font-mono font-bold text-primary mt-2">₹4,15,000.00 / Claim</span>
                    </div>
                    <div className="glass-panel p-5 rounded-lg border border-outline-variant/40 flex flex-col gap-2">
                      <h3 className="text-xs font-bold text-on-surface uppercase tracking-wide">Out-of-Network Max Limit</h3>
                      <p className="text-xs text-on-surface-variant">Automated trigger to escalate when an out-of-network provider claim exceeds thresholds.</p>
                      <span className="text-lg font-mono font-bold text-tertiary mt-2">₹83,000.00 / Claim</span>
                    </div>
                  </div>
                </div>
              </motion.main>
            )}

            {/* 3. Fraud Scanner (Pattern & Duplicates Analyzer) */}
            {activeTab === "fraud" && (
              <motion.main
                key="fraud"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 p-6 text-left overflow-y-auto"
              >
                <div className="max-w-5xl mx-auto">
                  <div className="flex items-center justify-between mb-6 border-b border-outline-variant/30 pb-4">
                    <div className="flex items-center gap-3">
                      <Shield className="w-8 h-8 text-error" />
                      <div>
                        <h1 className="text-2xl font-bold tracking-tight text-on-surface">Fraud Scanner</h1>
                        <p className="text-xs text-on-surface-variant mt-1">AI Pattern Recognition, anomalous activity detection, and historical duplication matching.</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 bg-error/10 border border-error/20 px-3 py-1.5 rounded-lg">
                      <span className="w-2 h-2 rounded-full bg-error animate-pulse"></span>
                      <span className="text-[10px] font-mono font-bold text-error uppercase tracking-wider">Guardrails Active</span>
                    </div>
                  </div>

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/40">
                      <span className="text-[10px] text-on-surface-variant uppercase font-bold tracking-wider">Overall Risk Index</span>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-2xl font-bold text-tertiary">34%</span>
                        <span className="text-[10px] text-on-surface-variant">Moderate</span>
                      </div>
                      <div className="w-full h-1.5 bg-surface-container rounded-full mt-2 overflow-hidden">
                        <div className="h-full bg-tertiary w-[34%]"></div>
                      </div>
                    </div>
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/40">
                      <span className="text-[10px] text-on-surface-variant uppercase font-bold tracking-wider">Anomalies Detected</span>
                      <span className="block text-2xl font-bold text-error mt-1">12</span>
                      <span className="text-[10px] text-on-surface-variant">Across 1,482 claims (30d)</span>
                    </div>
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/40">
                      <span className="text-[10px] text-on-surface-variant uppercase font-bold tracking-wider">Duplicate Matches</span>
                      <span className="block text-2xl font-bold text-primary mt-1">4 Blocks</span>
                      <span className="text-[10px] text-on-surface-variant">Prevented double billing</span>
                    </div>
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/40">
                      <span className="text-[10px] text-on-surface-variant uppercase font-bold tracking-wider">AI Scan Coverage</span>
                      <span className="block text-2xl font-bold text-secondary mt-1">100%</span>
                      <span className="text-[10px] text-on-surface-variant">Full ledger validation</span>
                    </div>
                  </div>

                  {/* Anomalous Activity Table */}
                  <div className="glass-panel rounded-lg border border-outline-variant/40 overflow-hidden shadow-sm">
                    <div className="p-4 border-b border-outline-variant/30 bg-surface-container/30 flex items-center justify-between">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface">Recent Security Flags</h3>
                      <SlidersHorizontal className="w-4 h-4 text-on-surface-variant cursor-pointer" />
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse min-w-[700px]">
                        <thead>
                          <tr className="border-b border-outline-variant/30 bg-surface-container/40">
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider">ID</th>
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider">Category</th>
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider">Conflict Reason</th>
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider text-right">Risk Score</th>
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider w-[120px]">Adjudication</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-outline-variant/30 text-xs font-medium">
                          <tr className="hover:bg-surface-container/20 transition-colors">
                            <td className="py-3 px-4 font-mono text-on-surface-variant">NEX-8829-X</td>
                            <td className="py-3 px-4">Hardware/IT</td>
                            <td className="py-3 px-4 text-error">Duplicate invoice ID (Ledger Collision)</td>
                            <td className="py-3 px-4 text-right font-mono text-error font-bold">89%</td>
                            <td className="py-3 px-4">
                              <span className="px-2 py-0.5 rounded bg-error/10 border border-error/30 text-[10px] text-error font-bold uppercase tracking-wider">REJECTED</span>
                            </td>
                          </tr>
                          <tr className="hover:bg-surface-container/20 transition-colors">
                            <td className="py-3 px-4 font-mono text-on-surface-variant">NEX-8902-A</td>
                            <td className="py-3 px-4">Medical/Supplies</td>
                            <td className="py-3 px-4 text-tertiary">Inflated treatment cost (Threshold Multiplier Exceeded)</td>
                            <td className="py-3 px-4 text-right font-mono text-tertiary font-bold">62%</td>
                            <td className="py-3 px-4">
                              <span className="px-2 py-0.5 rounded bg-tertiary/10 border border-tertiary/30 text-[10px] text-tertiary font-bold uppercase tracking-wider">ESCALATED</span>
                            </td>
                          </tr>
                          <tr className="hover:bg-surface-container/20 transition-colors">
                            <td className="py-3 px-4 font-mono text-on-surface-variant">NEX-7821-B</td>
                            <td className="py-3 px-4">Dental/Consultation</td>
                            <td className="py-3 px-4 text-on-surface-variant">Out-of-Network provider clustering</td>
                            <td className="py-3 px-4 text-right font-mono text-on-surface-variant font-bold">28%</td>
                            <td className="py-3 px-4">
                              <span className="px-2 py-0.5 rounded bg-secondary/10 border border-secondary/30 text-[10px] text-secondary font-bold uppercase tracking-wider">APPROVED</span>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </motion.main>
            )}

            {/* 4. Receipt Parser (OCR Multi-Modal View) */}
            {activeTab === "parser" && (
              <motion.main
                key="parser"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 p-6 text-left overflow-y-auto"
              >
                <div className="max-w-5xl mx-auto">
                  <div className="flex items-center gap-3 mb-6 border-b border-outline-variant/30 pb-4">
                    <FileText className="w-8 h-8 text-primary" />
                    <div>
                      <h1 className="text-2xl font-bold tracking-tight text-on-surface">Receipt Parser</h1>
                      <p className="text-xs text-on-surface-variant mt-1">Multi-Modal Document Layout OCR Extraction & confidence validation.</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
                    {/* Left: OCR Canvas View */}
                    <div className="lg:col-span-5 flex flex-col gap-4">
                      <div className="glass-panel p-4 rounded-lg border border-outline-variant/40 flex-1 flex flex-col">
                        <div className="flex justify-between items-center mb-3">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant flex items-center gap-1">
                            <FileImage className="w-3.5 h-3.5" /> Scan view
                          </span>
                          <span className="text-[10px] font-mono text-secondary bg-secondary/10 border border-secondary/20 px-2 py-0.5 rounded">
                            PDF Uploaded
                          </span>
                        </div>

                        {/* Interactive Receipt Scan Mock */}
                        <div className="border border-outline-variant/20 rounded-lg p-5 bg-surface-container-low flex-1 relative flex flex-col justify-start text-xs text-on-surface-variant font-mono gap-3 select-none overflow-hidden min-h-[320px]">
                          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent pointer-events-none opacity-40 animate-scan"></div>
                          
                          {/* Receipt Bounding Box Mock Overlays */}
                          <div className="border-b border-outline-variant/40 pb-2 text-center relative">
                            <div 
                              onMouseEnter={() => setHoveredBox("vendor")} 
                              onMouseLeave={() => setHoveredBox(null)}
                              className={`absolute inset-0 border border-primary/40 rounded transition-all cursor-pointer ${hoveredBox === "vendor" ? "bg-primary/20 scale-[1.02]" : "bg-primary/5"}`}
                            ></div>
                            <span className="text-sm font-bold text-on-surface">NEXUS MEDICAL CENTER</span>
                            <div className="text-[9px]">INVOICE #CLM-8921</div>
                          </div>

                          <div className="flex justify-between relative py-1">
                            <div 
                              onMouseEnter={() => setHoveredBox("date")} 
                              onMouseLeave={() => setHoveredBox(null)}
                              className={`absolute inset-0 border border-primary/40 rounded transition-all cursor-pointer ${hoveredBox === "date" ? "bg-primary/20 scale-[1.02]" : "bg-primary/5"}`}
                            ></div>
                            <span>DATE OF SERVICE:</span>
                            <span>OCT 24, 2023</span>
                          </div>

                          <div className="flex justify-between relative py-1">
                            <div 
                              onMouseEnter={() => setHoveredBox("member")} 
                              onMouseLeave={() => setHoveredBox(null)}
                              className={`absolute inset-0 border border-primary/40 rounded transition-all cursor-pointer ${hoveredBox === "member" ? "bg-primary/20 scale-[1.02]" : "bg-primary/5"}`}
                            ></div>
                            <span>MEMBER ID:</span>
                            <span>MEM-4071-B</span>
                          </div>

                          <div className="border-t border-dashed border-outline-variant/30 pt-2 flex flex-col gap-1">
                            <div className="flex justify-between">
                              <span>Consultation Fees</span>
                              <span>$850.00</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Lab Diagnostics</span>
                              <span>$400.00</span>
                            </div>
                          </div>

                          <div className="border-t border-outline-variant/40 pt-2 mt-auto flex justify-between font-bold text-on-surface text-sm relative py-1">
                            <div 
                              onMouseEnter={() => setHoveredBox("total")} 
                              onMouseLeave={() => setHoveredBox(null)}
                              className={`absolute inset-0 border border-primary/40 rounded transition-all cursor-pointer ${hoveredBox === "total" ? "bg-primary/20 scale-[1.02]" : "bg-primary/5"}`}
                            ></div>
                            <span>TOTAL PAID:</span>
                            <span>$1,250.00</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Right: Field Extraction Table */}
                    <div className="lg:col-span-7 flex flex-col gap-4">
                      <div className="glass-panel p-5 rounded-lg border border-outline-variant/40 flex flex-col h-full">
                        <div className="flex justify-between items-center mb-4">
                          <span className="text-xs font-bold uppercase tracking-wider text-on-surface">Extracted Parameters</span>
                          <button 
                            onClick={handleParseReceipt}
                            disabled={isParsing}
                            className="bg-primary-container text-on-primary-container font-label-sm text-[11px] py-1.5 px-3 rounded-lg flex items-center gap-1 hover:opacity-90 transition-opacity disabled:opacity-50"
                          >
                            <RefreshCw className={`w-3.5 h-3.5 ${isParsing ? "animate-spin" : ""}`} />
                            {isParsing ? "Re-scanning..." : "Run OCR Parser"}
                          </button>
                        </div>

                        <div className="flex-1 overflow-y-auto flex flex-col gap-3 font-mono text-xs">
                          {/* Parameter row 1: Vendor */}
                          <div className={`p-2.5 rounded-lg border transition-all ${hoveredBox === "vendor" ? "bg-primary/10 border-primary" : "border-outline-variant/20 bg-surface-container/30"}`}>
                            <div className="flex justify-between items-center mb-1">
                              <span className="font-bold text-on-surface">Vendor Name</span>
                              <span className="text-[10px] text-secondary font-bold">97.1% Conf.</span>
                            </div>
                            <span className="text-on-surface-variant font-sans">Nexus Medical Center</span>
                          </div>

                          {/* Parameter row 2: Date */}
                          <div className={`p-2.5 rounded-lg border transition-all ${hoveredBox === "date" ? "bg-primary/10 border-primary" : "border-outline-variant/20 bg-surface-container/30"}`}>
                            <div className="flex justify-between items-center mb-1">
                              <span className="font-bold text-on-surface">Service Date</span>
                              <span className="text-[10px] text-secondary font-bold">98.5% Conf.</span>
                            </div>
                            <span className="text-on-surface-variant font-sans">Oct 24, 2023</span>
                          </div>

                          {/* Parameter row 3: Member Id */}
                          <div className={`p-2.5 rounded-lg border transition-all ${hoveredBox === "member" ? "bg-primary/10 border-primary" : "border-outline-variant/20 bg-surface-container/30"}`}>
                            <div className="flex justify-between items-center mb-1">
                              <span className="font-bold text-on-surface">Member ID Reference</span>
                              <span className="text-[10px] text-secondary font-bold">99.2% Conf.</span>
                            </div>
                            <span className="text-on-surface-variant font-sans">MEM-4071-B</span>
                          </div>

                          {/* Parameter row 4: Total */}
                          <div className={`p-2.5 rounded-lg border transition-all ${hoveredBox === "total" ? "bg-primary/10 border-primary" : "border-outline-variant/20 bg-surface-container/30"}`}>
                            <div className="flex justify-between items-center mb-1">
                              <span className="font-bold text-on-surface">Invoice Total Amount</span>
                              <span className="text-[10px] text-secondary font-bold">99.8% Conf.</span>
                            </div>
                            <span className="text-on-surface-variant font-sans">$1,250.00 USD</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.main>
            )}

            {/* 5. Claims History */}
            {activeTab === "history" && (
              <motion.main
                key="history"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 p-6 text-left overflow-y-auto"
              >
                <div className="max-w-5xl mx-auto">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 border-b border-outline-variant/30 pb-4">
                    <div>
                      <h1 className="text-2xl font-bold tracking-tight text-on-surface">Claims History</h1>
                      <p className="text-xs text-on-surface-variant mt-1">Review and audit completed automated expense claim runs.</p>
                    </div>
                    <button 
                      onClick={() => setActiveTab("orchestration")}
                      className="bg-primary-container text-on-primary-container font-label-sm text-xs py-2 px-3 rounded-lg flex items-center gap-1.5 hover:opacity-90 transition-opacity"
                    >
                      <Sparkles className="w-4 h-4" /> Trigger New Run
                    </button>
                  </div>

                  {/* Filter Toolbar */}
                  <div className="flex flex-col sm:flex-row gap-3 justify-between items-center mb-4">
                    <div className="relative w-full sm:w-80">
                      <Search className="w-4 h-4 text-on-surface-variant absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={historySearch}
                        onChange={(e) => setHistorySearch(e.target.value)}
                        placeholder="Search claims by ID, submitter or vendor..."
                        className="w-full bg-surface-container-low border border-outline-variant/40 rounded-lg py-2 pl-[36px] pr-4 font-body-md text-xs text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-colors h-9"
                      />
                    </div>
                    <div className="flex gap-1 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
                      {(["ALL", "APPROVED", "REJECTED", "ESCALATED"] as const).map((filter) => (
                        <button
                          key={filter}
                          onClick={() => setHistoryStatusFilter(filter)}
                          className={`px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all whitespace-nowrap h-9 border ${
                            historyStatusFilter === filter
                              ? "bg-primary-container/20 text-primary border-primary/40"
                              : "bg-surface border-outline-variant/30 text-on-surface-variant hover:bg-surface-container"
                          }`}
                        >
                          {filter}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Claims List */}
                  <div className="glass-panel rounded-lg border border-outline-variant/40 overflow-hidden shadow-sm">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse min-w-[750px]">
                        <thead>
                          <tr className="border-b border-outline-variant/30 bg-surface-container/40">
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider w-[120px]">ID</th>
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider">Vendor & File</th>
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider text-right w-[110px]">Amount</th>
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider w-[120px]">Status</th>
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider w-[160px]">Confidence</th>
                            <th className="py-2.5 px-4 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider w-[100px] text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-outline-variant/30 text-xs font-medium">
                          {Object.values(mockMissions)
                            .filter((m) => {
                              // Filter by search text
                              if (historySearch) {
                                const term = historySearch.toLowerCase();
                                const matchId = m.id.toLowerCase().includes(term);
                                const matchVendor = m.vendorName.toLowerCase().includes(term);
                                const matchFile = m.invoiceName.toLowerCase().includes(term);
                                if (!matchId && !matchVendor && !matchFile) return false;
                              }
                              // Filter by status tab
                              if (historyStatusFilter !== "ALL" && m.status !== historyStatusFilter) {
                                return false;
                              }
                              return true;
                            })
                            .map((m) => (
                              <tr 
                                key={m.id}
                                onClick={() => {
                                  setActiveMissionId(m.id);
                                  setActiveTab("orchestration");
                                }}
                                className="hover:bg-surface-container/25 cursor-pointer transition-colors group"
                              >
                                <td className="py-3 px-4 font-mono text-primary group-hover:underline">{m.id}</td>
                                <td className="py-3 px-4">
                                  <div className="flex flex-col">
                                    <span className="text-on-surface">{m.vendorName}</span>
                                    <span className="text-[10px] text-on-surface-variant font-mono mt-0.5">{m.invoiceName} ({m.invoiceSize})</span>
                                  </div>
                                </td>
                                <td className="py-3 px-4 text-right font-mono font-semibold text-on-surface">{m.amount}</td>
                                <td className="py-3 px-4">
                                  <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${
                                    m.status === "APPROVED" 
                                      ? "bg-secondary-container/10 border-secondary/20 text-secondary"
                                      : m.status === "REJECTED"
                                      ? "bg-error-container/10 border-error/20 text-error"
                                      : "bg-tertiary-container/10 border-tertiary/20 text-tertiary"
                                  }`}>
                                    <span className={`w-1.5 h-1.5 rounded-full ${
                                      m.status === "APPROVED" ? "bg-secondary" : m.status === "REJECTED" ? "bg-error" : "bg-tertiary"
                                    }`}></span>
                                    {m.status}
                                  </div>
                                </td>
                                <td className="py-3 px-4">
                                  <div className="flex items-center gap-2">
                                    <div className="flex-1 h-1.5 bg-surface-container rounded-full overflow-hidden">
                                      <div className={`h-full ${
                                        m.extractedConfidence > 90 ? "bg-secondary" : m.extractedConfidence > 70 ? "bg-tertiary" : "bg-error"
                                      }`} style={{ width: `${m.extractedConfidence}%` }}></div>
                                    </div>
                                    <span className="font-mono text-[10px] text-on-surface-variant">{m.extractedConfidence}%</span>
                                  </div>
                                </td>
                                <td className="py-3 px-4 text-right">
                                  <button className="text-primary group-hover:text-primary-fixed transition-colors font-semibold text-[10px] flex items-center justify-end w-full gap-0.5">
                                    Audit <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                                  </button>
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </motion.main>
            )}

            {/* System Health */}
            {activeTab === "health" && (
              <motion.main
                key="health"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 p-6 text-left overflow-y-auto"
              >
                <div className="max-w-5xl mx-auto flex flex-col gap-6">
                  {/* Header */}
                  <div className="flex items-center gap-3 border-b border-outline-variant/30 pb-4">
                    <div className="w-10 h-10 rounded-lg bg-success-container/20 border border-secondary/30 flex items-center justify-center">
                      <Cpu className="w-6 h-6 text-secondary animate-pulse" />
                    </div>
                    <div>
                      <h1 className="text-2xl font-bold tracking-tight text-on-surface">System Health</h1>
                      <p className="text-xs text-on-surface-variant mt-1">Real-time status diagnostics, database pings, memory tracking, and agent heartbeat telemetries.</p>
                    </div>
                  </div>

                  {/* Top Status Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* API Server status */}
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/40 flex flex-col gap-1.5 relative overflow-hidden shadow-sm">
                      <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">FastAPI Server</span>
                      <div className="flex items-baseline gap-1.5 mt-1">
                        <span className="text-2xl font-mono font-bold text-on-surface">99.98%</span>
                        <span className="text-[10px] font-bold text-secondary uppercase">Uptime</span>
                      </div>
                      <div className="flex items-center gap-1.5 mt-2">
                        <span className="w-2 h-2 rounded-full bg-secondary animate-ping"></span>
                        <span className="text-[10px] font-semibold text-secondary font-mono">STATUS: HEALTHY</span>
                      </div>
                    </div>

                    {/* Postgres latency */}
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/40 flex flex-col gap-1.5 relative overflow-hidden shadow-sm">
                      <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Cloud SQL Latency</span>
                      <div className="flex items-baseline gap-1.5 mt-1">
                        <span className="text-2xl font-mono font-bold text-on-surface">2.4 ms</span>
                        <span className="text-[10px] font-bold text-secondary uppercase">Ping</span>
                      </div>
                      <div className="flex items-center gap-1.5 mt-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-secondary"></div>
                        <span className="text-[10px] font-semibold text-on-surface-variant font-mono">DB: nexus_claims</span>
                      </div>
                    </div>

                    {/* GCS Ingestion */}
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/40 flex flex-col gap-1.5 relative overflow-hidden shadow-sm">
                      <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Cloud Storage Bucket</span>
                      <div className="flex items-baseline gap-1.5 mt-1">
                        <span className="text-xl font-mono font-bold text-on-surface truncate">deepmind-hack...</span>
                      </div>
                      <div className="flex items-center gap-1.5 mt-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-secondary"></div>
                        <span className="text-[10px] font-semibold text-secondary font-mono">CONNECTED</span>
                      </div>
                    </div>

                    {/* BigQuery Stream */}
                    <div className="glass-panel p-4 rounded-lg border border-outline-variant/40 flex flex-col gap-1.5 relative overflow-hidden shadow-sm">
                      <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">BigQuery Dataset</span>
                      <div className="flex items-baseline gap-1.5 mt-1">
                        <span className="text-xl font-mono font-bold text-on-surface">nexus_claims_ds</span>
                      </div>
                      <div className="flex items-center gap-1.5 mt-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-secondary"></div>
                        <span className="text-[10px] font-semibold text-secondary font-mono">CONNECTED</span>
                      </div>
                    </div>
                  </div>

                  {/* Mid Section: Telemetry & Active Instances */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Left: Memory & Telemetry bars */}
                    <div className="lg:col-span-7 flex flex-col gap-4">
                      <div className="glass-panel p-5 rounded-lg border border-outline-variant/40 flex flex-col gap-4 shadow-sm text-left">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface flex items-center gap-1.5 border-b border-outline-variant/20 pb-2">
                          <Database className="w-4 h-4 text-primary" /> Telemetry diagnostics
                        </h3>

                        <div className="flex flex-col gap-4 mt-1">
                          {/* CPU */}
                          <div className="flex flex-col gap-1">
                            <div className="flex justify-between items-center text-[10px] font-bold">
                              <span className="text-on-surface-variant uppercase tracking-wider">CPU UTILIZATION</span>
                              <span className="text-on-surface font-mono">12.5%</span>
                            </div>
                            <div className="h-2 w-full bg-surface-container-high rounded-full overflow-hidden">
                              <div className="h-full bg-primary rounded-full transition-all duration-500" style={{ width: "12.5%" }}></div>
                            </div>
                          </div>

                          {/* Memory */}
                          <div className="flex flex-col gap-1">
                            <div className="flex justify-between items-center text-[10px] font-bold">
                              <span className="text-on-surface-variant uppercase tracking-wider">MEMORY FOOTPRINT</span>
                              <span className="text-on-surface font-mono">2.4 GB / 8 GB (30%)</span>
                            </div>
                            <div className="h-2 w-full bg-surface-container-high rounded-full overflow-hidden">
                              <div className="h-full bg-secondary rounded-full transition-all duration-500" style={{ width: "30%" }}></div>
                            </div>
                          </div>

                          {/* Network Bandwidth */}
                          <div className="flex flex-col gap-1">
                            <div className="flex justify-between items-center text-[10px] font-bold">
                              <span className="text-on-surface-variant uppercase tracking-wider">SSE CHANNEL BANDWIDTH</span>
                              <span className="text-on-surface font-mono">1.2 MB/s</span>
                            </div>
                            <div className="h-2 w-full bg-surface-container-high rounded-full overflow-hidden">
                              <div className="h-full bg-tertiary rounded-full transition-all duration-500" style={{ width: "15%" }}></div>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Active Agent Instances */}
                      <div className="glass-panel p-5 rounded-lg border border-outline-variant/40 flex flex-col gap-3 shadow-sm text-left">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface flex items-center gap-1.5 border-b border-outline-variant/20 pb-2">
                          <Cpu className="w-4 h-4 text-primary" /> Distributed Agent worker grid
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-1.5">
                          {[
                            { name: "Planner Agent Node", status: "ACTIVE", type: "primary" },
                            { name: "Provider Specialty Node", status: "IDLE", type: "secondary" },
                            { name: "Policy Evaluation Node", status: "IDLE", type: "secondary" },
                            { name: "Pattern Matching Node", status: "IDLE", type: "secondary" },
                            { name: "Arbiter Resolution Node", status: "IDLE", type: "secondary" },
                            { name: "Intake Classification Node", status: "IDLE", type: "secondary" }
                          ].map((node, idx) => (
                            <div key={idx} className="flex justify-between items-center border border-outline-variant/30 rounded-lg p-2.5 bg-surface-container/25 font-mono text-[10px]">
                              <span className="font-bold text-on-surface">{node.name}</span>
                              <span className={`px-2 py-0.5 rounded text-[9px] font-bold tracking-wider ${
                                node.status === "ACTIVE" 
                                  ? "bg-primary-container/20 border border-primary/30 text-primary"
                                  : "bg-secondary-container/10 border border-secondary/20 text-secondary"
                              }`}>{node.status}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Right: Live Diagnostics Console logs */}
                    <div className="lg:col-span-5 flex flex-col h-full">
                      <div className="glass-panel p-5 rounded-lg border border-outline-variant/40 flex flex-col flex-1 shadow-sm text-left h-full min-h-[350px]">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface flex items-center gap-1.5 border-b border-outline-variant/20 pb-2 shrink-0">
                          <Lock className="w-4 h-4 text-primary" /> Live diagnostics logstream
                        </h3>
                        <div className="flex-1 bg-surface-container-low border border-outline-variant/30 rounded-lg p-3 font-mono text-[10px] text-on-surface-variant overflow-y-auto flex flex-col gap-2 mt-3.5 h-[230px]">
                          <div className="flex gap-2">
                            <span className="text-primary">[10:09:18]</span>
                            <span className="text-secondary">[INFO]</span>
                            <span className="text-on-surface">nexus_ai starting microservices on host 127.0.0.1:8000</span>
                          </div>
                          <div className="flex gap-2">
                            <span className="text-primary">[10:09:19]</span>
                            <span className="text-error">[WARN]</span>
                            <span>[POLICY LOADER] Rules file not found at disk; fallback database active.</span>
                          </div>
                          <div className="flex gap-2">
                            <span className="text-primary">[10:09:19]</span>
                            <span className="text-secondary">[INFO]</span>
                            <span>FastAPI routing gateways established (65 passed tests).</span>
                          </div>
                          <div className="flex gap-2">
                            <span className="text-primary">[10:09:20]</span>
                            <span className="text-secondary">[INFO]</span>
                            <span>SSE subscription channels registered; waiting on client connection...</span>
                          </div>
                          <div className="flex gap-2">
                            <span className="text-primary">[10:09:24]</span>
                            <span className="text-secondary">[INFO]</span>
                            <span className="text-on-surface">Client connection established on SSE endpoint /api/v1/missions/stream</span>
                          </div>
                          <div className="flex gap-2">
                            <span className="text-primary">[10:10:05]</span>
                            <span className="text-secondary">[INFO]</span>
                            <span>Heartbeat ping completed successfully across 6 active nodes.</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.main>
            )}

            {/* 6. Admin Settings */}
            {activeTab === "settings" && (
              <motion.main
                key="settings"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="flex-1 p-6 text-left overflow-y-auto"
              >
                <div className="max-w-5xl mx-auto">
                  <div className="flex items-center gap-3 mb-6 border-b border-outline-variant/30 pb-4">
                    <CheckSquare className="w-8 h-8 text-primary" />
                    <div>
                      <h1 className="text-2xl font-bold tracking-tight text-on-surface">Admin Settings</h1>
                      <p className="text-xs text-on-surface-variant mt-1">Manage pipeline configurations, API credentials, models parameters, and database schemas.</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Left: Input Fields */}
                    <div className="lg:col-span-8 flex flex-col gap-5">
                      {/* Section 1: GCP Variables */}
                      <div className="glass-panel p-5 rounded-lg border border-outline-variant/40 flex flex-col gap-4">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface flex items-center gap-1.5 border-b border-outline-variant/20 pb-2">
                          <Cloud className="w-4 h-4 text-primary" /> Google Cloud Configurations
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                          <div className="flex flex-col gap-1">
                            <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">GCP Project ID</label>
                            <input 
                              type="text" 
                              defaultValue="deepmind-hack26blr-4071" 
                              disabled
                              className="bg-surface-container-low border border-outline-variant/40 rounded-lg p-2 font-mono text-[11px] text-on-surface outline-none cursor-not-allowed opacity-80 h-9"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">BigQuery Dataset ID</label>
                            <input 
                              type="text" 
                              defaultValue="nexus_claims_dataset" 
                              disabled
                              className="bg-surface-container-low border border-outline-variant/40 rounded-lg p-2 font-mono text-[11px] text-on-surface outline-none cursor-not-allowed opacity-80 h-9"
                            />
                          </div>
                          <div className="flex flex-col gap-1 sm:col-span-2">
                            <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Cloud Storage Bucket</label>
                            <input 
                              type="text" 
                              defaultValue="gs://deepmind-hack26blr-4071-bucket" 
                              disabled
                              className="bg-surface-container-low border border-outline-variant/40 rounded-lg p-2 font-mono text-[11px] text-on-surface outline-none cursor-not-allowed opacity-80 h-9"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Section 2: PostgreSQL Settings */}
                      <div className="glass-panel p-5 rounded-lg border border-outline-variant/40 flex flex-col gap-4">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface flex items-center gap-1.5 border-b border-outline-variant/20 pb-2">
                          <Database className="w-4 h-4 text-primary" /> Cloud SQL Database Instance
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                          <div className="flex flex-col gap-1">
                            <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Instance ID</label>
                            <input 
                              type="text" 
                              defaultValue="nexus-postgres-4071" 
                              disabled
                              className="bg-surface-container-low border border-outline-variant/40 rounded-lg p-2 font-mono text-[11px] text-on-surface outline-none cursor-not-allowed opacity-80 h-9"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Target Database</label>
                            <input 
                              type="text" 
                              defaultValue="nexus_claims" 
                              disabled
                              className="bg-surface-container-low border border-outline-variant/40 rounded-lg p-2 font-mono text-[11px] text-on-surface outline-none cursor-not-allowed opacity-80 h-9"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Username</label>
                            <input 
                              type="text" 
                              defaultValue="nexus_admin" 
                              disabled
                              className="bg-surface-container-low border border-outline-variant/40 rounded-lg p-2 font-mono text-[11px] text-on-surface outline-none cursor-not-allowed opacity-80 h-9"
                            />
                          </div>
                          <div className="flex flex-col gap-1">
                            <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">Connection Password</label>
                            <input 
                              type="password" 
                              defaultValue="•••••••••••••••••••••" 
                              disabled
                              className="bg-surface-container-low border border-outline-variant/40 rounded-lg p-2 font-mono text-[11px] text-on-surface outline-none cursor-not-allowed opacity-80 h-9"
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Right: Info Panels */}
                    <div className="lg:col-span-4 flex flex-col gap-4">
                      {/* Model Matrix Info */}
                      <div className="glass-panel p-4 rounded-lg border border-outline-variant/40 flex flex-col gap-3">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant flex items-center gap-1">
                          <Cpu className="w-3.5 h-3.5 text-primary" /> Active Model Matrix
                        </span>
                        <div className="flex flex-col gap-2.5 font-mono text-[10px]">
                          <div className="border border-outline-variant/20 rounded p-2 bg-surface-container/30">
                            <span className="font-bold block text-on-surface uppercase mb-0.5">Primary Planner</span>
                            <span className="text-on-surface-variant">gemini-3.5-flash</span>
                          </div>
                          <div className="border border-outline-variant/20 rounded p-2 bg-surface-container/30">
                            <span className="font-bold block text-on-surface uppercase mb-0.5">Live Translate Engine</span>
                            <span className="text-on-surface-variant">gemini-3.5-live-translate-preview</span>
                          </div>
                          <div className="border border-outline-variant/20 rounded p-2 bg-surface-container/30">
                            <span className="font-bold block text-on-surface uppercase mb-0.5">Audio/TTS Feed</span>
                            <span className="text-on-surface-variant">gemini-3.1-flash-tts-preview</span>
                          </div>
                          <div className="border border-outline-variant/20 rounded p-2 bg-surface-container/30">
                            <span className="font-bold block text-on-surface uppercase mb-0.5">Independent Explainer</span>
                            <span className="text-on-surface-variant">gemma2-27b-it</span>
                          </div>
                        </div>
                      </div>

                      {/* Credentials Mask */}
                      <div className="glass-panel p-4 rounded-lg border border-outline-variant/40 flex flex-col gap-3">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant flex items-center gap-1">
                          <Lock className="w-3.5 h-3.5 text-primary" /> Security Credentials
                        </span>
                        <div className="border border-outline-variant/20 rounded p-2.5 bg-surface-container/30 font-mono text-[10px] flex items-center justify-between">
                          <div className="flex flex-col">
                            <span className="font-bold text-on-surface uppercase">GEMINI API KEY</span>
                            <span className="text-on-surface-variant mt-0.5">AI_ZAy...f4CqY8</span>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-secondary/10 border border-secondary/20 text-secondary text-[9px] font-bold">LOADED</span>
                        </div>
                      </div>

                      {/* Pipeline Data Mode */}
                      <div className="glass-panel p-4 rounded-lg border border-outline-variant/40 flex flex-col gap-3">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant flex items-center gap-1">
                          <SlidersHorizontal className="w-3.5 h-3.5 text-primary" /> Ingestion Pipeline Mode
                        </span>
                        
                        <p className="text-[11px] text-on-surface-variant leading-relaxed text-left">
                          Toggle between mock simulated demonstration flows and active live GCP ingestion data feeds.
                        </p>

                        <div className="grid grid-cols-2 gap-2 mt-1">
                          <button
                            onClick={() => setDataMode("MOCK")}
                            className={`flex flex-col items-center justify-center p-3 rounded-lg border text-center transition-all duration-300 gap-1.5 ${
                              dataMode === "MOCK"
                                ? "bg-primary/10 border-primary text-primary shadow-[0_0_15px_rgba(255,110,64,0.15)]"
                                : "bg-surface-container/30 border-outline-variant/20 text-on-surface-variant hover:border-outline-variant/50 hover:bg-surface-container/50"
                            }`}
                          >
                            <PlayCircle className={`w-5 h-5 ${dataMode === "MOCK" ? "text-primary animate-pulse" : "text-on-surface-variant/60"}`} />
                            <div className="flex flex-col">
                              <span className="text-xs font-bold">Mock Demo</span>
                              <span className="text-[9px] opacity-60 font-medium">Local Sandbox</span>
                            </div>
                          </button>

                          <button
                            onClick={() => setDataMode("LIVE")}
                            className={`flex flex-col items-center justify-center p-3 rounded-lg border text-center transition-all duration-300 gap-1.5 ${
                              dataMode === "LIVE"
                                ? "bg-secondary/10 border-secondary text-secondary shadow-[0_0_15px_rgba(30,136,229,0.15)]"
                                : "bg-surface-container/30 border-outline-variant/20 text-on-surface-variant hover:border-outline-variant/50 hover:bg-surface-container/50"
                            }`}
                          >
                            <Server className={`w-5 h-5 ${dataMode === "LIVE" ? "text-secondary animate-pulse" : "text-on-surface-variant/60"}`} />
                            <div className="flex flex-col">
                              <span className="text-xs font-bold">Live Mode</span>
                              <span className="text-[9px] opacity-60 font-medium">GCS Ingestion</span>
                            </div>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.main>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
