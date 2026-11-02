# Third Dependencies
from copy import deepcopy
import pytest
import yaml

# Self Dependences
from refused_payments_report.config.settings import Configs
from refused_payments_report.config.exceptions import ConfigError

@pytest.fixture
def valid_config():
    """
    Configuração mínima válida conforme o contrato da aplicação.
    """
    return {
        "spark": {"app_name": "refused-payments-tests"},
        "paths": {
            "pagamentos": "./data/pagamentos",
            "pedidos": "./data/pedidos",
            "output": "./data/output",
        },
        "file_options": {
            "pagamentos_json": {"compression": "gzip"},
            "pedidos_csv": {"compression": "gzip", "header": True, "sep": ";"},
        },
        "transformer": {"target_year": 2025},
    }


def save_config(tmp_path, config):
    """
    Grava um YAML temporário para os testes.
    """

    config_path = tmp_path / "settings.yaml"

    config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")

    return str(config_path)


def test_load_config_returns_valid_configuration(tmp_path, valid_config):
    "Validando o retorno das configurações"

    path = save_config(tmp_path, valid_config)
    result = Configs(path)

    assert result.configs == valid_config
    assert result.configs["transformer"]["target_year"] == 2025


@pytest.mark.parametrize("section", ["spark", "paths", "file_options", "transformer"])
def test_load_config_rejects_missing_required_section(tmp_path, valid_config, section):
    """
    Valida o compartamento de uma sessão chave faltante nas configurações.
    """
    config = deepcopy(valid_config)
    del config[section]

    path = save_config(tmp_path, config)

    with pytest.raises(ConfigError, match="Seção obrigatória"):
        Configs(path)


@pytest.mark.parametrize("field", ["pagamentos", "pedidos", "output"])
def test_load_config_rejects_empty_required_path(tmp_path, valid_config, field):
    """
    Valida o comportamento de rejeição de paths vazios.
    """
    config = deepcopy(valid_config)
    config["paths"][field] = ""

    path = save_config(tmp_path, config)

    with pytest.raises(ConfigError, match="Caminho obrigatório"):
        Configs(path)


@pytest.mark.parametrize("file_type", ["pagamentos_json", "pedidos_csv"])
def test_load_config_rejects_unsupported_compression(tmp_path, valid_config, file_type):
    """
    Valida a rejeição de compressões não suportadas.
    """
    config = deepcopy(valid_config)
    config["file_options"][file_type]["compression"] = "zip"

    path = save_config(tmp_path, config)

    with pytest.raises(ConfigError, match="gzip"):
        Configs(path)


@pytest.mark.parametrize("invalid_header", ["True", 1, None])
def test_load_config_rejects_non_boolean_header(tmp_path, valid_config, invalid_header):
    """
    Valida a rejeição de header não booleanos.
    """
    config = deepcopy(valid_config)
    config["file_options"]["pedidos_csv"]["header"] = invalid_header

    path = save_config(tmp_path, config)

    with pytest.raises(ConfigError, match="deve ser booleano"):
        Configs(path)


def test_load_config_rejects_empty_separator(tmp_path, valid_config):
    """
    Valida a rejeição de separadores passados como valores vazios.
    """
    config = deepcopy(valid_config)
    config["file_options"]["pedidos_csv"]["sep"] = ""

    path = save_config(tmp_path, config)

    with pytest.raises(ConfigError, match="string não vazia"):
        Configs(path)


@pytest.mark.parametrize("invalid_year", [0, -1, "2025", None, True])
def test_load_config_rejects_invalid_target_year(tmp_path, valid_config, invalid_year):
    """
    Valida a inserção de anos com formato inválido.
    """
    config = deepcopy(valid_config)
    config["transformer"]["target_year"] = invalid_year

    path = save_config(tmp_path, config)

    with pytest.raises(ConfigError, match="ano inteiro positivo"):
        Configs(path)


def test_load_config_rejects_malformed_yaml(tmp_path):
    """
    Valida a carga de um yaml mal formado.
    """
    path = tmp_path / "invalid.yaml"
    path.write_text("spark: [invalid", encoding="utf-8")

    with pytest.raises(ConfigError, match="YAML inválido") as error:
        Configs(str(path))

    assert isinstance(error.value.__cause__, yaml.YAMLError)


def test_load_config_rejects_missing_file(tmp_path):
    """
    Valida o comportamento quando o yaml não existe.
    """
    path = tmp_path / "missing.yaml"

    with pytest.raises(ConfigError, match="Não foi possível acessar") as error:
        Configs(str(path))

    assert isinstance(error.value.__cause__, OSError)
