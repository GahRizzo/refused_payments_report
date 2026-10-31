import yaml

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
        with open(path, "r", encoding="utf-8") as file:
            configs = yaml.safe_load(file) or {}

        if not isinstance(configs, dict):
            raise ValueError("O arquivo YAML deve conter um dicionário.")

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