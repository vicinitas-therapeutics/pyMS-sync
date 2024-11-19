from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QLabel,
    QHBoxLayout,
)
from PyQt6.QtGui import QTextCursor
import threading
import json
from file_watcher import FileWatcher
from dotenv import load_dotenv
import os


class FileWatcherGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Watcher System")
        self.config = {}

        # Load environment variables
        load_dotenv()
        config_file_path = os.getenv(
            "CONFIG_FILE_PATH", os.path.join("config", "config.json")
        )
        with open(config_file_path) as config_file:
            self.config = json.load(config_file)

        default_watch_directory = self.config["watch_directory"]
        default_nas_directory = self.config["nas_directory"]

        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)

        self.watch_dir_label = QLabel("Watch Directory:", self)
        self.watch_dir_input = QLineEdit(self)
        self.watch_dir_input.setText(default_watch_directory)

        self.nas_dir_label = QLabel("NAS Directory:", self)
        self.nas_dir_input = QLineEdit(self)
        self.nas_dir_input.setText(default_nas_directory)

        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_watcher)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.stop_watcher)

        self.exit_button = QPushButton("Exit", self)
        self.exit_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.watch_dir_label)
        dir_layout.addWidget(self.watch_dir_input)
        dir_layout.addWidget(self.nas_dir_label)
        dir_layout.addWidget(self.nas_dir_input)

        layout.addLayout(dir_layout)
        layout.addWidget(self.text_area)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.exit_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.watcher_thread = None
        self.file_watcher = None

    def start_watcher(self):
        if self.watcher_thread is None or not self.watcher_thread.is_alive():
            self.watcher_thread = threading.Thread(
                target=self.run_file_watcher, daemon=True
            )
            self.watcher_thread.start()
            self.print_to_gui("File watcher started.")

    def stop_watcher(self):
        if self.file_watcher is not None:
            self.file_watcher.stop_watchman()
            self.print_to_gui("File watcher stopped.")

    def run_file_watcher(self):
        # read from the config file and pass the database details to the FileWatcher
        database_details = {
            "db_host": self.config["db_host"],
            "db_port": self.config["db_port"],
            "db_name": self.config["db_name"],
            "db_user": self.config["db_user"],
            "db_password": self.config["db_password"],
        }

        watch_directory = self.watch_dir_input.text()
        nas_directory = self.nas_dir_input.text()
        watch_file_ext = ".d"
        self.file_watcher = FileWatcher(
            watch_directory, nas_directory, watch_file_ext, database_details
        )
        self.file_watcher.set_output_element(self.print_to_gui)
        self.file_watcher.start_watchman()

    def print_to_gui(self, message):
        self.text_area.append(message)
        self.text_area.moveCursor(QTextCursor.MoveOperation.End)
        # self.text_area.append(message)


def main():
    app = QApplication([])
    window = FileWatcherGUI()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
