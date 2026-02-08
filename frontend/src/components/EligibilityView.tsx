"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { getEligibility, requestAIReview } from "@/lib/api";
import type { EligibilityResult, EligibilityCriterion, AIReviewResponse } from "@/types";

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

/** Transform the backend AI review response into the Part D spec JSON shape. */
function toSpecJson(review: AIReviewResponse): object {
  const stripFhirRefs = (text: string) =>
    text.replace(/\s*\(FHIR ID:\s*[0-9a-f-]+\)/gi, "");

  return {
    clinicalSummary: stripFhirRefs(review.clinical_summary),
    eligibilityAssessment: review.deterministic_status,
    checklist: review.checklist.map((item) => ({
      requirement: item.criterion,
      status: item.status,
      evidence: item.evidence.map((e) => `${e.resource_type}/${e.resource_id}`),
    })),
    recommendedNextSteps: review.recommended_next_steps,
  };
}

function AIReviewModal({
  review,
  onClose,
}: {
  review: AIReviewResponse;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const specJson = review.error ? null : JSON.stringify(toSpecJson(review), null, 2);

  const handleCopy = async () => {
    if (!specJson) return;
    await navigator.clipboard.writeText(specJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="relative mx-4 max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-lg border bg-background p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold">AI-Assisted Review</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-lg leading-none">&times;</button>
        </div>

        {review.error ? (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            {review.error}
          </div>
        ) : (
          <div className="relative">
            <button
              onClick={handleCopy}
              className="absolute right-2 top-2 rounded-md border bg-background px-2 py-1 text-xs font-medium transition-colors hover:bg-accent"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
            <pre className="bg-muted rounded-md p-4 text-sm overflow-x-auto">
              {specJson}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export function EligibilityView({ patientId }: Props) {
  const [result, setResult] = useState<EligibilityResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiReview, setAiReview] = useState<AIReviewResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const fetchEligibility = useCallback(async () => {
    setLoading(true);
    setAiReview(null);
    try {
      const data = await getEligibility(patientId);
      setResult(data);
    } catch {
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    fetchEligibility();
  }, [fetchEligibility]);

  const handleAIReview = async () => {
    setAiLoading(true);
    try {
      const review = await requestAIReview(patientId);
      setAiReview(review);
      setShowModal(true);
    } catch {
      setAiReview({
        patient_id: patientId,
        deterministic_status: result?.status ?? "unknown",
        clinical_summary: "",
        eligibility_assessment: "",
        checklist: [],
        recommended_next_steps: [],
        error: "Failed to connect to AI service. Check that the backend is running and the OpenAI API key is configured.",
      });
      setShowModal(true);
    } finally {
      setAiLoading(false);
    }
  };

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
      <Card>
        <CardHeader className="pb-1">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Bariatric Surgery Eligibility</CardTitle>
            <div className="flex items-center gap-2">
              <button
                onClick={handleAIReview}
                disabled={aiLoading}
                className="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium transition-colors hover:bg-accent disabled:opacity-50"
              >
                {aiLoading ? (
                  <svg className="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2a4 4 0 0 1 4 4c0 1.5-.8 2.8-2 3.5v1h-4v-1C8.8 8.8 8 7.5 8 6a4 4 0 0 1 4-4z" />
                    <path d="M10 14h4" />
                    <path d="M10 17h4" />
                    <path d="M11 20h2" />
                  </svg>
                )}
                {aiLoading ? "Reviewing..." : "AI Review"}
              </button>
              <Badge variant={config.variant} className={config.className}>
                {config.label}
              </Badge>
            </div>
          </div>
          <CardDescription className="text-xs">
            Deterministic evaluation based on BMI, comorbidities, and required documentation
          </CardDescription>
        </CardHeader>
        <CardContent>
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

      {showModal && aiReview && (
        <AIReviewModal review={aiReview} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
