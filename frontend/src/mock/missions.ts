export interface AgentState {
  name: string;
  role: string;
  status: "success" | "warning" | "pending" | "error";
  confidence: number;
  message: string;
}

export interface VerificationCheck {
  label: string;
  status: "success" | "warning" | "error" | "pending";
}

export interface AuditTrailEvent {
  time: string;
  title: string;
  status: "success" | "warning" | "error" | "info";
}

export interface Mission {
  id: string;
  invoiceName: string;
  invoiceSize: string;
  status: "REJECTED" | "ESCALATED" | "APPROVED";
  statusSubtext: string;
  category: string;
  amount: string;
  vendorName: string;
  gstin?: string;
  memberId?: string;
  dateOfService?: string;
  diagnosisCode?: string;
  duration: string;
  agentsUsed: number;
  extractedConfidence: number;
  verificationChecks: VerificationCheck[];
  agents: {
    planner: {
      name: string;
      role: string;
      message: string;
      logs: string[];
    };
    provider: AgentState;
    policy: AgentState;
    pattern: AgentState;
    arbiter: {
      name: string;
      title: string;
      message: string;
      logs: string[];
    };
  };
  audioDuration: string;
  audioWaveforms: number[];
  auditTrail: AuditTrailEvent[];
}

export const mockMissions: Record<string, Mission> = {
  "NEX-8829-X": {
    id: "NEX-8829-X",
    invoiceName: "Invoice-8829.pdf",
    invoiceSize: "2.4 MB",
    status: "REJECTED",
    statusSubtext: "EXECUTION REFUSED - HARD FLAG",
    category: "Hardware/IT",
    amount: "$4,250.00",
    vendorName: "Global Tech Solutions",
    gstin: "29AAACG1234F1Z5",
    duration: "4.2s",
    agentsUsed: 4,
    extractedConfidence: 99,
    verificationChecks: [
      { label: "GST Verified", status: "success" },
      { label: "Vendor Matched", status: "success" },
      { label: "MCP Endpoint Connected", status: "success" },
    ],
    agents: {
      planner: {
        name: "Planner Agent",
        role: "Orchestration & Dispatch",
        message: "Spawning parallel analysis paths for multi-vector billing conflict check.",
        logs: ["> spawn(workers, 3)", "> init_parallel_analysis()"],
      },
      provider: {
        name: "Provider Agent",
        role: "Entity Verification",
        status: "success",
        confidence: 99,
        message: "Entity verified",
      },
      policy: {
        name: "Policy Agent",
        role: "Corporate Rules Check",
        status: "pending",
        confidence: 70,
        message: "Checking travel limits...",
      },
      pattern: {
        name: "Pattern Agent",
        role: "Duplicity Detection",
        status: "error",
        confidence: 92,
        message: "Duplicate detected",
      },
      arbiter: {
        name: "Arbiter Agent",
        title: "CONFLICT: POLICY vs PATTERN",
        message: "Potential duplicate submission detected within 30-day window. Escaping to Tool Gate.",
        logs: [
          "> Processing historical patterns...",
          "> Cross-referencing Inv-8829 vs Inv-8102",
          "! Threshold ambiguity detected in 30-day window.",
          "> Escalating to Tool Gate.",
        ],
      },
    },
    audioDuration: "1:24",
    audioWaveforms: [20, 40, 60, 30, 10],
    auditTrail: [
      { time: "14:02:11.042", title: "Document ingested via API", status: "success" },
      { time: "14:02:12.184", title: "Vision models extracted 14 entities", status: "success" },
      { time: "14:02:14.992", title: "Parallel agent analysis initiated", status: "info" },
      { time: "14:02:15.221", title: "Execution halted at Tool Gate", status: "error" },
    ],
  },
  "NEX-882-901": {
    id: "NEX-882-901",
    invoiceName: "INV-2023-089.pdf",
    invoiceSize: "1.8 MB",
    status: "ESCALATED",
    statusSubtext: "HUMAN INTERVENTION REQUIRED",
    category: "Medical/Health",
    amount: "$1,250.00",
    vendorName: "City Health Clinic",
    memberId: "NEX-882-901",
    dateOfService: "Oct 24, 2023",
    diagnosisCode: "J01.90",
    duration: "2.1s",
    agentsUsed: 3,
    extractedConfidence: 98,
    verificationChecks: [
      { label: "Member Status Active", status: "success" },
      { label: "Diagnosis Code Code Valid", status: "success" },
      { label: "Clinic License Active", status: "success" },
    ],
    agents: {
      planner: {
        name: "Planner Agent",
        role: "Orchestration & Dispatch",
        message: "Delegating analysis tasks based on claim complexity level: Moderate.",
        logs: ["> spawn(workers, 3)"],
      },
      provider: {
        name: "Provider Agent",
        role: "Provider Verification",
        status: "success",
        confidence: 99,
        message: "Verified",
      },
      policy: {
        name: "Policy Agent",
        role: "Policy Check",
        status: "error",
        confidence: 95,
        message: "Out-of-network limits exceeded for J01.90.",
      },
      pattern: {
        name: "Pattern Agent",
        role: "Fraud Pattern Check",
        status: "success",
        confidence: 97,
        message: "Clear",
      },
      arbiter: {
        name: "Arbiter Agent",
        title: "RESOLVING POLICY CONFLICT",
        message: "Resolving policy conflict via historical precedent routing. Escaping to Human Review queue.",
        logs: [
          "> Reading claim history...",
          "> High similarity found in historical precedents",
          "! Out-of-network coverage threshold exceeded.",
          "> Escaping to Human Review queue.",
        ],
      },
    },
    audioDuration: "1:24",
    audioWaveforms: [10, 30, 20, 40, 5],
    auditTrail: [
      { time: "10:42 AM", title: "Document ingested via API.", status: "success" },
      { time: "10:43 AM", title: "Data parsed with 98% conf.", status: "success" },
      { time: "10:43 AM", title: "Policy violation flagged.", status: "error" },
      { time: "10:44 AM", title: "Routed to Human Queue.", status: "info" },
    ],
  },
};
