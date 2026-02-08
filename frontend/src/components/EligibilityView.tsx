"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { getEligibility } from "@/lib/api";
import type { EligibilityResult, EligibilityCriterion } from "@/types";

interface Props {
  patientId: string;
}

const STATUS_CONFIG = {
  eligible: { label: "Eligible", variant: "default" as const, className: "bg-green-600" },
  not_eligible: { label: "Not Eligible", variant: "destructive" as const, className: "" },
  unknown: { label: "Unknown", variant: "outline" as const, className: "border-amber-500 text-amber-700" },
};

function CriterionRow({ criterion }: { criterion: EligibilityCriterion }) {
  return (
    <div className="py-2">
      <div className="flex items-center gap-2">
        <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${criterion.met ? "bg-green-500" : "bg-red-400"}`} />
        <span className="text-sm font-medium">{criterion.criterion}</span>
        <span className="text-xs text-muted-foreground">
          {criterion.met ? "Met" : "Not met"}
        </span>
      </div>
      {criterion.reason && (
        <p className="ml-4 mt-0.5 text-xs text-muted-foreground">{criterion.reason}</p>
      )}
      {criterion.evidence.length > 0 && (
        <div className="ml-4 mt-1 space-y-0.5">
          {criterion.evidence.map((e) => (
            <div key={e.resource_id} className="text-xs text-muted-foreground/70">
              <span>{e.display ?? "Unknown"}</span>
              <span className="font-mono text-[10px] text-muted-foreground/50">
                {" "}· Source FHIR: {e.resource_id}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function EligibilityView({ patientId }: Props) {
  const [result, setResult] = useState<EligibilityResult | null>(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getEligibility(patientId);
      setResult(data);
    } catch {
      // keep current state
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  if (loading && !result) {
    return (
      <div className="py-8 text-center text-sm text-muted-foreground">
        Evaluating eligibility...
      </div>
    );
  }

  if (!result) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm italic text-muted-foreground">
          Unable to determine eligibility.
        </CardContent>
      </Card>
    );
  }

  const config = STATUS_CONFIG[result.status];

  return (
    <div className="space-y-4">
      {/* Status card */}
      <Card>
        <CardHeader className="pb-1">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Bariatric Surgery Eligibility</CardTitle>
            <Badge variant={config.variant} className={config.className}>
              {config.label}
            </Badge>
          </div>
          <CardDescription className="text-xs">
            Deterministic evaluation based on BMI, comorbidities, and required documentation
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Reasons */}
          <div className="mb-3">
            {result.reasons.map((r) => (
              <p key={r} className="text-sm">{r}</p>
            ))}
          </div>

          {result.bmi_value !== null && (
            <p className="mb-3 text-sm text-muted-foreground">
              BMI: <span className="font-semibold tabular-nums text-foreground">{result.bmi_value.toFixed(1)}</span>
            </p>
          )}

          {/* Criteria checklist */}
          <Separator />
          <div className="mt-1">
            {result.criteria.map((c, i) => (
              <div key={c.criterion}>
                {i > 0 && <Separator />}
                <CriterionRow criterion={c} />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
