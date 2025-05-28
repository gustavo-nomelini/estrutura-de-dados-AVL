import streamlit as st
import sqlite3
import pandas as pd
import graphviz
from datetime import datetime
import os
import time
import random
import matplotlib.pyplot as plt
import numpy as np
import altair as alt

# Aumenta o limite de células renderizáveis pelo Pandas Styler
pd.set_option("styler.render.max_elements", 500000)

# Importe a implementação da Árvore AVL
from sistema_farmacia_avl import ArvoreAVL, Medicamento, NoAVL, formatar_moeda, simular_busca_lista_encadeada


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
        arvore.inserir(medicamento, salvar_bd=False)
    
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
        color: red !important;
        font-weight: bold !important;
    }
    .warning {
        color: orange !important;
        font-weight: bold !important;
    }
    .normal {
        color: green !important;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
    }
    </style>
    """, unsafe_allow_html=True)

    # Título e cabeçalho
    st.title("🏥 Sistema de Gerenciamento de Farmácia")
    st.markdown("### Implementado com Árvore AVL - Estrutura de Dados Avançada")
    
    # Inicializa a sessão se necessário
    if 'sistema' not in st.session_state:
        st.session_state.sistema = carregar_arvore_do_banco()
        st.session_state.mostrar_visualizacao = False
    
    # Barra lateral para navegação
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2037/2037448.png", width=100)
        st.header("📋 Menu")
        pagina = st.radio("Selecione uma opção:", 
                          ["📊 Dashboard", 
                           "➕ Cadastrar Medicamento", 
                           "🔍 Buscar Medicamentos",
                           "📦 Gerenciar Estoque", 
                           "📈 Visualizar Árvore AVL",
                           "⚡ Comparativo AVL vs Lista"])
        
        # Informações da árvore no sidebar
        st.divider()
        st.caption("INFORMAÇÕES DA ÁRVORE AVL")
        st.metric("Total de Medicamentos", st.session_state.sistema.tamanho_arvore())
        st.metric("Altura da Árvore", st.session_state.sistema.altura_arvore())
        st.metric("Balanceada", "✓ Sim" if st.session_state.sistema.verificar_balanceamento() else "✗ Não")
        
        # Botão para recarregar dados
        if st.button("🔄 Recarregar Dados"):
            st.session_state.sistema = carregar_arvore_do_banco()
            st.success("Dados recarregados com sucesso!")
            st.experimental_rerun()
    
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
        
    elif pagina == "⚡ Comparativo AVL vs Lista":
        mostrar_comparativo_estruturas()


def mostrar_dashboard():
    st.header("📊 Dashboard")
    
    # Estatísticas do sistema
    medicamentos = st.session_state.sistema.listar_todos()
    
    if not medicamentos:
        st.warning("Não há medicamentos cadastrados. Utilize o menu para adicionar medicamentos.")
        return
    
    # Métricas principais
    total_estoque = sum(med.quantidade for med in medicamentos)
    valor_total = sum(med.preco * med.quantidade for med in medicamentos)
    estoque_baixo = len([m for m in medicamentos if m.quantidade < 10])
    estoque_critico = len([m for m in medicamentos if m.quantidade < 5])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(medicamentos)}</div>
            <div class="metric-label">Medicamentos Cadastrados</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_estoque}</div>
            <div class="metric-label">Itens em Estoque</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #16a085;">{formatar_moeda(valor_total)}</div>
            <div class="metric-label">Valor em Estoque</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {'red' if estoque_critico > 0 else 'green'};">{estoque_critico}</div>
            <div class="metric-label">Itens com Estoque Crítico</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Medicamentos com estoque crítico
    st.subheader("⚠️ Medicamentos com Estoque Crítico")
    estoque_critico_meds = st.session_state.sistema.listar_estoque_baixo(5)
    
    if estoque_critico_meds:
        df_critico = pd.DataFrame([{
            "Código": med.codigo,
            "Nome": med.nome,
            "Categoria": med.categoria,
            "Preço": f"R$ {med.preco:.2f}",
            "Estoque": med.quantidade,
            "Validade": med.validade
        } for med in estoque_critico_meds])
        
        # Usando .map em vez de .applymap (que está obsoleto)
        def highlight_estoque(s):
            return ['color: red; font-weight: bold' if v < 5 else 
                    'color: orange' if v < 10 else '' for v in s]
        
        styled_df = df_critico.style.apply(highlight_estoque, subset=['Estoque'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.success("Não há medicamentos com estoque crítico. Parabéns!")
    
    # Análises gráficas
    st.subheader("📈 Análise de Dados")
    
    tab1, tab2, tab3 = st.tabs(["Categorias", "Estoque", "Valor"])
    
    with tab1:
        # Análise por categoria
        if medicamentos:
            # Converter para DataFrame para análise
            df = pd.DataFrame([med.to_dict() for med in medicamentos])
            
            # Contagem por categoria
            cat_count = df['categoria'].value_counts().reset_index()
            cat_count.columns = ['Categoria', 'Quantidade']
            
            # Gráfico com Altair
            chart = alt.Chart(cat_count).mark_bar().encode(
                x=alt.X('Categoria:N', sort='-y'),
                y='Quantidade:Q',
                color=alt.Color('Categoria:N', legend=None),
                tooltip=['Categoria', 'Quantidade']
            ).properties(
                title='Medicamentos por Categoria',
                height=300
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
    
    with tab2:
        # Distribuição de estoque
        if medicamentos:
            # Criar categorias de estoque
            def categorizar_estoque(qtd):
                if qtd < 5:
                    return 'Crítico (<5)'
                elif qtd < 10:
                    return 'Baixo (5-9)'
                elif qtd < 20:
                    return 'Moderado (10-19)'
                elif qtd < 50:
                    return 'Bom (20-49)'
                else:
                    return 'Ótimo (50+)'
            
            df['estoque_cat'] = df['quantidade'].apply(categorizar_estoque)
            estoque_dist = df['estoque_cat'].value_counts().reset_index()
            estoque_dist.columns = ['Categoria', 'Quantidade']
            
            # Ordem personalizada para as categorias
            ordem = ['Crítico (<5)', 'Baixo (5-9)', 'Moderado (10-19)', 'Bom (20-49)', 'Ótimo (50+)']
            estoque_dist['Categoria'] = pd.Categorical(estoque_dist['Categoria'], 
                                                     categories=ordem, 
                                                     ordered=True)
            estoque_dist = estoque_dist.sort_values('Categoria')
            
            # Cores para cada categoria
            cores = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#27ae60']
            
            # Gráfico com Altair
            chart = alt.Chart(estoque_dist).mark_bar().encode(
                x=alt.X('Categoria:N', sort=ordem),
                y='Quantidade:Q',
                color=alt.Color('Categoria:N', scale=alt.Scale(domain=ordem, range=cores)),
                tooltip=['Categoria', 'Quantidade']
            ).properties(
                title='Distribuição de Níveis de Estoque',
                height=300
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
    
    with tab3:
        # Valor por categoria
        if medicamentos:
            # Calcular valor total por categoria
            df['valor_total'] = df['preco'] * df['quantidade']
            valor_por_cat = df.groupby('categoria')['valor_total'].sum().reset_index()
            valor_por_cat.columns = ['Categoria', 'Valor Total']
            valor_por_cat = valor_por_cat.sort_values('Valor Total', ascending=False)
            
            # Adicionar formatação de moeda
            valor_por_cat['Valor Formatado'] = valor_por_cat['Valor Total'].apply(
                lambda x: f"R$ {x:.2f}"
            )
            
            # Gráfico com Altair
            chart = alt.Chart(valor_por_cat).mark_bar().encode(
                x=alt.X('Categoria:N', sort='-y'),
                y=alt.Y('Valor Total:Q', axis=alt.Axis(format='$,.2f')),
                color=alt.Color('Categoria:N', legend=None),
                tooltip=['Categoria', 'Valor Formatado']
            ).properties(
                title='Valor Total em Estoque por Categoria',
                height=300
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
    
    # Medicamentos próximos da validade
    st.subheader("📅 Medicamentos com Validade Próxima")
    
    hoje = datetime.now().date()
    medicamentos_validade = []
    
    for med in medicamentos:
        try:
            data_validade = datetime.strptime(med.validade, "%Y-%m-%d").date()
            dias_ate_vencer = (data_validade - hoje).days
            
            if dias_ate_vencer <= 90:  # Próximos 3 meses
                medicamentos_validade.append({
                    "Código": med.codigo,
                    "Nome": med.nome,
                    "Categoria": med.categoria,
                    "Estoque": med.quantidade,
                    "Validade": med.validade,
                    "Dias até vencer": dias_ate_vencer
                })
        except:
            pass
    
    if medicamentos_validade:
        df_validade = pd.DataFrame(medicamentos_validade)
        df_validade = df_validade.sort_values("Dias até vencer")
        
        # Destacar por proximidade do vencimento
        def highlight_validade(val):
            if isinstance(val, int):
                if val < 0:
                    return 'background-color: darkred; color: white'
                elif val <= 30:
                    return 'background-color: red; color: white'
                elif val <= 60:
                    return 'background-color: orange; color: black'
                elif val <= 90:
                    return 'background-color: yellow; color: black'
            return ''
            
        styled_df = df_validade.style.map(highlight_validade, subset=['Dias até vencer'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("Não há medicamentos com vencimento nos próximos 3 meses.")


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
                "Antialérgico", "Vitamina", "Hormônio", "Controlado", "Outro"
            ])
            fabricante = st.text_input("Fabricante")
        
        with col2:
            preco = st.number_input("Preço (R$)", min_value=0.01, step=0.01, format="%.2f")
            quantidade = st.number_input("Quantidade em Estoque", min_value=0, step=1)
            validade = st.date_input("Data de Validade")
            validade_str = validade.strftime("%Y-%m-%d")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Salvar Medicamento", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
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
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Detalhes do Medicamento")
                st.write(f"**Nome:** {nome}")
                st.write(f"**Código:** {codigo}")
                st.write(f"**Categoria:** {categoria}")
                st.write(f"**Fabricante:** {fabricante or 'Não informado'}")
            
            with col2:
                st.write(f"**Preço:** {formatar_moeda(preco)}")
                
                # Estoque com cor baseada no nível
                if quantidade < 5:
                    st.markdown(f"**Estoque:** <span class='critical'>{quantidade} unidades (CRÍTICO)</span>", unsafe_allow_html=True)
                elif quantidade < 10:
                    st.markdown(f"**Estoque:** <span class='warning'>{quantidade} unidades (BAIXO)</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**Estoque:** <span class='normal'>{quantidade} unidades</span>", unsafe_allow_html=True)
                
                st.write(f"**Validade:** {validade_str}")
                
                # Valor em estoque
                valor_estoque = preco * quantidade
                st.write(f"**Valor em estoque:** {formatar_moeda(valor_estoque)}")


def buscar_medicamentos():
    st.header("🔍 Buscar Medicamentos")
    
    # Opções de busca em tabs
    tabs = st.tabs(["Por Código", "Por Intervalo", "Por Preço", "Por Nome/Categoria", "Todos"])
    
    # Tab 1: Busca por código
    with tabs[0]:
        st.subheader("Busca por Código")
        codigo = st.number_input("Digite o código do medicamento:", min_value=1, step=1, key="codigo_busca")
        if st.button("🔎 Buscar", key="btn_busca_codigo"):
            medicamento = st.session_state.sistema.buscar(codigo)
            if medicamento:
                st.success(f"✅ Medicamento encontrado: {medicamento.nome}")
                exibir_detalhes_medicamento(medicamento)
            else:
                st.error(f"❌ Medicamento com código {codigo} não encontrado.")
    
    # Tab 2: Busca por intervalo de códigos
    with tabs[1]:
        st.subheader("Busca por Intervalo de Códigos")
        col1, col2 = st.columns(2)
        with col1:
            codigo_inicio = st.number_input("Código inicial:", min_value=1, step=1, key="codigo_inicio")
        with col2:
            codigo_fim = st.number_input("Código final:", min_value=codigo_inicio, step=1, 
                                       value=min(codigo_inicio + 100, 9999), key="codigo_fim")
        
        if st.button("🔎 Buscar por Intervalo", key="btn_busca_intervalo"):
            medicamentos = st.session_state.sistema.buscar_por_intervalo(codigo_inicio, codigo_fim)
            exibir_lista_medicamentos(medicamentos, f"Medicamentos com código entre {codigo_inicio} e {codigo_fim}")
    
    # Tab 3: Busca por faixa de preço
    with tabs[2]:
        st.subheader("Busca por Faixa de Preço")
        col1, col2 = st.columns(2)
        with col1:
            preco_min = st.number_input("Preço mínimo (R$):", min_value=0.0, step=0.01, format="%.2f", key="preco_min")
        with col2:
            preco_max = st.number_input("Preço máximo (R$):", min_value=preco_min, step=0.01, 
                                      value=preco_min + 50.0, format="%.2f", key="preco_max")
        
        if st.button("🔎 Buscar por Preço", key="btn_busca_preco"):
            medicamentos = st.session_state.sistema.buscar_por_faixa_preco(preco_min, preco_max)
            exibir_lista_medicamentos(medicamentos, f"Medicamentos com preço entre {formatar_moeda(preco_min)} e {formatar_moeda(preco_max)}")
    
    # Tab 4: Busca por nome ou categoria
    with tabs[3]:
        st.subheader("Busca por Nome ou Categoria")
        tipo_busca = st.radio("Tipo de busca:", ["Nome", "Categoria"], horizontal=True, key="tipo_busca_texto")
        
        if tipo_busca == "Nome":
            nome = st.text_input("Digite o nome (ou parte do nome) do medicamento:", key="nome_busca")
            if st.button("🔎 Buscar por Nome", key="btn_busca_nome"):
                if nome:
                    medicamentos = st.session_state.sistema.buscar_por_nome(nome)
                    exibir_lista_medicamentos(medicamentos, f"Medicamentos contendo '{nome}' no nome")
                else:
                    st.warning("Digite um nome para buscar.")
        else:
            categoria = st.selectbox("Selecione a categoria:", [
                "Analgésico", "Antibiótico", "Anti-inflamatório", 
                "Antidepressivo", "Anti-hipertensivo", "Antiácido",
                "Antialérgico", "Vitamina", "Hormônio", "Controlado", "Outro"
            ], key="categoria_busca")
            if st.button("🔎 Buscar por Categoria", key="btn_busca_categoria"):
                medicamentos = st.session_state.sistema.buscar_por_categoria(categoria)
                exibir_lista_medicamentos(medicamentos, f"Medicamentos da categoria '{categoria}'")
    
    # Tab 5: Listar todos
    with tabs[4]:
        st.subheader("Todos os Medicamentos")
        if st.button("📋 Listar Todos os Medicamentos", key="btn_listar_todos"):
            medicamentos = st.session_state.sistema.listar_todos()
            exibir_lista_medicamentos(medicamentos, "Todos os Medicamentos")
            
            # Exportar para CSV se houver dados
            if medicamentos:
                df = pd.DataFrame([{
                    "Código": med.codigo,
                    "Nome": med.nome,
                    "Categoria": med.categoria,
                    "Preço": med.preco,
                    "Quantidade": med.quantidade,
                    "Validade": med.validade,
                    "Fabricante": med.fabricante or ""
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
        if st.button("🔍 Buscar para Atualização", key="busca_atualizacao"):
            medicamento = st.session_state.sistema.buscar(codigo)
            if medicamento:
                st.session_state.med_para_atualizar = medicamento
                st.success(f"Medicamento encontrado: {medicamento.nome}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Estoque Atual:** {medicamento.quantidade} unidades")
                    nova_qtd = st.number_input("Nova Quantidade:", 
                                             min_value=0, 
                                             value=medicamento.quantidade, 
                                             step=1,
                                             key="nova_qtd")
                    
                    # Opções para adicionar/remover
                    st.write("**Ações rápidas:**")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("+1", key="+1"):
                            nova_qtd += 1
                            st.session_state.nova_qtd = nova_qtd
                    with col_b:
                        if st.button("+5", key="+5"):
                            nova_qtd += 5
                            st.session_state.nova_qtd = nova_qtd
                    with col_c:
                        if st.button("+10", key="+10"):
                            nova_qtd += 10
                            st.session_state.nova_qtd = nova_qtd
                
                with col2:
                    st.info(f"**Preço Atual:** {formatar_moeda(medicamento.preco)}")
                    novo_preco = st.number_input("Novo Preço (R$):", 
                                               min_value=0.01, 
                                               value=float(medicamento.preco), 
                                               step=0.01,
                                               format="%.2f",
                                               key="novo_preco")
                    
                    # Opções para ajustar preço
                    st.write("**Ajuste de preço:**")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("-10%", key="-10pct"):
                            novo_preco = round(medicamento.preco * 0.90, 2)
                            st.session_state.novo_preco = novo_preco
                    with col_b:
                        if st.button("+10%", key="+10pct"):
                            novo_preco = round(medicamento.preco * 1.10, 2)
                            st.session_state.novo_preco = novo_preco
                    with col_c:
                        if st.button("+20%", key="+20pct"):
                            novo_preco = round(medicamento.preco * 1.20, 2)
                            st.session_state.novo_preco = novo_preco
                
                if st.button("💾 Salvar Alterações", key="salvar_atualizacao"):
                    # Atualiza o medicamento
                    medicamento.quantidade = nova_qtd
                    medicamento.preco = novo_preco
                    
                    # Salva no banco e na árvore
                    salvar_medicamento(medicamento)
                    st.session_state.sistema.inserir(medicamento)  # Isso atualizará o nó existente
                    
                    st.success(f"Medicamento {medicamento.nome} atualizado com sucesso!")
                    st.write("**Dados atualizados:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Estoque: {nova_qtd} unidades")
                    with col2:
                        st.write(f"Preço: {formatar_moeda(novo_preco)}")
                    
                    # Limpar campos
                    st.session_state.pop("med_para_atualizar", None)
            else:
                st.error(f"Medicamento com código {codigo} não encontrado.")
    
    with tabs[1]:  # Remover Medicamento
        st.subheader("Remover Medicamento")
        
        codigo_remover = st.number_input("Código do Medicamento a Remover:", min_value=1, step=1, key="remove_codigo")
        
        if st.button("🔍 Buscar para Remoção", key="busca_remocao"):
            medicamento = st.session_state.sistema.buscar(codigo_remover)
            if medicamento:
                st.session_state.med_para_remover = medicamento
                st.warning(f"⚠️ Você está prestes a remover: **{medicamento.nome}**")
                exibir_detalhes_medicamento(medicamento)
                
                confirmacao = st.checkbox("Confirmo a remoção deste medicamento", key="confirma_remocao")
                if confirmacao and st.button("🗑️ Remover Medicamento", key="btn_remover", help="Esta ação não pode ser desfeita"):
                    # Remove do banco de dados
                    removido_banco = remover_medicamento_banco(codigo_remover)
                    # Remove da árvore AVL
                    removido_arvore = st.session_state.sistema.remover(codigo_remover)
                    
                    if removido_arvore and removido_banco:
                        st.success(f"Medicamento {medicamento.nome} removido com sucesso!")
                        st.session_state.pop("med_para_remover", None)
                    else:
                        st.error("Erro ao remover o medicamento. Tente novamente.")
            else:
                st.error(f"Medicamento com código {codigo_remover} não encontrado.")
    
    with tabs[2]:  # Estoque Crítico
        st.subheader("Medicamentos com Estoque Crítico")
        
        col1, col2 = st.columns(2)
        with col1:
            limite = st.slider("Limite de Estoque Crítico:", min_value=1, max_value=50, value=10)
        with col2:
            btn_verificar = st.button("🔎 Verificar Estoque Crítico", key="btn_verificar_estoque")
        
        if btn_verificar:
            medicamentos_criticos = st.session_state.sistema.listar_estoque_baixo(limite)
            if medicamentos_criticos:
                st.warning(f"Encontrados {len(medicamentos_criticos)} medicamentos com estoque abaixo de {limite} unidades.")
                exibir_lista_medicamentos(medicamentos_criticos, "Medicamentos com Estoque Crítico", 
                                        destaque_estoque=True, limite_critico=limite)
                
                # Exportar lista para CSV
                df_critico = pd.DataFrame([{
                    "Código": med.codigo,
                    "Nome": med.nome,
                    "Categoria": med.categoria,
                    "Preço": med.preco,
                    "Quantidade": med.quantidade,
                    "Validade": med.validade,
                    "Fabricante": med.fabricante or ""
                } for med in medicamentos_criticos])
                
                csv = df_critico.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Exportar Lista de Estoque Crítico",
                    csv,
                    "estoque_critico.csv",
                    "text/csv",
                    key='download-csv-critico'
                )
            else:
                st.success(f"Não há medicamentos com estoque abaixo de {limite} unidades.")


def mostrar_visualizacao_arvore():
    st.header("📈 Visualização da Árvore AVL")
    
    # Informações sobre a árvore
    total_nos = st.session_state.sistema.tamanho_arvore()
    altura = st.session_state.sistema.altura_arvore()
    balanceada = st.session_state.sistema.verificar_balanceamento()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_nos}</div>
            <div class="metric-label">Nós na Árvore</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{altura}</div>
            <div class="metric-label">Altura da Árvore</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        status = "Sim" if balanceada else "Não"
        color = "green" if balanceada else "red"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: {color};">{status}</div>
            <div class="metric-label">Árvore Balanceada</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Informação teórica
    st.write("""
    A árvore AVL é uma estrutura de dados balanceada que garante operações de busca, 
    inserção e remoção em tempo logarítmico O(log n). O fator de balanceamento (FB) de 
    cada nó é a diferença entre a altura da subárvore esquerda e a altura da subárvore direita.
    """)
    
    # Alerta para árvores grandes
    if total_nos > 100:
        st.warning(f"""
        ⚠️ Atenção: A visualização de árvores grandes pode ser lenta e difícil de interpretar.
        A sua árvore tem {total_nos} nós. Considere visualizar apenas uma parte da árvore.
        """)
        
        # Opção para limitar visualização
        limitar = st.checkbox("Limitar visualização", value=True if total_nos > 100 else False)
        if limitar:
            max_nodes = st.slider("Número máximo de nós a mostrar:", 
                                min_value=10, max_value=100, value=min(30, total_nos))
            st.info(f"A visualização mostrará apenas os primeiros {max_nodes} nós da árvore.")
        
    # Botão para gerar visualização
    if st.button("🔄 Gerar Visualização da Árvore"):
        if total_nos > 0:
            st.info("Gerando visualização da árvore AVL. Isso pode levar alguns segundos...")
            
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
                with st.expander("📚 Sobre Fatores de Balanceamento"):
                    st.write("""
                    O **Fator de Balanceamento (FB)** é a diferença entre a altura da subárvore esquerda e a altura da subárvore direita.
                    
                    - **FB > 0**: A subárvore esquerda é mais alta
                    - **FB < 0**: A subárvore direita é mais alta
                    - **FB = 0**: As subárvores têm a mesma altura
                    
                    Na árvore AVL, o fator de balanceamento de qualquer nó deve estar entre -1 e +1. 
                    Quando uma operação de inserção ou remoção deixa um nó com FB fora desse intervalo, 
                    são realizadas rotações para reequilibrar a árvore.
                    """)
                
                # Explicação sobre rotações
                with st.expander("🔄 Sobre Rotações AVL"):
                    st.write("""
                    Para manter o balanceamento, a árvore AVL utiliza operações de rotação:
                    
                    1. **Rotação Simples à Esquerda**: Quando FB < -1 e o nó está inclinado à direita
                    2. **Rotação Simples à Direita**: Quando FB > 1 e o nó está inclinado à esquerda
                    3. **Rotação Dupla Direita-Esquerda**: Quando FB < -1 mas o filho está inclinado à esquerda
                    4. **Rotação Dupla Esquerda-Direita**: Quando FB > 1 mas o filho está inclinado à direita
                    
                    Estas rotações garantem que, após qualquer operação, a árvore permanece balanceada.
                    """)
                    
                    # Imagens ilustrativas de rotações
                    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/AVL_Tree_Rebalancing.svg/400px-AVL_Tree_Rebalancing.svg.png", 
                            caption="Exemplos de rotações AVL")
            else:
                st.error("Não foi possível gerar a visualização.")
        else:
            st.warning("A árvore está vazia. Adicione medicamentos para visualizar a estrutura.")


def mostrar_comparativo_estruturas():
    st.header("⚡ Comparativo: Árvore AVL vs Lista Encadeada")
    
    # Introdução
    st.write("""
    Esta página demonstra a diferença de desempenho entre:
    
    * **Árvore AVL**: Estrutura balanceada com busca em O(log n)
    * **Lista Encadeada**: Estrutura linear com busca em O(n)
    """)
    
    # Medicamentos existentes
    medicamentos = st.session_state.sistema.listar_todos()
    total = len(medicamentos)
    
    if total == 0:
        st.warning("Não há medicamentos cadastrados para realizar a comparação. Adicione medicamentos primeiro.")
        return
    
    st.subheader("🔍 Comparação de Desempenho")
    st.write(f"Base de dados atual: **{total} medicamentos**")
    
    # Tabs para diferentes análises
    tab1, tab2, tab3 = st.tabs(["Teste de Busca", "Análise Teórica", "Gráficos Comparativos"])
    
    # Tab 1: Teste de Busca
    with tab1:
        st.write("### Teste de Busca em Tempo Real")
        st.write("Selecione um medicamento para buscar e compare o tempo de execução entre AVL e Lista Encadeada.")
        
        # Seleção de medicamento
        opcao = st.radio("Escolha um cenário de busca:", [
            "Primeiro medicamento (melhor caso para lista)",
            "Medicamento no meio da lista",
            "Último medicamento (pior caso para lista)",
            "Medicamento aleatório",
            "Buscar código inexistente (pior caso)"
        ])
        
        if st.button("⏱️ Executar Teste de Busca"):
            # Determinar qual código buscar
            if opcao == "Primeiro medicamento (melhor caso para lista)":
                codigo_busca = medicamentos[0].codigo
            elif opcao == "Medicamento no meio da lista":
                codigo_busca = medicamentos[len(medicamentos)//2].codigo
            elif opcao == "Último medicamento (pior caso para lista)":
                codigo_busca = medicamentos[-1].codigo
            elif opcao == "Medicamento aleatório":
                codigo_busca = random.choice(medicamentos).codigo
            else:  # Inexistente
                codigo_busca = max([m.codigo for m in medicamentos]) + 1000
            
            # Tempo na AVL
            inicio = time.time()
            resultado_avl = st.session_state.sistema.buscar(codigo_busca)
            fim = time.time()
            tempo_avl = (fim - inicio) * 1000  # ms
            
            # Tempo na lista encadeada simulada
            inicio = time.time()
            # Simula busca sequencial em lista encadeada
            resultado_lista, tempo_lista = simular_busca_lista_encadeada(medicamentos, codigo_busca)
            
            # Exibir resultados
            st.write(f"**Código buscado:** {codigo_busca}")
            if resultado_avl:
                st.write(f"**Medicamento:** {resultado_avl.nome}")
            else:
                st.write("**Medicamento:** Não encontrado")
            
            # Métricas de tempo
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tempo de Busca na Árvore AVL", f"{tempo_avl:.6f} ms")
            with col2:
                st.metric("Tempo de Busca na Lista", f"{tempo_lista:.6f} ms")
            
            # Speedup
            if tempo_avl > 0:
                speedup = tempo_lista / tempo_avl
                st.success(f"A árvore AVL foi **{speedup:.2f}x mais rápida** que a lista encadeada!")
            
            # Mais detalhes
            with st.expander("📊 Detalhes da Comparação"):
                st.write(f"**Total de nós na árvore:** {total}")
                st.write(f"**Altura da árvore AVL:** {st.session_state.sistema.altura_arvore()}")
                st.write(f"**Comparações teóricas na árvore AVL:** Aproximadamente {int(np.log2(total) + 1)}")
                st.write(f"**Comparações na lista encadeada (pior caso):** {total}")
    
    # Tab 2: Análise Teórica
    with tab2:
        st.write("### Análise de Complexidade Teórica")
        st.write("""
        A complexidade das operações nas diferentes estruturas de dados:
        
        | Operação | Árvore AVL | Lista Encadeada |
        |----------|------------|-----------------|
        | Busca    | O(log n)   | O(n)            |
        | Inserção | O(log n)   | O(1) no início, O(n) em posição arbitrária |
        | Remoção  | O(log n)   | O(1) no início, O(n) em posição arbitrária |
        
        Para a base de dados atual com **{total} medicamentos**:
        """)
        
        # Cálculos teóricos
        altura_avl = st.session_state.sistema.altura_arvore()
        log_n = np.log2(total) + 1
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">O(log {total})</div>
                <div class="metric-label">Complexidade de Busca na AVL</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{log_n:.1f}</div>
                <div class="metric-label">Comparações (máx.) na AVL</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">O({total})</div>
                <div class="metric-label">Complexidade de Busca na Lista</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total}</div>
                <div class="metric-label">Comparações (máx.) na Lista</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Diferença teórica
        diferenca = total / log_n
        st.info(f"💡 Teoricamente, a busca na Lista Encadeada pode ser até **{diferenca:.1f}x mais lenta** que na Árvore AVL para esta quantidade de dados.")
        
        # Gráfico de complexidade
        st.write("### Crescimento da Complexidade")
        
        # Dados para o gráfico
        x = list(range(10, 10001, 100))
        y_avl = [np.log2(n) for n in x]
        y_lista = x
        
        # Criar DataFrame
        df_complexidade = pd.DataFrame({
            'Tamanho (n)': x + x,
            'Comparações': y_avl + y_lista,
            'Estrutura': ['AVL'] * len(x) + ['Lista'] * len(x)
        })
        
        # Gráfico com Altair
        chart = alt.Chart(df_complexidade).mark_line().encode(
            x='Tamanho (n)',
            y=alt.Y('Comparações', scale=alt.Scale(type='log', domain=[1, 10000])),
            color='Estrutura',
            strokeDash='Estrutura'
        ).properties(
            width=600,
            height=400,
            title='Comparações Necessárias para Busca (escala logarítmica)'
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)
        
    # Tab 3: Gráficos Comparativos
    with tab3:
        st.write("### Simulação de Desempenho para Diferentes Tamanhos")
        
        # Criar dados de simulação
        tamanhos = [10, 100, 1000, 10000, 100000, 1000000]
        tempo_avl = [np.log2(n) * 0.01 for n in tamanhos]  # Simulação de tempo AVL
        tempo_lista = [n * 0.01 for n in tamanhos]  # Simulação de tempo Lista
        
        # Limitar para visualização
        tempo_lista = [min(t, 100) for t in tempo_lista]  # Cap para visualização
        
        # Criar DataFrame
        df_tempo = pd.DataFrame({
            'Tamanho': [str(n) for n in tamanhos] * 2,
            'Tempo (ms)': tempo_avl + tempo_lista,
            'Estrutura': ['AVL'] * len(tamanhos) + ['Lista'] * len(tamanhos)
        })
        
        # Gráfico com Altair
        chart = alt.Chart(df_tempo).mark_bar().encode(
            x=alt.X('Tamanho:N', sort=tamanhos),
            y='Tempo (ms)',
            color='Estrutura',
            column=alt.Column('Estrutura', header=alt.Header(labelOrient='bottom'))
        ).properties(
            title='Tempo de Busca Estimado por Tamanho de Dataset'
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Outra visualização: speedup
        speedup = [lista/avl for lista, avl in zip(tempo_lista, tempo_avl)]
        df_speedup = pd.DataFrame({
            'Tamanho': [str(n) for n in tamanhos],
            'Speedup (vezes mais rápido)': speedup
        })
        
        chart2 = alt.Chart(df_speedup).mark_bar().encode(
            x='Tamanho:N',
            y='Speedup (vezes mais rápido)',
            color=alt.Color('Speedup (vezes mais rápido)', scale=alt.Scale(scheme='viridis'))
        ).properties(
            title='Quantas vezes a AVL é mais rápida que a Lista Encadeada',
            width=600,
            height=400
        )
        
        st.altair_chart(chart2, use_container_width=True)
        
        # Conclusão
        st.info("""
        **Conclusão:**
        
        A diferença de desempenho entre a Árvore AVL e a Lista Encadeada cresce dramaticamente 
        com o aumento do tamanho dos dados. Para conjuntos de dados grandes (milhões de itens), 
        a AVL pode ser milhares de vezes mais eficiente que uma lista encadeada para operações de busca.
        
        * Para 10 itens: Diferença pequena
        * Para 1.000 itens: AVL ~100x mais rápida
        * Para 1.000.000 itens: AVL ~50.000x mais rápida
        
        Isso demonstra por que estruturas de dados balanceadas como a Árvore AVL são essenciais 
        para sistemas que precisam manipular grandes volumes de dados eficientemente.
        """)


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
            st.markdown(f"**Estoque:** <span class='critical'>{medicamento.quantidade} unidades</span>", unsafe_allow_html=True)
        elif medicamento.quantidade < 10:
            st.markdown(f"**Estoque:** <span class='warning'>{medicamento.quantidade} unidades</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**Estoque:** <span class='normal'>{medicamento.quantidade} unidades</span>", unsafe_allow_html=True)
        
        st.write(f"**Preço:** {formatar_moeda(medicamento.preco)}")
        st.write(f"**Validade:** {medicamento.validade}")
        
        # Valor total em estoque
        valor_total = medicamento.preco * medicamento.quantidade
        st.write(f"**Valor em estoque:** {formatar_moeda(valor_total)}")


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
            "Preço": formatar_moeda(med.preco),
            "Estoque": med.quantidade,
            "Validade": med.validade
        } for med in medicamentos])
        
        # Adiciona estilo com destaque para estoque crítico
        if destaque_estoque:
            def highlight_estoque(s):
                return ['background-color: red; color: white' if v < 5 else 
                        'background-color: orange; color: black' if v < limite_critico else 
                        '' for v in s]
            
            styled_df = df.style.apply(highlight_estoque, subset=['Estoque'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    else:
        st.info(f"Nenhum medicamento encontrado para: {titulo}")


# Executa a aplicação
if __name__ == "__main__":
    main()
