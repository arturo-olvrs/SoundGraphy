from enum import Enum
import os
import sys
import traceback
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import soundscapy as sspy
import seaborn as sns
import matplotlib.pyplot as plt


FONT=("Arial", 20)
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class CustomFiltering(ctk.CTkFrame):
    """Custom filtering entry with a dropdown list of values."""
    def __init__(self, master, values, default_text="", **kwargs):
        super().__init__(master, **kwargs)
        self.values = values
        self.default_text = default_text
        
        # Container with better contrast for light mode
        container = ctk.CTkFrame(self, fg_color=("gray90", "gray13"))  # Light mode: gray90, Dark mode: gray13
        container.pack(fill="x")
        
        # Entry with proper contrast
        self.entry = ctk.CTkEntry(
            container,
            fg_color=("white", "gray20"),  # Light mode: white, Dark mode: gray20
            text_color=("black", "white"),  # Light mode: black text, Dark mode: white text
            border_color=("gray70", "gray30")  # Light mode: gray70 border, Dark mode: gray30 border
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<KeyRelease>", self.filter_values)
        
        # Toggle button with proper contrast
        self.toggle_button = ctk.CTkButton(
            container, 
            width=25, 
            text="▼", 
            command=self.toggle_list,
            fg_color=("gray80", "gray25"),  # Light mode: gray80, Dark mode: gray25
            hover_color=("gray70", "gray35"),  # Light mode: gray70, Dark mode: gray35
            text_color=("black", "white")  # Light mode: black text, Dark mode: white text
        )
        self.toggle_button.pack(side="left")
        
        self.list_window = None
        self.list_frame = None
        self.set(self.default_text)
    
    def toggle_list(self):
        """Toggle the visibility of the dropdown list."""
        if self.list_window and self.list_window.winfo_exists():
            self.close_list_window()
        else:
            self.show_list()
    
    def show_list(self):
        """Show the dropdown list with filtered values."""
        self.list_window = ctk.CTkToplevel(self)
        self.list_window.overrideredirect(True)
        
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.list_window.geometry(f"+{x}+{y}")
        
        # Scrollable frame with better contrast
        self.list_frame = ctk.CTkScrollableFrame(
            self.list_window, 
            height=150, 
            width=self.winfo_width(),
            fg_color=("white", "gray20"),  # Light mode: white, Dark mode: gray20
            scrollbar_fg_color=("gray85", "gray25"),  # Light mode: gray85, Dark mode: gray25
            scrollbar_button_color=("gray70", "gray40"),  # Light mode: gray70, Dark mode: gray40
            scrollbar_button_hover_color=("gray60", "gray50")  # Light mode: gray60, Dark mode: gray50
        )
        self.list_frame.pack()
        
        

        # Bind mouse scroll events to the scrollable frame
        def scroll_frame(event):
            self.list_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self._mousewheel_binding = self.list_frame.bind_all("<MouseWheel>", scroll_frame)  # Windows
        self._scroll_up_binding = self.list_frame.bind_all("<Button-4>", lambda e: self.list_frame._parent_canvas.yview_scroll(-1, "units"))  # Linux/macOS
        self._scroll_down_binding = self.list_frame.bind_all("<Button-5>", lambda e: self.list_frame._parent_canvas.yview_scroll(1, "units"))   # Linux/macOS


        current_text = self.entry.get()
        if current_text == self.default_text:
            self.filtered_values = self.values
        else:
            self.filtered_values = [v for v in self.values if current_text.lower() in v.lower()]
        
        for val in self.filtered_values:
            # Buttons with better contrast for light mode
            btn = ctk.CTkButton(
                self.list_frame, 
                text=val, 
                command=lambda v=val: self.select_value(v), 
                fg_color="transparent",
                hover_color=("gray90", "gray30"),  # Light mode: gray90, Dark mode: gray30
                text_color=("black", "white"),  # Light mode: black text, Dark mode: white text
                anchor="w"  # Align text to the left
            )
            btn.pack(fill="x", pady=1)

        self.list_window.focus_force()
        
        self.list_window.bind("<FocusOut>", lambda e: self.close_list_window())
        self.list_window.bind("<Escape>", lambda e: self.close_list_window())
        # Bind global click event to root window to detect clicks outside
        self.winfo_toplevel().bind("<Button-1>", self.on_global_click)

        
    
    def filter_values(self, event=None):
        """Filter the values based on the current entry text."""
        if self.list_window and self.list_window.winfo_exists():
            self.list_window.destroy()
            self.list_window = None
            self.show_list()
    
    def select_value(self, val):
        """Select a value from the dropdown list and set it in the entry."""
        self.set(val)
        self.close_list_window()
    
    def get(self):
        """Get the current value of the entry."""
        return self.entry.get()
    
    def set(self, value):
        """Set the value of the entry."""
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def close_list_window(self):
        """Close the dropdown list window and clean up."""
        if self.list_window:
            try:
                if self.list_window.winfo_exists():
                    self.list_window.destroy()
            except Exception:
                # Window is already destroyed or in invalid state
                pass
            finally:
                self.list_window = None
                
                # Safely unbind global events
                try:
                    self.winfo_toplevel().unbind("<Button-1>")
                except Exception:
                    pass

                # Clean up scroll bindings
                if self.list_frame:
                    try:
                        self.list_frame.unbind_all("<MouseWheel>")
                        self.list_frame.unbind_all("<Button-4>")
                        self.list_frame.unbind_all("<Button-5>")
                    except Exception:
                        pass
                    finally:
                        self.list_frame = None


    def on_global_click(self, event):
        """Handle global click events to close the dropdown list if clicked outside."""
        if self.list_window and self.list_window.winfo_exists():
            try:
                x1 = self.list_window.winfo_rootx()
                y1 = self.list_window.winfo_rooty()
                x2 = x1 + self.list_window.winfo_width()
                y2 = y1 + self.list_window.winfo_height()

                if not (x1 <= event.x_root <= x2 and y1 <= event.y_root <= y2):
                    self.close_list_window()
            except Exception:
                # If the window is in an invalid state, just close it
                self.close_list_window()



class BasicWindow(ctk.CTk):
    """Basic window class for the SoundScape application."""
    def __init__(self):
        super().__init__()
        self.title("SoundScape GUI")
        self.minsize(400, 300)

        width = int(self.winfo_screenwidth()/2)
        hight = int(self.winfo_screenheight()/2)
        self.geometry(f"{width}x{hight}")

        # Override Tkinter's error reporting to catch all callback exceptions
        self.report_callback_exception = self.handle_tkinter_error
        
        # Bind the window close event to cleanup
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    
    def handle_tkinter_error(self, exc_type, exc_value, exc_traceback):
        """
        Handle all Tkinter callback exceptions (button clicks, etc.)
        This method overrides Tkinter's default error reporting
        """
        
        # Print to console with our standard error prefix
        print("Error detected in a TKinter callback:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        
        # Show popup with error details
        error_msg = f"Error Type: {exc_type.__name__}\nError: {str(exc_value)}\n\nSee console for full traceback."
        messagebox.showerror("Error in Application", error_msg)

        exit(1)  # Exit the application after showing the error

    def on_closing(self):
        """Handle application closing event - cleanup matplotlib and close properly."""
        try:
            # Close all matplotlib figures to prevent background errors
            plt.close('all')
                
        except Exception as e:
            print(f"Warning: Error during matplotlib cleanup: {e}")
        
        try:
            # Destroy the window
            self.destroy()
        except Exception as e:
            print(f"Warning: Error during window destruction: {e}")
            
        # Force exit if needed
        sys.exit(0)

    def clear_window(self):
        """Clear the current window by destroying all widgets."""
        for widget in self.winfo_children():
            widget.destroy()



class GUI(BasicWindow):
    """Main GUI class for the SoundScape application."""
    
    # Class constant for maximum unique values threshold
    MAX_UNIQUES = 15

    # Class constant for maximum rows to use Radar plot
    MAX_RADAR_PLOT_ROWS = 7
    
    def __init__(self):
        super().__init__()
        self.df = None  # DataFrame to hold the loaded data             

        self.label = ctk.CTkLabel(self, text="Welcome to SoundScape GUI!\nCreate ISO 12913-3 compliant graphics.", font=FONT)
        self.label.pack(pady=30)

        self.select_doc_button = ctk.CTkButton(self, text="Select Document", command=self.open_select_doc)
        self.select_doc_button.pack(pady=20)

        # Frame for the appearance mode selector
        frame_mode = ctk.CTkFrame(self, fg_color="transparent")
        frame_mode.pack(pady=10)

        label_mode = ctk.CTkLabel(frame_mode, text="Select Appearance Mode:")
        label_mode.pack(pady=(0, 5))

        self.mode_selector = ctk.CTkOptionMenu(frame_mode, values=["System", "Light", "Dark"], command=self.change_mode)
        self.mode_selector.set("System")    # Default mode
        self.mode_selector.pack()

    def change_mode(self, mode):
        """Change the appearance mode of the application."""
        ctk.set_appearance_mode(mode)

    def header(self, back_func, title):
        """Create a header with a back button and title."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=10)

        back_button = ctk.CTkButton(header_frame, text="Back", command=back_func, width=60)
        back_button.pack(side="left", padx=10)

        title_label = ctk.CTkLabel(self, text=title, font=FONT)
        title_label.place(relx=0.5, rely=0.05, anchor="center")

    def open_select_doc(self):
        """Open a file dialog to select a spreadsheet document."""
        filetypes = [
            ("Excel files", "*.xls *.xlsx"),
            ("CSV/TSF files", "*.csv *.tsv"),
            ("OpenDocument Spreadsheet", "*.ods"),
        ]
        filepath = filedialog.askopenfilename(
            title="Select a spreadsheet file",
            filetypes=filetypes
        )
        if not filepath:
            messagebox.showwarning("No File Selected", "Please select a file to proceed.")
            return self.open_select_doc

        # Save name (w/o extension)
        self.file_name = os.path.splitext(os.path.basename(filepath))[0]

        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext in [".csv", ".tsv"]:
                self.df = pd.read_csv(filepath, sep=None, engine='python')  # Automatically detect separator
            elif ext in [".xls", ".xlsx", ".ods"]:
                self.df = pd.read_excel(filepath)
            else:
                raise ValueError("Unsupported file extension")
            
            if self.df.empty:
                raise ValueError("The selected file is empty.")
            

        except Exception as e:
            messagebox.showerror("Error loading file", f"Could not read the file:\n{e}")
            return self.open_select_doc
        
        self.data_type_selection()

    
    def data_type_selection(self):
        """Select the type of data to process."""
        self.clear_window()

        self.header(self.open_select_doc, "What type of data do you have?")

        self.option_emot = ctk.CTkButton(self, text="I have the values of the 8 emotions", command=self.handle_emotions)
        self.option_emot.pack(pady=10)

        self.option_pe = ctk.CTkButton(self, text="I only have the values for the ISOPleasant and ISOEventful", command=self.handle_pe)
        self.option_pe.pack(pady=10)


    def handle_emotions(self):
        """Handle the emotions mapping."""

        # To avoid losing previous selections when reloading the emotions
        previous_selections = {}
        if hasattr(self, "emotion_selectors"):
            try:
                for emot, dropdown in self.emotion_selectors.items():
                    previous_selections[emot] = dropdown.get()
            except Exception:
                # If widgets are destroyed, just start fresh
                previous_selections = {}
        
        self.clear_window()
        self.header(self.data_type_selection, "Map each emotion to a column:")

        columns = list(self.df.columns)
        self.emotion_selectors = {}
        emotion_labels = ["Annoying", "Calm", "Chaotic", "Eventful", "Monotonous", "Pleasant", "Uneventful", "Vibrant"]
        default_labels = {
            "Annoying": "Q2.6",
            "Calm": "Q2.5",
            "Chaotic": "Q2.2",
            "Eventful": "Q2.7",
            "Monotonous": "Q2.8",
            "Pleasant": "Q2.1",
            "Uneventful": "Q2.4",
            "Vibrant": "Q2.3"
        }
        default_labels_after = {
            "Annoying": "PAQ5",
            "Calm": "PAQ8",
            "Chaotic": "PAQ4",
            "Eventful": "PAQ3",
            "Monotonous": "PAQ6",
            "Pleasant": "PAQ1",
            "Uneventful": "PAQ7",
            "Vibrant": "PAQ2"
        }

        for emot in emotion_labels:
            frame = ctk.CTkFrame(self, fg_color="transparent")
            frame.pack(pady=5)
            label = ctk.CTkLabel(frame, text=f"{emot}:", width=120, anchor="w")
            label.pack(side="left", padx=5)



            dropdown = CustomFiltering(frame, values=columns, default_text="Select a column")
            dropdown.pack(side="left", padx=5)
            if emot in previous_selections:
                dropdown.set(previous_selections[emot])
            elif default_labels[emot] in columns:
                dropdown.set(default_labels[emot])
            elif default_labels_after[emot] in columns:
                dropdown.set(default_labels_after[emot])
            else:
                dropdown.set("Select a column")

            self.emotion_selectors[emot] = dropdown
            

        self.confirm_emot_button = ctk.CTkButton(self, text="Confirm Mapping", command=self.submit_emots)
        self.confirm_emot_button.pack(pady=20)

    def submit_emots(self):
        """Submit the selected emotions mapping."""
        for emot, dropdown in self.emotion_selectors.items():
            selected_value = dropdown.get()
            if selected_value not in self.df.columns:
                messagebox.showerror("Selection Error", "You must select a column for each emotion.")
                return self.handle_emotions()
            
            # Change the header of the emotions to its column name
            self.df.rename(columns={selected_value: emot.lower()}, inplace=True)
            
            
        # Convert the DataFrame to PAQ format
        try:
            self.df = sspy.surveys.rename_paqs(self.df)
            self.df = sspy.surveys.add_iso_coords(self.df)
        except Exception as e:
            messagebox.showerror("Processing Error", f"Error processing emotions:\n{e}")
            return self.handle_emotions()

        self.data_types = "emotions"
        self.filtering()



    def handle_pe(self):
        """Handle the mapping of ISOPleasant and ISOEventful."""
        
        # Save previous selections BEFORE clearing the window
        previous_selections = {}
        if hasattr(self, "PE_selectors"):
            try:
                for pe, dropdown in self.PE_selectors.items():
                    previous_selections[pe] = dropdown.get()
            except Exception:
                # If widgets are destroyed, just start fresh
                previous_selections = {}
        
        self.clear_window()
        self.header(self.data_type_selection, "Map each coordinate to a column:")

        columns = list(self.df.columns)
        self.PE_selectors = {}
        pe_labels = ["Pleasant", "Eventful"]
        default_labels = {
            "Pleasant": "ISO_P",
            "Eventful": "ISO_E"
        }
        # Default labels after renaming to PAQ
        default_labels_after = {
            "Pleasant": "ISOPleasant",
            "Eventful": "ISOEventful"
        }
        
        for pe in pe_labels:
            frame = ctk.CTkFrame(self, fg_color="transparent")
            frame.pack(pady=5)
            label = ctk.CTkLabel(frame, text=f"{pe}:", width=120, anchor="w")
            label.pack(side="left", padx=5)

            dropdown = CustomFiltering(frame, values=columns, default_text="Select a column")
            dropdown.pack(side="left", padx=5)
            if pe in previous_selections:
                dropdown.set(previous_selections[pe])
            elif default_labels[pe] in columns:
                dropdown.set(default_labels[pe])
            elif default_labels_after[pe] in columns:
                dropdown.set(default_labels_after[pe])
            else:
                dropdown.set("Select a column")
            self.PE_selectors[pe] = dropdown
        
        self.confirm_pe_button = ctk.CTkButton(self, text="Filter Data", command=self.submit_pe)
        self.confirm_pe_button.pack(pady=20)

    def submit_pe(self):
        """Submit the selected ISOPleasant and ISOEventful mapping."""
        for pe, dropdown in self.PE_selectors.items():
            selected_value = dropdown.get()
            if selected_value not in self.df.columns:
                messagebox.showerror("Selection Error", "You must select a column for each coordinate.")
                return self.handle_pe()
            
            # Change the header of the coordinates to its column name
            self.df.rename(columns={selected_value: f"ISO{pe}"}, inplace=True)

        self.data_types = "coords"
        self.filtering()

    def filtering(self):
        """Filter the DataFrame based on user-selected columns."""
        self.clear_window()
        back_func = self.handle_pe if self.data_types == "coords" else self.handle_emotions
        self.header(back_func, "Select a column to filter:")


        columns = list(self.df.columns)

        # Delete the ISOPleasant, ISOEventful, or PAQi if they exist
        to_delete = ["ISOPleasant", "ISOEventful"]
        for i in range(1,9):
            to_delete.append(f"PAQ{i}")
        for col in to_delete:
            if col in columns:
                columns.remove(col)

        self.column_selector = CustomFiltering(self, values=columns, default_text="Select a column")
        self.column_selector.pack(pady=10)

        self.filter_button = ctk.CTkButton(self, text="Select Filters", command=lambda: self.select_filter(self.column_selector.get()))
        self.filter_button.pack(pady=10)

        self.finish_button = ctk.CTkButton(self, text="Finish Filtering", command=self.finish_filtering)
        self.finish_button.pack(pady=10)

    def select_filter(self, selected_column):
        """Select the type of filter to apply to the selected column."""
        if selected_column not in self.df.columns:
            messagebox.showerror("Error", "You must select a valid column.")
            return self.filtering()
        
        self.clear_window()
        self.header(self.filtering, f"Filtering column '{selected_column}'")

        # Horizontal frame for checkbox and missing fields - FULL WIDTH
        self.missing_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.missing_frame.pack(pady=10, fill="x")  # fill="x" to make it full width
        self.center_frame = ctk.CTkFrame(self.missing_frame, fg_color="transparent")
        self.center_frame.pack(expand=True)  # expand=True centers the frame internally
        
        # Option to include missing values
        self.include_missing_var = ctk.BooleanVar(value=False)
        self.include_missing_checkbox = ctk.CTkCheckBox(
            self.center_frame,
            text="Include missing values",
            variable=self.include_missing_var,
            command=self.toggle_missing_entry
        )
        self.include_missing_checkbox.pack(side="left", padx=5)

        self.missing_value_label = ctk.CTkLabel(self.center_frame, text="Value used to specify missing entries:")
        self.missing_value_entry = ctk.CTkEntry(self.center_frame, placeholder_text="e.g. 'm'")
        self.missing_value_label.pack(side="left", padx=5)
        self.missing_value_entry.pack(side="left", padx=5)
        self.missing_value_label.pack_forget()
        self.missing_value_entry.pack_forget()

        col_data = self.df[selected_column].dropna()
        unique_values = col_data.unique()
        

        ### FILTERS depending on the type of data
        if len(unique_values) <= self.MAX_UNIQUES:

            unique_values = sorted(unique_values)
            
            # There are few unique values. Select which ones to keep
            self.unique_values_label = ctk.CTkLabel(self, text="Select the values to keep:")
            self.unique_values_label.pack(pady=10)

            # Frame for select all/none buttons
            buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
            buttons_frame.pack(pady=5)
            
            select_all_btn = ctk.CTkButton(
                buttons_frame, 
                text="Select All", 
                command=self.select_all_values,
                width=100,
                height=28
            )
            select_all_btn.pack(side="left", padx=5)
            
            select_none_btn = ctk.CTkButton(
                buttons_frame, 
                text="Select None", 
                command=self.select_none_values,
                width=100,
                height=28
            )
            select_none_btn.pack(side="left", padx=5)

            self.values_chosen = ctk.CTkFrame(self)
            self.values_chosen.pack(pady=10)
            self.vars_chosen = {}
            for value in unique_values:
                var = ctk.BooleanVar(value=False)
                self.vars_chosen[value] = var
                checkbox = ctk.CTkCheckBox(
                    self.values_chosen,
                    text=str(value),
                    variable=var
                )
                checkbox.pack(anchor="w", padx=10, pady=2)

            # Button to apply the filter
            self.apply_filter_button = ctk.CTkButton(self, text="Apply Filter", command=lambda: self.apply_filter(selected_column))
            self.apply_filter_button.pack(pady=20)  


        # Numeric operations
        elif pd.api.types.is_numeric_dtype(self.df[selected_column]):

            ctk.CTkLabel(self, text="Add numeric restriction:").pack(pady=10)
            ops = ["> (or >=)", "< (or <=)", "=", "≠", "between", "outside"]
            self.numeric_frame = []
            self.op_selector = ctk.CTkOptionMenu(
                self,
                values=ops,
                command=lambda op: self.handle_numeric_op(op, selected_column)
            )
            self.op_selector.set("Select an operation")  # Default option
            self.op_selector.pack(pady=5)


        # Dates
        elif pd.api.types.is_datetime64_any_dtype(self.df[selected_column]):
            self.datetime_format = "MM/DD/YYYY HH:MM:SS"
            ctk.CTkLabel(self, text=f"Add date restriction:\n(Dates format: {self.datetime_format})").pack(pady=10)
            ops = ["before", "after", "between", "on", "not on", "outside"]
            self.date_frame = []
            
            self.op_selector = ctk.CTkOptionMenu(
                self,
                values=ops,
                command=lambda op: self.handle_date_op(op, selected_column)
            )
            self.op_selector.set("Select an operation")  # Default option
            self.op_selector.pack(pady=5)

        else:
            messagebox.showinfo("Information", "No filters available for this column type.")
            return self.filtering()
        
    
    def toggle_missing_entry(self):
        """Toggle the visibility of the entry field for missing values."""
        # Hide or show the entry field for missing values
        if self.include_missing_var.get():
            self.missing_value_label.pack(side="left", padx=5)
            self.missing_value_entry.pack(side="left", padx=5)
        else:
            self.missing_value_label.pack_forget()
            self.missing_value_entry.pack_forget()

    def select_all_values(self):
        """Select all checkboxes in the values filter."""
        if hasattr(self, 'vars_chosen'):
            for var in self.vars_chosen.values():
                var.set(True)

    def select_none_values(self):
        """Deselect all checkboxes in the values filter."""
        if hasattr(self, 'vars_chosen'):
            for var in self.vars_chosen.values():
                var.set(False)


        

    def ask_for_numeric_entry(self, label_text, include_checkbox=True):
        """Ask the user for a numeric entry with an optional checkbox to include it."""
        frame = ctk.CTkFrame(self)
        frame.pack(pady=10, fill="x")
        label = ctk.CTkLabel(frame, text=label_text)
        label.pack(side="left", padx=5)
        
        entry = ctk.CTkEntry(frame, placeholder_text="e.g. 0")
        entry.pack(side="left", padx=5)
        
        if include_checkbox:
            var = ctk.BooleanVar(value=True)
            checkbox = ctk.CTkCheckBox(frame, text="Include?", variable=var)
            checkbox.pack(side="left", padx=5)
        else:
            var = None
        
        self.numeric_frame.append(frame)
        return entry, var
            

    def handle_numeric_op(self, op, selected_column):
        """Handle the numeric operation selected by the user."""

        # Remove previous numeric entry if it exists
        for frame in getattr(self, "numeric_frame", []):
            frame.destroy()
        if hasattr(self, 'apply_filter_button'):
            self.apply_filter_button.destroy()


        self.numeric_op = op

        if self.numeric_op == "between":
            self.min_entry, self.include_min_var = self.ask_for_numeric_entry("Min:")
            self.max_entry, self.include_max_var = self.ask_for_numeric_entry("Max:")
        elif self.numeric_op == "< (or <=)":
            self.max_entry, self.include_max_var = self.ask_for_numeric_entry("Max:")
        elif self.numeric_op == "> (or >=)":
            self.min_entry, self.include_min_var = self.ask_for_numeric_entry("Min:")
        elif self.numeric_op == "=":
            self.exact_entry, self.include_numeric_var = self.ask_for_numeric_entry("Exact Value:", include_checkbox=False)
        elif self.numeric_op == "≠":
            self.exact_entry, self.include_numeric_var = self.ask_for_numeric_entry("Value to exclude:", include_checkbox=False)
        elif self.numeric_op == "outside":
            self.min_entry, self.include_min_var = self.ask_for_numeric_entry("From -∞ to:")
            self.max_entry, self.include_max_var = self.ask_for_numeric_entry("To +∞ from:")

        # Button to apply the filter
        self.apply_filter_button = ctk.CTkButton(self, text="Apply Filter", command=lambda: self.apply_filter(selected_column))
        self.apply_filter_button.pack(pady=20)  

    
    def ask_for_date_entry(self, label_text):
        """Ask the user for a date entry with a label."""
        frame = ctk.CTkFrame(self)
        frame.pack(pady=10, fill="x")
        label = ctk.CTkLabel(frame, text=label_text)
        label.pack(side="left", padx=5)
        
        entry = ctk.CTkEntry(frame, placeholder_text="e.g. 01/31/2023 23:59:59")
        entry.pack(side="left", padx=5)
        
        self.date_frame.append(frame)
        return entry

    def handle_date_op(self, op, selected_column):
        """Handle the date operation selected by the user."""
        for frame in getattr(self, "date_frame", []):
            frame.destroy()
        if hasattr(self, 'apply_filter_button'):
            self.apply_filter_button.destroy()
        
        self.date_op = op

        if self.date_op == "before":
            self.date_entry = self.ask_for_date_entry(self, "End Date:")
        elif self.date_op == "after":
            self.date_entry = self.ask_for_date_entry(self, "Start Date:")
        elif self.date_op == "between":
            self.start_date_entry = self.ask_for_date_entry("Start Date:")
            self.end_date_entry = self.ask_for_date_entry("End Date:")
        elif self.date_op == "on":
            self.date_entry = self.ask_for_date_entry("Date to include:")
        elif self.date_op == "not on":
            self.date_entry = self.ask_for_date_entry("Date to exclude:")
        elif self.date_op == "outside":
            self.start_date_entry = self.ask_for_date_entry("From -∞ to:")
            self.end_date_entry = self.ask_for_date_entry("To +∞ from:")
        # Button to apply the filter
        self.apply_filter_button = ctk.CTkButton(self, text="Apply Filter", command=lambda: self.apply_filter(selected_column))
        self.apply_filter_button.pack(pady=20)  

    

    def apply_filter(self, selected_column):
        """Apply the selected filter to the DataFrame."""
        missing_rows = pd.DataFrame()
        
        keep_missing = self.include_missing_var.get()
        if keep_missing:
            missing_value = self.missing_value_entry.get()
            if not missing_value:
                messagebox.showerror("Error", "Please specify a value for missing entries.")
                return self.select_filter(selected_column)

            # Select rows with the missing value in the selected column
            missing_rows = self.df[self.df[selected_column] == missing_value]
            
            # Remove these rows from the DataFrame to filter them later
            self.df = self.df[self.df[selected_column] != missing_value]

        col_data = self.df[selected_column].dropna()
        unique_values = col_data.unique()

        ### APPLY FILTERS depending on the type of data
        if len(unique_values) <= self.MAX_UNIQUES:
            # Apply the filter based on selected values
            selected_values = [value for value, var in self.vars_chosen.items() if var.get()]
            if not selected_values:
                messagebox.showerror("Error", "At least one value must be selected.")
                return self.select_filter(selected_column)
            self.df = self.df[self.df[selected_column].isin(selected_values)]

        elif pd.api.types.is_numeric_dtype(self.df[selected_column]):
            if self.numeric_op == "between":
                min_value = self.min_entry.get()
                max_value = self.max_entry.get()

                if not min_value or not max_value:
                    messagebox.showerror("Error", "You must enter both min and max values.")
                    return self.select_filter(selected_column)
                
                try:
                    min_value = float(min_value)
                    max_value = float(max_value)
                except:
                    messagebox.showerror("Error", "Min and max values must be numeric.")
                    return self.select_filter(selected_column)

                if min_value >= max_value:
                    messagebox.showerror("Error", "Min value must be less than max value.")
                    return self.select_filter(selected_column)
                
                min_included = self.include_min_var.get()
                max_included = self.include_max_var.get()

                # Apply the filter
                if min_included and max_included:
                    self.df = self.df[(self.df[selected_column] >= min_value) & (self.df[selected_column] <= max_value)]
                elif min_included and not max_included:
                    self.df = self.df[(self.df[selected_column] >= min_value) & (self.df[selected_column] < max_value)]
                elif not min_included and max_included:
                    self.df = self.df[(self.df[selected_column] > min_value) & (self.df[selected_column] <= max_value)]
                else:
                    self.df = self.df[(self.df[selected_column] > min_value) & (self.df[selected_column] < max_value)]
            
            elif self.numeric_op == "< (or <=)":
                max_value = self.max_entry.get()
                if not max_value:
                    messagebox.showerror("Error", "You must enter a max value.")
                    return self.select_filter(selected_column)
                
                try:
                    max_value = float(max_value)
                except:
                    messagebox.showerror("Error", "Max value must be numeric.")
                    return self.select_filter(selected_column)

                max_included = self.include_max_var.get()

                # Apply the filter
                if max_included:
                    self.df = self.df[self.df[selected_column] <= max_value]
                else:
                    self.df = self.df[self.df[selected_column] < max_value]

            elif self.numeric_op == "> (or >=)":
                min_value = self.min_entry.get()
                if not min_value:
                    messagebox.showerror("Error", "You must enter a min value.")
                    return self.select_filter(selected_column)
                
                try:
                    min_value = float(min_value)
                except:
                    messagebox.showerror("Error", "Min value must be numeric.")
                    return self.select_filter(selected_column)

                min_included = self.include_min_var.get()

                # Apply the filter
                if min_included:
                    self.df = self.df[self.df[selected_column] >= min_value]
                else:
                    self.df = self.df[self.df[selected_column] > min_value]
            
            elif self.numeric_op == "=":
                exact_value = self.exact_entry.get()
                if not exact_value:
                    messagebox.showerror("Error", "You must enter an exact value.")
                    return self.select_filter(selected_column)
                
                try:
                    exact_value = float(exact_value)
                except:
                    messagebox.showerror("Error", "Exact value must be numeric.")
                    return self.select_filter(selected_column)
            
                self.df = self.df[self.df[selected_column] == exact_value]
                
            elif self.numeric_op == "≠":
                exact_value = self.exact_entry.get()
                if not exact_value:
                    messagebox.showerror("Error", "You must enter a value to exclude.")
                    return self.select_filter(selected_column)
                
                try:
                    exact_value = float(exact_value)
                except:
                    messagebox.showerror("Error", "Value to exclude must be numeric.")
                    return self.select_filter(selected_column)
                
                self.df = self.df[self.df[selected_column] != exact_value]

            elif self.numeric_op == "outside":
                min_value = self.min_entry.get()
                max_value = self.max_entry.get()

                if not min_value or not max_value:
                    messagebox.showerror("Error", "You must enter both min and max values.")
                    return self.select_filter(selected_column)
                
                try:
                    min_value = float(min_value)
                    max_value = float(max_value)
                except:
                    messagebox.showerror("Error", "Min and max values must be numeric.")
                    return self.select_filter(selected_column)

                if min_value >= max_value:
                    messagebox.showerror("Error", "Min value must be less than max value.")
                    return self.select_filter(selected_column)
                
                min_included = self.include_min_var.get()
                max_included = self.include_max_var.get()

                # Apply the filter
                if min_included and max_included:
                    self.df = self.df[(self.df[selected_column] <= min_value) | (self.df[selected_column] >= max_value)]
                elif min_included and not max_included:
                    self.df = self.df[(self.df[selected_column] <= min_value) | (self.df[selected_column] > max_value)]
                elif not min_included and max_included:
                    self.df = self.df[(self.df[selected_column] < min_value) | (self.df[selected_column] >= max_value)]
                else:
                    self.df = self.df[(self.df[selected_column] < min_value) | (self.df[selected_column] > max_value)]

        elif pd.api.types.is_datetime64_any_dtype(self.df[selected_column]):
            format_reading = "%m/%d/%Y %H:%M:%S"
            if self.date_op == "before":
                date_str = self.date_entry.get()
                if not date_str:
                    messagebox.showerror("Error", "You must enter a date.")
                    return self.select_filter(selected_column)
                
                try:
                    date_value = pd.to_datetime(date_str, format=format_reading)
                except ValueError:
                    messagebox.showerror("Error", f"Invalid date format. Use {self.datetime_format}.\nExample: 01/31/2023 15:00:00.")
                    return self.select_filter(selected_column)

                self.df = self.df[self.df[selected_column] <= date_value]
            elif self.date_op == "after":
                date_str = self.date_entry.get()
                if not date_str:
                    messagebox.showerror("Error", "You must enter a date.")
                    return self.select_filter(selected_column)
                
                try:
                    date_value = pd.to_datetime(date_str, format=format_reading)
                except ValueError:
                    messagebox.showerror("Error", f"Invalid date format. Use {self.datetime_format}.\nExample: 01/31/2023 15:00:00.")
                    return self.select_filter(selected_column)

                self.df = self.df[self.df[selected_column] >= date_value]
            elif self.date_op == "between":
                start_date_str = self.start_date_entry.get()
                end_date_str = self.end_date_entry.get()

                if not start_date_str or not end_date_str:
                    messagebox.showerror("Error", "You must enter both start and end dates.")
                    return self.select_filter(selected_column)
                
                try:
                    start_date_value = pd.to_datetime(start_date_str, format=format_reading)
                    end_date_value = pd.to_datetime(end_date_str, format=format_reading)
                except ValueError:
                    messagebox.showerror("Error", f"Invalid date format. Use {self.datetime_format}.\nExample: 01/31/2023 15:00:00.")
                    return self.select_filter(selected_column)

                if start_date_value >= end_date_value:
                    messagebox.showerror("Error", "Start date must be before end date.")
                    return self.select_filter(selected_column)

                self.df = self.df[(self.df[selected_column] >= start_date_value) & (self.df[selected_column] <= end_date_value)]
            elif self.date_op == "on":
                date_str = self.date_entry.get()
                if not date_str:
                    messagebox.showerror("Error", "You must enter a date.")
                    return self.select_filter(selected_column)
                
                try:
                    date_value = pd.to_datetime(date_str, format=format_reading)
                except ValueError:
                    messagebox.showerror("Error", f"Invalid date format. Use {self.datetime_format}.\nExample: 01/31/2023 15:00:00.")
                    return self.select_filter(selected_column)

                self.df = self.df[self.df[selected_column] == date_value]
            elif self.date_op == "not on":
                date_str = self.date_entry.get()
                if not date_str:
                    messagebox.showerror("Error", "You must enter a date.")
                    return self.select_filter(selected_column)
                
                try:
                    date_value = pd.to_datetime(date_str, format=format_reading)
                except ValueError:
                    messagebox.showerror("Error", f"Invalid date format. Use {self.datetime_format}.\nExample: 01/31/2023 15:00:00.")
                    return self.select_filter(selected_column)

                self.df = self.df[self.df[selected_column] != date_value]
            elif self.date_op == "outside":
                start_date_str = self.start_date_entry.get()
                end_date_str = self.end_date_entry.get()

                if not start_date_str or not end_date_str:
                    messagebox.showerror("Error", "You must enter both start and end dates.")
                    return self.select_filter(selected_column)
                
                try:
                    start_date_value = pd.to_datetime(start_date_str, format=format_reading)
                    end_date_value = pd.to_datetime(end_date_str, format=format_reading)
                except ValueError:
                    messagebox.showerror("Error", f"Invalid date format. Use {self.datetime_format}.\nExample: 01/31/2023 15:00:00.")
                    return self.select_filter(selected_column)

                if start_date_value >= end_date_value:
                    messagebox.showerror("Error", "Start date must be before end date.")
                    return self.select_filter(selected_column)

                self.df = self.df[(self.df[selected_column] < start_date_value) | (self.df[selected_column] > end_date_value)]



        if keep_missing and not missing_rows.empty:
            # If we are keeping the missing values, add them back to the filtered DataFrame
            self.df = pd.concat([self.df, missing_rows], ignore_index=True)

                    
        return self.filtering()

    def finish_filtering(self):
        """Finish the filtering process and display the filtered DataFrame."""
        self.clear_window()
        self.header(self.filtering, "Filtering Complete!")
        
        save_button = ctk.CTkButton(self, text="Download Filtered Data", command=lambda: self.save_df_to_file(self.df, default_name=self.file_name + "_filtered"))
        save_button.pack(pady=(10, 30))

        # CustomFiltering widget to select which columns to differentiate by
        values = list(self.df.columns)
        to_delete = ["ISOPleasant", "ISOEventful"]
        for i in range(1,9):
            to_delete.append(f"PAQ{i}")
        for col in to_delete:
            if col in values:
                values.remove(col)

        # Button to obtain the IQR of each column
        if self.data_types == "emotions":
            # Frame to contain both buttons in the same row
            statistics_frame = ctk.CTkFrame(self, fg_color="transparent")
            statistics_frame.pack(pady=(10,30))
            
            self.iqr_button = ctk.CTkButton(statistics_frame, text="IQR", command=lambda: self.show_iqr())
            self.iqr_button.pack(side="left", padx=5)
            
            self.median_button = ctk.CTkButton(statistics_frame, text="Median", command=lambda: self.show_median())
            self.median_button.pack(side="left", padx=5)
        
        # Column to differentiate by
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=10, fill="x")  # fill="x" to make it full width
        center_frame = ctk.CTkFrame(frame, fg_color="transparent")
        center_frame.pack(expand=True)  # expand=True centers the frame internally
        self.differentiation_selector = CustomFiltering(center_frame, values=values, default_text="None")        
        self.differentiation_selector_label = ctk.CTkLabel(center_frame, text="Select the column to differentiate by:")
        self.differentiation_selector_label.pack(side="left", padx=5)
        self.differentiation_selector.pack(side="left", padx=5)

        # Entry to select if drawing the median or not
        if self.data_types == "emotions":
            self.draw_median_var = ctk.BooleanVar(value=True)
            draw_median_checkbox = ctk.CTkCheckBox(
                self,
                text="Draw median",
                variable=self.draw_median_var
            )
            draw_median_checkbox.pack(pady=10)
        
    

        # Entry for the title of the graph
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=(10,40), fill="x")  # fill="x" to make it full width
        center_frame = ctk.CTkFrame(frame, fg_color="transparent")
        center_frame.pack(expand=True)  # expand=True centers the frame internally
        self.title_label = ctk.CTkLabel(center_frame, text="Title for the graph:")
        self.title_entry = ctk.CTkEntry(center_frame, placeholder_text="e.g. 'Filtered Data Visualization'", width=100)
        self.title_label.pack(side="left", padx=5)
        self.title_entry.pack(side="left", padx=5)

        
        


        # Dropdown to select the type of graph
        self.graph_type_label = ctk.CTkLabel(self, text="Select the type of graph:")
        self.graph_type_label.pack(pady=10)
        values = ["Scatter", "Density", "Density only P50", "Density only P50 (lines)", "Density with Distribution", "Density only P50 with Distribution", "Density only P50 (lines) with Distribution"]

        if self.data_types == "emotions":
            values.append("Boxplot")
            values.append("Radar Plot")
            values.append("Empty")

        self.graph_type_selector = ctk.CTkOptionMenu(self, values=values, command=self.draw_graph)
        self.graph_type_selector.set("Graph Type")  # Default option
        self.graph_type_selector.pack(pady=5)



    def draw_graph(self, graph_type):
        """Draw the selected type of graph based on the filtered DataFrame."""
        if not hasattr(self, 'df') or self.df.empty:
            messagebox.showerror("Error", "No data to visualize. Please filter the data first.")
            exit(1)
        
        title_label = self.title_entry.get() if hasattr(self, 'title_entry') else "Filtered Data Visualization"
        differentiation_column = self.differentiation_selector.get() if hasattr(self, 'differentiation_selector') else None
        if differentiation_column not in self.df.columns:
            differentiation_column = None
        
        # Create a copy of the DataFrame for plotting to avoid modifying the original
        plot_df = self.df.copy()
        
        # If we have a differentiation column, sort its values to ensure ordered legend
        if differentiation_column is not None:
            try:
                # Get unique values and sort them
                unique_values = plot_df[differentiation_column].dropna().unique()
                sorted_values = sorted(unique_values)
                
                # Create a categorical column with ordered categories for proper legend ordering
                plot_df[differentiation_column] = pd.Categorical(
                    plot_df[differentiation_column], 
                    categories=sorted_values, 
                    ordered=True
                )
            except Exception as e:
                # If sorting fails, continue without ordering (fallback)
                print(f"Warning: Could not sort legend values: {e}")
        
        try:
            common_args = {
                "hue": differentiation_column,
                "title": title_label,
                "diagonal_lines": True,
            }
            if differentiation_column is None:
                common_args["color"] = "steelblue"

            if graph_type == "Scatter":            
                sspy.scatter(plot_df, **common_args)

            elif graph_type == "Density":
                sspy.density(plot_df, **common_args)

            elif graph_type == "Density only P50":
                sspy.density(
                    plot_df,
                    **common_args,
                    density_type="simple",  # Use simple density type
                    incl_scatter=True,
                )

            elif graph_type == "Density only P50 (lines)":
                sspy.density(
                    plot_df, 
                    **common_args,
                    fill=False,
                    incl_scatter=True,
                    density_type="simple",  # Use simple density type
                )

            elif graph_type == "Density with Distribution":
                sspy.jointplot(
                    plot_df, 
                    **common_args
                )
            
            elif graph_type == "Density only P50 with Distribution":
                sspy.jointplot(
                    plot_df, 
                    **common_args,
                    density_type="simple",  # Use simple density type
                    incl_scatter=True,
                )
            
            elif graph_type == "Density only P50 (lines) with Distribution":
                sspy.jointplot(
                    plot_df, 
                    **common_args,
                    fill=False,
                    incl_scatter=True,
                    density_type="simple",  # Use simple density type
                )

            elif graph_type == "Boxplot":
                PAQs = plot_df
                # Obtain only the PAQ columns and the differentiation column
                PAQs = sspy.surveys.return_paqs(PAQs)
                if differentiation_column is not None:
                    PAQs = PAQs.join(plot_df[differentiation_column])
                # Check if there are no PAQ columns
                if PAQs.empty:
                    messagebox.showerror("Error", "No PAQ columns found in the DataFrame.")
                    return
                # Revert from emotions to PAQ
                PAQs = self.revert_from_PAQ(PAQs)

                # Capitalize the columns
                PAQs.columns = [emotion.capitalize() for emotion in PAQs.columns]
                differentiation_column = differentiation_column.capitalize() if differentiation_column else None                
            
                PAQs_melted = PAQs.melt(id_vars=differentiation_column, var_name='Emotion', value_name='Value')

                plt.figure(figsize=(10, 6))
                sns.boxplot(
                    x='Emotion',
                    y='Value',
                    data=PAQs_melted,
                    hue=differentiation_column,
                    gap=0.1,
                    medianprops=dict(color='black', linewidth=2.5)
                )
                plt.xticks(rotation=45)
                plt.title(title_label)
                plt.tight_layout()
            
            elif graph_type == "Radar Plot" and self.data_types == "emotions":
                # Check less than 3 rows
                if len(plot_df) > self.MAX_RADAR_PLOT_ROWS:
                    messagebox.showerror("Error", f"Radar Plot requires less than {self.MAX_RADAR_PLOT_ROWS} rows of data.")
                else:
                    # Revert from PAQ to emotions
                    plot_df = self.revert_from_PAQ(plot_df)
                    sspy.paq_radar_plot(plot_df)

            elif self.data_types == "emotions" \
                and hasattr(self, 'draw_median_var') \
                and self.draw_median_var.get() \
                and graph_type in ["Empty"]:

                # Empty DF - para solo mostrar las medianas sin puntos
                empty_df = pd.DataFrame(columns=plot_df.columns)
                
                # Crear argumentos sin hue para evitar la advertencia
                empty_args = {
                    "title": title_label,
                    "diagonal_lines": True,
                    "color": "steelblue"  # Color fijo para evitar problemas con hue vacío
                }
                sspy.scatter(empty_df, **empty_args)

                # Legend manual con una entrada para cada valor en la columna de diferenciación
                if differentiation_column is not None:
                    unique_values = plot_df[differentiation_column].dropna().unique()
                    # Crear handles de leyenda manualmente usando colors que coincidan con draw_median
                    palette = sns.color_palette(n_colors=len(unique_values))
                    color_mapping = dict(zip(sorted(unique_values), palette))
                    
                    for value, color in color_mapping.items():
                        plt.plot([], [], 'o', color=color, label=str(value), markersize=8)
                    plt.legend(title=differentiation_column)


            else:
                messagebox.showerror("Error", "Unsupported graph type selected.")

            
            if self.data_types == "emotions" \
                and hasattr(self, 'draw_median_var') \
                and self.draw_median_var.get() \
                and graph_type not in ["Radar Plot", "Boxplot"]:

                self.draw_median(plot_df, differentiation_column)

            
            plt.show()
            
        except Exception as e:
            print(f"Error drawing graph: {e}")
            messagebox.showerror("Error", f"Could not draw graph:\n{e}")

    def revert_from_PAQ(self, data):
        """Revert the DataFrame from PAQ columns to emotions."""
        class PAQ(Enum):
            """Enumeration of Perceptual Attribute Questions (PAQ) names and IDs."""

            PLEASANT = ("pleasant", "PAQ1")
            VIBRANT = ("vibrant", "PAQ2")
            EVENTFUL = ("eventful", "PAQ3")
            CHAOTIC = ("chaotic", "PAQ4")
            ANNOYING = ("annoying", "PAQ5")
            MONOTONOUS = ("monotonous", "PAQ6")
            UNEVENTFUL = ("uneventful", "PAQ7")
            CALM = ("calm", "PAQ8")

            def __init__(self, label: str, id: str):
                self.label = label
                self.id = id

        PAQ_DICT_REVERT = {paq.id: paq.label for paq in PAQ}
        
        
        # Check if it's a DataFrame or Series and handle accordingly
        if isinstance(data, pd.DataFrame):
            data.rename(columns=PAQ_DICT_REVERT, inplace=True)
        elif isinstance(data, pd.Series):
            data.rename(index=PAQ_DICT_REVERT, inplace=True)
        
        return data
        
    def show_iqr(self):
        """Show the IQR of each column PAQ and:
            - Show it in a messagebox
            - Save it to a file
        """

        if not hasattr(self, 'df') or self.df.empty:
            messagebox.showerror("Error", "No data to calculate IQR. Please filter the data first.")
            return
        
        # Obtain only the PAQ columns
        PAQs = sspy.surveys.return_paqs(self.df)
        if PAQs.empty:
            messagebox.showinfo("Information", "No PAQ columns found in the DataFrame.")
            return
        
        Q3 = PAQs.quantile(0.75)
        Q1 = PAQs.quantile(0.25)
        IQR = Q3 - Q1

        IQR = self.revert_from_PAQ(IQR)

        # Capitalize the indexes
        IQR.index = [emotion.capitalize() for emotion in IQR.index]
        
        # Popup        
        popup = ctk.CTkToplevel()
        popup.title("IRQ Values")
        popup.geometry("450x450")

        frame = ctk.CTkFrame(popup, corner_radius=15)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        title = ctk.CTkLabel(frame, text="IRQ Values for each Emotion", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(15, 5))

        # Create an inner frame to center the table and keep it compact
        inner_table_frame = ctk.CTkFrame(frame, fg_color="transparent")
        inner_table_frame.pack(pady=10, expand=True)

        # Header
        ctk.CTkLabel(inner_table_frame, text="Emotion", font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=0, padx=5, pady=4, sticky="w")
        ctk.CTkLabel(inner_table_frame, text="IQR", font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=1, padx=5, pady=4, sticky="e")

        # Rows
        for idx, (emotion, value) in enumerate(IQR.items(), start=1):
            emotion_label = ctk.CTkLabel(inner_table_frame, text=emotion.capitalize(), font=ctk.CTkFont(size=13), anchor="w")
            value_label = ctk.CTkLabel(inner_table_frame, text=f"{value:.2f}", font=ctk.CTkFont(size=13), anchor="e")
            emotion_label.grid(row=idx, column=0, padx=10, pady=2, sticky="w")
            value_label.grid(row=idx, column=1, padx=10, pady=2, sticky="e")

        # Buttons frame to place them in the same row
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.pack(pady=(10, 15))
        
        ctk.CTkButton(buttons_frame, text="Exit", command=popup.destroy).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Save IQR Values", command=lambda: self.save_df_to_file(pd.DataFrame(IQR).T, default_name=self.file_name + "_filtered_IQR")).pack(side="left", padx=5)

    def save_df_to_file(self, df, default_name=None):
        """Save the DataFrame to a file."""
        filetypes = [
            ("Excel files", "*.xls *.xlsx"),
            ("CSV/TSF files", "*.csv *.tsv"),
            ("OpenDocument Spreadsheet", "*.ods"),
        ]
        filepath = filedialog.asksaveasfilename(
            title="Save Data",
            filetypes=filetypes,
            defaultextension=".xlsx",  # Default extension
            initialfile=default_name + ".xlsx" if default_name else None,
        )
        if not filepath:
            messagebox.showwarning("No File Selected", "Please select a file to save the Data.")
            return self.save_df_to_file(df, default_name=default_name)
        
        if isinstance(df, pd.Series):
            # Convert Series to DataFrame with index as a column
            df = df.reset_index()
            df.columns = ['Index', 'Value']  # Rename columns appropriately

        try:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == ".csv":
                df.to_csv(filepath, index=False)
            elif ext in [".xls", ".xlsx"]:
                df.to_excel(filepath, index=False)
            elif ext == ".tsv":
                df.to_csv(filepath, sep="\t", index=False)
            elif ext == ".ods":
                df.to_excel(filepath, index=False, engine='odf')
            else:
                messagebox.showerror("Error", "Unsupported file format selected.")
                return self.save_df_to_file(df, default_name=default_name)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")


    def show_median(self):
        """Calculate and show the median of the DF."""
        if not hasattr(self, 'df') or self.df.empty:
            messagebox.showerror("Error", "No data to calculate median. Please filter the data first.")
            return
        
        # Obtain only the PAQ columns
        PAQs = sspy.surveys.return_paqs(self.df)
        if PAQs.empty:
            messagebox.showinfo("Information", "No PAQ columns found in the DataFrame.")
            return
        
        median = PAQs.median()

        # Convert median to DataFrame for consistency
        median = pd.DataFrame(median).T
        median = sspy.surveys.add_iso_coords(median)



        # Popup        
        popup = ctk.CTkToplevel()
        popup.title("Median Values")
        popup.geometry("400x400")

        frame = ctk.CTkFrame(popup, corner_radius=15)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        title = ctk.CTkLabel(frame, text="Median Coordinates", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(15, 5))

        # Create an inner frame to center the table and keep it compact
        inner_table_frame = ctk.CTkFrame(frame, fg_color="transparent")
        inner_table_frame.pack(pady=10, expand=True)

        # Only show the ISO coordinates
        median_iso = median[["ISOEventful", "ISOPleasant"]]
        # Header
        ctk.CTkLabel(inner_table_frame, text="ISOEventful", font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=0, padx=5, pady=4, sticky="w")
        ctk.CTkLabel(inner_table_frame, text="ISOPleasant", font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=1, padx=5, pady=4, sticky="e")
        # Rows
        for idx, (eventful, pleasant) in enumerate(zip(median_iso["ISOEventful"], median_iso["ISOPleasant"]), start=1):
            eventful_label = ctk.CTkLabel(inner_table_frame, text=f"{eventful:.5f}", font=ctk.CTkFont(size=13), anchor="w")
            pleasant_label = ctk.CTkLabel(inner_table_frame, text=f"{pleasant:.5f}", font=ctk.CTkFont(size=13), anchor="e")
            eventful_label.grid(row=idx, column=0, padx=10, pady=2, sticky="w")
            pleasant_label.grid(row=idx, column=1, padx=10, pady=2, sticky="e")

        # Buttons frame to place them in the same row
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.pack(pady=(10, 15))

        median = self.revert_from_PAQ(median)
        median.columns = [col.capitalize() for col in median.columns]  # Capitalize the column names
        
        ctk.CTkButton(buttons_frame, text="Exit", command=popup.destroy).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Save Median Values", command=lambda: self.save_df_to_file(median, default_name=self.file_name + "_filtered_median")).pack(side="left", padx=5)


    def draw_median(self, plot_df, differentiation_column=None):
        """Calculate and show the median of the DF."""
        if not hasattr(self, 'df') or self.df.empty:
            messagebox.showerror("Error", "No data to calculate median. Please filter the data first.")
            return
        
        # Obtain the colors
        if differentiation_column is not None:
            unique_hue_values = plot_df[differentiation_column].dropna().unique()
            n_colors = len(unique_hue_values)
        else:
            unique_hue_values = ["Default"]
            n_colors = 1

        palette = sns.color_palette(n_colors=n_colors)
            
        # Mapping: unique hue values to colors
        color_mapping = dict(zip(sorted(unique_hue_values), palette))
        
        # Represent the median of each hue value
        for value, color in color_mapping.items():

            if differentiation_column is not None:
                # Filter the DataFrame for the current hue value
                hue_df = plot_df[plot_df[differentiation_column] == value]
            else:
                hue_df = plot_df
            
            PAQs = sspy.surveys.return_paqs(hue_df)
            median = PAQs.median()
            median = pd.DataFrame(median).T
            median = sspy.surveys.add_iso_coords(median)
            x = median["ISOEventful"].values[0]
            y = median["ISOPleasant"].values[0]

            # Add the median point to the plot
            # Check if we're in a jointplot context (has multiple subplots)
            fig = plt.gcf()
            axes = fig.get_axes()
            
            main_ax = axes[0]
            main_ax.scatter(x, y, color=color, s=70, edgecolor='black', linewidth=2, zorder=10, alpha=0.9)        
        
        
        



        
    
        
        


if __name__ == "__main__":
    app = None
    try:
        app = GUI()
        app.mainloop()
    except Exception as e:
        ERROR_MSG = f"ERROR DETECTED:\n\n{str(e)}\n\nTechnical details:\n{traceback.format_exc()}"
        try:
            root = ctk.CTk()  # Create a hidden root window for tkinter
            root.withdraw()  # Hide the main window
            messagebox.showerror("ERROR DETECTED - Fatal Error", ERROR_MSG)
            root.destroy()
        except Exception as inner_e:
            # If tkinter is not available, print the error to the console
            print("Could not show error message with tkinter. Printing to console instead.")
            print(ERROR_MSG)
    finally:
        # Cleanup on exit
        try:
            plt.close('all')
            if app:
                app.quit()
        except Exception:
            pass
        import sys
        sys.exit(0)
