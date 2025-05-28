# Sistema de Gerenciamento de Farmácia com Árvore AVL

Este projeto implementa um sistema de gerenciamento de medicamentos para farmácias utilizando uma estrutura de dados Árvore AVL para armazenamento eficiente e operações rápidas de busca, inserção e remoção de medicamentos.

## Estrutura do Projeto

O projeto é composto por três componentes principais:

1. **sistema_farmacia_avl.py**: Implementação da estrutura de dados Árvore AVL e funcionalidades de gerenciamento.
2. **inserir_medicamentos.py**: Script para gerar e inserir medicamentos de teste em massa.
3. **app_farmacia.py**: Interface web interativa usando Streamlit.

## Requisitos

Para executar o projeto, você precisa ter Python 3.7+ instalado e as seguintes bibliotecas:

```bash
pip install sqlite3 pandas streamlit graphviz
```

Para visualização da árvore AVL no Streamlit, também é necessário instalar o Graphviz:

- **Linux**:

  ```bash
  sudo apt-get install graphviz
  ```

- **macOS**:

  ```bash
  brew install graphviz
  ```

- **Windows**:
  Faça o download e instale a partir de: https://graphviz.org/download/

## 1. Usando o sistema_farmacia_avl.py

Este arquivo contém a implementação da Árvore AVL e as funções para gerenciar medicamentos.

### Como importar e usar

```python
from sistema_farmacia_avl import ArvoreAVL, Medicamento

# Criar uma instância da árvore
sistema = ArvoreAVL()

# Conectar ao banco de dados (SQLite)
sistema.conectar_bd("caminho/para/farmacia.db")

# Criar um novo medicamento
med = Medicamento(
    codigo=1,
    nome="Paracetamol",
    categoria="Analgésico",
    preco=10.50,
    quantidade=100,
    validade="2025-12-31",
    fabricante="Medley"
)

# Inserir medicamento na árvore
sistema.inserir(med)

# Buscar medicamento por código
resultado = sistema.buscar(1)

# Listar todos os medicamentos
medicamentos = sistema.listar_todos()

# Fechar conexão com o banco
sistema.fechar_conexao()
```

### Principais funcionalidades

- **Inserção, busca e remoção** de medicamentos em O(log n)
- **Balanceamento automático** usando rotações AVL
- **Persistência** em banco de dados SQLite
- **Buscas avançadas** por nome, categoria, preço e intervalo de código
- **Exportação e importação** de dados via CSV

### Modo CLI (linha de comando)

O arquivo também contém uma interface de linha de comando que pode ser executada diretamente:

```bash
python sistema_farmacia_avl.py
```

Também é possível executar operações específicas via argumentos:

```bash
# Exportar medicamentos para CSV
python sistema_farmacia_avl.py --exportar medicamentos.csv

# Importar medicamentos de CSV
python sistema_farmacia_avl.py --importar medicamentos.csv

# Mostrar estatísticas da árvore
python sistema_farmacia_avl.py --estatisticas

# Listar medicamentos com estoque abaixo de 20
python sistema_farmacia_avl.py --estoque-baixo 20
```

## 2. Usando o inserir_medicamentos.py

Este script permite gerar medicamentos de teste com dados realistas e inseri-los no banco de dados.

### Como executar

Execução básica:

```bash
python inserir_medicamentos.py
```

### Parâmetros disponíveis

```bash
# Gerar 500 medicamentos (padrão é 1000)
python inserir_medicamentos.py --quantidade 500

# Especificar caminho do banco de dados
python inserir_medicamentos.py --database minha_farmacia.db

# Exibir estatísticas após inserir
python inserir_medicamentos.py --stats

# Resetar o banco de dados e começar IDs do 1
python inserir_medicamentos.py --reset

# Combinando parâmetros
python inserir_medicamentos.py --quantidade 200 --database teste.db --stats --reset
```

### Parâmetros detalhados

- **-q, --quantidade**: Número de medicamentos a serem gerados
- **-d, --database**: Caminho para o banco de dados SQLite
- **-s, --stats**: Exibir estatísticas dos medicamentos após inserção
- **-r, --reset**: Limpar o banco de dados existente e iniciar IDs do 1
- **Exemplo**: `python inserir_medicamentos.py --q 5000 --reset`

## 3. Usando o app_farmacia.py (Interface Streamlit)

Este arquivo implementa uma interface web interativa usando o framework Streamlit.

### Como executar

```bash
streamlit run app_farmacia.py
```

Após executar o comando, o navegador abrirá automaticamente com a aplicação rodando (geralmente em http://localhost:8501).

### Funcionalidades da interface

- **Dashboard**: Visão geral dos medicamentos, estoque crítico e estatísticas
- **Cadastro de medicamentos**: Interface para adicionar novos medicamentos
- **Busca avançada**: Por código, faixa de preço ou intervalo de códigos
- **Gerenciamento de estoque**: Atualização de quantidade e preço, remoção de medicamentos
- **Visualização da árvore AVL**: Representação visual da estrutura de dados com indicadores de balanceamento

## Exemplos de Uso Completo

### Cenário 1: Configuração inicial do sistema

```bash
# Gerar 500 medicamentos de teste
python inserir_medicamentos.py --quantidade 500 --stats

# Iniciar a interface web
streamlit run app_farmacia.py
```

### Cenário 2: Exportação/Importação de dados

```bash
# Exportar dados usando CLI
python sistema_farmacia_avl.py --exportar backup.csv

# Importar dados em outro sistema
python sistema_farmacia_avl.py --importar backup.csv
```

### Cenário 3: Verificação de estoque crítico via linha de comando

```bash
python sistema_farmacia_avl.py --estoque-baixo 15
```

## Estrutura de Dados

O projeto utiliza uma **Árvore AVL** como estrutura principal, garantindo:

- Operações de busca, inserção e remoção em tempo O(log n)
- Balanceamento automático para garantir desempenho consistente
- Organização eficiente dos medicamentos por código

## Observações Importantes

- O banco de dados SQLite é criado automaticamente, caso não exista
- Para atualizar a árvore com dados do banco, use `sistema.carregar_medicamentos_bd()`
- Sempre feche a conexão com `sistema.fechar_conexao()` ao final do uso
- A visualização da árvore pode ser lenta para grandes conjuntos de dados

## Solução de Problemas

### Erro ao conectar no banco de dados

Verifique se o diretório especificado para o banco existe e tem permissões de escrita.

### Erro na visualização da árvore

Certifique-se de que o Graphviz está instalado corretamente no sistema.

### Interface Streamlit não atualiza após modificações

Use o comando `streamlit cache clear` e reinicie a aplicação.
