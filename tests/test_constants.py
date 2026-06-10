from src import constants as c


def test_seed_is_42():
    assert c.SEED == 42


def test_simulated_effect_labeled_and_positive():
    assert c.SIMULATED_EFFECT == 0.05


def test_cohort_window_excludes_censored_tail():
    assert c.COHORT_START == "2017-01-01"
    assert c.COHORT_END_EXCLUSIVE == "2018-09-01"


def test_load_sql_reads_file(tmp_path, monkeypatch):
    import src._sql as sql_mod

    d = tmp_path / "sql" / "metrics"
    d.mkdir(parents=True)
    (d / "x.sql").write_text("SELECT 1")
    monkeypatch.setattr(sql_mod, "SQL_DIR", tmp_path / "sql")
    assert sql_mod.load_sql("metrics/x.sql") == "SELECT 1"
