import { Component, lazy, Suspense, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowDownToLine,
  Beaker,
  BookOpen,
  CheckCircle2,
  Database,
  ExternalLink,
  FileText,
  GitCommit,
  Orbit,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Waves,
} from 'lucide-react';

const AtmosphereHero = lazy(() => import('./AtmosphereHero.jsx'));

const warningRules = [
  {
    key: 'segment-stability',
    label: 'Wavelength-segment sensitivity',
    description: 'The preferred model is not uniform across every wavelength segment.',
    pattern: /segment|full spectrum|preference|favour|stability/i,
    tone: 'caveat',
  },
  {
    key: 'sample-size',
    label: 'Limited sample size',
    description: 'A reported sample is below the declared validation threshold.',
    pattern: /minimum(?:_sample_size| sample size)|underpowered|too few|sample size/i,
    tone: 'caveat',
  },
  {
    key: 'model-fit',
    label: 'Model-fit caveat',
    description: 'A documented fitting condition affects interpretation of this comparison.',
    pattern: /fit|converge|covariance|condition number/i,
    tone: 'caveat',
  },
  {
    key: 'failure',
    label: 'Validation failure',
    description: 'A zero-tolerance validation condition failed and requires attention.',
    pattern: /fatal|zero[- ]tolerance|validation fail|\berror\b/i,
    tone: 'failure',
  },
];

function parseResultJson(text) {
  return JSON.parse(text.replace(/:\s*NaN(?=\s*[,}])/g, ': null'));
}

function useJson(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    const controller = new AbortController();
    fetch(path, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
        return response.text();
      })
      .then((text) => setState({ data: parseResultJson(text), error: null, loading: false }))
      .catch((error) => {
        if (error.name !== 'AbortError') setState({ data: null, error, loading: false });
      });
    return () => controller.abort();
  }, [path]);

  return state;
}

function formatMetric(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toPrecision(4) : 'Unavailable';
}

function SectionHeading({ index, eyebrow, title, copy }) {
  return (
    <div className="section-heading">
      <div className="section-index">{index}</div>
      <div><span>{eyebrow}</span><h2>{title}</h2></div>
      {copy && <p>{copy}</p>}
    </div>
  );
}

function MetricCard({ metric, index }) {
  const available = typeof metric.estimate === 'number' && Number.isFinite(metric.estimate);
  const hasInterval = metric.uncertainty_low != null && metric.uncertainty_high != null;

  return (
    <article className={`metric-card ${available ? '' : 'metric-unavailable'}`}>
      <header><span>READING {String(index + 1).padStart(2, '0')}</span><i /></header>
      <p>{metric.name.replace(/_/g, ' ')}</p>
      <div className="metric-value"><strong>{formatMetric(metric.estimate)}</strong>{available && <span>{metric.units}</span>}</div>
      <footer>
        <span>{hasInterval ? `95% CI ${metric.uncertainty_low.toPrecision(3)} – ${metric.uncertainty_high.toPrecision(3)}` : '95% CI unavailable'}</span>
        <span>n / {metric.sample_size}</span>
      </footer>
    </article>
  );
}

function inverseNormalCDF(p) {
  if (p <= 0 || p >= 1) return Number.NaN;
  const a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269, -30.66479806614716, 2.506628277459239];
  const b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572];
  const c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416];
  const pLow = 0.02425;
  const pHigh = 1 - pLow;
  let q;
  let r;
  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
  }
  if (p <= pHigh) {
    q = p - 0.5;
    r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  q = Math.sqrt(-2 * Math.log(1 - p));
  return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
}

function ConfidenceExplorer({ metrics }) {
  const withIntervals = useMemo(
    () => (metrics ?? []).filter((metric) => metric.uncertainty_low != null && metric.uncertainty_high != null),
    [metrics],
  );
  const [selected, setSelected] = useState('');
  const [confidence, setConfidence] = useState(95);

  useEffect(() => {
    if (!selected && withIntervals.length > 0) setSelected(withIntervals[0].name);
  }, [selected, withIntervals]);

  if (withIntervals.length === 0) {
    return <div className="explorer-empty">Confidence explorer unavailable: no interval-bearing metric was published.</div>;
  }

  const metric = withIntervals.find((item) => item.name === selected) ?? withIntervals[0];
  const sigma = ((metric.uncertainty_high - metric.uncertainty_low) / 2) / 1.959963984540054;
  const zLevel = inverseNormalCDF(0.5 + confidence / 200);
  const lower = metric.estimate - zLevel * sigma;
  const upper = metric.estimate + zLevel * sigma;

  return (
    <div className="confidence-explorer">
      <div className="explorer-copy">
        <SlidersHorizontal size={19} />
        <span>Interactive approximation</span>
        <h3>Move the confidence boundary.</h3>
        <p>Rescales the published 95% bootstrap interval under a normal approximation. It does not rerun the bootstrap or replace the real result.</p>
      </div>
      <div className="explorer-controls">
        {withIntervals.length > 1 && (
          <select value={metric.name} onChange={(event) => setSelected(event.target.value)}>
            {withIntervals.map((item) => <option value={item.name} key={item.name}>{item.name.replace(/_/g, ' ')}</option>)}
          </select>
        )}
        <label><span>Confidence level</span><strong>{confidence.toFixed(1)}%</strong></label>
        <input type="range" min="50" max="99.9" step="0.1" value={confidence} onChange={(event) => setConfidence(Number(event.target.value))} />
        <output>[{lower.toPrecision(4)}, {upper.toPrecision(4)}]<small>{metric.units}</small></output>
        <p>Published estimate {metric.estimate.toPrecision(4)} / sample size {metric.sample_size}</p>
      </div>
    </div>
  );
}

function groupWarnings(entries) {
  const groups = new Map();
  entries.forEach((entry) => {
    const text = String(entry);
    const rule = warningRules.find(({ pattern }) => pattern.test(text)) ?? {
      key: 'other',
      label: 'Other documented caveat',
      description: 'Additional analysis context retained for reproducibility.',
      tone: 'caveat',
    };
    const group = groups.get(rule.key) ?? { ...rule, entries: [] };
    group.entries.push(text);
    groups.set(rule.key, group);
  });
  return [...groups.values()];
}

function WarningPanel({ warnings }) {
  const entries = useMemo(() => (Array.isArray(warnings.data) ? warnings.data : []), [warnings.data]);
  const groups = useMemo(() => groupWarnings(entries), [entries]);

  if (warnings.loading) return <p className="feed-status">Reading results/warnings.json…</p>;
  if (warnings.error) return <p className="feed-error">Warning feed unavailable: {String(warnings.error)}</p>;
  if (entries.length === 0) return <p className="feed-clear"><CheckCircle2 size={19} />No warnings recorded in results/warnings.json.</p>;

  return (
    <div className="warning-panel">
      <header><div><strong>{entries.length}</strong><span>documented {entries.length === 1 ? 'entry' : 'entries'}</span></div><p>Grouped by scientific meaning. Amber marks a limitation; red is reserved for validation failure.</p></header>
      <div className="warning-groups">
        {groups.map((group) => (
          <article className={`warning-group ${group.tone}`} key={group.key}>
            <span>{group.entries.length}</span><div><h3>{group.label}</h3><p>{group.description}</p></div>
          </article>
        ))}
      </div>
      <details><summary>Show all {entries.length} raw {entries.length === 1 ? 'entry' : 'entries'}</summary><ol>{entries.map((entry, index) => <li key={`${index}-${entry}`}>{entry}</li>)}</ol></details>
    </div>
  );
}

class HeroBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) return <div className="hero-fallback">Transit schematic unavailable.</div>;
    return this.props.children;
  }
}

export default function App() {
  const project = useJson('./project.json');
  const summary = useJson('./results/summary.json');
  const warnings = useJson('./results/warnings.json');
  const benchmarks = useJson('./results/benchmarks.json');

  if (project.loading) return <main className="loading-screen">Opening atmospheric evidence log…</main>;
  if (project.error || !project.data) return <main className="loading-screen loading-error">Could not load project.json: {String(project.error)}</main>;

  const p = project.data;
  const isDemo = summary.data?.data_kind === 'synthetic_smoke_test' || summary.data?.data_kind === 'synthetic_demo';

  return (
    <main className="atmosphere-shell">
      <header className="topline">
        <a href="#top"><Orbit size={17} />WASP-39 b / CO</a>
        <nav aria-label="Report sections"><a href="#readings">Readings</a><a href="#spectra">Spectra</a><a href="#audit">Audit</a><a href="#notes">Notes</a></nav>
        <span><i />live evidence</span>
      </header>

      <section className="transit-hero" id="top">
        <div className="hero-copy">
          <p><Sparkles size={14} />{p.category}</p>
          <h1>Atmosphere,<br /><em>in transit.</em></h1>
          <h2>{p.title}</h2>
          <blockquote>{p.question}</blockquote>
          <div className="hero-tags"><span>{p.status}</span><span>Priority {p.priority}/10</span><span>{isDemo ? 'Synthetic demo' : 'Real public spectrum'}</span></div>
        </div>
        <figure className="transit-figure">
          <HeroBoundary><Suspense fallback={<div className="hero-fallback">Rendering transit geometry…</div>}><AtmosphereHero /></Suspense></HeroBoundary>
          <figcaption>Stylized illustration, not flight data</figcaption>
        </figure>
        <aside className="hero-ledger"><span>DATA MODE</span><strong>{p.dataMode}</strong><span>EVIDENCE STEP</span><strong>Full model vs. no-CO model</strong></aside>
      </section>

      {isDemo && <div className="demo-banner"><AlertTriangle size={18} /><p>Synthetic validation output is displayed, not real WASP-39 b observations.</p></div>}

      <section className="report-section readings-section" id="readings">
        <SectionHeading index="01" eyebrow="Evidence readings" title="Five signals, one nested-model comparison." copy="Every value is loaded from the published summary. Missing estimates and confidence intervals remain explicitly unavailable." />
        {summary.error && <p className="feed-error">Result feed unavailable: {String(summary.error)}</p>}
        <div className="metrics-grid">
          {summary.data?.metrics?.slice(0, 6).map((metric, index) => <MetricCard metric={metric} index={index} key={metric.name} />)}
          {!summary.loading && !summary.data && !summary.error && <article className="metric-card metric-unavailable"><p>Result status</p><div className="metric-value"><strong>Unavailable</strong></div><footer><span>Run scripts/run_analysis.py</span></footer></article>}
        </div>
        <ConfidenceExplorer metrics={summary.data?.metrics} />
      </section>

      <section className="report-section spectra-section" id="spectra">
        <SectionHeading index="02" eyebrow="Spectral atlas" title="Trace the evidence from spectrum to stability." copy="The gallery follows the real model overlay, residual structure, information criteria, bootstrap interval, and segment test." />
        <div className="spectra-mosaic">
          {p.figures.map((figure, index) => (
            <figure key={figure.id} className={`spectrum-card spectrum-${index + 1}`}>
              <div><span>{String(index + 1).padStart(2, '0')}</span><i>{figure.id}</i></div>
              <img src={`./figures/${figure.id}.svg`} alt={figure.label} loading="lazy" />
              <figcaption>{figure.label}</figcaption>
            </figure>
          ))}
        </div>
      </section>

      <section className="report-section audit-section" id="audit">
        <SectionHeading index="03" eyebrow="Interpretation airlock" title="Evidence enters only after provenance and validation." />
        <div className="provenance-ribbon">
          <div><ShieldCheck size={24} /><span>Boundary</span><p>{p.novelty}</p></div>
          <dl>
            <div><dt><GitCommit size={14} />Commit</dt><dd>{summary.data?.provenance?.git_commit ?? 'Unavailable'}</dd></div>
            <div><dt><FileText size={14} />Config SHA-256</dt><dd title={summary.data?.provenance?.config_sha256}>{summary.data?.provenance?.config_sha256 ?? 'Unavailable'}</dd></div>
            <div><dt><Beaker size={14} />Package</dt><dd>{summary.data?.provenance?.package_version ?? 'Unavailable'}</dd></div>
          </dl>
        </div>
        <div className="validation-flow">
          {p.validationContract.map((item, index) => <article key={item}><span>V{String(index + 1).padStart(2, '0')}</span><i /><p>{item}</p></article>)}
        </div>
        <div className="warning-shell"><div className="warning-title"><AlertTriangle size={17} /><span>WARNINGS.JSON / LIVE INTERPRETATION FEED</span></div><WarningPanel warnings={warnings} /></div>
      </section>

      <section className="report-section notes-section" id="notes">
        <SectionHeading index="04" eyebrow="Field notes" title="A bridge to retrieval, not a retrieval itself." />
        <div className="notes-grid">
          <article className="method-note"><Activity size={21} /><span>Methodology</span><h3>Read the published nested models against the published spectrum.</h3><p>{p.methodology}</p></article>
          <article className="boundary-note"><BookOpen size={19} /><h3>Assumptions</h3><ol>{p.assumptions.map((item, index) => <li key={item}><span>A{index + 1}</span>{item}</li>)}</ol></article>
          <article className="boundary-note"><AlertTriangle size={19} /><h3>Limitations</h3><ol>{p.limitations.map((item, index) => <li key={item}><span>L{index + 1}</span>{item}</li>)}</ol></article>
        </div>
      </section>

      <section className="report-section archive-section">
        <SectionHeading index="05" eyebrow="Evidence archive" title="Take the manifest and machine-readable results." />
        <div className="archive-grid">
          <div className="download-list">
            <a href="./manifest.csv" download><span>01</span><strong>data/manifest.csv</strong><ArrowDownToLine size={17} /></a>
            <a href="./results/summary.json" download><span>02</span><strong>results/summary.json</strong><ArrowDownToLine size={17} /></a>
            {benchmarks.data && <a href="./results/benchmarks.json" download><span>03</span><strong>results/benchmarks.json</strong><ArrowDownToLine size={17} /></a>}
          </div>
          <article className="citation-card"><Database size={20} /><span>Citation and licence</span><p>Author <strong>{p.citation.author}</strong></p><p>Licence <strong>{p.citation.license}</strong></p><a href={p.citation.repository}>Repository <ExternalLink size={14} /></a></article>
        </div>
      </section>

      <footer className="site-footer"><span><Waves size={15} />JWST WASP-39 b evidence ladder</span><span>Biswajit Jana / 2026</span></footer>
    </main>
  );
}
