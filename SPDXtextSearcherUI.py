import tkinter as tk
from tkinter import ttk, filedialog, font, messagebox
import os
import csv

# Removed: from spdx_license_list import LICENSES


# --- Global Data Storage ---

# Global variable to store the final, structured search results
SEARCH_RESULTS = []


# --- Core Search Function (Modified: Removed OSI Lookup) ---

def search_license_files(folder_path, search_phrase):
    """
    Searches for a phrase in all .txt files in the specified folder.
    Results are based only on local file content.
    """
    global SEARCH_RESULTS

    # --- Input Validation ---
    if not folder_path or not os.path.isdir(folder_path):
        # Clear global results on error
        SEARCH_RESULTS = []
        return [{'error': "Error: Please select a valid folder containing your license files."}]

    if not search_phrase or not search_phrase.strip():
        SEARCH_RESULTS = []
        return [{'error': "Error: The search phrase cannot be empty."}]

    search_phrase_lower = search_phrase.lower()
    matches = []

    # --- File Iteration and Search: Only .txt files in nominated directory ---
    try:
        for filename in os.listdir(folder_path):
            if filename.endswith(".txt"):
                filepath = os.path.join(folder_path, filename)
                try:
                    # R (read mode), utf-8 encoding, ignore errors for robustness
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        content_lower = content.lower()

                        # --- Actual text search of the whole file content ---
                        if search_phrase_lower in content_lower:

                            # --- 1. Get Full License Name from first line ---
                            first_line = content.strip().split('\n')[0].strip()
                            license_name = first_line if first_line else filename

                            # --- 2. Get Paragraph Context (Split for separate columns) ---
                            paragraphs = content.split('\n\n')

                            paragraph_before = ""
                            matching_paragraph = ""
                            context_parts = []

                            # Find the first paragraph in the file with a match
                            for i, p in enumerate(paragraphs):
                                p_stripped = p.strip()
                                if search_phrase_lower in p.lower():
                                    # Set paragraph before (for CSV)
                                    if i > 0:
                                        paragraph_before = paragraphs[i - 1].strip()
                                        context_parts.append(paragraph_before)

                                    # Set the matching paragraph (for CSV)
                                    matching_paragraph = p_stripped
                                    context_parts.append(matching_paragraph)

                                    # Add paragraph after for better GUI context (optional)
                                    if i < len(paragraphs) - 1:
                                        context_parts.append(paragraphs[i + 1].strip())

                                    # Exit after finding the first match in the file
                                    break

                            # Join paragraphs for GUI display context
                            context_display = "\n\n[...] \n\n".join(context_parts)

                            # --- 3. OSI Status: Hardcoded to N/A as external libraries are disallowed ---
                            osi_status = "N/A (Local Search Only)"

                            # Store ALL required data for the CSV export
                            matches.append({
                                'license_name': license_name,
                                'osi_approved': osi_status,
                                'matching_paragraph': matching_paragraph,
                                'paragraph_before': paragraph_before,
                                'context_display': context_display  # Used for the GUI
                            })

                except Exception as e:
                    # The error you reported occurred here. We are now only logging it.
                    print(f"Could not read or process file {filename}: {e}")

    except Exception as e:
        SEARCH_RESULTS = []
        return [{'error': f"An unexpected error occurred: {e}"}]

    if not matches:
        SEARCH_RESULTS = []
        return [{'error': f"No files containing the phrase '{search_phrase}' were found."}]

    # Store results globally and sort them
    SEARCH_RESULTS = sorted(matches, key=lambda x: x['license_name'])

    # Return a simplified list for GUI display
    return [
        {'license_name': m['license_name'], 'osi_approved': m['osi_approved'], 'context_display': m['context_display']}
        for m in SEARCH_RESULTS]


# --- GUI Application Setup (Using Tkinter) ---

class LicenseSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local License Text Search Tool")
        self.root.geometry("700x550")
        self.root.minsize(600, 400)

        style = ttk.Style(self.root)
        if 'aqua' in style.theme_names():
            style.theme_use('aqua')
        else:
            style.theme_use('vista')

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._create_widgets(main_frame)
        self.export_button.config(state=tk.DISABLED)

    def _create_widgets(self, parent):
        # --- Title and Description ---
        title_font = font.Font(family="Helvetica", size=16, weight="bold")
        ttk.Label(parent, text="Local License Text Search Tool", font=title_font).pack(anchor="w", pady=(0, 5))
        ttk.Label(parent,
                  text="This tool performs a local text search across all .txt files in a nominated directory.").pack(
            anchor="w")
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)

        # --- Input Section ---
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill='x', pady=5)

        # Folder Selection
        folder_frame = ttk.Frame(input_frame)
        folder_frame.pack(fill='x', pady=5)
        ttk.Label(folder_frame, text="1. Select the folder containing license .txt files:").pack(anchor="w")

        self.folder_path_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path_var, state='readonly')
        folder_entry.pack(side=tk.LEFT, fill='x', expand=True, ipady=2, padx=(0, 5))
        ttk.Button(folder_frame, text="Browse...", command=self.browse_folder).pack(side=tk.RIGHT)

        # Search Phrase Input
        phrase_frame = ttk.Frame(input_frame)
        phrase_frame.pack(fill='x', pady=5)
        ttk.Label(phrase_frame, text="2. Enter the exact phrase to search for:").pack(anchor="w")

        self.search_phrase_var = tk.StringVar()
        ttk.Entry(phrase_frame, textvariable=self.search_phrase_var).pack(fill='x', expand=True, ipady=2)

        # --- Search and Export Buttons ---
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text="Search Files", command=self.perform_search).pack(side=tk.LEFT, fill='x',
                                                                                        expand=True, ipady=4,
                                                                                        padx=(0, 5))

        self.export_button = ttk.Button(button_frame, text="Export to CSV 💾", command=self.export_results_to_csv,
                                        state=tk.DISABLED)
        self.export_button.pack(side=tk.RIGHT, fill='x', expand=True, ipady=4, padx=(5, 0))

        # --- Results Display ---
        results_frame = ttk.Frame(parent)
        results_frame.pack(fill='both', expand=True)
        results_label_font = font.Font(family="Helvetica", size=10, weight="bold")
        ttk.Label(results_frame, text="Results:", font=results_label_font).pack(anchor="w")

        self.results_text = tk.Text(results_frame, wrap=tk.WORD, state='disabled', height=10, relief=tk.SOLID,
                                    borderwidth=1)
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.results_text.yview)
        self.results_text['yscrollcommand'] = scrollbar.set

        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.results_text.pack(side=tk.LEFT, fill='both', expand=True)

        bold_font = font.Font(self.results_text, self.results_text.cget("font"))
        bold_font.configure(weight="bold")
        header_font = font.Font(family="Helvetica", size=11, weight="bold")
        self.results_text.tag_configure("bold", font=bold_font)
        self.results_text.tag_configure("header", font=header_font, spacing1=5, spacing3=5)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Please select a folder and enter a search phrase.")
        ttk.Label(parent, textvariable=self.status_var, anchor='w').pack(side=tk.BOTTOM, fill='x', pady=(5, 0))

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path_var.set(folder_selected)

    def highlight_phrase(self, phrase):
        """Finds all occurrences of a phrase in the text widget and applies a 'bold' tag."""
        if not phrase.strip():
            return

        start_pos = '1.0'
        while True:
            # Case-insensitive search (nocase=True)
            start_pos = self.results_text.search(phrase, start_pos, stopindex=tk.END, nocase=True)
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(phrase)}c"
            self.results_text.tag_add("bold", start_pos, end_pos)
            start_pos = end_pos

    def perform_search(self):
        global SEARCH_RESULTS
        folder = self.folder_path_var.get()
        phrase = self.search_phrase_var.get()

        self.results_text.config(state='normal', fg='black')
        self.results_text.delete('1.0', tk.END)
        self.status_var.set("Searching, this may take a moment...")
        self.export_button.config(state=tk.DISABLED)
        self.root.update_idletasks()

        # Run the search
        gui_results = search_license_files(folder, phrase)

        # Check for error messages
        if gui_results and 'error' in gui_results[0]:
            error_message = gui_results[0]['error']
            self.results_text.insert('1.0', error_message)
            self.results_text.config(fg='red')
            self.status_var.set("An error occurred. Please check the results above.")
        else:
            # Populate the results text widget
            for match in SEARCH_RESULTS:
                osi_display = f"[OSI: {match['osi_approved']}]"
                header = f"--- {match['license_name']} {osi_display} ---\n"

                # Use the context generated for the GUI display
                context_display = match['context_display'] + "\n\n"

                self.results_text.insert(tk.END, header, ("header",))
                self.results_text.insert(tk.END, context_display)

            self.highlight_phrase(phrase)

            match_count = len(SEARCH_RESULTS)
            self.status_var.set(f"Search complete. Found matches in {match_count} file(s).")

            if match_count > 0:
                self.export_button.config(state=tk.NORMAL)

        self.results_text.config(state='disabled')

    def export_results_to_csv(self):
        """Opens a file dialog and writes the global search results to a CSV file."""
        global SEARCH_RESULTS

        if not SEARCH_RESULTS:
            messagebox.showinfo("Export Error", "No search results to export. Please run a successful search first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Search Results as CSV"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'full_licence_name',
                    'osi_approved',
                    'matching_paragraph',
                    'paragraph_before'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()

                for match in SEARCH_RESULTS:
                    # Clean up newlines in paragraph data for CSV compatibility
                    writer.writerow({
                        'full_licence_name': match['license_name'],
                        'osi_approved': match['osi_approved'],
                        # Replace newlines with a space to keep it in one CSV cell
                        'matching_paragraph': match['matching_paragraph'].replace('\n', ' ').strip(),
                        'paragraph_before': match['paragraph_before'].replace('\n', ' ').strip()
                    })

            messagebox.showinfo("Export Successful",
                                f"Successfully exported {len(SEARCH_RESULTS)} records to:\n{file_path}")
            self.status_var.set(f"Export successful. Results saved to {os.path.basename(file_path)}.")

        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during CSV export:\n{e}")
            self.status_var.set("CSV export failed.")


# --- Main Application Logic ---
if __name__ == "__main__":
    # Ensure the global results variable is initialized
    SEARCH_RESULTS = []

    root = tk.Tk()
    app = LicenseSearchApp(root)
    root.mainloop()
    