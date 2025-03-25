# serial_chart_matplot.py

import sys
import serial
import serial.tools.list_ports
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QLineEdit, QTextEdit, QCheckBox
)
from PySide6.QtCore import QTimer, Slot
from datetime import datetime
from PySide6.QtGui import QTextCursor

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class SerialChartApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Chart with Matplotlib")
        self.resize(1000, 600)

        self.serial = None
        self.data_x = []
        self.data_y = []
        self.counter = 0

        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Top: Serial Text and Chart
        top_layout = QHBoxLayout()

        # Serial Text Area
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        top_layout.addWidget(self.console)

        # Matplotlib Chart
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.line, = self.ax.plot([], [], 'g-')
        self.ax.set_title("Live Chart")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Value")
        top_layout.addWidget(self.canvas)

        layout.addLayout(top_layout)

        # Serial Controls
        ctrl_layout = QHBoxLayout()
        self.port_box = QComboBox()
        self.baud_box = QComboBox()
        self.baud_box.addItems(["9600", "115200", "2000000"])
        self.connect_btn = QPushButton("Connect")

        self.timestamp_checkbox = QCheckBox("Rcv Time")
        self.timestamp_checkbox.setChecked(True)
        self.autoscroll_checkbox = QCheckBox("Auto Scroll")
        self.autoscroll_checkbox.setChecked(True)

        ctrl_layout.addWidget(QLabel("Port:"))
        ctrl_layout.addWidget(self.port_box)
        ctrl_layout.addWidget(QLabel("Text:"))
        self.text_input = QLineEdit()
        self.text_input.setMaximumWidth(100)
        self.text_input.setText("")
        ctrl_layout.addWidget(self.text_input)
        ctrl_layout.addWidget(QLabel("Baud:"))
        ctrl_layout.addWidget(self.baud_box)
        ctrl_layout.addWidget(self.timestamp_checkbox)
        ctrl_layout.addWidget(self.autoscroll_checkbox)
        ctrl_layout.addWidget(self.connect_btn)

        layout.addLayout(ctrl_layout)

        # Command Line
        cmd_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.send_btn = QPushButton("Send")
        self.stop_btn = QPushButton("Stop")
        self.clear_btn = QPushButton("Clear")
        self.save_btn = QPushButton("Save")

        # input_line에서 엔터키 입력 시 send_command 실행
        self.input_line.returnPressed.connect(self.send_command)

        cmd_layout.addWidget(self.input_line)
        cmd_layout.addWidget(self.send_btn)
        cmd_layout.addWidget(self.stop_btn)
        cmd_layout.addWidget(self.clear_btn)
        cmd_layout.addWidget(self.save_btn)
        layout.addLayout(cmd_layout)

        self.connect_btn.clicked.connect(self.toggle_connection)
        self.send_btn.clicked.connect(self.send_command)
        self.stop_btn.clicked.connect(self.stop_chart)
        self.clear_btn.clicked.connect(self.clear_chart)
        self.save_btn.clicked.connect(self.save_data)

        self.refresh_ports()

    def refresh_ports(self):
        self.port_box.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_box.addItem(port.device)

    @Slot()
    def toggle_connection(self):
        if self.serial and self.serial.is_open:
            self.timer.stop()
            self.serial.close()
            self.connect_btn.setText("Connect")
            self.console.append("Disconnected.")
        else:
            try:
                port = self.port_box.currentText()
                baud = int(self.baud_box.currentText())
                self.serial = serial.Serial(port, baudrate=baud, timeout=0.1)
                self.timer.start(50)  # 20Hz
                self.connect_btn.setText("Disconnect")
                self.console.append(f"Connected to {port}")
            except Exception as e:
                self.console.append(f"Error: {e}")

    def read_serial(self):
        if not self.timer.isActive():  # 타이머가 멈춰있으면 데이터를 읽지 않음
            return
            
        if self.serial and self.serial.in_waiting:
            try:
                line = self.serial.readline().decode(errors='ignore').strip()

                # timestamp prefix
                if self.timestamp_checkbox.isChecked():
                    now = datetime.now().strftime("[%H:%M:%S.%f]")[:-3]
                    line = f"{now} {line}"

                self.console.append(line)

                if self.autoscroll_checkbox.isChecked():
                    self.console.moveCursor(QTextCursor.MoveOperation.End)

                # text_input이 비어있지 않을 때만 파싱 진행
                input_text = self.text_input.text().strip()
                if input_text:
                    prefix = f"[{input_text}"
                    if line.find(f"{input_text}:") != -1:
                        start = line.find(f"{input_text}:")
                        try:
                            value_str = line[start:].split(",")[0]
                            value = int(value_str.split(":")[1].strip())

                            self.counter += 1
                            self.data_x.append(self.counter)
                            self.data_y.append(value)

                            self.data_x = self.data_x[-100:]
                            self.data_y = self.data_y[-100:]

                            self.update_chart()
                        except Exception as parse_error:
                            self.console.append(f"Parse Error: {parse_error}")

            except Exception as e:
                self.console.append(f"Read Error: {e}")

    def update_chart(self):
        self.line.set_data(self.data_x, self.data_y)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def send_command(self):
        if self.serial and self.serial.is_open:
            command = self.input_line.text()
            self.serial.write((command + '\n').encode())
            self.console.append(f"> {command}")
            self.input_line.clear()

    def stop_chart(self):
        if self.timer.isActive():
            self.timer.stop()
            self.stop_btn.setText("Start")
            self.console.append("Chart stopped.")
            if self.serial and self.serial.is_open:
                self.serial.reset_input_buffer()  # 입력 버퍼 비우기
        else:
            if self.serial and self.serial.is_open:
                self.serial.reset_input_buffer()  # 시작 전 버퍼 비우기
            self.timer.start(50)  # 20Hz
            self.stop_btn.setText("Stop")
            self.console.append("Chart started.")

    def clear_chart(self):
        # 차트 데이터 초기화
        self.data_x.clear()
        self.data_y.clear()
        self.ax.cla()
        self.ax.set_title("Live Chart")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Value")
        self.line, = self.ax.plot([], [], 'g-')
        self.canvas.draw()
        
        # 콘솔 초기화
        self.console.clear()
        self.console.append("Chart and console cleared.")

    def save_data(self):
        # 현재 시간을 파일명에 포함
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 차트 데이터 저장
        chart_filename = f"chart_data_{timestamp}.csv"
        with open(chart_filename, "w") as f:
            f.write("Index,Value\n")  # CSV 헤더 추가
            for x, y in zip(self.data_x, self.data_y):
                f.write(f"{x},{y}\n")
        
        # 콘솔 데이터 저장
        console_filename = f"console_data_{timestamp}.csv"
        with open(console_filename, "w", encoding='utf-8') as f:
            f.write(self.console.toPlainText())
            
        self.console.append(f"Chart data saved to {chart_filename}")
        self.console.append(f"Console data saved to {console_filename}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialChartApp()
    window.show()
    sys.exit(app.exec())
