import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Download, Hash, FileWarning, Clock, ChevronLeft } from "lucide-react";
import { threatApi } from "@/api/threatApi";
import { Threat } from "@/types/threat.types";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Skeleton from "@/components/ui/Skeleton";
import { formatDateTime } from "@/utils/formatters";
import { useToast } from "@/hooks/useToast";

export default function ThreatDetailsPage() {
  const { id } = useParams();
  const [threat, setThreat] = useState<Threat | null | undefined>(undefined);
  const { toast } = useToast();

  useEffect(() => {
    if (!id) return;
    threatApi.getThreatById(id).then(setThreat);
  }, [id]);

  if (threat === undefined) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!threat) {
    return (
      <div className="text-center py-20">
        <FileWarning className="h-10 w-10 text-slate-700 mx-auto mb-4" />
        <p className="text-muted">Threat record not found.</p>
        <Link to="/" className="text-accent-cyan text-sm mt-2 inline-block">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-slate-200">
        <ChevronLeft className="h-4 w-4" /> Back
      </Link>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="font-display text-xl font-semibold text-slate-100">{threat.threatName}</h1>
            <Badge severity={threat.severity} />
          </div>
          <p className="text-sm text-muted mt-1">
            {threat.threatFamily} family · Detected {formatDateTime(threat.detectionTime)}
          </p>
        </div>
        <Button variant="secondary" onClick={() => toast({ title: "Report downloading", variant: "info" })}>
          <Download className="h-4 w-4" /> Download Report
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Threat Score</CardTitle>
            </CardHeader>
            <div className="flex items-center gap-6">
              <div className="relative h-24 w-24 shrink-0">
                <svg className="h-24 w-24 -rotate-90">
                  <circle cx="48" cy="48" r="40" stroke="rgba(148,163,184,0.1)" strokeWidth="8" fill="none" />
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke="#f43f5e"
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={`${(threat.threatScore / 100) * 251} 251`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center font-display text-lg font-semibold">
                  {threat.threatScore}
                </span>
              </div>
              <p className="text-sm text-slate-400 flex-1">{threat.description}</p>
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Detection Timeline</CardTitle>
              <Clock className="h-4 w-4 text-muted" />
            </CardHeader>
            <ol className="space-y-4 border-l border-white/10 pl-4">
              {threat.timeline.map((event, i) => (
                <li key={i} className="relative">
                  <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-accent-cyan ring-4 ring-background" />
                  <p className="text-xs text-muted font-mono">{event.time}</p>
                  <p className="text-sm text-slate-200 mt-0.5">{event.event}</p>
                </li>
              ))}
            </ol>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recommended Action</CardTitle>
            </CardHeader>
            <p className="text-sm text-slate-300">{threat.recommendedAction}</p>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>File Metadata</CardTitle>
              <Hash className="h-4 w-4 text-muted" />
            </CardHeader>
            <div className="space-y-3 text-xs">
              {[
                ["Threat Family", threat.threatFamily],
                ["File Size", threat.fileSize],
                ["Detection Engine", threat.detectionEngine],
                ["YARA Rule", threat.yaraRule],
                ["Status", threat.status],
              ].map(([label, val]) => (
                <div key={label} className="flex justify-between border-b border-white/5 pb-2.5">
                  <span className="text-muted">{label}</span>
                  <span className="text-slate-200 capitalize text-right">{val}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Hash Values</CardTitle>
            </CardHeader>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-muted mb-1">SHA-256</p>
                <p className="font-mono text-xs text-slate-300 break-all bg-background-surface rounded-lg p-2 border border-border">
                  {threat.sha256}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted mb-1">MD5</p>
                <p className="font-mono text-xs text-slate-300 break-all bg-background-surface rounded-lg p-2 border border-border">
                  {threat.md5}
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
