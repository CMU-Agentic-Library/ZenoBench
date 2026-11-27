from benchmark.v6 import taxonomy as T


def test_every_layout_has_one_label_per_axis():
    rows = T.build()
    assert len(rows) == len({(r["task"], r["layout"]) for r in rows})
    for r in rows:
        assert r["strategy"] in T.STRATEGY
        assert (r["basis"] is None) == (r["strategy"] == "nominal")
        assert r["basis"] is None or r["basis"] in T.BASIS
        assert r["object_category"] in T.OBJ_CAT, r
        if r["category"] == "control":
            assert r["strategy"] == "nominal"
