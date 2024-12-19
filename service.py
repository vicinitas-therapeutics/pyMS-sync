import win32serviceutil
import win32service
import win32event
import servicemanager
import os
import sys
import subprocess

class FileWatcherService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FileWatcherService"
    _svc_display_name_ = "File Watcher Service"
    _svc_description_ = "Service to run the File Watcher GUI application."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.main()

    def main(self):
        # Path to your Python script
        script_path = os.path.join(os.path.dirname(__file__), "pyms_sync", "gui.py")
        subprocess.call([sys.executable, script_path, "--config=config/config.json"])

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(FileWatcherService)