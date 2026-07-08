import os

from directory import Directory
from library import Library
from scene import Scene
from show import Show


class QuReader:
    # QuReader remains essentially as is - file format appears to be different and I have no example

    @staticmethod
    def is_library(path):
        if os.path.basename(path).lower().startswith("lib") and os.path.basename(path).lower().endswith(".dat"):
            return True
        return False

    @staticmethod
    def is_scene(path):
        if os.path.basename(path).lower().startswith("scene") and os.path.basename(path).lower().endswith(".dat"):
            return True
        return False

    @staticmethod
    def is_show(path):
        path = os.path.join(path, "SHOW.DAT")
        if os.path.exists(path):
            return True
        return False

    @staticmethod
    def read_library(path):
        # Check if the file exists
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        filepath, filename = os.path.split(path)
        return Library(filename, filepath, format="QU")

    @staticmethod
    def read_scene(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        filepath, filename = os.path.split(path)
        return Scene(filename, filepath, format="QU")

    @staticmethod
    def read_show(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Folder not found: {path}")
        showfilepath = os.path.join(path, "SHOW.DAT")
        if not os.path.exists(showfilepath):
            raise FileNotFoundError(f"File not found: {path}")
        show = Show(os.path.basename(showfilepath), path, format="QU")

        for temp_filename in os.listdir(path):
            temp_filepath = os.path.join(path, temp_filename)

            if temp_filename.lower().startswith("scene") and temp_filename.lower().endswith(".dat"):
                scene = QuReader.read_scene(temp_filepath)
                show.add_scene(scene)

            if temp_filename.lower().startswith("lib") and temp_filename.lower().endswith(".dat"):
                library = QuReader.read_library(temp_filepath)
                show.add_library(library)

        return show

    @staticmethod
    def scan_folder(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Folder not found: {path}")

        # If the data is in the AHQU subfolder, use that, no more scanning
        # (to avoid user mistake of not opening the AHQU folder)
        if os.path.exists(os.path.join(path, "AHQU")):
            temp_directory = QuReader.scan_folder(os.path.join(path, "AHQU"))
            # Update directory name to the parent (AHQU would not be too recognisable)
            temp_directory.set_name(os.path.basename(path))
            return temp_directory

        temp_directory = Directory(os.path.basename(path), path)

        # Check for libraries folder
        if os.path.exists(os.path.join(path, "LIBRARY")):
            for filename in os.listdir(os.path.join(path, "LIBRARY")):
                file_path = os.path.join(path, "LIBRARY", filename)
                if QuReader.is_library(file_path):
                    temp_directory.add_library(QuReader.read_library(file_path))

        # Check for scenes
        if os.path.exists(os.path.join(path, "SCENES")):
            for filename in os.listdir(os.path.join(path, "SCENES")):
                file_path = os.path.join(path, "SCENES", filename)
                if QuReader.is_library(file_path):
                    temp_directory.add_library(QuReader.read_scene(file_path))

        # Check for shows
        if os.path.exists(os.path.join(path, "SHOWS")):
            for show_folder_name in os.listdir(os.path.join(path, "SHOWS")):
                show_folder_path = os.path.join(path, "SHOWS", show_folder_name)
                if QuReader.is_show(show_folder_path):
                    temp_directory.add_show(QuReader.read_show(show_folder_path))

        # Check for shows not in the SHOWS folder
        for current_path in os.listdir(path):
            current_path = os.path.join(path, current_path)
            if os.path.isdir(current_path) and QuReader.is_show(current_path):
                temp_directory.add_show(QuReader.read_show(current_path))

        # Check for orphan libraries / scenes
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if QuReader.is_library(file_path):
                temp_directory.add_library(QuReader.read_library(file_path))
            if QuReader.is_scene(file_path):
                temp_directory.add_scene(QuReader.read_scene(file_path))

        return temp_directory
