import os
import sys
import platform
import subprocess
import tkinter as tk
import shutil
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from directories import Directories
from qureader import QuReader
from sqreader import SQReader
from PIL import ImageTk, Image

dir_storage = Directories()
environment = platform.system()


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        # print(base_path, relative_path)
    return os.path.join(base_path, relative_path)


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("A&H Showfile Explorer")

        # Create a top menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        self.option_add("*tearOff", False)

        # Create a "File" menu
        self.file_menu = tk.Menu(self.menu_bar)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open: Qu files", command=self.qu_scan_directory)
        self.file_menu.add_command(label="Open: SQ files", command=self.sq_scan_directory)
        self.file_menu.add_command(label="Close All files", command=self.close_all_files)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_app)

        # Create an "About" menu
        self.about_menu = tk.Menu(self.menu_bar)
        self.menu_bar.add_cascade(label="About", menu=self.about_menu)
        self.about_menu.add_command(label="Help", command=self.show_help)
        self.about_menu.add_command(label="About", command=self.show_about)

        # Create a Treeview widget
        self.tree = ttk.Treeview(columns=("filename", "path"))

        self.tree.column("#0", width=200, minwidth=50)
        self.tree.column("filename", width=100, minwidth=50)
        self.tree.column("path", width=300, minwidth=100)

        self.tree.heading("#0", text="Name")
        self.tree.heading("filename", text="Filename")
        self.tree.heading("path", text="Path")

        # Add scrollbar to treeview then pack them
        self.tree_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)
        self.tree_scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # Create item context menu
        self.context_menu = tk.Menu(self, tearoff=False)
        if environment == "Darwin":
            self.context_menu.add_command(label="Show in Finder", command=self.show_in_finder)
            self.context_menu.add_command(label="[future] Copy to..", command=self.copy_on_mac)
            self.context_menu.add_command(label="[future] Move to..", command=self.cut_on_mac)
        else:
            self.context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)
            self.context_menu.add_command(label="Copy to..", command=self.copy)
            self.context_menu.add_command(label="Move to..", command=self.cut)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Add icons to different types of items
        self.folder_icon = ImageTk.PhotoImage(self.image_pad(resource_path("icons/folder.png")))
        self.show_icon = ImageTk.PhotoImage(self.image_pad(resource_path("icons/show.png")))
        self.scene_icon = ImageTk.PhotoImage(self.image_pad(resource_path("icons/scene.png")))
        self.library_icon = ImageTk.PhotoImage(self.image_pad(resource_path("icons/library.png")))

        self.tree.tag_configure("directory", image=self.folder_icon)
        self.tree.tag_configure("show", image=self.show_icon)
        self.tree.tag_configure("scene", image=self.scene_icon)
        self.tree.tag_configure("library", image=self.library_icon)

        # Populate the tree view
        self.populate_tree()

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        elif item not in self.tree.selection():
            self.tree.selection_set(item)
        self.context_menu.post(event.x_root, event.y_root)

    def show_in_explorer(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        for item in selected_items:
            item_path = self.tree.set(item)["path"]
            if os.path.isfile(item_path):
                item_path = os.path.dirname(item_path)
            # Open the file explorer at the location of the selected item or its containing directory
            os.startfile(item_path)

    def show_in_finder(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        for item in selected_items:
            item_path = self.tree.set(item)["path"]
            if os.path.isfile(item_path):
                item_path = os.path.dirname(item_path)
            # Open the finder at the location of the selected item or its containing directory
            subprocess.call(["open", item_path])

    def copy(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        destination_folder = filedialog.askdirectory(title="Select destination folder for copying")
        if not destination_folder:
            return  # User canceled operation
        for item in selected_items:
            # Get the path associated with the selected item
            item_path = self.tree.set(item)["path"]
            # Determine destination path
            destination_path = os.path.join(destination_folder, os.path.basename(item_path))
            # Check if item is a directory
            if os.path.isdir(item_path):
                try:
                    # Copy directory tree
                    shutil.copytree(item_path, destination_path)
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            else:
                try:
                    # Copy individual file
                    shutil.copy(item_path, destination_path)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

    def copy_on_mac(self):
        pass

    def cut(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "No items selected for moving")
            return
        destination_folder = filedialog.askdirectory(title="Select destination folder for moving")
        if not destination_folder:
            return  # User canceled operation
        for item in selected_items:
            # Get the path associated with the selected item
            item_path = self.tree.set(item)["path"]
            # Determine destination path
            destination_path = os.path.join(destination_folder, os.path.basename(item_path))
            # Check if item is a directory
            if os.path.isdir(item_path):
                try:
                    # Move directory tree
                    shutil.move(item_path, destination_path)
                    # Remove the selected item from the tree view
                    self.tree.delete(item)
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            else:
                try:
                    # Move individual file
                    shutil.move(item_path, destination_path)
                    # Remove the selected item from the tree view
                    self.tree.delete(item)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

    def cut_on_mac(self):
        pass

    @staticmethod
    def image_pad(in_image, pad_x=5):
        load_image = Image.open(in_image)
        out_image = Image.new("RGBA", (load_image.width + pad_x, load_image.height))
        out_image.paste(load_image)
        return out_image

    def qu_scan_directory(self):
        directory_path = filedialog.askdirectory(title="Select a folder containing AHQU data")
        if directory_path:
            temp_directory = QuReader.scan_folder(directory_path)
            temp_directory.set_name(os.path.basename(directory_path))
            dir_storage.add_directory(temp_directory)
            self.populate_tree()

    def sq_scan_directory(self):
        directory_path = filedialog.askdirectory(title="Select a folder containing AHSQ data")
        if directory_path:
            temp_directory = SQReader.scan_folder(directory_path)
            temp_directory.set_name(os.path.basename(directory_path))
            dir_storage.add_directory(temp_directory)
            self.populate_tree()

    def close_all_files(self):
        dir_storage.clear_all()
        self.populate_tree()

    def populate_tree(self):
        # Clear existing items
        self.tree.delete(*self.tree.get_children())
        # Populate the tree view with directory structure
        for directory in dir_storage.directories:
            # Insert directory as root item
            dir_id = self.tree.insert("", "end", values=(os.path.basename(directory.path), directory.path, directory),
                                      text=directory.name, tags=("directory",))
            # Insert shows under the directory
            for show in directory.shows:
                show_id = self.tree.insert(dir_id, "end", text=show.name, values=(show.filename, show.path, show),
                                           tags=("show",))
                # Insert scenes under the show
                for scene in show.scenes:
                    scene_id = self.tree.insert(show_id, "end", text=scene.name, values=(scene.filename, scene.path, scene),
                                     tags=("scene",))
                    tab_levels = [scene_id]
                    for level, name, value in scene.explode():
                        next_id = self.tree.insert(tab_levels[level], "end", text=name, values=(name, value))
                        try:
                            tab_levels[level + 1] = next_id
                        except IndexError:
                            tab_levels.append(next_id)

                # Insert libraries under the show
                for library in show.libraries:
                    self.tree.insert(show_id, "end", text=library.name,
                                     values=(library.filename, library.path, library),
                                     tags=("library",))

    def exit_app(self):
        self.destroy()

    @staticmethod
    def show_help():
        messagebox.showinfo("Help",
                            "Select a directory containing either:\n- AHQU/AHSQ folder\n- SHOWS\n- Scenes\n- Libraries")

    @staticmethod
    def show_about():
        messagebox.showinfo("About", "Made by:\nBotond Csatári-Szűcs\nU2VC5A")


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
