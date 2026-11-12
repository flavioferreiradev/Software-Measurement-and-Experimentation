"use client";

import { useEffect, useRef, useState } from "react";
import type { PointerEvent } from "react";
import { BinomialDistribution, Histogram, PowerChart, TypeIChart, ZDistribution } from "./charts";
import type { DashboardData, ExperimentRow, TestKey } from "@/lib/types";

const REPOSITORY = "https://github.com/flavioferreiradev/Software-Measurement-and-Experimentation";
const PROJECT = "https://github.com/users/flavioferreiradev/projects/3";
const chapters = [
  ["cenario", "Cenário"], ["dados", "Dados · G1"], ["testes", "Testes · G2"],
  ["erro", "Erro tipo I · G3"], ["poder", "Poder · G4"], ["reais", "Dados reais"], ["conclusao", "Conclusão"],
] as const;

const pct = (value: number, digits = 1) => `${(value * 100).toFixed(digits).replace(".", ",")}%`;
const dec = (value: number, digits = 6) => value.toFixed(digits).replace(".", ",");
const effect = (value: number) => `${(value * 100 >= 0 ? "+" : "") + (value * 100).toFixed(2).replace(".", ",")} p.p.`;

function Chapter({ id, number, title, subtitle, children }: { id: string; number: string; title: string; subtitle: string; children: React.ReactNode }) {
  return <section id={id} data-section className="chapter">
    <span className="chapter-watermark" aria-hidden="true">{number}</span>
    <div className="section-heading reveal"><div className="section-kicker"><span className="section-number">{number}</span><span>LAB04 · EXPLORAÇÃO</span><span className="section-rule"/></div>
      <h2>{title}</h2><p className="section-subtitle">{subtitle}</p></div>
    {children}
  </section>;
}

function pointerGlow(event: PointerEvent<HTMLElement>) {
  if (event.pointerType === "touch" || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const card = event.currentTarget;
  const bounds = card.getBoundingClientRect();
  card.style.setProperty("--spot-x", `${event.clientX - bounds.left}px`);
  card.style.setProperty("--spot-y", `${event.clientY - bounds.top}px`);
}

function AnimatedValue({ value, digits = 2, prefix = "", suffix = "%" }: { value: number; digits?: number; prefix?: string; suffix?: string }) {
  const node = useRef<HTMLSpanElement>(null);
  const [display, setDisplay] = useState(value);
  const format = (current: number) => `${prefix}${current.toFixed(digits).replace(".", ",")}${suffix}`;
  useEffect(() => {
    if (!node.current || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let frame = 0;
    const observer = new IntersectionObserver(entries => {
      if (!entries[0].isIntersecting) return;
      observer.disconnect();
      setDisplay(0);
      const start = performance.now();
      const duration = 1150;
      const tick = (now: number) => {
        const t = Math.min(1, (now - start) / duration);
        setDisplay(value * (1 - Math.pow(1 - t, 3)));
        if (t < 1) frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    }, { threshold: .5 });
    observer.observe(node.current);
    return () => { observer.disconnect(); cancelAnimationFrame(frame); };
  }, [value]);
  return <span ref={node} aria-label={format(value)}><span aria-hidden="true">{format(display)}</span></span>;
}

function Metric({ label, value, foot }: { label: string; value: string | number; foot: string }) {
  return <div className="metric-card reveal" onPointerMove={pointerGlow}><span>{label}</span><strong>{value}</strong><small>{foot}</small></div>;
}

function FigureCard({ title, meta, children, note }: { title: string; meta: string; children: React.ReactNode; note: React.ReactNode }) {
  return <article className="figure-card reveal" onPointerMove={pointerGlow}><div className="figure-head"><div><h3>{title}</h3><p>{meta}</p></div><span className="figure-action" aria-hidden="true">↗</span></div><div className="figure-body">{children}</div><p className="figure-note">{note}</p></article>;
}

function rowsFor(s02: DashboardData["s02"], selector: "g3" | "g4") {
  const map = new Map(s02.rows.map(row => [row.id, row]));
  return s02[selector].row_ids.map(id => map.get(id)!).filter(Boolean);
}

function Explorer({ rows, pLevels, p0 }: { rows: ExperimentRow[]; pLevels: number[]; p0: number }) {
  const [n, setN] = useState(42);
  const [index, setIndex] = useState(2);
  const p = pLevels[index];
  const row = rows.find(item => item.n === n && Math.abs(item.p - p) < 1e-12);
  if (!row) return <p>Cenário ausente no contrato S02.</p>;
  const isNull = p === p0;
  const z = row.tests.z.rejection_rate;
  const exact = row.tests.binomial_exact.rejection_rate;
  const story = isNull
    ? "Aqui p = p₀: as rejeições são falsos alarmes, ou erro tipo I."
    : `Com p = ${pct(p, 1)} (+${((p - p0) * 100).toFixed(1).replace(".", ",")} p.p. sobre a meta), estas rejeições medem poder.`;
  return <div id="lab-interativo" className="explorer reveal">
    <div className="explorer-intro"><span className="micro-label">EXPLORE O EXPERIMENTO</span><h3>E se mudarmos a taxa de falhas?</h3><p>Escolha um ponto já simulado na Sprint 02. As barras mostram a proporção de rejeições nas mesmas 10.000 repetições por cenário.</p></div>
    <div className="explorer-controls"><fieldset><legend>Tamanho da amostra</legend><div className="segmented" role="group" aria-label="Tamanho da amostra">{[42,200].map(value => <button key={value} type="button" aria-pressed={n===value} onClick={() => setN(value)}>n = {value}</button>)}</div></fieldset>
      <div className="range-wrap"><label htmlFor="failure-rate">Taxa geradora de falhas <strong>p = {pct(p,1)}</strong></label><input id="failure-rate" type="range" min="0" max={pLevels.length-1} step="1" value={index} onChange={event => setIndex(Number(event.target.value))}/><div className="range-labels">{pLevels.map((value,i) => <button type="button" key={value} className={index===i ? "selected" : ""} onClick={() => setIndex(i)} aria-label={`Taxa ${pct(value,1)}`}>{pct(value,1)}</button>)}</div></div>
    </div>
    <div className="live-comparison" aria-live="polite"><div className="live-comparison-top"><span>{isNull ? "ERRO TIPO I" : "PODER ESTATÍSTICO"} · n={n}</span><strong>p = {pct(p,1)}</strong></div>
      {(["z","binomial_exact"] as TestKey[]).map(key => { const rate = key === "z" ? z : exact; return <div className="compare-row" key={key}><div><span>{key === "z" ? "TESTE Z" : "BINOMIAL EXATO"}</span><strong>{pct(rate,2)}</strong></div><div className="compare-track"><span className={`compare-fill ${key === "z" ? "z" : "exact"}`} style={{ width: `${100*rate}%` }}/></div></div>; })}
      <p className="live-story">{story}</p></div>
  </div>;
}

export default function Dashboard({ data }: { data: DashboardData }) {
  const { s01, s02, real } = data;
  const [active, setActive] = useState("cenario");
  const progress = useRef<HTMLDivElement>(null);
  const nullRows = rowsFor(s02, "g3");
  const powerRows = rowsFor(s02, "g4");
  const nullByN = Object.fromEntries(nullRows.map(row => [row.n, row]));
  const tenByN = Object.fromEntries(powerRows.filter(row => Math.abs(row.p-.1)<1e-12).map(row => [row.n,row]));
  const realEffect = effect(real.effect_difference);
  const activeChapter = chapters.findIndex(([id]) => id === active) + 1;

  useEffect(() => {
    document.documentElement.classList.add("motion-ready");
    const onScroll = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (progress.current) progress.current.style.transform = `scaleX(${max > 0 ? Math.min(1,window.scrollY/max) : 0})`;
    };
    window.addEventListener("scroll", onScroll, { passive: true }); onScroll();
    const revealObserver = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add("is-visible"); revealObserver.unobserve(entry.target); } }), { threshold: .08, rootMargin: "0px 0px -35px 0px" });
    document.querySelectorAll(".reveal").forEach(node => revealObserver.observe(node));
    const sectionObserver = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) setActive(entry.target.id); }), { rootMargin: "-20% 0px -62% 0px" });
    document.querySelectorAll("[data-section]").forEach(node => sectionObserver.observe(node));
    return () => { window.removeEventListener("scroll", onScroll); revealObserver.disconnect(); sectionObserver.disconnect(); document.documentElement.classList.remove("motion-ready"); };
  }, []);

  return <>
    <div className="scroll-progress" ref={progress} aria-hidden="true" />
    <header className="site-header"><a href="#top" className="brand" aria-label="Voltar ao início"><span className="brand-mark">∑</span><span>LAB<span>04</span></span></a><span className="header-chapter" aria-hidden="true"><i/> CAPÍTULO {String(activeChapter).padStart(2,"0")} / 07</span><nav aria-label="Navegação principal"><a href="#cenario">Estudo</a><a href="#poder">Resultados</a><a href="#lab-interativo">Explorar</a><a href="#conclusao" className="header-cta">Conclusão <span aria-hidden="true">↗</span></a></nav></header>
    <div className="page-shell" id="top"><aside className="chapter-rail" aria-label="Capítulos do dashboard"><span className="rail-title">NESTA PÁGINA</span>{chapters.map(([id,label],i) => <a href={`#${id}`} key={id} className={active===id ? "active" : ""}><span>{String(i+1).padStart(2,"0")}</span>{label}</a>)}<div className="rail-foot">P4 · Z × binomial exato</div></aside>
    <main>
      <div className="hero reveal" onPointerMove={pointerGlow}><div className="hero-scan" aria-hidden="true"/><div className="hero-top"><span className="eyebrow">PUC MINAS · LABORATÓRIO 04</span><span className="status"><span className="status-dot"/> ENTREGA FINAL · G1–G4</span></div>
        <div className="hero-orbit" aria-hidden="true"><span className="orbit-ring orbit-ring-outer"/><span className="orbit-ring orbit-ring-inner"/><span className="orbit-dot"/><span className="orbit-core"><small>NÍVEL NOMINAL</small><strong>05<span>%</span></strong></span></div>
        <div className="hero-label"><span className="live-dot"/> UMA INVESTIGAÇÃO EM 7 CAPÍTULOS</div><h1>Testes de hipótese <span>por dentro</span></h1><p>Quando a taxa de falhas do CI parece superar a meta: o que o teste Z e o binomial exato realmente mostram?</p>
        <nav className="hero-links" aria-label="Links do projeto"><a href="#lab-interativo">Testar cenários <span aria-hidden="true">↘</span></a><a href="/">Dashboard <span aria-hidden="true">↗</span></a><a href={REPOSITORY} target="_blank" rel="noopener noreferrer">Repositório <span aria-hidden="true">↗</span></a><a href={PROJECT} target="_blank" rel="noopener noreferrer">GitHub Projects <span aria-hidden="true">↗</span></a></nav>
        <div className="hero-bottom"><span>ROLE PARA DESCOBRIR <b aria-hidden="true">↓</b></span><span>H₀: p ≤ 5% <i>·</i> H₁: p &gt; 5%</span></div>
      </div>

      <div className="story-map reveal" aria-label="Etapas do estudo"><div className="story-step"><span>01</span><strong>Observar</strong><small>Dados do CI</small></div><div className="story-step"><span>02</span><strong>Testar</strong><small>Z e binomial exato</small></div><div className="story-step"><span>03</span><strong>Simular</strong><small>Erro e poder</small></div><div className="story-step"><span>04</span><strong>Decidir</strong><small>Recomendação</small></div></div>

      <Chapter id="cenario" number="01" title="Cenário" subtitle="Uma pergunta de qualidade de software, duas maneiras de calcular a cauda sob H₀.">
        <p className="question reveal">{s01.scenario.question_pt}</p>
        <div className="metrics-grid"><Metric label="META DE FALHAS" value={pct(s01.scenario.p0,0)} foot="fronteira de H₀"/><Metric label="SIGNIFICÂNCIA" value={pct(s01.scenario.alpha,0)} foot="nível α"/><Metric label="EXECUÇÕES REAIS" value={s01.empirical.n} foot="amostra válida"/><Metric label="TESTES" value="Z + exato" foot="mesma pergunta"/></div>
        <div className="prose-grid reveal"><div><h3>Hipóteses e direção</h3><p>H₀: p ≤ {pct(s01.scenario.p0,0)}. H₁: p &gt; {pct(s01.scenario.p0,0)}. A cauda é à direita: só um excesso de falhas responde à pergunta. Cada observação é uma execução concluída do workflow; 0 significa sucesso e 1, falha ou timeout.</p></div><div><h3>Fonte e previsão</h3><p><a href={s01.source.workflow_url} target="_blank" rel="noopener noreferrer">Workflow test de {s01.source.repository} ↗</a>, eventos <code>{s01.source.event}</code> na branch <code>{s01.source.branch}</code>, entre {s01.source.observed_period.start.slice(0,10)} e {s01.source.observed_period.end.slice(0,10)} (UTC). Quatro execuções canceladas foram excluídas.</p><p>Antes da simulação, previmos que o binomial exato controlaria melhor o nível nominal com falhas raras e n pequeno.</p></div></div>
      </Chapter>

      <Chapter id="dados" number="02" title="Os dados · G1" subtitle="Histogramas discretos: os dois intervalos representam sucesso (0) e falha (1).">
        <div className="two-columns"><FigureCard title="Dados reais" meta={`n = ${s01.g1.real.values.length} · ${s01.g1.real.counts[0]} sucessos · ${s01.g1.real.counts[1]} falhas · p̂ = ${pct(s01.empirical.p_hat,2)}`} note={<>Das {real.n} execuções válidas, {real.k} falharam; a frequência observada é {pct(real.p_hat,2)}. A variável é binária, então não há assimetria nem outliers contínuos a interpretar. O recorte temporal descreve somente as execuções incluídas.</>}><Histogram s01={s01} group="real"/></FigureCard>
          <FigureCard title="Dados simulados" meta={`n = ${s01.g1.simulated.values.length} · ${s01.g1.simulated.counts[0]} sucessos · ${s01.g1.simulated.counts[1]} falhas · p̂ = ${pct(s01.g1.simulated.counts[1]/s01.g1.simulated.values.length,2)}`} note={<>Amostra Bernoulli(p={pct(s01.generator.p,2)}), n={s01.generator.n}, seed={s01.generator.seed}. O p veio da frequência real para manter uma escala plausível. O modelo supõe independência e probabilidade constante. As contagens coincidiram por acaso, embora as sequências sejam diferentes.</>}><Histogram s01={s01} group="simulated"/></FigureCard></div>
      </Chapter>

      <Chapter id="testes" number="03" title="Como os testes funcionam · G2" subtitle="Duas distribuições sob a fronteira H₀: p = 5%; p-valores do mesmo exemplo simulado.">
        <div className="notice reveal"><strong>Exemplo simulado:</strong> {s01.example.k} falhas em {s01.example.n} execuções (p̂ = {pct(s01.example.p_hat,2)}). Estes valores não são a inferência dos dados reais.</div>
        <div className="two-columns"><FigureCard title="Teste Z · aproximação normal" meta={`Z observado = ${dec(s01.g2.z.observed,3)} · Z crítico = ${dec(s01.g2.z.critical_value,3)} · p = ${dec(s01.g2.z.p_value_tail.area)}`} note={<>A curva N(0,1) aproxima a distribuição de Z sob H₀. A cauda âmbar começa no Z observado e representa p={dec(s01.g2.z.p_value_tail.area)}; a região vermelha começa no valor crítico. Como p ≥ α, não rejeitamos H₀. Aqui n·p₀=2,1: a aproximação normal pode ser ruim para falhas raras.</>}><ZDistribution s01={s01}/></FigureCard>
          <FigureCard title="Binomial exato · massas discretas" meta={`K observado = ${s01.g2.binomial_exact.observed_k} · crítico K ≥ ${s01.g2.binomial_exact.critical_k} · p = ${dec(s01.g2.binomial_exact.p_value_area)}`} note={<>As barras são massas Binomial(n=42, p₀=5%) sob H₀. O p-valor soma K ≥ {s01.g2.binomial_exact.observed_k}, incluindo a barra observada. As barras hachuradas K ≥ {s01.g2.binomial_exact.critical_k} formam a região crítica, com probabilidade {pct(s01.g2.binomial_exact.critical_area,3)}. Como p ≥ α, não rejeitamos H₀.</>}><BinomialDistribution s01={s01}/></FigureCard></div>
        <div className="explanation reveal"><strong>Por que os p-valores diferem?</strong> O Z usa uma cauda normal contínua aproximada. O binomial soma as massas inteiras de K=4 até 42; com só 2,1 falhas esperadas sob H₀, os degraus da distribuição importam. Não rejeitar H₀ não comprova que a meta foi atendida.</div>
      </Chapter>

      <Chapter id="erro" number="04" title="Erro tipo I · G3" subtitle="Q1 e Q3: 10.000 amostras sob p = 5% em cada tamanho amostral.">
        <div className="wide-figure reveal"><TypeIChart s02={s02}/></div>
        <div className="insight-strip reveal"><div className="insight-heading"><span className="micro-label">LEITURA RÁPIDA · n=42</span><strong>O tamanho da amostra muda o jogo.</strong></div><div className="insight-value teal"><span>TESTE Z</span><strong><AnimatedValue value={100*nullByN[42].tests.z.rejection_rate}/></strong><small>acima de α</small></div><div className="insight-value violet"><span>BINOMIAL EXATO</span><strong><AnimatedValue value={100*nullByN[42].tests.binomial_exact.rejection_rate}/></strong><small>abaixo de α</small></div></div>
        <p className="section-prose reveal">Em n=200, ambos rejeitaram H₀ em {pct(nullByN[200].tests.z.rejection_rate,2)} das amostras. A linha de 5% é nominal, não uma taxa que a simulação precise atingir exatamente. Em n=42, o Z chegou a {pct(nullByN[42].tests.z.rejection_rate,2)} e o binomial exato a {pct(nullByN[42].tests.binomial_exact.rejection_rate,2)}: o primeiro excedeu o nível nominal e o segundo foi conservador. As barras de erro mostram incerteza Monte Carlo das 10.000 repetições, não a incerteza da taxa real de falhas.</p>
      </Chapter>

      <Chapter id="poder" number="05" title="Poder · G4" subtitle="Q2 e Q3: frequência de rejeição conforme aumenta a taxa geradora de falhas.">
        <div className="wide-figure reveal"><PowerChart s02={s02}/></div>
        <div className="power-banner reveal"><div className="power-icon" aria-hidden="true">↗</div><div><span className="micro-label">PONTO DE COMPARAÇÃO · p=10%</span><strong>Com 200 execuções, os dois testes detectam o aumento em {pct(tenByN[200].tests.z.rejection_rate,2)} das amostras.</strong><span>Com 42 execuções, a capacidade de detecção cai e a escolha do teste pesa mais.</span></div></div>
        <p className="section-prose reveal">O ponto de efeito zero reutiliza Q1: ele mede erro tipo I; os pontos à direita medem poder. Quando p=10% (+5 p.p. sobre a meta), os testes rejeitaram em {pct(tenByN[200].tests.z.rejection_rate,2)} das amostras com n=200; as curvas coincidem porque ambos usam K≥16. Em n=42, foram {pct(tenByN[42].tests.z.rejection_rate,2)} para o Z e {pct(tenByN[42].tests.binomial_exact.rejection_rate,2)} para o exato. A maior detecção do Z deve ser lida junto ao erro tipo I acima de 5% em G3.</p>
        <Explorer rows={powerRows} pLevels={s02.protocol.p_levels} p0={s01.scenario.p0}/>
      </Chapter>

      <Chapter id="reais" number="06" title="Dados reais" subtitle="Inferência sobre o CSV validado, separada do exemplo simulado e das repetições Monte Carlo.">
        <div className="real-stats reveal"><div><span>RECORTE OBSERVADO</span><strong>{real.k}<em> / {real.n}</em></strong><small>falhas / execuções</small></div><div><span>TAXA OBSERVADA</span><strong><AnimatedValue value={100*real.p_hat}/></strong><small>meta de 5%</small></div><div><span>DIFERENÇA</span><strong><AnimatedValue value={100*real.effect_difference} prefix="+" suffix=" p.p."/></strong><small>acima da meta na amostra</small></div></div>
        <div className="table-scroll reveal"><table><caption>Resultados dos dois testes nos dados reais, α=5%</caption><thead><tr><th>Teste</th><th>Estatística</th><th>p-valor</th><th>Efeito observado</th><th>Decisão</th><th>Conclusão</th></tr></thead><tbody>{(["z","binomial_exact"] as TestKey[]).map(key => { const test = real.tests[key]; return <tr key={key}><th scope="row"><span className={`test-dot ${key === "z" ? "z" : "exact"}`}/>{key === "z" ? "Teste Z" : "Binomial exato"}</th><td>{key === "z" ? `Z = ${dec(test.statistic,3)}` : `K = ${test.count_statistic}; p̂ = ${pct(test.statistic,2)}`}</td><td className="number-cell">{dec(test.p_value)}</td><td>{realEffect}</td><td><span className={`decision ${test.reject_h0 ? "reject" : "retain"}`}>{test.reject_h0 ? "Rejeitar H₀" : "Não rejeitar H₀"}</span></td><td>{test.reject_h0 ? "Evidência de taxa acima de 5%" : "Evidência insuficiente de taxa acima de 5%"}</td></tr>; })}</tbody></table></div>
        <p className="section-prose reveal">Os p-valores foram recalculados dos registros reais, apesar de a contagem de falhas coincidir com a amostra simulada da S01. A diferença observada de 4,52 p.p. não basta, com α=5%, para afirmar que a taxa supera a meta. Não rejeitar H₀ também não demonstra que a meta foi cumprida.</p>
      </Chapter>

      <Chapter id="conclusao" number="07" title="Conclusão" subtitle="O que os experimentos e os dados reais permitem recomendar.">
        <div className="verdict reveal"><span className="verdict-symbol" aria-hidden="true">✳</span><div><span className="micro-label">RECOMENDAÇÃO DO ESTUDO</span><strong>Para falhas raras com amostra pequena, prefira o binomial exato.</strong><p>Ele respeitou o nível nominal neste cenário; para ganhar poder, colete mais execuções.</p></div></div>
        <div className="conclusion-grid reveal"><p>A previsão registrada antes da simulação se confirmou quanto ao <strong>controle do erro tipo I em amostra pequena</strong>: com n=42, o exato rejeitou {pct(nullByN[42].tests.binomial_exact.rejection_rate,2)} sob H₀, enquanto o Z rejeitou {pct(nullByN[42].tests.z.rejection_rate,2)}. O exato ficou abaixo de 5% pelos degraus da distribuição binomial; o menor poder em G4 é o custo desse conservadorismo.</p><p>Nos dados reais, p̂={pct(real.p_hat,2)} está acima da meta, mas nenhum teste rejeita H₀ a 5%. Sob o modelo iid Bernoulli, recomendamos o exato se a prioridade é não ultrapassar o erro tipo I nominal. Com amostra maior, o Z pode ser uma alternativa após avaliar a aproximação. Dependência temporal ou probabilidade de falha variável exigem rever o modelo.</p></div>
        <p className="limitations reveal"><strong>Limites do estudo.</strong> As 42 execuções vieram de uma janela temporal por conveniência; commits, reruns e infraestrutura podem criar dependência. A meta de 5% é pedagógica, não uma política declarada pelo projeto fonte. G3/G4 estudam tamanho amostral sob Bernoulli iid, sem simular esses vieses dos dados reais.</p>
      </Chapter>
      <footer className="footer"><span>LAB04 · TESTES DE HIPÓTESE POR DENTRO</span><span>Fonte, simulação e inferência documentadas no <a href={REPOSITORY} target="_blank" rel="noopener noreferrer">repositório ↗</a></span></footer>
    </main></div>
  </>;
}
