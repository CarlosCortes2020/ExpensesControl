import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
from .. import core as em

# Set theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class ExpenseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Expense Control Manager")
        self.geometry("1100x700")

        # Initialize DB
        em.init_db()

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Tab View
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.tab_dashboard = self.tab_view.add("Dashboard")
        self.tab_add = self.tab_view.add("Add Expense")
        self.tab_budget = self.tab_view.add("Set Budget")
        self.tab_history = self.tab_view.add("History")

        # Setup Tabs
        self.setup_dashboard_tab()
        self.setup_add_expense_tab()
        self.setup_budget_tab()
        self.setup_history_tab()

    def setup_dashboard_tab(self):
        # Configure grid
        self.tab_dashboard.grid_columnconfigure(0, weight=1)
        self.tab_dashboard.grid_rowconfigure(1, weight=1)

        # Control Frame
        control_frame = ctk.CTkFrame(self.tab_dashboard)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(control_frame, text="Year:").pack(side="left", padx=10)
        self.dashboard_year_var = ctk.StringVar(value=str(datetime.date.today().year))
        self.dashboard_year_entry = ctk.CTkEntry(control_frame, width=100, textvariable=self.dashboard_year_var)
        self.dashboard_year_entry.pack(side="left", padx=10)
        
        ctk.CTkButton(control_frame, text="Refresh", command=self.refresh_dashboard).pack(side="left", padx=10)

        self.summary_label = ctk.CTkLabel(control_frame, text="Total: 0 | Budget: 0", font=("Arial", 14, "bold"))
        self.summary_label.pack(side="right", padx=20)

        # Plot Frame
        self.plot_frame = ctk.CTkFrame(self.tab_dashboard)
        self.plot_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Initial Load
        self.after(100, self.refresh_dashboard)

    def refresh_dashboard(self):
        # Clear previous plots
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        try:
            year = int(self.dashboard_year_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid Year")
            return

        df_expenses, df_budgets = em.db_get_analytics_data(year)
        
        if df_expenses.empty:
            ctk.CTkLabel(self.plot_frame, text=f"No data for {year}", font=("Arial", 20)).pack(expand=True)
            self.summary_label.configure(text="Total: 0 | Budget: 0")
            return

        analysis = em.process_monthly_summary(df_expenses, df_budgets)
        
        total_exp = analysis['amount'].sum()
        total_budg = analysis['budget_amount'].sum()
        self.summary_label.configure(text=f"Total Expenses: ${total_exp:,.2f} | Total Budget: ${total_budg:,.2f}")

        # Create Figures
        fig = plt.Figure(figsize=(10, 8), dpi=100)
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)

        # Bar Chart
        months = range(1, 13)
        ax1.bar([x - 0.2 for x in months], analysis['budget_amount'], width=0.4, label='Budget', color='green', alpha=0.6)
        ax1.bar([x + 0.2 for x in months], analysis['amount'], width=0.4, label='Expenses', color='red', alpha=0.6)
        ax1.set_title('Monthly Budget vs Expenses')
        ax1.set_xticks(list(months))
        ax1.set_xticklabels([datetime.date(2000, m, 1).strftime('%b') for m in months])
        ax1.legend()

        # Pie Chart
        cat_expenses = df_expenses.groupby('category')['amount'].sum()
        ax2.pie(cat_expenses, labels=cat_expenses.index, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Expenses by Category')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    def setup_add_expense_tab(self):
        # Center Content
        frame = ctk.CTkFrame(self.tab_add)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Add New Expense", font=("Arial", 20, "bold")).pack(pady=20)

        # Date
        ctk.CTkLabel(frame, text="Date (YYYY-MM-DD):").pack(anchor="w", padx=50)
        self.date_entry = ctk.CTkEntry(frame, placeholder_text="YYYY-MM-DD")
        self.date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.date_entry.pack(fill="x", padx=50, pady=5)

        # Amount
        ctk.CTkLabel(frame, text="Amount:").pack(anchor="w", padx=50)
        self.amount_entry = ctk.CTkEntry(frame, placeholder_text="0.00")
        self.amount_entry.pack(fill="x", padx=50, pady=5)

        # Category
        ctk.CTkLabel(frame, text="Category:").pack(anchor="w", padx=50)
        self.categories = em.db_get_categories()
        self.category_var = ctk.StringVar(value=self.categories[0] if self.categories else "")
        self.category_menu = ctk.CTkOptionMenu(frame, variable=self.category_var, values=self.categories)
        self.category_menu.pack(fill="x", padx=50, pady=5)

        # Description
        ctk.CTkLabel(frame, text="Description:").pack(anchor="w", padx=50)
        self.desc_entry = ctk.CTkEntry(frame, placeholder_text="Optional description")
        self.desc_entry.pack(fill="x", padx=50, pady=5)

        # Submit
        ctk.CTkButton(frame, text="Add Expense", command=self.submit_expense, fg_color="green").pack(pady=30)

    def submit_expense(self):
        date = self.date_entry.get()
        amount_str = self.amount_entry.get()
        category = self.category_var.get()
        description = self.desc_entry.get()

        if not date or not amount_str or not category:
            messagebox.showwarning("Missing Info", "Please fill in all required fields.")
            return

        try:
            amount = float(amount_str)
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Input", "Invalid Date or Amount format.")
            return

        em.db_add_expense(date, category, amount, description)
        messagebox.showinfo("Success", "Expense Added!")
        
        # Clear inputs
        self.amount_entry.delete(0, "end")
        self.desc_entry.delete(0, "end")
        
        # Refresh other tabs
        self.refresh_dashboard()
        self.load_history()

    def setup_budget_tab(self):
        self.tab_budget.grid_columnconfigure(0, weight=1)
        self.tab_budget.grid_rowconfigure(1, weight=1)
        self.tab_budget.grid_rowconfigure(2, weight=0)

        # Control Frame (Year Selection & Add Category)
        control_frame = ctk.CTkFrame(self.tab_budget)
        control_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(control_frame, text="Budget Year:", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        
        self.budget_year_var = ctk.StringVar(value=str(datetime.date.today().year))
        self.budget_year_entry = ctk.CTkEntry(control_frame, width=100, textvariable=self.budget_year_var)
        self.budget_year_entry.pack(side="left", padx=10)
        self.budget_year_entry.bind("<Return>", lambda e: self.load_budget_data())
        self.budget_year_entry.bind("<FocusOut>", lambda e: self.load_budget_data())

        ctk.CTkButton(control_frame, text="Load", command=self.load_budget_data, width=80).pack(side="left", padx=10)
        
        # Add Category Button
        ctk.CTkButton(control_frame, text="Add Budget Type", command=self.add_new_category, fg_color="green").pack(side="right", padx=10)

        # Budget Table Frame (Scrollable)
        self.budget_table_frame = ctk.CTkScrollableFrame(self.tab_budget)
        self.budget_table_frame.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")

        # Chart Frame
        self.budget_chart_frame = ctk.CTkFrame(self.tab_budget, height=200)
        self.budget_chart_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Constants
        self.month_names_short = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        # Initial Load
        self.after(200, self.load_budget_data)

    def add_new_category(self):
        dialog = ctk.CTkInputDialog(text="Enter new category name:", title="New Budget Type")
        new_category = dialog.get_input()
        if new_category:
            if em.db_add_category(new_category):
                messagebox.showinfo("Success", f"Category '{new_category}' added.")
                self.load_budget_data() # Reload table
                # Also update dropdown in Add Expense tab
                self.categories = em.db_get_categories()
                self.category_menu.configure(values=self.categories)
            else:
                messagebox.showerror("Error", "Category already exists or invalid.")

    def load_budget_data(self):
        try:
            year = int(self.budget_year_var.get())
        except ValueError:
            return

        # Clear existing table widgets
        for widget in self.budget_table_frame.winfo_children():
            widget.destroy()

        # Fetch data
        categories = em.db_get_categories()
        _, df_budgets = em.db_get_analytics_data(year)
        
        # Prepare Data Map: (category, month) -> amount
        budget_map = {}
        if not df_budgets.empty:
            for _, row in df_budgets.iterrows():
                budget_map[(row['category'], int(row['month']))] = row['budget_amount']

        self.budget_entries = {}

        # --- Build Grid ---
        
        # Headers
        ctk.CTkLabel(self.budget_table_frame, text="Category", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        for i, m_name in enumerate(self.month_names_short):
            ctk.CTkLabel(self.budget_table_frame, text=m_name, font=("Arial", 12, "bold")).grid(row=0, column=i+1, padx=2, pady=5)

        # Rows
        for r, cat in enumerate(categories):
            row_idx = r + 1
            
            # Category Name Entry (Editable)
            cat_var = ctk.StringVar(value=cat)
            cat_entry = ctk.CTkEntry(self.budget_table_frame, textvariable=cat_var, width=120)
            cat_entry.grid(row=row_idx, column=0, padx=5, pady=2, sticky="w")
            
            cat_entry.bind("<FocusOut>", lambda e, old=cat, v=cat_var: self.on_category_rename(old, v))
            cat_entry.bind("<Return>", lambda e, old=cat, v=cat_var: self.on_category_rename(old, v))

            for m in range(1, 13):
                col_idx = m
                amount = budget_map.get((cat, m), 0.0)
                
                var = ctk.StringVar(value=f"{amount:.2f}")
                
                # Small entry
                entry = ctk.CTkEntry(self.budget_table_frame, textvariable=var, width=60)
                entry.grid(row=row_idx, column=col_idx, padx=2, pady=2)
                
                # Bind
                entry.bind("<FocusOut>", lambda e, c=cat, m=m, v=var: self.on_budget_change(c, m, v))
                entry.bind("<Return>", lambda e, c=cat, m=m, v=var: self.on_budget_change(c, m, v))
                
                self.budget_entries[(cat, m)] = var

        self.update_budget_chart(df_budgets, year)

    def on_category_rename(self, old_name, var):
        new_name = var.get().strip()
        if not new_name:
            # Revert if empty
            var.set(old_name)
            return
            
        if new_name == old_name:
            return

        success, msg = em.db_rename_category(old_name, new_name)
        if success:
            messagebox.showinfo("Success", f"Renamed '{old_name}' to '{new_name}'")
            # Update the dropdown in Add Expense tab
            self.categories = em.db_get_categories()
            self.category_menu.configure(values=self.categories)
            # If the renamed category was selected in the dropdown, update it
            if self.category_var.get() == old_name:
                self.category_var.set(new_name)
            
            # Reload grid to update bindings for budget cells
            self.load_budget_data()
        else:
            messagebox.showerror("Error", msg)
            var.set(old_name)

    def on_budget_change(self, category, month, var):
        try:
            year = int(self.budget_year_var.get())
            amount = float(var.get())
            em.db_set_budget(category, month, year, amount)
            # Re-fetch for chart only
            _, df_budgets = em.db_get_analytics_data(year)
            self.update_budget_chart(df_budgets, year)
            self.refresh_dashboard() # Update main dashboard too
        except ValueError:
            pass

    def update_budget_chart(self, df_budgets, year):
        for widget in self.budget_chart_frame.winfo_children():
            widget.destroy()

        # Aggregate by month for the trend chart
        budget_monthly = {m: 0.0 for m in range(1, 13)}
        if not df_budgets.empty:
            for _, row in df_budgets.iterrows():
                budget_monthly[int(row['month'])] += row['budget_amount']
        
        months = list(budget_monthly.keys())
        amounts = list(budget_monthly.values())

        fig = plt.Figure(figsize=(8, 3), dpi=100)
        ax = fig.add_subplot(111)
        
        ax.plot(months, amounts, marker='o', linestyle='-', color='blue', label='Total Monthly Budget')
        ax.fill_between(months, amounts, color='blue', alpha=0.1)
        
        ax.set_title(f'Total Budget Trend {year}')
        ax.set_xticks(months)
        ax.set_xticklabels(self.month_names_short)
        ax.grid(True, linestyle='--', alpha=0.6)

        canvas = FigureCanvasTkAgg(fig, master=self.budget_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    def setup_history_tab(self):
        # Use a Treeview for better column management
        # CustomTkinter doesn't have a Treeview, so we wrap a ttk.Treeview in a frame
        
        self.tab_history.grid_columnconfigure(0, weight=1)
        self.tab_history.grid_rowconfigure(1, weight=1)

        # Refresh Button
        ctk.CTkButton(self.tab_history, text="Refresh List", command=self.load_history).grid(row=0, column=0, pady=10)

        # Container for Treeview
        tree_frame = ctk.CTkFrame(self.tab_history)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")

        # Treeview
        columns = ("id", "date", "category", "amount", "description")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("amount", text="Amount")
        self.tree.heading("description", text="Description")

        self.tree.column("id", width=50)
        self.tree.column("date", width=100)
        self.tree.column("category", width=150)
        self.tree.column("amount", width=100)
        self.tree.column("description", width=300)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)

        self.load_history()

    def load_history(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        expenses = em.db_get_recent_expenses()
        for exp in expenses:
            self.tree.insert("", "end", values=(exp['id'], exp['date'], exp['category'], f"${exp['amount']:.2f}", exp['description']))
