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
import os
import logging
import argparse

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FileWatcherGUI(QMainWindow):
    def __init__(self, config_file_path=None):
        super().__init__()
        self.setWindowTitle("File Watcher System")
        self.config = {}

        # Load environment variables
        if not os.path.exists(config_file_path) or config_file_path is None:
            config_file_path = "config.json"
            logging.warning("Using local config file: config.json")
        try:
            with open(config_file_path) as config_file:
                self.config = json.load(config_file)
                logging.debug(f"Loaded config file: {config_file_path}")
        except FileNotFoundError:
            logging.error(f"Config file not found: {config_file_path}")
            raise FileNotFoundError(f"Config file not found: {config_file_path}")

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
        logging.debug("Starting file watcher.")
        if self.watcher_thread is None or not self.watcher_thread.is_alive():
            self.watcher_thread = threading.Thread(
                target=self.run_file_watcher, daemon=True
            )
            self.watcher_thread.start()
            self.print_to_gui("File watcher started.")
            logging.debug("File watcher started.")

    def stop_watcher(self):
        logging.debug("Stopping file watcher.")
        if self.file_watcher is not None:
            self.file_watcher.stop_watchman()
            self.print_to_gui("File watcher stopped.")
            logging.debug("File watcher stopped.")

    def run_file_watcher(self):
        logging.debug("Running file watcher.")
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
        logging.debug(f"Watch Directory: {watch_directory}")
        logging.debug(f"NAS Directory: {nas_directory}")
        self.file_watcher = FileWatcher(
            watch_directory, nas_directory, watch_file_ext, database_details
        )
        self.file_watcher.set_output_element(self.print_to_gui)
        self.file_watcher.start_watchman()

    def print_to_gui(self, message):
        self.text_area.append(message)
        self.text_area.moveCursor(QTextCursor.MoveOperation.End)
        logging.debug(message)
        # self.text_area.append(message)


def main():
    parser = argparse.ArgumentParser(description="File Watcher GUI")
    parser.add_argument(
        "--config", type=str, default="config.json", help="Path to the config file"
    )
    args = parser.parse_args()

    app = QApplication([])
    window = FileWatcherGUI(args.config)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
