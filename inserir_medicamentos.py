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

# Configuração de estoque por categoria (para gerar dados mais realistas)
# Define padrões de estoque específicos para cada categoria
ESTOQUE_POR_CATEGORIA = {
    "Analgésico": {"baixo": 0.05, "medio": 0.30, "alto": 0.50, "muito_alto": 0.15},  # Alto giro de estoque
    "Antibiótico": {"baixo": 0.15, "medio": 0.60, "alto": 0.20, "muito_alto": 0.05},  # Estoque controlado
    "Anti-inflamatório": {"baixo": 0.05, "medio": 0.35, "alto": 0.55, "muito_alto": 0.05},  # Alto giro
    "Antidepressivo": {"baixo": 0.10, "medio": 0.70, "alto": 0.15, "muito_alto": 0.05},  # Estoque estável
    "Anti-hipertensivo": {"baixo": 0.05, "medio": 0.70, "alto": 0.20, "muito_alto": 0.05},  # Uso contínuo
    "Antiácido": {"baixo": 0.20, "medio": 0.60, "alto": 0.15, "muito_alto": 0.05},  # Varia bastante
    "Antialérgico": {"baixo": 0.30, "medio": 0.50, "alto": 0.15, "muito_alto": 0.05},  # Sazonal, baixo agora
    "Vitamina": {"baixo": 0.05, "medio": 0.25, "alto": 0.50, "muito_alto": 0.20},  # Estoque alto
    "Hormônio": {"baixo": 0.15, "medio": 0.75, "alto": 0.08, "muito_alto": 0.02},  # Controlado
    "Antiviral": {"baixo": 0.40, "medio": 0.50, "alto": 0.08, "muito_alto": 0.02},  # Baixo estoque geral
    "Anticoagulante": {"baixo": 0.15, "medio": 0.75, "alto": 0.08, "muito_alto": 0.02},  # Controlado
    "Antidiabético": {"baixo": 0.10, "medio": 0.70, "alto": 0.15, "muito_alto": 0.05},  # Estável
    "Antifúngico": {"baixo": 0.25, "medio": 0.60, "alto": 0.10, "muito_alto": 0.05},  # Modesto
    "Antiparasitário": {"baixo": 0.30, "medio": 0.60, "alto": 0.08, "muito_alto": 0.02},  # Baixo estoque
    "Broncodilatador": {"baixo": 0.20, "medio": 0.60, "alto": 0.15, "muito_alto": 0.05},  # Moderado
    "Corticosteroide": {"baixo": 0.15, "medio": 0.70, "alto": 0.10, "muito_alto": 0.05},  # Controlado
    "Diurético": {"baixo": 0.10, "medio": 0.70, "alto": 0.15, "muito_alto": 0.05},  # Estável
    "Laxante": {"baixo": 0.05, "medio": 0.35, "alto": 0.40, "muito_alto": 0.20},  # Alto estoque
    "Relaxante muscular": {"baixo": 0.15, "medio": 0.60, "alto": 0.20, "muito_alto": 0.05},  # Moderado
    "Sedativo": {"baixo": 0.20, "medio": 0.70, "alto": 0.08, "muito_alto": 0.02},  # Controlado
}

# Padrão para categorias não especificadas
ESTOQUE_PADRAO = {"baixo": 0.15, "medio": 0.60, "alto": 0.20, "muito_alto": 0.05}

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
    """
    Gera uma data de validade, com uma pequena chance (5%) de ser nos próximos 3 meses
    """
    hoje = datetime.date.today()
    
    # 5% de chance para gerar uma data próxima da validade (dentro de 3 meses)
    if random.random() < 0.05:
        # Entre 0 e 90 dias para a validade
        dias_para_adicionar = random.randint(0, 90)
    else:
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

def gerar_quantidade(categoria: str) -> int:
    """
    Gera uma quantidade realista para o estoque baseado na categoria
    """
    # Obtém a distribuição de estoque para a categoria específica ou usa o padrão
    distribuicao = ESTOQUE_POR_CATEGORIA.get(categoria, ESTOQUE_PADRAO)
    
    # Determina a faixa de estoque com base na distribuição específica da categoria
    faixa = random.random()
    acumulado = 0
    
    # Estoque muito baixo/crítico (1-5) - chance específica por categoria
    acumulado += distribuicao["baixo"] * 0.33  # Um terço da probabilidade "baixo" é crítico
    if faixa < acumulado:
        return random.randint(1, 5)
    
    # Estoque baixo (6-20) - restante da probabilidade "baixo" + parte de "medio"
    acumulado += distribuicao["baixo"] * 0.67  # Dois terços da probabilidade "baixo" é baixo normal
    if faixa < acumulado:
        return random.randint(6, 20)
    
    # Estoque médio (21-100) - maior parte da probabilidade "medio"
    acumulado += distribuicao["medio"]
    if faixa < acumulado:
        return random.randint(21, 100)
    
    # Estoque alto (101-300) - probabilidade "alto"
    acumulado += distribuicao["alto"]
    if faixa < acumulado:
        return random.randint(101, 300)
    
    # Estoque muito alto (301-1000) - probabilidade "muito_alto"
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
        qtd = gerar_quantidade(categoria)  # Usa a categoria para determinar o padrão de estoque
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
    
    # Estatísticas de estoque por categoria
    print("\nDistribuição de estoque por categoria:")
    cursor.execute("""
        SELECT categoria, 
               AVG(quantidade) as media, 
               MIN(quantidade) as minimo, 
               MAX(quantidade) as maximo,
               SUM(quantidade) as total
        FROM medicamentos 
        GROUP BY categoria 
        ORDER BY AVG(quantidade) DESC
    """)
    
    estoque_por_categoria = cursor.fetchall()
    for cat, media, minimo, maximo, total in estoque_por_categoria:
        print(f"  {cat}: Média={media:.1f}, Min={minimo}, Max={maximo}, Total={total}")
    
    # Medicamentos próximos da validade
    hoje = datetime.date.today()
    tres_meses = hoje + datetime.timedelta(days=90)
    tres_meses_str = tres_meses.strftime("%Y-%m-%d")
    
    cursor.execute(f"""
        SELECT COUNT(*) FROM medicamentos 
        WHERE validade <= '{tres_meses_str}' AND validade >= '{hoje}'
    """)
    vencendo = cursor.fetchone()[0]
    
    print(f"\nMedicamentos vencendo nos próximos 3 meses: {vencendo} ({vencendo/total*100:.1f}%)")
    
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