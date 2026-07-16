import { useEffect, useState } from 'react';
import {
  Database, ShieldCheck, AlertTriangle, BookOpen, FileText,
  Download, GitCommit, Beaker, ListChecks,
} from 'lucide-react';

const card = 'rounded-2xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl shadow-black/20';
const pill = 'rounded-full border border-slate-700 px-4 py-2 text-sm';

function useJson(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  useEffect(() => {
    let cancelled = false;
    fetch(path)
      .then((r) => {
        if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => { if (!cancelled) setState({ data, error: null, loading: false }); })
      .catch((error) => { if (!cancelled) setState({ data: null, error, loading: false }); });
    return () => { cancelled = true; };
  }, [path]);
  return state;
}

function MetricCard({ metric }) {
  const hasUncertainty = metric.uncertainty_low != null && metric.uncertainty_high != null;
  return (
    <article className={card}>
      <p className="text-sm text-slate-400">{metric.name.replace(/_/g, ' ')}</p>
      <p className="mt-2 text-2xl font-semibold">
        {typeof metric.estimate === 'number' ? metric.estimate.toPrecision(4) : String(metric.estimate)}
        <span className="ml-1 text-sm font-normal text-slate-400">{metric.units}</span>
      </p>
      {hasUncertainty && (
        <p className="mt-1 text-xs text-slate-400">
          95% CI [{metric.uncertainty_low.toPrecision(3)}, {metric.uncertainty_high.toPrecision(3)}]
        </p>
      )}
      <p className="mt-1 text-xs text-slate-500">n = {metric.sample_size}</p>
    </article>
  );
}

function Section({ icon: Icon, title, children }) {
  return (
    <article className={card}>
      <div className="mb-4 flex items-center gap-2">
        <Icon size={18} />
        <h2 className="font-semibold">{title}</h2>
      </div>
      {children}
    </article>
  );
}

export default function App() {
  const project = useJson('./project.json');
  const summary = useJson('./results/summary.json');
  const warnings = useJson('./results/warnings.json');
  const benchmarks = useJson('./results/benchmarks.json');

  if (project.loading) {
    return <main className="min-h-screen grid place-items-center">Loading local project metadata…</main>;
  }
  if (project.error || !project.data) {
    return (
      <main className="min-h-screen grid place-items-center text-amber-300">
        Could not load project.json: {String(project.error)}
      </main>
    );
  }
  const p = project.data;
  const isDemo = summary.data?.data_kind === 'synthetic_smoke_test' || summary.data?.data_kind === 'synthetic_demo';

  return (
    <main className="grid-bg min-h-screen">
      <div className="mx-auto max-w-7xl px-5 py-10">
        <header className="mb-8 rounded-3xl border border-slate-800 bg-slate-950/80 p-7 backdrop-blur">
          <p className="mb-3 text-sm uppercase tracking-[0.28em] text-cyan-300">{p.category}</p>
          <h1 className="max-w-5xl text-3xl font-semibold leading-tight md:text-5xl">{p.title}</h1>
          <p className="mt-5 max-w-4xl text-lg text-slate-300">{p.question}</p>
          <div className="mt-6 flex flex-wrap gap-3 text-sm">
            <span className={`${pill} border-cyan-800 bg-cyan-950/50`}>{p.status}</span>
            <span className={pill}>Priority {p.priority}/10</span>
            <span className={pill}>{p.dataMode}</span>
            {summary.data && (
              <span className={`${pill} ${isDemo ? 'border-amber-800 bg-amber-950/40 text-amber-200' : 'border-emerald-800 bg-emerald-950/40 text-emerald-200'}`}>
                {isDemo ? 'SYNTHETIC DEMO RESULTS' : 'REAL DATA RESULTS'}
              </span>
            )}
          </div>
        </header>

        {isDemo && (
          <div className="mb-6 flex items-start gap-2 rounded-xl border border-amber-900 bg-amber-950/30 p-4 text-sm text-amber-200">
            <AlertTriangle size={18} className="mt-0.5 shrink-0" />
            The metrics and figures below were generated from clearly-labelled synthetic demo data
            (scripts/run_analysis.py --demo), not real WASP-39b JWST observations. Real-data results
            appear here automatically once scripts/fetch_data.py and scripts/run_analysis.py have
            been run against the downloaded Zenodo spectrum.
          </div>
        )}

        <section className="grid gap-4 md:grid-cols-3">
          {summary.data?.metrics?.slice(0, 6).map((m) => <MetricCard key={m.name} metric={m} />)}
          {!summary.data && (
            <article className={card}>
              <p className="text-sm text-slate-400">Result status</p>
              <p className="mt-2 text-2xl font-semibold">NO RESULTS YET</p>
              <p className="mt-1 text-xs text-slate-500">Run scripts/run_analysis.py first.</p>
            </article>
          )}
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <Section icon={BookOpen} title="Figure gallery">
            <div className="grid gap-4 sm:grid-cols-2">
              {p.figures.map((f) => (
                <figure key={f.id} className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
                  <img
                    src={`./figures/${f.id}.svg`}
                    alt={f.label}
                    className="w-full rounded-lg bg-white"
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                  <figcaption className="mt-2 text-sm text-slate-300">{f.label}</figcaption>
                </figure>
              ))}
            </div>
          </Section>
          <Section icon={ShieldCheck} title="Provenance boundary">
            <p className="text-slate-300">{p.novelty}</p>
            <div className="mt-5 flex items-start gap-2 rounded-xl border border-amber-900 bg-amber-950/30 p-4 text-sm text-amber-200">
              <AlertTriangle size={18} className="mt-0.5 shrink-0" />
              No result is public-ready until validation and provenance checks pass.
            </div>
            {summary.data?.provenance && (
              <dl className="mt-4 space-y-1 text-sm text-slate-300">
                <div className="flex items-center gap-2"><GitCommit size={14} /><dt className="text-slate-500">git commit</dt><dd className="ml-auto font-mono">{summary.data.provenance.git_commit}</dd></div>
                <div className="flex items-center gap-2"><FileText size={14} /><dt className="text-slate-500">config sha256</dt><dd className="ml-auto font-mono truncate max-w-[10rem]">{summary.data.provenance.config_sha256 ?? 'n/a'}</dd></div>
                <div className="flex items-center gap-2"><Beaker size={14} /><dt className="text-slate-500">package version</dt><dd className="ml-auto font-mono">{summary.data.provenance.package_version}</dd></div>
              </dl>
            )}
          </Section>
        </section>

        <section className="mt-6 grid gap-6 md:grid-cols-2">
          <Section icon={ListChecks} title="Validation contract">
            <ul className="space-y-2 text-slate-300">
              {p.validationContract.map((v) => <li key={v}>• {v}</li>)}
            </ul>
          </Section>
          <Section icon={AlertTriangle} title="Warnings">
            {warnings.data && warnings.data.length > 0 ? (
              <ul className="space-y-2 text-sm text-amber-200">
                {warnings.data.map((w, i) => <li key={i}>• {w}</li>)}
              </ul>
            ) : (
              <p className="text-sm text-slate-400">No warnings recorded in results/warnings.json.</p>
            )}
          </Section>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          <Section icon={Beaker} title="Methodology">
            <p className="text-sm leading-relaxed text-slate-300">{p.methodology}</p>
          </Section>
          <Section icon={AlertTriangle} title="Assumptions and limitations">
            <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Assumptions</p>
            <ul className="mb-4 space-y-1 text-sm text-slate-300">
              {p.assumptions.map((a) => <li key={a}>• {a}</li>)}
            </ul>
            <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Limitations</p>
            <ul className="space-y-1 text-sm text-slate-300">
              {p.limitations.map((l) => <li key={l}>• {l}</li>)}
            </ul>
          </Section>
        </section>

        <section className="mt-6 grid gap-6 md:grid-cols-2">
          <Section icon={Download} title="Downloads and provenance manifest">
            <div className="flex flex-wrap gap-3 text-sm">
              <a className="rounded-lg border border-slate-700 px-3 py-2 hover:border-cyan-600" href="./manifest.csv" download>data/manifest.csv</a>
              <a className="rounded-lg border border-slate-700 px-3 py-2 hover:border-cyan-600" href="./results/summary.json" download>results/summary.json</a>
              {benchmarks.data && (
                <a className="rounded-lg border border-slate-700 px-3 py-2 hover:border-cyan-600" href="./results/benchmarks.json" download>results/benchmarks.json</a>
              )}
            </div>
            <p className="mt-4 text-xs text-slate-500">
              data/manifest.csv records product_id, source, source_url, retrieved_utc, sha256, file_size_bytes,
              selection_reason and licence_or_terms for every real archive product used.
            </p>
          </Section>
          <Section icon={Database} title="Citation and licence">
            <p className="text-sm text-slate-300">Author: {p.citation.author}</p>
            <p className="text-sm text-slate-300">Licence: {p.citation.license}</p>
            <a className="mt-2 inline-block text-sm text-cyan-300 hover:underline" href={p.citation.repository}>{p.citation.repository}</a>
          </Section>
        </section>
      </div>
    </main>
  );
}
