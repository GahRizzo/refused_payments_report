# Pytest Dependencie
# Python Dependencies
from datetime import datetime

import pytest

from refused_payments_report.processing.exceptions import BusinessRuleError

# Self Dependencies
from refused_payments_report.processing.transformations import Transformation


def test_add_total_value_calculates_correct_amount(spark):
    """
    Teste para validar o cálculo do valor total, multiplicando pedidos por quantidade.
    """

    df = spark.createDataFrame(
        [
            (1, 2, 25.0),
            (2, 3, 10.0),
        ],
        ["id_pedido", "quantidade", "valor_unitario"],
    )

    result = Transformation().add_total_value(df)

    actual = {row["id_pedido"]: row["valor_total"] for row in result.collect()}

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
    ],
)
def test_add_total_value_rejects_invalid_values(spark, quantity, unit_price):
    """
    Teste para validar o formato esperado para os dados de quantidade e preço unitário.
    """
    df = spark.createDataFrame(
        [(quantity, unit_price)], "quantidade LONG, valor_unitario DOUBLE"
    )

    with pytest.raises(BusinessRuleError):
        Transformation().add_total_value(df)


def test_year_orders_filter_keeps_only_target_year(spark):
    """
    Teste para validar se o filtro de ano dos pedidos está funcionando corretamente.
    """
    df = spark.createDataFrame(
        [
            ("P001", datetime(2025, 1, 10)),
            ("P002", datetime(2024, 12, 31)),
            ("P003", datetime(2025, 8, 20)),
        ],
        "id_pedido STRING, data_criacao TIMESTAMP",
    )

    result = Transformation().year_orders_filter(df, target_year=2025)

    ids = {row.id_pedido for row in result.collect()}

    assert ids == {"P001", "P003"}


@pytest.mark.parametrize("invalid_year", [0, -1, "2025", None])
def test_year_orders_filter_rejects_invalid_year(spark, invalid_year):
    """
    Teste para validar se o filtro de orders rejeita dados inválidos.
    """
    df = spark.createDataFrame(
        [("P001", datetime(2025, 1, 10))], "id_pedido STRING, data_criacao TIMESTAMP"
    )

    with pytest.raises(BusinessRuleError):
        Transformation().year_orders_filter(df, target_year=invalid_year)


def test_false_negative_filter_keeps_only_expected_payments(spark):
    """
    Teste para validar se o filtro de pedidos com status 'false' e avaliação de fraude também 'false'.
    """
    df = spark.createDataFrame(
        [
            ("P001", False, (False,)),
            ("P002", False, (True,)),
            ("P003", True, (False,)),
            ("P004", True, (True,)),
        ],
        """
        id_pedido STRING,
        status BOOLEAN,
        avaliacao_fraude STRUCT<fraude: BOOLEAN>
        """,
    )

    result = Transformation().false_negative_payments_filter(df)

    assert [row.id_pedido for row in result.collect()] == ["P001"]


def test_join_information_preserves_correct_financial_values(spark):
    """
    Teste para validar se o join entre o dataset de pagamentos e pedidos está sendo efetuado corretamente.
    """
    orders = spark.createDataFrame(
        [
            ("P001", "SP", 100.0, datetime(2025, 1, 10)),
            ("P002", "RJ", 250.0, datetime(2025, 2, 15)),
        ],
        """
        id_pedido STRING,
        uf STRING,
        valor_total DOUBLE,
        data_criacao TIMESTAMP
        """,
    )

    payments = spark.createDataFrame(
        [
            ("P001", "PIX"),
            ("P002", "CARTAO"),
        ],
        "id_pedido STRING, forma_pagamento STRING",
    )

    result = Transformation().join_information(orders, payments)

    actual = {
        row.id_pedido: (row.uf, row.forma_pagamento, row.valor_total)
        for row in result.collect()
    }

    assert actual == {
        "P001": ("SP", "PIX", 100.0),
        "P002": ("RJ", "CARTAO", 250.0),
    }

    assert result.count() == 2


def test_join_information_rejects_duplicate_orders(spark):
    """
    Teste para validar se a existência de id_pedidos duplicados será rejeitada pela aplicação.
    """
    orders = spark.createDataFrame(
        [
            ("P001", "SP", 100.0, datetime(2025, 1, 10)),
            ("P001", "SP", 100.0, datetime(2025, 1, 10)),
        ],
        """
        id_pedido STRING,
        uf STRING,
        valor_total DOUBLE,
        data_criacao TIMESTAMP
        """,
    )

    payments = spark.createDataFrame(
        [("P001", "PIX")], "id_pedido STRING, forma_pagamento STRING"
    )

    with pytest.raises(BusinessRuleError, match="duplicado"):
        Transformation().join_information(orders, payments)


def test_join_information_rejects_duplicate_payments(spark):
    """
    Teste para validar se a existência de pagamentos com id_pedido duplicados será rejeitada pela aplicação.
    """
    orders = spark.createDataFrame(
        [
            ("P001", "SP", 100.0, datetime(2025, 1, 10)),
        ],
        """
        id_pedido STRING,
        uf STRING,
        valor_total DOUBLE,
        data_criacao TIMESTAMP
        """,
    )

    payments = spark.createDataFrame(
        [
            ("P001", "PIX"),
            ("P001", "CARTAO"),
        ],
        "id_pedido STRING, forma_pagamento STRING",
    )

    with pytest.raises(BusinessRuleError, match="duplicado"):
        Transformation().join_information(orders, payments)


def test_priorization_orders_by_business_criteria(spark):
    """
    Teste se o processo de ordenação do dataframe está sendo respeitado.
    """
    df = spark.createDataFrame(
        [
            ("SP", "PIX", datetime(2025, 1, 12, 17, 10, 0),100.0),
            ("SP", "PIX", datetime(2025, 1, 12, 13, 4, 0),100.0),
            ("RJ", "PIX", datetime(2025, 2, 10, 13, 4, 0),200.0),
            ("SP", "PIX", datetime(2025, 3, 25, 13, 4, 0),300.0),
            ("SP", "CARTAO", datetime(2025, 2, 5, 13, 4, 0),150.0)
        ],
        "uf STRING, forma_pagamento STRING, data_criacao TIMESTAMP, valor_total DOUBLE",
    )

    result = Transformation().priorization(df)

    actual = [
        (row.uf, row.forma_pagamento, row.data_criacao, row.valor_total) for row in result.collect()
    ]

    assert actual == [
        ("RJ", "PIX", datetime(2025, 2, 10, 13, 4, 0),200.0),
        ("SP", "CARTAO", datetime(2025, 2, 5, 13, 4, 0),150.0),
        ("SP", "PIX", datetime(2025, 1, 12, 13, 4, 0),100.0),
        ("SP", "PIX", datetime(2025, 1, 12, 17, 10, 0),100.0),
        ("SP", "PIX", datetime(2025, 3, 25, 13, 4, 0),300.0)
    ]
