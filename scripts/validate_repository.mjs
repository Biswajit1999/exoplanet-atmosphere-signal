import crypto from 'node:crypto';
import fs from 'node:fs';

const expected = new Map([
  ['data/raw/wasp39b_grant2023_transmission_spectrum.nc', '61c05c570ca39854b43b8958e44e97cd229710e6ecec2769a951b5d1b715fb95'],
  ['data/raw/wasp39b_grant2023_co_sub_band_samples.nc', '5fb4e75e1366b8b12f21c4317cc78e292dc713b92d52c278e35d3f5b4caeb4a0'],
  ['data/raw/wasp39b_grant2023_light_curves.nc', '5416546a1b35b3039d2c03af942bd7446851f352f643f58917e9af0269c1ea97'],
]);
const required = ['README.md', 'data/manifest.csv', 'data/provenance.yml', 'CITATION.cff'];
const failures = required.filter((file) => !fs.existsSync(file)).map((file) => `${file} missing`);
for (const [file, digest] of expected) {
  if (!fs.existsSync(file)) { failures.push(`${file} missing`); continue; }
  const actual = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  if (actual !== digest) failures.push(`${file} checksum mismatch`);
}
const readme = fs.readFileSync('README.md', 'utf8');
for (const phrase of ['263.66', '67.68', '6.30 × 10⁻⁵', '145 out-of-band']) {
  if (!readme.includes(phrase)) failures.push(`README missing reproduced result: ${phrase}`);
}
if (/strongly prefers the CO model|delta.?AIC|delta.?BIC/i.test(readme)) failures.push('README contains unsupported information-criterion claim');
if (failures.length) { console.error(failures.join('\n')); process.exit(1); }
console.log(`validated ${expected.size} archived products and bounded scientific claims`);
