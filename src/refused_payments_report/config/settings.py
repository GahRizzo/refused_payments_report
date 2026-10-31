# Pytho Dependencies
import yaml
import logging

# Spark Dependencies
from pyspark.errors import AnalysisException, PySparkException

# Self Dependencies
from io_utils.exceptions import LoadSources

logger = logging.getLogger(__name__)

class Configs:
    """
    Classe responsável por gerir a carga de configurações do Pipeline

    :Classes:
    load_config: Carrega o arquivo .yaml de configurações do pipeline
    print_config: Faz a exibição do arquivo YAML carregado.
    """

    def __init__(self, path: str = "./config/settings.yaml"):
        self.configs = self.load_config(path)

    @staticmethod
    def load_config(path: str) -> dict:
        """
        Carrega um arquivo de configuração YAML.

        :Parâmetro:
        path(str): Caminho ao qual o yaml de configurações está salvo

        :Retorno:
        YAML carregado como uma variáveil para o ambiente
        """

        try: 
            with open(path, "r", encoding="utf-8") as file:
                configs = yaml.safe_load(file) or {}
        
        except OSError as e:
            raise ConfigError(
                f"Não foi possível acessar o arquivo de configuração '{path}'"
            ) from e
        
        except yaml.YAMLError as e:
            raise ConfigError(
                f"YAML inválido no arquivo '{path}'"
            ) from e
        
        
        if not isinstance(configs, dict):
            raise ConfigError("O arquivo YAML deve conter um dicionário de configurações.")
        
        # Seções obrigatórias
        for section in ("spark","logging", "paths", "file_options", "transformer"):
            if not isinstance(configs.get(section), dict):
                raise ConfigError(f"Seção obrigatória ausente ou inválida: '{section}'")
        
        # Caminhos essenciais
        for key in ("pagamentos", "pedidos", "output"):

            value = configs["paths"].get(key)

            if not isinstance(value, str) or not value.strip():
                raise ConfigError(f"Caminho obrigatório ausente ou inválido: 'paths.{key}'")
        
        # Configurações de leitura de file_option
        file_options = configs["file_options"]
        for section in ("pagamentos_json", "pedidos_csv"):
            if not isinstance(file_options.get(section), dict):
                raise ConfigError(f"Configuração de leitura ausente: 'file_options.{section}'")

        ## Verificando configurações de pagamentos_json
        json_options = file_options["pagamentos_json"]
        if not isinstance(json_options.get("compression"), str):
            raise ConfigError("file_options.pagamentos_json.compression' deve ser uma string.")
        if not json_options.get("compression") == "gzip":
            raise ConfigError("'file_options.pagamentos_json.compression' aceita apenas o modelo de compressão 'gzip'.")
        
        ## Verificando configurações de pedidos_csv
        csv_options = file_options["pedidos_csv"]
        if not isinstance(csv_options.get("header"), bool):
            raise ConfigError("'file_options.pedidos_csv.header' deve ser booleano.")
        
        compression = csv_options.get("compression")
        if not isinstance(compression, str):
            raise ConfigError("file_options.pedidos_csv.compression' deve ser uma string.")
        if not compression == "gzip":
            raise ConfigError("'file_options.pedidos_csv.compression' aceita apenas o modelo de compressão 'gzip'.")

        separator = csv_options.get("sep")
        if not isinstance(separator, str) or not separator:
            raise ConfigError("'file_options.pedidos_csv.sep' deve ser uma string não vazia.")

        # Verificando configurações de transformer
        target_year = configs["transformer"].get("target_year")

        if type(target_year) is not int or target_year < 1:
            raise ConfigError("'transformer.target_year' deve ser um ano inteiro positivo.")

        return configs

    def __str__(self) -> str:
        """
        Representação legível das configurações.
        """
        return yaml.safe_dump(
            self.configs,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False
        )