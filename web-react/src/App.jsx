import { useEffect, useState } from 'react';
import { ArrowUpRight, Database, Download, Github, Microscope } from 'lucide-react';

function useJson(path) {
  const [state, setState] = useState({ data: null, error: null });
  useEffect(() => {
    const controller = new AbortController();
    fetch(path, { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); })
      .then((data) => setState({ data, error: null }))
      .catch((error) => { if (error.name !== 'AbortError') setState({ data: null, error }); });
    return () => controller.abort();
  }, [path]);
  return state;
}

const metricLabels = {
  co_sub_band_mean_contrast: ['CO contrast', 'The primary in-band minus out-of-band estimand'],
  welch_t_statistic: ['Welch t', 'Unequal-variance test statistic'],
  welch_p_one_sided: ['One-sided p', 'Conditional on Welch-test assumptions'],
  permutation_p_one_sided: ['Permutation p', 'Exploratory exchangeable-label check'],
  fixed_curve_delta_chi2: ['Fixed-curve Δχ²', 'Descriptive only; models were not refit'],
  fixed_curve_chi2_per_point_full: ['Full curve χ²/N', 'Residual scale for the archived full curve'],
};

function number(value) {
  if (!Number.isFinite(value)) return '—';
  if (Math.abs(value) < 0.001) return value.toExponential(2);
  return value.toLocaleString(undefined, { maximumSignificantDigits: 5 });
}

function Metric({ metric, index }) {
  const [label, note] = metricLabels[metric.name] ?? [metric.name.replaceAll('_', ' '), 'Published pipeline metric'];
  return <article className={`metric metric-${index + 1}`}>
    <span>0{index + 1}</span><div><p>{label}</p><strong>{number(metric.estimate)}</strong><small>{metric.units}</small>
      {metric.uncertainty_low != null && <em>bootstrap 95%: {number(metric.uncertainty_low)}–{number(metric.uncertainty_high)}</em>}
      <footer>{note} · n={metric.sample_size}</footer></div>
  </article>;
}

function App() {
  const project = useJson('./project.json');
  const summary = useJson('./results/summary.json');
  const warnings = useJson('./results/warnings.json');
  if (project.error) return <main className="loading">Project metadata unavailable.</main>;
  if (!project.data) return <main className="loading">Loading scientific record…</main>;
  const p = project.data;
  const metrics = summary.data?.metrics ?? [];
  const primary = metrics.find((item) => item.name === 'co_sub_band_mean_contrast');
  return <main>
    <nav><a href="#top" className="wordmark"><Microscope size={18}/>WASP-39 b / CO</a><div><a href="#result">Result</a><a href="#figures">Figures</a><a href="#method">Method</a><a href="#limits">Limits</a></div><a href={p.citation.repository} aria-label="GitHub repository"><Github size={18}/></a></nav>

    <header id="top" className="hero">
      <div className="hero-kicker"><span>REPRODUCTION NOTE 01</span><i/>JWST · NIRSpec G395H</div>
      <h1>Carbon monoxide<br/>in <em>WASP-39 b</em></h1>
      <div className="hero-bottom"><p>{p.subtitle}</p><dl><div><dt>Data</dt><dd>256 selected spectral samples</dd></div><div><dt>Archive</dt><dd>Zenodo 7866690</dd></div><div><dt>Scope</dt><dd>Derived-product reproduction</dd></div></dl></div>
    </header>

    <section className="question"><span>Scientific question</span><p>{p.question}</p></section>

    <section id="result" className="section result-section">
      <div className="section-label"><span>01</span><p>Primary result</p></div>
      <div className="result-lead"><p>Released-array estimate</p><strong>{primary ? number(primary.estimate) : '—'}<small> ppm</small></strong><h2>The selected CO bands are deeper than the comparison bands.</h2><p>The reproduced contrast is conditional on the authors’ band definition. Agreement with the paper validates the computation; it is not a new independent detection.</p></div>
      <div className="metric-grid">{metrics.map((metric, index) => <Metric key={metric.name} metric={metric} index={index}/>)}</div>
    </section>

    <section id="figures" className="section figures-section">
      <div className="section-label"><span>02</span><p>Evidence figures</p></div>
      <div className="figure-grid">{p.figures.map((figure, index) => <figure key={figure.id} className={index === 0 || index === 4 ? 'wide' : ''}><header><span>FIG. {index + 1}</span><p>{figure.label}</p></header><img src={`./figures/${figure.id}.svg`} alt={figure.label}/></figure>)}</div>
    </section>

    <section id="method" className="section method-section">
      <div className="section-label"><span>03</span><p>Method</p></div>
      <div className="method-copy"><h2>One estimand,<br/>several checks.</h2><p>The analysis follows the released experiment rather than inventing a surrogate model-selection problem.</p></div>
      <ol>{p.methods.map((item, index) => <li key={item}><span>{String(index + 1).padStart(2, '0')}</span><p>{item}</p></li>)}</ol>
    </section>

    <section id="limits" className="section limits-section">
      <div className="section-label"><span>04</span><p>Interpretation boundary</p></div>
      <div className="limits-intro"><h2>What this result does—and does not—establish.</h2><p>Good scientific software exposes the conditions around a number as clearly as the number itself.</p></div>
      <ul>{p.limitations.map((item, index) => <li key={item}><span>L{index + 1}</span><p>{item}</p></li>)}</ul>
      {warnings.data && <details><summary>Pipeline warnings and release notes</summary>{warnings.data.map((item) => <p key={item}>{item}</p>)}</details>}
    </section>

    <section className="archive">
      <div><Database size={22}/><span>Reproducibility package</span><h2>Data, results, and provenance are inspectable.</h2></div>
      <div className="archive-links"><a href="./manifest.csv" download><Download size={17}/>Source manifest</a><a href="./results/summary.json" download><Download size={17}/>Machine-readable results</a><a href={p.citation.archive}><ArrowUpRight size={17}/>Source archive</a><a href={p.citation.doi}><ArrowUpRight size={17}/>Research article</a></div>
    </section>

    <footer><p>{p.citation.paper}</p><p>Analysis and interface · Biswajit Jana · 2026</p></footer>
  </main>;
}

export default App;
