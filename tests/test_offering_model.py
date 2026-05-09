from offering_app.models.offering import Offering


def test_compute_total_sums_all_amount_fields():
    offering = Offering(
        member_name="Ana",
        diezmo=10,
        ofrenda=5,
        primicias=2,
        pro_templo=1,
        ofrenda_misionera=3,
        ofrenda_pastoral=4,
    )

    total = offering.compute_total()

    assert total == 25
    assert offering.total == 25
