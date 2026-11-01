# Pytest Dependencies
from unittest.mock import Mock, call

import pytest

from refused_payments_report.io_utils.exceptions import LoadSources

# Self Dependencies
from refused_payments_report.pipeline.pipeline import Pipeline


@pytest.fixture
def pipeline_configs():
    return {
        "paths": {
            "pedidos": "pedidos.csv.gz",
            "pagamentos": "pagamentos.json.gz",
            "output": "relatorio",
        },
        "file_options": {
            "pedidos_csv": {"compression": "gzip", "header": True, "sep": ";"},
            "pagamentos_json": {"compression": "gzip"},
        },
        "transformer": {"target_year": 2025},
    }


class FakeDataFrame:
    """
    Simula apenas a interface transform() do Spark DataFrame.

    Não executa operações Spark. Encaminha as chamadas
    para os métodos simulados e permite verificar a
    orquestração feita pelo Pipeline.
    """

    def transform(self, function, *args, **kwargs):
        function(self, *args, **kwargs)
        return self


def test_pipeline_calls_components_in_correct_order(pipeline_configs):
    """
    Valida a chamada dos componentes no pipeline
    """
    data_handler = Mock()
    transformer = Mock()

    orders_df = FakeDataFrame()
    payments_df = FakeDataFrame()

    data_handler.load_pedidos.return_value = orders_df
    data_handler.load_pagamentos.return_value = payments_df

    pipeline = Pipeline(data_handler=data_handler, data_transformer=transformer)

    pipeline.run(pipeline_configs)

    data_handler.load_pedidos.assert_called_once_with(
        path="pedidos.csv.gz", header=True, sep=";", compression="gzip"
    )

    data_handler.load_pagamentos.assert_called_once_with(
        path="pagamentos.json.gz", compression="gzip"
    )

    assert transformer.mock_calls == [
        call.add_total_value(orders_df),
        call.year_orders_filter(orders_df, target_year=2025),
        call.false_negative_payments_filter(payments_df),
        call.join_information(orders_df, payments_df=payments_df),
        call.priorization(orders_df),
    ]

    data_handler.apply_output_schema.assert_called_once_with(orders_df)
    data_handler.write_parquet.assert_called_once_with(df=orders_df, path="relatorio")


def test_pipeline_propagates_loading_error(pipeline_configs):
    """
    Simulando o erro de carga dos pedidos no pipeline e a propagação do mesmo.
    """
    data_handler = Mock()
    transformer = Mock()

    data_handler.load_pedidos.side_effect = LoadSources("Falha ao carregar pedidos.")

    pipeline = Pipeline(data_handler=data_handler, data_transformer=transformer)

    with pytest.raises(LoadSources, match="Falha ao carregar pedidos"):
        pipeline.run(pipeline_configs)

    data_handler.load_pagamentos.assert_not_called()
    data_handler.write_parquet.assert_not_called()

    transformer.assert_not_called()
    assert transformer.mock_calls == []
