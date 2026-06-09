def test_base_con_has_orders(base_con):
    assert base_con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 6


def test_frame_has_six_rows(frame):
    assert len(frame) == 6
    assert set(frame["variant"]) == {"control", "treatment"}
