import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import win32api
import datetime
import win32file


class FileCopyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Copy Utility by helpdesk8675")
        self.root.geometry("600x350")

        # Get available drives
        self.drives = self.get_available_drives()

        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Source Drive Selection
        ttk.Label(main_frame, text="Source Drive:").grid(row=0, column=0, pady=5)
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(main_frame, textvariable=self.source_var)
        self.source_combo['values'] = self.drives
        self.source_combo.grid(row=0, column=1, pady=5)
        self.source_combo.bind('<<ComboboxSelected>>', self.update_target_drives)

        # Target Drive Selection
        ttk.Label(main_frame, text="Target Drive:").grid(row=1, column=0, pady=5)
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(main_frame, textvariable=self.target_var)
        self.target_combo.grid(row=1, column=1, pady=5)

        # Configuration File Selection
        ttk.Label(main_frame, text="Configuration File:").grid(row=2, column=0, pady=5)
        self.config_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.config_path, width=50).grid(row=2, column=1, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_config).grid(row=2, column=2, pady=5)

        # Start Button
        ttk.Button(main_frame, text="Start Copy", command=self.start_copy).grid(row=3, column=1, pady=20)

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, length=400, variable=self.progress_var, mode='determinate')
        self.progress_bar.grid(row=4, column=0, columnspan=3, pady=5)

        # Status Label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=5, column=0, columnspan=3, pady=5)

    def get_available_drives(self):
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        return [drive[0] for drive in drives]

    def update_target_drives(self, event=None):
        source_drive = self.source_var.get()
        available_targets = [drive for drive in self.drives if drive != source_drive and drive != 'C']
        self.target_combo['values'] = available_targets
        if self.target_var.get() in [source_drive, 'C']:
            self.target_var.set('')

    def browse_config(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            self.config_path.set(filename)

    def start_copy(self):
        source_drive = self.source_var.get()
        target_drive = self.target_var.get()
        config_file = self.config_path.get()

        if not all([source_drive, target_drive, config_file]):
            messagebox.showerror("Error", "Please select all required fields")
            return

        try:
            # Read configuration file
            with open(config_file, 'r') as f:
                config_items = set(line.strip() for line in f if line.strip())

            # Constants for file attributes
            FILE_ATTRIBUTE_REPARSE_POINT = 0x400

            def is_reparse_point(path):
                """Check if a path is a reparse point"""
                try:
                    attrs = win32api.GetFileAttributes(path)
                    return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
                except:
                    return False

            def convert_to_long_path(path):
                """Convert a path to Windows extended-length path format"""
                if path.startswith('\\\\?\\'):
                    return path
                return '\\\\?\\' + os.path.abspath(path)

            # Get all files from source, skipping reparse points
            source_files = []
            source_root = convert_to_long_path(f"{source_drive}:\\")
        
            for root, dirs, files in os.walk(source_root, followlinks=False):
                # Remove reparse points and symlinks from dirs list
                dirs[:] = [d for d in dirs if not (
                    is_reparse_point(os.path.join(root, d)) or 
                    os.path.islink(os.path.join(root, d))
                )]
            
                for file in files:
                    file_path = os.path.join(root, file)
                    # Only add file if it's not a reparse point or symlink
                    if not (is_reparse_point(file_path) or os.path.islink(file_path)):
                        source_files.append(file_path)

            total_files = len(source_files)
            processed_files = 0

            for source_file in source_files:
                # Get relative path without the extended path prefix
                relative_path = os.path.relpath(
                    source_file.replace('\\\\?\\', ''), 
                    f"{source_drive}:\\"
                )
            
                target_file = convert_to_long_path(
                    os.path.join(f"{target_drive}:\\", relative_path)
                )
            
                # Create target directory if it doesn't exist
                target_dir = os.path.dirname(target_file)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir, exist_ok=True)

                try:
                    # Get original creation and modification times
                    creation_time = os.path.getctime(source_file)
                    modified_time = os.path.getmtime(source_file)

                    # Check if file is in configuration
                    if any(config_item in source_file.replace('\\\\?\\', '') for config_item in config_items):
                        # Copy file normally, without following symlinks
                        shutil.copy2(source_file, target_file, follow_symlinks=False)
                    else:
                        # Create zero-byte file
                        with open(target_file, 'w') as f:
                            pass
    
                    # Set both creation and modification times
                    os.utime(target_file, (modified_time, modified_time))
                    if hasattr(os, 'utime'):
                        try:
                            win32_handle = win32file.CreateFile(
                                target_file,
                                win32file.GENERIC_WRITE,
                                0,
                                None,
                                win32file.OPEN_EXISTING,
                                win32file.FILE_ATTRIBUTE_NORMAL,
                                None
                            )
                            win32file.SetFileTime(
                                win32_handle,
                                win32api.Time_Unix_To_FileTime(creation_time),
                                None,
                                win32api.Time_Unix_To_FileTime(modified_time)
                            )
                            win32file.CloseHandle(win32_handle)
                        except:
                            pass  # If setting creation time fails, at least modification time is preserved

                except OSError as e:
                    # Log error but continue with next file
                    print(f"Error processing {relative_path}: {str(e)}")
                    continue

                processed_files += 1
                self.progress_var.set((processed_files / total_files) * 100)
                self.root.update()

            self.status_var.set("Copy completed successfully!")
            messagebox.showinfo("Success", "File copy process completed!")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set("Error occurred during copy")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileCopyGUI(root)
    root.mainloop()
