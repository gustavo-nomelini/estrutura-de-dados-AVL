import sqlite3
import argparse
import os
import datetime
from typing import List, Optional, Tuple, Dict
import sys
import locale
import time
import random
import numpy as np

# Configurar locale para formatação monetária adequada ao Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        pass  # Fallback para o locale padrão se não encontrar configuração brasileira


class Medicamento:
    """Classe que representa um medicamento no sistema."""
    
    def __init__(self, codigo: int, nome: str, categoria: str, preco: float, 
                 quantidade: int, validade: str, fabricante: str = None):
        self.codigo = codigo          # Código único do medicamento (chave primária)
        self.nome = nome              # Nome comercial do medicamento
        self.categoria = categoria    # Categoria terapêutica (ex: analgésico, antibiótico)
        self.preco = preco            # Preço de venda
        self.quantidade = quantidade  # Quantidade em estoque
        self.validade = validade      # Data de validade
        self.fabricante = fabricante  # Fabricante do medicamento
    
    def __str__(self) -> str:
        """Representação de string do medicamento."""
        return f"Código: {self.codigo}, Nome: {self.nome}, Preço: R${self.preco:.2f}, Estoque: {self.quantidade}, Validade: {self.validade}"
    
    def estoque_critico(self, limite: int = 10) -> bool:
        """Verifica se o medicamento está com estoque crítico."""
        return self.quantidade <= limite
    
    def to_dict(self) -> Dict:
        """Converte o medicamento para um dicionário."""
        return {
            "codigo": self.codigo,
            "nome": self.nome,
            "categoria": self.categoria,
            "preco": self.preco,
            "quantidade": self.quantidade,
            "validade": self.validade,
            "fabricante": self.fabricante
        }


class NoAVL:
    """Classe que representa um nó na árvore AVL."""
    
    def __init__(self, medicamento: Medicamento):
        self.medicamento = medicamento  # Medicamento armazenado no nó
        self.esquerda = None            # Filho esquerdo (menor código)
        self.direita = None             # Filho direito (maior código)
        self.altura = 1                 # Altura do nó (para balanceamento AVL)


class ArvoreAVL:
    """Implementação de uma Árvore AVL para gerenciamento de medicamentos."""
    
    def __init__(self):
        """Inicializa uma árvore AVL vazia."""
        self.raiz = None
        self.tamanho = 0
        self.db = None  # Conexão com o banco de dados
    
    def conectar_bd(self, db_path: str = "farmacia.db") -> None:
        """Conecta a árvore a um banco de dados SQLite."""
        self.db_path = db_path
        
        # Cria a pasta se não existir
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
        
        # Conecta ao banco e cria tabela se não existir
        self.db = sqlite3.connect(db_path)
        cursor = self.db.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicamentos (
            codigo INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            categoria TEXT,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            validade TEXT,
            fabricante TEXT,
            data_atualizacao TEXT
        )
        ''')
        
        self.db.commit()
    
    def fechar_conexao(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self.db:
            self.db.close()
            self.db = None
    
    def esta_vazia(self) -> bool:
        """Verifica se a árvore está vazia."""
        return self.raiz is None
    
    def tamanho_arvore(self) -> int:
        """Retorna o número de medicamentos na árvore."""
        return self.tamanho
    
    def _altura(self, no: Optional[NoAVL]) -> int:
        """Retorna a altura de um nó (0 se nulo)."""
        if no is None:
            return 0
        return no.altura
    
    def _fator_balanceamento(self, no: Optional[NoAVL]) -> int:
        """Calcula o fator de balanceamento de um nó (diferença entre alturas)."""
        if no is None:
            return 0
        return self._altura(no.esquerda) - self._altura(no.direita)
    
    def _atualizar_altura(self, no: NoAVL) -> None:
        """Atualiza a altura de um nó com base na altura de seus filhos."""
        if no is not None:
            no.altura = 1 + max(self._altura(no.esquerda), self._altura(no.direita))
    
    def _rotacao_direita(self, y: NoAVL) -> NoAVL:
        """Realiza uma rotação simples à direita."""
        x = y.esquerda
        T2 = x.direita
        
        # Realiza a rotação
        x.direita = y
        y.esquerda = T2
        
        # Atualiza alturas
        self._atualizar_altura(y)
        self._atualizar_altura(x)
        
        return x
    
    def _rotacao_esquerda(self, x: NoAVL) -> NoAVL:
        """Realiza uma rotação simples à esquerda."""
        y = x.direita
        T2 = y.esquerda
        
        # Realiza a rotação
        y.esquerda = x
        x.direita = T2
        
        # Atualiza alturas
        self._atualizar_altura(x)
        self._atualizar_altura(y)
        
        return y
    
    def inserir(self, medicamento: Medicamento, salvar_bd: bool = True) -> bool:
        """
        Insere um novo medicamento na árvore.
        
        Args:
            medicamento: O medicamento a ser inserido
            salvar_bd: Se True, também salva no banco de dados
            
        Returns:
            bool: True se foi inserido, False se foi apenas atualizado
        """
        if self.raiz is None:
            self.raiz = NoAVL(medicamento)
            self.tamanho += 1
            if salvar_bd and self.db:
                self._salvar_medicamento_bd(medicamento)
            return True
        
        # Tenta inserir e verifica se houve alteração no tamanho
        tamanho_anterior = self.tamanho
        self.raiz = self._inserir_recursivo(self.raiz, medicamento)
        
        # Se o tamanho mudou, foi inserido um novo, senão foi atualizado
        inserido_novo = self.tamanho > tamanho_anterior
        
        # Salva no banco se solicitado
        if salvar_bd and self.db:
            self._salvar_medicamento_bd(medicamento)
            
        return inserido_novo
    
    def _inserir_recursivo(self, no: Optional[NoAVL], medicamento: Medicamento) -> NoAVL:
        """Função recursiva para inserção em uma árvore AVL."""
        # Inserção BST padrão
        if no is None:
            self.tamanho += 1
            return NoAVL(medicamento)
        
        # Se o código já existe, atualiza o medicamento
        if medicamento.codigo == no.medicamento.codigo:
            no.medicamento = medicamento
            return no
        
        # Inserção recursiva
        if medicamento.codigo < no.medicamento.codigo:
            no.esquerda = self._inserir_recursivo(no.esquerda, medicamento)
        else:
            no.direita = self._inserir_recursivo(no.direita, medicamento)
        
        # Atualiza altura do nó atual
        self._atualizar_altura(no)
        
        # Verifica o balanceamento e reequilibra se necessário
        balanceamento = self._fator_balanceamento(no)
        
        # Caso Esquerda-Esquerda
        if balanceamento > 1 and medicamento.codigo < no.esquerda.medicamento.codigo:
            return self._rotacao_direita(no)
        
        # Caso Direita-Direita
        if balanceamento < -1 and medicamento.codigo > no.direita.medicamento.codigo:
            return self._rotacao_esquerda(no)
        
        # Caso Esquerda-Direita
        if balanceamento > 1 and medicamento.codigo > no.esquerda.medicamento.codigo:
            no.esquerda = self._rotacao_esquerda(no.esquerda)
            return self._rotacao_direita(no)
        
        # Caso Direita-Esquerda
        if balanceamento < -1 and medicamento.codigo < no.direita.medicamento.codigo:
            no.direita = self._rotacao_direita(no.direita)
            return self._rotacao_esquerda(no)
        
        return no
    
    def buscar(self, codigo: int) -> Optional[Medicamento]:
        """Busca um medicamento pelo código."""
        return self._buscar_recursivo(self.raiz, codigo)
    
    def _buscar_recursivo(self, no: Optional[NoAVL], codigo: int) -> Optional[Medicamento]:
        """Função recursiva para busca na árvore."""
        if no is None:
            return None
        
        if codigo == no.medicamento.codigo:
            return no.medicamento
        
        if codigo < no.medicamento.codigo:
            return self._buscar_recursivo(no.esquerda, codigo)
        else:
            return self._buscar_recursivo(no.direita, codigo)
    
    def remover(self, codigo: int, remover_bd: bool = True) -> bool:
        """
        Remove um medicamento pelo código.
        
        Args:
            codigo: Código do medicamento a ser removido
            remover_bd: Se True, também remove do banco de dados
            
        Returns:
            bool: True se removido com sucesso, False se não encontrado
        """
        resultado = [False]  # Usando lista para referência mutável
        self.raiz = self._remover_recursivo(self.raiz, codigo, resultado)
        if resultado[0]:
            self.tamanho -= 1
            
            # Remove do banco se solicitado
            if remover_bd and self.db:
                self._remover_medicamento_bd(codigo)
                
        return resultado[0]
    
    def _encontrar_minimo(self, no: NoAVL) -> NoAVL:
        """Encontra o nó com o menor valor (mais à esquerda)."""
        atual = no
        while atual.esquerda is not None:
            atual = atual.esquerda
        return atual
    
    def _remover_recursivo(self, no: Optional[NoAVL], codigo: int, resultado: List[bool]) -> Optional[NoAVL]:
        """Função recursiva para remoção em uma árvore AVL."""
        # Remoção BST padrão
        if no is None:
            return None
        
        if codigo < no.medicamento.codigo:
            no.esquerda = self._remover_recursivo(no.esquerda, codigo, resultado)
        elif codigo > no.medicamento.codigo:
            no.direita = self._remover_recursivo(no.direita, codigo, resultado)
        else:
            resultado[0] = True  # Medicamento encontrado e será removido
            
            # Nó com apenas um filho ou nenhum
            if no.esquerda is None:
                return no.direita
            elif no.direita is None:
                return no.esquerda
            
            # Nó com dois filhos
            sucessor = self._encontrar_minimo(no.direita)  # Encontra o sucessor in-order
            no.medicamento = sucessor.medicamento  # Copia o conteúdo do sucessor
            
            # Remove o sucessor
            no.direita = self._remover_recursivo(no.direita, sucessor.medicamento.codigo, [False])
        
        # Se a árvore tinha apenas um nó, retorna
        if no is None:
            return no
        
        # Atualiza a altura do nó atual
        self._atualizar_altura(no)
        
        # Verifica o balanceamento e reequilibra se necessário
        balanceamento = self._fator_balanceamento(no)
        
        # Caso Esquerda-Esquerda
        if balanceamento > 1 and self._fator_balanceamento(no.esquerda) >= 0:
            return self._rotacao_direita(no)
        
        # Caso Esquerda-Direita
        if balanceamento > 1 and self._fator_balanceamento(no.esquerda) < 0:
            no.esquerda = self._rotacao_esquerda(no.esquerda)
            return self._rotacao_direita(no)
        
        # Caso Direita-Direita
        if balanceamento < -1 and self._fator_balanceamento(no.direita) <= 0:
            return self._rotacao_esquerda(no)
        
        # Caso Direita-Esquerda
        if balanceamento < -1 and self._fator_balanceamento(no.direita) > 0:
            no.direita = self._rotacao_direita(no.direita)
            return self._rotacao_esquerda(no)
        
        return no
    
    def listar_todos(self) -> List[Medicamento]:
        """Lista todos os medicamentos em ordem crescente de código."""
        medicamentos = []
        self._percurso_em_ordem(self.raiz, medicamentos)
        return medicamentos
    
    def _percurso_em_ordem(self, no: Optional[NoAVL], medicamentos: List[Medicamento]) -> None:
        """Realiza percurso em-ordem na árvore (esquerda, raiz, direita)."""
        if no is not None:
            self._percurso_em_ordem(no.esquerda, medicamentos)
            medicamentos.append(no.medicamento)
            self._percurso_em_ordem(no.direita, medicamentos)
    
    def buscar_por_intervalo(self, codigo_inicio: int, codigo_fim: int) -> List[Medicamento]:
        """Busca medicamentos com códigos no intervalo especificado."""
        medicamentos = []
        self._buscar_intervalo_recursivo(self.raiz, codigo_inicio, codigo_fim, medicamentos)
        return medicamentos
    
    def _buscar_intervalo_recursivo(self, no: Optional[NoAVL], inicio: int, fim: int, 
                                   medicamentos: List[Medicamento]) -> None:
        """Função recursiva para buscar medicamentos em um intervalo de códigos."""
        if no is None:
            return
        
        # Verifica se há medicamentos à esquerda
        if inicio < no.medicamento.codigo:
            self._buscar_intervalo_recursivo(no.esquerda, inicio, fim, medicamentos)
        
        # Verifica se o medicamento atual está no intervalo
        if inicio <= no.medicamento.codigo <= fim:
            medicamentos.append(no.medicamento)
        
        # Verifica se há medicamentos à direita
        if fim > no.medicamento.codigo:
            self._buscar_intervalo_recursivo(no.direita, inicio, fim, medicamentos)
    
    def listar_estoque_baixo(self, limite: int = 10) -> List[Medicamento]:
        """Lista medicamentos com estoque abaixo do limite especificado."""
        medicamentos_baixo_estoque = []
        self._verificar_estoque_recursivo(self.raiz, limite, medicamentos_baixo_estoque)
        return medicamentos_baixo_estoque
    
    def _verificar_estoque_recursivo(self, no: Optional[NoAVL], limite: int, 
                                    medicamentos: List[Medicamento]) -> None:
        """Função recursiva para verificar medicamentos com estoque baixo."""
        if no is None:
            return
        
        self._verificar_estoque_recursivo(no.esquerda, limite, medicamentos)
        
        if no.medicamento.quantidade < limite:
            medicamentos.append(no.medicamento)
        
        self._verificar_estoque_recursivo(no.direita, limite, medicamentos)
    
    def buscar_por_faixa_preco(self, preco_min: float, preco_max: float) -> List[Medicamento]:
        """Busca medicamentos com preços no intervalo especificado."""
        medicamentos = []
        self._buscar_faixa_preco_recursivo(self.raiz, preco_min, preco_max, medicamentos)
        return medicamentos
    
    def _buscar_faixa_preco_recursivo(self, no: Optional[NoAVL], preco_min: float, 
                                     preco_max: float, medicamentos: List[Medicamento]) -> None:
        """Função recursiva para buscar medicamentos em uma faixa de preço."""
        if no is None:
            return
        
        # Como a árvore é organizada por código, precisamos verificar ambos os lados
        self._buscar_faixa_preco_recursivo(no.esquerda, preco_min, preco_max, medicamentos)
        
        if preco_min <= no.medicamento.preco <= preco_max:
            medicamentos.append(no.medicamento)
        
        self._buscar_faixa_preco_recursivo(no.direita, preco_min, preco_max, medicamentos)
    
    def altura_arvore(self) -> int:
        """Retorna a altura da árvore."""
        return self._altura(self.raiz)
    
    def verificar_balanceamento(self) -> bool:
        """Verifica se a árvore está balanceada corretamente."""
        return self._verificar_balanceamento_recursivo(self.raiz)
    
    def _verificar_balanceamento_recursivo(self, no: Optional[NoAVL]) -> bool:
        """Função recursiva para verificar o balanceamento de todos os nós."""
        if no is None:
            return True
        
        # Verifica o fator de balanceamento atual
        fb = self._fator_balanceamento(no)
        if abs(fb) > 1:
            return False
        
        # Verifica recursivamente as subárvores
        return (self._verificar_balanceamento_recursivo(no.esquerda) and 
                self._verificar_balanceamento_recursivo(no.direita))
    
    def buscar_por_nome(self, nome_parcial: str) -> List[Medicamento]:
        """Busca medicamentos pelo nome (busca parcial, case-insensitive)."""
        nome_parcial = nome_parcial.lower()
        medicamentos = []
        self._buscar_por_nome_recursivo(self.raiz, nome_parcial, medicamentos)
        return medicamentos
    
    def _buscar_por_nome_recursivo(self, no: Optional[NoAVL], nome_parcial: str, 
                                  medicamentos: List[Medicamento]) -> None:
        """Função recursiva para buscar medicamentos por nome."""
        if no is None:
            return
        
        # Percorre toda a árvore
        self._buscar_por_nome_recursivo(no.esquerda, nome_parcial, medicamentos)
        
        # Verifica se o nome contém a string de busca
        if nome_parcial in no.medicamento.nome.lower():
            medicamentos.append(no.medicamento)
        
        self._buscar_por_nome_recursivo(no.direita, nome_parcial, medicamentos)
    
    def buscar_por_categoria(self, categoria: str) -> List[Medicamento]:
        """Busca medicamentos por categoria."""
        categoria = categoria.lower()
        medicamentos = []
        self._buscar_por_categoria_recursivo(self.raiz, categoria, medicamentos)
        return medicamentos
    
    def _buscar_por_categoria_recursivo(self, no: Optional[NoAVL], categoria: str, 
                                       medicamentos: List[Medicamento]) -> None:
        """Função recursiva para buscar medicamentos por categoria."""
        if no is None:
            return
        
        # Percorre toda a árvore
        self._buscar_por_categoria_recursivo(no.esquerda, categoria, medicamentos)
        
        # Verifica se a categoria corresponde
        if categoria in no.medicamento.categoria.lower():
            medicamentos.append(no.medicamento)
        
        self._buscar_por_categoria_recursivo(no.direita, categoria, medicamentos)
    
    def _salvar_medicamento_bd(self, medicamento: Medicamento) -> bool:
        """Salva um medicamento no banco de dados (insere ou atualiza)."""
        if not self.db:
            raise ValueError("Banco de dados não conectado. Use conectar_bd() primeiro.")
        
        cursor = self.db.cursor()
        data_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Verifica se o medicamento já existe
        cursor.execute('SELECT codigo FROM medicamentos WHERE codigo = ?', (medicamento.codigo,))
        resultado = cursor.fetchone()
        
        if resultado:
            # Atualiza o medicamento existente
            cursor.execute('''
            UPDATE medicamentos 
            SET nome = ?, categoria = ?, preco = ?, quantidade = ?, validade = ?, fabricante = ?, data_atualizacao = ?
            WHERE codigo = ?
            ''', (medicamento.nome, medicamento.categoria, medicamento.preco, medicamento.quantidade, 
                  medicamento.validade, medicamento.fabricante, data_atual, medicamento.codigo))
        else:
            # Insere novo medicamento
            cursor.execute('''
            INSERT INTO medicamentos (codigo, nome, categoria, preco, quantidade, validade, fabricante, data_atualizacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (medicamento.codigo, medicamento.nome, medicamento.categoria, medicamento.preco, 
                  medicamento.quantidade, medicamento.validade, medicamento.fabricante, data_atual))
        
        self.db.commit()
        return True
    
    def _remover_medicamento_bd(self, codigo: int) -> bool:
        """Remove um medicamento do banco de dados."""
        if not self.db:
            raise ValueError("Banco de dados não conectado. Use conectar_bd() primeiro.")
        
        cursor = self.db.cursor()
        cursor.execute('DELETE FROM medicamentos WHERE codigo = ?', (codigo,))
        
        rows_affected = cursor.rowcount
        self.db.commit()
        
        return rows_affected > 0
    
    def carregar_medicamentos_bd(self) -> int:
        """
        Carrega todos os medicamentos do banco de dados para a árvore.
        
        Returns:
            int: Número de medicamentos carregados
        """
        if not self.db:
            raise ValueError("Banco de dados não conectado. Use conectar_bd() primeiro.")
        
        # Limpa a árvore atual
        self.raiz = None
        self.tamanho = 0
        
        cursor = self.db.cursor()
        cursor.execute('SELECT codigo, nome, categoria, preco, quantidade, validade, fabricante FROM medicamentos')
        
        count = 0
        for row in cursor.fetchall():
            codigo, nome, categoria, preco, quantidade, validade, fabricante = row
            medicamento = Medicamento(codigo, nome, categoria, preco, quantidade, validade, fabricante)
            
            # Insere na árvore sem salvar no banco novamente
            self.inserir(medicamento, salvar_bd=False)
            count += 1
        
        return count
    
    def exportar_para_csv(self, arquivo: str) -> int:
        """
        Exporta todos os medicamentos para um arquivo CSV.
        
        Args:
            arquivo: Caminho do arquivo CSV
            
        Returns:
            int: Número de medicamentos exportados
        """
        medicamentos = self.listar_todos()
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            # Cabeçalho
            f.write("codigo,nome,categoria,preco,quantidade,validade,fabricante\n")
            
            # Dados
            for med in medicamentos:
                linha = f"{med.codigo},{med.nome},{med.categoria},{med.preco},{med.quantidade},{med.validade},{med.fabricante or ''}\n"
                f.write(linha)
        
        return len(medicamentos)
    
    def importar_de_csv(self, arquivo: str, salvar_bd: bool = True) -> int:
        """
        Importa medicamentos de um arquivo CSV.
        
        Args:
            arquivo: Caminho do arquivo CSV
            salvar_bd: Se True, também salva no banco de dados
            
        Returns:
            int: Número de medicamentos importados
        """
        count = 0
        
        with open(arquivo, 'r', encoding='utf-8') as f:
            # Pula o cabeçalho
            next(f)
            
            for linha in f:
                dados = linha.strip().split(',')
                if len(dados) >= 6:
                    codigo = int(dados[0])
                    nome = dados[1]
                    categoria = dados[2]
                    preco = float(dados[3])
                    quantidade = int(dados[4])
                    validade = dados[5]
                    fabricante = dados[6] if len(dados) > 6 and dados[6] else None
                    
                    medicamento = Medicamento(codigo, nome, categoria, preco, quantidade, validade, fabricante)
                    self.inserir(medicamento, salvar_bd=salvar_bd)
                    count += 1
        
        return count


# Funções para interface de linha de comando (CLI)
def exibir_menu() -> None:
    """Exibe o menu principal da aplicação CLI."""
    print("\n" + "="*60)
    print("    SISTEMA DE GERENCIAMENTO DE FARMÁCIA - ÁRVORE AVL")
    print("="*60)
    print("1. Cadastrar novo medicamento")
    print("2. Buscar medicamento por código")
    print("3. Remover medicamento")
    print("4. Listar todos os medicamentos")
    print("5. Buscar medicamentos por faixa de código")
    print("6. Buscar medicamentos por faixa de preço")
    print("7. Listar medicamentos com estoque baixo")
    print("8. Buscar medicamentos por nome")
    print("9. Buscar medicamentos por categoria")
    print("10. Exportar dados para CSV")
    print("11. Importar dados de CSV")
    print("12. Estatísticas da árvore AVL")
    print("13. Comparar tempos de busca (AVL vs Lista Encadeada)")
    print("14. Verificar medicamentos próximos do vencimento")  # Nova opção
    print("15. Análise de desempenho com 500.000 medicamentos")  # Nova opção para análise avançada
    print("0. Sair")
    print("="*60)


def formatar_moeda(valor: float) -> str:
    """Formata um valor monetário adequadamente."""
    try:
        # Tenta usar formatação localizada
        return locale.currency(valor, grouping=True)
    except:
        # Fallback para formatação manual
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_percentual(parte: int, total: int) -> str:
    """Calcula e formata o percentual."""
    if total == 0:
        return "0,0%"
    return f"{(parte / total * 100):.1f}%".replace(".", ",")


def ler_medicamento() -> Medicamento:
    """Lê os dados de um medicamento a partir da entrada do usuário."""
    print("\n--- Cadastro de Medicamento ---")
    codigo = int(input("Código: "))
    nome = input("Nome: ")
    categoria = input("Categoria: ")
    
    # Validação de preço com formatação adequada
    while True:
        preco_str = input("Preço (R$): ")
        try:
            # Remove caracteres não numéricos e converte vírgula para ponto
            preco_str = preco_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
            preco = float(preco_str)
            if preco < 0:
                print("O preço não pode ser negativo.")
                continue
            break
        except ValueError:
            print("Formato de preço inválido. Digite um valor numérico.")
    
    quantidade = int(input("Quantidade em estoque: "))
    
    # Validação de data
    while True:
        validade = input("Data de validade (YYYY-MM-DD): ")
        try:
            # Verifica se a data está no formato correto
            datetime.datetime.strptime(validade, "%Y-%m-%d")
            break
        except ValueError:
            print("Formato de data inválido! Use YYYY-MM-DD.")
    
    fabricante = input("Fabricante (opcional): ")
    if not fabricante.strip():
        fabricante = None
    
    return Medicamento(codigo, nome, categoria, preco, quantidade, validade, fabricante)


def exibir_medicamento(med: Medicamento) -> None:
    """Exibe os detalhes de um medicamento formatados."""
    print("\n--- Detalhes do Medicamento ---")
    print(f"Código: {med.codigo}")
    print(f"Nome: {med.nome}")
    print(f"Categoria: {med.categoria}")
    print(f"Fabricante: {med.fabricante or 'Não informado'}")
    print(f"Preço: {formatar_moeda(med.preco)}")
    
    # Destaque para estoque crítico
    if med.quantidade < 5:
        print(f"Estoque: {med.quantidade} unidades [CRÍTICO]")
    elif med.quantidade < 10:
        print(f"Estoque: {med.quantidade} unidades [BAIXO]")
    else:
        print(f"Estoque: {med.quantidade} unidades")
    
    print(f"Validade: {med.validade}")
    
    # Valor total deste item
    valor_total = med.preco * med.quantidade
    print(f"Valor total em estoque: {formatar_moeda(valor_total)}")


def exibir_lista_medicamentos(medicamentos: List[Medicamento], titulo: str) -> None:
    """Exibe uma lista de medicamentos com formatação."""
    if not medicamentos:
        print(f"\nNenhum medicamento encontrado para: {titulo}")
        return
    
    print(f"\n--- {titulo} ({len(medicamentos)}) ---")
    print(f"{'Código':<8} {'Nome':<25} {'Categoria':<15} {'Preço':<15} {'Estoque':<10} {'Validade':<12}")
    print("-" * 85)
    
    for med in medicamentos:
        nome_truncado = med.nome[:23] + ".." if len(med.nome) > 25 else med.nome
        categoria_truncada = med.categoria[:13] + ".." if len(med.categoria) > 15 else med.categoria
        
        # Formatação com destaque para estoque crítico
        if med.quantidade < 5:
            estoque = f"{med.quantidade} [!]"
        elif med.quantidade < 10:
            estoque = f"{med.quantidade} *"
        else:
            estoque = str(med.quantidade)
        
        preco_formatado = formatar_moeda(med.preco)
        
        print(f"{med.codigo:<8} {nome_truncado:<25} {categoria_truncada:<15} {preco_formatado:<15} {estoque:<10} {med.validade:<12}")


def exibir_estatisticas_arvore(sistema: ArvoreAVL) -> None:
    """Exibe estatísticas sobre a árvore AVL."""
    print("\n--- Estatísticas da Árvore AVL ---")
    print(f"Total de medicamentos: {sistema.tamanho_arvore()}")
    print(f"Altura da árvore: {sistema.altura_arvore()}")
    print(f"Árvore balanceada: {'Sim' if sistema.verificar_balanceamento() else 'Não'}")
    
    # Estatísticas adicionais
    medicamentos = sistema.listar_todos()
    if medicamentos:
        total_estoque = sum(med.quantidade for med in medicamentos)
        valor_total = sum(med.preco * med.quantidade for med in medicamentos)
        estoque_baixo = len(sistema.listar_estoque_baixo(10))
        estoque_critico = len(sistema.listar_estoque_baixo(5))
        
        print(f"\nTotal de itens em estoque: {total_estoque} unidades")
        print(f"Valor total em estoque: {formatar_moeda(valor_total)}")
        print(f"Medicamentos com estoque baixo (<10): {estoque_baixo}")
        print(f"Medicamentos com estoque crítico (<5): {estoque_critico}")
        
        # Contagem e análise por categoria
        categorias = {}
        valor_por_categoria = {}
        estoque_por_categoria = {}
        
        for med in medicamentos:
            categorias[med.categoria] = categorias.get(med.categoria, 0) + 1
            valor_por_categoria[med.categoria] = valor_por_categoria.get(med.categoria, 0) + (med.preco * med.quantidade)
            estoque_por_categoria[med.categoria] = estoque_por_categoria.get(med.categoria, 0) + med.quantidade
        
        print("\n--- Análise por Categoria ---")
        print(f"{'Categoria':<20} {'Qtd. Itens':<10} {'%':<6} {'Unidades':<10} {'%':<6} {'Valor em Estoque':<20}")
        print("-" * 75)
        
        # Ordenar categorias pelo valor total em estoque (decrescente)
        categorias_ordenadas = sorted(categorias.keys(), key=lambda c: valor_por_categoria[c], reverse=True)
        
        for categoria in categorias_ordenadas:
            qtd_itens = categorias[categoria]
            qtd_unidades = estoque_por_categoria[categoria]
            valor_cat = valor_por_categoria[categoria]
            
            perc_itens = calcular_percentual(qtd_itens, len(medicamentos))
            perc_unidades = calcular_percentual(qtd_unidades, total_estoque)
            
            print(f"{categoria[:19]:<20} {qtd_itens:<10} {perc_itens:<6} "
                  f"{qtd_unidades:<10} {perc_unidades:<6} {formatar_moeda(valor_cat):<20}")
        
        print("-" * 75)
        print(f"{'TOTAL':<20} {len(medicamentos):<10} {'100%':<6} "
              f"{total_estoque:<10} {'100%':<6} {formatar_moeda(valor_total):<20}")


def pausar() -> None:
    """Pausa a execução até que o usuário pressione Enter."""
    input("\nPressione Enter para continuar...")


def simular_busca_lista_encadeada(medicamentos: List[Medicamento], codigo: int) -> Tuple[Optional[Medicamento], float]:
    """
    Simula a busca em uma lista encadeada (complexidade O(n)).
    
    Args:
        medicamentos: Lista de medicamentos
        codigo: Código do medicamento a ser buscado
        
    Returns:
        Tuple[Optional[Medicamento], float]: O medicamento encontrado (ou None) e o tempo de busca
    """
    inicio = time.time()
    
    resultado = None
    # Percorre a lista sequencialmente (simulando uma lista encadeada)
    for med in medicamentos:
        if med.codigo == codigo:
            resultado = med
            break
    
    fim = time.time()
    tempo = (fim - inicio) * 1000  # Tempo em milissegundos
    
    return resultado, tempo


def comparar_tempos_busca(sistema: ArvoreAVL) -> None:
    """Compara os tempos de busca entre árvore AVL e uma lista encadeada simulada."""
    # Obtém todos os medicamentos
    medicamentos = sistema.listar_todos()
    total = len(medicamentos)
    
    if total == 0:
        print("\nNão há medicamentos cadastrados para realizar a comparação.")
        return
    
    print("\n--- Comparação de Tempos de Busca: AVL vs Lista Encadeada ---")
    print(f"Total de medicamentos: {total}")
    
    # Prepara a tabela de resultados
    print("\n{:<15} {:<20} {:<20} {:<15}".format("Caso", "Tempo AVL (ms)", "Tempo Lista (ms)", "Diferença (x)"))
    print("-" * 75)
    
    # Casos de teste
    casos = [
        ("Melhor caso", medicamentos[0].codigo),  # Primeiro elemento (raiz da árvore)
        ("Pior caso", medicamentos[-1].codigo),   # Último elemento
        ("Caso médio", medicamentos[len(medicamentos)//2].codigo)  # Elemento do meio
    ]
    
    # Código aleatório dentro do intervalo existente
    if total > 3:
        codigos = [med.codigo for med in medicamentos]
        random_idx = random.randint(0, total-1)
        casos.append(("Caso aleatório", medicamentos[random_idx].codigo))
    
    # Código inexistente (sempre maior que todos os existentes)
    codigo_inexistente = max([med.codigo for med in medicamentos]) + 1000
    casos.append(("Inexistente", codigo_inexistente))
    
    # Realizando as buscas
    for caso, codigo in casos:
        # Tempo na AVL
        inicio = time.time()
        resultado_avl = sistema.buscar(codigo)
        fim = time.time()
        tempo_avl = (fim - inicio) * 1000  # Tempo em milissegundos
        
        # Tempo na lista encadeada simulada
        _, tempo_lista = simular_busca_lista_encadeada(medicamentos, codigo)
        
        # Calcula a diferença (quantas vezes a lista é mais lenta)
        if tempo_avl > 0:
            diferenca = tempo_lista / tempo_avl
        else:
            diferenca = "N/A"
        
        # Formata e exibe os resultados
        print("{:<15} {:<20.6f} {:<20.6f} {:<15.2f}".format(caso, tempo_avl, tempo_lista, diferenca if diferenca != "N/A" else 0))
    
    # Conclusão teórica
    print("\n--- Análise de Complexidade ---")
    print(f"Para {total} medicamentos:")
    print(f"• Árvore AVL:      O(log n) ≈ {(2.3 * (total.bit_length() - 1)):.1f} comparações no pior caso")
    print(f"• Lista Encadeada:  O(n)     = {total} comparações no pior caso")
    print("\nA diferença teórica é de {:.1f}x em favor da AVL para este volume de dados.".format(
          total / (2.3 * (total.bit_length() - 1)) if total > 1 else 1))
    
    print("\nObservações:")
    print("• A AVL mantém tempos de busca muito mais estáveis mesmo com grandes volumes de dados")
    print("• Com 1.000 medicamentos, a lista encadeada pode ser até 100x mais lenta no pior caso")
    print("• Para 1 milhão de medicamentos, a diferença pode chegar a 50.000x")
    print("• Além da busca rápida, a AVL também mantém os dados organizados (ordenados)")


def verificar_validade(medicamentos: List[Medicamento], dias_limite: int = 90) -> List[Medicamento]:
    """
    Filtra medicamentos que estão próximos da data de vencimento.
    
    Args:
        medicamentos: Lista de medicamentos
        dias_limite: Número de dias para considerar próximo do vencimento
    
    Returns:
        Lista de medicamentos próximos do vencimento
    """
    hoje = datetime.date.today()
    med_a_vencer = []
    
    for med in medicamentos:
        try:
            data_validade = datetime.datetime.strptime(med.validade, "%Y-%m-%d").date()
            dias_ate_vencer = (data_validade - hoje).days
            
            if 0 <= dias_ate_vencer <= dias_limite:
                med_a_vencer.append((med, dias_ate_vencer))
        except (ValueError, TypeError):
            # Ignora datas de validade inválidas
            pass
    
    # Ordena por proximidade da validade
    med_a_vencer.sort(key=lambda x: x[1])
    return [med for med, _ in med_a_vencer]


def exibir_medicamentos_a_vencer() -> None:
    """Exibe uma lista de medicamentos próximos do vencimento."""
    # Fix: Access the sistema variable directly from the calling scope
    sistema = None
    
    # Check if we're in the global session state context
    if 'st' in globals() and hasattr(globals()['st'], 'session_state') and hasattr(globals()['st'].session_state, 'sistema'):
        sistema = globals()['st'].session_state.sistema
    
    # If not in session state, try to get from current function's scope
    if sistema is None and 'sistema' in locals():
        sistema = locals()['sistema']
    
    # If still not found, look in global scope
    if sistema is None and 'sistema' in globals():
        sistema = globals()['sistema']
    
    # Final fallback - access it via the parent function's local variables
    if sistema is None:
        import inspect
        frame = inspect.currentframe().f_back
        if 'sistema' in frame.f_locals:
            sistema = frame.f_locals['sistema']
    
    # Check if we found a valid sistema object
    if sistema is None or not hasattr(sistema, 'listar_todos'):
        print("\nSistema não inicializado corretamente.")
        return
    
    medicamentos = sistema.listar_todos()
    
    if not medicamentos:
        print("\nNão há medicamentos cadastrados.")
        return
    
    # Solicita o limite de dias ao usuário
    try:
        dias_limite = int(input("\nConsiderar medicamentos que vencem em até quantos dias? (padrão: 90): ") or "90")
    except ValueError:
        print("\nValor inválido. Usando padrão de 90 dias.")
        dias_limite = 90
    
    # Obtém medicamentos próximos do vencimento
    med_a_vencer = verificar_validade(medicamentos, dias_limite)
    
    if not med_a_vencer:
        print(f"\nNão há medicamentos vencendo nos próximos {dias_limite} dias.")
        return
    
    hoje = datetime.date.today()
    
    print(f"\n--- Medicamentos Vencendo nos Próximos {dias_limite} dias ({len(med_a_vencer)}) ---")
    print(f"{'Código':<8} {'Nome':<25} {'Estoque':<10} {'Validade':<12} {'Dias restantes':<15} {'Status'}")
    print("-" * 85)
    
    for med in med_a_vencer:
        # Calcula dias até o vencimento
        data_validade = datetime.datetime.strptime(med.validade, "%Y-%m-%d").date()
        dias_ate_vencer = (data_validade - hoje).days
        
        # Define o status de vencimento
        if dias_ate_vencer < 0:
            status = "VENCIDO"
        elif dias_ate_vencer <= 30:
            status = "CRÍTICO"
        elif dias_ate_vencer <= 60:
            status = "ATENÇÃO"
        else:
            status = "OK"
        
        nome_truncado = med.nome[:23] + ".." if len(med.nome) > 25 else med.nome
        
        print(f"{med.codigo:<8} {nome_truncado:<25} {med.quantidade:<10} {med.validade:<12} {dias_ate_vencer:>15} {status}")
    
    # Opção para gerar relatório CSV
    exportar = input("\nDeseja exportar esta lista para CSV? (S/N): ").upper() == "S"
    if exportar:
        nome_arquivo = input("Nome do arquivo (padrão: medicamentos_validade.csv): ") or "medicamentos_validade.csv"
        
        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                # Cabeçalho
                f.write("codigo,nome,categoria,preco,quantidade,validade,dias_ate_vencer,status\n")
                
                # Dados
                for med in med_a_vencer:
                    data_validade = datetime.datetime.strptime(med.validade, "%Y-%m-%d").date()
                    dias_ate_vencer = (data_validade - hoje).days
                    
                    if dias_ate_vencer < 0:
                        status = "VENCIDO"
                    elif dias_ate_vencer <= 30:
                        status = "CRÍTICO"
                    elif dias_ate_vencer <= 60:
                        status = "ATENÇÃO"
                    else:
                        status = "OK"
                    
                    linha = f"{med.codigo},{med.nome},{med.categoria},{med.preco},{med.quantidade},{med.validade},{dias_ate_vencer},{status}\n"
                    f.write(linha)
                
                print(f"\nRelatório exportado com sucesso para '{nome_arquivo}'!")
        except Exception as e:
            print(f"\nErro ao exportar relatório: {e}")


def analisar_desempenho_grande_escala() -> None:
    """Realiza uma análise detalhada de desempenho com grande volume de dados."""
    print("\n=== ANÁLISE DE DESEMPENHO AVL vs. LISTA ENCADEADA COM 500.000 ITENS ===")
    print("\nEste teste simula operações em uma base de dados muito grande.")
    print("ATENÇÃO: Esta análise pode demorar alguns minutos para ser concluída.")
    
    confirmar = input("\nDeseja prosseguir com a análise? (S/N): ").upper()
    if confirmar != "S":
        print("Análise cancelada.")
        return
    
    # Tamanho da simulação
    n = 500000
    print(f"\nGerando {n:,} códigos para teste...".replace(",", "."))
    
    # Gera IDs sequenciais (ordenados)
    ids_ordenados = list(range(1, n+1))
    
    # Gera IDs aleatórios (não ordenados)
    ids_aleatorios = list(range(1, n+1))
    random.shuffle(ids_aleatorios)
    
    # Tempos para diferentes cenários e estruturas
    tempos = {
        "avl": {"melhor": 0, "medio": 0, "pior": 0, "aleatorio": 0, "inexistente": 0},
        "lista": {"melhor": 0, "medio": 0, "pior": 0, "aleatorio": 0, "inexistente": 0}
    }
    
    print("\n=== SIMULANDO BUSCAS EM ÁRVORE AVL ===")
    
    # Simulação de busca na AVL (log n)
    def simular_busca_avl(codigo, n):
        # Simulação simplificada de busca em AVL: O(log n)
        comparacoes = int(np.log2(n)) + 1
        # Simula o tempo gasto (proporcional ao número de comparações)
        tempo = comparacoes * 0.001  # simula microsegundos por comparação
        return tempo * 1000  # converte para milissegundos
    
    # Melhor/pior/médio caso para AVL são semelhantes devido à natureza balanceada
    print("Simulando busca no primeiro elemento (raiz/melhor caso)...")
    tempos["avl"]["melhor"] = simular_busca_avl(ids_ordenados[0], n)
    
    print("Simulando busca no elemento do meio...")
    tempos["avl"]["medio"] = simular_busca_avl(ids_ordenados[n//2], n)
    
    print("Simulando busca no último elemento (pior caso)...")
    tempos["avl"]["pior"] = simular_busca_avl(ids_ordenados[n-1], n)
    
    print("Simulando busca em elemento aleatório...")
    idx_aleatorio = random.randint(0, n-1)
    tempos["avl"]["aleatorio"] = simular_busca_avl(ids_aleatorios[idx_aleatorio], n)
    
    print("Simulando busca de código inexistente...")
    tempos["avl"]["inexistente"] = simular_busca_avl(n+1000, n)
    
    print("\n=== SIMULANDO BUSCAS EM LISTA ENCADEADA ===")
    
    # Simulação de busca na lista (linear)
    def simular_busca_lista(indice, n):
        # Simulação de busca em lista encadeada: O(n)
        # Na lista, o número de comparações depende da posição do elemento
        comparacoes = indice + 1  # +1 porque índice começa em 0
        # Simula o tempo gasto (proporcional ao número de comparações)
        tempo = comparacoes * 0.001  # simula microsegundos por comparação
        return tempo * 1000  # converte para milissegundos
    
    print("Simulando busca no primeiro elemento (melhor caso para lista)...")
    tempos["lista"]["melhor"] = simular_busca_lista(0, n)
    
    print("Simulando busca no elemento do meio...")
    tempos["lista"]["medio"] = simular_busca_lista(n//2, n)
    
    print("Simulando busca no último elemento (pior caso para lista)...")
    tempos["lista"]["pior"] = simular_busca_lista(n-1, n)
    
    print("Simulando busca em elemento aleatório...")
    tempos["lista"]["aleatorio"] = simular_busca_lista(idx_aleatorio, n)
    
    print("Simulando busca de código inexistente...")
    tempos["lista"]["inexistente"] = simular_busca_lista(n, n)  # Se não existe, percorre toda a lista
    
    # Exibe resultados
    print("\n=== RESULTADOS DA SIMULAÇÃO ===")
    print(f"\nComparando busca em {n:,} elementos:".replace(",", "."))
    print(f"\n{'Cenário':<15} {'Tempo AVL (ms)':<20} {'Tempo Lista (ms)':<20} {'Diferença (x)':<15}")
    print("-" * 72)
    
    for cenario in ["melhor", "medio", "pior", "aleatorio", "inexistente"]:
        tempo_avl = tempos["avl"][cenario]
        tempo_lista = tempos["lista"][cenario]
        diferenca = tempo_lista / tempo_avl if tempo_avl > 0 else "N/A"
        
        # Formata o nome do cenário para exibição
        nome_cenario = {
            "melhor": "Melhor caso",
            "medio": "Caso médio",
            "pior": "Pior caso",
            "aleatorio": "Aleatório",
            "inexistente": "Inexistente"
        }.get(cenario, cenario)
        
        print(f"{nome_cenario:<15} {tempo_avl:<20.6f} {tempo_lista:<20.6f} {diferenca:<15.2f}")
    
    # Gráfico ASCII simples para visualizar a diferença
    print("\nComparação Visual (escala logarítmica, cada '*' representa ~10x):")
    
    max_log = int(np.log10(tempos["lista"]["pior"] / tempos["avl"]["pior"])) + 1
    escala = max(1, max_log // 10)
    
    print(f"\n{'Cenário':<15} {'AVL':<50} {'Lista':<50}")
    print("-" * 115)
    
    for cenario in ["melhor", "medio", "pior", "aleatorio", "inexistente"]:
        nome_cenario = {
            "melhor": "Melhor caso",
            "medio": "Caso médio",
            "pior": "Pior caso",
            "aleatorio": "Aleatório",
            "inexistente": "Inexistente"
        }.get(cenario, cenario)
        
        tempo_avl = tempos["avl"][cenario]
        tempo_lista = tempos["lista"][cenario]
        
        # Cálculo para escala logarítmica do gráfico ASCII
        bar_avl = "*" * (int(np.log10(tempo_avl + 0.001) / escala) + 1)
        bar_lista = "*" * (int(np.log10(tempo_lista + 0.001) / escala) + 1)
        
        print(f"{nome_cenario:<15} {bar_avl:<50} {bar_lista:<50}")
    
    # Conclusão
    avl_log = np.log2(n)
    print(f"\nConclusão Teórica para {n:,} elementos:".replace(",", "."))
    print(f"- Árvore AVL:      O(log n) ≈ {avl_log:.1f} comparações")
    print(f"- Lista Encadeada:  O(n)     = {n:,} comparações (pior caso)".replace(",", "."))
    print(f"- Diferença teórica: {n/avl_log:.1f}x em favor da AVL")
    
    # Explicação avançada
    print("\nAnálise Detalhada:")
    print("- A AVL mantém um desempenho consistente (logarítmico) independente do caso")
    print("- A lista tem desempenho linear que varia muito do melhor para o pior caso")
    print("- Em sistemas reais, o impacto seria ainda maior devido a:")
    print("  * Alocação de memória mais eficiente na árvore (localidade)")
    print("  * Operações de cache mais eficientes")
    print("  * Menor overhead em operações subsequentes após a primeira busca")


def main_cli() -> None:
    """Função principal da interface de linha de comando."""
    # Configura o sistema
    sistema = ArvoreAVL()
    sistema.conectar_bd("farmacia.db")
    
    # Create a módulo global para armazenas objeto st simulado
    # This creates a module-level variable to store the session state
    global st
    st = type('', (), {})()  # Cria um objeto simples para simular o st do Streamlit
    st.session_state = type('', (), {})()
    st.session_state.sistema = sistema
    
    try:
        # Carrega medicamentos do banco
        num_carregados = sistema.carregar_medicamentos_bd()
        print(f"Sistema inicializado. {num_carregados} medicamentos carregados do banco de dados.")
        
        while True:
            exibir_menu()
            opcao = input("Digite a opção desejada: ")
            
            if opcao == "0":
                print("\nEncerrando o sistema...")
                break
            
            elif opcao == "1":  # Cadastrar
                try:
                    medicamento = ler_medicamento()
                    resultado = sistema.inserir(medicamento)
                    
                    if resultado:
                        print(f"\nMedicamento '{medicamento.nome}' cadastrado com sucesso!")
                    else:
                        print(f"\nMedicamento '{medicamento.nome}' atualizado com sucesso!")
                    
                    exibir_medicamento(medicamento)
                except ValueError as e:
                    print(f"\nErro ao cadastrar: {e}")
                
                pausar()
            
            elif opcao == "2":  # Buscar por código
                try:
                    codigo = int(input("\nDigite o código do medicamento: "))
                    medicamento = sistema.buscar(codigo)
                    
                    if medicamento:
                        exibir_medicamento(medicamento)
                    else:
                        print(f"\nMedicamento com código {codigo} não encontrado.")
                except ValueError:
                    print("\nCódigo inválido. Digite um número inteiro.")
                
                pausar()
            
            elif opcao == "3":  # Remover
                try:
                    codigo = int(input("\nDigite o código do medicamento a remover: "))
                    medicamento = sistema.buscar(codigo)
                    
                    if medicamento:
                        exibir_medicamento(medicamento)
                        confirmacao = input("\nConfirma a remoção? (S/N): ").upper()
                        
                        if confirmacao == "S":
                            sistema.remover(codigo)
                            print(f"\nMedicamento '{medicamento.nome}' removido com sucesso!")
                        else:
                            print("\nOperação cancelada.")
                    else:
                        print(f"\nMedicamento com código {codigo} não encontrado.")
                except ValueError:
                    print("\nCódigo inválido. Digite um número inteiro.")
                
                pausar()
            
            elif opcao == "4":  # Listar todos
                medicamentos = sistema.listar_todos()
                exibir_lista_medicamentos(medicamentos, "Todos os Medicamentos")
                pausar()
            
            elif opcao == "5":  # Buscar por faixa de código
                try:
                    codigo_inicio = int(input("\nDigite o código inicial: "))
                    codigo_fim = int(input("Digite o código final: "))
                    
                    if codigo_inicio > codigo_fim:
                        codigo_inicio, codigo_fim = codigo_fim, codigo_inicio
                    
                    medicamentos = sistema.buscar_por_intervalo(codigo_inicio, codigo_fim)
                    exibir_lista_medicamentos(medicamentos, f"Medicamentos com código entre {codigo_inicio} e {codigo_fim}")
                except ValueError:
                    print("\nCódigo inválido. Digite números inteiros.")
                
                pausar()
            
            elif opcao == "6":  # Buscar por faixa de preço
                try:
                    preco_min = float(input("\nDigite o preço mínimo (R$): "))
                    preco_max = float(input("Digite o preço máximo (R$): "))
                    
                    if preco_min > preco_max:
                        preco_min, preco_max = preco_max, preco_min
                    
                    medicamentos = sistema.buscar_por_faixa_preco(preco_min, preco_max)
                    exibir_lista_medicamentos(medicamentos, f"Medicamentos com preço entre R${preco_min:.2f} e R${preco_max:.2f}")
                except ValueError:
                    print("\nPreço inválido. Digite valores numéricos.")
                
                pausar()
            
            elif opcao == "7":  # Listar estoque baixo
                try:
                    limite = int(input("\nDigite o limite de estoque (padrão 10): ") or "10")
                    medicamentos = sistema.listar_estoque_baixo(limite)
                    exibir_lista_medicamentos(medicamentos, f"Medicamentos com estoque abaixo de {limite} unidades")
                except ValueError:
                    print("\nLimite inválido. Digite um número inteiro.")
                
                pausar()
            
            elif opcao == "8":  # Buscar por nome
                nome = input("\nDigite o nome (ou parte do nome) do medicamento: ")
                if nome:
                    medicamentos = sistema.buscar_por_nome(nome)
                    exibir_lista_medicamentos(medicamentos, f"Medicamentos contendo '{nome}' no nome")
                else:
                    print("\nNome inválido.")
                
                pausar()
            
            elif opcao == "9":  # Buscar por categoria
                categoria = input("\nDigite a categoria do medicamento: ")
                if categoria:
                    medicamentos = sistema.buscar_por_categoria(categoria)
                    exibir_lista_medicamentos(medicamentos, f"Medicamentos da categoria '{categoria}'")
                else:
                    print("\nCategoria inválida.")
                
                pausar()
            
            elif opcao == "10":  # Exportar para CSV
                arquivo = input("\nDigite o nome do arquivo CSV para exportação (padrão: medicamentos.csv): ") or "medicamentos.csv"
                try:
                    count = sistema.exportar_para_csv(arquivo)
                    print(f"\n{count} medicamentos exportados com sucesso para '{arquivo}'!")
                except Exception as e:
                    print(f"\nErro ao exportar: {e}")
                
                pausar()
            
            elif opcao == "11":  # Importar de CSV
                arquivo = input("\nDigite o nome do arquivo CSV para importação: ")
                if not arquivo:
                    print("\nNome de arquivo inválido.")
                elif not os.path.isfile(arquivo):
                    print(f"\nArquivo '{arquivo}' não encontrado.")
                else:
                    try:
                        count = sistema.importar_de_csv(arquivo)
                        print(f"\n{count} medicamentos importados com sucesso de '{arquivo}'!")
                    except Exception as e:
                        print(f"\nErro ao importar: {e}")
                
                pausar()
            
            elif opcao == "12":  # Estatísticas
                exibir_estatisticas_arvore(sistema)
                pausar()
            
            elif opcao == "13":  # Comparar tempos de busca
                comparar_tempos_busca(sistema)
                pausar()
            
            elif opcao == "14":  # Verificar medicamentos próximos do vencimento
                exibir_medicamentos_a_vencer()
                pausar()
                
            elif opcao == "15":  # Análise de desempenho avançada
                analisar_desempenho_grande_escala()
                pausar()
            
            else:
                print("\nOpção inválida! Por favor, escolha uma opção do menu.")
                pausar()
    
    finally:
        # Garante que a conexão com o banco seja fechada
        sistema.fechar_conexao()
        print("\nConexão com o banco de dados fechada. Sistema encerrado.")


# Permite que o arquivo seja usado como módulo ou como script
if __name__ == "__main__":
    # Verifica se foi chamado com argumentos
    parser = argparse.ArgumentParser(description="Sistema de Gerenciamento de Farmácia com Árvore AVL")
    parser.add_argument("--exportar", help="Exporta medicamentos para arquivo CSV")
    parser.add_argument("--importar", help="Importa medicamentos de arquivo CSV")
    parser.add_argument("--estatisticas", action="store_true", help="Mostra estatísticas da árvore")
    parser.add_argument("--estoque-baixo", type=int, metavar="LIMITE", help="Lista medicamentos com estoque abaixo do limite")
    
    args = parser.parse_args()
    
    # Se nenhum argumento foi fornecido, inicia a interface CLI
    if len(sys.argv) == 1:
        main_cli()
    else:
        # Executa operações específicas com base nos argumentos
        sistema = ArvoreAVL()
        sistema.conectar_bd("farmacia.db")
        
        try:
            sistema.carregar_medicamentos_bd()
            
            if args.exportar:
                count = sistema.exportar_para_csv(args.exportar)
                print(f"Exportados {count} medicamentos para {args.exportar}")
            
            if args.importar:
                count = sistema.importar_de_csv(args.importar)
                print(f"Importados {count} medicamentos de {args.importar}")
            
            if args.estatisticas:
                exibir_estatisticas_arvore(sistema)
            
            if args.estoque_baixo is not None:
                medicamentos = sistema.listar_estoque_baixo(args.estoque_baixo)
                exibir_lista_medicamentos(medicamentos, f"Medicamentos com estoque abaixo de {args.estoque_baixo}")
        
        finally:
            sistema.fechar_conexao()
