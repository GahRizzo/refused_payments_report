# Python dependencies
import logging
import logging.config
import yaml
from pathlib import Path


class LoggingConfig:
    """
    Classe responsável pela configuração de logging da aplicação.

    :Métodos:
        configure: Aplica as configurações de logging do YAML.
    """

    @staticmethod
    def configure(path: str = "./config/logging.yaml") -> None:
        """
        Aplica a configuração de logging definida no YAML.

        :Parmâmetros:
        path (str): Caminho onde o arquivo .yaml com as configurações do logger está armazenado.
        """

        try:
            with Path(path).open("r", encoding="utf-8") as file:
                config = yaml.safe_load(file)

            if not isinstance(config, dict):
                raise ValueError("O arquivo de logging deve conter um dicionário.")
            
            logging.config.dictConfig(config)

        except (OSError, yaml.YAMLError, ValueError) as e:
            raise RuntimeError(f"Falha ao configurar logging a partir de '{path}'") from e