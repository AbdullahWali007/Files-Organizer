# File Organizer Pro

File Organizer Pro is a robust, multi-threaded desktop application designed to bring order to chaotic directories. Built with Python and `customtkinter`, it wraps powerful file-management logic in a modern, minimalist dark-mode interface. 

Whether you are managing massive datasets, development assets, or just a messy "Downloads" folder, this tool handles heavy lifting asynchronously without freezing the UI, keeping you informed with real-time progress tracking.

## Features

* **Modern & Sleek UI:** Built with `customtkinter` for a premium, native-feeling dark mode aesthetic.
* **Intelligent Categorization:** Comes pre-configured with a granular dictionary for sorting Development files (Python, Web, Configs), ML/Data Models, 3D/Design Assets, MATLAB environments, and general media.
* **Safe Preview Mode (Dry Run):** Simulate the organization process before committing. The app generates a summary of planned moves, ensuring you never accidentally misplace important files.
* **Undo Ledger:** Mistakes happen. Every successful batch operation is logged to a local JSON ledger, allowing you to instantly revert the directory to its previous state with a single click.
* **Asynchronous Processing:** File operations run on a dedicated background thread, keeping the progress bar smooth and the application responsive even when processing thousands of files.
* **Custom Rules Engine:** Easily add, edit, or remove specific file extensions and route them to custom subfolders using the built-in GUI manager.

2. **Install dependencies:**
The only external dependency required is `customtkinter`.
```bash
pip install customtkinter

```


3. **Run the application:**
```bash
python file_organizer.py

```



## Usage

1. **Target Directory:** Click "Browse" to select the folder you want to organize.
2. **Configure Rules (Optional):** Toggle "Use Custom Rules" to define specific routing for niche file types.
3. **Preview:** Click "Preview (Dry Run)" to see exactly where your files will go without actually moving them.
4. **Organize:** Click "Organize Files" to execute the move.
5. **Revert:** If you change your mind, click the red "Undo Last Action" button at the top right to restore files to their original locations.

## Extensibility

The underlying routing logic dynamically reads from the `default_rules` dictionary. Developers can easily expand file categories (e.g., adding specialized MLOps pipelines, custom game engine assets, or specific cloud config files) simply by updating the dictionary mapping in the `__init__` method.

---

*Developed by M. Abdullah Wali*
