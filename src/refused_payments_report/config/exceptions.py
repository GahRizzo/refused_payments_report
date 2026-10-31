class ConfigException(Exception):
    """Exceção base para qualquer falha na camada de I/O."""
    pass

class ConfigError(ConfigException):
    """Configurações ausentes, inválidas ou inacessíveis."""
    pass