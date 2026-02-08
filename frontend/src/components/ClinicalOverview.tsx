"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { ClinicalSnapshot, ObservationSummary } from "@/types";

interface Props {
  snapshot: ClinicalSnapshot;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "Date unknown";
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function ObservationCard({
  label,
  obs,
  missingText,
}: {
  label: string;
  obs: ObservationSummary | null;
  missingText: string;
}) {
  if (!obs) {
    return (
      <div className="rounded-md border border-dashed border-muted-foreground/30 p-3">
        <div className="text-xs font-medium text-muted-foreground">{label}</div>
        <div className="mt-1 text-sm italic text-muted-foreground/60">
          {missingText}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-md border p-3">
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold tabular-nums">
        {obs.value ?? "No value"}
      </div>
      <div className="mt-0.5 text-xs text-muted-foreground">
        {formatDate(obs.date)}
      </div>
      <div className="mt-0.5 font-mono text-[10px] text-muted-foreground/50">
        Source FHIR: {obs.id}
      </div>
    </div>
  );
}

export function ClinicalOverview({ snapshot }: Props) {
  const { active_conditions, recent_procedures, key_observations, missing_data } =
    snapshot;

  const hasBP =
    key_observations.systolic_bp && key_observations.diastolic_bp;

  return (
    <div className="space-y-4">
      {/* Missing data warnings */}
      {missing_data.length > 0 && (
        <Card className="border-amber-300 bg-amber-50">
          <CardContent className="py-3">
            <div className="text-sm font-medium text-amber-900">
              Missing Clinical Data
            </div>
            <ul className="mt-1 space-y-0.5">
              {missing_data.map((msg) => (
                <li key={msg} className="text-sm text-amber-800">
                  - {msg}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Key observations */}
      <Card>
        <CardHeader className="pb-1">
          <CardTitle className="text-sm">Key Observations</CardTitle>
          <CardDescription className="text-xs">Most recent BMI, blood pressure, weight, and height by LOINC code</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            <ObservationCard
              label="BMI"
              obs={key_observations.bmi}
              missingText="No BMI recorded"
            />
            {hasBP ? (
              <div className="rounded-md border p-3">
                <div className="text-xs font-medium text-muted-foreground">
                  Blood Pressure
                </div>
                <div className="mt-1 text-lg font-semibold tabular-nums">
                  {key_observations.systolic_bp!.value_numeric}/
                  {key_observations.diastolic_bp!.value_numeric} mmHg
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  {formatDate(key_observations.systolic_bp!.date)}
                </div>
                <div className="mt-0.5 font-mono text-[10px] text-muted-foreground/50">
                  Source FHIR: {key_observations.systolic_bp!.id}
                </div>
              </div>
            ) : (
              <ObservationCard
                label="Blood Pressure"
                obs={null}
                missingText="No BP recorded"
              />
            )}
            <ObservationCard
              label="Weight"
              obs={key_observations.weight}
              missingText="No weight recorded"
            />
            <ObservationCard
              label="Height"
              obs={key_observations.height}
              missingText="No height recorded"
            />
          </div>
        </CardContent>
      </Card>

      {/* Active conditions */}
      <Card>
        <CardHeader className="pb-1">
          <CardTitle className="text-sm">
            Active Conditions ({active_conditions.length})
          </CardTitle>
          <CardDescription className="text-xs">Conditions with clinical status &quot;active&quot;, excluding social and administrative findings</CardDescription>
        </CardHeader>
        <CardContent>
          {active_conditions.length === 0 ? (
            <p className="text-sm italic text-muted-foreground">
              No active conditions recorded.
            </p>
          ) : (
            <div>
              {active_conditions.map((c, i) => (
                <div key={c.id}>
                  {i > 0 && <Separator />}
                  <div className="flex items-start justify-between py-2">
                    <div>
                      <div className="text-sm">{c.display}</div>
                      <div className="mt-0.5 font-mono text-[10px] text-muted-foreground/50">
                        SNOMED {c.code} · Source FHIR: {c.id}
                      </div>
                    </div>
                    <div className="shrink-0 text-right text-xs text-muted-foreground">
                      {c.onset_date ? `Onset: ${formatDate(c.onset_date)}` : "Onset: unknown"}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent procedures */}
      <Card>
        <CardHeader className="pb-1">
          <CardTitle className="text-sm">
            Recent Procedures ({recent_procedures.length})
          </CardTitle>
          <CardDescription className="text-xs">Last 10 procedures by performed date</CardDescription>
        </CardHeader>
        <CardContent>
          {recent_procedures.length === 0 ? (
            <p className="text-sm italic text-muted-foreground">
              No procedures recorded.
            </p>
          ) : (
            <div>
              {recent_procedures.map((p, i) => (
                <div key={p.id}>
                  {i > 0 && <Separator />}
                  <div className="flex items-start justify-between py-2">
                    <div>
                      <div className="text-sm">{p.display}</div>
                      <div className="mt-0.5 font-mono text-[10px] text-muted-foreground/50">
                        Source FHIR: {p.id}
                      </div>
                    </div>
                    <div className="shrink-0 text-right">
                      <div className="text-xs text-muted-foreground">
                        {p.performed_date
                          ? formatDate(p.performed_date)
                          : "Date unknown"}
                      </div>
                      <div className="text-xs capitalize text-muted-foreground/60">
                        {p.status}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
