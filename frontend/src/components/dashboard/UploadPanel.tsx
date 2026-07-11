"use client";

import React from "react";
import { useStore } from "@/store/useStore";
import { Scan, FileText, CheckCircle2, CloudUpload } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function UploadPanel() {
  const {
    getActiveMission,
    isSimulating,
    simulationStep,
    simulationScanProgress,
    startSimulation,
    activeMissionId,
    isFreshUpload,
    dataMode,
  } = useStore();
  const mission = getActiveMission();

  const isScanning = isSimulating && simulationStep === "INGESTING";
  const scanProgress = simulationScanProgress;

  const [uploadedFile, setUploadedFile] = React.useState<{ name: string; size: string } | null>(null);
  const [isDragging, setIsDragging] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Reset custom uploaded file when switching active mission
  React.useEffect(() => {
    setUploadedFile(null);
  }, [activeMissionId]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile({
        name: file.name,
        size: file.size > 1024 * 1024 
          ? `${(file.size / (1024 * 1024)).toFixed(1)} MB` 
          : `${(file.size / 1024).toFixed(0)} KB`
      });
      
      // Smart OCR Mock Routing based on file name (only in MOCK mode)
      let targetId = activeMissionId;
      if (dataMode === "MOCK") {
        const fileNameLower = file.name.toLowerCase();
        if (fileNameLower.includes("apollo") || fileNameLower.includes("clinic") || fileNameLower.includes("claim1") || fileNameLower.includes("8829")) {
          targetId = "NEX-8829-X";
        } else if (fileNameLower.includes("health") || fileNameLower.includes("city") || fileNameLower.includes("89") || fileNameLower.includes("901")) {
          targetId = "NEX-882-901";
        }
      }
      
      startSimulation(targetId, file);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setUploadedFile({
        name: file.name,
        size: file.size > 1024 * 1024 
          ? `${(file.size / (1024 * 1024)).toFixed(1)} MB` 
          : `${(file.size / 1024).toFixed(0)} KB`
      });
      
      // Smart OCR Mock Routing based on file name (only in MOCK mode)
      let targetId = activeMissionId;
      if (dataMode === "MOCK") {
        const fileNameLower = file.name.toLowerCase();
        if (fileNameLower.includes("apollo") || fileNameLower.includes("clinic") || fileNameLower.includes("claim1") || fileNameLower.includes("8829")) {
          targetId = "NEX-8829-X";
        } else if (fileNameLower.includes("health") || fileNameLower.includes("city") || fileNameLower.includes("89") || fileNameLower.includes("901")) {
          targetId = "NEX-882-901";
        }
      }
      
      startSimulation(targetId, file);
    }
  };

  // Helpers to check visibility during active simulation streams
  const showVendor = !isFreshUpload && (!isSimulating || simulationStep !== "INGESTING" || scanProgress >= 30);
  const showId = !isFreshUpload && (!isSimulating || simulationStep !== "INGESTING" || scanProgress >= 60);
  const showCategory = !isFreshUpload && (!isSimulating || simulationStep !== "INGESTING" || scanProgress >= 90);
  const showChecks = !isFreshUpload && (!isSimulating || simulationStep !== "INGESTING");

  return (
    <div className="flex-1 min-w-[300px] max-w-sm flex flex-col gap-4 h-full overflow-y-auto log-stream pr-2">
      <div className="flex items-center justify-between">
        <h3 className="text-[18px] font-semibold text-on-surface flex items-center gap-2">
          <Scan className="text-primary w-5 h-5" />
          Intake &amp; OCR
        </h3>
      </div>

      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".pdf,.png,.jpg,.jpeg"
      />

      {/* Drag & Drop Area / Scanning Area */}
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={`glass-panel rounded-lg p-6 border-dashed border-2 flex flex-col items-center justify-center gap-2 relative overflow-hidden group transition-all duration-200 cursor-pointer select-none ${
          isDragging 
            ? "border-primary bg-primary/5 scale-[1.01]" 
            : "border-outline-variant hover:border-primary/50"
        }`}
      >
        <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
        
        {isScanning || isFreshUpload ? (
          <CloudUpload className={`w-12 h-12 text-primary mb-2 ${isScanning ? "animate-bounce" : "animate-pulse"}`} />
        ) : (
          <FileText className="w-12 h-12 text-on-surface-variant group-hover:text-primary transition-colors mb-2" />
        )}

        <span className="font-semibold text-xs text-on-surface">
          {isScanning 
            ? "Processing Document..." 
            : isFreshUpload 
              ? "Select or Drag & Drop invoice" 
              : (uploadedFile ? uploadedFile.name : mission.invoiceName)}
        </span>
        <span className="text-[11px] text-on-surface-variant font-mono">
          {isFreshUpload 
            ? "Supported: PDF, PNG, JPG • Max 5MB" 
            : `${(uploadedFile ? uploadedFile.size : mission.invoiceSize)} • ${isScanning ? `${scanProgress}%` : "Processed"}`}
        </span>

        {!isScanning && (
          <span className="text-[10px] text-primary/80 group-hover:text-primary font-medium tracking-wide mt-1.5 animate-pulse">
            {isFreshUpload ? "Click here to upload receipt" : "Click or Drag & Drop to upload new"}
          </span>
        )}

        {/* Dynamic Scan Laser Line Overlay */}
        {isScanning && (
          <div className="absolute top-0 left-0 w-full h-[2px] bg-primary shadow-[0_0_8px_#b2c5ff] z-20 animate-scan"></div>
        )}
      </div>

      {/* Extracted Entity Fields Checklist */}
      <div className="glass-panel rounded-lg p-4 flex flex-col gap-3 mt-1">
        <div className="text-[11px] font-mono text-on-surface-variant uppercase tracking-widest border-b border-outline-variant/60 pb-2 mb-1 flex justify-between select-none">
          <span>Extracted Entities</span>
          {isScanning ? (
            <span className="text-primary animate-pulse font-bold">PARSING...</span>
          ) : isFreshUpload ? (
            <span className="text-on-surface-variant font-bold opacity-60">EMPTY</span>
          ) : (
            <span className="text-secondary font-bold animate-pulse">LIVE</span>
          )}
        </div>

        {isFreshUpload && (
          <div className="flex flex-col items-center justify-center py-6 px-4 border border-dashed border-outline-variant/40 rounded-md bg-surface-container-low/30 text-center gap-2 select-none">
            <Scan className="w-8 h-8 text-on-surface-variant opacity-40 animate-pulse" />
            <span className="text-xs font-semibold text-on-surface/80">Awaiting Claim Upload</span>
            <p className="text-[10px] text-on-surface-variant leading-relaxed max-w-[200px]">
              Upload a claim document above to begin real-time extraction.
            </p>
          </div>
        )}

        <AnimatePresence mode="popLayout">
          {showVendor && (
            <motion.div
              key="vendor"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex justify-between items-center bg-surface-container-low p-2 rounded border border-outline-variant/50"
            >
              <div className="flex flex-col text-left">
                <span className="text-[10px] uppercase font-bold text-on-surface-variant">Vendor</span>
                <span className="text-sm text-on-surface font-semibold">{mission.vendorName}</span>
              </div>
              <div className="flex items-center gap-1 bg-secondary-container/20 text-secondary px-2 py-1 rounded text-[10px] font-mono border border-secondary/30 shadow-[0_0_5px_rgba(117,219,148,0.2)]">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary pulse-dot"></span> {mission.extractedConfidence}%
              </div>
            </motion.div>
          )}

          {showId && (
            <motion.div
              key="memberId"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex justify-between items-center bg-surface-container-low p-2 rounded border border-outline-variant/50"
            >
              <div className="flex flex-col text-left">
                <span className="text-[10px] uppercase font-bold text-on-surface-variant">
                  {mission.gstin ? "GSTIN" : "Member ID"}
                </span>
                <span className="text-sm text-on-surface font-mono tracking-wider font-semibold">
                  {mission.gstin || mission.memberId}
                </span>
              </div>
              <div className="flex items-center gap-1 bg-secondary-container/20 text-secondary px-2 py-1 rounded text-[10px] font-mono border border-secondary/30 shadow-[0_0_5px_rgba(117,219,148,0.2)]">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary pulse-dot"></span> {mission.extractedConfidence - 1}%
              </div>
            </motion.div>
          )}

          {showCategory && (
            <motion.div
              key="category"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex justify-between items-center bg-surface-container-low p-2 rounded border border-outline-variant/50"
            >
              <div className="flex flex-col text-left">
                <span className="text-[10px] uppercase font-bold text-on-surface-variant">Category</span>
                <span className="text-sm text-on-surface font-semibold">{mission.category}</span>
              </div>
              <div className="flex items-center gap-1 bg-tertiary-container/20 text-tertiary px-2 py-1 rounded text-[10px] font-mono border border-tertiary/30 shadow-[0_0_5px_rgba(255,183,126,0.2)]">
                <span className="w-1.5 h-1.5 rounded-full bg-tertiary pulse-dot"></span> {mission.extractedConfidence - 14}%
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Verification Checklist */}
      <AnimatePresence>
        {showChecks && (
          <motion.div
            key="checklist"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="glass-panel rounded-lg p-4 flex flex-col gap-2.5 mt-1 border-l-2 border-l-secondary text-left overflow-hidden"
          >
            {mission.verificationChecks.map((check, idx) => (
              <div key={idx} className="flex items-center gap-2 text-secondary text-xs font-semibold">
                <CheckCircle2 className="w-4 h-4 text-secondary shrink-0" />
                <span>{check.label}</span>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
export default UploadPanel;
