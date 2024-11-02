from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileClosedNoWriteEvent, FileOpenedEvent
import datetime
import threading
import time
import os
import file_mover as fm

class FileWatcher(FileSystemEventHandler):
    def __init__(self, watch_directory, nas_directory, watch_file_ext):
        self.watch_directory = watch_directory
        self.nas_directory = nas_directory
        self.observer = Observer()
        self.watch_created = 0
        self.watch_modified = 0
        self.finished_src = {}
        self.finished_move = {}
        self.watch_file_ext = watch_file_ext

    def start_watchman(self):
        self.observer.schedule(self, self.watch_directory, recursive=True)
        self.observer.start()
        print("Watchdog started.")

    def on_created(self, event):
        self.handle_event(event.src_path, event.event_type)
        # skip unless the files is one
        # try:
        # threading.Thread(target=self.handle_event,
        #                  args=(event.src_path, event.event_type ),
        #                  daemon=True).start()
        # except Exception as e:
        #     print(f"Exception caught: {e}")
        #     self.cleanup_needed = True
        # finally:
        #     if self.cleanup_needed:
        #         self.cleanup()


    def on_modified(self, event):
        print("m ", end="")
        # threading.Thread(target=self.handle_event,
        #                  args=(event.src_path, event.event_type ),
        #                  daemon=True).start()

    def handle_event(self, src_path, event: str = None):
        pid = os.getpid()
        print(f"Event: {event} - {src_path} -- {pid} -- ")

        # Check if the file is a directory
        if os.path.isdir(src_path):
            os.makedirs(os.path.join(self.nas_directory, os.path.relpath(src_path, self.watch_directory)), exist_ok=True)
            # print(f"Directory detected - {os.path.isdir(src_path)}. Skipping...")
            print("d", end="")
            return
        dest_path = os.path.join(self.nas_directory, os.path.relpath(src_path, self.watch_directory))
        fmove = fm.FileMover(src_path, dest_path)
        # add to the dict the current file we're waching, finshed or not, and the time
        now = datetime.datetime.now()
        self.finished_src[src_path]= [ False,  now, None]
        self.finished_src[src_path][0] = fmove.check_finished(location="src")
        # print(self.finished_src, " ")
        while not self.finished_src[src_path][0]:
            time.sleep(10)
            print("+ ", end="")
            ## todo add in a simple check if we go over 2hr mark, then stop the loop
            self.finished_src[src_path][0] = fmove.check_finished(location="src")
            print(f"Checking if file is finished at src: {self.finished_src[src_path][0]}")
            if self.finished_src[src_path][0]:
                print(f"File finished at src: {self.finished_src[src_path][1]}")
                success_move = fmove.move_file()
                if success_move:
                    break

    def stop_watchman(self):
        self.observer.stop()
        self.observer.join()
        print("Watchdog stopped.")

    def cleanup(self):
        # Your cleanup logic here
        print(f"Cleaning up dead threads {datetime.datetime.now()}")
