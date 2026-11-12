"use client";

import { useState } from "react";
import type { ExperimentRow, S01, S02, TestKey } from "@/lib/types";

const C = { teal: "#087f8c", violet: "#6752b8", amber: "#e8a23a", red: "#c94b53", ink: "#29485b", muted: "#687f8d", grid: "#dce9ec" };
const pct = (v: number, digits = 1) => `${(v * 100).toFixed(digits).replace(".", ",")}%`;
const dec = (v: number, digits = 3) => v.toFixed(digits).replace(".", ",");

function Grid({ ticks, y, x1, x2, labelX = 43 }: { ticks: number[]; y: (v: number) => number; x1: number; x2: number; labelX?: number }) {
  return <g aria-hidden="true">{ticks.map(tick => <g key={tick}>
    <line x1={x1} x2={x2} y1={y(tick)} y2={y(tick)} stroke={C.grid} strokeDasharray={tick === 0 ? undefined : "4 5"} />
    <text x={labelX} y={y(tick) + 4} textAnchor="end" className="axis-text">{pct(tick, 0)}</text>
  </g>)}</g>;
}

export function Histogram({ s01, group }: { s01: S01; group: "real" | "simulated" }) {
  const counts = s01.g1[group].counts;
  const n = counts.reduce((sum, count) => sum + count, 0);
  const y = (v: number) => 260 - v * 215;
  const bars = [165, 365];
  const color = group === "real" ? C.teal : C.violet;
  return <svg className="chart-svg" viewBox="0 0 620 330" role="img" aria-label={`G1. Frequência relativa de sucessos e falhas nos dados ${group === "real" ? "reais" : "simulados"}.`}>
    <text x="58" y="24" className="axis-title">Frequência relativa</text>
    <Grid ticks={[0, .2, .4, .6, .8, 1]} y={y} x1={58} x2={590} labelX={48} />
    {counts.map((count, i) => {
      const rate = count / n;
      return <g key={i} className="chart-item"><title>{`${s01.g1.labels[i]}: ${count}/${n} (${pct(rate, 2)})`}</title>
        <rect className="chart-bar" x={bars[i]} y={y(rate)} width="105" height={260 - y(rate)} rx="9" fill={color} opacity={i === 0 ? .9 : .72} />
        <text x={bars[i] + 52.5} y={y(rate) - 10} textAnchor="middle" className="bar-value chart-detail">{pct(rate, 1)}</text>
        <text x={bars[i] + 52.5} y="285" textAnchor="middle" className="axis-text">{s01.g1.labels[i]}</text>
      </g>;
    })}
    <text x="325" y="316" textAnchor="middle" className="axis-title">Resultado da execução de CI</text>
  </svg>;
}

function tailPath(xs: number[], ys: number[], lower: number, sx: (v: number) => number, sy: (v: number) => number, bottom: number) {
  const index = xs.findIndex(x => x >= lower);
  if (index < 0) return "";
  const left = Math.max(0, index - 1);
  const ratio = (lower - xs[left]) / (xs[index] - xs[left] || 1);
  const ordinate = left === index ? ys[index] : ys[left] + ratio * (ys[index] - ys[left]);
  const points = [[lower, ordinate], ...xs.slice(index).map((x, i) => [x, ys[index + i]])];
  return `M ${sx(lower)} ${bottom} L ${points.map(([x, yy]) => `${sx(x)} ${sy(yy)}`).join(" L ")} L ${sx(xs.at(-1)!)} ${bottom} Z`;
}

export function ZDistribution({ s01 }: { s01: S01 }) {
  const z = s01.g2.z;
  const min = z.x[0], max = z.x.at(-1)!;
  const sx = (v: number) => 58 + (v - min) / (max - min) * 630;
  const sy = (v: number) => 285 - v / .43 * 235;
  const curve = z.x.map((x, i) => `${i ? "L" : "M"} ${sx(x)} ${sy(z.pdf[i])}`).join(" ");
  return <svg className="chart-svg" viewBox="0 0 740 370" role="img" aria-label="G2. Distribuição normal aproximada do teste Z, cauda do p-valor e região de rejeição.">
    <text x="58" y="25" className="axis-title">Densidade de probabilidade</text>
    {[0, .1, .2, .3, .4].map(v => <g key={v}><line x1="58" x2="688" y1={sy(v)} y2={sy(v)} stroke={C.grid} strokeDasharray={v ? "4 5" : undefined}/><text x="48" y={sy(v)+4} textAnchor="end" className="axis-text">{dec(v, 1)}</text></g>)}
    <path className="chart-area" d={tailPath(z.x, z.pdf, z.observed, sx, sy, 285)} fill={C.amber} opacity=".58" />
    <path className="chart-area" d={tailPath(z.x, z.pdf, z.critical_value, sx, sy, 285)} fill={C.red} opacity=".76" />
    <path className="chart-curve" d={curve} fill="none" stroke={C.teal} strokeWidth="3" />
    <line x1={sx(z.observed)} x2={sx(z.observed)} y1="65" y2="285" stroke={C.teal} strokeWidth="2" strokeDasharray="4 5"/>
    <line x1={sx(z.critical_value)} x2={sx(z.critical_value)} y1="78" y2="285" stroke={C.red} strokeWidth="2" strokeDasharray="7 5"/>
    <rect x={sx(z.observed)-128} y="69" width="124" height="24" rx="5" fill="#f1faf8"/><text x={sx(z.observed)-8} y="86" textAnchor="end" className="annotation teal">observado {dec(z.observed)}</text>
    <rect x={sx(z.critical_value)+5} y="96" width="117" height="24" rx="5" fill="#fff2f0"/><text x={sx(z.critical_value)+12} y="113" className="annotation red">crítico {dec(z.critical_value)}</text>
    {[-3,-2,-1,0,1,2,3].map(v => <text key={v} x={sx(v)} y="305" textAnchor="middle" className="axis-text">{v}</text>)}
    <text x="373" y="338" textAnchor="middle" className="axis-title">Estatística Z (desvios-padrão)</text>
    <g transform="translate(76 350)" className="chart-legend"><circle r="5" fill={C.teal}/><text x="10">N(0,1)</text><circle cx="100" r="5" fill={C.amber}/><text x="110">Área do p-valor</text><circle cx="260" r="5" fill={C.red}/><text x="270">Região de rejeição</text></g>
  </svg>;
}

export function BinomialDistribution({ s01 }: { s01: S01 }) {
  const [all, setAll] = useState(false);
  const exact = s01.g2.binomial_exact;
  const visible = all ? exact.k_support : exact.k_support.slice(0, 14);
  const maxMass = Math.max(...exact.pmf);
  const bottom = 276;
  const sy = (v: number) => bottom - v / (maxMass * 1.15) * 220;
  const gap = all ? 1.8 : 5;
  const width = (610 - gap * (visible.length - 1)) / visible.length;
  const sx = (i: number) => 67 + i * (width + gap);
  return <div>
    <svg className="chart-svg" viewBox="0 0 740 365" role="img" aria-label="G2. Distribuição binomial exata, massas da cauda do p-valor e região de rejeição.">
      <defs><pattern id="critical-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke={C.red} strokeWidth="2"/></pattern></defs>
      <text x="60" y="25" className="axis-title">Massa de probabilidade</text>
      {[0, .1, .2, .3].map(v => <g key={v}><line x1="60" x2="690" y1={sy(v)} y2={sy(v)} stroke={C.grid} strokeDasharray={v ? "4 5" : undefined}/><text x="50" y={sy(v)+4} textAnchor="end" className="axis-text">{dec(v, 1)}</text></g>)}
      {visible.map((k, i) => {
        const mass = exact.pmf[i]; const inTail = exact.p_value_mask[i]; const critical = exact.rejection_mask[i];
        return <g key={k} className="chart-item"><title>{`K=${k}: massa ${dec(mass, 5)}${critical ? "; região crítica" : inTail ? "; área do p-valor" : ""}`}</title>
          <rect className="chart-bar" x={sx(i)} y={sy(mass)} width={width} height={bottom-sy(mass)} rx={all ? 1 : 3} fill={inTail ? C.amber : C.violet} opacity={inTail ? .86 : .48}/>
          {critical && <rect className="chart-bar" x={sx(i)} y={sy(mass)} width={width} height={bottom-sy(mass)} fill="url(#critical-hatch)" stroke={C.red} strokeWidth="1"/>}
          {(all ? k % 5 === 0 : k % 2 === 0) && <text x={sx(i)+width/2} y="295" textAnchor="middle" className="axis-text">{k}</text>}
        </g>;
      })}
      <line x1={sx(exact.observed_k)+width/2} x2={sx(exact.observed_k)+width/2} y1="70" y2="276" stroke={C.violet} strokeWidth="2" strokeDasharray="3 5"/>
      <rect x={sx(exact.observed_k)+width/2+7} y="75" width="112" height="23" rx="5" fill="#f2effb"/><text x={sx(exact.observed_k)+width/2+14} y="91" className="annotation violet">K observado = {exact.observed_k}</text>
      <text x="370" y="326" textAnchor="middle" className="axis-title">Número K de falhas (execuções)</text>
      <g transform="translate(76 351)" className="chart-legend"><circle r="5" fill={C.violet}/><text x="10">Massa sob H₀</text><circle cx="145" r="5" fill={C.amber}/><text x="155">Área do p-valor</text><circle cx="305" r="5" fill={C.red}/><text x="315">Região crítica</text></g>
    </svg>
    <button type="button" className="chart-toggle" onClick={() => setAll(value => !value)} aria-pressed={all}>{all ? "Ampliar K = 0–13" : "Ver suporte completo K = 0–42"} <span aria-hidden="true">↗</span></button>
  </div>;
}

function selectedRows(s02: S02, selector: "g3" | "g4"): ExperimentRow[] {
  const byId = new Map(s02.rows.map(row => [row.id, row]));
  return s02[selector].row_ids.map(id => { const row = byId.get(id); if (!row) throw new Error(`Linha ${id} ausente`); return row; });
}

export function TypeIChart({ s02 }: { s02: S02 }) {
  const rows = selectedRows(s02, "g3");
  const sy = (v: number) => 314 - v / .085 * 255;
  const groups = [270, 610];
  return <svg className="chart-svg chart-wide" viewBox="0 0 900 420" role="img" aria-label="G3. Erro tipo I do teste Z e binomial exato para amostras de 200 e 42 execuções, com intervalos de Monte Carlo e linha nominal de 5%.">
    <text x="58" y="25" className="axis-title">Amostras rejeitadas (%)</text>
    <Grid ticks={[0,.02,.04,.06,.08]} y={sy} x1={62} x2={853} labelX={51}/>
    <line x1="62" x2="853" y1={sy(.05)} y2={sy(.05)} stroke={C.red} strokeWidth="2" strokeDasharray="8 6"/><text x="70" y={sy(.05)-9} className="annotation red">α = 5% nominal</text>
    {rows.map((row, i) => <g key={row.id}>{(["z", "binomial_exact"] as TestKey[]).map((key, j) => {
      const result = row.tests[key]; const x = groups[i] + (j === 0 ? -67 : 17); const color = key === "z" ? C.teal : C.violet;
      return <g key={key} className="chart-item"><title>{`${row.n} execuções, ${key === "z" ? "teste Z" : "binomial exato"}: ${pct(result.rejection_rate,2)}; IC MC 95% [${pct(result.mc_ci95_wilson[0],2)}, ${pct(result.mc_ci95_wilson[1],2)}]`}</title>
        <rect className="chart-bar" x={x} y={sy(result.rejection_rate)} width="66" height={314-sy(result.rejection_rate)} rx="6" fill={color}/>
        <line className="chart-detail" x1={x+33} x2={x+33} y1={sy(result.mc_ci95_wilson[0])} y2={sy(result.mc_ci95_wilson[1])} stroke={C.ink} strokeWidth="1.5"/>
        <line className="chart-detail" x1={x+26} x2={x+40} y1={sy(result.mc_ci95_wilson[0])} y2={sy(result.mc_ci95_wilson[0])} stroke={C.ink} strokeWidth="1.5"/>
        <line className="chart-detail" x1={x+26} x2={x+40} y1={sy(result.mc_ci95_wilson[1])} y2={sy(result.mc_ci95_wilson[1])} stroke={C.ink} strokeWidth="1.5"/>
        <text x={x+33} y={sy(result.mc_ci95_wilson[1])-11} textAnchor="middle" className="bar-value chart-detail">{pct(result.rejection_rate,2)}</text>
      </g>;
    })}<text x={groups[i]+8} y="341" textAnchor="middle" className="axis-label">{row.n === 200 ? "Referência · n = 200" : "Amostra pequena · n = 42"}</text></g>)}
    <text x="450" y="374" textAnchor="middle" className="axis-title">Situação simulada</text>
    <g transform="translate(312 403)" className="chart-legend"><circle r="5" fill={C.teal}/><text x="11">Teste Z</text><circle cx="110" r="5" fill={C.violet}/><text x="121">Binomial exato</text></g>
  </svg>;
}

export function PowerChart({ s02 }: { s02: S02 }) {
  const rows = selectedRows(s02, "g4");
  const sx = (v: number) => 73 + v / 15 * 785;
  const sy = (v: number) => 343 - v * 285;
  const series = s02.scenarios.flatMap(scenario => (["z", "binomial_exact"] as TestKey[]).map(key => ({ scenario, key, values: rows.filter(row => row.scenario_id === scenario.id).sort((a,b) => a.delta-b.delta) })));
  return <svg className="chart-svg chart-wide" viewBox="0 0 940 490" role="img" aria-label="G4. Curvas de poder para dois testes em amostras de 42 e 200 execuções, conforme cresce a taxa geradora de falhas.">
    <text x="73" y="28" className="axis-title">Amostras rejeitadas (%)</text>
    <Grid ticks={[0,.2,.4,.6,.8,1]} y={sy} x1={73} x2={858} labelX={60}/>
    {[0,2.5,5,7.5,10,15].map(v => <g key={v}><line x1={sx(v)} x2={sx(v)} y1="343" y2="348" stroke={C.muted}/><text x={sx(v)} y="365" textAnchor="middle" className="axis-text">{String(v).replace(".", ",")}</text></g>)}
    {series.map(({scenario,key,values}, seriesIndex) => {
      const color = key === "z" ? C.teal : C.violet;
      const name = `${key === "z" ? "Teste Z" : "Binomial exato"} · n=${scenario.n}`;
      return <g key={`${scenario.id}-${key}`}>
        <path className="chart-series" style={{ animationDelay: `${seriesIndex * 130}ms` }} d={values.map((row,i) => `${i ? "L" : "M"} ${sx(row.delta*100)} ${sy(row.tests[key].rejection_rate)}`).join(" ")} fill="none" stroke={color} strokeWidth={scenario.n === 200 && key === "z" ? 5 : key === "z" ? 3.5 : 2.5} strokeDasharray={scenario.n === 200 ? "9 6" : undefined}/>
        {values.map(row => <g key={row.id} className="chart-item"><title>{`${name}; aumento ${dec(row.delta*100,1)} p.p.; rejeições ${pct(row.tests[key].rejection_rate,2)}`}</title>
          {key === "z" ? <circle className="chart-point" cx={sx(row.delta*100)} cy={sy(row.tests[key].rejection_rate)} r="5" fill={color} stroke="white" strokeWidth="1.5"/> : <rect className="chart-point" x={sx(row.delta*100)-5} y={sy(row.tests[key].rejection_rate)-5} width="10" height="10" transform={`rotate(45 ${sx(row.delta*100)} ${sy(row.tests[key].rejection_rate)})`} fill="white" stroke={color} strokeWidth="2"/>}
        </g>)}
      </g>;
    })}
    <text x="465" y="400" textAnchor="middle" className="axis-title">Aumento da taxa de falhas Δ (pontos percentuais)</text>
    <g className="chart-legend" transform="translate(151 437)"><line x1="0" x2="24" y1="0" y2="0" stroke={C.teal} strokeWidth="3"/><text x="32">Z · n=42</text><line x1="145" x2="169" stroke={C.violet} strokeWidth="3"/><text x="177">Exato · n=42</text><line x1="320" x2="344" stroke={C.teal} strokeWidth="3" strokeDasharray="6 4"/><text x="352">Z · n=200</text><line x1="475" x2="499" stroke={C.violet} strokeWidth="3" strokeDasharray="6 4"/><text x="507">Exato · n=200</text></g>
    <text x="73" y="475" className="chart-note">Δ=0 representa erro tipo I; os demais pontos representam poder.</text>
  </svg>;
}
