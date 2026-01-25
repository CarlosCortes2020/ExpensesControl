import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import src.expenses_control.core as em
import datetime

# --- CONFIG ---
st.set_page_config(
    page_title="Control de Gastos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS STYLING ---
def local_css():
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        /* Card styling for metrics */
        div[data-testid="stMetric"] {
            background-color: #f0f2f6;
            border: 1px solid #dce0e6;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        }
        /* Dark mode adjustment for metrics */
        @media (prefers-color-scheme: dark) {
            div[data-testid="stMetric"] {
                background-color: #262730;
                border: 1px solid #464b5c;
            }
        }
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        /* Expander styling */
        .streamlit-expanderHeader {
            font-weight: bold;
            font-size: 1.1rem;
        }
    </style>
    """, unsafe_allow_html=True)

# --- INIT DB ---
em.init_db()

# --- UTILS ---

def get_current_year():
    return datetime.date.today().year

def color_negative_red(val):
    color = 'red' if val < 0 else 'green'
    return f'color: {color}'

# --- CALLBACKS FOR TRANSACTIONS ---

def on_transactions_change():
    """Handle changes in the DataEditor for Transactions."""
    state = st.session_state["transactions_editor"]
    
    # Use the dataframe that was displayed when the edit happened
    if "current_table_df" not in st.session_state:
        return

    # This is the filtered/sorted dataframe from the UI
    display_df = st.session_state["current_table_df"]
    
    # 1. ADDED ROWS
    for row in state["added_rows"]:
        # row is a dict of {column_name: value}
        # Default values if missing
        date = row.get("Fecha", datetime.date.today().strftime("%Y-%m-%d"))
        # Ensure date is string
        if isinstance(date, datetime.date):
            date = date.strftime("%Y-%m-%d")
            
        category = row.get("Categoría", "Otros")
        val = row.get("Monto", 0.0)
        try:
            amount = float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            amount = 0.0
        description = row.get("Descripción", "")
        member = row.get("Miembro", "")
        t_type = row.get("Tipo", "Gasto")
        payment_method = row.get("Método Pago", "Efectivo")
        
        em.db_add_expense(date, category, amount, description, t_type, member, payment_method)

    # 2. DELETED ROWS
    # state["deleted_rows"] is a list of integers (indices of the displayed dataframe)
    if state["deleted_rows"]:
        for idx in state["deleted_rows"]:
            try:
                # Get the ID from the displayed dataframe
                expense_id = display_df.iloc[idx]['id']
                em.db_delete_expense(expense_id)
            except IndexError:
                pass 

    # 3. EDITED ROWS
    # state["edited_rows"] is a dict {row_index: {col_name: new_value}}
    for idx, changes in state["edited_rows"].items():
        try:
            expense_id = display_df.iloc[idx]['id']
            for col, value in changes.items():
                # Convert value if necessary
                if col == "Fecha" and isinstance(value, (datetime.date, datetime.datetime)):
                    value = value.strftime("%Y-%m-%d")
                
                em.db_update_expense(expense_id, col, value)
        except IndexError:
            pass

# --- TABS ---

def tab_dashboard(year):
    st.header(f"Tablero de Control - {year}")
    
    # Fetch Data
    df_expenses, df_income, df_budget_expenses, df_budget_income = em.db_get_analytics_data(str(year))
    analysis = em.process_monthly_summary(df_expenses, df_income, df_budget_expenses, df_budget_income)
    
    # Add Month Names
    analysis['month_name'] = analysis['month'].map(em.MONTH_MAP)
    
    # Metrics
    total_income = analysis['income_amount'].sum()
    total_expense = analysis['expense_amount'].sum()
    balance = total_income - total_expense
    
    # Use columns with gaps for card effect
    col1, col2, col3 = st.columns(3, gap="medium")
    col1.metric("Ingresos Reales", f"${total_income:,.2f}", delta_color="normal")
    col2.metric("Gastos Reales", f"${total_expense:,.2f}", delta="-"+f"${total_expense:,.2f}", delta_color="inverse")
    col3.metric("Balance", f"${balance:,.2f}", delta_color="normal" if balance >= 0 else "inverse")
    
    st.divider()
    
    # Charts
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # 1. Line Chart: Trend
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=analysis['month_name'], y=analysis['income_amount'], mode='lines+markers', name='Ingresos', line=dict(color='#27AE60', width=3)))
        fig_trend.add_trace(go.Scatter(x=analysis['month_name'], y=analysis['expense_amount'], mode='lines+markers', name='Gastos', line=dict(color='#E74C3C', width=3)))
        fig_trend.update_layout(
            title="Evolución Financiera Anual", 
            xaxis_title="Mes", 
            yaxis_title="Monto", 
            template="plotly_white",
            yaxis_tickformat=',.2f',
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        # 2. Donut Chart: Expenses
        if not df_expenses.empty:
            cat_summary = df_expenses.groupby('category')['amount'].sum().reset_index()
            fig_pie = px.pie(cat_summary, values='amount', names='category', title='Distribución de Gastos', hole=0.4)
            fig_pie.update_traces(textinfo='percent+label', hovertemplate='Categoría: %{label}<br>Monto: $%{value:,.2f}')
            fig_pie.update_layout(
                template="plotly_white",
                margin=dict(l=20, r=20, t=50, b=20),
                showlegend=False
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sin datos de gastos para mostrar gráfico circular.")

    # 3. Bar Chart: Budget vs Real
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=analysis['month_name'], y=analysis['budget_amount'], name='Presupuesto', marker_color='#34495E'))
    fig_bar.add_trace(go.Bar(x=analysis['month_name'], y=analysis['expense_amount'], name='Real', marker_color='#E74C3C'))
    fig_bar.update_layout(
        title="Presupuesto vs Ejecución (Gastos)", 
        xaxis_title="Mes", 
        yaxis_title="Monto", 
        barmode='group', 
        template="plotly_white",
        yaxis_tickformat=',.2f',
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

def tab_matrix_view(year, type_label, db_type):
    """Generic function for Income/Expense Budget & Analysis."""
    st.subheader(f"Gestión de {type_label}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Presupuesto de {type_label} (Planificado)**")
        st.caption("Edita los valores y presiona 'Guardar Presupuestos'")
        
        # Load Budget Matrix
        # Index: Category, Cols: 1..12
        df_budget = em.db_get_budget_matrix(year, ctype=db_type)
        
        # Rename columns to Month Names
        df_budget.columns = [em.MONTH_MAP.get(c, c) for c in df_budget.columns]
        
        # Streamlit Data Editor
        budget_cols_config = {
            m: st.column_config.NumberColumn(m, format="$%.2f", min_value=0, step=0.01)
            for m in df_budget.columns
        }
        edited_budget = st.data_editor(
            df_budget, 
            key=f"budget_{db_type}_{year}", 
            use_container_width=True,
            column_config=budget_cols_config
        )
        
        if st.button(f"Guardar Presupuestos ({type_label})"):
            # Iterate and save
            # df has index=CategoryName, columns="Ene", "Feb"...
            for category in edited_budget.index:
                for month_name in edited_budget.columns:
                    try:
                        month_num = em.MONTH_NAME_TO_NUM.get(month_name)
                        if month_num:
                            amount = float(edited_budget.loc[category, month_name])
                            em.db_set_budget(category, month_num, year, amount)
                    except ValueError:
                        pass # Ignore non-numeric
            st.success("Presupuestos actualizados correctamente.")
            st.rerun()

    with col2:
        st.markdown(f"**{type_label} Reales (Ejecutado)**")
        st.caption("Solo lectura (Cálculo automático desde Movimientos)")
        
        if db_type == "Expense":
            df_real = em.db_get_real_expenses_matrix(year)
        else:
            df_real = em.db_get_real_income_matrix(year)
            
        # Rename columns to Month Names
        df_real.columns = [em.MONTH_MAP.get(c, c) for c in df_real.columns]

        st.dataframe(df_real.style.format("{:,.2f}"), use_container_width=True)

    # Comparison / Variance (Optional enhancement)
    st.markdown("---")
    st.markdown("**Comparativa Mensual**")
    
    # Simple difference matrix
    # Ensure indices align
    common_index = df_budget.index.union(df_real.index)
    df_budget_aligned = df_budget.reindex(common_index).fillna(0)
    df_real_aligned = df_real.reindex(common_index).fillna(0)
    
    # Ensure columns match (months names)
    for m in em.MONTH_NAMES:
        if m not in df_budget_aligned.columns: df_budget_aligned[m] = 0.0
        if m not in df_real_aligned.columns: df_real_aligned[m] = 0.0
    
    # Sort columns by Month Order
    df_budget_aligned = df_budget_aligned[em.MONTH_NAMES]
    df_real_aligned = df_real_aligned[em.MONTH_NAMES]

    if db_type == "Expense":
        # Variance = Budget - Real (Positive is good/under budget)
        diff = df_budget_aligned - df_real_aligned
    else:
        # Variance = Real - Budget (Positive is good/over income)
        diff = df_real_aligned - df_budget_aligned
        
    st.dataframe(diff.style.format("{:,.2f}").applymap(lambda x: 'color: green' if x >= 0 else 'color: red'), use_container_width=True)

def tab_daily(year):
    st.subheader(f"Gastos por Día - {year}")
    
    # Month Selector
    current_month = datetime.date.today().month
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_month_name = st.selectbox("Seleccionar Mes", em.MONTH_NAMES, index=current_month-1)
    
    selected_month = em.MONTH_NAME_TO_NUM[selected_month_name]
    
    # Fetch Data
    df = em.db_get_all_expenses_df()
    
    if df.empty:
        st.info("No hay datos disponibles.")
        return

    # Filter by Year and Month, and Type=Gasto
    # Ensure Fecha is datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    mask = (df['Fecha'].dt.year == year) & (df['Fecha'].dt.month == selected_month) & (df['Tipo'] == 'Gasto')
    df_filtered = df[mask].copy()
    
    if df_filtered.empty:
        st.info(f"No hay gastos registrados en {selected_month_name} {year}.")
        return

    # Group by Day
    df_filtered['day'] = df_filtered['Fecha'].dt.day
    daily_expenses = df_filtered.groupby('day')['Monto'].sum().reset_index()
    
    # Ensure all days are present
    import calendar
    _, num_days = calendar.monthrange(year, selected_month)
    all_days = pd.DataFrame({'day': range(1, num_days + 1)})
    daily_expenses = pd.merge(all_days, daily_expenses, on='day', how='left').fillna(0)
    
    # Metrics
    total_month = daily_expenses['Monto'].sum()
    st.metric(f"Total Gastos {selected_month_name}", f"${total_month:,.2f}")

    # 1. Chart
    fig = px.bar(daily_expenses, x='day', y='Monto', title=f"Evolución Diaria - {selected_month_name}")
    fig.update_layout(xaxis_title="Día", yaxis_title="Monto ($)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    
    # 2. Table (Detailed view for that month)
    with st.expander("Ver Detalle de Registros", expanded=True):
        st.dataframe(
            df_filtered[['Fecha', 'Categoría', 'Descripción', 'Monto', 'Método Pago']].sort_values('Fecha', ascending=False),
            use_container_width=True,
            hide_index=True
        )


def tab_transactions():
    st.subheader("Registro de Movimientos")
    
    # --- Add New Category Section ---
    with st.expander("➕ Crear Nueva Categoría", expanded=False):
        with st.form("new_category_form"):
            new_cat_name = st.text_input("Nombre de la Categoría")
            new_cat_type = st.selectbox("Tipo", ["Gasto", "Ingreso"])
            submit_cat = st.form_submit_button("Crear Categoría")
            
            if submit_cat:
                if new_cat_name:
                    # Map GUI type to DB type
                    db_type = "Expense" if new_cat_type == "Gasto" else "Income"
                    if em.db_add_category(new_cat_name, db_type):
                        st.success(f"Categoría '{new_cat_name}' creada!")
                        st.rerun()
                    else:
                        st.error("Error: La categoría ya existe.")
                else:
                    st.warning("Por favor ingresa un nombre.")

    # --- Filters ---
    st.markdown("### Filtros")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    df = em.db_get_all_expenses_df()
    
    # Ensure 'Fecha' is datetime objects for st.data_editor (required by DateColumn)
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
    
    # 1. Date Filter
    with col_f1:
        date_range = st.date_input("Fecha", [])
    
    # 2. Category Filter
    with col_f2:
        # Get unique categories from current data + default categories
        # Note: Here we show ALL categories for filtering, even headers if they exist in data
        all_cats = sorted(list(set(df['Categoría'].unique()) | set(em.db_get_categories())))
        selected_cats = st.multiselect("Categoría", all_cats)
        
    # 3. Type Filter
    with col_f3:
        selected_type = st.multiselect("Tipo", ["Gasto", "Ingreso"])

    # Apply Filters
    filtered_df = df.copy()
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[(filtered_df['Fecha'] >= start_date) & (filtered_df['Fecha'] <= end_date)]
    if selected_cats:
        filtered_df = filtered_df[filtered_df['Categoría'].isin(selected_cats)]
    if selected_type:
        filtered_df = filtered_df[filtered_df['Tipo'].isin(selected_type)]

    # Store filtered DF for callback usage (crucial for ID mapping)
    st.session_state["current_table_df"] = filtered_df

    # Configuration for columns
    column_config = {
        "id": None, # Hide ID
        "Fecha": st.column_config.DateColumn("Fecha", format="YYYY-MM-DD", required=True),
        # Use exclude_headers=True for the dropdown options
        "Categoría": st.column_config.SelectboxColumn("Categoría", options=em.db_get_categories(exclude_headers=True), required=True),
        "Descripción": st.column_config.TextColumn("Descripción", required=True),
        "Miembro": st.column_config.TextColumn("Miembro"),
        "Monto": st.column_config.NumberColumn("Monto", format="$%.2f", min_value=0.01, step=0.01, required=True),
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Gasto", "Ingreso"], required=True),
        "Método Pago": st.column_config.SelectboxColumn("Método Pago", options=em.DEFAULT_PAYMENT_METHODS, required=True)
    }

    st.data_editor(
        filtered_df,
        key="transactions_editor",
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        on_change=on_transactions_change
    )
    
    st.caption("Instrucciones: Edita directamente las celdas. Usa la fila inferior para agregar nuevos registros. Selecciona filas y presiona Supr para borrar.")

# --- SIDEBAR & MAIN ---

def main():
    local_css() # Apply CSS
    st.sidebar.title("Control de Gastos")
    
    # Year Selector
    current_year = get_current_year()
    selected_year = st.sidebar.number_input("Año Fiscal", min_value=2000, max_value=2100, value=current_year, step=1)
    
    # Export Section
    st.sidebar.markdown("### Acciones")
    
    export_type = st.sidebar.selectbox(
        "Datos a Exportar", 
        [
            "Movimientos (Todos)", 
            "Presupuesto de Gastos Planeado", 
            "Presupuesto Gastos Reales",
            "Presupuesto de Ingresos Planeado",
            "Presupuesto Ingresos Reales"
        ]
    )
    
    # Prepare Data based on selection
    if export_type == "Movimientos (Todos)":
        df_export = em.db_get_all_expenses_df()
        if 'id' in df_export.columns:
            df_export = df_export.drop(columns=['id'])
        file_name = f"movimientos_{datetime.date.today()}.csv"
    
    elif export_type == "Presupuesto de Gastos Planeado":
        df_export = em.db_get_budget_matrix(selected_year, ctype="Expense")
        df_export.columns = [em.MONTH_MAP.get(c, c) for c in df_export.columns]
        file_name = f"presupuesto_gastos_planeado_{selected_year}.csv"

    elif export_type == "Presupuesto Gastos Reales":
        df_export = em.db_get_real_expenses_matrix(selected_year)
        df_export.columns = [em.MONTH_MAP.get(c, c) for c in df_export.columns]
        file_name = f"presupuesto_gastos_reales_{selected_year}.csv"
        
    elif export_type == "Presupuesto de Ingresos Planeado":
        df_export = em.db_get_budget_matrix(selected_year, ctype="Income")
        df_export.columns = [em.MONTH_MAP.get(c, c) for c in df_export.columns]
        file_name = f"presupuesto_ingresos_planeado_{selected_year}.csv"

    else: # Presupuesto Ingresos Reales
        df_export = em.db_get_real_income_matrix(selected_year)
        df_export.columns = [em.MONTH_MAP.get(c, c) for c in df_export.columns]
        file_name = f"presupuesto_ingresos_reales_{selected_year}.csv"
    
    # Convert to CSV string (utf-8-sig for Excel compatibility)
    csv_data = df_export.to_csv(index=True if "Presupuesto" in export_type else False, encoding='utf-8-sig').encode('utf-8-sig')
    
    st.sidebar.download_button(
        label=f"📥 Descargar CSV",
        data=csv_data,
        file_name=file_name,
        mime="text/csv",
    )
    
    st.sidebar.divider()
    st.sidebar.info("Web App migrada con Streamlit")
    
    # Tabs
    t1, t2, t3, t4, t5 = st.tabs(["📊 Dashboard", "📅 Diario", "📉 Gastos", "📈 Ingresos", "📝 Movimientos"])
    
    with t1:
        tab_dashboard(selected_year)
    
    with t2:
        tab_daily(selected_year)

    with t3:
        tab_matrix_view(selected_year, "Gastos", "Expense")
        
    with t4:
        tab_matrix_view(selected_year, "Ingresos", "Income")
        
    with t5:
        tab_transactions()

if __name__ == "__main__":
    main()
