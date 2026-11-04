"""Integração visual com o contrato versionado, sem repetir os testes estatísticos."""

import json

import pytest
from streamlit.testing.v1 import AppTest

from dashboard.charts import ROOT, g1_histogram, g2_binomial, g2_z, load_contract


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


def test_streamlit_page_runs_offline_with_four_charts():
    page = AppTest.from_file(str(ROOT / "dashboard" / "app.py"), default_timeout=20).run()
    assert not page.exception
    assert len(page.get("plotly_chart")) == 4
    assert [heading.value for heading in page.header] == ["Cenário", "Os dados · G1", "Como os testes funcionam · G2"]
