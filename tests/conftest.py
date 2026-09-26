import pytest


@pytest.fixture(scope="session")
def cycle():
    """One full BGW-SYN-01 cycle, shared by the T03/T04 tests (~30 s)."""
    import time

    from twin import scenario_cycle
    t0 = time.time()
    res, df, summ = scenario_cycle.main(save=False)
    summ["wall_s"] = time.time() - t0
    return res, df, summ
