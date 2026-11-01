# Pytest Dependences
from unittest.mock import Mock

# Self Dependences
from refused_payments_report.session import spark_session


def test_spark_session_manager_builds_session(monkeypatch):
    """
    Validando a construção da spark sessions.
    """

    builder = Mock()
    session = Mock(name="spark_session")

    builder.appName.return_value = builder
    builder.master.return_value = builder
    builder.getOrCreate.return_value = session

    monkeypatch.setattr(spark_session.SparkSession, "builder", builder)

    result = spark_session.SparkSessionManager.get_spark_session(
        app_name="refused-payments-tests"
    )

    builder.appName.assert_called_once_with("refused-payments-tests")
    builder.master.assert_called_once_with("local[*]")
    builder.getOrCreate.assert_called_once_with()

    assert result is session
