import random
import datetime
import sqlite3
from typing import List, Dict
import os
from sistema_farmacia_avl import ArvoreAVL, Medicamento

# Dados de exemplo para gerar medicamentos realistas
CATEGORIAS = [
    "Analgésico", "Antibiótico", "Anti-inflamatório", "Antidepressivo", 
    "Anti-hipertensivo", "Antiácido", "Antialérgico", "Vitamina", 
    "Hormônio", "Antiviral", "Anticoagulante", "Antidiabético",
    "Antifúngico", "Antiparasitário", "Broncodilatador", "Corticosteroide",
    "Diurético", "Laxante", "Relaxante muscular", "Sedativo"
]

FABRICANTES = [
    "EMS", "Medley", "Neo Química", "Eurofarma", "Aché", "Cimed", 
    "Novartis", "Pfizer", "Sanofi", "Bayer", "GSK", "Roche",
    "Merck", "Teuto", "Hypera Pharma", "União Química", "Cristália",
    "Boehringer", "Libbs", "Biolab"
]

# Prefixos e sufixos para nomes de medicamentos
PREFIXOS = [
    "Neo", "Max", "Ultra", "Super", "Pro", "Bio", "Flex", "Vita", 
    "Cardio", "Dor", "Gastro", "Hepato", "Neuro", "Dermato", "Oto",
    "Oftalmo", "Gino", "Andro", "Pneu", "Hemo"
]

RADICAIS = [
    "cet", "cin", "dol", "cox", "pril", "sartan", "statina", "vir", 
    "cilina", "micina", "zepam", "dipina", "feno", "tiazida", "xetina",
    "tropium", "vastatin", "codona", "gliptina", "lutamida"
]

SUFIXOS = [
    "ol", "ex", "in", "al", "il", "an", "ium", "ax", "on", "en",
    "ix", "ase", "yl", "at", "id", "ar", "ine", "one", "ate", "ium"
]

def gerar_nome_medicamento() -> str:
    """Gera um nome realista para medicamento"""
    
    # Estilo 1: Prefixo + Radical + Sufixo
    if random.random() < 0.7:
        prefixo = random.choice(PREFIXOS)
        radical = random.choice(RADICAIS)
        sufixo = random.choice(SUFIXOS)
        return f"{prefixo}{radical}{sufixo}"
    
    # Estilo 2: Radical + Sufixo + Número
    else:
        radical = random.choice(RADICAIS)
        sufixo = random.choice(SUFIXOS)
        numero = random.choice(["", " " + str(random.randint(1, 100))])
        return f"{radical.capitalize()}{sufixo}{numero}"

def gerar_data_validade() -> str:
    """Gera uma data de validade futura no formato YYYY-MM-DD"""
    hoje = datetime.date.today()
    # Medicamentos geralmente têm validade de 1 a 5 anos
    dias_para_adicionar = random.randint(365, 365 * 5)
    data_validade = hoje + datetime.timedelta(days=dias_para_adicionar)
    return data_validade.strftime("%Y-%m-%d")

def gerar_preco() -> float:
    """Gera um preço realista para medicamento"""
    # Diferentes faixas de preço com probabilidades diferentes
    faixa = random.random()
    
    if faixa < 0.4:  # 40% dos medicamentos entre R$5 e R$30
        return round(random.uniform(5.0, 30.0), 2)
    elif faixa < 0.7:  # 30% dos medicamentos entre R$30 e R$100
        return round(random.uniform(30.0, 100.0), 2)
    elif faixa < 0.9:  # 20% dos medicamentos entre R$100 e R$300
        return round(random.uniform(100.0, 300.0), 2)
    else:  # 10% dos medicamentos caros, entre R$300 e R$1000
        return round(random.uniform(300.0, 1000.0), 2)

def gerar_quantidade() -> int:
    """Gera uma quantidade realista para o estoque"""
    # Diferentes padrões de estoque
    padrao = random.random()
    
    if padrao < 0.05:  # 5% com estoque muito baixo (1-5)
        return random.randint(1, 5)
    elif padrao < 0.15:  # 10% com estoque baixo (6-20)
        return random.randint(6, 20)
    elif padrao < 0.65:  # 50% com estoque médio (21-100)
        return random.randint(21, 100)
    elif padrao < 0.90:  # 25% com estoque alto (101-300)
        return random.randint(101, 300)
    else:  # 10% com estoque muito alto (301-1000)
        return random.randint(301, 1000)

def obter_proximo_id_disponivel(db_path: str) -> int:
    """Obtém o próximo ID disponível no banco de dados"""
    try:
        # Verifica se o banco de dados existe
        if not os.path.exists(db_path):
            return 1  # Banco não existe, começar do ID 1
            
        # Conecta ao banco e busca o maior ID
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(codigo) FROM medicamentos")
        resultado = cursor.fetchone()[0]
        conn.close()
        
        if resultado is None:
            return 1  # Tabela vazia, começar do ID 1
        else:
            return resultado + 1  # Próximo ID após o maior existente
    except:
        # Em caso de erro, começar do ID 1
        return 1

def gerar_medicamentos(quantidade: int = 1000, id_inicial: int = 1) -> List[Medicamento]:
    """Gera uma lista com a quantidade especificada de medicamentos com IDs sequenciais"""
    medicamentos = []
    
    print(f"Gerando {quantidade} medicamentos começando do ID {id_inicial}...")
    
    for i in range(quantidade):
        # ID sequencial
        codigo = id_inicial + i
        
        nome = gerar_nome_medicamento()
        categoria = random.choice(CATEGORIAS)
        preco = gerar_preco()
        qtd = gerar_quantidade()
        validade = gerar_data_validade()
        fabricante = random.choice(FABRICANTES)
        
        medicamento = Medicamento(codigo, nome, categoria, preco, qtd, validade, fabricante)
        medicamentos.append(medicamento)
    
    return medicamentos

def inserir_medicamentos_em_massa(quantidade: int = 1000, db_path: str = "farmacia.db"):
    """Insere a quantidade especificada de medicamentos no banco de dados com IDs sequenciais"""
    
    # Determina o ID inicial para a sequência
    id_inicial = obter_proximo_id_disponivel(db_path)
    print(f"ID inicial para inserção: {id_inicial}")
    
    # Cria ou conecta ao banco de dados
    conexao_direta = False
    
    try:
        # Tenta usar a árvore AVL
        sistema = ArvoreAVL()
        sistema.conectar_bd(db_path)
        print("Usando ArvoreAVL para inserção em massa...")
    except Exception as e:
        # Se falhar, conecta diretamente ao SQLite
        print(f"Não foi possível usar ArvoreAVL: {e}")
        print("Conectando diretamente ao SQLite...")
        conexao_direta = True
        
        # Verifica se o diretório existe
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Cria a tabela se não existir
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
        conn.commit()
    
    # Gera os medicamentos com IDs sequenciais
    medicamentos = gerar_medicamentos(quantidade, id_inicial)
    
    # Mostra alguns exemplos
    print("\nExemplos de medicamentos gerados:")
    for i in range(min(5, len(medicamentos))):
        print(f"{i+1}. {medicamentos[i]}")
    
    # Insere os medicamentos
    print(f"\nInserindo {len(medicamentos)} medicamentos no banco de dados...")
    
    if conexao_direta:
        # Inserção direta via SQLite
        data_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        count = 0
        
        try:
            # Usa transação para maior eficiência
            cursor.execute("BEGIN TRANSACTION")
            
            for med in medicamentos:
                cursor.execute('''
                INSERT OR REPLACE INTO medicamentos 
                (codigo, nome, categoria, preco, quantidade, validade, fabricante, data_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (med.codigo, med.nome, med.categoria, med.preco, 
                      med.quantidade, med.validade, med.fabricante, data_atual))
                count += 1
                
                # Feedback a cada 100 inserções
                if count % 100 == 0:
                    print(f"Progresso: {count}/{len(medicamentos)} medicamentos inseridos")
            
            cursor.execute("COMMIT")
            print(f"Concluído! {count} medicamentos inseridos com sucesso.")
            print(f"Faixa de IDs inseridos: {id_inicial} a {id_inicial + count - 1}")
        
        except Exception as e:
            cursor.execute("ROLLBACK")
            print(f"Erro durante a inserção: {e}")
        
        finally:
            conn.close()
    
    else:
        # Inserção via ArvoreAVL
        count = 0
        try:
            for med in medicamentos:
                sistema.inserir(med)
                count += 1
                
                # Feedback a cada 100 inserções
                if count % 100 == 0:
                    print(f"Progresso: {count}/{len(medicamentos)} medicamentos inseridos")
            
            print(f"Concluído! {count} medicamentos inseridos com sucesso.")
            print(f"Faixa de IDs inseridos: {id_inicial} a {id_inicial + count - 1}")
        
        except Exception as e:
            print(f"Erro durante a inserção: {e}")
        
        finally:
            sistema.fechar_conexao()

def visualizar_estatisticas_medicamentos(db_path: str = "farmacia.db"):
    """Exibe estatísticas dos medicamentos no banco de dados"""
    
    # Conecta ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total de medicamentos
    cursor.execute("SELECT COUNT(*) FROM medicamentos")
    total = cursor.fetchone()[0]
    print(f"\nEstatísticas do banco de dados '{db_path}':")
    print(f"Total de medicamentos: {total}")
    
    # Faixa de IDs
    cursor.execute("SELECT MIN(codigo), MAX(codigo) FROM medicamentos")
    min_id, max_id = cursor.fetchone()
    print(f"Faixa de IDs: {min_id} a {max_id}")
    
    # Distribuição por categoria
    cursor.execute("SELECT categoria, COUNT(*) FROM medicamentos GROUP BY categoria ORDER BY COUNT(*) DESC")
    categorias = cursor.fetchall()
    
    print("\nDistribuição por categoria:")
    for cat, count in categorias:
        print(f"  {cat}: {count} ({count/total*100:.1f}%)")
    
    # Faixas de preço
    cursor.execute("SELECT COUNT(*) FROM medicamentos WHERE preco <= 30")
    baixo = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM medicamentos WHERE preco > 30 AND preco <= 100")
    medio = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM medicamentos WHERE preco > 100 AND preco <= 300")
    alto = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM medicamentos WHERE preco > 300")
    muito_alto = cursor.fetchone()[0]
    
    print("\nDistribuição por faixa de preço:")
    print(f"  Até R$30,00: {baixo} ({baixo/total*100:.1f}%)")
    print(f"  R$30,01 a R$100,00: {medio} ({medio/total*100:.1f}%)")
    print(f"  R$100,01 a R$300,00: {alto} ({alto/total*100:.1f}%)")
    print(f"  Acima de R$300,00: {muito_alto} ({muito_alto/total*100:.1f}%)")
    
    # Estoque crítico
    cursor.execute("SELECT COUNT(*) FROM medicamentos WHERE quantidade <= 10")
    critico = cursor.fetchone()[0]
    
    print(f"\nMedicamentos com estoque crítico (<=10): {critico} ({critico/total*100:.1f}%)")
    
    # Valor total em estoque
    cursor.execute("SELECT SUM(preco * quantidade) FROM medicamentos")
    valor_total = cursor.fetchone()[0]
    
    print(f"Valor total em estoque: R$ {valor_total:,.2f}")
    
    conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerador de medicamentos para o sistema de farmácia")
    parser.add_argument("-q", "--quantidade", type=int, default=1000, 
                        help="Quantidade de medicamentos a gerar (padrão: 1000)")
    parser.add_argument("-d", "--database", type=str, default="farmacia.db", 
                        help="Caminho para o banco de dados (padrão: farmacia.db)")
    parser.add_argument("-s", "--stats", action="store_true", 
                        help="Mostrar estatísticas após a inserção")
    parser.add_argument("-r", "--reset", action="store_true",
                        help="Limpar banco de dados e começar IDs do 1")
    
    args = parser.parse_args()
    
    print("\n=== GERADOR DE MEDICAMENTOS COM IDs SEQUENCIAIS ===")
    
    # Opção para limpar o banco e começar do 1
    if args.reset and os.path.exists(args.database):
        confirm = input(f"Isso apagará TODOS os dados em '{args.database}'. Confirmar? (s/n): ")
        if confirm.lower() == 's':
            try:
                os.remove(args.database)
                print(f"Banco de dados '{args.database}' removido. IDs começarão do 1.")
            except Exception as e:
                print(f"Erro ao remover banco: {e}")
    
    print(f"Inserindo {args.quantidade} medicamentos em '{args.database}'...")
    inserir_medicamentos_em_massa(args.quantidade, args.database)
    
    if args.stats:
        visualizar_estatisticas_medicamentos(args.database)
    
    print("\nProcesso concluído!")