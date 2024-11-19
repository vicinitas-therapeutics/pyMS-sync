import hashlib
import os
import shutil
import logging


class FileMover:
    """
    Class to move a file or folder(!) from source to destination and
    check if the file is moved successfully
    """

    def __init__(self, src: str, dest: str, md5_check: str = True) -> None:
        """
        :param src: the source path
        :param dest: the destination path
        :param md5_check: bool - True if MD5 hash is to be checked, False otherwise (default: True)
        """
        logging.basicConfig(filename="mover_app.log", level=logging.INFO)
        self.src = src
        self.dest = dest
        self.md5_src = ""
        self.md5_dest = None
        self.md5_check = False
        self.folder = None
        self.md5_src = self.get_md5_src()
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"FileMover initialized with source: {src} and destination: {dest}"
        )

    def get_md5(self, file_path: str) -> str:
        """
        Get the MD5 hash of a file
        :param file_path:
        :return:
        """
        # Get the MD5 hash of a file
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_md5_src(self) -> str:
        """
        Get the MD5 hash of the source file
        :return: str - MD5 hash of the source file
        """
        if self.md5_src is None:
            self.md5_src = self.get_md5(self.src)

    def get_md5_dest(self) -> str:
        """
        Get the MD5 hash of the destination file
        :return: str - MD5 hash of the destination file
        """
        if self.md5_dest is None:
            self.md5_dest = self.get_md5(self.dest)

    def get_md5s(self) -> None:
        """
        Get the MD5 hashes of the source and destination files
        """
        self.get_md5_src()
        self.get_md5_dest()

    def check_finished(self, location: str = "dest") -> bool:
        """
        Check if the file  MD5 hash matches before and after
        if the the md5 is false then the selected location is updated
        :param location: list - location of the file to check
        :return: bool - True if the file MD5 hash matches, False otherwise
        """
        file_loc = self.src if location == "src" else self.dest
        finished = self.get_md5(file_loc) == self.md5_src
        if not finished:
            self.md5_src = self.get_md5(self.src)
            if location == "dest":
                self.md5_dest = self.get_md5(self.dest)
        return finished

    def compare_md5(self) -> bool:
        """
        Compare the MD5 hashes of the source and destination files
        :return: bool - True if the MD5 hashes match, False otherwise
        """
        if self.md5_check is None:
            self.md5_check = self.get_md5_src() == self.get_md5_dest()
        return self.md5_check

    # def check_file_exists(self, location:str ="src") -> bool:
    #     """
    #     Check if the source file exists
    #     :param location: list - location of the file to check
    #     :return: bool - True if the file exists, False otherwise
    #     """
    #     file_loc = self.src if location == "src" else self.dest
    #     return os.path.exists(file_loc)

    def move_file(self) -> bool:
        """
        Move the file from source to destination and check if the file is moved successfully
        :return: bool - True if the file is moved successfully and MD5 hash matches, False otherwise
        """
        # Calculate MD5 of the source file
        self.md5_src = self.get_md5(self.src)

        dest_dir = os.path.dirname(self.dest)
        if not os.path.exists(self.dest):
            os.makedirs(dest_dir, exist_ok=True)
        # Move the file/ directory
        if os.path.isdir(self.src):
            # Move the directory
            shutil.copytree(self.src, self.dest)
            self.logger.info(f"Directory moved from {self.src} to {self.dest}")

            # Check MD5 for each file in the directory
            for root, _, files in os.walk(self.src):
                for file in files:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(
                        self.dest, os.path.relpath(src_file, self.src)
                    )

                    # Calculate MD5 of the source file
                    md5_src = self.get_md5(src_file)

                    # Calculate MD5 of the destination file
                    md5_dest = self.get_md5(dest_file)

                    # Check if the MD5 hashes match
                    if md5_src != md5_dest:
                        self.logger.warning(
                            f"MD5 hash mismatch for file {src_file}! File may be corrupted."
                        )
                        return False

            self.logger.info(
                "All files in the directory moved successfully and MD5 hashes match."
            )
            return True
        else:
            shutil.copy(self.src, self.dest)

            # Calculate MD5 of the destination file
            self.md5_dest = self.get_md5(self.dest)

            # Check if the MD5 hashes match
            self.md5_check = self.md5_src == self.md5_dest

            if self.md5_check:
                self.logger.info(
                    f"File {self.src} moved successfully and MD5 hash matches: {self.md5_src}"
                )
                return True
            else:
                self.logger.error("MD5 hash mismatch! File may be corrupted.")
                return False
