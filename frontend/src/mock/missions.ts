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
    invoiceName: "claim1.png",
    invoiceSize: "2.8 MB",
    status: "ESCALATED",
    statusSubtext: "HUMAN INTERVENTION REQUIRED",
    category: "Medical/Health",
    amount: "$400.00",
    vendorName: "Apollo Clinics",
    memberId: "ACN-5598842",
    dateOfService: "Sep 24, 2026",
    diagnosisCode: "M25.50",
    duration: "3.5s",
    agentsUsed: 3,
    extractedConfidence: 99,
    verificationChecks: [
      { label: "Member Status Active", status: "success" },
      { label: "Clinic License Active", status: "success" },
      { label: "Out-of-Network Limit Exceeded", status: "warning" },
    ],
    agents: {
      planner: {
        name: "Planner Agent",
        role: "Orchestration & Dispatch",
        message: "Delegating medical policy checks and provider validation paths.",
        logs: ["> spawn(workers, 3)"],
      },
      provider: {
        name: "Provider Agent",
        role: "Entity Verification",
        status: "success",
        confidence: 99,
        message: "Apollo Clinics matched on active license registries.",
      },
      policy: {
        name: "Policy Agent",
        role: "Corporate Rules Check",
        status: "warning",
        confidence: 95,
        message: "Consultation falls under Out-of-Network policy limits.",
      },
      pattern: {
        name: "Pattern Agent",
        role: "Duplicity Detection",
        status: "success",
        confidence: 97,
        message: "No duplicate billing flags found.",
      },
      arbiter: {
        name: "Arbiter Agent",
        title: "RESOLVING POLICY CONFLICT",
        message: "Out-of-Network coverage limit exceeded. Escaping to Human Review queue.",
        logs: [
          "> Reading claim history...",
          "> Checking travel & medical benefits...",
          "! Out-of-network coverage threshold exceeded.",
          "> Escaping to Human Review queue.",
        ],
      },
    },
    audioDuration: "1:12",
    audioWaveforms: [10, 30, 50, 80, 40, 20, 45, 60, 30, 15],
    auditTrail: [
      { time: "10:42 AM", title: "Document ingested via API", status: "success" },
      { time: "10:43 AM", title: "Data parsed with 99% conf.", status: "success" },
      { time: "10:43 AM", title: "Policy violation flagged", status: "warning" },
      { time: "10:44 AM", title: "Routed to Human Queue", status: "info" },
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
