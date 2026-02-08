"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { getCohortReport } from "@/lib/api";
import type { CohortReport } from "@/types";

export function CohortReportView() {
  const [report, setReport] = useState<CohortReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCohortReport()
      .then(setReport)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Generating cohort report (this may take a moment)...
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-destructive">
        Failed to load cohort report.
      </div>
    );
  }

  const categories = [
    { label: "Eligible", data: report.eligible, color: "bg-green-500" },
    { label: "Not Eligible", data: report.not_eligible, color: "bg-red-400" },
    { label: "Unknown", data: report.unknown, color: "bg-amber-400" },
  ];

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold">Cohort Eligibility Report</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Bariatric surgery eligibility across {report.total_patients} patients
        </p>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader className="pb-1">
            <CardTitle className="text-sm">Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-3 flex h-4 overflow-hidden rounded-full">
              {categories.map((cat) => (
                cat.data.percentage > 0 && (
                  <div
                    key={cat.label}
                    className={`${cat.color} transition-all`}
                    style={{ width: `${cat.data.percentage}%` }}
                  />
                )
              ))}
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              {categories.map((cat) => (
                <div key={cat.label}>
                  <div className="flex items-center justify-center gap-1.5">
                    <span className={`inline-block h-2.5 w-2.5 rounded-full ${cat.color}`} />
                    <span className="text-sm font-medium">{cat.label}</span>
                  </div>
                  <div className="mt-1 text-2xl font-semibold tabular-nums">{cat.data.count}</div>
                  <div className="text-xs text-muted-foreground">{cat.data.percentage}%</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {report.top_unknown_reasons.length > 0 && (
          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-sm">Top Reasons for Unknown Status</CardTitle>
              <CardDescription className="text-xs">
                Why patients could not be definitively classified
              </CardDescription>
            </CardHeader>
            <CardContent>
              {report.top_unknown_reasons.map((r, i) => (
                <div key={r.reason}>
                  {i > 0 && <Separator />}
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm">{r.reason}</span>
                    <div className="shrink-0 text-right">
                      <span className="text-sm font-medium tabular-nums">{r.count}</span>
                      <span className="ml-1 text-xs text-muted-foreground">({r.percentage}%)</span>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
