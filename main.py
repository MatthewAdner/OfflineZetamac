import sys
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFormLayout, QSpinBox, QCheckBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor

class ArithmeticTrainer(QWidget):
    def __init__(self):
        super().__init__()

        self.score = 0
        self.time_left = 120  # Default 120 seconds timer
        
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Arithmetic Trainer")
        self.setGeometry(100, 100, 400, 600)

        self.layout = QVBoxLayout()

        self.info_label = QLabel("Solve as many problems as you can!", self)
        self.info_label.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.info_label)

        self.problem_label = QLabel("", self)
        self.problem_label.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(self.problem_label)

        self.answer_entry = QLineEdit(self)
        self.answer_entry.setStyleSheet("font-size: 24px;")
        self.answer_entry.returnPressed.connect(self.check_answer)
        self.layout.addWidget(self.answer_entry)

        self.result_label = QLabel("", self)
        self.result_label.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.result_label)

        self.score_label = QLabel(f"Score: {self.score}", self)
        self.score_label.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.score_label)

        self.timer_label = QLabel(f"Time left: {self.time_left} s", self)
        self.timer_label.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.timer_label)

        self.start_button = QPushButton("Start", self)
        self.start_button.setStyleSheet("font-size: 18px;")
        self.start_button.clicked.connect(self.start_game)
        self.layout.addWidget(self.start_button)

        # Number range settings with checkboxes
        self.form_layout = QFormLayout()

        self.addition_checkbox = QCheckBox("Addition")
        self.addition_checkbox.setChecked(True)
        self.form_layout.addRow(self.addition_checkbox)

        self.addition_range_layout = QHBoxLayout()
        self.addition_range1_spinbox1 = QSpinBox(self)
        self.addition_range1_spinbox1.setRange(1, 100)
        self.addition_range1_spinbox1.setValue(2)
        self.addition_range_layout.addWidget(self.addition_range1_spinbox1)

        self.addition_range1_spinbox2 = QSpinBox(self)
        self.addition_range1_spinbox2.setRange(1, 100)
        self.addition_range1_spinbox2.setValue(100)
        self.addition_range_layout.addWidget(self.addition_range1_spinbox2)

        self.addition_plus_label = QLabel("+")
        self.addition_range_layout.addWidget(self.addition_plus_label)

        self.addition_range2_spinbox1 = QSpinBox(self)
        self.addition_range2_spinbox1.setRange(1, 100)
        self.addition_range2_spinbox1.setValue(2)
        self.addition_range_layout.addWidget(self.addition_range2_spinbox1)

        self.addition_range2_spinbox2 = QSpinBox(self)
        self.addition_range2_spinbox2.setRange(1, 100)
        self.addition_range2_spinbox2.setValue(100)
        self.addition_range_layout.addWidget(self.addition_range2_spinbox2)

        self.form_layout.addRow(self.addition_range_layout)

        self.subtraction_checkbox = QCheckBox("Subtraction")
        self.subtraction_checkbox.setChecked(True)
        self.form_layout.addRow(self.subtraction_checkbox)

        self.multiplication_checkbox = QCheckBox("Multiplication")
        self.multiplication_checkbox.setChecked(True)
        self.form_layout.addRow(self.multiplication_checkbox)

        self.multiplication_range_layout = QHBoxLayout()
        self.multiplication_range1_spinbox1 = QSpinBox(self)
        self.multiplication_range1_spinbox1.setRange(1, 100)
        self.multiplication_range1_spinbox1.setValue(2)
        self.multiplication_range_layout.addWidget(self.multiplication_range1_spinbox1)

        self.multiplication_range1_spinbox2 = QSpinBox(self)
        self.multiplication_range1_spinbox2.setRange(1, 100)
        self.multiplication_range1_spinbox2.setValue(12)
        self.multiplication_range_layout.addWidget(self.multiplication_range1_spinbox2)

        self.multiplication_label = QLabel("×")
        self.multiplication_range_layout.addWidget(self.multiplication_label)

        self.multiplication_range2_spinbox1 = QSpinBox(self)
        self.multiplication_range2_spinbox1.setRange(1, 100)
        self.multiplication_range2_spinbox1.setValue(2)
        self.multiplication_range_layout.addWidget(self.multiplication_range2_spinbox1)

        self.multiplication_range2_spinbox2 = QSpinBox(self)
        self.multiplication_range2_spinbox2.setRange(1, 100)
        self.multiplication_range2_spinbox2.setValue(100)
        self.multiplication_range_layout.addWidget(self.multiplication_range2_spinbox2)

        self.form_layout.addRow(self.multiplication_range_layout)

        self.division_checkbox = QCheckBox("Division")
        self.division_checkbox.setChecked(True)
        self.form_layout.addRow(self.division_checkbox)

        self.game_time_label = QLabel("Game Time (seconds):")
        self.form_layout.addRow(self.game_time_label)

        self.game_time_spinbox = QSpinBox(self)
        self.game_time_spinbox.setRange(30, 600)
        self.game_time_spinbox.setValue(120)
        self.form_layout.addRow(self.game_time_spinbox)

        self.layout.addLayout(self.form_layout)

        self.setLayout(self.layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.show_settings_screen()

    def show_settings_screen(self):
        self.info_label.show()
        self.start_button.show()
        self.problem_label.hide()
        self.answer_entry.hide()
        self.result_label.hide()
        self.score_label.hide()
        self.timer_label.hide()

        self.addition_checkbox.show()
        self.subtraction_checkbox.show()
        self.multiplication_checkbox.show()
        self.division_checkbox.show()

        self.addition_range1_spinbox1.show()
        self.addition_range1_spinbox2.show()
        self.addition_plus_label.show()
        self.addition_range2_spinbox1.show()
        self.addition_range2_spinbox2.show()
        self.multiplication_range1_spinbox1.show()
        self.multiplication_range1_spinbox2.show()
        self.multiplication_label.show()
        self.multiplication_range2_spinbox1.show()
        self.multiplication_range2_spinbox2.show()
        self.game_time_label.show()
        self.game_time_spinbox.show()

    def show_game_screen(self):
        self.info_label.hide()
        self.start_button.hide()
        self.problem_label.show()
        self.answer_entry.show()
        self.result_label.hide()
        self.score_label.show()
        self.timer_label.show()

        self.addition_checkbox.hide()
        self.subtraction_checkbox.hide()
        self.multiplication_checkbox.hide()
        self.division_checkbox.hide()

        self.addition_range1_spinbox1.hide()
        self.addition_range1_spinbox2.hide()
        self.addition_plus_label.hide()
        self.addition_range2_spinbox1.hide()
        self.addition_range2_spinbox2.hide()
        self.multiplication_range1_spinbox1.hide()
        self.multiplication_range1_spinbox2.hide()
        self.multiplication_label.hide()
        self.multiplication_range2_spinbox1.hide()
        self.multiplication_range2_spinbox2.hide()
        self.game_time_label.hide()
        self.game_time_spinbox.hide()

    def show_end_screen(self):
        self.problem_label.hide()
        self.answer_entry.hide()
        self.result_label.show()
        self.result_label.setText(f"Time's up! Your final score is {self.score}.")
        self.back_button = QPushButton("Back to Start", self)
        self.back_button.setStyleSheet("font-size: 18px;")
        self.back_button.clicked.connect(self.reset_to_start)
        self.layout.addWidget(self.back_button)

    def reset_to_start(self):
        self.back_button.hide()
        self.show_settings_screen()

    def generate_problem(self):
        selected_operations = []
        if self.addition_checkbox.isChecked():
            selected_operations.append('+')
        if self.subtraction_checkbox.isChecked():
            selected_operations.append('-')
        if self.multiplication_checkbox.isChecked():
            selected_operations.append('*')
        if self.division_checkbox.isChecked():
            selected_operations.append('/')

        if not selected_operations:
            self.problem_label.setText("Select at least one operation.")
            return

        self.operator = random.choice(selected_operations)

        if self.operator == '+':
            self.num1 = random.randint(self.addition_range1_spinbox1.value(), self.addition_range1_spinbox2.value())
            self.num2 = random.randint(self.addition_range2_spinbox1.value(), self.addition_range2_spinbox2.value())
        elif self.operator == '-':
            self.num1 = random.randint(self.addition_range1_spinbox1.value(), self.addition_range1_spinbox2.value())
            self.num2 = random.randint(self.addition_range2_spinbox1.value(), self.addition_range2_spinbox2.value())
            if self.num1 < self.num2:
                self.num1, self.num2 = self.num2, self.num1
        elif self.operator == '*':
            self.num1 = random.randint(self.multiplication_range1_spinbox1.value(), self.multiplication_range1_spinbox2.value())
            self.num2 = random.randint(self.multiplication_range2_spinbox1.value(), self.multiplication_range2_spinbox2.value())
        elif self.operator == '/':
            self.num1 = random.randint(self.multiplication_range1_spinbox1.value(), self.multiplication_range1_spinbox2.value())
            self.num2 = random.randint(self.multiplication_range2_spinbox1.value(), self.multiplication_range2_spinbox2.value())
            self.num1 = self.num1 * self.num2  # Ensure division problems have integer results

        self.problem_label.setText(f"{self.num1} {self.operator} {self.num2}")

    def start_game(self):
        self.score = 0
        self.time_left = self.game_time_spinbox.value()
        self.score_label.setText(f"Score: {self.score}")
        self.timer_label.setText(f"Time left: {self.time_left} s")
        self.result_label.setText("")
        self.start_button.setEnabled(False)
        self.form_layout.setEnabled(False)
        self.generate_problem()
        self.show_game_screen()
        self.timer.start(1000)
        
    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.setText(f"Time left: {self.time_left} s")
        else:
            self.end_game()
            
    def check_answer(self):
        try:
            user_answer = float(self.answer_entry.text())
            correct_answer = eval(f"{self.num1} {self.operator} {self.num2}")
            if abs(user_answer - correct_answer) < 0.001:  # Account for float precision
                self.score += 1
                self.result_label.setText("Correct!")
                self.flash_screen('green')
            else:
                self.result_label.setText(f"Incorrect! The answer was {correct_answer}")
                self.flash_screen('red')
            self.score_label.setText(f"Score: {self.score}")
            self.answer_entry.clear()
            self.generate_problem()
        except ValueError:
            self.result_label.setText("Please enter a valid number!")
            self.flash_screen('red')
    
    def flash_screen(self, color):
        original_color = self.palette().color(self.backgroundRole())
        flash_color = QColor('green') if color == 'green' else QColor('red')

        self.setStyleSheet(f"background-color: {flash_color.name()};")
        QTimer.singleShot(100, lambda: self.setStyleSheet(f"background-color: {original_color.name()};"))

    def end_game(self):
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.form_layout.setEnabled(True)
        self.show_end_screen()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    trainer = ArithmeticTrainer()
    trainer.show()
    sys.exit(app.exec_())
