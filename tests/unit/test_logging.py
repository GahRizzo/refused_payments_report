## Third Dependences
import logging.config
import yaml

# Test Dependences
import pytest
from unittest.mock import Mock

## Self Dependences
from refused_payments_report.config.logging import LoggingConfig


def test_logging_config_applies_valid_configuration(tmp_path, monkeypatch):
    """
    Validando a leitura do arquivo YAML e transporte das informações para o dictConfig.
    """

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "root": {
            "level": "INFO",
            "handlers": []
        }
    }

    path = tmp_path / "logging.yaml"
    path.write_text(
        yaml.safe_dump(config),
        encoding="utf-8"
    )

    mock_dict_config = Mock()
    
    monkeypatch.setattr(
        logging.config,
        "dictConfig",
        mock_dict_config
    )

    LoggingConfig.configure(str(path))

    mock_dict_config.assert_called_once_with(config)


@pytest.mark.parametrize(
    "content,expected_cause",
    [
        ("[invalid", yaml.YAMLError),
        ("- item1\n- item2", ValueError),
    ]
)
def test_logging_config_rejects_invalid_content(tmp_path, content, expected_cause):
    """
    Validando se um arquivo inválido recebe o erro correto.
    """

    path = tmp_path / "logging.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(RuntimeError) as error:
        LoggingConfig.configure(str(path))

    assert isinstance(
        error.value.__cause__,
        expected_cause
    )


def test_logging_config_rejects_missing_file(tmp_path):
    """
    Validando se um arquivo inexistente retornará erro.
    """
    
    path = tmp_path / "missing.yaml"

    with pytest.raises(RuntimeError) as error:
        LoggingConfig.configure(str(path))

    assert isinstance(
        error.value.__cause__,
        FileNotFoundError
    )
