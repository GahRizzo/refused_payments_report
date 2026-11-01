class ConfigException(Exception):
    """Exceção base para qualquer falha na camada de I/O."""


class ConfigError(ConfigException):
    """Configurações ausentes, inválidas ou inacessíveis."""
