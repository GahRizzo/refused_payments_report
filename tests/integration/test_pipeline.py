
# Python Dependencies
import gzip
import json

# Pytest Dependencies
import pytest

# Self Dependencies
from refused_payments_report.io_utils.data_handler import DataHandler
from refused_payments_report.processing.transformations import Transformation
from refused_payments_report.processing.exceptions import BusinessRuleError
from refused_payments_report.pipeline.pipeline import Pipeline


def create_test_sources(tmp_path, invalid_quantity=False):
    """
    Cria as fontes temporárias para os testes de integração.
    """
    orders_path = tmp_path / "pedidos.csv.gz"
    payments_path = tmp_path / "pagamentos.json.gz"
    output_path = tmp_path / "output"

    orders = [
        ("P001", "Produto A", 60.0, 2,
         "2025-01-10 10:00:00", "SP", 1),
        ("P002", "Produto B", 40.0, 1,
         "2025-02-10 10:00:00", "SP", 2),
        ("P003", "Produto C", 30.0, 3,
         "2025-03-10 10:00:00", "RJ", 3),
        ("P004", "Produto D", 50.0, 2,
         "2024-04-10 10:00:00", "MG", 4),
        ("P005", "Produto E", 50.0, 1,
         "2025-05-10 10:00:00", "SP", 5),
        ("P006", "Produto F", 60.0, 1,
         "2025-06-10 10:00:00", "SP", 6)
    ]

    if invalid_quantity:
        orders[0] = (
            "P001", "Produto A", 60.0, -2,
            "2025-01-10 10:00:00", "SP", 1
        )

    with gzip.open(orders_path, "wt", encoding="utf-8") as file:
        file.write(
            "id_pedido;produto;valor_unitario;quantidade;"
            "data_criacao;uf;id_cliente\n"
        )

        for order in orders:
            file.write(";".join(map(str, order)) + "\n")

    payments = [
        ("P001", "PIX", False, False),
        ("P002", "PIX", False, False),
        ("P003", "CARTAO", False, False),
        ("P004", "PIX", False, False),
        ("P005", "PIX", True, False),
        ("P006", "PIX", False, True)
    ]

    with gzip.open(payments_path, "wt", encoding="utf-8") as file:
        for order_id, method, status, fraud in payments:
            record = {
                "id_pedido": order_id,
                "forma_pagamento": method,
                "valor_pagamento": 100.0,
                "status": status,
                "data_processamento": "2025-07-01T12:00:00",
                "avaliacao_fraude": {
                    "fraude": fraud,
                    "score": 0.1
                }
            }

            file.write(json.dumps(record) + "\n")

    configs = {
        "paths": {
            "pedidos": str(orders_path),
            "pagamentos": str(payments_path),
            "output": str(output_path)
        },
        "file_options": {
            "pedidos_csv": {
                "compression": "gzip",
                "header": True,
                "sep": ";"
            },
            "pagamentos_json": {
                "compression": "gzip"
            }
        },
        "transformer": {
            "target_year": 2025
        }
    }

    return configs, output_path


def create_pipeline(spark):
    """Instancia o Pipeline com seus componentes reais."""
    return Pipeline(data_handler=DataHandler(spark), data_transformer=Transformation())


def test_pipeline_generates_correct_report(spark, tmp_path):
    """
    Valida o conteúdo gerado pelo pipeline.
    """
    configs, output_path = create_test_sources(tmp_path)

    pipeline = create_pipeline(spark)
    pipeline.run(configs)

    result = spark.read.parquet(str(output_path))

    actual = {
        (
            row.id_pedido,
            row.uf,
            row.forma_pagamento,
            row.valor_total
        )
        for row in result.collect()
    }

    assert actual == {
        ("P001", "SP", "PIX", 120.0),
        ("P002", "SP", "PIX", 40.0),
        ("P003", "RJ", "CARTAO", 90.0)
    }

    assert result.count() == 3

    assert result.columns == [
        "id_pedido",
        "uf",
        "forma_pagamento",
        "valor_total",
        "data_criacao"
    ]


def test_pipeline_rejects_invalid_orders_without_writing(spark, tmp_path):
    """
    Valida que dados inválidos interrompem o pipeline antes da escrita do relatório.
    """
    configs, output_path = create_test_sources(tmp_path, invalid_quantity=True)

    pipeline = create_pipeline(spark)

    with pytest.raises(BusinessRuleError, match="quantidade ou valor unitário inválidos"):
        pipeline.run(configs)

    assert not output_path.exists()
