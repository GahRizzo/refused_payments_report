# Test Dependences
from unittest.mock import Mock
import pytest

# Self Dependences
from refused_payments_report import main as main_module


@pytest.fixture
def main_dependencies(monkeypatch):
    """
    Simula dependências externas para testar
    o ciclo de execução da aplicação.
    """
    configs = {
        "spark": {
            "app_name": "refused-payments-tests"
        }
    }

    mock_configs = Mock()
    mock_configs.configs = configs

    mock_spark = Mock()
    mock_pipeline = Mock()

    mock_logging_config = Mock()

    monkeypatch.setattr(main_module.LoggingConfig, "configure", mock_logging_config)

    monkeypatch.setattr(main_module, "Configs", Mock(return_value=mock_configs))

    mock_get_session = Mock(return_value=mock_spark)

    monkeypatch.setattr(main_module.SparkSessionManager, "get_spark_session", mock_get_session)
    monkeypatch.setattr(main_module, "DataHandler", Mock())
    monkeypatch.setattr(main_module, "Transformation", Mock())
    monkeypatch.setattr(main_module, "Pipeline", Mock(return_value=mock_pipeline))

    return {
        "configs": configs,
        "spark": mock_spark,
        "pipeline": mock_pipeline,
        "get_session": mock_get_session,
        "logging_config": mock_logging_config,
    }


def test_main_executes_pipeline_and_closes_spark(main_dependencies):
    """
    Validando a execução completa do módulo main.
    """
    result = main_module.main()

    assert result == 0

    main_dependencies["logging_config"].assert_called_once_with("./config/logging.yaml")
    main_dependencies["get_session"].assert_called_once_with(app_name="refused-payments-tests")
    main_dependencies["pipeline"].run.assert_called_once_with(configs=main_dependencies["configs"])
    main_dependencies["spark"].stop.assert_called_once()


def test_main_returns_error_and_closes_spark_on_pipeline_failure(main_dependencies):
    """
    Validando o retorno de erro do pipeline.
    """
    
    main_dependencies["pipeline"].run.side_effect = RuntimeError("Falha simulada durante o processamento.")
    result = main_module.main()

    assert result == 1

    main_dependencies["pipeline"].run.assert_called_once()
    main_dependencies["spark"].stop.assert_called_once()


def test_main_returns_error_when_spark_shutdown_fails(main_dependencies):
    """
    Validando o retorno de erro com uma falha pelo Spark.
    """
    
    main_dependencies["spark"].stop.side_effect = RuntimeError("Falha simulada ao encerrar Spark.")
    result = main_module.main()

    assert result == 1

    main_dependencies["pipeline"].run.assert_called_once()
    main_dependencies["spark"].stop.assert_called_once()