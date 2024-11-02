import json
import os
import time
from dotenv import load_dotenv

import file_mover as fm
import file_watcher as fw

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Main function to run the file watcher and mover
    :return:
    """
    config_file_path = os.getenv("CONFIG_FILE_PATH")
    with open(config_file_path) as config_file:
        config = json.load(config_file)

    watch_directory = config['watch_directory']
    nas_directory = config['nas_directory']
    watcher = fw.FileWatcher(watch_directory, nas_directory,
                             config['watch_file_ext'])

    watcher.start_watchman()

    try:
        while True:
            time.sleep(10)
            print(". ", end="")
    except KeyboardInterrupt:
        watcher.stop_watchman()


        # time.sleep(10)

if __name__ == "__main__":
    main()
