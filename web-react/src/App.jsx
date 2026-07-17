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


function inverseNormalCDF(p) {
  if (p <= 0 || p >= 1) return NaN;
  const a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];
  const b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01];
  const c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];
  const d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00];
  const pLow = 0.02425, pHigh = 1 - pLow;
  let q, r;
  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
  } else if (p <= pHigh) {
    q = p - 0.5; r = q * q;
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1);
  } else {
    q = Math.sqrt(-2 * Math.log(1 - p));
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
  }
}

function ConfidenceExplorer({ metrics }) {
  const withCI = (metrics || []).filter((m) => m.uncertainty_low != null && m.uncertainty_high != null);
  const [selected, setSelected] = useState(null);
  const [confidence, setConfidence] = useState(95);
  useEffect(() => { if (!selected && withCI.length > 0) setSelected(withCI[0].name); }, [withCI, selected]);
  if (withCI.length === 0) return null;
  const metric = withCI.find((m) => m.name === selected) ?? withCI[0];
  const z95 = 1.959963984540054;
  const halfWidth95 = (metric.uncertainty_high - metric.uncertainty_low) / 2;
  const sigma = halfWidth95 / z95;
  const zLevel = inverseNormalCDF(0.5 + confidence / 200);
  const lo = metric.estimate - zLevel * sigma;
  const hi = metric.estimate + zLevel * sigma;
  return (
    <Section icon={Beaker} title="Confidence-level explorer">
      <p className="mb-4 text-xs text-slate-500">
        Recomputes an approximate confidence interval at any level from this metric's reported 95%
        bootstrap interval, assuming a normal sampling distribution. This is a client-side
        approximation for exploring sensitivity around the real result &mdash; it does not
        re-run the bootstrap; the 95% CI shown in the metric cards above is the actual computed
        result from <code>uncertainty.py</code>.
      </p>
      {withCI.length > 1 && (
        <select
          className="mb-4 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
          value={metric.name}
          onChange={(e) => setSelected(e.target.value)}
        >
          {withCI.map((m) => <option key={m.name} value={m.name}>{m.name.replace(/_/g, ' ')}</option>)}
        </select>
      )}
      <label className="flex items-center justify-between text-sm text-slate-300">
        <span>Confidence level</span>
        <span className="font-mono">{confidence.toFixed(1)}%</span>
      </label>
      <input
        type="range" min="50" max="99.9" step="0.1" value={confidence}
        onChange={(e) => setConfidence(Number(e.target.value))}
        className="mt-2 w-full accent-cyan-500"
      />
      <p className="mt-4 text-2xl font-semibold">
        [{lo.toPrecision(4)}, {hi.toPrecision(4)}]
        <span className="ml-2 text-sm font-normal text-slate-400">{metric.units}</span>
      </p>
      <p className="mt-1 text-xs text-slate-500">
        estimate {metric.estimate.toPrecision(4)}, n = {metric.sample_size}
      </p>
    </Section>
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

        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          <ConfidenceExplorer metrics={summary.data?.metrics} />
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
