import { spawnSync } from "child_process";
import path from "path";

/**
 * Compute patch operations grouped by section and KPI deltas using Python helpers.
 */
export function diffWithKpi(source: any, target: any) {
  const repoRoot = path.resolve(__dirname, "../../../..");
  const script = path.join(repoRoot, "packages/py/odl_sd_patch/diff_cli.py");
  const input = JSON.stringify({ source, target });
  const result = spawnSync("python", [script], { input, encoding: "utf-8" });
  if (result.status !== 0) {
    throw new Error(result.stderr);
  }
  return JSON.parse(result.stdout);
}
