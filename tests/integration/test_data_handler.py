# Pytest Dependencie
# Python Dependencies
import json
from datetime import datetime

import pytest

# Pyspark Dependencies
from pyspark.sql.types import (
    DoubleType,
    StringType,
    TimestampType,
)

# Self Dependencies
from refused_payments_report.io_utils.data_handler import DataHandler
from refused_payments_report.io_utils.exceptions import LoadSources


def test_load_pedidos_reads_csv_correctly(spark, tmp_path):
    """
    Valida leitura do CSV, separador, cabeçalho e tipos.
    """

    source = tmp_path / "pedidos.csv"
    source.write_text(
        "id_pedido;produto;valor_unitario;quantidade;"
        "data_criacao;uf;id_cliente\n"
        "P001;Notebook;2500.50;2;2025-01-10 10:00:00;SP;10\n"
        "P002;Mouse;50.00;3;2025-01-11 11:00:00;RJ;20\n",
        encoding="utf-8",
    )

    handler = DataHandler(spark)

    result = handler.load_pedidos(
        path=str(source), compression=None, header=True, sep=";"
    )

    rows = {row.id_pedido: row for row in result.collect()}

    assert len(rows) == 2
    assert rows["P001"].produto == "Notebook"
    assert rows["P001"].valor_unitario == 2500.50
    assert rows["P001"].quantidade == 2
    assert rows["P001"].uf == "SP"
    assert rows["P002"].id_cliente == 20
    assert isinstance(result.schema["data_criacao"].dataType, TimestampType)


def test_load_pagamentos_reads_nested_json(spark, tmp_path):
    """
    Valida campos financeiros e estrutura aninhada.
    """

    source = tmp_path / "pagamentos.json"

    records = [
        {
            "id_pedido": "P001",
            "forma_pagamento": "PIX",
            "valor_pagamento": 100.0,
            "status": False,
            "data_processamento": "2025-01-10T10:00:00",
            "avaliacao_fraude": {"fraude": False, "score": 0.15},
        },
        {
            "id_pedido": "P002",
            "forma_pagamento": "CARTAO",
            "valor_pagamento": 200.0,
            "status": True,
            "data_processamento": "2025-01-11T11:00:00",
            "avaliacao_fraude": {"fraude": True, "score": 0.95},
        },
    ]

    source.write_text(
        "\n".join(json.dumps(record) for record in records), encoding="utf-8"
    )

    handler = DataHandler(spark)

    result = handler.load_pagamentos(path=str(source), compression=None)

    rows = {row.id_pedido: row for row in result.collect()}

    assert len(rows) == 2
    assert rows["P001"].forma_pagamento == "PIX"
    assert rows["P001"].valor_pagamento == 100.0
    assert rows["P001"].status is False
    assert rows["P001"].avaliacao_fraude.fraude is False
    assert rows["P002"].avaliacao_fraude.score == 0.95
    assert isinstance(result.schema["valor_pagamento"].dataType, DoubleType)


def test_apply_output_schema_casts_and_orders_columns(spark):
    """
    Valida se o contrato de tipos e ordem do relatório está sendo respeitado.
    """

    df = spark.createDataFrame(
        [("2025-01-10 10:00:00", "100.50", "PIX", "SP", "P001")],
        ["data_criacao", "valor_total", "forma_pagamento", "uf", "id_pedido"],
    )

    handler = DataHandler(spark)
    result = handler.apply_output_schema(df)

    assert result.columns == [
        "id_pedido",
        "uf",
        "forma_pagamento",
        "data_criacao",
        "valor_total"
    ]

    assert isinstance(result.schema["id_pedido"].dataType, StringType)
    assert isinstance(result.schema["valor_total"].dataType, DoubleType)
    assert isinstance(result.schema["data_criacao"].dataType, TimestampType)

    row = result.first()

    assert row.id_pedido == "P001"
    assert row.valor_total == 100.50
    assert row.data_criacao == datetime(2025, 1, 10, 10, 0)


def test_write_parquet_preserves_data(spark, tmp_path):
    """
    Valida a escrita e a recuperação dos dados do relatório.
    """

    df = spark.createDataFrame(
        [("P001", "SP", "PIX", 100.0), ("P002", "RJ", "CARTAO", 250.0)],
        """
        id_pedido STRING,
        uf STRING,
        forma_pagamento STRING,
        valor_total DOUBLE
        """,
    )

    handler = DataHandler(spark)
    output_path = tmp_path / "relatorio"

    handler.write_parquet(df=df, path=str(output_path))

    recovered = spark.read.parquet(str(output_path))

    actual = {
        row.id_pedido: (row.uf, row.forma_pagamento, row.valor_total)
        for row in recovered.collect()
    }

    assert actual == {"P001": ("SP", "PIX", 100.0), "P002": ("RJ", "CARTAO", 250.0)}
    assert recovered.count() == 2


def test_load_pedidos_raises_load_sources_for_missing_file(spark, tmp_path):
    """
    Valida se path inexistente envia o erro esperado.
    """

    handler = DataHandler(spark)

    missing_path = tmp_path / "pedidos_inexistentes.csv"

    with pytest.raises(LoadSources) as error:
        handler.load_pedidos(
            path=str(missing_path), compression=None, header=True, sep=";"
        )

    assert "pedidos" in str(error.value).lower()
    assert error.value.__cause__ is not None
