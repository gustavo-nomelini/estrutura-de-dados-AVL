import streamlit as st
import sqlite3
import pandas as pd
import graphviz
from datetime import datetime
import os

# Importe a implementação da Árvore AVL
from sistema_farmacia_avl import ArvoreAVL, Medicamento, NoAVL


# Configuração do banco de dados SQLite
def inicializar_banco():
    """Cria o banco de dados e tabelas se não existirem"""
    conn = sqlite3.connect('farmacia.db')
    cursor = conn.cursor()
    
    # Criar tabela de medicamentos se não existir
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
    return conn


def carregar_arvore_do_banco():
    """Carrega os dados do SQLite para a árvore AVL"""
    conn = inicializar_banco()
    cursor = conn.cursor()
    
    # Consulta todos os medicamentos
    cursor.execute('SELECT codigo, nome, categoria, preco, quantidade, validade, fabricante FROM medicamentos')
    dados = cursor.fetchall()
    
    # Cria uma nova árvore
    arvore = ArvoreAVL()
    
    # Insere cada medicamento na árvore
    for med in dados:
        codigo, nome, categoria, preco, quantidade, validade, fabricante = med
        medicamento = Medicamento(codigo, nome, categoria, preco, quantidade, validade, fabricante)
        arvore.inserir(medicamento)
    
    conn.close()
    return arvore


def salvar_medicamento(medicamento):
    """Salva ou atualiza um medicamento no banco de dados"""
    conn = inicializar_banco()
    cursor = conn.cursor()
    
    # Atualiza data de modificação
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
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
    
    conn.commit()
    conn.close()
    return True


def remover_medicamento_banco(codigo):
    """Remove um medicamento do banco de dados"""
    conn = inicializar_banco()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM medicamentos WHERE codigo = ?', (codigo,))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_affected > 0


def buscar_medicamentos_banco(filtro=None, valor=None):
    """Busca medicamentos no banco com filtro opcional"""
    conn = inicializar_banco()
    cursor = conn.cursor()
    
    if filtro and valor:
        # Consulta com filtro
        if filtro == "codigo":
            cursor.execute('SELECT * FROM medicamentos WHERE codigo = ?', (valor,))
        elif filtro == "nome":
            cursor.execute('SELECT * FROM medicamentos WHERE nome LIKE ?', (f'%{valor}%',))
        elif filtro == "categoria":
            cursor.execute('SELECT * FROM medicamentos WHERE categoria LIKE ?', (f'%{valor}%',))
        else:
            cursor.execute('SELECT * FROM medicamentos')
    else:
        # Consulta todos
        cursor.execute('SELECT * FROM medicamentos')
    
    colunas = [desc[0] for desc in cursor.description]
    dados = cursor.fetchall()
    
    conn.close()
    
    # Converte para DataFrame
    df = pd.DataFrame(dados, columns=colunas)
    return df


# Funções para visualização da árvore AVL
def visualizar_arvore(arvore):
    """Cria uma visualização gráfica da árvore AVL"""
    if arvore.raiz is None:
        return None
    
    graph = graphviz.Digraph()
    
    def adicionar_nos(no, graph):
        if no is None:
            return
        
        # Adiciona o nó atual com fator de balanceamento
        fb = arvore._fator_balanceamento(no)
        node_label = f"{no.medicamento.codigo}\n{no.medicamento.nome[:10]}\nFB: {fb}"
        
        # Cores diferentes baseadas no fator de balanceamento
        if fb > 0:
            node_color = "lightblue"
        elif fb < 0:
            node_color = "lightgreen"
        else:
            node_color = "white"
        
        graph.node(str(no.medicamento.codigo), label=node_label, style="filled", fillcolor=node_color)
        
        # Adiciona conexões com os filhos
        if no.esquerda:
            graph.edge(str(no.medicamento.codigo), str(no.esquerda.medicamento.codigo))
            adicionar_nos(no.esquerda, graph)
        
        if no.direita:
            graph.edge(str(no.medicamento.codigo), str(no.direita.medicamento.codigo))
            adicionar_nos(no.direita, graph)
    
    adicionar_nos(arvore.raiz, graph)
    return graph


# Interface Streamlit
def main():
    st.set_page_config(page_title="Sistema de Farmácia AVL", 
                       page_icon="💊", 
                       layout="wide",
                       initial_sidebar_state="expanded")
    
    # Estilos CSS personalizados
    st.markdown("""
    <style>
    .reportview-container {
        background-color: #f0f2f6;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1, h2, h3 {
        color: #1e3d59;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .critical {
        color: red;
        font-weight: bold;
    }
    .warning {
        color: orange;
        font-weight: bold;
    }
    .normal {
        color: green;
    }
    </style>
    """, unsafe_allow_html=True)

    # Título e cabeçalho
    st.title("🏥 Sistema de Gerenciamento de Farmácia")
    st.subheader("Implementado com Árvore AVL, Streamlit e SQLite")
    
    # Inicializa a sessão se necessário
    if 'sistema' not in st.session_state:
        st.session_state.sistema = carregar_arvore_do_banco()
        st.session_state.mostrar_visualizacao = False
    
    # Barra lateral para navegação
    with st.sidebar:
        st.header("📋 Menu")
        pagina = st.radio("Selecione uma opção:", 
                          ["📊 Dashboard", 
                           "➕ Cadastrar Medicamento", 
                           "🔍 Buscar Medicamentos",
                           "📦 Gerenciar Estoque", 
                           "📈 Visualizar Árvore AVL"])
    
    # Páginas da aplicação
    if pagina == "📊 Dashboard":
        mostrar_dashboard()
    
    elif pagina == "➕ Cadastrar Medicamento":
        cadastrar_medicamento()
    
    elif pagina == "🔍 Buscar Medicamentos":
        buscar_medicamentos()
    
    elif pagina == "📦 Gerenciar Estoque":
        gerenciar_estoque()
    
    elif pagina == "📈 Visualizar Árvore AVL":
        mostrar_visualizacao_arvore()


def mostrar_dashboard():
    st.header("📊 Dashboard")
    
    # Estatísticas do sistema
    col1, col2, col3 = st.columns(3)
    
    total_medicamentos = st.session_state.sistema.tamanho_arvore()
    altura_arvore = st.session_state.sistema.altura_arvore()
    balanceada = st.session_state.sistema.verificar_balanceamento()
    
    with col1:
        st.metric("Total de Medicamentos", total_medicamentos)
    
    with col2:
        st.metric("Altura da Árvore AVL", altura_arvore)
    
    with col3:
        st.metric("Árvore Balanceada", "Sim" if balanceada else "Não")
    
    # Medicamentos com estoque crítico
    st.subheader("⚠️ Medicamentos com Estoque Crítico")
    estoque_critico = st.session_state.sistema.listar_estoque_baixo(10)
    
    if estoque_critico:
        df_critico = pd.DataFrame([{
            "Código": med.codigo,
            "Nome": med.nome,
            "Categoria": med.categoria,
            "Preço": f"R$ {med.preco:.2f}",
            "Estoque": med.quantidade,
            "Validade": med.validade
        } for med in estoque_critico])
        
        st.dataframe(df_critico.style.applymap(
            lambda x: 'color: red; font-weight: bold' if isinstance(x, int) and x < 5 else 
            'color: orange' if isinstance(x, int) and x < 10 else '',
            subset=['Estoque']
        ), use_container_width=True)
    else:
        st.info("Não há medicamentos com estoque crítico.")
    
    # Visualização simplificada dos dados
    st.subheader("📝 Resumo do Inventário")
    
    medicamentos = st.session_state.sistema.listar_todos()
    if medicamentos:
        # Converter para DataFrame
        df = pd.DataFrame([{
            "Código": med.codigo,
            "Nome": med.nome,
            "Categoria": med.categoria,
            "Preço": med.preco,
            "Estoque": med.quantidade
        } for med in medicamentos])
        
        # Análise por categoria
        if not df.empty:
            st.write("Quantidade de medicamentos por categoria:")
            categoria_count = df.groupby('Categoria').size().reset_index(name='Quantidade')
            st.bar_chart(categoria_count.set_index('Categoria'))
            
            # Valor total em estoque
            df['Valor Total'] = df['Preço'] * df['Estoque']
            valor_total = df['Valor Total'].sum()
            st.metric("Valor Total em Estoque", f"R$ {valor_total:.2f}")
    else:
        st.info("Não há medicamentos cadastrados.")


def cadastrar_medicamento():
    st.header("➕ Cadastrar Novo Medicamento")
    
    with st.form("cadastro_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            codigo = st.number_input("Código", min_value=1, step=1)
            nome = st.text_input("Nome do Medicamento")
            categoria = st.selectbox("Categoria", [
                "Analgésico", "Antibiótico", "Anti-inflamatório", 
                "Antidepressivo", "Anti-hipertensivo", "Antiácido",
                "Antialérgico", "Vitamina", "Outro"
            ])
            fabricante = st.text_input("Fabricante")
        
        with col2:
            preco = st.number_input("Preço (R$)", min_value=0.01, step=0.01, format="%.2f")
            quantidade = st.number_input("Quantidade em Estoque", min_value=0, step=1)
            validade = st.date_input("Data de Validade")
            validade_str = validade.strftime("%Y-%m-%d")
        
        submitted = st.form_submit_button("Cadastrar Medicamento")
        
        if submitted:
            if not nome:
                st.error("O nome do medicamento é obrigatório!")
                return
            
            # Verifica se já existe
            medicamento_existente = st.session_state.sistema.buscar(codigo)
            
            # Cria o objeto medicamento
            novo_med = Medicamento(codigo, nome, categoria, preco, quantidade, validade_str, fabricante)
            
            # Salva no banco e na árvore
            salvar_medicamento(novo_med)
            st.session_state.sistema.inserir(novo_med)
            
            if medicamento_existente:
                st.success(f"Medicamento {nome} (Código: {codigo}) atualizado com sucesso!")
            else:
                st.success(f"Medicamento {nome} (Código: {codigo}) cadastrado com sucesso!")
            
            # Mostra os detalhes do medicamento cadastrado
            st.write("**Detalhes do medicamento:**")
            st.json({
                "codigo": codigo,
                "nome": nome,
                "categoria": categoria,
                "preco": preco,
                "quantidade": quantidade,
                "validade": validade_str,
                "fabricante": fabricante
            })


def buscar_medicamentos():
    st.header("🔍 Buscar Medicamentos")
    
    # Opções de busca
    tipo_busca = st.radio(
        "Tipo de busca:",
        ["Por Código", "Por Intervalo de Código", "Por Faixa de Preço", "Todos os Medicamentos"]
    )
    
    if tipo_busca == "Por Código":
        codigo = st.number_input("Digite o código do medicamento:", min_value=1, step=1)
        if st.button("Buscar"):
            medicamento = st.session_state.sistema.buscar(codigo)
            if medicamento:
                st.success(f"Medicamento encontrado: {medicamento.nome}")
                exibir_detalhes_medicamento(medicamento)
            else:
                st.error(f"Medicamento com código {codigo} não encontrado.")
    
    elif tipo_busca == "Por Intervalo de Código":
        col1, col2 = st.columns(2)
        with col1:
            codigo_inicio = st.number_input("Código inicial:", min_value=1, step=1)
        with col2:
            codigo_fim = st.number_input("Código final:", min_value=codigo_inicio, step=1, value=codigo_inicio + 100)
        
        if st.button("Buscar por Intervalo"):
            medicamentos = st.session_state.sistema.buscar_por_intervalo(codigo_inicio, codigo_fim)
            exibir_lista_medicamentos(medicamentos, f"Medicamentos com código entre {codigo_inicio} e {codigo_fim}")
    
    elif tipo_busca == "Por Faixa de Preço":
        col1, col2 = st.columns(2)
        with col1:
            preco_min = st.number_input("Preço mínimo (R$):", min_value=0.0, step=0.01, format="%.2f")
        with col2:
            preco_max = st.number_input("Preço máximo (R$):", min_value=preco_min, step=0.01, value=preco_min + 50.0, format="%.2f")
        
        if st.button("Buscar por Faixa de Preço"):
            medicamentos = st.session_state.sistema.buscar_por_faixa_preco(preco_min, preco_max)
            exibir_lista_medicamentos(medicamentos, f"Medicamentos com preço entre R${preco_min:.2f} e R${preco_max:.2f}")
    
    else:  # Todos os Medicamentos
        if st.button("Listar Todos"):
            medicamentos = st.session_state.sistema.listar_todos()
            exibir_lista_medicamentos(medicamentos, "Todos os Medicamentos")
            
            # Exportar para CSV
            if medicamentos:
                df = pd.DataFrame([{
                    "Código": med.codigo,
                    "Nome": med.nome,
                    "Categoria": med.categoria,
                    "Preço": med.preco,
                    "Quantidade": med.quantidade,
                    "Validade": med.validade,
                    "Fabricante": med.fabricante
                } for med in medicamentos])
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Exportar para CSV",
                    csv,
                    "medicamentos.csv",
                    "text/csv",
                    key='download-csv'
                )


def gerenciar_estoque():
    st.header("📦 Gerenciar Estoque")
    
    tabs = st.tabs(["Atualizar Estoque", "Remover Medicamento", "Estoque Crítico"])
    
    with tabs[0]:  # Atualizar Estoque
        st.subheader("Atualização de Estoque")
        
        codigo = st.number_input("Código do Medicamento:", min_value=1, step=1, key="update_codigo")
        if st.button("Buscar Medicamento"):
            medicamento = st.session_state.sistema.buscar(codigo)
            if medicamento:
                st.session_state.med_para_atualizar = medicamento
                st.success(f"Medicamento encontrado: {medicamento.nome}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Estoque Atual:** {medicamento.quantidade} unidades")
                    nova_qtd = st.number_input("Nova Quantidade:", 
                                              min_value=0, 
                                              value=medicamento.quantidade, 
                                              step=1,
                                              key="nova_qtd")
                
                with col2:
                    st.write(f"**Preço Atual:** R$ {medicamento.preco:.2f}")
                    novo_preco = st.number_input("Novo Preço (R$):", 
                                               min_value=0.01, 
                                               value=float(medicamento.preco), 
                                               step=0.01,
                                               format="%.2f",
                                               key="novo_preco")
                
                if st.button("Atualizar Medicamento"):
                    # Atualiza o medicamento
                    medicamento.quantidade = nova_qtd
                    medicamento.preco = novo_preco
                    
                    # Salva no banco e na árvore
                    salvar_medicamento(medicamento)
                    st.session_state.sistema.inserir(medicamento)  # Isso atualizará o nó existente
                    
                    st.success(f"Medicamento {medicamento.nome} atualizado com sucesso!")
                    st.write("**Dados atualizados:**")
                    st.json({
                        "quantidade": nova_qtd,
                        "preco": novo_preco
                    })
            else:
                st.error(f"Medicamento com código {codigo} não encontrado.")
    
    with tabs[1]:  # Remover Medicamento
        st.subheader("Remover Medicamento")
        
        codigo_remover = st.number_input("Código do Medicamento a Remover:", min_value=1, step=1, key="remove_codigo")
        
        if st.button("Buscar para Remoção"):
            medicamento = st.session_state.sistema.buscar(codigo_remover)
            if medicamento:
                st.warning(f"⚠️ Você está prestes a remover: **{medicamento.nome}**")
                exibir_detalhes_medicamento(medicamento)
                
                if st.button("⚠️ Confirmar Remoção", key="confirm_remove"):
                    # Remove do banco de dados
                    removido_banco = remover_medicamento_banco(codigo_remover)
                    # Remove da árvore AVL
                    removido_arvore = st.session_state.sistema.remover(codigo_remover)
                    
                    if removido_arvore and removido_banco:
                        st.success(f"Medicamento {medicamento.nome} removido com sucesso!")
                    else:
                        st.error("Erro ao remover o medicamento. Tente novamente.")
            else:
                st.error(f"Medicamento com código {codigo_remover} não encontrado.")
    
    with tabs[2]:  # Estoque Crítico
        st.subheader("Medicamentos com Estoque Crítico")
        
        limite = st.slider("Limite de Estoque Crítico:", min_value=1, max_value=50, value=10)
        
        if st.button("Verificar Estoque Crítico"):
            medicamentos_criticos = st.session_state.sistema.listar_estoque_baixo(limite)
            if medicamentos_criticos:
                st.warning(f"Encontrados {len(medicamentos_criticos)} medicamentos com estoque abaixo de {limite} unidades.")
                exibir_lista_medicamentos(medicamentos_criticos, "Medicamentos com Estoque Crítico", 
                                         destaque_estoque=True, limite_critico=limite)
            else:
                st.success(f"Não há medicamentos com estoque abaixo de {limite} unidades.")


def mostrar_visualizacao_arvore():
    st.header("📈 Visualização da Árvore AVL")
    
    # Informações sobre a árvore
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Nós", st.session_state.sistema.tamanho_arvore())
    with col2:
        st.metric("Altura da Árvore", st.session_state.sistema.altura_arvore())
    with col3:
        balanceada = st.session_state.sistema.verificar_balanceamento()
        st.metric("Árvore Balanceada", "Sim" if balanceada else "Não")
    
    # Botão para atualizar visualização
    if st.button("Gerar Visualização da Árvore"):
        if st.session_state.sistema.tamanho_arvore() > 0:
            st.info("Gerando visualização da árvore AVL. Isso pode levar alguns segundos para árvores maiores...")
            
            # Gera o gráfico da árvore
            graph = visualizar_arvore(st.session_state.sistema)
            
            if graph:
                st.graphviz_chart(graph)
                
                # Legenda
                st.write("**Legenda:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("🟦 **Azul**: FB > 0 (mais pesado à esquerda)")
                with col2:
                    st.markdown("🟩 **Verde**: FB < 0 (mais pesado à direita)")
                with col3:
                    st.markdown("⬜ **Branco**: FB = 0 (perfeitamente balanceado)")
                
                # Explicação dos fatores de balanceamento
                with st.expander("ℹ️ Sobre Fatores de Balanceamento"):
                    st.write("""
                    O **Fator de Balanceamento (FB)** é a diferença entre a altura da subárvore esquerda e a altura da subárvore direita.
                    
                    - **FB > 0**: A subárvore esquerda é mais alta
                    - **FB < 0**: A subárvore direita é mais alta
                    - **FB = 0**: As subárvores têm a mesma altura
                    
                    Na árvore AVL, o fator de balanceamento de qualquer nó deve estar entre -1 e +1. 
                    Quando uma operação de inserção ou remoção deixa um nó com FB fora desse intervalo, 
                    são realizadas rotações para reequilibrar a árvore.
                    """)
            else:
                st.error("Não foi possível gerar a visualização.")
        else:
            st.warning("A árvore está vazia. Adicione medicamentos para visualizar a estrutura.")
    
    # Teste de desempenho da árvore
    with st.expander("🧪 Teste de Desempenho da Árvore AVL"):
        st.write("""
        Este teste demonstra a eficiência da árvore AVL em comparação com uma busca sequencial.
        Veremos a velocidade de busca de um medicamento na árvore atual.
        """)
        
        if st.session_state.sistema.tamanho_arvore() > 0:
            # Pega um medicamento aleatório para buscar
            import random
            medicamentos = st.session_state.sistema.listar_todos()
            if medicamentos:
                med_aleatorio = random.choice(medicamentos)
                
                if st.button("Executar Teste de Busca"):
                    import time
                    
                    # Teste da Árvore AVL
                    inicio = time.time()
                    resultado_avl = st.session_state.sistema.buscar(med_aleatorio.codigo)
                    tempo_avl = (time.time() - inicio) * 1000  # em ms
                    
                    # Simula busca sequencial
                    inicio = time.time()
                    resultado_seq = None
                    for med in medicamentos:
                        if med.codigo == med_aleatorio.codigo:
                            resultado_seq = med
                            break
                    tempo_seq = (time.time() - inicio) * 1000  # em ms
                    
                    # Exibe resultados
                    st.write(f"**Medicamento buscado:** {med_aleatorio.nome} (Código: {med_aleatorio.codigo})")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Tempo de Busca na Árvore AVL", f"{tempo_avl:.6f} ms")
                        st.write(f"Altura da árvore: {st.session_state.sistema.altura_arvore()}")
                    
                    with col2:
                        st.metric("Tempo de Busca Sequencial", f"{tempo_seq:.6f} ms")
                        st.write(f"Número de comparações: até {len(medicamentos)}")
                    
                    # Comparação
                    if tempo_avl < tempo_seq:
                        speedup = tempo_seq / tempo_avl
                        st.success(f"A árvore AVL foi {speedup:.1f}x mais rápida que a busca sequencial!")
                    else:
                        st.info("Para poucos elementos, a diferença pode não ser significativa devido a otimizações do Python.")


# Funções auxiliares para exibição
def exibir_detalhes_medicamento(medicamento):
    """Exibe os detalhes de um medicamento específico"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Nome:** {medicamento.nome}")
        st.write(f"**Código:** {medicamento.codigo}")
        st.write(f"**Categoria:** {medicamento.categoria}")
        st.write(f"**Fabricante:** {medicamento.fabricante or 'Não informado'}")
    
    with col2:
        if medicamento.quantidade < 5:
            st.write(f"**Estoque:** <span class='critical'>{medicamento.quantidade} unidades</span>", unsafe_allow_html=True)
        elif medicamento.quantidade < 10:
            st.write(f"**Estoque:** <span class='warning'>{medicamento.quantidade} unidades</span>", unsafe_allow_html=True)
        else:
            st.write(f"**Estoque:** <span class='normal'>{medicamento.quantidade} unidades</span>", unsafe_allow_html=True)
        
        st.write(f"**Preço:** R$ {medicamento.preco:.2f}")
        st.write(f"**Validade:** {medicamento.validade}")


def exibir_lista_medicamentos(medicamentos, titulo, destaque_estoque=False, limite_critico=10):
    """Exibe uma lista de medicamentos em forma de tabela"""
    if medicamentos:
        st.subheader(titulo)
        st.write(f"Total de itens: {len(medicamentos)}")
        
        # Converte para DataFrame
        df = pd.DataFrame([{
            "Código": med.codigo,
            "Nome": med.nome,
            "Categoria": med.categoria,
            "Preço": f"R$ {med.preco:.2f}",
            "Estoque": med.quantidade,
            "Validade": med.validade
        } for med in medicamentos])
        
        # Adiciona estilo com destaque para estoque crítico
        if destaque_estoque:
            def highlight_estoque(val):
                if isinstance(val, int):
                    if val < 5:
                        return 'background-color: red; color: white'
                    elif val < limite_critico:
                        return 'background-color: orange'
                return ''
            
            st.dataframe(df.style.applymap(highlight_estoque, subset=['Estoque']), use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    else:
        st.info(f"Nenhum medicamento encontrado para: {titulo}")


# Executa a aplicação
if __name__ == "__main__":
    main()
