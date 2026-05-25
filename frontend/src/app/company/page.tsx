"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { authFetch } from "@/lib/api";
import {
  BuildingOfficeIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/solid";
import { toast } from "sonner";

/* ── types ────────────────────────────────────────────────── */
interface CompanyProfile {
  company_id: string;
  legal_name: string;
  city: string;
  region: string;
  industry_code: string;
  size_band: string;
  node_role: string;
  is_active: boolean;
}

interface Document {
  document_id: string;
  doc_type: string;
  issue_date: string;
  status: string;
  gross_amount: number;
  discrepancy_flag: boolean;
}

const STATUS_OPTIONS = ["PENDING", "APPROVED", "REJECTED", "PAID", "CANCELLED"];

/* ── helpers ──────────────────────────────────────────────── */
function SectionHeader({
  icon: Icon,
  title,
  subtitle,
}: {
  icon: React.ElementType;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="flex items-start gap-3 mb-6">
      <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex-shrink-0">
        <Icon className="w-5 h-5 text-cyan-400" />
      </div>
      <div>
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        <p className="text-sm text-slate-400">{subtitle}</p>
      </div>
    </div>
  );
}

/* ── main component ───────────────────────────────────────── */
export default function CompanyPage() {
  const { user } = useAuth();

  /* profile state */
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editCity, setEditCity] = useState("");
  const [editRegion, setEditRegion] = useState("");
  const [editLegalName, setEditLegalName] = useState("");

  /* documents state */
  const [docs, setDocs] = useState<Document[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [updatingDoc, setUpdatingDoc] = useState<string | null>(null);

  /* load profile */
  useEffect(() => {
    authFetch("/api/company/me")
      .then((r) => r.json())
      .then((data: CompanyProfile) => {
        setProfile(data);
        setEditCity(data.city ?? "");
        setEditRegion(data.region ?? "");
        setEditLegalName(data.legal_name ?? "");
      })
      .catch(() => toast.error("Error al cargar el perfil"))
      .finally(() => setProfileLoading(false));
  }, []);

  /* load documents */
  useEffect(() => {
    authFetch("/api/company/documents")
      .then((r) => r.json())
      .then(setDocs)
      .catch(() => toast.error("Error al cargar los documentos"))
      .finally(() => setDocsLoading(false));
  }, []);

  /* save profile */
  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await authFetch("/api/company/me", {
        method: "PATCH",
        body: JSON.stringify({
          legal_name: editLegalName || null,
          city: editCity || null,
          region: editRegion || null,
        }),
      });
      if (!res.ok) throw new Error();
      const updated: CompanyProfile = await res.json();
      setProfile(updated);
      toast.success("Perfil actualizado");
    } catch {
      toast.error("Error al guardar el perfil");
    } finally {
      setSaving(false);
    }
  }

  /* update document status */
  async function handleStatusChange(docId: string, status: string) {
    setUpdatingDoc(docId);
    try {
      const res = await authFetch(`/api/documents/${docId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error();
      setDocs((prev) =>
        prev.map((d) => (d.document_id === docId ? { ...d, status } : d))
      );
      toast.success("Estado actualizado");
    } catch {
      toast.error("Error al actualizar el estado");
    } finally {
      setUpdatingDoc(null);
    }
  }

  /* ── render ─────────────────────────────────────────────── */
  return (
    <div className="max-w-5xl mx-auto px-4 md:px-6 py-10 space-y-10">

      {/* greeting */}
      <div>
        <h1 className="text-2xl font-bold text-white">Mi Empresa</h1>
        <p className="text-slate-400 text-sm mt-1">
          {user?.email} · {user?.company_id}
        </p>
      </div>

      {/* ── Profile ─────────────────────────────────────────── */}
      <section className="bg-[#161B22] border border-slate-800 rounded-2xl p-6">
        <SectionHeader
          icon={BuildingOfficeIcon}
          title="Mi Perfil"
          subtitle="Información de tu empresa en la red"
        />

        {profileLoading ? (
          <div className="text-slate-500 text-sm">Cargando…</div>
        ) : !profile ? (
          <div className="text-red-400 text-sm">No se pudo cargar el perfil.</div>
        ) : (
          <form onSubmit={handleSaveProfile} className="space-y-5">
            {/* read-only info */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { label: "Company ID", value: profile.company_id },
                { label: "Sector (NACE)", value: profile.industry_code },
                { label: "Tamaño", value: profile.size_band },
                { label: "Rol en red", value: profile.node_role },
                { label: "Estado", value: profile.is_active ? "Activo" : "Inactivo" },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-xs text-slate-500 mb-0.5">{label}</p>
                  <p className="text-sm text-slate-200 font-medium">{value}</p>
                </div>
              ))}
            </div>

            <div className="border-t border-slate-800 pt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { label: "Nombre legal", value: editLegalName, setter: setEditLegalName },
                { label: "Ciudad", value: editCity, setter: setEditCity },
                { label: "Región / Provincia", value: editRegion, setter: setEditRegion },
              ].map(({ label, value, setter }) => (
                <div key={label}>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">{label}</label>
                  <input
                    type="text"
                    value={value}
                    onChange={(e) => setter(e.target.value)}
                    className="w-full bg-[#0E1117] border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-sm placeholder-slate-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-colors"
                  />
                </div>
              ))}
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-2 bg-cyan-500 hover:bg-cyan-400 disabled:bg-cyan-500/40 disabled:cursor-not-allowed text-[#0E1117] font-semibold rounded-lg px-5 py-2 text-sm transition-colors"
              >
                <CheckCircleIcon className="w-4 h-4" />
                {saving ? "Guardando…" : "Guardar cambios"}
              </button>
            </div>
          </form>
        )}
      </section>

      {/* ── Documents ───────────────────────────────────────── */}
      <section className="bg-[#161B22] border border-slate-800 rounded-2xl p-6">
        <SectionHeader
          icon={DocumentTextIcon}
          title="Mis Documentos"
          subtitle="Documentos EDI emitidos por tu empresa"
        />

        {docsLoading ? (
          <div className="text-slate-500 text-sm">Cargando…</div>
        ) : docs.length === 0 ? (
          <div className="text-slate-500 text-sm">No hay documentos registrados.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left">
                  {["Tipo", "Fecha", "Importe (€)", "Estado", "Discrepancia"].map((h) => (
                    <th key={h} className="pb-3 pr-4 text-xs font-medium text-slate-500 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {docs.map((doc) => (
                  <tr key={doc.document_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 pr-4 font-mono text-slate-300 text-xs">{doc.doc_type}</td>
                    <td className="py-3 pr-4 text-slate-400">
                      {doc.issue_date ? new Date(doc.issue_date).toLocaleDateString("es-ES") : "—"}
                    </td>
                    <td className="py-3 pr-4 text-slate-200 font-medium">
                      {doc.gross_amount != null
                        ? doc.gross_amount.toLocaleString("es-ES", { minimumFractionDigits: 2 })
                        : "—"}
                    </td>
                    <td className="py-3 pr-4">
                      <select
                        value={doc.status ?? "PENDING"}
                        disabled={updatingDoc === doc.document_id}
                        onChange={(e) => handleStatusChange(doc.document_id, e.target.value)}
                        className="bg-[#0E1117] border border-slate-700 rounded-md px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 disabled:opacity-50 cursor-pointer"
                      >
                        {STATUS_OPTIONS.map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </td>
                    <td className="py-3">
                      {doc.discrepancy_flag ? (
                        <span className="inline-flex items-center gap-1 text-amber-400 text-xs">
                          <ExclamationTriangleIcon className="w-3.5 h-3.5" /> Sí
                        </span>
                      ) : (
                        <span className="text-slate-600 text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}