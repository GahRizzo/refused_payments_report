# Refused Payments Report

Pipeline de engenharia de dados desenvolvido em **Python e PySpark** para gerar um relatório de **pagamentos recusados sem indicação de fraude**, enriquecido com informações dos pedidos. Os dados são lidos de fontes CSV e JSON, transformados e gravados no formato **Parquet**.

## Objetivo

Identificar pagamentos com `status = false` e `avaliacao_fraude.fraude = false`, relacioná-los aos pedidos correspondentes e produzir um relatório com as principais informações organizada por estado, forma de pagamento e data de criação do pedido.

O projeto também contempla validações de qualidade dos dados, tratamento de exceções, logs configuráveis e testes automatizados.

## Tecnologias

- **Python 3.14+**
- **PySpark 4.2+** para processamento de dados
- **PyYAML** para leitura das configurações
- **uv** para gerenciamento do ambiente e dependências
- **pytest** e **pytest-cov** para testes e cobertura
- **Black** para formatação e **Ruff** para análise estática

As versões e dependências efetivas estão declaradas em [`pyproject.toml`](pyproject.toml) e [`uv.lock`](uv.lock).

## Funcionamento do pipeline

```text
CSV de pedidos (.csv.gz)       JSON de pagamentos (.json.gz)
          |                               |
          v                               v
   Leitura com schema              Leitura com schema
          |                               |
          v                               v
 Cálculo de valor_total       Filtro de pagamentos recusados
          |                    e não sinalizados como fraude
          v                               |
   Filtro pelo ano                        |
          |                               |
          +---------------+---------------+
                          |
                          v
                  Inner join por id_pedido
                          |
                          v
            Ordenação por UF, forma de pagamento
                   e data de criação
                          |
                          v
                Schema do relatório final
                          |
                          v
                 Escrita em Parquet
```

### Regras de negócio

1. Calcula `valor_total = valor_unitario * quantidade` para cada pedido.
2. Rejeita pedidos com quantidade nula ou menor ou igual a zero, ou valor unitário nulo, negativo ou `NaN`.
3. Considera somente pedidos do ano definido em `transformer.target_year`.
4. Seleciona pagamentos com `status = false` e `avaliacao_fraude.fraude = false`.
5. Verifica duplicidade de `id_pedido` nos conjuntos de pedidos e pagamentos antes da junção.
6. Une pedidos e pagamentos por `id_pedido` com **inner join**. Pagamentos sem pedido correspondente **não são incluídos** na saída. Esse comportamento não é tratado como erro.
7. Ordena o relatório por `uf`, `forma_pagamento` e `data_criacao` em ordem crescente.

> **Premissa de integridade:** a validação de duplicidades pressupõe que o identificador `id_pedido` seja único em cada fonte. Se o domínio admitir múltiplos pagamentos legítimos por pedido, essa regra precisará ser revista.

### Colunas do relatório

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id_pedido` | string | Identificador do pedido |
| `uf` | string | Unidade federativa (SP, RJ, etc.) |
| `forma_pagamento` | string | Forma de pagamento (PIX, CARTAO DE CREDITO, etc.) |
| `data_criacao` | timestamp | Data de criação do pedido |
| `valor_total` | double | Valor calculado do pedido |

## Estrutura do projeto

```text
refused_payments_report/
├── config/
│   ├── logging.yaml
│   └── settings.yaml
├── data/
│   ├── input/
│   │   ├── dataset-json-pagamentos/
│   │   └── datasets-csv-pedidos/
│   └── output/                    # Gerado na execução
├── src/
│   └── refused_payments_report/
│       ├── config/                # Configurações e logging
│       ├── io_utils/              # Leitura, schema e escrita
│       ├── pipeline/              # Orquestração
│       ├── processing/            # Transformações e regras de negócio
│       ├── session/               # SparkSession
│       └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── pyproject.toml
└── uv.lock
```

A pasta `data/output/` **não precisa existir no clone**: o Spark cria o destino quando grava o relatório. Os datasets de entrada devem estar presentes em `data/input/`, conforme os caminhos configurados no YAML.

## Pré-requisitos

- **Python 3.14 ou superior** (conforme `pyproject.toml`)
- **Java/JDK compatível com a versão de PySpark utilizada**, disponível no ambiente
- **uv** instalado
- Git, para clonar o repositório

> Execute os comandos a seguir **a partir da raiz do repositório**. Os caminhos dos arquivos de configuração e das fontes são relativos a esse diretório.

## Instalação

```bash
git clone https://github.com/GahRizzo/refused_payments_report.git

cd refused_payments_report

pip install uv # Caso não tenha instalado, caso sim, ignorar.

uv sync
```

O `uv sync` cria/sincroniza o ambiente virtual e instala o projeto com as dependências descritas no lockfile.

## Configuração

O arquivo [`config/settings.yaml`](config/settings.yaml) define o nome da sessão Spark, os caminhos de entrada e saída, o formato dos arquivos e o ano filtrado:

```yaml
spark:
  app_name: "refused-payments-report"

paths:
  pagamentos: "./data/input/dataset-json-pagamentos/data/pagamentos/"
  pedidos: "./data/input/datasets-csv-pedidos/data/pedidos/"
  output: "./data/output/refused_payments_report"

file_options:
  pagamentos_json:
    compression: "gzip"
  pedidos_csv:
    compression: "gzip"
    header: true
    sep: ";"

transformer:
  target_year: 2025
```

Altere `target_year` ou os caminhos conforme a necessidade. Para preservar a leitura das fontes, mantenha os formatos, o separador e as configurações de compressão coerentes com os arquivos disponíveis.

A configuração do logging fica separada em [`config/logging.yaml`](config/logging.yaml).

## Execução

Após instalar as dependências, execute:

```bash
uv run refused-payments-report
```

O comando acima requer este *entry point* configurado no `pyproject.toml`:

```toml
[project.scripts]
refused-payments-report = "refused_payments_report.main:cli"
```

A função `cli()` deve finalizar o processo com o código retornado por `main()` (por exemplo, usando `sys.exit(main())`).

**Alternativa de execução:** caso o *entry point* ainda não esteja configurado no checkout, utilize:

```bash
uv run python -m refused_payments_report.main
```

Ao final de uma execução bem-sucedida, o relatório é gravado no caminho definido em `paths.output`, por padrão:

```text
data/output/refused_payments_report/
```

O Spark gera um diretório contendo arquivos `part-*.parquet` e arquivos auxiliares. A escrita utiliza o modo **`overwrite`**: executar novamente no mesmo caminho substitui o conteúdo anterior.

## Testes e cobertura

O projeto utiliza testes **unitários** (incluindo mocks para orquestração) e **de integração** (com Spark real, arquivos temporários e validação do conteúdo gravado).

```bash
# Executar toda a suíte
uv run pytest tests/ -v

# Apenas unitários
uv run pytest tests/unit/ -v

# Apenas integração
uv run pytest tests/integration/ -v

# Cobertura, incluindo branches
uv run pytest tests/ --cov=refused_payments_report --cov-branch --cov-report=term-missing
```

O limite mínimo configurado no `pyproject.toml` é **80% de cobertura**. A meta de cobertura complementa, mas não substitui, a verificação de regras de negócio e cenários de falha.

## Qualidade do código

```bash
# Verificações sem alterar arquivos
uv run ruff check src/ tests/
uv run black --check src/ tests/

# Correções automáticas e formatação
uv run ruff check --fix src/ tests/
uv run black src/ tests/
```

Recomenda-se executar os testes novamente após alterações automáticas no código.

## Tratamento de falhas e logs

- Configurações inválidas são identificadas durante o carregamento do YAML.
- Falhas de leitura e escrita são encapsuladas em exceções específicas, preservando a exceção original quando aplicável.
- As transformações validam campos obrigatórios e regras de integridade antes de gerar o relatório.
- O `main.py` registra as falhas e encerra a sessão Spark quando ela foi iniciada.
- O nível de logs do Spark pode ser reduzido independentemente dos logs da aplicação.

## Observações e limitações

- Os caminhos definidos no YAML são relativos ao **diretório de execução**; execute o projeto pela raiz do repositório.
- O `inner join` elimina registros sem correspondência entre as fontes. Não há, nesta versão, uma verificação de pagamentos órfãos que interrompa a execução.
- A gravação em Parquet não garante a preservação da ordenação física na leitura posterior, mesmo que o DataFrame tenha sido ordenado antes da escrita.
- Os diretórios de saída são artefatos gerados e não precisam ser versionados. Recomenda-se ignorar `/data/output/` no `.gitignore`.

## Repositório

[GitHub — GahRizzo/refused_payments_report](https://github.com/GahRizzo/refused_payments_report)