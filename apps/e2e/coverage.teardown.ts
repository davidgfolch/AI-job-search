import { promises as fs } from 'fs';
import path from 'path';
import { CoverageReport } from 'monocart-coverage-reports';
import { coverageOptions } from './coverage.config';

/** Merge every worker's cached V8 coverage into the configured reports. */
export default async function globalTeardown() {
  const report = new CoverageReport(coverageOptions);
  if (report.hasCache()) {
    await report.generate();
  } else {
    await fs.rm(path.join(coverageOptions.outputDir, 'coverage-summary.json'), { force: true });
  }
}
