# main.py

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
import mplcursors
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar


class SerialChartApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Chart with Matplotlib - OIS(oinse719@gmail.com)")
        self.resize(1000, 600)

        self.serial = None
        self.data_x = []
        self.lines = []  # 빈 리스트로 시작
        self.data_y = []  # 빈 리스트로 시작
        self.cursors = []  # 커서도 빈 리스트로 시작
        self.counter = 0
        self.colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 
                      'pink', 'gray', 'olive', 'cyan']  # 10개 색상 준비

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

        # Matplotlib Chart와 Toolbar를 포함할 컨테이너
        chart_container = QVBoxLayout()
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # 네비게이션 툴바 추가
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Stop, Clear, Save 버튼 생성 및 스타일 설정
        self.stop_btn = QPushButton("Stop")
        self.clear_btn = QPushButton("Clear")
        self.save_btn = QPushButton("Save")
        
        # 툴바에 버튼 추가
        self.toolbar.addWidget(self.stop_btn)
        self.toolbar.addWidget(self.clear_btn)
        self.toolbar.addWidget(self.save_btn)
        
        chart_container.addWidget(self.canvas)
        chart_container.addWidget(self.toolbar)
        top_layout.addLayout(chart_container)

        layout.addLayout(top_layout)

        # Serial Controls
        ctrl_layout = QHBoxLayout()
        self.port_box = QComboBox()
        self.baud_box = QComboBox()
        self.baud_box.addItems([
            "4800",
            "9600",
            "19200",
            "38400", 
            "57600",
            "115200",
            "230400",
            "460800",
            "921600",
            "2000000"
        ])
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

        # input_line에서 엔터키 입력 시 send_command 실행
        self.input_line.returnPressed.connect(self.send_command)

        cmd_layout.addWidget(self.input_line)
        cmd_layout.addWidget(self.send_btn)
        layout.addLayout(cmd_layout)

        self.connect_btn.clicked.connect(self.toggle_connection)
        self.send_btn.clicked.connect(self.send_command)
        self.stop_btn.clicked.connect(self.stop_chart)
        self.clear_btn.clicked.connect(self.clear_chart)
        self.save_btn.clicked.connect(self.save_data)

        self.refresh_ports()

        # 각 선에 대해 커서 추가
        self.cursors = []
        for line in self.lines:
            cursor = mplcursors.cursor(
                line, 
                hover=True,
                annotation_kwargs=dict(bbox=dict(fc="white", alpha=0.8))
            )
            cursor.connect("add", self.on_cursor_add)
            self.cursors.append(cursor)

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
        if not self.timer.isActive():
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

                input_text = self.text_input.text().strip()
                if input_text:
                    if line.find(f"#{input_text}:") != -1:  # '#' 기호 추가
                        try:
                            # '#TEST:' 형식의 데이터 파싱
                            start = line.find(f"#{input_text}:")
                            value_str = line[start:].split("/")[0]  # delay 부분 제거
                            values = value_str.split(":")[1].strip()  # #TEST: 부분 제거
                            number_list = [int(num.strip()) for num in values.split(",")]
                            
                            # 최대 10개까지만 처리
                            number_list = number_list[:10]
                            
                            # 데이터 개수에 따라 lines와 data_y 조정
                            while len(self.lines) < len(number_list):
                                i = len(self.lines)
                                color = self.colors[i]
                                line, = self.ax.plot([], [], color, label=str(i+1), visible=False)
                                self.lines.append(line)
                                self.data_y.append([])
                                cursor = mplcursors.cursor(
                                    line, 
                                    hover=True,
                                    annotation_kwargs=dict(bbox=dict(fc="white", alpha=0.8))
                                )
                                cursor.connect("add", self.on_cursor_add)
                                self.cursors.append(cursor)

                            # x 축 데이터 추가
                            self.counter += 1
                            self.data_x.append(self.counter)
                            
                            # 각 데이터 시리즈 업데이트
                            for i in range(len(number_list)):
                                self.data_y[i].append(number_list[i])
                            
                            # 최근 100개 데이터만 유지
                            if len(self.data_x) > 100:
                                self.data_x = self.data_x[-100:]
                                for i in range(len(self.data_y)):
                                    self.data_y[i] = self.data_y[i][-100:]

                            self.update_chart()
                        except Exception as parse_error:
                            self.console.append(f"Parse Error: {parse_error}")

            except Exception as e:
                self.console.append(f"Read Error: {e}")

    def update_chart(self):
        # 각 선 업데이트 및 가시성 설정
        for i, line in enumerate(self.lines):
            data = self.data_y[i]
            if data and any(x is not None for x in data):  # 데이터가 있는 경우만
                line.set_data(self.data_x, self.data_y[i])
                line.set_visible(True)
            else:
                line.set_visible(False)
        
        # 보이는 선만 범례에 표시
        handles = [line for line in self.lines if line.get_visible()]
        labels = [f"{i+1}" for i, line in enumerate(self.lines) if line.get_visible()]
        
        # 범례 설정 변경
        self.ax.legend(handles, labels, 
                      loc='upper center',
                      bbox_to_anchor=(0.5, -0.05),  # 그래프 아래에 위치
                      ncol=10,  # 10개를 한 줄에 표시
                      frameon=False,  # 테두리 제거
                      prop={'size': 8},  # 폰트 크기 축소
                      borderaxespad=0)  # 그래프와의 간격 조정
        
        # 그래프 여백 조정
        self.figure.tight_layout()  # 자동으로 여백 조정
        
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
        self.data_x.clear()
        self.data_y.clear()
        self.lines.clear()
        self.cursors.clear()
        self.ax.cla()
        
        self.ax.set_title("Live Chart")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Value")
        
        # clear_chart에도 동일한 범례 설정 적용
        self.ax.legend(loc='upper center',
                      bbox_to_anchor=(0.5, -0.05),
                      ncol=10,
                      frameon=False,
                      prop={'size': 8},
                      borderaxespad=0)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        self.console.clear()
        self.console.append("Chart and console cleared.")

    def save_data(self):
        # 현재 시간을 파일명에 포함
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 차트 데이터 저장
        chart_filename = f"chart_data_{timestamp}.csv"
        with open(chart_filename, "w") as f:
            f.write("Index,Value\n")  # CSV 헤더 추가
            for x, y in zip(self.data_x, self.data_y[0]):
                f.write(f"{x},{y}\n")
        
        # 콘솔 데이터 저장
        console_filename = f"console_data_{timestamp}.csv"
        with open(console_filename, "w", encoding='utf-8') as f:
            f.write(self.console.toPlainText())
            
        self.console.append(f"Chart data saved to {chart_filename}")
        self.console.append(f"Console data saved to {console_filename}")

    def on_cursor_add(self, sel):
        x_val = int(sel.target[0])
        y_val = int(sel.target[1])
        label = sel.artist.get_label()
        sel.annotation.set_text(f"{label}\nX: {x_val}\nY: {y_val}")
        sel.annotation.set_visible(True)
        self.canvas.draw_idle()

        def remove_annotation(event):
            if sel.annotation:
                sel.annotation.set_visible(False)
                self.canvas.draw_idle()

        sel.annotation.figure.canvas.mpl_connect('motion_notify_event', remove_annotation)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialChartApp()
    window.show()
    sys.exit(app.exec())
