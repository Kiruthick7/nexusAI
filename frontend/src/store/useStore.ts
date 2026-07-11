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
  dataMode: "MOCK" | "LIVE";
  overriddenMissions: Record<string, "APPROVED" | "REJECTED">;
  liveMission: Mission | null;

  // Simulation States
  isFreshUpload: boolean;
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
  startSimulation: (missionId?: string, file?: File) => void;
  startLiveSimulation: (file: File) => Promise<void>;
  cancelSimulation: () => void;
  resetToFreshUpload: () => void;
  toggleVoicePlayback: () => void;
  setVoiceProgress: (progress: number) => void;
  toggleSidebar: () => void;
  getActiveMission: () => Mission;
  setDataMode: (mode: "MOCK" | "LIVE") => void;
  overrideMissionStatus: (id: string, status: "APPROVED" | "REJECTED") => void;
}

// Global registry of running timeouts to prevent overlapping simulation loops
let activeTimers: NodeJS.Timeout[] = [];
let activeEventSource: EventSource | null = null;
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const clearAllTimers = () => {
  activeTimers.forEach(clearTimeout);
  activeTimers = [];
  if (activeEventSource) {
    activeEventSource.close();
    activeEventSource = null;
  }
};

export const useStore = create<AppState>((set, get) => ({
  theme: "dark",
  activeTab: "orchestration",
  activeMissionId: "NEX-8829-X",
  isVoicePlaying: false,
  voiceProgress: 35,
  sidebarCollapsed: false,
  dataMode: "LIVE",
  overriddenMissions: {},
  liveMission: null,

  // Simulation Defaults
  isFreshUpload: true, // Default to empty file drop zone on startup
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
      isFreshUpload: false, // Show past run static details instantly
      isSimulating: false,
      simulationStep: "IDLE",
      simulationScanProgress: 100,
      isVoicePlaying: false,
      voiceProgress: 0,
    });
  },

  resetToFreshUpload: () => {
    clearAllTimers();
    set({
      isFreshUpload: true,
      isSimulating: false,
      simulationStep: "IDLE",
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
  },

  // State-of-the-art Simulation Playback Engine
  startSimulation: (missionId, file) => {
    clearAllTimers();

    if (get().dataMode === "LIVE" && file) {
      get().startLiveSimulation(file);
      return;
    }

    const targetMissionId = missionId || get().activeMissionId;
    const mission = mockMissions[targetMissionId];

    set({
      isFreshUpload: false,
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

  startLiveSimulation: async (file: File) => {
    clearAllTimers();
    
    // 1. Initial State for Live Mode Ingestion
    set({
      isFreshUpload: false,
      isSimulating: true,
      simulationStep: "INGESTING",
      simulationScanProgress: 15,
      simulationArbiterLogs: [],
      simulationAuditTrail: [
        {
          time: new Date().toLocaleTimeString("en-US", { hour12: false }),
          title: `Uploading file ${file.name} to Live Ingestion server...`,
          status: "info"
        }
      ],
      simulationAgents: {
        provider: "idle",
        policy: "idle",
        pattern: "idle",
      },
      isVoicePlaying: false,
      voiceProgress: 0,
      liveMission: {
        id: "RUN-LIVE",
        invoiceName: file.name,
        invoiceSize: file.size > 1024 * 1024 
          ? `${(file.size / (1024 * 1024)).toFixed(1)} MB` 
          : `${(file.size / 1024).toFixed(0)} KB`,
        status: "ESCALATED",
        statusSubtext: "INGESTING DOCUMENT...",
        category: "Processing...",
        amount: "...",
        vendorName: "Reading document...",
        duration: "12s",
        agentsUsed: 3,
        extractedConfidence: 0,
        verificationChecks: [],
        agents: {
          planner: { name: "Planner Agent", role: "Orchestration & Dispatch", message: "Awaiting logs...", logs: [] },
          provider: { name: "Provider Agent", role: "Validation", status: "pending", confidence: 0, message: "Awaiting..." },
          policy: { name: "Policy Agent", role: "Rules & Limits", status: "pending", confidence: 0, message: "Awaiting..." },
          pattern: { name: "Pattern Agent", role: "Fraud Scan", status: "pending", confidence: 0, message: "Awaiting..." },
          arbiter: { name: "Arbiter Agent", title: "ARBITRATION", message: "Awaiting...", logs: [] }
        },
        audioDuration: "0:25",
        audioWaveforms: [12, 18, 45, 15, 32, 22, 10, 8, 30, 20],
        auditTrail: [],
      }
    });

    try {
      // 2. Submit Claim to FastAPI backend
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/claims`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Ingestion request failed");
      }

      const responseData = await response.json();
      const { mission_id, claim_id } = responseData;

      // Update states with sequential identifiers
      set((state) => {
        if (!state.liveMission) return {};
        return {
          activeMissionId: claim_id,
          simulationScanProgress: 40,
          liveMission: {
            ...state.liveMission,
            id: claim_id,
          },
          simulationAuditTrail: [
            ...state.simulationAuditTrail,
            {
              time: new Date().toLocaleTimeString("en-US", { hour12: false }),
              title: `Live Ingestion Registered as Claim ${claim_id}`,
              status: "success"
            }
          ]
        };
      });

      // 3. Establish SSE Connection
      activeEventSource = new EventSource(`${API_URL}/claims/${mission_id}/events`);

      activeEventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const eventType = data.event_type;
          const severity = data.severity || "INFO";
          const title = data.title || "Log update";
          const message = data.message || "";
          const confidence = data.confidence || 0;
          const timestampStr = data.timestamp || new Date().toISOString();
          const eventTime = new Date(timestampStr).toLocaleTimeString("en-US", { hour12: false });

          // Helper status converter
          const mapSeverity = (sev: string) => {
            if (sev === "SUCCESS") return "success";
            if (sev === "ERROR") return "error";
            if (sev === "WARN") return "warning";
            return "info";
          };

          // Append log to general timeline audit trail
          if (title && eventType !== "field_extracted") {
            set((state) => ({
              simulationAuditTrail: [
                ...state.simulationAuditTrail,
                { time: eventTime, title: title + (message ? `: ${message}` : ""), status: mapSeverity(severity) }
              ]
            }));
          }

          // Handle specific event checkpoint triggers
          switch (eventType) {
            case "workflow_started":
              set({ simulationScanProgress: 45 });
              break;

            case "intake_started":
              set({ simulationScanProgress: 60 });
              break;

            case "field_extracted": {
              const { field, value } = data.metadata || {};
              const conf = data.confidence || 95;
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                if (field === "vendor_name") {
                  updated.vendorName = String(value);
                  updated.extractedConfidence = conf;
                } else if (field === "amount") {
                  updated.amount = typeof value === "number" ? `$${value.toFixed(2)}` : String(value);
                } else if (field === "category") {
                  updated.category = String(value);
                } else if (field === "employee_id") {
                  updated.memberId = String(value);
                } else if (field === "date") {
                  updated.dateOfService = String(value);
                }
                return { liveMission: updated };
              });
              break;
            }

            case "extraction_completed":
              const isClassificationError = data.status === "error";
              if (isClassificationError) {
                // If not a valid invoice, display the classification rejection error beautifully!
                set((state) => {
                  if (!state.liveMission) return {};
                  const updated = { ...state.liveMission };
                  updated.status = "REJECTED";
                  updated.statusSubtext = `DOCUMENT REJECTED: ${message.toUpperCase()}`;
                  updated.vendorName = "INVALID DOCUMENT";
                  updated.amount = "N/A";
                  updated.category = "Invalid";
                  return {
                    liveMission: updated,
                    simulationScanProgress: 100,
                    simulationStep: "COMPLETED",
                    isSimulating: false,
                  };
                });
                if (activeEventSource) {
                  activeEventSource.close();
                  activeEventSource = null;
                }
              } else {
                set((state) => {
                  if (!state.liveMission) return {};
                  const updated = { ...state.liveMission };
                  updated.statusSubtext = "ORCHESTRATION IN PROGRESS...";
                  return {
                    liveMission: updated,
                    simulationScanProgress: 100,
                    simulationStep: "PLANNING",
                  };
                });
              }
              break;

            case "planner_started":
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                updated.agents.planner.message = message;
                return { liveMission: updated };
              });
              break;

            case "planner_dispatch":
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                updated.agents.planner.logs = [...updated.agents.planner.logs, message];
                return {
                  liveMission: updated,
                  simulationStep: "ANALYZING",
                  simulationAgents: {
                    provider: "loading",
                    policy: "loading",
                    pattern: "loading",
                  }
                };
              });
              break;

            case "provider_started":
              set((state) => ({ simulationAgents: { ...state.simulationAgents, provider: "loading" } }));
              break;

            case "provider_completed": {
              const statusVal: "success" | "warning" | "pending" | "error" = data.status === "error" ? "error" : data.status === "warning" ? "warning" : "success";
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                updated.agents.provider.status = statusVal;
                updated.agents.provider.confidence = confidence || 99;
                updated.agents.provider.message = message;
                
                // Add a dynamic verification check list entry!
                const newCheck = { label: "Provider Status " + statusVal.toUpperCase(), status: statusVal };
                updated.verificationChecks = [...updated.verificationChecks, newCheck];

                return {
                  liveMission: updated,
                  simulationAgents: { ...state.simulationAgents, provider: statusVal }
                };
              });
              break;
            }

            case "policy_started":
              set((state) => ({ simulationAgents: { ...state.simulationAgents, policy: "loading" } }));
              break;

            case "policy_completed": {
              const statusVal: "success" | "warning" | "pending" | "error" = data.status === "error" ? "error" : data.status === "warning" ? "warning" : "success";
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                updated.agents.policy.status = statusVal;
                updated.agents.policy.confidence = confidence || 95;
                updated.agents.policy.message = message;

                // Add a dynamic verification check list entry!
                const newCheck = { label: "Policy Validation " + statusVal.toUpperCase(), status: statusVal };
                updated.verificationChecks = [...updated.verificationChecks, newCheck];

                return {
                  liveMission: updated,
                  simulationAgents: { ...state.simulationAgents, policy: statusVal }
                };
              });
              break;
            }

            case "pattern_started":
              set((state) => ({ simulationAgents: { ...state.simulationAgents, pattern: "loading" } }));
              break;

            case "pattern_completed": {
              const statusVal: "success" | "warning" | "pending" | "error" = data.status === "error" ? "error" : data.status === "warning" ? "warning" : "success";
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                updated.agents.pattern.status = statusVal;
                updated.agents.pattern.confidence = confidence || 97;
                updated.agents.pattern.message = message;

                // Add a dynamic verification check list entry!
                const newCheck = { label: "Pattern Duplicate Check " + statusVal.toUpperCase(), status: statusVal };
                updated.verificationChecks = [...updated.verificationChecks, newCheck];

                return {
                  liveMission: updated,
                  simulationAgents: { ...state.simulationAgents, pattern: statusVal }
                };
              });
              break;
            }

            case "conflict_detected":
            case "arbiter_started":
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                updated.agents.arbiter.message = message;
                const formattedMessage = message || "Conflict detected: Escalating to Arbiter Agent node";
                updated.agents.arbiter.logs = [...updated.agents.arbiter.logs, formattedMessage];
                return {
                  liveMission: updated,
                  simulationStep: "ARBITRATING",
                  simulationArbiterLogs: [...state.simulationArbiterLogs, formattedMessage]
                };
              });
              break;

            case "arbiter_completed":
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                updated.agents.arbiter.logs = [...updated.agents.arbiter.logs, message];
                return {
                  liveMission: updated,
                  simulationArbiterLogs: [...state.simulationArbiterLogs, message]
                };
              });
              break;

            case "gate_check":
              // Append log message to Arbiter logs
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                const formattedMessage = `[GATE CHECK] ${message}`;
                updated.agents.arbiter.logs = [...updated.agents.arbiter.logs, formattedMessage];
                return {
                  liveMission: updated,
                  simulationArbiterLogs: [...state.simulationArbiterLogs, formattedMessage]
                };
              });
              break;

            case "human_required":
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                updated.status = "ESCALATED";
                updated.statusSubtext = "HUMAN INTERVENTION REQUIRED";
                return {
                  liveMission: updated,
                  simulationStep: "COMPLETED",
                  isSimulating: false,
                };
              });
              if (activeEventSource) {
                activeEventSource.close();
                activeEventSource = null;
              }
              break;

            case "decision": {
              const outcome = data.status === "success" ? "APPROVED" : data.status === "error" ? "REJECTED" : "ESCALATED";
              set((state) => {
                if (!state.liveMission) return {};
                const updated = { ...state.liveMission };
                updated.status = outcome;
                updated.statusSubtext = message || `CLAIM ${outcome}`;
                return { liveMission: updated };
              });
              break;
            }

            case "workflow_completed":
              set({
                simulationStep: "COMPLETED",
                isSimulating: false,
              });
              if (activeEventSource) {
                activeEventSource.close();
                activeEventSource = null;
              }
              break;
          }
        } catch (err) {
          console.error("Error processing live SSE stream payload:", err);
        }
      };

      activeEventSource.onerror = (err) => {
        // If we are no longer simulating, or the simulation has already completed,
        // this connection close is expected at the end of the SSE stream. Do not log as an error.
        if (!activeEventSource || !get().isSimulating || get().simulationStep === "COMPLETED") {
          return;
        }

        console.error("SSE Streaming Connection Lost:", err);
        set((state) => ({
          isSimulating: false,
          simulationStep: "COMPLETED",
          simulationAuditTrail: [
            ...state.simulationAuditTrail,
            {
              time: new Date().toLocaleTimeString("en-US", { hour12: false }),
              title: "SSE Connection lost or completed",
              status: "warning"
            }
          ]
        }));
        if (activeEventSource) {
          activeEventSource.close();
          activeEventSource = null;
        }
      };

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to reach server";
      console.error("Failed to upload claim and connect to live backend:", err);
      set((state) => ({
        isSimulating: false,
        simulationStep: "COMPLETED",
        simulationAuditTrail: [
          ...state.simulationAuditTrail,
          {
            time: new Date().toLocaleTimeString("en-US", { hour12: false }),
            title: `Live Ingestion Error: ${errorMsg}`,
            status: "error"
          },
          {
            time: new Date().toLocaleTimeString("en-US", { hour12: false }),
            title: `Please ensure your FastAPI backend is running on ${API_URL}`,
            status: "info"
          }
        ]
      }));
    }
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

    if (typeof window !== "undefined" && window.speechSynthesis) {
      if (isPlaying) {
        window.speechSynthesis.cancel();
        const activeMission = get().getActiveMission();
        const text = activeMission.status === "REJECTED"
          ? `Automated adjudication summary for claim ID ${activeMission.id}. The claim from ${activeMission.vendorName} for ${activeMission.amount} has been rejected due to a duplicate intake check. Potential duplicate submission detected within 30 day window. Invoice highly similar to previous approval.`
          : `Automated adjudication summary for claim ID ${activeMission.id}. The claim from ${activeMission.vendorName} for ${activeMission.amount} has been escalated due to a policy conflict. Claim requires manual review due to unresolvable policy conflict regarding out of network coverage.`;
        
        const utterance = new SpeechSynthesisUtterance(text);
        ((window as unknown) as { _activeUtterance?: SpeechSynthesisUtterance })._activeUtterance = utterance;
        
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => v.lang.startsWith("en-") && (v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("Samantha") || v.name.includes("Microsoft")));
        if (preferredVoice) {
          utterance.voice = preferredVoice;
        }
        utterance.rate = 1.05;
        
        utterance.onend = () => {
          set({ isVoicePlaying: false, voiceProgress: 0 });
        };
        
        utterance.onerror = () => {
          set({ isVoicePlaying: false, voiceProgress: 0 });
        };

        window.speechSynthesis.speak(utterance);

        const interval = setInterval(() => {
          const { isVoicePlaying, voiceProgress } = get();
          if (!isVoicePlaying || voiceProgress >= 100) {
            clearInterval(interval);
            if (voiceProgress >= 100) {
              set({ isVoicePlaying: false, voiceProgress: 0 });
              window.speechSynthesis.cancel();
            }
          } else {
            set({ voiceProgress: voiceProgress + 1.5 });
          }
        }, 150);
        activeTimers.push(interval as unknown as NodeJS.Timeout);
      } else {
        window.speechSynthesis.cancel();
        set({ voiceProgress: 0 });
      }
    } else {
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
    }
  },

  setVoiceProgress: (voiceProgress) => set({ voiceProgress }),

  toggleSidebar: () => set({ sidebarCollapsed: !get().sidebarCollapsed }),

  getActiveMission: () => {
    const { activeMissionId, overriddenMissions, dataMode, liveMission } = get();
    if (dataMode === "LIVE" && liveMission) {
      if (overriddenMissions[liveMission.id]) {
        return {
          ...liveMission,
          status: overriddenMissions[liveMission.id],
          statusSubtext: overriddenMissions[liveMission.id] === "APPROVED" ? "MANUAL OVERRIDE - APPROVED" : "MANUAL OVERRIDE - REJECTED",
        };
      }
      return liveMission;
    }
    const mission = mockMissions[activeMissionId] || mockMissions["NEX-8829-X"];
    if (overriddenMissions[mission.id]) {
      return {
        ...mission,
        status: overriddenMissions[mission.id],
        statusSubtext: overriddenMissions[mission.id] === "APPROVED" ? "MANUAL OVERRIDE - APPROVED" : "MANUAL OVERRIDE - REJECTED",
      };
    }
    return mission;
  },

  overrideMissionStatus: (id, status) => {
    const updated = { ...get().overriddenMissions, [id]: status };
    set({ overriddenMissions: updated });

    // Inject a beautiful audit log timeline event
    const time = new Date().toLocaleTimeString("en-US", { hour: '2-digit', minute: '2-digit', hour12: true });
    const logEvent = {
      time,
      title: `Adjudicator override: Claim manually ${status.toLowerCase()}`,
      status: status === "APPROVED" ? ("success" as const) : ("error" as const),
    };
    
    // Check if simulationAuditTrail is active, else append to it
    set({
      simulationAuditTrail: [...get().simulationAuditTrail, logEvent]
    });
  },

  setDataMode: (dataMode) => {
    clearAllTimers();
    set({
      dataMode,
      activeMissionId: dataMode === "MOCK" ? "NEX-8829-X" : "RUN-LIVE",
      isFreshUpload: true,
      isSimulating: false,
      simulationStep: "IDLE",
      simulationScanProgress: 100,
      liveMission: null,
      simulationArbiterLogs: [],
      simulationAuditTrail: [],
    });
  },
}));
export type { AppState };
export { clearAllTimers };
