import logging
import logging.config


class LoggingConfig:
    """
    Classe responsável pela configuração de logging da aplicação.

    :Métodos:
        configure: Aplica as configurações de logging do YAML.
    """

    @staticmethod
    def configure(config_logging: dict) -> None:
        """
        Aplica a configuração de logging definida no YAML.

        :Parmâmetros:
        config_logging (dict): Dicionário gerado a partir do arquivo settings.yaml com as configurações do logger.
        """
        logging.config.dictConfig(config_logging)

        logger = logging.getLogger(__name__)
        logger.info("Logging configurado com sucesso via YAML.")