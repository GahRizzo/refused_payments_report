import yaml

def load_config(path: str = "./config/settings.yaml") -> dict:
    """Carrega um arquivo de configuração YAML."""
    with open(path, 'r') as file:
        return yaml.safe_load(file)