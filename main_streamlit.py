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
    
    # We need the original dataframe to look up IDs for updates/deletes
    # It must be stored in session_state BEFORE the editor is rendered
    if "original_transactions_df" not in st.session_state:
        return

    original_df = st.session_state["original_transactions_df"]
    
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
        
        em.db_add_expense(date, category, amount, description, t_type, member)

    # 2. DELETED ROWS
    # state["deleted_rows"] is a list of integers (indices of the displayed dataframe)
    # We must match these indices to the ORIGINAL dataframe to get the ID.
    # Note: If the user filters or sorts within the editor, indices might shift if not handled carefully,
    # but st.data_editor usually respects the original index if not reset.
    # However, to be safe, we rely on the fact that the editor was initialized with original_df.
    if state["deleted_rows"]:
        for idx in state["deleted_rows"]:
            try:
                # Get the ID from the original dataframe at this index
                # We use iloc because deleted_rows returns positional indices of the data passed to the editor
                expense_id = original_df.iloc[idx]['id']
                em.db_delete_expense(expense_id)
            except IndexError:
                pass # Should not happen if sync is correct

    # 3. EDITED ROWS
    # state["edited_rows"] is a dict {row_index: {col_name: new_value}}
    for idx, changes in state["edited_rows"].items():
        try:
            expense_id = original_df.iloc[idx]['id']
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
    
    # Metrics
    total_income = analysis['income_amount'].sum()
    total_expense = analysis['expense_amount'].sum()
    balance = total_income - total_expense
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos Reales", f"${total_income:,.2f}", delta_color="normal")
    col2.metric("Gastos Reales", f"${total_expense:,.2f}", delta="-"+f"${total_expense:,.2f}", delta_color="inverse")
    col3.metric("Balance", f"${balance:,.2f}", delta_color="normal" if balance >= 0 else "inverse")
    
    st.divider()
    
    # Charts
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # 1. Line Chart: Trend
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=analysis['month'], y=analysis['income_amount'], mode='lines+markers', name='Ingresos', line=dict(color='#27AE60', width=3)))
        fig_trend.add_trace(go.Scatter(x=analysis['month'], y=analysis['expense_amount'], mode='lines+markers', name='Gastos', line=dict(color='#E74C3C', width=3)))
        fig_trend.update_layout(
            title="Evolución Financiera Anual", 
            xaxis_title="Mes", 
            yaxis_title="Monto", 
            template="plotly_white",
            yaxis_tickformat=',.2f'
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        # 2. Donut Chart: Expenses
        if not df_expenses.empty:
            cat_summary = df_expenses.groupby('category')['amount'].sum().reset_index()
            fig_pie = px.pie(cat_summary, values='amount', names='category', title='Distribución de Gastos', hole=0.4)
            fig_pie.update_traces(textinfo='percent+label', hovertemplate='Categoría: %{label}<br>Monto: $%{value:,.2f}')
            fig_pie.update_layout(template="plotly_white")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sin datos de gastos para mostrar gráfico circular.")

    # 3. Bar Chart: Budget vs Real
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=analysis['month'], y=analysis['budget_amount'], name='Presupuesto', marker_color='#34495E'))
    fig_bar.add_trace(go.Bar(x=analysis['month'], y=analysis['expense_amount'], name='Real', marker_color='#E74C3C'))
    fig_bar.update_layout(
        title="Presupuesto vs Ejecución (Gastos)", 
        xaxis_title="Mes", 
        yaxis_title="Monto", 
        barmode='group', 
        template="plotly_white",
        yaxis_tickformat=',.2f'
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
        
        # To make it editable and easier to save, we keep it as is.
        # Streamlit Data Editor
        budget_cols_config = {
            str(m): st.column_config.NumberColumn(str(m), format="$%.2f", min_value=0, step=0.01)
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
            # df has index=CategoryName, columns=1..12 (integers or strings depending on load)
            for category in edited_budget.index:
                for month in edited_budget.columns:
                    try:
                        amount = float(edited_budget.loc[category, month])
                        em.db_set_budget(category, int(month), year, amount)
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
            
        st.dataframe(df_real.style.format("{:,.2f}"), use_container_width=True)

    # Comparison / Variance (Optional enhancement)
    st.markdown("---")
    st.markdown("**Comparativa Mensual**")
    
    # Simple difference matrix
    # Ensure indices align
    common_index = df_budget.index.union(df_real.index)
    df_budget_aligned = df_budget.reindex(common_index).fillna(0)
    df_real_aligned = df_real.reindex(common_index).fillna(0)
    
    # Ensure columns match (months 1-12)
    for m in range(1, 13):
        if m not in df_budget_aligned.columns: df_budget_aligned[m] = 0.0
        if m not in df_real_aligned.columns: df_real_aligned[m] = 0.0
    
    # Sort columns
    df_budget_aligned = df_budget_aligned[sorted(df_budget_aligned.columns)]
    df_real_aligned = df_real_aligned[sorted(df_real_aligned.columns)]

    if db_type == "Expense":
        # Variance = Budget - Real (Positive is good/under budget)
        diff = df_budget_aligned - df_real_aligned
    else:
        # Variance = Real - Budget (Positive is good/over income)
        diff = df_real_aligned - df_budget_aligned
        
    st.dataframe(diff.style.format("{:,.2f}").applymap(lambda x: 'color: green' if x >= 0 else 'color: red'), use_container_width=True)


def tab_transactions():
    st.subheader("Registro de Movimientos")
    
    # Load Data
    df = em.db_get_all_expenses_df()
    
    # Ensure 'Fecha' is datetime objects for st.data_editor (required by DateColumn)
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
    
    # Store original in session state for ID lookup during edits
    st.session_state["original_transactions_df"] = df
    
    # Configuration for columns
    column_config = {
        "id": None, # Hide ID
        "Fecha": st.column_config.DateColumn("Fecha", format="YYYY-MM-DD", required=True),
        "Categoría": st.column_config.SelectboxColumn("Categoría", options=em.db_get_categories(), required=True),
        "Descripción": st.column_config.TextColumn("Descripción", required=True),
        "Miembro": st.column_config.TextColumn("Miembro"),
        "Monto": st.column_config.NumberColumn("Monto", format="$%.2f", min_value=0.01, step=0.01, required=True),
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Gasto", "Ingreso"], required=True)
    }

    st.data_editor(
        df,
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
    st.sidebar.title("Control de Gastos")
    
    # Year Selector
    current_year = get_current_year()
    selected_year = st.sidebar.number_input("Año Fiscal", min_value=2000, max_value=2100, value=current_year, step=1)
    
    st.sidebar.divider()
    st.sidebar.info("Web App migrada con Streamlit")
    
    # Tabs
    t1, t2, t3, t4 = st.tabs(["📊 Dashboard", "📉 Gastos", "📈 Ingresos", "📝 Movimientos"])
    
    with t1:
        tab_dashboard(selected_year)
    
    with t2:
        tab_matrix_view(selected_year, "Gastos", "Expense")
        
    with t3:
        tab_matrix_view(selected_year, "Ingresos", "Income")
        
    with t4:
        tab_transactions()

if __name__ == "__main__":
    main()
