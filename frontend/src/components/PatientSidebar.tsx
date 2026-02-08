"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { getPatients } from "@/lib/api";
import type { PatientSummary } from "@/types";

interface Props {
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCohortReport: () => void;
  showingCohort: boolean;
}

export function PatientSidebar({ selectedId, onSelect, onCohortReport, showingCohort }: Props) {
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const pageSize = 30;

  const fetchPatients = useCallback(async (q: string, p: number) => {
    setLoading(true);
    try {
      const data = await getPatients(q, p, pageSize);
      setPatients(data.patients);
      setTotal(data.total);
    } catch {
      // keep current state on error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPatients("", 1);
  }, [fetchPatients]);

  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(1);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchPatients(value, 1);
    }, 300);
  };

  const totalPages = Math.ceil(total / pageSize);

  const goToPage = (p: number) => {
    setPage(p);
    fetchPatients(search, p);
  };

  return (
    <aside className="flex h-screen w-80 flex-col border-r bg-background">
      <div className="shrink-0 border-b p-3">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-sm font-semibold tracking-tight">
            Prior Auth Review
          </h1>
          <button
            onClick={onCohortReport}
            className={`rounded-md px-2 py-1 text-xs transition-colors hover:bg-accent ${
              showingCohort ? "bg-accent font-medium" : "text-muted-foreground"
            }`}
          >
            Cohort Report
          </button>
        </div>
        <Input
          placeholder="Search by name or ID..."
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          className="h-8 text-sm"
        />
        <p className="mt-1.5 text-xs text-muted-foreground">
          {total} patient{total !== 1 ? "s" : ""}
        </p>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {loading && patients.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            Loading...
          </div>
        ) : patients.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No patients found.
          </div>
        ) : (
          <div className="divide-y">
            {patients.map((p) => (
              <button
                key={p.id}
                onClick={() => onSelect(p.id)}
                className={`w-full px-3 py-2.5 text-left transition-colors hover:bg-accent ${
                  selectedId === p.id ? "bg-accent" : ""
                }`}
              >
                <div className="text-sm font-medium leading-tight">
                  {p.full_name}
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">
                  {p.age !== null ? `${p.age}y` : "Age unknown"}
                  {" · "}
                  {p.gender ? p.gender.charAt(0).toUpperCase() + p.gender.slice(1) : "Unknown sex"}
                  {p.city && p.state ? ` · ${p.city}, ${p.state}` : ""}
                  {p.is_deceased && (
                    <span className="ml-1 text-destructive">(Deceased)</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
      {totalPages > 1 && (
        <div className="shrink-0 flex items-center justify-between border-t px-3 py-2 text-xs text-muted-foreground">
          <button
            onClick={() => goToPage(page - 1)}
            disabled={page <= 1 || loading}
            className="hover:text-foreground disabled:opacity-40"
          >
            Prev
          </button>
          <span>
            {loading ? "Loading..." : `Page ${page} of ${totalPages}`}
          </span>
          <button
            onClick={() => goToPage(page + 1)}
            disabled={page >= totalPages || loading}
            className="hover:text-foreground disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </aside>
  );
}
