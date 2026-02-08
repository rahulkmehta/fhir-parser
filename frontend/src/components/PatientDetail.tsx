"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { getSnapshot } from "@/lib/api";
import { ClinicalOverview } from "@/components/ClinicalOverview";
import { TimelineView } from "@/components/TimelineView";
import { EligibilityView } from "@/components/EligibilityView";
import type { ClinicalSnapshot } from "@/types";

type Tab = "overview" | "timeline" | "eligibility";

interface Props {
  patientId: string;
}

function formatDOB(dateStr: string): string {
  try {
    return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "Clinical Overview" },
  { key: "eligibility", label: "Eligibility" },
  { key: "timeline", label: "Timeline" },
];

export function PatientDetail({ patientId }: Props) {
  const [snapshot, setSnapshot] = useState<ClinicalSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  useEffect(() => {
    setLoading(true);
    setError(null);
    setTab("overview");
    getSnapshot(patientId)
      .then(setSnapshot)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [patientId]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Loading patient data...
      </div>
    );
  }

  if (error || !snapshot) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-destructive">
        {error ?? "Patient not found."}
      </div>
    );
  }

  const { patient } = snapshot;

  return (
    <div className="mx-auto max-w-4xl p-6">
      {/* Patient header */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold">{patient.full_name}</h2>
          {patient.is_deceased && (
            <Badge variant="destructive">Deceased</Badge>
          )}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-sm text-muted-foreground">
          <span>{patient.age !== null ? `${patient.age} years old` : "Age unknown"}</span>
          <span className="text-border">|</span>
          <span className="capitalize">{patient.gender ?? "Unknown sex"}</span>
          {patient.birth_date && (
            <>
              <span className="text-border">|</span>
              <span>DOB: {formatDOB(patient.birth_date)}</span>
            </>
          )}
          {patient.city && patient.state && (
            <>
              <span className="text-border">|</span>
              <span>{patient.city}, {patient.state}</span>
            </>
          )}
          <span className="text-border">|</span>
          <span>MRN: <span className="font-mono text-xs">{patient.id}</span></span>
        </div>
      </div>

      {/* Segmented control */}
      <div className="mb-4 inline-flex rounded-md border bg-muted p-0.5 text-sm">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-sm px-4 py-1.5 font-medium transition-colors ${
              tab === t.key
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "overview" && <ClinicalOverview snapshot={snapshot} />}
      {tab === "eligibility" && <EligibilityView patientId={patientId} />}
      {tab === "timeline" && <TimelineView patientId={patientId} />}
    </div>
  );
}
