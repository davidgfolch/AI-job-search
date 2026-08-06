import { CoverageReport } from 'monocart-coverage-reports';
import { coverageOptions } from './coverage.config';

/** Clean monocart's shared V8 cache so a previous run's coverage can't leak. */
export default async function globalSetup() {
  new CoverageReport(coverageOptions).cleanCache();
}
