import { create } from "zustand";
import { mockMissions, Mission, AuditTrailEvent } from "@/mock/missions";

export type SimulationStep =
  | "IDLE"
  | "INGESTING"
  | "PLANNING"
  | "ANALYZING"
  | "ARBITRATING"
  | "COMPLETED";

interface AppState {
  theme: "dark" | "light";
  activeTab:
    | "orchestration"
    | "claims"
    | "health"
    | "settings"
    | "dashboard"
    | "policy"
    | "fraud"
    | "parser"
    | "history";
  activeMissionId: string;
  isVoicePlaying: boolean;
  voiceProgress: number;
  sidebarCollapsed: boolean;

  // Simulation States
  isSimulating: boolean;
  simulationStep: SimulationStep;
  simulationScanProgress: number;
  simulationAgents: {
    provider: "idle" | "loading" | "success" | "warning" | "error" | "pending";
    policy: "idle" | "loading" | "success" | "warning" | "error" | "pending";
    pattern: "idle" | "loading" | "success" | "warning" | "error" | "pending";
  };
  simulationArbiterLogs: string[];
  simulationAuditTrail: AuditTrailEvent[];

  // Actions
  toggleTheme: () => void;
  setTheme: (theme: "dark" | "light") => void;
  setActiveTab: (tab: AppState["activeTab"]) => void;
  setActiveMissionId: (id: string) => void;
  startSimulation: (missionId?: string) => void;
  cancelSimulation: () => void;
  toggleVoicePlayback: () => void;
  setVoiceProgress: (progress: number) => void;
  toggleSidebar: () => void;
  getActiveMission: () => Mission;
}

// Global registry of running timeouts to prevent overlapping simulation loops
let activeTimers: NodeJS.Timeout[] = [];
const clearAllTimers = () => {
  activeTimers.forEach(clearTimeout);
  activeTimers = [];
};

export const useStore = create<AppState>((set, get) => ({
  theme: "dark",
  activeTab: "orchestration",
  activeMissionId: "NEX-8829-X",
  isVoicePlaying: false,
  voiceProgress: 35,
  sidebarCollapsed: false,

  // Simulation Defaults
  isSimulating: false,
  simulationStep: "IDLE",
  simulationScanProgress: 100,
  simulationAgents: {
    provider: "success",
    policy: "pending",
    pattern: "error",
  },
  simulationArbiterLogs: [],
  simulationAuditTrail: [],

  toggleTheme: () => {
    const nextTheme = get().theme === "dark" ? "light" : "dark";
    set({ theme: nextTheme });
    if (typeof window !== "undefined") {
      const root = window.document.documentElement;
      root.classList.remove("light", "dark");
      root.classList.add(nextTheme);
    }
  },

  setTheme: (theme) => {
    set({ theme });
    if (typeof window !== "undefined") {
      const root = window.document.documentElement;
      root.classList.remove("light", "dark");
      root.classList.add(theme);
    }
  },

  setActiveTab: (activeTab) => set({ activeTab }),

  setActiveMissionId: (activeMissionId) => {
    clearAllTimers();
    set({
      activeMissionId,
      isSimulating: false,
      simulationStep: "IDLE",
      simulationScanProgress: 100,
      isVoicePlaying: false,
      voiceProgress: 0,
    });
  },

  // State-of-the-art Simulation Playback Engine
  startSimulation: (missionId) => {
    clearAllTimers();
    const targetMissionId = missionId || get().activeMissionId;
    const mission = mockMissions[targetMissionId];

    set({
      isSimulating: true,
      activeMissionId: targetMissionId,
      simulationStep: "INGESTING",
      simulationScanProgress: 0,
      simulationArbiterLogs: [],
      simulationAuditTrail: [],
      simulationAgents: {
        provider: "idle",
        policy: "idle",
        pattern: "idle",
      },
      isVoicePlaying: false,
      voiceProgress: 0,
    });

    const pushTimer = (timer: NodeJS.Timeout) => {
      activeTimers.push(timer);
    };

    // Helper to get formatted timestamp
    const getTimestamp = (secOffset = 0) => {
      const now = new Date();
      now.setSeconds(now.getSeconds() + secOffset);
      return now.toLocaleTimeString("en-US", { hour12: false });
    };

    // --- PHASE 1: Document OCR Ingestion ---
    let progress = 0;
    const scanInterval = setInterval(() => {
      progress += 10;
      set({ simulationScanProgress: progress });

      if (progress === 10) {
        set((state) => ({
          simulationAuditTrail: [
            ...state.simulationAuditTrail,
            { time: getTimestamp(), title: `Document ${mission.invoiceName} Ingested via OCR`, status: "success" },
          ],
        }));
      } else if (progress === 50) {
        set((state) => ({
          simulationAuditTrail: [
            ...state.simulationAuditTrail,
            { time: getTimestamp(), title: "Vision Layout Engine parsing tables...", status: "success" },
          ],
        }));
      } else if (progress === 100) {
        clearInterval(scanInterval);

        // --- PHASE 2: Planning & Dispatch ---
        const planningTimer = setTimeout(() => {
          set({
            simulationStep: "PLANNING",
            simulationAuditTrail: [
              ...get().simulationAuditTrail,
              { time: getTimestamp(), title: "Entities extracted. Dispatching to Planner Agent Node", status: "success" },
            ],
            simulationAgents: {
              provider: "loading",
              policy: "loading",
              pattern: "loading",
            },
          });

          // --- PHASE 3: Parallel Worker Grid Processing ---
          const analysisTimer = setTimeout(() => {
            set({ simulationStep: "ANALYZING" });

            // Resolve Provider Agent first
            const r1 = setTimeout(() => {
              set((state) => ({
                simulationAgents: { ...state.simulationAgents, provider: "success" },
                simulationAuditTrail: [
                  ...state.simulationAuditTrail,
                  { time: getTimestamp(), title: "Provider Agent: Vendor and license verification verified", status: "success" },
                ],
              }));
            }, 1000);
            pushTimer(r1);

            // Resolve Policy Agent second
            const r2 = setTimeout(() => {
              const status = mission.agents.policy.status;
              set((state) => ({
                simulationAgents: { ...state.simulationAgents, policy: status },
                simulationAuditTrail: [
                  ...state.simulationAuditTrail,
                  {
                    time: getTimestamp(),
                    title: `Policy Agent: Check completed with outcome (${status.toUpperCase()})`,
                    status: status === "success" ? "success" : status === "pending" ? "info" : "error",
                  },
                ],
              }));
            }, 2000);
            pushTimer(r2);

            // Resolve Pattern Agent third
            const r3 = setTimeout(() => {
              const status = mission.agents.pattern.status;
              set((state) => ({
                simulationAgents: { ...state.simulationAgents, pattern: status },
                simulationAuditTrail: [
                  ...state.simulationAuditTrail,
                  {
                    time: getTimestamp(),
                    title: `Pattern Agent: Fraud & duplicate analysis completed (${status.toUpperCase()})`,
                    status: status === "success" ? "success" : status === "pending" ? "info" : "error",
                  },
                ],
              }));
            }, 3000);
            pushTimer(r3);

            // Transition to Conflict Arbitration
            const arbiterTransitionTimer = setTimeout(() => {
              set({
                simulationStep: "ARBITRATING",
                simulationAuditTrail: [
                  ...get().simulationAuditTrail,
                  { time: getTimestamp(), title: "Routing conflict detected: Escalating to Arbiter Agent", status: "info" },
                ],
              });

              // Stream Arbiter Logs line-by-line
              const logs = mission.agents.arbiter.logs;
              let currentLogIndex = 0;

              const logStreamer = setInterval(() => {
                if (currentLogIndex < logs.length) {
                  const nextLine = logs[currentLogIndex];
                  set((state) => ({
                    simulationArbiterLogs: [...state.simulationArbiterLogs, nextLine],
                  }));
                  currentLogIndex++;
                } else {
                  clearInterval(logStreamer);

                  // --- PHASE 5: Complete Resolution & Final Decision ---
                  const completionTimer = setTimeout(() => {
                    set({
                      simulationStep: "COMPLETED",
                      isSimulating: false,
                      simulationAuditTrail: [
                        ...get().simulationAuditTrail,
                        {
                          time: getTimestamp(),
                          title: `Workflow halted at Tool Gate: Status set to ${mission.status}`,
                          status: mission.status === "REJECTED" ? "error" : "warning",
                        },
                      ],
                    });
                  }, 1200);
                  pushTimer(completionTimer);
                }
              }, 900);
              // Store interval inside the active registry as well
              activeTimers.push(logStreamer as unknown as NodeJS.Timeout);

            }, 4200);
            pushTimer(arbiterTransitionTimer);

          }, 1500);
          pushTimer(analysisTimer);

        }, 800);
        pushTimer(planningTimer);
      }
    }, 150);

    // Keep interval reference safe in case user cancels
    activeTimers.push(scanInterval as unknown as NodeJS.Timeout);
  },

  cancelSimulation: () => {
    clearAllTimers();
    set({
      isSimulating: false,
      simulationStep: "IDLE",
      simulationScanProgress: 100,
    });
  },

  toggleVoicePlayback: () => {
    const isPlaying = !get().isVoicePlaying;
    set({ isVoicePlaying: isPlaying });
    if (isPlaying) {
      const interval = setInterval(() => {
        const { isVoicePlaying, voiceProgress } = get();
        if (!isVoicePlaying || voiceProgress >= 100) {
          clearInterval(interval);
          if (voiceProgress >= 100) {
            set({ isVoicePlaying: false, voiceProgress: 0 });
          }
        } else {
          set({ voiceProgress: voiceProgress + 2 });
        }
      }, 100);
      activeTimers.push(interval as unknown as NodeJS.Timeout);
    }
  },

  setVoiceProgress: (voiceProgress) => set({ voiceProgress }),

  toggleSidebar: () => set({ sidebarCollapsed: !get().sidebarCollapsed }),

  getActiveMission: () => {
    const { activeMissionId } = get();
    return mockMissions[activeMissionId] || mockMissions["NEX-8829-X"];
  },
}));
export type { AppState };
export { clearAllTimers };
