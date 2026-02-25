# OpenOPC

`openopc` é um pacote Python para criar automaticamente uma estrutura **OPC UA** a partir de um arquivo **JSON**.

Ele usa `asyncua` para instanciar um servidor OPC UA real e montar os nós definidos no JSON.

## Recursos

- Leitura de especificação JSON.
- Criação de servidor OPC UA com endpoint e nome configuráveis.
- Criação recursiva de nós:
  - `folder`
  - `object`
  - `variable`
- Suporte a tipos de dados básicos (`boolean`, `int32`, `float`, `string`, etc.).

## Formato JSON esperado

```json
{
  "server": {
    "name": "OpenOPC Example Server",
    "endpoint": "opc.tcp://0.0.0.0:4840/openopc/example/",
    "namespace_uri": "http://openopc.example/manufatura"
  },
  "nodes": [
    {
      "type": "folder",
      "name": "Factory",
      "children": [
        {
          "type": "object",
          "name": "MachineA",
          "children": [
            {
              "type": "variable",
              "name": "Temperature",
              "datatype": "float",
              "value": 36.7,
              "writable": false
            }
          ]
        }
      ]
    }
  ]
}
```

## API principal

```python
from openopc import create_server_from_json

server = await create_server_from_json("caminho/para/estrutura.json")
```

Funções disponíveis:

- `load_json_spec(path)`
- `create_server_from_json(path)`
- `build_server_from_json(path)` (alias)
- `populate_from_dict(server, spec)`

## Como executar o exemplo

1. Instale as dependências:

```bash
pip install -e .
```

2. Execute o script de exemplo:

```bash
python examples/run_openopc_example.py
```

3. Conecte um cliente OPC UA ao endpoint:

```text
opc.tcp://0.0.0.0:4840/openopc/example/
```

## Arquivos de exemplo

- `examples/opc_structure_example.json`
- `examples/run_openopc_example.py`

## Observações

- Campos obrigatórios por nó:
  - `type`
  - `name`
- Para `variable`, também são obrigatórios:
  - `datatype`
  - `value` (recomendado)
- Para nós com filhos (`folder`/`object`), use `children` como lista.
