import datetime
import datetime as dt
import os
import threading
import time

# from dotenv import load_dotenv
import mysql.connector
from watchdog.events import (
    FileSystemEventHandler,
)
from watchdog.observers import Observer

import file_mover as fm
from file_parser import parse_file_name


# load_dotenv()
# # Database connection details
# DB_HOST = os.getenv('DB_HOST')
# DB_PORT = os.getenv('DB_PORT')
# DB_NAME = os.getenv('DB_NAME')
# DB_USER = os.getenv('DB_USER')
# DB_PASSWORD = os.getenv('DB_PASSWORD')


class FileWatcher(FileSystemEventHandler):
    def __init__(
        self, watch_directory, nas_directory, watch_file_ext, database_details=None
    ):
        """
        Initialize the FileWatcher class
        :param watch_directory:
        :param nas_directory:
        :param watch_file_ext:
        """
        self.watch_directory = watch_directory
        self.nas_directory = nas_directory
        self.observer = Observer()
        self.watch_created = 0
        self.watch_modified = 0
        self.finished_src = {}
        self.finished_move = {}
        self.watch_file_ext = watch_file_ext
        self.cleanup_needed = False
        self.output_element = None
        self.database_details = database_details if database_details else None

    def set_output_element(self, output_element):
        self.output_element = output_element

    def print(self, message, event_type="", pid=0, src_path=""):
        """
        Print the message to the console or the GUI
        :param message:
        :param event_type:
        :param pid:
        :param src_path:
        :return:
        """
        message = (
            f"{dt.datetime.now()} Event:  {event_type} - {src_path} - {pid} - {message}"
        )
        if self.output_element:
            self.output_element(message)
        else:
            print(message)

    def start_watchman(self):
        self.observer.schedule(self, self.watch_directory, recursive=True)
        self.observer.start()
        self.print("Watchdog started.", event_type="Started", pid=os.getpid())

    def on_created(self, event):
        # self.handle_event(event.src_path, event.event_type)
        # skip unless the files is one
        try:
            threading.Thread(
                target=self.handle_event,
                args=(event.src_path, event.event_type),
                daemon=True,
            ).start()
        except Exception as e:
            self.print(f"Exception caught: {e}", event_type="Error", pid=os.getpid())
            self.cleanup_needed = True
        finally:
            if self.cleanup_needed:
                self.cleanup()

    def on_modified(self, event):
        print(".")
        time.sleep(20)
        # self.print(
        #     message="skipping...",
        #     event_type=event.event_type,
        #     pid=os.getpid(),
        #     src_path=event.src_path,
        # )
        # threading.Thread(target=self.handle_event,
        #                  args=(event.src_path, event.event_type ),
        #                  daemon=True).start()

    def handle_event(self, src_path, event: str = None):
        pid = os.getpid()
        self.print(message="waiting...", event_type=event, pid=pid, src_path=src_path)

        # Check if the file is a directory
        if os.path.isdir(src_path):
            os.makedirs(
                os.path.join(
                    self.nas_directory, os.path.relpath(src_path, self.watch_directory)
                ),
                exist_ok=True,
            )
            # print(f"Directory detected - {os.path.isdir(src_path)}. Skipping...")
            self.print(
                f"{dt.datetime.now()} - Event: Directory found - {src_path} - {pid} - skipping..."
            )
            return

        # Parse the file name
        file_name = os.path.basename(src_path)
        try:
            parsed_data = parse_file_name(file_name)
            parsed_data["file_name"] = file_name
            self.print(
                message="Parsed file name data: {parsed_data}",
                event_type="parsed file name ",
                pid=pid,
                src_path=src_path,
            )
        except ValueError as e:
            self.print(
                message=f"Error parsing file name: {e}",
                event_type="Error",
                pid=pid,
                src_path=src_path,
            )
            parsed_data = {
                "file_name": file_name,
                "ExperimentID": "",
                "Instrument": "",
                "Method": "",
                "Protein": "",
                "Condition": "",
                "Concentration": 0,
                "Time": 0,
                "BioReplicate": 0,
                "TechnicalRep": 0,
            }

        # Insert parsed data into the database
        self.insert_into_db(parsed_data)

        dest_path = os.path.join(
            self.nas_directory, os.path.relpath(src_path, self.watch_directory)
        )
        fmove = fm.FileMover(src_path, dest_path)
        # add to the dict the current file we're waching, finshed or not, and the time
        now = datetime.datetime.now()
        self.finished_src[src_path] = [False, now, None]
        self.finished_src[src_path][0] = fmove.check_finished(location="src")
        # print(self.finished_src, " ")

        while not self.finished_src[src_path][0]:
            time.sleep(10)
            self.print(
                "Waiting for the file to finish...",
                event_type="Waiting",
                pid=pid,
                src_path=src_path,
            )
            ## todo add in a simple check if we go over 2hr mark, then stop the loop
            self.finished_src[src_path][0] = fmove.check_finished(location="src")
            self.print(
                message="Checking if file is finished at src: {self.finished_src[src_path][0]}",
                event_type="Checking",
                pid=pid,
                src_path=src_path,
            )
            if self.finished_src[src_path][0]:
                self.print(
                    message=f"File finished at src: {self.finished_src[src_path][1]}",
                    event_type="Finished",
                    pid=pid,
                    src_path=src_path,
                )
                success_move = fmove.move_file()
                if success_move:
                    break

    def stop_watchman(self):
        self.print(
            message="Stopping the watchdog.", event_type="Stopping", pid=os.getpid()
        )
        self.observer.stop()
        self.observer.join()
        self.print(message="Watchdog stopped.", event_type="Stopped", pid=os.getpid())

    def cleanup(self):
        # Your cleanup logic here
        self.print(f"Cleaning up dead threads {datetime.datetime.now()}")

    def insert_into_db(self, parsed_data):
        connection = None
        try:
            connection = mysql.connector.connect(
                host=self.database_details["db_host"],
                port=self.database_details["db_port"],
                database=self.database_details["db_name"],
                user=self.database_details["db_user"],
                password=self.database_details["db_password"],
            )
            cursor = connection.cursor()
            self.print("Connected to database", event_type="Database connection", pid=0)

            insert_query = """
            INSERT INTO ms_files.files (file_name, experiment_id, instrument, method,
             protein, `condition`, concentration, time_point, bio_rep, tech_rep)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (
                    parsed_data["file_name"],
                    parsed_data["ExperimentID"],
                    parsed_data["Instrument"],
                    parsed_data["Method"],
                    parsed_data["Protein"],
                    parsed_data["Condition"],
                    parsed_data["Concentration"],
                    parsed_data["Time"],
                    parsed_data["BioReplicate"],
                    parsed_data["TechnicalRep"],
                ),
            )
            connection.commit()
            self.print(
                message="Data inserted into the database successfully",
                event_type="Database insert",
                pid=0,
            )

        except mysql.connector.Error as err:
            self.print(message=f"Error: {err}", event_type="Database error", pid=0)
        finally:
            if connection is not None:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
                    self.print(
                        message="Database connection closed",
                        event_type="Database connection",
                        pid=0,
                    )

    #


#
