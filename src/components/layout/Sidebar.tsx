"use client";

import React from "react";
import { useStore } from "@/store/useStore";
import {
  Network,
  ShieldCheck,
  Shield,
  FileText,
  History,
  Plus,
  HelpCircle,
  BookOpen,
} from "lucide-react";

export function Sidebar() {
  const { activeTab, setActiveTab, startSimulation, isSimulating, activeMissionId } = useStore();

  const navItems = [
    { id: "orchestration", label: "Orchestration", icon: Network },
    { id: "policy", label: "Policy Auditor", icon: ShieldCheck },
    { id: "fraud", label: "Fraud Scanner", icon: Shield },
    { id: "parser", label: "Receipt Parser", icon: FileText },
    { id: "history", label: "History", icon: History },
  ] as const;

  return (
    <aside className="hidden lg:flex flex-col h-full w-64 border-r border-outline-variant bg-surface-container p-4 gap-2 shrink-0 z-20">
      {/* Brand Header */}
      <div className="flex items-center gap-3 mb-6 px-2 border-b border-outline-variant pb-4">
        <div className="w-10 h-10 rounded bg-primary-container flex items-center justify-center text-on-primary-container font-bold border border-primary/20">
          NX
        </div>
        <div>
          <h2 className="font-label-sm text-xs font-bold text-on-surface">Nexus AI Ops</h2>
          <span className="font-label-sm text-[10px] text-on-surface-variant font-bold uppercase tracking-wider">
            HACKATHON-DEMO
          </span>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 flex flex-col gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-xs font-semibold ${
                isActive
                  ? "bg-primary-container text-on-primary-container font-bold translate-x-1 shadow-[0_0_15px_rgba(0,82,204,0.15)] border border-primary/20"
                  : "text-on-surface-variant hover:bg-surface-variant hover:text-on-surface"
              }`}
            >
              <Icon className="w-[18px] h-[18px]" />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Footer / CTA Actions */}
      <div className="mt-auto flex flex-col gap-2">
        <button
          onClick={() => startSimulation(activeMissionId)}
          disabled={isSimulating}
          className="w-full py-2.5 px-4 bg-primary text-on-primary text-xs font-bold rounded-lg hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          {isSimulating ? "Orchestrating..." : "New Analysis"}
        </button>

        <div className="h-px w-full bg-outline-variant/60 my-1"></div>

        <a
          href="#"
          className="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-variant hover:text-on-surface rounded-lg transition-all text-xs font-semibold"
        >
          <BookOpen className="w-[18px] h-[18px]" />
          Documentation
        </a>
        <a
          href="#"
          className="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-variant hover:text-on-surface rounded-lg transition-all text-xs font-semibold"
        >
          <HelpCircle className="w-[18px] h-[18px]" />
          Support
        </a>
      </div>
    </aside>
  );
}
export default Sidebar;
