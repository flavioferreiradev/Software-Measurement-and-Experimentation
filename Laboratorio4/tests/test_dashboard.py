"""Integração visual com o contrato versionado, sem repetir os testes estatísticos."""

import json
import subprocess
import sys

import pytest
from streamlit.testing.v1 import AppTest

from dashboard.charts import (ROOT, TEAL, VIOLET, g1_histogram, g2_binomial, g2_z,
                              g3_type_i, g4_power, load_contract, load_s02_contract, selected_rows)
from dashboard.real_analysis import analyze_real


def test_dashboard_uses_versioned_samples_and_reference_regions():
    payload = load_contract()
    assert len(payload["g1"]["real"]["values"]) == 42
    assert len(payload["g1"]["simulated"]["values"]) == 42
    assert sum(payload["g1"]["real"]["values"]) == 4
    assert sum(payload["g1"]["simulated"]["values"]) == 4

    for group in ("real", "simulated"):
        histogram = g1_histogram(payload, group).data[0]
        assert list(histogram.x) == payload["g1"][group]["values"]
        assert histogram.xbins.start == payload["g1"]["bin_edges"][0]
        assert histogram.xbins.end == payload["g1"]["bin_edges"][-1]

    z = payload["g2"]["z"]
    z_figure = g2_z(payload)
    assert z_figure.data[0].x[0] == z["observed"]
    assert z_figure.data[1].x[0] == z["critical_value"]
    assert list(z_figure.data[2].y) == z["pdf"]

    exact = payload["g2"]["binomial_exact"]
    exact_figure = g2_binomial(payload)
    assert list(exact_figure.data[0].x) == exact["k_support"]
    assert list(exact_figure.data[0].y) == exact["pmf"]
    assert list(exact_figure.data[1].x) == [k for k, use in zip(exact["k_support"], exact["p_value_mask"]) if use]
    assert list(exact_figure.data[2].x) == [k for k, use in zip(exact["k_support"], exact["rejection_mask"]) if use]
    assert exact_figure.data[1].x[0] == exact["observed_k"]
    assert exact_figure.data[2].x[0] == exact["critical_k"]


def test_dashboard_rejects_incompatible_contract(tmp_path):
    path = tmp_path / "demo_s01.json"
    path.write_text(json.dumps({"schema_version": "2.0.0"}), encoding="utf-8")
    with pytest.raises(ValueError, match="v1.0.0"):
        load_contract(path)


def test_s02_visuals_use_the_exact_versioned_rows_and_nominal_reference():
    payload = load_s02_contract()
    rows = selected_rows(payload, "g3")
    figure = g3_type_i(payload)
    assert len(figure.data) == 2
    assert list(figure.data[0].y) == [row["tests"]["z"]["rejection_rate"] for row in rows]
    assert list(figure.data[1].y) == [row["tests"]["binomial_exact"]["rejection_rate"] for row in rows]
    assert figure.layout.shapes[0].y0 == payload["g3"]["nominal_rate"]
    assert figure.data[0].marker.color == TEAL
    assert figure.data[1].marker.color == VIOLET

    curves = g4_power(payload)
    assert len(curves.data) == 4
    assert {trace.name for trace in curves.data} == {
        "Z · n=200", "Binomial exato · n=200", "Z · n=42", "Binomial exato · n=42"}
    for scenario, z_curve, exact_curve in zip(payload["scenarios"], curves.data[::2], curves.data[1::2]):
        subset = sorted((row for row in selected_rows(payload, "g4")
                         if row["scenario_id"] == scenario["id"]), key=lambda row: row["delta"])
        assert list(z_curve.x) == [100 * row["delta"] for row in subset]
        assert list(z_curve.y) == [row["tests"]["z"]["rejection_rate"] for row in subset]
        assert list(exact_curve.y) == [row["tests"]["binomial_exact"]["rejection_rate"] for row in subset]
        assert z_curve.line.color == TEAL
        assert exact_curve.line.color == VIOLET


def test_real_inference_comes_from_validated_csv():
    result = analyze_real()
    assert (result["n"], result["k"]) == (42, 4)
    assert result["effect_difference"] == pytest.approx(4 / 42 - 0.05)
    assert result["tests"]["z"]["p_value"] == pytest.approx(0.089282682, abs=1e-8)
    assert result["tests"]["binomial_exact"]["p_value"] == pytest.approx(0.156892615, abs=1e-8)
    assert all(not test["reject_h0"] for test in result["tests"].values())


def test_dashboard_rejects_broken_s02_contract(tmp_path):
    path = tmp_path / "experiments_s02.json"
    path.write_text(json.dumps({"schema_version": "2.0.0"}), encoding="utf-8")
    with pytest.raises(ValueError, match="G3/G4 v1.0.0"):
        load_s02_contract(path)
    path.write_text(json.dumps({"schema_version": "1.0.0", "protocol": {"p0": 0.05}}), encoding="utf-8")
    with pytest.raises(ValueError, match="incompleto"):
        load_s02_contract(path)


def test_streamlit_page_runs_offline_with_all_sections():
    page = AppTest.from_file(str(ROOT / "dashboard" / "app.py"), default_timeout=20).run()
    assert not page.exception
    assert len(page.get("plotly_chart")) == 6
    assert [heading.value for heading in page.header] == [
        "Cenário", "Os dados · G1", "Como os testes funcionam · G2",
        "Erro tipo I · G3", "Poder · G4", "Dados reais", "Conclusão"]
    assert len(page.dataframe) == 1


def test_interactive_explorer_switches_between_null_error_and_power():
    page = AppTest.from_file(str(ROOT / "dashboard" / "app.py"), default_timeout=20).run()
    page.select_slider[0].set_value(0.05).run()
    null_card = next(item.value for item in page.markdown if 'class="live-comparison"' in item.value)
    assert "ERRO TIPO I · n=42" in null_card
    assert "5,77%" in null_card and "1,95%" in null_card

    page.radio[0].set_value(200).run()
    page.select_slider[0].set_value(0.10).run()
    power_card = next(item.value for item in page.markdown if 'class="live-comparison"' in item.value)
    assert "PODER ESTATÍSTICO · n=200" in power_card
    assert power_card.count("85,58%") == 2


def test_one_command_reproduces_full_lab_without_changing_official_snapshots(tmp_path):
    official = [ROOT / "results" / name for name in (
        "demo_s01.json", "simulated_sample.csv", "demo_interpretation.md",
        "experiments_s02.json", "experiments_s02.csv", "experiments_s02_summary.md")]
    before = {path: path.read_bytes() for path in official}
    output = tmp_path / "full"
    run = subprocess.run([sys.executable, "-m", "src.run_all", "--output", str(output)],
                         cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    assert (output / "s01/demo_s01.json").exists()
    assert (output / "s02/experiments_s02.json").exists()
    real = json.loads((output / "real_analysis.json").read_text(encoding="utf-8"))
    assert (real["result"]["n"], real["result"]["k"]) == (42, 4)
    assert {path: path.read_bytes() for path in official} == before
