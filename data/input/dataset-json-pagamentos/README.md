# Dataset de pagamentos de pedidos
Author: Prof. Barbosa  
Contact: infobarbosa@gmail.com  
Github: [infobarbosa](https://github.com/infobarbosa)

- **Formato**: JSON
- **Nomenclatura do arquivo**: `pagamentos-YYYY-MM-DD.json.gz`
- **Estrutura**:

 | Atributo           | Tipo      | Obs                                                            | 
 | ---                | ---       | ---                                                            |
 | ID_PEDIDO          | UUID      | O identificador da pessoa                                      | 
 | FORMA_PAGAMENTO    | float     | A forma de pagamento (Pix, Boleto ou Cartão de Crédito)        | 
 | VALOR_PAGAMENTO    | float     | O valor do pagamento                                           | 
 | STATUS             | boolean   | O status de aprovação do pagamento (true/false)                | 
 | DATA_PROCESSAMENTO | date      | A data de processamento do pagamento. Ex.: 2024-01-01T02:55:59 | 
 | AVALIACAO_FRAUDE   | object    | Um objeto json com os seguintes atributos:                     |
 |                    |           | - O status de fraude (true/false)                              | 
 |                    |           | - O score de potencial de fraude (float)                       | 


#### Sample de pagamento
1. Pagamento aprovado (status=true) e conclusão de fraude de que É legítimo (fraude=false)
```json
 {"id_pedido": "9fc9c6b8-6dda-44c9-a780-dbfa6e394a84", "forma_pagamento": "CARTAO_CREDITO", "valor_pagamento": 1800, "status": true, "avaliacao_fraude": {"fraude": false, "score": 0.10}}
```
2. Pagamento recusado (status=false) e conclusão de fraude de que NAO É legítimo (fraude=false)
```json
{"id_pedido": "3b831b7e-7aa3-41aa-b5b2-5bdcdcfef19e", "forma_pagamento": "PIX", "valor_pagamento": 1500, "status": false, "avaliacao_fraude": {"fraude": true, "score": 0.99}}
```
3. Pagamento recusado (status=false) e conclusão de fraude de que É legítimo (fraude=false)
```json
{"id_pedido": "81024c98-bc43-4844-b46d-ea26d009c1b7", "forma_pagamento": "BOLETO", "valor_pagamento": 1500, "status": false, "avaliacao_fraude": {"fraude": false, "score": 0.20}}
```