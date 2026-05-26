import os
import shutil
import json
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

# Set modern appearance
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")

class FileOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer Pro")
        self.root.geometry("750x600")
        self.root.minsize(750, 600)
        
        # Initialize variables
        self.selected_folder = ctk.StringVar()
        self.use_custom_rules = ctk.BooleanVar(value=False)
        self.status_text = ctk.StringVar(value="Ready")
        self.custom_rules = []
        self.history_file = 'organize_history.json'
        
        # Threading queue for UI updates
        self.queue = queue.Queue()
        
        # Load default and custom rules
        # Expanded default and custom rules
        self.default_rules = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff', '.ico'],
            'Documents': {
                'Word': ['.doc', '.docx', '.rtf', '.odt', '.wps'],
                'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods', '.tsv'],
                'Presentations': ['.ppt', '.pptx', '.odp', '.key'],
                'PDF': ['.pdf'],
                'Text': ['.txt', '.md', '.log']
            },
            'Development': {
                'Python': ['.py', '.ipynb', '.pyw', '.whl', '.requirements'],
                'Web': ['.html', '.css', '.js', '.jsx', '.ts', '.tsx', '.wasm'],
                'Data_and_Models': ['.json', '.xml', '.yaml', '.yml', '.h5', '.pkl', '.pt', '.onnx', '.tflite', '.pb'],
                'MATLAB': ['.m', '.mat', '.fig', '.mlx'],
                'Config': ['.env', '.ini', '.cfg', '.conf', '.dockerignore', '.gitignore']
            },
            'Design_and_3D': ['.psd', '.ai', '.xd', '.blend', '.obj', '.gltf', '.glb', '.fbx', '.stl'],
            'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm'],
            'Audio': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.mid'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
            'Executables': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.sh', '.bat', '.cmd', '.apk'],
            'Misc': []
        }
        
                
        self.load_custom_rules()
        
        # Create GUI
        self.style_treeview()
        self.create_widgets()
        
        # Start queue polling
        self.process_queue()
        
    def style_treeview(self):
        # Configure standard ttk Treeview to blend better with CustomTkinter dark mode
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure('Treeview', 
                             background="#2b2b2b", 
                             foreground="white", 
                             rowheight=25, 
                             fieldbackground="#2b2b2b",
                             borderwidth=0)
        self.style.map('Treeview', background=[('selected', '#1f538d')])
        self.style.configure('Treeview.Heading', 
                             background="#1f538d", 
                             foreground="white", 
                             font=('Helvetica', 10, 'bold'))
        self.style.map('Treeview.Heading', background=[('active', '#14375e')])

    def create_widgets(self):
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill=ctk.X, pady=(0, 15))
        
        ctk.CTkLabel(
            header_frame, 
            text="File Organizer Pro", 
            font=ctk.CTkFont(family='Helvetica', size=20, weight='bold')
        ).pack(side=ctk.LEFT)
        
        # Action Buttons (Top Right)
        ctk.CTkButton(
            header_frame, 
            text="Undo Last Action", 
            command=self.undo_last_action,
            fg_color="#b23b3b",
            hover_color="#8b2e2e",
            width=120
        ).pack(side=ctk.RIGHT)

        # Folder selection section
        folder_frame = ctk.CTkFrame(main_frame)
        folder_frame.pack(fill=ctk.X, pady=(0, 15))
        
        ctk.CTkLabel(folder_frame, text="Target Directory:", font=ctk.CTkFont(weight="bold")).pack(side=ctk.LEFT, padx=10, pady=10)
        
        ctk.CTkEntry(folder_frame, textvariable=self.selected_folder, state='readonly').pack(
            side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 10))
        ctk.CTkButton(folder_frame, text="Browse", command=self.browse_folder, width=100).pack(side=ctk.RIGHT, padx=10)
        
        # Core Actions
        action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_frame.pack(fill=ctk.X, pady=10)

        ctk.CTkButton(
            action_frame, 
            text="Preview (Dry Run)", 
            command=lambda: self.start_processing(preview=True),
            fg_color="#d48c00",
            hover_color="#a36b00"
        ).pack(side=ctk.LEFT, expand=True, padx=5)

        ctk.CTkButton(
            action_frame, 
            text="Organize Files", 
            command=lambda: self.start_processing(preview=False),
            fg_color="#28a745",
            hover_color="#218838"
        ).pack(side=ctk.RIGHT, expand=True, padx=5)
        
        # Custom rules section
        self.custom_rules_frame = ctk.CTkFrame(main_frame)
        
        self.custom_rules_check = ctk.CTkCheckBox(
            main_frame, 
            text="Use Custom Rules", 
            variable=self.use_custom_rules,
            command=self.toggle_custom_rules
        )
        self.custom_rules_check.pack(anchor=ctk.W, pady=(15, 5))
        
        # Custom rules controls (hidden by default)
        self.rules_controls_frame = ctk.CTkFrame(self.custom_rules_frame, fg_color="transparent")
        self.rules_controls_frame.pack(fill=ctk.X, pady=(5, 10), padx=10)
        
        # Treeview (using standard ttk because CTk doesn't have a native data grid yet)
        tree_frame = ctk.CTkFrame(self.custom_rules_frame)
        tree_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.rules_tree = ttk.Treeview(
            tree_frame, 
            columns=('extension', 'folder', 'subfolder'), 
            show='headings', 
            height=5
        )
        self.rules_tree.heading('extension', text='Extension')
        self.rules_tree.heading('folder', text='Main Folder')
        self.rules_tree.heading('subfolder', text='Subfolder')
        self.rules_tree.column('extension', width=100)
        self.rules_tree.column('folder', width=150)
        self.rules_tree.column('subfolder', width=150)
        self.rules_tree.pack(fill=ctk.BOTH, expand=True)
        
        ctk.CTkButton(self.rules_controls_frame, text="Add", command=self.add_rule, width=80).pack(side=ctk.LEFT, padx=(0, 5))
        ctk.CTkButton(self.rules_controls_frame, text="Edit", command=self.edit_rule, width=80).pack(side=ctk.LEFT, padx=(0, 5))
        ctk.CTkButton(self.rules_controls_frame, text="Remove", command=self.remove_rule, width=80).pack(side=ctk.LEFT)
        
        # Status & Progress bar
        status_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        status_frame.pack(fill=ctk.X, side=ctk.BOTTOM, pady=(10, 0))
        
        ctk.CTkLabel(status_frame, textvariable=self.status_text).pack(side=ctk.LEFT)
        
        self.progress = ctk.CTkProgressBar(main_frame)
        self.progress.pack(fill=ctk.X, side=ctk.BOTTOM, pady=(10, 0))
        self.progress.set(0)
        
        # Load rules into treeview
        self.update_rules_treeview()
    
    def process_queue(self):
        """Processes messages from the background thread to update the UI safely"""
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg['type'] == 'progress':
                    self.progress.set(msg['value']) # CTk uses 0.0 to 1.0
                elif msg['type'] == 'status':
                    self.status_text.set(msg['text'])
                elif msg['type'] == 'preview_done':
                    self.show_preview_modal(msg['data'])
                elif msg['type'] == 'done':
                    messagebox.showinfo("Success", msg['text'])
                elif msg['type'] == 'error':
                    messagebox.showerror("Error", msg['text'])
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def toggle_custom_rules(self):
        if self.use_custom_rules.get():
            self.custom_rules_frame.pack(fill=ctk.BOTH, expand=True, pady=(5, 0))
        else:
            self.custom_rules_frame.pack_forget()
    
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_folder.set(folder_selected)
    
    def start_processing(self, preview=False):
        folder = self.selected_folder.get()
        if not folder:
            messagebox.showerror("Error", "Please select a folder first")
            return
            
        rules = self.get_active_rules()
        
        # Disable UI elements during processing
        self.status_text.set("Initializing..." if not preview else "Generating Preview...")
        self.progress.set(0)
        
        # Start background thread
        thread = threading.Thread(
            target=self._process_files_thread, 
            args=(folder, rules, preview),
            daemon=True
        )
        thread.start()

    def _process_files_thread(self, folder, rules, preview):
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            
            if not files:
                self.queue.put({'type': 'status', 'text': 'Ready'})
                self.queue.put({'type': 'done', 'text': 'No files to organize in the selected folder'})
                return
            
            total_files = len(files)
            moved_files = 0
            action_ledger = []
            preview_summary = {}

            if not preview:
                self.create_folders_structure(folder, rules)

            for i, filename in enumerate(files):
                file_ext = os.path.splitext(filename)[1].lower()
                src_path = os.path.join(folder, filename)
                
                dest_path = self.get_destination_path(folder, file_ext, rules, filename)
                
                if not dest_path or os.path.dirname(src_path) == os.path.dirname(dest_path):
                    continue
                
                if preview:
                    dest_folder_rel = os.path.relpath(os.path.dirname(dest_path), folder)
                    if dest_folder_rel not in preview_summary:
                        preview_summary[dest_folder_rel] = 0
                    preview_summary[dest_folder_rel] += 1
                else:
                    shutil.move(src_path, dest_path)
                    action_ledger.append({
                        "original_path": src_path,
                        "new_path": dest_path
                    })
                
                moved_files += 1
                self.queue.put({'type': 'progress', 'value': (i + 1) / total_files})
                self.queue.put({'type': 'status', 'text': f"Processing: {filename}..."})

            if preview:
                self.queue.put({'type': 'preview_done', 'data': preview_summary})
                self.queue.put({'type': 'status', 'text': 'Preview ready.'})
            else:
                if action_ledger:
                    self.save_ledger(action_ledger)
                self.queue.put({'type': 'status', 'text': f"{moved_files} files moved successfully!"})
                self.queue.put({'type': 'done', 'text': f"Organized {moved_files} files successfully."})
                self.queue.put({'type': 'progress', 'value': 0})

        except Exception as e:
            self.queue.put({'type': 'status', 'text': 'Error occurred.'})
            self.queue.put({'type': 'error', 'text': str(e)})

    def show_preview_modal(self, summary_data):
        modal = ctk.CTkToplevel(self.root)
        modal.title("Preview: Dry Run Results")
        modal.geometry("400x350")
        modal.transient(self.root)
        modal.grab_set()

        ctk.CTkLabel(modal, text="Planned Moves Summary", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        if not summary_data:
            ctk.CTkLabel(modal, text="No files need to be moved.").pack(pady=20)
        else:
            scroll_frame = ctk.CTkScrollableFrame(modal)
            scroll_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=10)

            total = 0
            for folder, count in summary_data.items():
                ctk.CTkLabel(scroll_frame, text=f"• {count} file(s) -> /{folder}").pack(anchor="w", pady=2)
                total += count
            
            ctk.CTkLabel(modal, text=f"Total files to move: {total}", font=ctk.CTkFont(weight="bold")).pack(pady=5)

        ctk.CTkButton(modal, text="Close", command=modal.destroy).pack(pady=10)

    def undo_last_action(self):
        if not os.path.exists(self.history_file):
            messagebox.showinfo("Undo", "No recent actions found to undo.")
            return
            
        try:
            with open(self.history_file, 'r') as f:
                ledger = json.load(f)
                
            if not ledger:
                messagebox.showinfo("Undo", "History is empty.")
                return

            confirm = messagebox.askyesno("Confirm Undo", f"Are you sure you want to revert {len(ledger)} file moves?")
            if not confirm: return

            self.status_text.set("Reverting files...")
            self.progress.set(0)
            
            # Start background thread for undo
            threading.Thread(target=self._undo_thread, args=(ledger,), daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Could not read history: {str(e)}")

    def _undo_thread(self, ledger):
        try:
            total = len(ledger)
            restored = 0
            for i, action in enumerate(ledger):
                src = action["original_path"]
                dest = action["new_path"]
                
                if os.path.exists(dest):
                    # Make sure original directory exists just in case
                    os.makedirs(os.path.dirname(src), exist_ok=True)
                    shutil.move(dest, src)
                    restored += 1
                
                self.queue.put({'type': 'progress', 'value': (i + 1) / total})
            
            # Clear history after successful undo
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
                
            self.queue.put({'type': 'status', 'text': 'Undo complete.'})
            self.queue.put({'type': 'done', 'text': f"Successfully restored {restored}/{total} files."})
            self.queue.put({'type': 'progress', 'value': 0})
            
        except Exception as e:
            self.queue.put({'type': 'status', 'text': 'Undo Error.'})
            self.queue.put({'type': 'error', 'text': f"Error during undo: {str(e)}"})

    def save_ledger(self, ledger):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(ledger, f, indent=4)
        except Exception as e:
            print(f"Failed to save undo history: {e}")

    def create_folders_structure(self, base_folder, rules):
        for main_folder, sub_rules in rules.items():
            if isinstance(sub_rules, dict):
                main_folder_path = os.path.join(base_folder, main_folder)
                os.makedirs(main_folder_path, exist_ok=True)
                
                for sub_folder in sub_rules.keys():
                    sub_folder_path = os.path.join(main_folder_path, sub_folder)
                    os.makedirs(sub_folder_path, exist_ok=True)
            else:
                folder_path = os.path.join(base_folder, main_folder)
                os.makedirs(folder_path, exist_ok=True)
        
        misc_folder = os.path.join(base_folder, 'Misc')
        if 'Misc' not in rules:
            os.makedirs(misc_folder, exist_ok=True)
    
    def get_destination_path(self, base_folder, file_ext, rules, filename):
        for main_folder, sub_rules in rules.items():
            if isinstance(sub_rules, dict):
                for sub_folder, extensions in sub_rules.items():
                    if file_ext in extensions:
                        dest_folder = os.path.join(base_folder, main_folder, sub_folder)
                        return self.handle_filename_conflict(dest_folder, filename)
            else:
                if file_ext in sub_rules:
                    dest_folder = os.path.join(base_folder, main_folder)
                    return self.handle_filename_conflict(dest_folder, filename)
        
        dest_folder = os.path.join(base_folder, 'Misc')
        return self.handle_filename_conflict(dest_folder, filename)
    
    def handle_filename_conflict(self, dest_folder, filename):
        dest_path = os.path.join(dest_folder, filename)
        base, ext = os.path.splitext(filename)
        counter = 1
        
        while os.path.exists(dest_path):
            new_filename = f"{base} ({counter}){ext}"
            dest_path = os.path.join(dest_folder, new_filename)
            counter += 1
        
        return dest_path
    
    def get_active_rules(self):
        if self.use_custom_rules.get() and self.custom_rules:
            rules = self.default_rules.copy()
            for rule in self.custom_rules:
                ext, main_folder, subfolder = rule
                self.remove_extension_from_rules(rules, ext)
                if main_folder in rules and isinstance(rules[main_folder], dict):
                    if subfolder:
                        if subfolder not in rules[main_folder]:
                            rules[main_folder][subfolder] = []
                        rules[main_folder][subfolder].append(ext)
                else:
                    if main_folder not in rules:
                        rules[main_folder] = []
                    rules[main_folder].append(ext)
            return rules
        else:
            return self.default_rules
    
    def remove_extension_from_rules(self, rules, ext):
        for main_folder, sub_rules in rules.items():
            if isinstance(sub_rules, dict):
                for sub_folder, extensions in sub_rules.items():
                    if ext in extensions:
                        extensions.remove(ext)
            else:
                if ext in sub_rules:
                    sub_rules.remove(ext)
    
    def add_rule(self):
        self.rule_dialog("Add New Rule")
    
    def edit_rule(self):
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a rule to edit")
            return
        item = self.rules_tree.item(selected[0])
        values = item['values']
        self.rule_dialog("Edit Rule", values[0], values[1], values[2])
    
    def remove_rule(self):
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a rule to remove")
            return
        item = self.rules_tree.item(selected[0])
        ext = item['values'][0]
        
        self.custom_rules = [r for r in self.custom_rules if r[0] != ext]
        self.save_custom_rules()
        self.update_rules_treeview()
    
    def rule_dialog(self, title, extension="", folder="", subfolder=""):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Extension
        ctk.CTkLabel(main_frame, text="File Extension:").grid(row=0, column=0, padx=5, pady=10, sticky=ctk.W)
        ext_entry = ctk.CTkEntry(main_frame)
        ext_entry.grid(row=0, column=1, padx=5, pady=10, sticky=ctk.EW)
        ext_entry.insert(0, extension)
        
        # Main folder
        ctk.CTkLabel(main_frame, text="Main Folder:").grid(row=1, column=0, padx=5, pady=10, sticky=ctk.W)
        folder_combobox = ctk.CTkComboBox(main_frame, values=list(self.default_rules.keys()))
        folder_combobox.grid(row=1, column=1, padx=5, pady=10, sticky=ctk.EW)
        folder_combobox.set(folder if folder else list(self.default_rules.keys())[0])
        
        # Subfolder
        ctk.CTkLabel(main_frame, text="Subfolder (Docs):").grid(row=2, column=0, padx=5, pady=10, sticky=ctk.W)
        subfolder_combobox = ctk.CTkComboBox(main_frame, values=[""])
        subfolder_combobox.grid(row=2, column=1, padx=5, pady=10, sticky=ctk.EW)
        subfolder_combobox.set(subfolder)
        
        def update_subfolders(*args):
            if folder_combobox.get() == "Documents":
                sub_opts = list(self.default_rules['Documents'].keys())
                subfolder_combobox.configure(values=sub_opts, state='normal')
                if not subfolder_combobox.get() in sub_opts:
                    subfolder_combobox.set(sub_opts[0])
            else:
                subfolder_combobox.set('')
                subfolder_combobox.configure(values=[""], state='disabled')
        
        # Poll for combobox changes since CTk combobox doesn't trigger Virtual Events the same way
        dialog.after(100, self._check_combo_change, folder_combobox, folder_combobox.get(), update_subfolders, dialog)
        update_subfolders() 
        
        def save_rule():
            ext = ext_entry.get().strip().lower()
            main_folder = folder_combobox.get().strip()
            subfolder_val = subfolder_combobox.get().strip() if folder_combobox.get() == "Documents" else ""
            
            if not ext.startswith('.'): ext = '.' + ext
            
            if not ext or not main_folder:
                messagebox.showwarning("Warning", "Extension and Main Folder are required")
                return
            
            for i, rule in enumerate(self.custom_rules):
                if rule[0] == ext:
                    self.custom_rules[i] = (ext, main_folder, subfolder_val)
                    break
            else:
                self.custom_rules.append((ext, main_folder, subfolder_val))
            
            self.save_custom_rules()
            self.update_rules_treeview()
            dialog.destroy()
        
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ctk.CTkButton(buttons_frame, text="Save", command=save_rule, width=100).pack(side=ctk.LEFT, padx=10)
        ctk.CTkButton(buttons_frame, text="Cancel", command=dialog.destroy, width=100, fg_color="#555555").pack(side=ctk.LEFT)
        
        main_frame.columnconfigure(1, weight=1)

    def _check_combo_change(self, widget, last_val, callback, dialog):
        if not dialog.winfo_exists(): return
        current = widget.get()
        if current != last_val:
            callback()
        dialog.after(100, self._check_combo_change, widget, current, callback, dialog)
    
    def update_rules_treeview(self):
        self.rules_tree.delete(*self.rules_tree.get_children())
        for ext, folder, subfolder in self.custom_rules:
            self.rules_tree.insert('', 'end', values=(ext, folder, subfolder))
    
    def load_custom_rules(self):
        try:
            if os.path.exists('file_organizer_rules.json'):
                with open('file_organizer_rules.json', 'r') as f:
                    loaded_rules = json.load(f)
                    self.custom_rules = [
                        (rule[0], rule[1], rule[2] if len(rule) > 2 else "") 
                        for rule in loaded_rules
                    ]
        except Exception:
            self.custom_rules = []
    
    def save_custom_rules(self):
        try:
            with open('file_organizer_rules.json', 'w') as f:
                json.dump(self.custom_rules, f)
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not save custom rules: {str(e)}")

if __name__ == "__main__":
    root = ctk.CTk()
    app = FileOrganizerApp(root)
    root.mainloop()