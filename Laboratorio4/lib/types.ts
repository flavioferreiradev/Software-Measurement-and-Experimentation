export type TestKey = "z" | "binomial_exact";

export type S01 = {
  schema_version: string;
  scenario: { question_pt: string; p0: number; alpha: number };
  source: { repository: string; workflow_url: string; event: string; branch: string; observed_period: { start: string; end: string }; csv_sha256: string };
  empirical: { n: number; k: number; p_hat: number };
  generator: { n: number; p: number; seed: number };
  g1: {
    labels: string[];
    real: { values: number[]; counts: number[] };
    simulated: { values: number[]; counts: number[] };
  };
  example: { n: number; k: number; p_hat: number; tests: { z: { expected_failures_h0: number } } };
  g2: {
    z: {
      x: number[]; pdf: number[]; observed: number; critical_value: number;
      p_value_tail: { area: number }; critical_tail: { area: number };
    };
    binomial_exact: {
      n: number; p0: number; k_support: number[]; pmf: number[];
      observed_k: number; critical_k: number; p_value_area: number; critical_area: number;
      p_value_mask: boolean[]; rejection_mask: boolean[];
    };
  };
};

export type ExperimentResult = {
  rejections: number;
  rejection_rate: number;
  theoretical_rejection_rate: number;
  mc_ci95_wilson: [number, number];
};

export type ExperimentRow = {
  id: string; scenario_id: string; n: number; p: number; delta: number;
  estimand: string; repetitions: number;
  tests: Record<TestKey, ExperimentResult>;
};

export type S02 = {
  schema_version: string;
  protocol: { p0: number; alpha: number; repetitions: number; p_levels: number[] };
  scenarios: { id: string; label_pt: string; n: number }[];
  rows: ExperimentRow[];
  g3: { row_ids: string[]; nominal_rate: number };
  g4: { row_ids: string[] };
};

export type RealResult = {
  n: number; k: number; p_hat: number; effect_difference: number;
  tests: Record<TestKey, { statistic: number; p_value: number; reject_h0: boolean; count_statistic?: number }>;
};

export type DashboardData = { s01: S01; s02: S02; real: RealResult };
