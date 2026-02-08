"use client";

import { useState } from "react";
import { PatientSidebar } from "@/components/PatientSidebar";
import { PatientDetail } from "@/components/PatientDetail";
import { CohortReportView } from "@/components/CohortReport";

type View = "patient" | "cohort";

export default function Home() {
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(
    null
  );
  const [view, setView] = useState<View>("patient");

  const handleSelectPatient = (id: string) => {
    setSelectedPatientId(id);
    setView("patient");
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <PatientSidebar
        selectedId={view === "patient" ? selectedPatientId : null}
        onSelect={handleSelectPatient}
        onCohortReport={() => setView("cohort")}
        showingCohort={view === "cohort"}
      />
      <main className="flex-1 overflow-y-auto bg-muted/30">
        {view === "cohort" ? (
          <CohortReportView />
        ) : selectedPatientId ? (
          <PatientDetail patientId={selectedPatientId} />
        ) : (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            <p>Select a patient to view their clinical data.</p>
          </div>
        )}
      </main>
    </div>
  );
}
