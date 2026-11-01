# Pytest Dependencie
import pytest

# Self Dependencies
from refused_payments_report.processing.transformations import Transformation
from refused_payments_report.processing.exceptions import BusinessRuleError


def test_add_total_value_calculates_correct_amount(spark):
    """
    Teste do cálculo do valor total, multiplicando pedidos por quantidade.
    """
    
    df = spark.createDataFrame(
        [
            (1, 2, 25.0),
            (2, 3, 10.0),
        ],
        ["id_pedido", "quantidade", "valor_unitario"]
    )

    result = Transformation().add_total_value(df)

    actual = {
        row["id_pedido"]: row["valor_total"]
        for row in result.collect()
    }

    assert actual == {
        1: 50.0,
        2: 30.0,
    }


@pytest.mark.parametrize(
    "quantity, unit_price",
    [
        (-1, 10.0),
        (0, 10.0),
        (2, -10.0),
        (2, None),
        (2, float("nan")),
    ]
)

def test_add_total_value_rejects_invalid_values(spark, quantity, unit_price):
    """
    Testando formato esperado para os dados de quantidade e preço unitário.
    """
    df = spark.createDataFrame(
        [(quantity, unit_price)],
        "quantidade LONG, valor_unitario DOUBLE"
    )

    with pytest.raises(BusinessRuleError):
        Transformation().add_total_value(df)