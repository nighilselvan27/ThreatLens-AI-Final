import { useEffect, useMemo, useState } from "react";
import { Search, Download, FileDown, Eye, Trash2, FileBarChart2 } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import { fetchReports, deleteReport } from "@/redux/slices/reportsSlice";
import { Card } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { Table, THead, TBody, Tr, Th, Td } from "@/components/ui/Table";
import { usePagination } from "@/hooks/usePagination";
import { useDebounce } from "@/hooks/useDebounce";
import { useToast } from "@/hooks/useToast";
import { formatDate } from "@/utils/formatters";
import { Report } from "@/types/report.types";

const RISK_FILTERS: (Report["riskLevel"] | "all")[] = ["all", "critical", "high", "medium", "low", "safe"];

export default function ReportsPage() {
  const dispatch = useAppDispatch();
  const { items, status } = useAppSelector((s) => s.reports);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState<(typeof RISK_FILTERS)[number]>("all");
  const [selected, setSelected] = useState<Report | null>(null);
  const debouncedSearch = useDebounce(search, 250);
  const { toast } = useToast();

  useEffect(() => {
    dispatch(fetchReports());
  }, [dispatch]);

  const filtered = useMemo(() => {
    return items.filter((r) => {
      const matchesSearch = r.fileName.toLowerCase().includes(debouncedSearch.toLowerCase());
      const matchesRisk = riskFilter === "all" || r.riskLevel === riskFilter;
      return matchesSearch && matchesRisk;
    });
  }, [items, debouncedSearch, riskFilter]);

  const { page, totalPages, paginated, goToPage } = usePagination(filtered, 8);

  function handleDelete(id: string) {
    dispatch(deleteReport(id));
    toast({ title: "Report deleted", variant: "success" });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="font-display text-xl font-semibold text-slate-100">Scan Reports</h1>
          <p className="text-sm text-muted mt-1">{filtered.length} reports found</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => toast({ title: "CSV exported", variant: "success" })}>
            <FileDown className="h-4 w-4" /> Export CSV
          </Button>
          <Button variant="secondary" size="sm" onClick={() => toast({ title: "PDF downloading", variant: "info" })}>
            <Download className="h-4 w-4" /> Download PDF
          </Button>
        </div>
      </div>

      <Card>
        <div className="flex flex-col sm:flex-row gap-3 mb-5">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search by file name..."
              className="pl-10"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex gap-1.5 flex-wrap">
            {RISK_FILTERS.map((r) => (
              <button
                key={r}
                onClick={() => setRiskFilter(r)}
                className={`px-3 py-2 rounded-lg text-xs font-medium capitalize border transition-colors ${
                  riskFilter === r
                    ? "bg-accent-cyan/10 border-accent-cyan/40 text-accent-cyan"
                    : "border-border text-slate-400 hover:text-slate-200"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <Table>
          <THead>
            <Th>Report ID</Th>
            <Th>File Name</Th>
            <Th>Scan Date</Th>
            <Th>Risk</Th>
            <Th>Family</Th>
            <Th>Status</Th>
            <Th className="text-right">Actions</Th>
          </THead>
          <TBody>
            {status === "loading" && (
              <Tr>
                <Td colSpan={7} className="text-center text-muted py-8">
                  Loading reports...
                </Td>
              </Tr>
            )}
            {paginated.map((r) => (
              <Tr key={r.id}>
                <Td className="font-mono text-xs">{r.id}</Td>
                <Td className="font-mono text-xs max-w-[220px] truncate">{r.fileName}</Td>
                <Td className="text-xs">{formatDate(r.scanDate)}</Td>
                <Td>
                  <Badge severity={r.riskLevel === "safe" ? "safe" : r.riskLevel} />
                </Td>
                <Td className="text-xs">{r.threatFamily ?? "—"}</Td>
                <Td className="text-xs capitalize">{r.status}</Td>
                <Td>
                  <div className="flex justify-end gap-1">
                    <button onClick={() => setSelected(r)} className="h-8 w-8 flex items-center justify-center rounded-lg text-slate-400 hover:text-accent-cyan hover:bg-white/5">
                      <Eye className="h-4 w-4" />
                    </button>
                    <button onClick={() => handleDelete(r.id)} className="h-8 w-8 flex items-center justify-center rounded-lg text-slate-400 hover:text-severity-critical hover:bg-white/5">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </Td>
              </Tr>
            ))}
          </TBody>
        </Table>

        <div className="flex items-center justify-between mt-4">
          <span className="text-xs text-muted">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-1.5">
            <Button variant="outline" size="sm" onClick={() => goToPage(page - 1)} disabled={page === 1}>
              Previous
            </Button>
            <Button variant="outline" size="sm" onClick={() => goToPage(page + 1)} disabled={page === totalPages}>
              Next
            </Button>
          </div>
        </div>
      </Card>

      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title="Report Details">
        {selected && (
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-2 mb-2">
              <FileBarChart2 className="h-5 w-5 text-accent-cyan" />
              <span className="font-mono text-xs">{selected.id}</span>
            </div>
            {[
              ["File Name", selected.fileName],
              ["Scan Date", formatDate(selected.scanDate)],
              ["File Size", selected.fileSize],
              ["Malware Family", selected.threatFamily ?? "None detected"],
              ["Status", selected.status],
              ["Analyst", selected.analyst],
            ].map(([label, val]) => (
              <div key={label} className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-muted">{label}</span>
                <span className="text-slate-200">{val}</span>
              </div>
            ))}
            <div className="flex justify-between items-center pt-1">
              <span className="text-muted">Risk Level</span>
              <Badge severity={selected.riskLevel === "safe" ? "safe" : selected.riskLevel} />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
