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
import locale
from functools import lru_cache

# Aumenta o limite de células renderizáveis pelo Pandas Styler
pd.set_option("styler.render.max_elements", 500000)

# Importe a implementação da Árvore AVL
from sistema_farmacia_avl import ArvoreAVL, Medicamento, NoAVL, formatar_moeda, simular_busca_lista_encadeada

# Configuração adicional de locale para formatação de números
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        pass

# Funções auxiliares de formatação
def formatar_numero(valor):
    """Formata números grandes com separadores de milhar."""
    try:
        return locale.format_string("%d", valor, grouping=True)
    except:
        # Fallback para formatação manual
        return f"{valor:,}".replace(",", ".")

def formatar_decimal(valor, precisao=2):
    """Formata números decimais com separadores de milhar e casas decimais."""
    try:
        return locale.format_string(f"%.{precisao}f", valor, grouping=True)
    except:
        # Fallback para formatação manual
        return f"{valor:,.{precisao}f}".replace(",", "X").replace(".", ",").replace("X", ".")


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


@st.cache_data(ttl=300)  # Cache data for 5 minutes
def get_cached_medicamentos():
    """Cache medicamentos to avoid repeated database queries"""
    return st.session_state.sistema.listar_todos()

@st.cache_data(ttl=300)
def get_estoque_critico(_medicamentos, limite=5):
    """Get medications with critical stock levels"""
    return [med for med in _medicamentos if med.quantidade < limite]

@st.cache_data(ttl=300)
def get_estoque_statistics(_medicamentos):
    """Calculate stock statistics"""
    total_estoque = sum(med.quantidade for med in _medicamentos)
    valor_total = sum(med.preco * med.quantidade for med in _medicamentos)
    estoque_baixo = sum(1 for med in _medicamentos if med.quantidade < 10)
    estoque_critico = sum(1 for med in _medicamentos if med.quantidade < 5)
    return total_estoque, valor_total, estoque_baixo, estoque_critico

def mostrar_dashboard():
    st.header("📊 Dashboard")
    
    # Show loading state
    with st.spinner("Carregando dados do sistema..."):
        # Get cached medications data
        medicamentos = get_cached_medicamentos()
    
    if not medicamentos:
        st.warning("Não há medicamentos cadastrados. Utilize o menu para adicionar medicamentos.")
        return
    
    # Prepare data - use cached statistics
    total_estoque, valor_total, estoque_baixo, estoque_critico = get_estoque_statistics(medicamentos)
    
    # Display metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{formatar_numero(len(medicamentos))}</div>
            <div class="metric-label">Medicamentos Cadastrados</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{formatar_numero(total_estoque)}</div>
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
            <div class="metric-value" style="color: {'red' if estoque_critico > 0 else 'green'};">{formatar_numero(estoque_critico)}</div>
            <div class="metric-label">Itens com Estoque Crítico</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Implement tabbed interface for better organization and performance
    dashboard_tabs = st.tabs(["Estoque Crítico", "Análise de Dados", "Validade"])
    
    # Tab 1: Critical stock - only load when this tab is selected
    with dashboard_tabs[0]:
        st.subheader("⚠️ Medicamentos com Estoque Crítico")
        
        # Use the cached critical stock data
        with st.spinner("Verificando medicamentos com estoque crítico..."):
            estoque_critico_meds = get_estoque_critico(medicamentos)
        
        if estoque_critico_meds:
            # Create DataFrame once, efficiently
            df_critico = pd.DataFrame([{
                "Código": med.codigo,
                "Nome": med.nome,
                "Categoria": med.categoria,
                "Preço": formatar_moeda(med.preco),  # Pre-format the price
                "Estoque": med.quantidade,
                "Validade": med.validade
            } for med in estoque_critico_meds])
            
            # Apply styling more efficiently
            def highlight_estoque(s):
                return ['color: red; font-weight: bold' if v < 5 else '' for v in s]
            
            styled_df = df_critico.style.apply(highlight_estoque, subset=['Estoque'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Provide download option
            if st.button("📥 Baixar Lista de Estoque Crítico", key="download_critico"):
                csv = df_critico.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Confirmar Download CSV",
                    csv,
                    "estoque_critico.csv",
                    "text/csv",
                    key="download_critico_confirm"
                )
        else:
            st.success("Não há medicamentos com estoque crítico. Parabéns!")
    
    # Tab 2: Data Analysis
    with dashboard_tabs[1]:
        # Defer expensive chart creation until this tab is selected
        st.subheader("📈 Análise de Dados")
        
        charts_tab1, charts_tab2, charts_tab3 = st.tabs(["Categorias", "Estoque", "Valor"])
        
        with charts_tab1:
            # Análise por categoria - only if this tab is selected
            if medicamentos:
                with st.spinner("Gerando análise de categorias..."):
                    # Process data efficiently - avoid creating multiple DataFrames
                    categorias = {}
                    for med in medicamentos:
                        categorias[med.categoria] = categorias.get(med.categoria, 0) + 1
                    
                    cat_count = pd.DataFrame({
                        'Categoria': list(categorias.keys()),
                        'Quantidade': list(categorias.values())
                    })
                    cat_count = cat_count.sort_values('Quantidade', ascending=False)
                    
                    # Add formatted values for tooltips
                    cat_count['Qtd_Formatada'] = cat_count['Quantidade'].apply(formatar_numero)
                    
                    # Create chart
                    chart = alt.Chart(cat_count).mark_bar().encode(
                        x=alt.X('Categoria:N', sort='-y'),
                        y='Quantidade:Q',
                        color=alt.Color('Categoria:N', legend=None),
                        tooltip=[
                            alt.Tooltip('Categoria:N', title='Categoria'),
                            alt.Tooltip('Qtd_Formatada:N', title='Quantidade')
                        ]
                    ).properties(
                        title='Medicamentos por Categoria',
                        height=300
                    ).interactive()
                    
                    st.altair_chart(chart, use_container_width=True)
        
        with charts_tab2:
            # Only calculate distribution if this tab is selected
            if medicamentos:
                with st.spinner("Analisando distribuição de estoque..."):
                    # More efficient calculation
                    estoque_categorias = {'Crítico (<5)': 0, 'Baixo (5-9)': 0, 
                                         'Moderado (10-19)': 0, 'Bom (20-49)': 0, 'Ótimo (50+)': 0}
                    
                    for med in medicamentos:
                        if med.quantidade < 5:
                            estoque_categorias['Crítico (<5)'] += 1
                        elif med.quantidade < 10:
                            estoque_categorias['Baixo (5-9)'] += 1
                        elif med.quantidade < 20:
                            estoque_categorias['Moderado (10-19)'] += 1
                        elif med.quantidade < 50:
                            estoque_categorias['Bom (20-49)'] += 1
                        else:
                            estoque_categorias['Ótimo (50+)'] += 1
                    
                    # Create DataFrame directly from the counts
                    ordem = ['Crítico (<5)', 'Baixo (5-9)', 'Moderado (10-19)', 'Bom (20-49)', 'Ótimo (50+)']
                    estoque_dist = pd.DataFrame({
                        'Categoria': ordem,
                        'Quantidade': [estoque_categorias[cat] for cat in ordem],
                    })
                    
                    # Add formatted values
                    estoque_dist['Qtd_Formatada'] = estoque_dist['Quantidade'].apply(formatar_numero)
                    
                    # Colors for each category
                    cores = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#27ae60']
                    
                    # Create chart
                    chart = alt.Chart(estoque_dist).mark_bar().encode(
                        x=alt.X('Categoria:N', sort=ordem),
                        y='Quantidade:Q',
                        color=alt.Color('Categoria:N', scale=alt.Scale(domain=ordem, range=cores)),
                        tooltip=[
                            alt.Tooltip('Categoria:N', title='Nível de Estoque'),
                            alt.Tooltip('Qtd_Formatada:N', title='Quantidade')
                        ]
                    ).properties(
                        title='Distribuição de Níveis de Estoque',
                        height=300
                    ).interactive()
                    
                    st.altair_chart(chart, use_container_width=True)
        
        with charts_tab3:
            # Only calculate value analysis if this tab is selected
            if medicamentos:
                with st.spinner("Calculando valor por categoria..."):
                    # More efficient calculation by category
                    valor_por_cat_dict = {}
                    for med in medicamentos:
                        valor_item = med.preco * med.quantidade
                        valor_por_cat_dict[med.categoria] = valor_por_cat_dict.get(med.categoria, 0) + valor_item
                    
                    # Convert to DataFrame
                    valor_por_cat = pd.DataFrame({
                        'Categoria': list(valor_por_cat_dict.keys()),
                        'Valor Total': list(valor_por_cat_dict.values())
                    }).sort_values('Valor Total', ascending=False)
                    
                    # Format for display
                    valor_por_cat['Valor Formatado'] = valor_por_cat['Valor Total'].apply(formatar_moeda)
                    
                    # Create chart
                    chart = alt.Chart(valor_por_cat).mark_bar().encode(
                        x=alt.X('Categoria:N', sort='-y'),
                        y=alt.Y('Valor Total:Q', axis=alt.Axis(format='~s', title='Valor Total (R$)')),
                        color=alt.Color('Categoria:N', legend=None),
                        tooltip=[
                            alt.Tooltip('Categoria:N', title='Categoria'),
                            alt.Tooltip('Valor Formatado:N', title='Valor em Estoque')
                        ]
                    ).properties(
                        title='Valor Total em Estoque por Categoria',
                        height=300
                    ).interactive()
                    
                    st.altair_chart(chart, use_container_width=True)
    
    # Tab 3: Expiration dates
    with dashboard_tabs[2]:
        st.subheader("📅 Medicamentos com Validade Próxima")
        
        with st.container():
            # Lazy load expiration data
            with st.spinner("Verificando datas de validade..."):
                hoje = datetime.now().date()
                medicamentos_validade = []
                
                # Process all at once to avoid multiple loops
                for med in medicamentos:
                    try:
                        data_validade = datetime.strptime(med.validade, "%Y-%m-%d").date()
                        dias_ate_vencer = (data_validade - hoje).days
                        
                        if dias_ate_vencer <= 90:  # Next 3 months
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
                # Create DataFrame once
                df_validade = pd.DataFrame(medicamentos_validade)
                df_validade = df_validade.sort_values("Dias até vencer")
                
                # Highlight function
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
                
                # Apply styling
                styled_df = df_validade.style.map(highlight_validade, subset=['Dias até vencer'])
                st.dataframe(styled_df, use_container_width=True)
                
                # Provide download option
                if st.button("📥 Baixar Lista de Validade", key="download_validade"):
                    csv = df_validade.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Confirmar Download CSV",
                        csv,
                        "medicamentos_validade.csv",
                        "text/csv",
                        key="download_validade_confirm"
                    )
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
        
        # Use a form to handle sequential input properly
        with st.form(key="intervalo_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                codigo_inicio = st.number_input(
                    "Código inicial:", 
                    min_value=1, 
                    step=1, 
                    key="codigo_inicio"
                )
            
            with col2:
                # Set a reasonable default max value
                max_codigo = 999999
                codigo_fim = st.number_input(
                    "Código final:", 
                    min_value=1,  # Start with 1 as min_value
                    value=codigo_inicio + 100,  # Default to inicio+100
                    max_value=max_codigo,
                    step=1, 
                    key="codigo_fim"
                )
            
            # Add a validation message if needed
            if codigo_fim < codigo_inicio:
                st.warning("O código final deve ser maior ou igual ao código inicial.")
            
            # Submit button for the form
            buscar_submitted = st.form_submit_button("🔎 Buscar por Intervalo")
        
        # Process form after submission
        if buscar_submitted:
            # Ensure código_fim is at least código_inicio
            codigo_fim_final = max(codigo_inicio, codigo_fim)
            medicamentos = st.session_state.sistema.buscar_por_intervalo(codigo_inicio, codigo_fim_final)
            exibir_lista_medicamentos(medicamentos, f"Medicamentos com código entre {codigo_inicio} e {codigo_fim_final}")
    
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
                    O **Fator de Balanceamento (FB)** é a diferença entre a altura da subárvore esquerda e a subárvore direita.
                    
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
        
        Para a base de dados atual com **{} medicamentos**:
        """.format(formatar_numero(total)))
        
        # Cálculos teóricos
        altura_avl = st.session_state.sistema.altura_arvore()
        log_n = np.log2(total) + 1
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">O(log {formatar_numero(total)})</div>
                <div class="metric-label">Complexidade de Busca na AVL</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{formatar_decimal(log_n, 1)}</div>
                <div class="metric-label">Comparações (máx.) na AVL</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">O({formatar_numero(total)})</div>
                <div class="metric-label">Complexidade de Busca na Lista</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{formatar_numero(total)}</div>
                <div class="metric-label">Comparações (máx.) na Lista</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Diferença teórica
        diferenca = total / log_n
        st.info(f"💡 Teoricamente, a busca na Lista Encadeada pode ser até **{formatar_decimal(diferenca, 1)}x mais lenta** que na Árvore AVL para esta quantidade de dados.")
        
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
        tamanhos_formatados = [formatar_numero(t) for t in tamanhos]
        tempo_avl = [np.log2(n) * 0.01 for n in tamanhos]  # Simulação de tempo AVL
        tempo_lista = [n * 0.01 for n in tamanhos]  # Simulação de tempo Lista
        
        # Limitar para visualização
        tempo_lista = [min(t, 100) for t in tempo_lista]  # Cap para visualização
        
        # Formatar para exibição
        tempo_avl_fmt = [formatar_decimal(t, 3) for t in tempo_avl]
        tempo_lista_fmt = [formatar_decimal(t, 3) for t in tempo_lista]
        
        # Criar DataFrame
        df_tempo = pd.DataFrame({
            'Tamanho': tamanhos_formatados * 2,
            'Tamanho_Original': tamanhos * 2,  # Para ordenação
            'Tempo (ms)': tempo_avl + tempo_lista,
            'Tempo_Fmt': tempo_avl_fmt + tempo_lista_fmt,
            'Estrutura': ['AVL'] * len(tamanhos) + ['Lista'] * len(tamanhos)
        })
        
        # Gráfico com Altair
        chart = alt.Chart(df_tempo).mark_bar().encode(
            x=alt.X('Tamanho:N', sort=alt.EncodingSortField(field='Tamanho_Original', order='ascending')),
            y=alt.Y('Tempo (ms):Q'),
            color='Estrutura:N',
            tooltip=[
                alt.Tooltip('Tamanho:N', title='Tamanho (n)'),
                alt.Tooltip('Tempo_Fmt:N', title='Tempo (ms)')
            ],
            column=alt.Column('Estrutura:N', header=alt.Header(labelOrient='bottom'))
        ).properties(
            title='Tempo de Busca Estimado por Tamanho de Dataset'
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Outra visualização: speedup
        speedup = [lista/avl for lista, avl in zip(tempo_lista, tempo_avl)]
        speedup_fmt = [formatar_decimal(s, 1) for s in speedup]
        df_speedup = pd.DataFrame({
            'Tamanho': tamanhos_formatados,
            'Tamanho_Original': tamanhos,  # Para ordenação
            'Speedup': speedup,
            'Speedup_Fmt': speedup_fmt
        })
        
        chart2 = alt.Chart(df_speedup).mark_bar().encode(
            x=alt.X('Tamanho:N', sort=alt.EncodingSortField(field='Tamanho_Original', order='ascending')),
            y=alt.Y('Speedup:Q', title='Vezes mais rápido'),
            color=alt.Color('Speedup:Q', scale=alt.Scale(scheme='viridis')),
            tooltip=[
                alt.Tooltip('Tamanho:N', title='Tamanho (n)'),
                alt.Tooltip('Speedup_Fmt:N', title='Vezes mais rápido')
            ]
        ).properties(
            title='Quantas vezes a AVL é mais rápida que a Lista Encadeada',
            width=600,
            height=400
        )
        
        st.altair_chart(chart2, use_container_width=True)
        
        # Conclusão
        st.info(f"""
        **Conclusão:**
        
        A diferença de desempenho entre a Árvore AVL e a Lista Encadeada cresce dramaticamente 
        com o aumento do tamanho dos dados. Para conjuntos de dados grandes (milhões de itens), 
        a AVL pode ser milhares de vezes mais eficiente que uma lista encadeada para operações de busca.
        
        * Para 10 itens: Diferença pequena
        * Para 1.000 itens: AVL ~{formatar_decimal(speedup[2], 0)}x mais rápida
        * Para 1.000.000 itens: AVL ~{formatar_decimal(speedup[5], 0)}x mais rápida
        
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
            st.markdown(f"**Estoque:** <span class='critical'>{formatar_numero(medicamento.quantidade)} unidades</span>", unsafe_allow_html=True)
        elif medicamento.quantidade < 10:
            st.markdown(f"**Estoque:** <span class='warning'>{formatar_numero(medicamento.quantidade)} unidades</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**Estoque:** <span class='normal'>{formatar_numero(medicamento.quantidade)} unidades</span>", unsafe_allow_html=True)
        
        st.write(f"**Preço:** {formatar_moeda(medicamento.preco)}")
        st.write(f"**Validade:** {medicamento.validade}")
        
        # Valor total em estoque
        valor_total = medicamento.preco * medicamento.quantidade
        st.write(f"**Valor em estoque:** {formatar_moeda(valor_total)}")


def exibir_lista_medicamentos(medicamentos, titulo, destaque_estoque=False, limite_critico=10):
    """Exibe uma lista de medicamentos em forma de tabela"""
    if medicamentos:
        st.subheader(titulo)
        st.write(f"Total de itens: {formatar_numero(len(medicamentos))}")
        
        # Converte para DataFrame
        df = pd.DataFrame([{
            "Código": med.codigo,
            "Nome": med.nome,
            "Categoria": med.categoria,
            "Preço": formatar_moeda(med.preco),
            "Estoque": med.quantidade,
            "Estoque_Fmt": formatar_numero(med.quantidade),  # Coluna adicional formatada
            "Validade": med.validade
        } for med in medicamentos])
        
        # Prepara dataframe para exibição
        df_exibicao = df.copy()
        df_exibicao["Estoque"] = df_exibicao["Estoque_Fmt"]  # Substitui pela versão formatada
        df_exibicao = df_exibicao.drop(columns=["Estoque_Fmt"])  # Remove coluna auxiliar
        
        # Adiciona estilo com destaque para estoque crítico
        if destaque_estoque:
            def highlight_estoque(s):
                # Usa a coluna original não formatada para comparações
                original_estoque = df['Estoque'].tolist()
                return ['background-color: red; color: white' if v < 5 else 
                        'background-color: orange; color: black' if v < limite_critico else 
                        '' for v in original_estoque]
            
            styled_df = df_exibicao.style.apply(highlight_estoque, subset=['Estoque'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.dataframe(df_exibicao, use_container_width=True)
    else:
        st.info(f"Nenhum medicamento encontrado para: {titulo}")


# Executa a aplicação
if __name__ == "__main__":
    main()
