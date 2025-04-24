import sys
import os 
import resources_rc
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import QThread, Signal
from db import SQLiteDB  
from pysilk import silk_bytes_to_mp3
from PySide6.QtGui import QIcon


class ExportVoiceThread(QThread):
    log_signal = Signal(str)  

    def __init__(self, src_wechat_id, export_path, db_path):
        super().__init__()
        self.src_wechat_id = src_wechat_id
        self.export_path = export_path
        self.db_path = db_path

    def run(self):
        self.log_signal.emit(f"开始导出微信号({self.src_wechat_id})的语音消息")
        msg_db = SQLiteDB(self.db_path, "MSG")
        query = 'SELECT count(*) FROM MSG WHERE StrTalker = ? AND Type = 34 AND IsSender = 0;'
        data_count = msg_db.select_count(query, (self.src_wechat_id,))
        if data_count == 0:
            self.log_signal.emit(f"没有找到微信号({self.src_wechat_id})的语音消息")
            return
        self.log_signal.emit(f"找到语音消息{data_count}条")
        query = 'SELECT MsgSvrID FROM MSG WHERE StrTalker = ? AND Type = 34 AND IsSender = 0;'
        voice_db = SQLiteDB(self.db_path, "MediaMSG")
        export_path = os.path.join(self.export_path, self.src_wechat_id)
        if not os.path.exists(export_path):
            os.makedirs(export_path)
        n = 0
        for row in msg_db.selcet_all(query, (self.src_wechat_id,)):
            msg_id = row["MsgSvrID"]
            query = 'SELECT Buf FROM Media WHERE Reserved0 = ?;'
            row = voice_db.select_one(query, (msg_id,))
            if not row:
                self.log_signal.emit(f"消息({msg_id})没有找到对应的语音内容!")
                continue
            silk_data = row["Buf"]
            mp3_path = os.path.join(export_path, f"{msg_id}.mp3")
            if os.path.exists(mp3_path):
                self.log_signal.emit(f"消息({msg_id})的语音文件已存在，跳过")
                continue
            silk_bytes_to_mp3(silk_data, mp3_path, 24000)
            self.log_signal.emit(f"导出语音成功: {msg_id}.mp3")
            n += 1
        self.log_signal.emit(f"导出完成，成功数量: {n}!")
        if n > 0:
            os.startfile(export_path)  # 使用文件资源管理器打开导出目录


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信语音导出")
        self.setWindowIcon(QIcon(":/main.ico"))  # 设置窗口图标
        self.resize(800, 600)
        self.setStyleSheet("""
            QWidget {
                font-size: 15px;
                background-color: #f5f5f5;
            }
            QLabel {
                font-weight: bold;
                color: #333;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: #fff;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: #fff;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        wechat_layout = QHBoxLayout()
        wechat_label = QLabel("微信号:")
        self.wechat_input = QLineEdit()
        self.wechat_input.setMaximumWidth(300)
        self.print_button = QPushButton("开始导出")
        self.print_button.clicked.connect(self.export_voice_callback)
        wechat_layout.addWidget(wechat_label)
        wechat_layout.addWidget(self.wechat_input)
        wechat_layout.addWidget(self.print_button)
        wechat_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(wechat_layout)

        db_layout = QHBoxLayout()
        db_label = QLabel("数据库路径:")
        self.db_input = QLineEdit()
        self.db_input.setPlaceholderText("请输入数据库路径")
        self.db_button = QPushButton("选择路径")
        self.db_button.clicked.connect(self.select_db_path)
        db_layout.addWidget(db_label)
        db_layout.addWidget(self.db_input)
        db_layout.addWidget(self.db_button)
        layout.addLayout(db_layout)

        path_layout = QHBoxLayout()
        path_label = QLabel("导出路径:")
        self.path_input = QLineEdit()
        self.path_input.setText(os.getcwd())  
        self.path_button = QPushButton("选择路径")
        self.path_button.clicked.connect(self.select_path)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.path_button)
        layout.addLayout(path_layout)

        self.log_output = QTextEdit()
        self.log_output.setPlaceholderText("初始化已完成...")
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def export_voice_callback(self):
        wechat_id = self.wechat_input.text()
        if not wechat_id:
            self.log_output.append("请输入微信号!")
            return
        db_path = self.db_input.text()
        if not db_path:
            self.log_output.append("请输入数据库路径!")
            return
        src_wechat_id = self.get_wechat_id(wechat_id, db_path)
        if not src_wechat_id:
            self.log_output.append(f"没有找到微信号({wechat_id})!")
            return
        export_path = self.path_input.text()
        if not os.path.exists(export_path):
            os.makedirs(export_path)

        # 创建并启动线程
        self.thread = ExportVoiceThread(src_wechat_id, export_path, db_path)
        self.thread.log_signal.connect(self.log_output.append)  # 连接日志信号到日志输出
        self.thread.start()

    def get_wechat_id(self, wechat_id, db_path):
        db_name = "MicroMsg"
        db = SQLiteDB(db_path, db_name)
        query = 'SELECT UserName,Alias,Remark,NickName FROM Contact WHERE UserName = ? OR Alias = ? '
        row = db.select_one(query, (wechat_id, wechat_id))
        if not row:
            return None
        return row["UserName"]

    def select_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择导出路径")
        if path:
            self.path_input.setText(path)

    def select_db_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择数据库路径")
        if path:
            self.db_input.setText(path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())