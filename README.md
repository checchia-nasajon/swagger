# Planejador de Rotas Nasajon
![banner](https://user-images.githubusercontent.com/2954659/132579084-0e3ccafc-d8c0-42f4-80d0-2145d0142ea7.png)
## Objetivo:

Construir uma API REST que recebe um conjunto de locais e um conjunto de veículos com as suas respectivas restrições e retorne uma rota viável e boa para atender as demandas. 

Encontrar a solução ótima é uma problema muito custoso, inviável para casos mais complexos. A API busca uma solução próxima da ótima dentro das restrições de recurso para a busca da solução.

## Manual técnico do código

### Estrutura de pastas e arquivos

O código está dividido em duas pastas importantes, a pasta `routing/` que contem a implementação da API e a pasta `test/` com a implementação dos testes

Dentro da pasta `routing/` temos as seguintes pastas e arquivos:

`routing/entities/` pasta com as entidades do sistema, responsável por armazenar e encapsular informações  
`routing/entities/location.py` informações sobre um local  
`routing/entities/vehicle.py` informações sobre um veículo  
`routing/entities/system_entities.py` informações do sistemas como locais, veículos e configurações  
`routing/entities/routing_solution.py` informações da solução encontrada pelo sistema  
`routing/entities/exception.py` exceptions do sistemas


`routing/services` pasta com os serviços do sistema.  
`routing/services/locations.py` serviço responsável pelos locais e suas lógicas. Esse serviço conhece como criar uma cópia de um depósito, como permitir múltiplas visitas de um carro ao depósito, como encontrar um depósito etc  
`routing/services/vehicles.py` serviço responsável pelos veículos e seus lógicas. Esse serviço conhece qual a maior carga do conjunto de veículos e quais veículos são acessíveis em um local  
`routing/services/input_parser.py` serviço responsável em construir as entidades de entrada para o sistema a partir do JSON no corpo da mensagem HTTP  
`routing/services/routing.py` serviço responsável por montar o problema no otimizador  
`routing/services/ortools.py` serviço responsável em fazer as chamadas para a biblioteca/solucionador ORTOOLS  
`routing/services/penalty.py` implementação das funções de penalidade que podem ser utilizadas no sistema  
`routing/services/solution_verifier.py` serviço responsável em verificar se a solução encontrada é viável  
`routing/services/exception.py` construtor/acumulador de exceptions  
`routing/services/logging.py` logging

`test/` pasta com os testes para as entidades e arquivos descritos acima

### Bibliotecas utilizadas

`ortools` biblioteca de otimização  
`python-intervals` biblioteca para fazer operação de conjuntos  
`flask-restful` biblioteca para criar a API REST, baseado em flask  
`gunicorn` servidor http

### Como montar o ambiente

O repositório tem um arquivo Makefile com o código para subir a aplicação usando docker.  
Para subir o servidor http `make infra`

### Como executar os testes
Antes de executar os teste é necessário instalar as dependência especificas dos testes `requirements_for_testing.txt`
O repositório tem um arquivo Makefile com o código para execução dos teste.  
Para executar os testes `make test` para os testes rápidos ou `make test_slow` para executar também os testes que são mais lentos, como testes que vão executar o otimizador e podem demorar.

### Documentação Open API
A documentação está no caminho /apidocs, se estiver executando pelo docker-compose localmente, está em http://localhost:5000/apidocs/
