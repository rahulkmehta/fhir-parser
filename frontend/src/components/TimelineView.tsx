"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { getTimeline } from "@/lib/api";
import type { TimelineEntry, TimelineResponse } from "@/types";

interface Props {
  patientId: string;
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

function TimelineRow({ entry }: { entry: TimelineEntry }) {
  return (
    <div className="flex items-start justify-between py-2.5">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="shrink-0 text-[10px] font-normal"
          >
            {entry.resource_type}
          </Badge>
          <span className="truncate text-sm">{entry.display_name}</span>
        </div>
        <div className="mt-0.5 font-mono text-[10px] text-muted-foreground/50">
          Source FHIR: {entry.resource_id}
        </div>
      </div>
      <div className="shrink-0 pl-4 text-right">
        <div className="text-xs text-muted-foreground">
          {formatDate(entry.date)}
        </div>
        {entry.detail ? (
          <div className="mt-0.5 text-xs text-muted-foreground/80">
            {entry.detail}
          </div>
        ) : (
          <div className="mt-0.5 text-xs italic text-muted-foreground/40">
            No value
          </div>
        )}
      </div>
    </div>
  );
}

export function TimelineView({ patientId }: Props) {
  const [data, setData] = useState<TimelineResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const pageSize = 50;

  const fetchPage = useCallback(
    async (p: number) => {
      setLoading(true);
      try {
        const res = await getTimeline(patientId, p, pageSize);
        setData(res);
      } catch {
        // keep current state
      } finally {
        setLoading(false);
      }
    },
    [patientId]
  );

  useEffect(() => {
    setPage(1);
    fetchPage(1);
  }, [fetchPage]);

  const goToPage = (p: number) => {
    setPage(p);
    fetchPage(p);
  };

  if (loading && !data) {
    return (
      <div className="py-8 text-center text-sm text-muted-foreground">
        Loading timeline...
      </div>
    );
  }

  if (!data || data.entries.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm italic text-muted-foreground">
          No timeline entries recorded for this patient.
        </CardContent>
      </Card>
    );
  }

  const totalPages = Math.ceil(data.total / pageSize);

  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-sm">
          Clinical Timeline ({data.total} entries)
        </CardTitle>
      </CardHeader>
      <CardContent className={loading ? "opacity-50" : ""}>
        <div>
          {data.entries.map((entry, i) => (
            <div key={`${entry.resource_id}-${i}`}>
              {i > 0 && <Separator />}
              <TimelineRow entry={entry} />
            </div>
          ))}
        </div>

        {totalPages > 1 && (
          <div className="mt-4 flex items-center justify-between border-t pt-3 text-xs text-muted-foreground">
            <button
              onClick={() => goToPage(page - 1)}
              disabled={page <= 1 || loading}
              className="hover:text-foreground disabled:opacity-40"
            >
              {loading && page > 1 ? "Loading..." : "Previous"}
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => goToPage(page + 1)}
              disabled={page >= totalPages || loading}
              className="hover:text-foreground disabled:opacity-40"
            >
              {loading ? "Loading..." : "Next"}
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
