import sys
import json
import random
from decimal import Decimal, getcontext, ROUND_HALF_UP
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QFormLayout, QSpinBox, QCheckBox, QFrame, QSlider,
    QRadioButton, QTableWidget, QTableWidgetItem, QAbstractItemView, QAbstractScrollArea
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QBrush, QColor

# Exact decimal math
getcontext().prec = 100
getcontext().rounding = ROUND_HALF_UP


def _app_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    base = Path(__file__).resolve().parent if '__file__' in globals() else Path(sys.argv[0]).resolve().parent
    return base


def _prefs_path() -> Path:
    return _app_dir() / "preferences.json"


def _prefs_exist_and_valid() -> bool:
    p = _prefs_path()
    if not p.exists():
        return False
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return isinstance(data, dict)
    except Exception:
        return False


class ArithmeticTrainer(QWidget):
    def __init__(self):
        super().__init__()

        # Game state
        self.score = 0
        self.time_left = 120
        self.operator = '+'
        self.num1 = Decimal(0)
        self.num2 = Decimal(0)
        self.mode = "range"  # "range" or "sigfigs"
        self.history = []         # list of {"problem","user","correct","ok"}
        self.history_table = None

        # Flash baseline
        self._base_stylesheet = ""
        self._base_stylesheet_saved = False
        self._flash_restore_timer = QTimer(self)
        self._flash_restore_timer.setSingleShot(True)

        # UI
        self.initUI()

        if not self._base_stylesheet_saved:
            self._base_stylesheet = self.styleSheet()
            self._base_stylesheet_saved = True

        # Load prefs if present
        self._load_preferences_if_any()

        # Initial screen
        if _prefs_exist_and_valid():
            self.show_home_screen()
        else:
            self.show_preferences_screen()

    # ---------------- UI BUILD ----------------
    def initUI(self):
        self.setWindowTitle("Arithmetic Trainer")
        self.setGeometry(100, 100, 600, 840)

        self.root = QVBoxLayout(self)

        # Home (Start + Preferences)
        self.home_panel = QFrame(self)
        home_layout = QHBoxLayout(self.home_panel)
        self.home_start_button = QPushButton("Start", self)
        self.home_start_button.setStyleSheet("font-size: 18px;")
        self.home_start_button.clicked.connect(self.start_game)
        self.home_prefs_button = QPushButton("Preferences…", self)
        self.home_prefs_button.setStyleSheet("font-size: 18px;")
        self.home_prefs_button.clicked.connect(self.show_preferences_screen)
        home_layout.addWidget(self.home_start_button)
        home_layout.addWidget(self.home_prefs_button)

        # Preferences panel
        self.settings_panel = QFrame(self)
        self.settings_panel.setFrameShape(QFrame.StyledPanel)
        self.form_layout = QFormLayout(self.settings_panel)

        # Mode toggle
        mode_row = QHBoxLayout()
        self.range_mode_radio = QRadioButton("Range mode")
        self.sigfigs_mode_radio = QRadioButton("Significant figures mode")
        self.range_mode_radio.setChecked(True)
        self.range_mode_radio.toggled.connect(self._on_mode_toggle)
        mode_row.addWidget(self.range_mode_radio)
        mode_row.addWidget(self.sigfigs_mode_radio)
        self.form_layout.addRow(QLabel("Problem mode:"), mode_row)

        # Operation selection
        self.addition_checkbox = QCheckBox("Addition"); self.addition_checkbox.setChecked(True)
        self.form_layout.addRow(self.addition_checkbox)

        # Addition ranges (A + B)
        add_ranges = QHBoxLayout()
        self.addition_range1_spinbox1 = QSpinBox(self); self.addition_range1_spinbox1.setRange(1, 100); self.addition_range1_spinbox1.setValue(2)
        self.addition_range1_spinbox2 = QSpinBox(self); self.addition_range1_spinbox2.setRange(1, 100); self.addition_range1_spinbox2.setValue(100)
        add_ranges.addWidget(self.addition_range1_spinbox1); add_ranges.addWidget(self.addition_range1_spinbox2)
        add_ranges.addWidget(QLabel("+"))
        self.addition_range2_spinbox1 = QSpinBox(self); self.addition_range2_spinbox1.setRange(1, 100); self.addition_range2_spinbox1.setValue(2)
        self.addition_range2_spinbox2 = QSpinBox(self); self.addition_range2_spinbox2.setRange(1, 100); self.addition_range2_spinbox2.setValue(100)
        add_ranges.addWidget(self.addition_range2_spinbox1); add_ranges.addWidget(self.addition_range2_spinbox2)
        self.form_layout.addRow(QLabel("Add/Sub ranges (A + B):"), add_ranges)

        self.subtraction_checkbox = QCheckBox("Subtraction"); self.subtraction_checkbox.setChecked(True)
        self.form_layout.addRow(self.subtraction_checkbox)

        self.multiplication_checkbox = QCheckBox("Multiplication"); self.multiplication_checkbox.setChecked(True)
        self.form_layout.addRow(self.multiplication_checkbox)

        # Multiplication / Division ranges (X × Y)
        mul_ranges = QHBoxLayout()
        self.multiplication_range1_spinbox1 = QSpinBox(self); self.multiplication_range1_spinbox1.setRange(1, 100); self.multiplication_range1_spinbox1.setValue(2)
        self.multiplication_range1_spinbox2 = QSpinBox(self); self.multiplication_range1_spinbox2.setRange(1, 100); self.multiplication_range1_spinbox2.setValue(12)
        mul_ranges.addWidget(self.multiplication_range1_spinbox1); mul_ranges.addWidget(self.multiplication_range1_spinbox2)
        mul_ranges.addWidget(QLabel("×"))
        self.multiplication_range2_spinbox1 = QSpinBox(self); self.multiplication_range2_spinbox1.setRange(1, 100); self.multiplication_range2_spinbox1.setValue(2)
        self.multiplication_range2_spinbox2 = QSpinBox(self); self.multiplication_range2_spinbox2.setRange(1, 100); self.multiplication_range2_spinbox2.setValue(100)
        mul_ranges.addWidget(self.multiplication_range2_spinbox1); mul_ranges.addWidget(self.multiplication_range2_spinbox2)
        self.form_layout.addRow(QLabel("Mul/Div ranges (X × Y):"), mul_ranges)

        self.division_checkbox = QCheckBox("Division"); self.division_checkbox.setChecked(True)
        self.form_layout.addRow(self.division_checkbox)

        # Weights (discrete sliders 0–5)
        self.form_layout.addRow(QLabel("<b>Operation weights (0–5)</b>"))
        self.add_weight_slider, self.add_weight_label = self._make_weight_slider(default=3)
        self.sub_weight_slider, self.sub_weight_label = self._make_weight_slider(default=3)
        self.mul_weight_slider, self.mul_weight_label = self._make_weight_slider(default=3)
        self.div_weight_slider, self.div_weight_label = self._make_weight_slider(default=3)
        self.form_layout.addRow(self._row_with_label("Addition weight:", self.add_weight_slider, self.add_weight_label))
        self.form_layout.addRow(self._row_with_label("Subtraction weight:", self.sub_weight_slider, self.sub_weight_label))
        self.form_layout.addRow(self._row_with_label("Multiplication weight:", self.mul_weight_slider, self.mul_weight_label))
        self.form_layout.addRow(self._row_with_label("Division weight:", self.div_weight_slider, self.div_weight_label))

        # Sig-figs settings (A/B specs)
        self.form_layout.addRow(QLabel("<b>Sig-figs settings</b> (used only in Significant figures mode)"))
        a_sig_row = QHBoxLayout()
        self.a_sig_min = QSpinBox(self); self.a_sig_min.setRange(1, 6); self.a_sig_min.setValue(2)
        self.a_sig_max = QSpinBox(self); self.a_sig_max.setRange(1, 6); self.a_sig_max.setValue(3)
        a_sig_row.addWidget(QLabel("A sig figs:")); a_sig_row.addWidget(self.a_sig_min); a_sig_row.addWidget(QLabel("to")); a_sig_row.addWidget(self.a_sig_max)
        a_exp_row = QHBoxLayout()
        self.a_exp_min = QSpinBox(self); self.a_exp_min.setRange(-6, 6); self.a_exp_min.setValue(-2)
        self.a_exp_max = QSpinBox(self); self.a_exp_max.setRange(-6, 6); self.a_exp_max.setValue(3)
        a_exp_row.addWidget(QLabel("A exponent 10^(")); a_exp_row.addWidget(self.a_exp_min); a_exp_row.addWidget(QLabel(") to 10^(")); a_exp_row.addWidget(self.a_exp_max); a_exp_row.addWidget(QLabel(")"))
        self.form_layout.addRow(a_sig_row); self.form_layout.addRow(a_exp_row)

        b_sig_row = QHBoxLayout()
        self.b_sig_min = QSpinBox(self); self.b_sig_min.setRange(1, 6); self.b_sig_min.setValue(2)
        self.b_sig_max = QSpinBox(self); self.b_sig_max.setRange(1, 6); self.b_sig_max.setValue(3)
        b_sig_row.addWidget(QLabel("B sig figs:")); b_sig_row.addWidget(self.b_sig_min); b_sig_row.addWidget(QLabel("to")); b_sig_row.addWidget(self.b_sig_max)
        b_exp_row = QHBoxLayout()
        self.b_exp_min = QSpinBox(self); self.b_exp_min.setRange(-6, 6); self.b_exp_min.setValue(-2)
        self.b_exp_max = QSpinBox(self); self.b_exp_max.setRange(-6, 6); self.b_exp_max.setValue(3)
        b_exp_row.addWidget(QLabel("B exponent 10^(")); b_exp_row.addWidget(self.b_exp_min); b_exp_row.addWidget(QLabel(") to 10^(")); b_exp_row.addWidget(self.b_exp_max); b_exp_row.addWidget(QLabel(")"))
        self.form_layout.addRow(b_sig_row); self.form_layout.addRow(b_exp_row)

        # Max solution sig figs (per operator) — used ONLY to FILTER generation
        row_mul = QHBoxLayout()
        self.max_sig_mul_spin = QSpinBox(self); self.max_sig_mul_spin.setRange(1, 20); self.max_sig_mul_spin.setValue(4)
        row_mul.addWidget(QLabel("Max solution sig figs for ×:")); row_mul.addWidget(self.max_sig_mul_spin)
        self.form_layout.addRow(row_mul)

        row_div = QHBoxLayout()
        self.max_sig_div_spin = QSpinBox(self); self.max_sig_div_spin.setRange(1, 20); self.max_sig_div_spin.setValue(4)
        row_div.addWidget(QLabel("Max solution sig figs for ÷:")); row_div.addWidget(self.max_sig_div_spin)
        self.form_layout.addRow(row_div)

        row_add = QHBoxLayout()
        self.max_sig_add_spin = QSpinBox(self); self.max_sig_add_spin.setRange(1, 20); self.max_sig_add_spin.setValue(5)
        row_add.addWidget(QLabel("Max solution sig figs for +:")); row_add.addWidget(self.max_sig_add_spin)
        self.form_layout.addRow(row_add)

        row_sub = QHBoxLayout()
        self.max_sig_sub_spin = QSpinBox(self); self.max_sig_sub_spin.setRange(1, 20); self.max_sig_sub_spin.setValue(5)
        row_sub.addWidget(QLabel("Max solution sig figs for −:")); row_sub.addWidget(self.max_sig_sub_spin)
        self.form_layout.addRow(row_sub)

        # Feedback toggles
        fb1 = QHBoxLayout()
        self.toggle_flash_incorrect = QCheckBox("Flash screen for incorrect answers"); self.toggle_flash_incorrect.setChecked(True)
        fb1.addWidget(self.toggle_flash_incorrect); self.form_layout.addRow(fb1)

        fb2 = QHBoxLayout()
        self.toggle_show_correct = QCheckBox("Show correct answer"); self.toggle_show_correct.setChecked(True)
        self.toggle_show_correct.toggled.connect(self._on_show_correct_toggled)
        fb2.addWidget(self.toggle_show_correct); self.form_layout.addRow(fb2)

        fb3 = QHBoxLayout()
        self.toggle_show_problem_text = QCheckBox("Show problem text in feedback"); self.toggle_show_problem_text.setChecked(False)
        fb3.addWidget(self.toggle_show_problem_text); self.form_layout.addRow(fb3)

        # Game time
        self.form_layout.addRow(QLabel("<b>Game time</b>"))
        time_row = QHBoxLayout()
        self.game_time_spinbox = QSpinBox(self); self.game_time_spinbox.setRange(30, 600); self.game_time_spinbox.setValue(120)
        time_row.addWidget(QLabel("Seconds:")); time_row.addWidget(self.game_time_spinbox)
        self.form_layout.addRow(time_row)

        # Save/Back (Preferences)
        prefs_btn_row = QHBoxLayout()
        self.save_prefs_button = QPushButton("Save my choices")
        self.save_prefs_button.clicked.connect(self._on_save_clicked)
        self.back_to_home_button = QPushButton("Back")
        self.back_to_home_button.clicked.connect(self.show_home_screen)
        prefs_btn_row.addWidget(self.save_prefs_button)
        prefs_btn_row.addWidget(self.back_to_home_button)
        self.form_layout.addRow(prefs_btn_row)

        # Gameplay widgets
        self.problem_label = QLabel("", self); self.problem_label.setStyleSheet("font-size: 28px; font-weight: 600;")
        self.answer_entry = QLineEdit(self); self.answer_entry.setStyleSheet("font-size: 24px;"); self.answer_entry.setAlignment(Qt.AlignCenter)
        self.answer_entry.returnPressed.connect(self.check_answer)
        self.result_label = QLabel("", self); self.result_label.setStyleSheet("font-size: 18px; min-height: 36px;")
        self.score_label = QLabel(f"Score: {self.score}", self); self.score_label.setStyleSheet("font-size: 18px;")
        self.timer_label = QLabel(f"Time left: {self.time_left} s", self); self.timer_label.setStyleSheet("font-size: 18px;")
        self.back_button = QPushButton("Back"); self.back_button.setStyleSheet("font-size: 18px;")
        self.back_button.clicked.connect(self.show_home_screen); self.back_button.hide()

        # Assemble root
        self.root.addWidget(self.home_panel)
        self.root.addWidget(self.settings_panel)
        self.root.addSpacing(8)
        self.root.addWidget(self.problem_label)
        self.root.addWidget(self.answer_entry)
        self.root.addWidget(self.result_label)
        self.root.addWidget(self.score_label)
        self.root.addWidget(self.timer_label)
        self.root.addWidget(self.back_button)
        self.setLayout(self.root)

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self._hide_game_widgets()

    # ---------------- UI helpers ----------------
    def _make_weight_slider(self, default: int = 3):
        s = QSlider(Qt.Horizontal)
        s.setRange(0, 5)
        s.setSingleStep(1)
        s.setPageStep(1)
        s.setTickPosition(QSlider.TicksBelow)
        s.setTickInterval(1)
        s.setValue(default)
        label = QLabel(str(default))
        s.valueChanged.connect(lambda v, lbl=label: lbl.setText(str(v)))
        return s, label

    def _row_with_label(self, title: str, widget, trailing_label: QLabel):
        box = QHBoxLayout()
        box.addWidget(QLabel(title))
        box.addWidget(widget, stretch=1)
        box.addWidget(trailing_label)
        return box

    def _on_mode_toggle(self, _):
        self.mode = "range" if self.range_mode_radio.isChecked() else "sigfigs"

    def _on_show_correct_toggled(self, checked: bool):
        # When no correct-answer feedback, also disable flashing (no indicators)
        if not checked:
            self.toggle_show_problem_text.setChecked(False)
            self.toggle_show_problem_text.setEnabled(False)
        else:
            self.toggle_show_problem_text.setEnabled(True)

    # ---------------- Screens ----------------
    def _hide_game_widgets(self):
        self.problem_label.hide()
        self.answer_entry.hide()
        self.result_label.hide()
        self.score_label.hide()
        self.timer_label.hide()
        self.back_button.hide()

    def _remove_history_table(self):
        if self.history_table is not None:
            self.root.removeWidget(self.history_table)
            self.history_table.deleteLater()
            self.history_table = None

    def show_home_screen(self):
        self.home_panel.show()
        self.settings_panel.hide()
        self._hide_game_widgets()
        self.back_button.hide()
        if not self.history:
            self._remove_history_table()

    def show_preferences_screen(self):
        self.home_panel.hide()
        self.settings_panel.show()
        self._hide_game_widgets()
        self._remove_history_table()

    def show_game_screen(self):
        self.home_panel.hide()
        self.settings_panel.hide()
        self.problem_label.show()
        self.answer_entry.show()
        self.result_label.show()
        self.score_label.show()
        self.timer_label.show()
        self.back_button.hide()
        self._remove_history_table()

    def show_end_screen(self):
        self.show_home_screen()
        self._build_history_table()

    # ---------------- Results table ----------------
    def _build_history_table(self):
        self._remove_history_table()
        table = QTableWidget(self)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Problem", "Your answer", "Correct answer"])
        table.setRowCount(len(self.history))
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setStyleSheet("font-size: 14px;")
        table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setMinimumHeight(240)
        table.setMaximumHeight(520)

        green = QBrush(QColor(215, 245, 223))
        red = QBrush(QColor(255, 221, 221))

        for r, item in enumerate(self.history):
            prob = QTableWidgetItem(item["problem"])
            yours = QTableWidgetItem(item["user"])
            corr = QTableWidgetItem(item["correct"])
            table.setItem(r, 0, prob)
            table.setItem(r, 1, yours)
            table.setItem(r, 2, corr)
            brush = green if item["ok"] else red
            for c in range(3):
                table.item(r, c).setBackground(brush)

        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        self.root.addWidget(table)
        self.history_table = table

    # ---------------- Decimal helpers ----------------
    @staticmethod
    def _format_num(v) -> str:
        d = Decimal(v) if not isinstance(v, Decimal) else v
        if d == d.to_integral_value():
            return str(d.quantize(Decimal('1')))
        s = format(d.normalize(), 'f')
        if '.' in s:
            s = s.rstrip('0').rstrip('.')
        return s

    @staticmethod
    def _sigfigs(d: Decimal) -> int:
        if not isinstance(d, Decimal):
            d = Decimal(d)
        if d.is_zero():
            return 1
        dn = d.normalize()
        return len(dn.as_tuple().digits)

    @staticmethod
    def _decimal_places_leq_one(x: Decimal) -> bool:
        if x == x.to_integral_value():
            return True
        try:
            return x == x.quantize(Decimal('0.1'))
        except Exception:
            return False

    @staticmethod
    def _norm(a: int, b: int):
        return (a, b) if a <= b else (b, a)

    def _get_add_ranges(self):
        a1 = self.addition_range1_spinbox1.value()
        a2 = self.addition_range1_spinbox2.value()
        b1 = self.addition_range2_spinbox1.value()
        b2 = self.addition_range2_spinbox2.value()
        return self._norm(a1, a2), self._norm(b1, b2)

    def _get_mul_ranges(self):
        x1 = self.multiplication_range1_spinbox1.value()
        x2 = self.multiplication_range1_spinbox2.value()
        y1 = self.multiplication_range2_spinbox1.value()
        y2 = self.multiplication_range2_spinbox2.value()
        return self._norm(x1, x2), self._norm(y1, y2)

    def _compute_answer_decimal(self, n1, n2, op) -> Decimal:
        d1, d2 = (n1 if isinstance(n1, Decimal) else Decimal(n1)), (n2 if isinstance(n2, Decimal) else Decimal(n2))
        if op == '+': return d1 + d2
        if op == '-': return d1 - d2
        if op == '*': return d1 * d2
        if op == '/': return d1 / d2
        raise ValueError("Unknown operator")

    def _round_to_sigfigs(self, x: Decimal, sig: int) -> Decimal:
        if x.is_zero():
            return Decimal('0')
        shift = - (x.adjusted())
        quant = Decimal(1).scaleb(shift + (sig - 1))
        y = (x * quant).to_integral_value(rounding=ROUND_HALF_UP)
        return y / quant

    # Random exact sig-fig value (avoid mantissas ending in 0 so count is stable after normalize)
    def _rand_sigfig_value(self, sf_min, sf_max, exp_min, exp_max) -> Decimal:
        sf_lo, sf_hi = self._norm(sf_min, sf_max)
        k_lo, k_hi = self._norm(exp_min, exp_max)
        sf = random.randint(sf_lo, sf_hi)
        k = random.randint(k_lo, k_hi)

        m_lo = 10 ** (sf - 1)
        m_hi = 10 ** sf - 1
        while True:
            m = random.randint(m_lo, m_hi)
            if m % 10 != 0 or sf == 1:
                break

        val = Decimal(m) * (Decimal(10) ** Decimal(k - (sf - 1)))
        return val.normalize()

    def _rand_quotient_max_one_decimal(self) -> Decimal:
        # Ensures finite decimal with ≤1 decimal place
        if random.random() < 0.5:
            q = Decimal(random.randint(-99, 99))
            if q == 0:
                q = Decimal(1)
            return q
        else:
            k = random.randint(-990, 990)
            if k % 10 == 0:
                k += 1
            q = Decimal(k) / Decimal(10)
            if abs(q) < Decimal('0.1'):
                q = Decimal('0.1') if q >= 0 else Decimal('-0.1')
            return q

    # ---------------- Operator weighting ----------------
    def _weighted_choice_operator(self):
        ops = []
        weights = []
        if self.addition_checkbox.isChecked():      ops.append('+'); weights.append(self.add_weight_slider.value())
        if self.subtraction_checkbox.isChecked():   ops.append('-'); weights.append(self.sub_weight_slider.value())
        if self.multiplication_checkbox.isChecked():ops.append('*'); weights.append(self.mul_weight_slider.value())
        if self.division_checkbox.isChecked():      ops.append('/'); weights.append(self.div_weight_slider.value())
        if not ops:
            return None
        if any(w > 0 for w in weights):
            ops_f = [op for op, w in zip(ops, weights) if w > 0]
            weights_f = [w for w in weights if w > 0]
            return random.choices(ops_f, weights=weights_f, k=1)[0]
        return random.choice(ops)

    # ---------------- Result caps (filter only) ----------------
    def _cap_ok_for_result(self, op: str, result: Decimal) -> bool:
        s = self._sigfigs(result)
        if op == '+':  return s <= self.max_sig_add_spin.value()
        if op == '-':  return s <= self.max_sig_sub_spin.value()
        if op == '*':  return s <= self.max_sig_mul_spin.value()
        if op == '/':  return s <= self.max_sig_div_spin.value() and self._decimal_places_leq_one(result)
        return True

    # ---------------- Problem generation ----------------
    def generate_problem(self):
        op = self._weighted_choice_operator()
        if not op:
            self.problem_label.setText("Select at least one operation.")
            return
        self.operator = op

        last_pair = None
        for _ in range(800):  # try hard to honor every preference
            if self.mode == "range":
                if op in ('+', '-'):
                    (a_lo, a_hi), (b_lo, b_hi) = self._get_add_ranges()
                    n1 = Decimal(random.randint(a_lo, a_hi))
                    n2 = Decimal(random.randint(b_lo, b_hi))
                    if op == '-' and n1 < n2:
                        n1, n2 = n2, n1
                else:  # * or /
                    (x_lo, x_hi), (y_lo, y_hi) = self._get_mul_ranges()
                    n1i = random.randint(x_lo, x_hi)
                    n2i = random.randint(y_lo, y_hi)
                    if op == '/':
                        n1 = Decimal(n1i * n2i)  # integer quotient
                        n2 = Decimal(n2i)
                    else:
                        n1 = Decimal(n1i)
                        n2 = Decimal(n2i)
                last_pair = (n1, n2)
                res = self._compute_answer_decimal(n1, n2, op)
                if self._cap_ok_for_result(op, res):
                    break

            else:  # sigfigs mode
                if op == '/':
                    # Build division so that result is EXACT with ≤1 decimal and operands match requested sig-fig ranges.
                    A_min, A_max = self.a_sig_min.value(), self.a_sig_max.value()
                    B_min, B_max = self.b_sig_min.value(), self.b_sig_max.value()

                    built = False
                    for _attempt in range(400):
                        use_A_for_left = random.choice([True, False])
                        # pick desired sig counts for the two roles
                        sfa = random.randint(*self._norm(A_min, A_max))
                        sfb = random.randint(*self._norm(B_min, B_max))

                        # build divisor first (respect its intended range depending on which side it maps to)
                        if use_A_for_left:
                            # left uses A-spec, right (divisor) uses B-spec
                            b = self._rand_sigfig_value(self.b_sig_min.value(), self.b_sig_max.value(),
                                                        self.b_exp_min.value(), self.b_exp_max.value())
                            if not (B_min <= self._sigfigs(b) <= B_max) or b == 0:
                                continue
                            q = self._rand_quotient_max_one_decimal()  # exact finite decimal with ≤1 dp
                            a = q * b  # DO NOT ROUND; shape by rejection
                            if self._sigfigs(a) != sfa:
                                continue
                            res = a / b  # == q exactly
                            if not self._cap_ok_for_result('/', res):
                                continue
                            last_pair = (a, b)
                            built = True
                            break
                        else:
                            # left uses B-spec, right (divisor) uses A-spec
                            b = self._rand_sigfig_value(self.a_sig_min.value(), self.a_sig_max.value(),
                                                        self.a_exp_min.value(), self.a_exp_max.value())
                            if not (A_min <= self._sigfigs(b) <= A_max) or b == 0:
                                continue
                            q = self._rand_quotient_max_one_decimal()
                            a = q * b
                            if self._sigfigs(a) != sfb:
                                continue
                            res = a / b
                            if not self._cap_ok_for_result('/', res):
                                continue
                            # Put operands so that left operand corresponds to B-spec, right to A-spec
                            last_pair = (a, b)  # still a / b
                            built = True
                            break
                    if built:
                        break

                    # last resort: simple integer quotient respecting caps
                    n2 = Decimal(random.randint(2, 99))
                    q = Decimal(random.randint(1, 99))
                    n1 = n2 * q
                    res = n1 / n2
                    if self._cap_ok_for_result('/', res):
                        last_pair = (n1, n2)
                        break

                else:
                    # +, -, *
                    use_A_for_left = random.choice([True, False])
                    a_val = self._rand_sigfig_value(self.a_sig_min.value(), self.a_sig_max.value(),
                                                    self.a_exp_min.value(), self.a_exp_max.value())
                    b_val = self._rand_sigfig_value(self.b_sig_min.value(), self.b_sig_max.value(),
                                                    self.b_exp_min.value(), self.b_exp_max.value())
                    n1, n2 = (a_val, b_val) if use_A_for_left else (b_val, a_val)
                    if op == '-' and n1 < n2:
                        n1, n2 = n2, n1
                    res = self._compute_answer_decimal(n1, n2, op)
                    if self._cap_ok_for_result(op, res):
                        last_pair = (n1, n2)
                        break

        # Use the last acceptable pair
        if last_pair is None:
            self.operator = '+'
            self.num1, self.num2 = Decimal(1), Decimal(1)
        else:
            self.num1, self.num2 = last_pair

        self.problem_label.setText(f"{self._format_num(self.num1)} {self.operator} {self._format_num(self.num2)}")

    # ---------------- Game flow ----------------
    def start_game(self):
        self.history = []
        self.score = 0
        self.time_left = self.game_time_spinbox.value()
        self.score_label.setText(f"Score: {self.score}")
        self.timer_label.setText(f"Time left: {self.time_left} s")
        self.result_label.setText("")
        self.generate_problem()
        self.show_game_screen()
        self.timer.start(1000)
        self.answer_entry.setFocus()
        self.answer_entry.selectAll()

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.setText(f"Time left: {self.time_left} s")
        else:
            self.end_game()

    def check_answer(self):
        if not self.answer_entry.isVisible():
            return
        user_text = self.answer_entry.text().strip()
        try:
            user_dec = Decimal(user_text)
        except Exception:
            if self.toggle_show_correct.isChecked():
                self.result_label.setText("Please enter a valid number!")
            self._do_flash('red')
            return

        true_dec = self._compute_answer_decimal(self.num1, self.num2, self.operator)  # EXACT, never rounded
        ok = (user_dec == true_dec)

        prob_str = f"{self._format_num(self.num1)} {self.operator} {self._format_num(self.num2)}"
        corr_str = self._format_num(true_dec)
        user_str = self._format_num(user_dec)

        if self.toggle_show_correct.isChecked():
            if ok:
                msg = "Correct!"
                self._do_flash('green')
            else:
                if self.toggle_show_problem_text.isChecked():
                    msg = f"The correct answer to {prob_str} is {corr_str}"
                else:
                    msg = f"The correct answer to the last problem was: {corr_str}"
                self._do_flash('red')
            self.result_label.setText(msg)
        else:
            self.result_label.setText("")
            # no indicator in this mode

        if ok:
            self.score += 1

        self.history.append({"problem": prob_str, "user": user_str, "correct": corr_str, "ok": ok})
        self.score_label.setText(f"Score: {self.score}")

        self.answer_entry.selectAll()
        self.generate_problem()


    # Flash helper honoring toggles + robust restore
    def _do_flash(self, color: str):
        if not self.toggle_show_correct.isChecked():
            return
        if color == 'red' and not self.toggle_flash_incorrect.isChecked():
            return
        if self._flash_restore_timer.isActive():
            self._flash_restore_timer.stop()
        flash_css = "background-color: #3ddc84;" if color == 'green' else "background-color: #ff6b6b;"
        self.setStyleSheet(flash_css)
        try:
            if self._flash_restore_timer.receivers(self._flash_restore_timer.timeout):
                self._flash_restore_timer.timeout.disconnect()
        except Exception:
            pass
        self._flash_restore_timer.timeout.connect(lambda: self.setStyleSheet(self._base_stylesheet))
        self._flash_restore_timer.start(120)

    def end_game(self):
        self.timer.stop()
        self.show_end_screen()

    # ---------------- Preferences (save/load) ----------------
    def _collect_preferences(self) -> dict:
        return {
            "mode": self.mode,
            "ops": {
                "+": self.addition_checkbox.isChecked(),
                "-": self.subtraction_checkbox.isChecked(),
                "*": self.multiplication_checkbox.isChecked(),
                "/": self.division_checkbox.isChecked(),
            },
            "ranges": {
                "add_A": [self.addition_range1_spinbox1.value(), self.addition_range1_spinbox2.value()],
                "add_B": [self.addition_range2_spinbox1.value(), self.addition_range2_spinbox2.value()],
                "mul_X": [self.multiplication_range1_spinbox1.value(), self.multiplication_range1_spinbox2.value()],
                "mul_Y": [self.multiplication_range2_spinbox1.value(), self.multiplication_range2_spinbox2.value()],
            },
            "weights": {
                "+": self.add_weight_slider.value(),
                "-": self.sub_weight_slider.value(),
                "*": self.mul_weight_slider.value(),
                "/": self.div_weight_slider.value(),
            },
            "sigfigs": {
                "A_sig": [self.a_sig_min.value(), self.a_sig_max.value()],
                "A_exp": [self.a_exp_min.value(), self.a_exp_max.value()],
                "B_sig": [self.b_sig_min.value(), self.b_sig_max.value()],
                "B_exp": [self.b_exp_min.value(), self.b_exp_max.value()],
            },
            "max_solution_sigfigs": {
                "*": self.max_sig_mul_spin.value(),
                "/": self.max_sig_div_spin.value(),
                "+": self.max_sig_add_spin.value(),
                "-": self.max_sig_sub_spin.value(),
            },
            "game_time": self.game_time_spinbox.value(),
            "radio": {
                "range_checked": self.range_mode_radio.isChecked(),
                "sig_checked": self.sigfigs_mode_radio.isChecked(),
            },
            "toggles": {
                "flash_incorrect": self.toggle_flash_incorrect.isChecked(),
                "show_correct": self.toggle_show_correct.isChecked(),
                "show_problem_text": self.toggle_show_problem_text.isChecked()
            }
        }

    def _apply_preferences(self, prefs: dict) -> bool:
        try:
            mode = prefs.get("mode", "range")
            if mode not in ("range", "sigfigs"): return False

            ops = prefs.get("ops", {})
            ranges = prefs.get("ranges", {})
            weights = prefs.get("weights", {})
            sfs = prefs.get("sigfigs", {})
            maxsol = prefs.get("max_solution_sigfigs", {})
            game_time = int(prefs.get("game_time", 120))
            toggles = prefs.get("toggles", {})

            # Ops
            self.addition_checkbox.setChecked(bool(ops.get("+", True)))
            self.subtraction_checkbox.setChecked(bool(ops.get("-", True)))
            self.multiplication_checkbox.setChecked(bool(ops.get("*", True)))
            self.division_checkbox.setChecked(bool(ops.get("/", True)))

            # Ranges
            def _set_pair(spin_lo, spin_hi, pair):
                if not isinstance(pair, list) or len(pair) != 2: return
                a, b = int(pair[0]), int(pair[1])
                spin_lo.setValue(max(spin_lo.minimum(), min(spin_lo.maximum(), a)))
                spin_hi.setValue(max(spin_hi.minimum(), min(spin_hi.maximum(), b)))
            _set_pair(self.addition_range1_spinbox1, self.addition_range1_spinbox2, ranges.get("add_A", [2, 100]))
            _set_pair(self.addition_range2_spinbox1, self.addition_range2_spinbox2, ranges.get("add_B", [2, 100]))
            _set_pair(self.multiplication_range1_spinbox1, self.multiplication_range1_spinbox2, ranges.get("mul_X", [2, 12]))
            _set_pair(self.multiplication_range2_spinbox1, self.multiplication_range2_spinbox2, ranges.get("mul_Y", [2, 100]))

            # Weights
            def _set_slider(slider, v):
                slider.setValue(max(slider.minimum(), min(slider.maximum(), int(v))))
            _set_slider(self.add_weight_slider, weights.get("+", 3))
            _set_slider(self.sub_weight_slider, weights.get("-", 3))
            _set_slider(self.mul_weight_slider, weights.get("*", 3))
            _set_slider(self.div_weight_slider, weights.get("/", 3))

            # Sig figs & exponents
            def _set_pair_spin(spin_lo, spin_hi, pair):
                if not isinstance(pair, list) or len(pair) != 2: return
                lo, hi = int(pair[0]), int(pair[1])
                spin_lo.setValue(max(spin_lo.minimum(), min(spin_lo.maximum(), lo)))
                spin_hi.setValue(max(spin_hi.minimum(), min(spin_hi.maximum(), hi)))
            _set_pair_spin(self.a_sig_min, self.a_sig_max, sfs.get("A_sig", [2, 3]))
            _set_pair_spin(self.a_exp_min, self.a_exp_max, sfs.get("A_exp", [-2, 3]))
            _set_pair_spin(self.b_sig_min, self.b_sig_max, sfs.get("B_sig", [2, 3]))
            _set_pair_spin(self.b_exp_min, self.b_exp_max, sfs.get("B_exp", [-2, 3]))

            # Max solution sig figs (caps for generator only)
            self.max_sig_mul_spin.setValue(int(maxsol.get("*", 4)))
            self.max_sig_div_spin.setValue(int(maxsol.get("/", 4)))
            self.max_sig_add_spin.setValue(int(maxsol.get("+", 5)))
            self.max_sig_sub_spin.setValue(int(maxsol.get("-", 5)))

            # Time
            self.game_time_spinbox.setValue(max(self.game_time_spinbox.minimum(),
                                                min(self.game_time_spinbox.maximum(), game_time)))

            # Mode radios
            if mode == "range":
                self.range_mode_radio.setChecked(True); self.sigfigs_mode_radio.setChecked(False)
            else:
                self.sigfigs_mode_radio.setChecked(True); self.range_mode_radio.setChecked(False)
            self._on_mode_toggle(True)

            # Toggles
            self.toggle_flash_incorrect.setChecked(bool(toggles.get("flash_incorrect", True)))
            self.toggle_show_correct.setChecked(bool(toggles.get("show_correct", True)))
            self._on_show_correct_toggled(self.toggle_show_correct.isChecked())
            self.toggle_show_problem_text.setChecked(bool(toggles.get("show_problem_text", False)) and self.toggle_show_correct.isChecked())

            return True
        except Exception:
            return False

    def _on_save_clicked(self):
        self._save_preferences_safely()
        old = self.save_prefs_button.text()
        self.save_prefs_button.setText("Saved!")
        QTimer.singleShot(1200, lambda: self.save_prefs_button.setText(old))

    def _save_preferences_safely(self):
        try:
            prefs = self._collect_preferences()
            pth = _prefs_path()
            with pth.open("w", encoding="utf-8") as f:
                json.dump(prefs, f, indent=2)
        except Exception:
            pass

    def _load_preferences_if_any(self):
        pth = _prefs_path()
        if not pth.exists():
            return
        try:
            with pth.open("r", encoding="utf-8") as f:
                prefs = json.load(f)
            if not isinstance(prefs, dict):
                return
            self._apply_preferences(prefs)
        except Exception:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    trainer = ArithmeticTrainer()
    trainer.show()
    sys.exit(app.exec_())
