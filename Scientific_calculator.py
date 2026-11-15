"""
Advanced Scientific Calculator
------------------------------------
Python 3.9+ | Standard library only | Tkinter GUI

Run:
    python Scientific_calculator.py

Features:
- Scientific calculator with DEG/RAD and inverse trig functions
- Safe AST-based expression evaluator (no eval)
- Memory: MC, MR, M+, M-, MS and Ans
- Calculation history panel (click an item to reuse it)
- Statistics: mean, median, mode, variance and standard deviation
- Unit converter: length, mass, temperature, speed, area, volume and time
- Equation solver: linear and quadratic equations
- Matrix calculator: add, subtract, multiply, determinant and inverse
- Complex number calculator
- Keyboard support and blue-and-white interface

"""

import ast
import math
import operator
import re
import statistics
import tkinter as tk
from tkinter import ttk, messagebox


# ---------------------------------------------------------------------------
# Safe mathematical expression evaluator
# ---------------------------------------------------------------------------

class SafeMathEvaluator:
    """Evaluate a restricted mathematical expression without Python eval()."""

    FUNCTIONS = {}
    CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}

    def __init__(self, degree_mode=True, answer=0):
        self.degree_mode = degree_mode
        self.answer = answer
        self._build_functions()

    def _build_functions(self):
        def angle_in(x):
            return math.radians(x) if self.degree_mode else x

        def angle_out(x):
            return math.degrees(x) if self.degree_mode else x

        self.FUNCTIONS = {
            "sin": lambda x: math.sin(angle_in(x)),
            "cos": lambda x: math.cos(angle_in(x)),
            "tan": lambda x: math.tan(angle_in(x)),
            "asin": lambda x: angle_out(math.asin(x)),
            "acos": lambda x: angle_out(math.acos(x)),
            "atan": lambda x: angle_out(math.atan(x)),
            "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
            "asinh": math.asinh, "acosh": math.acosh, "atanh": math.atanh,
            "sqrt": math.sqrt,
            "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
            "log": math.log10, "ln": math.log,
            "exp": math.exp, "abs": abs,
            "factorial": self._factorial,
            "floor": math.floor, "ceil": math.ceil,
            "round": round, "degrees": math.degrees, "radians": math.radians,
            "sign": lambda x: (x > 0) - (x < 0),
        }

    @staticmethod
    def _factorial(value):
        if not float(value).is_integer() or value < 0 or value > 170:
            raise ValueError("Factorial requires an integer from 0 to 170.")
        return math.factorial(int(value))

    def evaluate(self, expression):
        expression = expression.strip()
        if not expression:
            raise ValueError("Enter an expression.")

        # Calculator-friendly symbols and aliases.
        expression = expression.replace("×", "*").replace("÷", "/")
        expression = expression.replace("−", "-").replace("^", "**")
        expression = expression.replace("π", "pi").replace("Ans", "ans")
        expression = expression.replace("√", "sqrt")
        expression = expression.replace("²", "**2").replace("³", "**3")
        expression = expression.replace("!", "__FACT__")

        # Convert postfix factorial on a number or parenthesized expression.
        # Repeated passes support forms such as 5! and (3+2)!.
        expression = re.sub(r"(\([^()]*\))\s*__FACT__", r"factorial\1", expression)
        expression = re.sub(r"(\d+(?:\.\d+)?)\s*__FACT__", r"factorial(\1)", expression)
        if "__FACT__" in expression:
            raise ValueError("Use factorial after a number or closing parenthesis.")

        expression = re.sub(r"\bans\b", "ANS_VALUE", expression, flags=re.IGNORECASE)
        tree = ast.parse(expression, mode="eval")
        result = self._visit(tree.body)

        if isinstance(result, (int, float)):
            if not math.isfinite(float(result)):
                raise ValueError("Result is outside the finite numeric range.")
        elif isinstance(result, complex):
            if not math.isfinite(result.real) or not math.isfinite(result.imag):
                raise ValueError("Result is outside the finite numeric range.")
        else:
            raise ValueError("Unsupported result.")
        return result

    def _visit(self, node):
        binary_ops = {
            ast.Add: operator.add, ast.Sub: operator.sub,
            ast.Mult: operator.mul, ast.Div: operator.truediv,
            ast.Pow: operator.pow, ast.Mod: operator.mod,
            ast.FloorDiv: operator.floordiv,
        }
        unary_ops = {ast.UAdd: operator.pos, ast.USub: operator.neg}

        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            name = node.id.lower()
            if name == "ans_value":
                return self.answer
            if name in self.CONSTANTS:
                return self.CONSTANTS[name]
            raise ValueError(f"Unknown constant: {node.id}")
        if isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
            left, right = self._visit(node.left), self._visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10000:
                raise ValueError("Exponent is too large.")
            return binary_ops[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary_ops:
            return unary_ops[type(node.op)](self._visit(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id.lower()
            if name not in self.FUNCTIONS or node.keywords:
                raise ValueError(f"Function not allowed: {name}")
            args = [self._visit(arg) for arg in node.args]
            if len(args) not in (1, 2):
                raise ValueError("Functions accept one or two arguments.")
            return self.FUNCTIONS[name](*args)
        raise ValueError("Invalid or unsupported expression.")


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class MultifunctionalCalculator:
    BLUE = "#155A91"
    DARK_BLUE = "#0D416B"
    PALE_BLUE = "#E5F2FC"
    LIGHT_BG = "#F3F8FD"
    TEXT = "#123B5D"
    WHITE = "#FFFFFF"

    def __init__(self, root):
        self.root = root
        self.root.title("Multifunctional Scientific Calculator")
        self.root.geometry("1240x790")
        self.root.minsize(1080, 700)
        self.root.configure(bg=self.LIGHT_BG)

        self.expression = ""
        self.degree_mode = True
        self.inverse_mode = False
        self.memory = 0
        self.answer = 0
        self.history = []
        self.evaluator = SafeMathEvaluator(self.degree_mode, self.answer)

        self._configure_styles()
        self._build_header()
        self._build_main_area()
        self._build_keyboard_bindings()

    # ----- Styling and overall layout -------------------------------------

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background=self.LIGHT_BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(15, 9), font=("Arial", 10, "bold"),
                        background="#D8EAF8", foreground=self.TEXT)
        style.map("TNotebook.Tab", background=[("selected", self.BLUE)],
                  foreground=[("selected", self.WHITE)])
        style.configure("TFrame", background=self.LIGHT_BG)
        style.configure("TLabel", background=self.LIGHT_BG, foreground=self.TEXT,
                        font=("Arial", 10))
        style.configure("TLabelframe", background=self.LIGHT_BG, foreground=self.TEXT)
        style.configure("TLabelframe.Label", background=self.LIGHT_BG,
                        foreground=self.BLUE, font=("Arial", 10, "bold"))
        style.configure("TButton", font=("Arial", 10, "bold"), padding=7)
        style.configure("Blue.TButton", background=self.BLUE, foreground=self.WHITE)
        style.map("Blue.TButton", background=[("active", self.DARK_BLUE)])

    def _build_header(self):
        header = tk.Frame(self.root, bg=self.BLUE, height=58)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="ADVANCED SCIENTIFIC CALCULATOR",
                 bg=self.BLUE, fg=self.WHITE, font=("Arial", 17, "bold")).pack(
                     side="left", padx=22, pady=12)
        tk.Label(header, text="Scientific • Statistics • Converter • Matrices • Equations",
                 bg=self.BLUE, fg="#D9ECFA", font=("Arial", 9)).pack(
                     side="right", padx=20)

    def _build_main_area(self):
        body = tk.Frame(self.root, bg=self.LIGHT_BG)
        body.pack(fill="both", expand=True, padx=14, pady=12)

        workspace = tk.Frame(body, bg=self.LIGHT_BG)
        workspace.pack(side="left", fill="both", expand=True)

        history_frame = tk.LabelFrame(body, text="  Calculation History  ",
                                      bg=self.WHITE, fg=self.BLUE,
                                      font=("Arial", 10, "bold"), padx=8, pady=8,
                                      width=260)
        history_frame.pack(side="right", fill="y", padx=(12, 0))
        history_frame.pack_propagate(False)
        self.history_list = tk.Listbox(history_frame, font=("Consolas", 10),
                                       bg="#F8FBFE", fg=self.TEXT,
                                       selectbackground=self.BLUE, relief="flat",
                                       activestyle="none")
        self.history_list.pack(fill="both", expand=True)
        self.history_list.bind("<Double-Button-1>", self._reuse_history)
        tk.Button(history_frame, text="Use selected result", command=self._reuse_history,
                  bg=self.PALE_BLUE, fg=self.BLUE, relief="flat").pack(fill="x", pady=(8, 4))
        tk.Button(history_frame, text="Clear history", command=self._clear_history,
                  bg="#FCEAEA", fg="#9B2929", relief="flat").pack(fill="x")

        self.notebook = ttk.Notebook(workspace)
        self.notebook.pack(fill="both", expand=True)

        self.calc_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)
        self.converter_tab = ttk.Frame(self.notebook)
        self.equation_tab = ttk.Frame(self.notebook)
        self.matrix_tab = ttk.Frame(self.notebook)
        self.complex_tab = ttk.Frame(self.notebook)

        for tab, label in [
            (self.calc_tab, "Scientific"), (self.stats_tab, "Statistics"),
            (self.converter_tab, "Unit Converter"), (self.equation_tab, "Equation Solver"),
            (self.matrix_tab, "Matrix"), (self.complex_tab, "Complex Numbers")
        ]:
            self.notebook.add(tab, text=label)

        self._build_scientific_tab()
        self._build_statistics_tab()
        self._build_converter_tab()
        self._build_equation_tab()
        self._build_matrix_tab()
        self._build_complex_tab()

    # ----- Scientific calculator -----------------------------------------

    def _build_scientific_tab(self):
        frame = self.calc_tab
        display_area = tk.Frame(frame, bg=self.WHITE, padx=12, pady=12)
        display_area.pack(fill="x", padx=12, pady=12)

        self.expression_var = tk.StringVar(value="0")
        self.result_var = tk.StringVar(value="DEG | Ready")
        self.display = tk.Entry(display_area, textvariable=self.expression_var,
                                font=("Arial", 25, "bold"), justify="right",
                                bg=self.WHITE, fg=self.TEXT, relief="flat",
                                insertbackground=self.BLUE)
        self.display.pack(fill="x", ipady=9)
        self.display.bind("<KeyRelease>", self._sync_expression)
        tk.Label(display_area, textvariable=self.result_var, anchor="e",
                 bg=self.WHITE, fg="#66839B", font=("Arial", 10)).pack(fill="x")

        toolbar = tk.Frame(frame, bg=self.LIGHT_BG)
        toolbar.pack(fill="x", padx=12, pady=(0, 5))
        self.angle_button = tk.Button(toolbar, text="DEG", width=7,
                                      command=self._toggle_angle,
                                      bg=self.PALE_BLUE, fg=self.BLUE, relief="flat")
        self.angle_button.pack(side="left", padx=3)
        self.inverse_button = tk.Button(toolbar, text="INV OFF", width=9,
                                        command=self._toggle_inverse,
                                        bg=self.PALE_BLUE, fg=self.BLUE, relief="flat")
        self.inverse_button.pack(side="left", padx=3)
        for label, command in [
            ("MC", self._memory_clear), ("MR", self._memory_recall),
            ("M+", self._memory_add), ("M−", self._memory_subtract),
            ("MS", self._memory_store), ("Ans", lambda: self._insert("Ans"))
        ]:
            tk.Button(toolbar, text=label, command=command, width=5,
                      bg="#EAF3FA", fg=self.BLUE, relief="flat").pack(side="left", padx=2)

        self.keypad = tk.Frame(frame, bg=self.LIGHT_BG)
        self.keypad.pack(fill="both", expand=True, padx=12, pady=8)
        self.button_grid = [
            ["(", ")", "C", "⌫", "÷", "MC", "MR"],
            ["sin", "cos", "tan", "√", "x²", "xʸ", "×"],
            ["ln", "log", "π", "e", "x!", "1/x", "−"],
            ["7", "8", "9", "4", "5", "6", "+" , "="],
            ["1", "2", "3", "0", ".", "%", "EXP", "Ans"],
        ]
        self.normal_labels = [
            ["(", ")", "C", "⌫", "÷", "MC", "MR"],
            ["sin", "cos", "tan", "√", "x²", "xʸ", "×"],
            ["ln", "log", "π", "e", "x!", "1/x", "−"],
            ["7", "8", "9", "4", "5", "6", "+" , "="],
            ["1", "2", "3", "0", ".", "%", "EXP", "Ans"],
        ]
        self.inverse_labels = [
            ["(", ")", "C", "⌫", "÷", "MC", "MR"],
            ["asin", "acos", "atan", "cbrt", "x³", "10ˣ", "×"],
            ["sinh", "cosh", "tanh", "eˣ", "n!", "abs", "−"],
            ["7", "8", "9", "4", "5", "6", "+" , "="],
            ["1", "2", "3", "0", ".", "%", "EXP", "Ans"],
        ]
        self.calc_buttons = {}
        for r, row in enumerate(self.normal_labels):
            self.keypad.grid_rowconfigure(r, weight=1)
            for c, label in enumerate(row):
                self.keypad.grid_columnconfigure(c, weight=1)
                btn = tk.Button(self.keypad, text=label, font=("Arial", 11, "bold"),
                                bg=self.WHITE, fg=self.BLUE, activebackground="#C8E2F6",
                                relief="flat", bd=0, cursor="hand2",
                                command=lambda x=label: self._calculator_button(x))
                if label == "=":
                    btn.configure(bg=self.BLUE, fg=self.WHITE,
                                  activebackground=self.DARK_BLUE)
                elif label in ("C", "⌫"):
                    btn.configure(bg="#E4F0FA")
                btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3, ipady=8)
                self.calc_buttons[(r, c)] = btn

    def _sync_expression(self, _event=None):
        self.expression = self.expression_var.get()

    def _refresh_display(self):
        self.expression_var.set(self.expression or "0")
        self.display.icursor(tk.END)

    def _insert(self, value):
        if self.expression == "Error":
            self.expression = ""
        if self.expression == "0":
            self.expression = ""
        self.expression += str(value)
        self._refresh_display()

    def _calculator_button(self, label):
        self._sync_expression()
        if label == "C":
            self.expression = ""
        elif label == "⌫":
            self.expression = self.expression[:-1]
        elif label == "=":
            self._calculate()
            return
        elif label in ("MC", "MR"):
            self._memory_clear() if label == "MC" else self._memory_recall()
            return
        elif label == "π":
            self._insert("pi")
            return
        elif label == "e":
            self._insert("e")
            return
        elif label == "√":
            self._insert("sqrt(")
            return
        elif label == "cbrt":
            self._insert("cbrt(")
            return
        elif label in ("sin", "cos", "tan", "asin", "acos", "atan",
                       "sinh", "cosh", "tanh", "ln", "log", "abs"):
            self._insert(label + "(")
            return
        elif label == "x²":
            self._insert("**2")
            return
        elif label == "x³":
            self._insert("**3")
            return
        elif label == "xʸ":
            self._insert("**(")
            return
        elif label == "10ˣ":
            self._insert("10**(")
            return
        elif label == "eˣ":
            self._insert("exp(")
            return
        elif label == "1/x":
            self.expression = "1/(" + self.expression + ")"
        elif label == "x!":
            self._insert("!")
            return
        elif label == "n!":
            self._insert("factorial(")
            return
        elif label == "EXP":
            self._insert("*10**(")
            return
        elif label == "%":
            self._insert("/100")
            return
        elif label == "Ans":
            self._insert("Ans")
            return
        elif label == "÷":
            self._insert("/")
            return
        elif label == "×":
            self._insert("*")
            return
        elif label == "−":
            self._insert("-")
            return
        else:
            self._insert(label)
            return
        self._refresh_display()

    def _toggle_angle(self):
        self.degree_mode = not self.degree_mode
        self.angle_button.configure(text="DEG" if self.degree_mode else "RAD")
        self.result_var.set(("DEG" if self.degree_mode else "RAD") + " | Angle mode changed")
        self.evaluator.degree_mode = self.degree_mode

    def _toggle_inverse(self):
        self.inverse_mode = not self.inverse_mode
        labels = self.inverse_labels if self.inverse_mode else self.normal_labels
        for r, row in enumerate(labels):
            for c, label in enumerate(row):
                btn = self.calc_buttons[(r, c)]
                btn.configure(text=label, command=lambda x=label: self._calculator_button(x))
                if label == "=":
                    btn.configure(bg=self.BLUE, fg=self.WHITE)
                elif label in ("C", "⌫"):
                    btn.configure(bg="#E4F0FA", fg=self.BLUE)
                else:
                    btn.configure(bg=self.WHITE, fg=self.BLUE)
        self.inverse_button.configure(
            text="INV ON" if self.inverse_mode else "INV OFF",
            bg="#C8E2F6" if self.inverse_mode else self.PALE_BLUE
        )

    def _calculate(self):
        self._sync_expression()
        original = self.expression
        try:
            self.evaluator.degree_mode = self.degree_mode
            self.evaluator.answer = self.answer
            result = self.evaluator.evaluate(original)
            self.answer = result
            self.expression = self._format_number(result)
            self._add_history(original, self.expression)
            self.result_var.set("Result copied to Ans")
        except Exception as exc:
            self.expression = "Error"
            self.result_var.set(str(exc))
        self._refresh_display()

    @staticmethod
    def _format_number(value):
        if isinstance(value, complex):
            return str(value)
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return f"{value:.12g}"
        return str(value)

    def _current_numeric_value(self):
        self.evaluator.degree_mode = self.degree_mode
        self.evaluator.answer = self.answer
        return self.evaluator.evaluate(self.expression)

    def _memory_clear(self):
        self.memory = 0
        self.result_var.set("Memory cleared")

    def _memory_recall(self):
        self._insert(self._format_number(self.memory))
        self.result_var.set("Memory recalled")

    def _memory_add(self):
        try:
            self.memory += self._current_numeric_value()
            self.result_var.set("Added to memory")
        except Exception as exc:
            messagebox.showerror("Memory", str(exc))

    def _memory_subtract(self):
        try:
            self.memory -= self._current_numeric_value()
            self.result_var.set("Subtracted from memory")
        except Exception as exc:
            messagebox.showerror("Memory", str(exc))

    def _memory_store(self):
        try:
            self.memory = self._current_numeric_value()
            self.result_var.set("Value stored in memory")
        except Exception as exc:
            messagebox.showerror("Memory", str(exc))

    # ----- History --------------------------------------------------------

    def _add_history(self, expression, result):
        self.history.insert(0, (expression, result))
        self.history_list.insert(0, f"{expression} = {result}")

    def _reuse_history(self, _event=None):
        selection = self.history_list.curselection()
        if selection:
            expression, result = self.history[selection[0]]
            self.expression = result
            self._refresh_display()
            self.notebook.select(self.calc_tab)

    def _clear_history(self):
        self.history.clear()
        self.history_list.delete(0, tk.END)

    # ----- Statistics -----------------------------------------------------

    def _build_statistics_tab(self):
        frame = self.stats_tab
        ttk.Label(frame, text="Enter numbers separated by commas or spaces:",
                  font=("Arial", 11, "bold")).pack(anchor="w", padx=18, pady=(20, 8))
        self.stats_input = tk.Text(frame, height=5, font=("Consolas", 12),
                                   bg=self.WHITE, fg=self.TEXT, relief="solid", bd=1)
        self.stats_input.pack(fill="x", padx=18)
        self.stats_input.insert("1.0", "10, 12, 15, 15, 18, 20")
        ttk.Button(frame, text="Calculate statistics", style="Blue.TButton",
                   command=self._calculate_statistics).pack(anchor="w", padx=18, pady=12)
        self.stats_output = tk.Text(frame, height=14, font=("Consolas", 11),
                                    bg=self.WHITE, fg=self.TEXT, relief="flat")
        self.stats_output.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def _calculate_statistics(self):
        try:
            raw = self.stats_input.get("1.0", "end").strip()
            values = [float(x) for x in re.split(r"[\s,;]+", raw) if x]
            if not values:
                raise ValueError("Enter at least one number.")
            modes = statistics.multimode(values)
            lines = [
                f"Count:                  {len(values)}",
                f"Sum:                    {sum(values):.10g}",
                f"Mean:                   {statistics.mean(values):.10g}",
                f"Median:                 {statistics.median(values):.10g}",
                f"Mode(s):                {', '.join(map(str, modes))}",
                f"Minimum:                {min(values):.10g}",
                f"Maximum:                {max(values):.10g}",
                f"Range:                  {max(values)-min(values):.10g}",
                f"Population variance:    {statistics.pvariance(values):.10g}",
                f"Population std. dev.:   {statistics.pstdev(values):.10g}",
            ]
            if len(values) >= 2:
                lines += [
                    f"Sample variance:        {statistics.variance(values):.10g}",
                    f"Sample std. dev.:       {statistics.stdev(values):.10g}",
                ]
            self.stats_output.delete("1.0", tk.END)
            self.stats_output.insert("1.0", "\n".join(lines))
        except Exception as exc:
            messagebox.showerror("Statistics error", str(exc))

    # ----- Unit converter -------------------------------------------------

    def _build_converter_tab(self):
        frame = self.converter_tab
        units = {
            "Length": {"Millimeter": 0.001, "Centimeter": 0.01, "Meter": 1,
                       "Kilometer": 1000, "Inch": 0.0254, "Foot": 0.3048,
                       "Yard": 0.9144, "Mile": 1609.344},
            "Mass": {"Milligram": 0.000001, "Gram": 0.001, "Kilogram": 1,
                     "Tonne": 1000, "Ounce": 0.028349523125, "Pound": 0.45359237},
            "Speed": {"m/s": 1, "km/h": 1/3.6, "mph": 0.44704, "knot": 0.514444},
            "Area": {"mm²": 1e-6, "cm²": 1e-4, "m²": 1, "km²": 1e6,
                     "hectare": 10000, "acre": 4046.8564224},
            "Volume": {"mL": 0.001, "Liter": 1, "m³": 1000, "US gallon": 3.785411784,
                       "Cup (US)": 0.2365882365},
            "Time": {"Second": 1, "Minute": 60, "Hour": 3600,
                     "Day": 86400, "Week": 604800},
        }
        self.unit_definitions = units
        pad = tk.Frame(frame, bg=self.LIGHT_BG)
        pad.pack(anchor="nw", padx=24, pady=24)
        ttk.Label(pad, text="Category").grid(row=0, column=0, sticky="w", pady=7)
        self.unit_category = tk.StringVar(value="Length")
        category_box = ttk.Combobox(pad, textvariable=self.unit_category,
                                    values=list(units) + ["Temperature"],
                                    state="readonly", width=22)
        category_box.grid(row=0, column=1, padx=10, pady=7)
        category_box.bind("<<ComboboxSelected>>", self._update_unit_choices)

        ttk.Label(pad, text="Value").grid(row=1, column=0, sticky="w", pady=7)
        self.unit_value = tk.StringVar(value="1")
        ttk.Entry(pad, textvariable=self.unit_value, width=25).grid(row=1, column=1, padx=10, pady=7)
        ttk.Label(pad, text="From").grid(row=2, column=0, sticky="w", pady=7)
        self.unit_from = tk.StringVar()
        self.unit_from_box = ttk.Combobox(pad, textvariable=self.unit_from, state="readonly", width=22)
        self.unit_from_box.grid(row=2, column=1, padx=10, pady=7)
        ttk.Label(pad, text="To").grid(row=3, column=0, sticky="w", pady=7)
        self.unit_to = tk.StringVar()
        self.unit_to_box = ttk.Combobox(pad, textvariable=self.unit_to, state="readonly", width=22)
        self.unit_to_box.grid(row=3, column=1, padx=10, pady=7)
        ttk.Button(pad, text="Convert", style="Blue.TButton",
                   command=self._convert_units).grid(row=4, column=1, sticky="w", padx=10, pady=12)
        self.unit_result = tk.StringVar(value="Result will appear here")
        ttk.Label(pad, textvariable=self.unit_result, font=("Arial", 15, "bold"),
                  foreground=self.BLUE).grid(row=5, column=0, columnspan=3, sticky="w", pady=16)
        self._update_unit_choices()

    def _update_unit_choices(self, _event=None):
        category = self.unit_category.get()
        if category == "Temperature":
            choices = ["Celsius", "Fahrenheit", "Kelvin"]
        else:
            choices = list(self.unit_definitions[category])
        self.unit_from_box["values"] = choices
        self.unit_to_box["values"] = choices
        self.unit_from.set(choices[0])
        self.unit_to.set(choices[1] if len(choices) > 1 else choices[0])

    def _convert_units(self):
        try:
            value = float(self.unit_value.get())
            category = self.unit_category.get()
            source, target = self.unit_from.get(), self.unit_to.get()
            if category == "Temperature":
                to_c = {
                    "Celsius": lambda x: x,
                    "Fahrenheit": lambda x: (x - 32) * 5/9,
                    "Kelvin": lambda x: x - 273.15,
                }
                from_c = {
                    "Celsius": lambda x: x,
                    "Fahrenheit": lambda x: x * 9/5 + 32,
                    "Kelvin": lambda x: x + 273.15,
                }
                result = from_c[target](to_c[source](value))
            else:
                factors = self.unit_definitions[category]
                result = value * factors[source] / factors[target]
            self.unit_result.set(f"{value:g} {source} = {result:.12g} {target}")
        except Exception as exc:
            messagebox.showerror("Conversion error", str(exc))

    # ----- Equation solver ------------------------------------------------

    def _build_equation_tab(self):
        frame = self.equation_tab
        content = tk.Frame(frame, bg=self.LIGHT_BG)
        content.pack(anchor="nw", padx=24, pady=24)
        ttk.Label(content, text="Linear equation: ax + b = 0",
                  font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        self.linear_a = tk.StringVar(value="2")
        self.linear_b = tk.StringVar(value="-8")
        ttk.Label(content, text="a").grid(row=1, column=0)
        ttk.Entry(content, textvariable=self.linear_a, width=12).grid(row=1, column=1, padx=6)
        ttk.Label(content, text="b").grid(row=1, column=2)
        ttk.Entry(content, textvariable=self.linear_b, width=12).grid(row=1, column=3, padx=6)
        ttk.Button(content, text="Solve linear", style="Blue.TButton",
                   command=self._solve_linear).grid(row=1, column=4, padx=12)

        ttk.Label(content, text="Quadratic equation: ax² + bx + c = 0",
                  font=("Arial", 12, "bold")).grid(row=3, column=0, columnspan=5, sticky="w", pady=(28, 8))
        self.quad_a = tk.StringVar(value="1")
        self.quad_b = tk.StringVar(value="-5")
        self.quad_c = tk.StringVar(value="6")
        for i, (label, var) in enumerate([("a", self.quad_a), ("b", self.quad_b), ("c", self.quad_c)]):
            ttk.Label(content, text=label).grid(row=4, column=i*2)
            ttk.Entry(content, textvariable=var, width=12).grid(row=4, column=i*2+1, padx=6)
        ttk.Button(content, text="Solve quadratic", style="Blue.TButton",
                   command=self._solve_quadratic).grid(row=4, column=6, padx=12)
        self.equation_result = tk.Text(frame, height=9, font=("Consolas", 11),
                                       bg=self.WHITE, fg=self.TEXT, relief="flat")
        self.equation_result.pack(fill="x", padx=24, pady=10)

    def _show_equation_result(self, text):
        self.equation_result.delete("1.0", tk.END)
        self.equation_result.insert("1.0", text)

    def _solve_linear(self):
        try:
            a, b = float(self.linear_a.get()), float(self.linear_b.get())
            if a == 0:
                result = "If b = 0, every x is a solution." if b == 0 else "No solution."
            else:
                result = f"x = {-b/a:.12g}"
            self._show_equation_result("Linear equation result\n" + result)
        except Exception as exc:
            messagebox.showerror("Equation error", str(exc))

    def _solve_quadratic(self):
        try:
            a, b, c = map(float, (self.quad_a.get(), self.quad_b.get(), self.quad_c.get()))
            if a == 0:
                if b == 0:
                    result = "Not a quadratic equation. If c=0, every x works; otherwise no solution."
                else:
                    result = f"Linear equation: x = {-c/b:.12g}"
            else:
                discriminant = b*b - 4*a*c
                if discriminant >= 0:
                    root = math.sqrt(discriminant)
                    x1, x2 = (-b + root)/(2*a), (-b - root)/(2*a)
                    result = f"Discriminant = {discriminant:g}\nx₁ = {x1:.12g}\nx₂ = {x2:.12g}"
                else:
                    real = -b/(2*a)
                    imag = math.sqrt(-discriminant)/(2*abs(a))
                    result = (f"Discriminant = {discriminant:g}\n"
                              f"x₁ = {real:.12g} + {imag:.12g}i\n"
                              f"x₂ = {real:.12g} - {imag:.12g}i")
            self._show_equation_result("Quadratic equation result\n" + result)
        except Exception as exc:
            messagebox.showerror("Equation error", str(exc))

    # ----- Matrix calculator ---------------------------------------------

    def _build_matrix_tab(self):
        frame = self.matrix_tab
        ttk.Label(frame, text="Enter matrices as rows separated by semicolons; values separated by commas.",
                  wraplength=850).pack(anchor="w", padx=18, pady=(18, 8))
        self.matrix_a = tk.StringVar(value="1,2;3,4")
        self.matrix_b = tk.StringVar(value="5,6;7,8")
        area = tk.Frame(frame, bg=self.LIGHT_BG)
        area.pack(anchor="w", padx=18)
        ttk.Label(area, text="Matrix A").grid(row=0, column=0, sticky="w")
        ttk.Entry(area, textvariable=self.matrix_a, width=38).grid(row=1, column=0, padx=(0, 18), pady=5)
        ttk.Label(area, text="Matrix B").grid(row=0, column=1, sticky="w")
        ttk.Entry(area, textvariable=self.matrix_b, width=38).grid(row=1, column=1, pady=5)
        controls = tk.Frame(frame, bg=self.LIGHT_BG)
        controls.pack(anchor="w", padx=18, pady=8)
        for label, operation_name in [
            ("A + B", "add"), ("A − B", "subtract"), ("A × B", "multiply"),
            ("det(A)", "det"), ("A⁻¹", "inverse")
        ]:
            ttk.Button(controls, text=label,
                       command=lambda op=operation_name: self._matrix_calculate(op)).pack(side="left", padx=3)
        self.matrix_output = tk.Text(frame, height=13, font=("Consolas", 11),
                                     bg=self.WHITE, fg=self.TEXT, relief="flat")
        self.matrix_output.pack(fill="both", expand=True, padx=18, pady=10)

    @staticmethod
    def _parse_matrix(raw):
        rows = [[float(x.strip()) for x in row.split(",") if x.strip()]
                for row in raw.strip().split(";")]
        if not rows or any(not row for row in rows):
            raise ValueError("Matrix cannot contain empty rows.")
        if len({len(row) for row in rows}) != 1:
            raise ValueError("Every matrix row must have the same number of columns.")
        if len(rows) > 10 or len(rows[0]) > 10:
            raise ValueError("Matrix dimensions are limited to 10 × 10.")
        return rows

    @staticmethod
    def _determinant(matrix):
        n = len(matrix)
        if n == 0 or any(len(row) != n for row in matrix):
            raise ValueError("Determinant requires a square matrix.")
        a = [row[:] for row in matrix]
        det, sign = 1.0, 1
        for col in range(n):
            pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
            if abs(a[pivot][col]) < 1e-12:
                return 0.0
            if pivot != col:
                a[col], a[pivot] = a[pivot], a[col]
                sign *= -1
            value = a[col][col]
            det *= value
            for row in range(col + 1, n):
                factor = a[row][col] / value
                for j in range(col + 1, n):
                    a[row][j] -= factor * a[col][j]
        return det * sign

    @classmethod
    def _inverse_matrix(cls, matrix):
        n = len(matrix)
        if n == 0 or any(len(row) != n for row in matrix):
            raise ValueError("Inverse requires a square matrix.")
        a = [matrix[i][:] + [float(i == j) for j in range(n)] for i in range(n)]
        for col in range(n):
            pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
            if abs(a[pivot][col]) < 1e-12:
                raise ValueError("Matrix is singular and has no inverse.")
            a[col], a[pivot] = a[pivot], a[col]
            divisor = a[col][col]
            a[col] = [x / divisor for x in a[col]]
            for row in range(n):
                if row != col:
                    factor = a[row][col]
                    a[row] = [a[row][j] - factor*a[col][j] for j in range(2*n)]
        return [row[n:] for row in a]

    def _matrix_calculate(self, operation_name):
        try:
            a = self._parse_matrix(self.matrix_a.get())
            if operation_name == "det":
                result = self._determinant(a)
            elif operation_name == "inverse":
                result = self._inverse_matrix(a)
            else:
                b = self._parse_matrix(self.matrix_b.get())
                if operation_name in ("add", "subtract"):
                    if len(a) != len(b) or len(a[0]) != len(b[0]):
                        raise ValueError("Addition/subtraction requires equal dimensions.")
                    fn = operator.add if operation_name == "add" else operator.sub
                    result = [[fn(a[i][j], b[i][j]) for j in range(len(a[0]))]
                              for i in range(len(a))]
                else:
                    if len(a[0]) != len(b):
                        raise ValueError("For A × B, columns of A must equal rows of B.")
                    result = [[sum(a[i][k]*b[k][j] for k in range(len(b)))
                               for j in range(len(b[0]))] for i in range(len(a))]
            self.matrix_output.delete("1.0", tk.END)
            self.matrix_output.insert("1.0", str(result))
        except Exception as exc:
            messagebox.showerror("Matrix error", str(exc))

    # ----- Complex number calculator -------------------------------------

    def _build_complex_tab(self):
        frame = self.complex_tab
        area = tk.Frame(frame, bg=self.LIGHT_BG)
        area.pack(anchor="nw", padx=24, pady=24)
        ttk.Label(area, text="Complex number A = a + bi",
                  font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        self.complex_ar = tk.StringVar(value="3")
        self.complex_ai = tk.StringVar(value="2")
        ttk.Label(area, text="Real part").grid(row=1, column=0, sticky="w")
        ttk.Entry(area, textvariable=self.complex_ar, width=12).grid(row=1, column=1, padx=5)
        ttk.Label(area, text="Imaginary part").grid(row=1, column=2, sticky="w")
        ttk.Entry(area, textvariable=self.complex_ai, width=12).grid(row=1, column=3, padx=5)
        ttk.Label(area, text="Complex number B = c + di",
                  font=("Arial", 11, "bold")).grid(row=2, column=0, columnspan=4, sticky="w", pady=(22, 8))
        self.complex_br = tk.StringVar(value="1")
        self.complex_bi = tk.StringVar(value="-4")
        ttk.Label(area, text="Real part").grid(row=3, column=0, sticky="w")
        ttk.Entry(area, textvariable=self.complex_br, width=12).grid(row=3, column=1, padx=5)
        ttk.Label(area, text="Imaginary part").grid(row=3, column=2, sticky="w")
        ttk.Entry(area, textvariable=self.complex_bi, width=12).grid(row=3, column=3, padx=5)
        buttons = tk.Frame(frame, bg=self.LIGHT_BG)
        buttons.pack(anchor="w", padx=24, pady=8)
        for label, op_name in [("A + B", "add"), ("A − B", "sub"), ("A × B", "mul"),
                               ("A ÷ B", "div"),("|A|", "abs"), ("Conjugate A", "conj"),
                               ("Polar A", "polar")]:
            ttk.Button(buttons, text=label,
                       command=lambda op=op_name: self._complex_calculate(op)).pack(
                           side="left", padx=3, pady=3)
        self.complex_output = tk.StringVar(value="Results appear here")
        ttk.Label(frame, textvariable=self.complex_output, font=("Consolas", 13, "bold"),
                  wraplength=850).pack(anchor="w", padx=24, pady=20)

    def _complex_calculate(self, operation_name):
        try:
            a = complex(float(self.complex_ar.get()), float(self.complex_ai.get()))
            b = complex(float(self.complex_br.get()), float(self.complex_bi.get()))
            operations = {
                "add": lambda: a + b, "sub": lambda: a - b,
                "mul": lambda: a * b, "div": lambda: a / b,
                "abs": lambda: abs(a), "conj": lambda: a.conjugate(),
                "polar": lambda: f"r = {abs(a):.12g}, θ = {math.degrees(math.atan2(a.imag, a.real)):.12g}°",
            }
            self.complex_output.set(f"Result: {operations[operation_name]()}")
        except ZeroDivisionError:
            messagebox.showerror("Complex calculation", "Cannot divide by zero.")
        except Exception as exc:
            messagebox.showerror("Complex calculation", str(exc))

    # ----- Keyboard -------------------------------------------------------

    def _build_keyboard_bindings(self):
        self.root.bind("<Return>", self._keyboard_enter)
        self.root.bind("<KP_Enter>", self._keyboard_enter)
        self.root.bind("<Escape>", lambda _e: self._clear_from_keyboard())
        self.root.bind("<Control-l>", lambda _e: self._clear_from_keyboard())
        self.root.bind("<Control-m>", lambda _e: self._memory_store())
        self.root.bind("<Control-r>", lambda _e: self._memory_recall())

    def _keyboard_enter(self, _event=None):
        if self.notebook.select() == str(self.calc_tab):
            self._calculate()
        return "break"

    def _clear_from_keyboard(self):
        if self.notebook.select() == str(self.calc_tab):
            self.expression = ""
            self._refresh_display()
        return "break"


def main():
    root = tk.Tk()
    app = MultifunctionalCalculator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
