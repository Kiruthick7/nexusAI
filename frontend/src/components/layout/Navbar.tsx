"use client";

import React, { useEffect, useState } from "react";
import { useStore } from "@/store/useStore";
import { Search, Bell, Moon, Sun, Cpu, Play, RefreshCw } from "lucide-react";
import { mockMissions } from "@/mock/missions";

export function Navbar() {
  const {
    theme,
    toggleTheme,
    activeTab,
    setActiveTab,
    activeMissionId,
    startSimulation,
    isSimulating,
    dataMode,
    liveMission,
  } = useStore();
  const [mounted, setSmounted] = useState(false);

  // Avoid hydration mismatched issues
  useEffect(() => {
    setSmounted(true);
    // Sync initial root element class
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(theme);
  }, [theme]);

  if (!mounted) return null;

  return (
    <header className="sticky top-0 z-50 flex justify-between items-center w-full px-6 h-16 border-b border-outline-variant bg-surface glass-panel">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <Cpu className="text-primary w-6 h-6 animate-pulse" />
          <span className="text-xl font-bold tracking-tight text-on-surface">Nexus AI</span>
        </div>
        <nav className="hidden md:flex gap-4 ml-6">
          {(["orchestration", "claims", "health", "settings"] as const).map((tab) => {
            const isTabActive =
              activeTab === tab ||
              (tab === "claims" && ["claims", "policy", "fraud", "parser", "history"].includes(activeTab));
            return (
              <button
                key={tab}
                onClick={() => {
                  if (tab === "claims") {
                    setActiveTab("history");
                  } else {
                    setActiveTab(tab);
                  }
                }}
                className={`font-label-sm text-xs uppercase tracking-wider py-2 px-3 rounded transition-all duration-200 ${
                  isTabActive
                    ? "bg-primary-container/20 text-primary border border-primary/30 font-bold shadow-[0_0_15px_rgba(0,82,204,0.15)]"
                    : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high"
                }`}
              >
                {tab === "orchestration" ? "Mission Control" : tab}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-4">
        {/* Claim Selector & Interactive Simulation Controls */}
        <div className="flex items-center gap-2 bg-surface-container-low border border-outline-variant/50 px-3 py-1 rounded-lg">
          <span className="text-[10px] uppercase font-bold text-on-surface-variant tracking-wider">Active Run:</span>
          <select
            value={activeMissionId}
            onChange={(e) => startSimulation(e.target.value)}
            className="bg-transparent text-xs font-semibold text-primary font-mono outline-none border-none cursor-pointer pr-1"
          >
            {dataMode === "LIVE" && liveMission && (
              <option value={liveMission.id} className="bg-surface text-on-surface font-mono">
                {liveMission.id} ({liveMission.status})
              </option>
            )}
            {Object.keys(mockMissions).map((id) => (
              <option key={id} value={id} className="bg-surface text-on-surface font-mono">
                {id} ({mockMissions[id].status})
              </option>
            ))}
          </select>
        </div>

        {/* Play Simulation Button */}
        <button
          onClick={() => startSimulation(activeMissionId)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-bold transition-all active:scale-[0.97] ${
            isSimulating
              ? "bg-secondary-container/20 text-secondary border-secondary/30 shadow-[0_0_15px_rgba(117,219,148,0.25)]"
              : "bg-primary text-on-primary border-primary hover:opacity-90 shadow-sm"
          }`}
          title="Run full agent execution playback simulation"
        >
          {isSimulating ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Running...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Simulate Run</span>
            </>
          )}
        </button>



        {/* Dark Mode Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-full hover:bg-surface-container-high text-on-surface-variant transition-colors duration-200"
          title={`Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`}
        >
          {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {/* User profile card */}
        <div className="w-px h-6 bg-outline-variant/60 ml-2"></div>

        <div className="flex items-center gap-2 ml-2">
          <div className="w-8 h-8 rounded-full bg-surface-variant border border-outline-variant overflow-hidden">
            <img
              alt="AI System Admin Profile"
              className="w-full h-full object-cover"
              src={
                theme === "dark"
                  ? "https://lh3.googleusercontent.com/aida-public/AB6AXuBTV9Xb9uC_dFOH8xS4TId9CmueXUiUFNkxxpLBPkW2uv5BSmWS2vJzVACvt7r7OKJnxjc5ElcvxWPZk-3iJyAQSgQe5oBgIDpZCl3Ku0MisW2iDIA_sjmGSlOtds-N_o5TEVcO0LzkT3pvo1gBFgmW0fCwBdR_gk27i3YhYoduCBW6kmEZhfreiuhoobkV6WoeVa4U1xSeXebhw48wFgmWQHsdT5pp_0TG6qbkRyH-9jWGxr7RIg-RsQ"
                  : "https://lh3.googleusercontent.com/aida-public/AB6AXuDkhlf6MBwXohivwvOa7jYlHzpqeXoEq8kIlaneQFXA11GGwvjfkTt9PSGl3e_04C5FD5ddwylncAcxSVFHSYKBeZiNDs53UtdMro4AS11w-ushxO_aK12o7Kj0DEeagGsESSfWWfTmrV6AjsC47149N5ZvfuMEkFi1MB4Nf1UyIX2y4-N8PszB7JBqJ0VUkGM8oTlvXZorjbwciyVKQbXnLUaCy2AqorhDT7NUjGqY3Uvv9M77nOW_yA"
              }
            />
          </div>
          <div className="hidden lg:flex flex-col text-left">
            <span className="text-xs font-semibold text-on-surface">Admin Session</span>
            <span className="text-[10px] text-on-surface-variant font-mono">ENV: {dataMode}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
export default Navbar;
