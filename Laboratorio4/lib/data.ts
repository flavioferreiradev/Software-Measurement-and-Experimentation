import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { DashboardData, RealResult, S01, S02 } from "./types";

const root = process.cwd();

function readJson<T>(path: string): T {
  return JSON.parse(readFileSync(join(root, path), "utf8")) as T;
}

function parseCsvLine(line: string): string[] {
  const fields: string[] = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (quoted && line[i + 1] === '"') { value += '"'; i += 1; }
      else quoted = !quoted;
    } else if (char === "," && !quoted) {
      fields.push(value);
      value = "";
    } else value += char;
  }
  if (quoted) throw new Error("CSV real com aspas inválidas.");
  fields.push(value);
  return fields;
}

function normalSurvival(z: number): number {
  // Abramowitz–Stegun 7.1.26, erro absoluto menor que 8e-8.
  const a = Math.abs(z);
  const t = 1 / (1 + 0.2316419 * a);
  const polynomial = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
  const upper = Math.exp(-a * a / 2) / Math.sqrt(2 * Math.PI) * polynomial;
  return z >= 0 ? upper : 1 - upper;
}

function binomialUpperTail(k: number, n: number, p: number): number {
  let mass = Math.pow(1 - p, n);
  let total = k === 0 ? mass : 0;
  for (let count = 1; count <= n; count += 1) {
    mass *= (n - count + 1) / count * p / (1 - p);
    if (count >= k) total += mass;
  }
  return total;
}

type CsvMetadata = {
  csv_sha256: string; valid_count: number; repository: string; workflow_id: number;
  branch: string; event: string; created_window: { start: string; end: string };
  audit: Array<Record<string, string | number> & { selection: string }>;
};

function analyzeReal(s01: S01): RealResult {
  const csv = readFileSync(join(root, "data/real_ci.csv"));
  const metadata = readJson<CsvMetadata>("data/source_metadata.json");
  const digest = createHash("sha256").update(csv).digest("hex");
  if (digest !== metadata.csv_sha256 || digest !== s01.source.csv_sha256) throw new Error("SHA256 do CSV real difere da coleta registrada.");

  const lines = csv.toString("utf8").trimEnd().split(/\r?\n/);
  const expectedFields = "run_id,repository,workflow_id,workflow_name,head_branch,event,status,conclusion,failed,run_attempt,created_at,updated_at,head_sha,html_url".split(",");
  const header = parseCsvLine(lines.shift() ?? "");
  if (header.join(",") !== expectedFields.join(",")) throw new Error("Cabeçalho do CSV real incompatível.");
  if (lines.length !== metadata.valid_count || lines.length < 30) throw new Error("Quantidade de observações reais inválida.");

  const included = new Map(metadata.audit.filter(row => row.selection === "included").map(row => [String(row.run_id), row]));
  const seen = new Set<string>();
  let k = 0;
  for (const line of lines) {
    const values = parseCsvLine(line);
    if (values.length !== header.length) throw new Error("Linha incompleta no CSV real.");
    const row = Object.fromEntries(header.map((field, index) => [field, values[index]]));
    if (!/^\d+$/.test(row.run_id) || Number(row.run_id) < 1 || seen.has(row.run_id)) throw new Error("Execução real inválida ou duplicada.");
    seen.add(row.run_id);
    const audit = included.get(row.run_id);
    if (!audit || expectedFields.some(field => String(audit[field]) !== row[field])) throw new Error("CSV real diverge da auditoria.");
    if (row.repository !== metadata.repository || row.workflow_id !== String(metadata.workflow_id) || row.head_branch !== metadata.branch || row.event !== metadata.event || row.status !== "completed") throw new Error("Recorte do CSV real inválido.");
    const expectedFailure = row.conclusion === "success" ? "0" : ["failure", "timed_out"].includes(row.conclusion) ? "1" : "invalid";
    if (row.failed !== expectedFailure) throw new Error("Classificação real inválida.");
    if (row.html_url !== `https://github.com/${metadata.repository}/actions/runs/${row.run_id}`) throw new Error("URL da execução real inválida.");
    if (row.created_at < metadata.created_window.start || row.created_at > metadata.created_window.end) throw new Error("Data real fora da janela.");
    if (!/^[a-f0-9]{40}$/.test(row.head_sha) || !/^\d+$/.test(row.run_attempt) || Number(row.run_attempt) < 1) throw new Error("Identificador real inválido.");
    k += Number(row.failed);
  }
  if (seen.size !== included.size || k !== s01.empirical.k || lines.length !== s01.empirical.n) throw new Error("Amostra real difere do contrato S01.");

  const n = lines.length;
  const p0 = s01.scenario.p0;
  const alpha = s01.scenario.alpha;
  const p_hat = k / n;
  const z = (p_hat - p0) / Math.sqrt(p0 * (1 - p0) / n);
  const zP = normalSurvival(z);
  const exactP = binomialUpperTail(k, n, p0);
  return {
    n, k, p_hat, effect_difference: p_hat - p0,
    tests: {
      z: { statistic: z, p_value: zP, reject_h0: zP < alpha },
      binomial_exact: { statistic: p_hat, count_statistic: k, p_value: exactP, reject_h0: exactP < alpha },
    },
  };
}

export function loadDashboardData(): DashboardData {
  const s01 = readJson<S01>("results/demo_s01.json");
  const s02 = readJson<S02>("results/experiments_s02.json");
  if (s01.schema_version !== "1.0.0" || s02.schema_version !== "1.0.0") throw new Error("Versão dos contratos do Lab04 incompatível.");
  if (s01.scenario.p0 !== s02.protocol.p0 || s01.scenario.alpha !== s02.protocol.alpha) throw new Error("Protocolos S01 e S02 incompatíveis.");
  const rowIds = new Set(s02.rows.map(row => row.id));
  if (rowIds.size !== s02.rows.length || s02.g3.row_ids.length !== 2 || s02.g4.row_ids.length !== 12 || s02.g4.row_ids.some(id => !rowIds.has(id))) throw new Error("Seletores G3/G4 inválidos.");
  return { s01, s02, real: analyzeReal(s01) };
}
