"""Graphical User Interface (GUI) module for SoundGraphy.

This module provides the main desktop interface for loading, filtering,
and visualizing acoustic and perceptual soundscape data in accordance with
the ISO 12913-3 standard.
"""

import os
import sys
import traceback
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import soundscapy as sspy
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image, ImageTk

from soundgraphy.models import PAQ, PAQ_DICT_REVERT, PAQ_NAME_TO_ID, ssm_model
from soundgraphy.widgets import CustomFiltering

FONT = ("Arial", 20)
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class BasicWindow(ctk.CTk):
    """Basic window class for the SoundScape application."""
    def __init__(self):
        """Initialize the basic window configuration, icon, dimensions, and error handlers."""
        super().__init__(className="SoundGraphy")
        self.title("SoundGraphy GUI")
        self.minsize(700, 500)

        try:
            logo_path = os.path.join(BASE_DIR, "logo", "logo.png")
            if os.path.exists(logo_path):
                logo_img = ImageTk.PhotoImage(Image.open(logo_path))
                self.iconphoto(False, logo_img)
                self._logo_img = logo_img
            else:
                print(f"Warning: Logo file not found at {logo_path}. Window icon not set.")
        except Exception as e:
            print(f"Warning: Could not set window icon: {e}")

        width = int(self.winfo_screenwidth()/2)
        hight = int(self.winfo_screenheight()/2)
        self.geometry(f"{width}x{hight}")

        # Override Tkinter's error reporting to catch all callback exceptions
        self.report_callback_exception = self.handle_tkinter_error
        
        # Bind the window close event to cleanup
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    
    def handle_tkinter_error(self, exc_type, exc_value, exc_traceback):
        """Handle all Tkinter callback exceptions (button clicks, etc.).

        Overrides Tkinter's default error reporting to display a popup and print
        the traceback to the standard output.

        Args:
            exc_type (type): The exception class.
            exc_value (BaseException): The exception instance.
            exc_traceback (traceback): The traceback object.
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
            plt.close('all')                
        except Exception as e:
            print(f"Warning: Error during matplotlib cleanup: {e}")
        
        try:
            self.destroy()
        except Exception as e:
            print(f"Warning: Error during window destruction: {e}")
            
        sys.exit(0)

    def clear_window(self):
        """Clear the current window by destroying all child widgets."""
        for widget in self.winfo_children():
            widget.destroy()



class GUI(BasicWindow):
    """Main GUI class managing the soundscape processing workflow and visualization."""
    
    # Class constant for maximum unique values threshold
    MAX_UNIQUES = 15

    # Class constant for maximum rows to use Radar plot
    MAX_RADAR_PLOT_ROWS = 7
    
    def __init__(self):
        """Initialize the main graphical interface and default home view."""
        super().__init__()

        self.df = None  # DataFrame to hold the loaded data   

        try:
            logo_path = os.path.join(BASE_DIR, "logo", "logo.png")
            if os.path.exists(logo_path):
                pil_img = Image.open(logo_path)
                self.logo_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(150, 150))
                self.logo_label = ctk.CTkLabel(self, image=self.logo_ctk, text="")
                self.logo_label.pack(pady=(20, 0))
            else:
                print(f"Warning: Logo file not found at {logo_path}. Logo not displayed.")
        except Exception as e:
            print(f"Warning loading UI logo: {e}")          

        self.label = ctk.CTkLabel(self, text="Welcome to SoundGraphy GUI!\nCreate ISO 12913-3 compliant graphics", font=FONT)
        self.label.pack(pady=(10, 20))

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

        # Label at footer
        footer_label = ctk.CTkLabel(self, text="Soundscape, Health & Heritage (SHH) Group\nUniversity of Granada (UGR)", font=ctk.CTkFont(family="Arial", size=12, weight="bold"))
        author_label = ctk.CTkLabel(self, text="Developed by Arturo Olivares Martos", font=ctk.CTkFont(family="Arial", size=12, weight="bold", slant="italic"))
        author_label.pack(side="bottom", pady=(0,10))
        footer_label.pack(side="bottom", pady=(10,0))

    def change_mode(self, mode):
        """Change the appearance mode of the application.

        Args:
            mode (str): Theme mode name ('System', 'Light', or 'Dark').
        """
        ctk.set_appearance_mode(mode)

    def header(self, back_func, title):
        """Create a header with a back navigation button and title.

        Args:
            back_func (callable): Function to call when clicking the back button.
            title (str): Header title text to display.
        """
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=10)

        back_button = ctk.CTkButton(header_frame, text="Back", command=back_func, width=60)
        back_button.pack(side="left", padx=10)

        title_label = ctk.CTkLabel(self, text=title, font=FONT)
        title_label.place(relx=0.5, rely=0.05, anchor="center")

    def open_select_doc(self):
        """Open a file dialog to select and load a spreadsheet dataset (Excel, CSV, TSV, ODS)."""
        filetypes = [
            ("Excel files", "*.xls *.xlsx"),
            ("CSV/TSV files", "*.csv *.tsv"),
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
        """Display the screen to select the format/type of data to process."""
        self.clear_window()

        self.header(self.open_select_doc, "What type of data do you have?")

        self.option_emot = ctk.CTkButton(self, text="I have the values of the 8 emotions", command=self.handle_emotions)
        self.option_emot.pack(pady=10)

        self.option_pe = ctk.CTkButton(self, text="I only have the values for the ISOPleasant and ISOEventful", command=self.handle_pe)
        self.option_pe.pack(pady=10)


    def handle_emotions(self):
        """Render the column mapping screen for the 8 perceptual emotion variables."""

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
        default_labels_q2 = {
            "Annoying": "Q2.6",
            "Calm": "Q2.5",
            "Chaotic": "Q2.2",
            "Eventful": "Q2.7",
            "Monotonous": "Q2.8",
            "Pleasant": "Q2.1",
            "Uneventful": "Q2.4",
            "Vibrant": "Q2.3"
        }

        for emot in PAQ_NAME_TO_ID.keys():
            frame = ctk.CTkFrame(self, fg_color="transparent")
            frame.pack(pady=5)
            label = ctk.CTkLabel(frame, text=f"{emot}:", width=120, anchor="w")
            label.pack(side="left", padx=5)



            dropdown = CustomFiltering(frame, values=columns, default_text="Select a column")
            dropdown.pack(side="left", padx=5)
            if emot in previous_selections:
                dropdown.set(previous_selections[emot])
            elif default_labels_q2.get(emot) in columns:
                dropdown.set(default_labels_q2.get(emot))
            elif PAQ_NAME_TO_ID.get(emot) in columns:
                dropdown.set(PAQ_NAME_TO_ID.get(emot))
            else:
                dropdown.set("Select a column")

            self.emotion_selectors[emot] = dropdown
            

        self.confirm_emot_button = ctk.CTkButton(self, text="Confirm Mapping", command=self.submit_emots)
        self.confirm_emot_button.pack(pady=20)

    def submit_emots(self):
        """Validate emotion mapping, convert DataFrame to PAQ format, and calculate ISO coordinates."""
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
            self.df = sspy.surveys.add_iso_coords(self.df, overwrite=True)
        except Exception as e:
            messagebox.showerror("Processing Error", f"Error processing emotions:\n{e}")
            return self.handle_emotions()

        self.data_types = "emotions"
        self.filtering()



    def handle_pe(self):
        """Render the column mapping screen for ISOPleasant and ISOEventful coordinates."""
        
        previous_selections = {}
        if hasattr(self, "PE_selectors"):
            try:
                for pe, dropdown in self.PE_selectors.items():
                    previous_selections[pe] = dropdown.get()
            except Exception:
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
        """Validate and apply ISOPleasant and ISOEventful coordinate column mapping."""
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
        """Display the main column selection interface for applying data filters."""
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
        """Generate filtering widgets dynamically based on the selected column's data type.

        Args:
            selected_column (str): Name of the column to filter.
        """
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
        """Toggle the visibility of the text entry for missing value definitions."""
        if self.include_missing_var.get():
            self.missing_value_label.pack(side="left", padx=5)
            self.missing_value_entry.pack(side="left", padx=5)
        else:
            self.missing_value_label.pack_forget()
            self.missing_value_entry.pack_forget()

    def select_all_values(self):
        """Select all categorical checkboxes in the filter panel."""
        if hasattr(self, 'vars_chosen'):
            for var in self.vars_chosen.values():
                var.set(True)

    def select_none_values(self):
        """Deselect all categorical checkboxes in the filter panel."""
        if hasattr(self, 'vars_chosen'):
            for var in self.vars_chosen.values():
                var.set(False)


        

    def ask_for_numeric_entry(self, label_text, include_checkbox=True):
        """Create a numeric input field with an optional inclusion checkbox.

        Args:
            label_text (str): Descriptive label text.
            include_checkbox (bool, optional): Whether to display an inclusive boundary checkbox. Defaults to True.

        Returns:
            tuple[ctk.CTkEntry, ctk.BooleanVar | None]: The entry widget and its BooleanVar state.
        """
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
        """Render input widgets according to the chosen numeric operator.

        Args:
            op (str): Selected numeric operator (e.g., 'between', '< (or <=)').
            selected_column (str): Target column for the filter.
        """

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
        """Create a text input field for date restrictions.

        Args:
            label_text (str): Descriptive label for the date input.

        Returns:
            ctk.CTkEntry: Configured text entry widget.
        """
        frame = ctk.CTkFrame(self)
        frame.pack(pady=10, fill="x")
        label = ctk.CTkLabel(frame, text=label_text)
        label.pack(side="left", padx=5)
        
        entry = ctk.CTkEntry(frame, placeholder_text="e.g. 01/31/2023 23:59:59")
        entry.pack(side="left", padx=5)
        
        self.date_frame.append(frame)
        return entry

    def handle_date_op(self, op, selected_column):
        """Render date input widgets according to the chosen date operator.

        Args:
            op (str): Selected date comparison operator (e.g., 'before', 'between').
            selected_column (str): Target column for the filter.
        """
        for frame in getattr(self, "date_frame", []):
            frame.destroy()
        if hasattr(self, 'apply_filter_button'):
            self.apply_filter_button.destroy()
        
        self.date_op = op

        if self.date_op == "before":
            self.date_entry = self.ask_for_date_entry("End Date:")
        elif self.date_op == "after":
            self.date_entry = self.ask_for_date_entry("Start Date:")
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
        """Apply the configured categorical, numeric, or temporal filter to the dataset.

        Args:
            selected_column (str): Column name to apply the filter on.
        """
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
        """Finalize filtering and display the plotting / metrics selection interface."""
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

            self.ssm_button = ctk.CTkButton(statistics_frame, text="SSM Metrics", command=lambda: self.show_ssm_metrics())
            self.ssm_button.pack(side="left", padx=5)
        
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

            self.draw_median_labels_var = ctk.BooleanVar(value=True)  # True por defecto
            draw_median_labels_checkbox = ctk.CTkCheckBox(
                self,
                text="Show text inside median points",
                variable=self.draw_median_labels_var
            )
            draw_median_labels_checkbox.pack(pady=10)
        
    

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
        values = ["Scatter", "Density", "Density only P50", "Density only P50 (lines)", "Density with Distribution", "Density only P50 with Distribution", "Density only P50 (lines) with Distribution", "Personalized Boxplot", "Personalized Scatter"]

        if self.data_types == "emotions":
            values.append("Classic Boxplot")
            values.append("Radar Plot")
            values.append("SSM Fitting (lines)")
            values.append("SSM Fitting (sinusoidal)")
            values.append("Empty")

        self.graph_type_selector = ctk.CTkOptionMenu(self, values=values, command=self.draw_graph)
        self.graph_type_selector.set("Graph Type")  # Default option
        self.graph_type_selector.pack(pady=5)



    def draw_graph(self, graph_type):
        """Draw the selected type of soundscape visualization.

        Args:
            graph_type (str): Type of chart to generate (e.g., 'Scatter', 'Density', 'Radar Plot').
        """
        if not hasattr(self, 'df') or self.df.empty:
            messagebox.showerror("Error", "No data to visualize. Please filter the data first.")
            exit(1)

        # Reset the value in the graph type selector
        self.graph_type_selector.set("Graph Type")
        
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
                "diagonal_lines": False,
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
                g = sspy.jointplot(
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

            elif graph_type == "Classic Boxplot":
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

                x_label = 'PAQ model dimension'
                y_label = 'Survey score'
            
                PAQs_melted = PAQs.melt(id_vars=differentiation_column, var_name=x_label, value_name=y_label)

                plt.figure(figsize=(10, 6))
                sns.boxplot(
                    x=x_label,
                    y=y_label,
                    data=PAQs_melted,
                    hue=differentiation_column,
                    gap=0.1,
                    medianprops=dict(color='black', linewidth=2.5)
                )
                plt.xticks(rotation=45)
                plt.title(title_label)

            elif graph_type == "Personalized Boxplot":

                # Popup        
                popup = ctk.CTkToplevel()
                popup.title("Personalized Boxplot")
                popup.geometry("600x300")

                frame = ctk.CTkFrame(popup, corner_radius=15)
                frame.pack(padx=20, pady=10, fill="both", expand=True)

                title = ctk.CTkLabel(frame, text="Personalized Boxplot", font=ctk.CTkFont(size=18, weight="bold"))
                title.pack(pady=(15, 5))

                y_values = list(self.df.columns)
                x_values = list(self.df.columns)
                to_delete = ["ISOPleasant", "ISOEventful"]
                for i in range(1,9):
                    to_delete.append(f"PAQ{i}")
                for col in x_values:
                    # If it has more than MAX_UNIQUES, remove it
                    if self.df[col].nunique() > self.MAX_UNIQUES:
                        to_delete.append(col)
                for col in to_delete:
                    if col in x_values:
                        x_values.remove(col)

                # Entry for X Axis
                center_frame = ctk.CTkFrame(frame, fg_color="transparent")
                center_frame.pack(pady=10)

                self.x_axis_selector = CustomFiltering(center_frame, values=x_values, default_text="X Axis")
                self.x_axis_selector_label = ctk.CTkLabel(center_frame, text="Select the column for the X Axis:")
                self.x_axis_selector_label.pack(side="left", padx=5)
                self.x_axis_selector.pack(side="left", padx=5)

                # Entry for Y Axis
                center_frame = ctk.CTkFrame(frame, fg_color="transparent")
                center_frame.pack(pady=10)  # expand=True centers the frame
                self.y_axis_selector = CustomFiltering(center_frame, values=y_values, default_text="Y Axis")
                self.y_axis_selector_label = ctk.CTkLabel(center_frame, text="Select the column for the Y Axis:")
                self.y_axis_selector_label.pack(side="left", padx=5)
                self.y_axis_selector.pack(side="left", padx=5)


                # Buttons frame to place them in the same row
                buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
                buttons_frame.pack(pady=(10, 15))
                
                ctk.CTkButton(buttons_frame, text="Exit", command=popup.destroy).pack(side="left", padx=5)
                ctk.CTkButton(buttons_frame, text="Plot", command=lambda: self.plot_personalized_boxplot(differentiation_column)).pack(side="left", padx=5)

            elif graph_type == "Personalized Scatter":
                popup = ctk.CTkToplevel()
                popup.title("Personalized Scatter")
                popup.geometry("600x300")

                frame = ctk.CTkFrame(popup, corner_radius=15)
                frame.pack(padx=20, pady=10, fill="both", expand=True)

                title = ctk.CTkLabel(frame, text="Personalized Scatter", font=ctk.CTkFont(size=18, weight="bold"))
                title.pack(pady=(15, 5))

                # Permitimos elegir cualquier columna del DataFrame original
                all_columns = list(self.df.columns)

                # Selector Eje X
                center_frame_x = ctk.CTkFrame(frame, fg_color="transparent")
                center_frame_x.pack(pady=10)
                self.custom_x_selector = CustomFiltering(center_frame_x, values=all_columns, default_text="X-Axis")
                ctk.CTkLabel(center_frame_x, text="X-Axis Variable:").pack(side="left", padx=5)
                self.custom_x_selector.pack(side="left", padx=5)

                # Selector Eje Y
                center_frame_y = ctk.CTkFrame(frame, fg_color="transparent")
                center_frame_y.pack(pady=10)
                self.custom_y_selector = CustomFiltering(center_frame_y, values=all_columns, default_text="Y-Axis")
                ctk.CTkLabel(center_frame_y, text="Y-Axis Variable:").pack(side="left", padx=5)
                self.custom_y_selector.pack(side="left", padx=5)

                # Botones de acción
                buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
                buttons_frame.pack(pady=(10, 15))
                
                ctk.CTkButton(buttons_frame, text="Exit", command=popup.destroy).pack(side="left", padx=5)
                ctk.CTkButton(buttons_frame, text="Plot", command=lambda: self.plot_custom_scatter(differentiation_column)).pack(side="left", padx=5)


            elif (graph_type == "SSM Fitting (lines)" or graph_type == "SSM Fitting (sinusoidal)") and self.data_types == "emotions":
                
                merged_df = self.obtain_ssm_metrics()

                equal_angles = (0, 45, 90, 135, 180, 225, 270, 315)
                emotions = ["Pleasant", "Vibrant", "Eventful", "Chaotic", "Annoying", "Monotonous", "Uneventful", "Calm"]


                merged_df = self.revert_from_PAQ(merged_df)
                # Capitalize the columns
                merged_df.columns = [col.capitalize() for col in merged_df.columns]
                
                
                x_label = 'PAQ model dimension'
                y_label = ''
                plt.figure(figsize=(12, 8))
                plt.title(title_label, fontsize=16, fontweight='bold')
                plt.xlabel(x_label, fontsize=14)
                plt.ylabel(y_label, fontsize=14)

                # Generate colors for each row (group)
                n_groups = len(merged_df)
                colors = sns.color_palette("husl", n_groups) if n_groups > 1 else ['steelblue']




                for index, (row_idx, row) in enumerate(merged_df.iterrows()):
                    color = colors[index]
                    
                    # Get real values for each emotion
                    real_values = [row[emotion] for emotion in emotions]
                    
                    # Calculate fitted values using SSM model
                    fitted_values = []
                    for angle_idx, emotion in enumerate(emotions):
                        fitted_value = ssm_model(
                            equal_angles[angle_idx], 
                            row["Amplitude"],
                            row["Displacement"],
                            row["Elevation"]
                        )
                        fitted_values.append(fitted_value)
                    
                    
                    if graph_type == "SSM Fitting (lines)":
                        # Plot real values with solid line
                        plt.plot(emotions, real_values, 
                            color=color, 
                            linestyle='-', 
                            linewidth=2, 
                            marker='s', 
                            markersize=6,
                            label=f'Real - {row["Value"]}' if differentiation_column else 'Real values')


                        # Plot fitted values with dashed line
                        plt.plot(emotions, fitted_values, 
                                color=color, 
                                linestyle='--', 
                                linewidth=2, 
                                marker='o',
                                markerfacecolor='none',   # <-- evita que el relleno del marker tape la línea
                                markersize=6,
                                label=f'Fitted - {row["Value"]}' if differentiation_column else 'Fitted values')
                        
                    elif graph_type == "SSM Fitting (sinusoidal)":
                        # 1. Graficar valores reales usando los ángulos como X
                        plt.plot(equal_angles, real_values, 
                                color=color, linestyle='-', linewidth=2, marker='s', markersize=6,
                                label=f'Real - {row["Value"]}' if differentiation_column else 'Real values')
                        
                        # 2. Graficar la curva continua (0 a 360 grados)
                        theta = np.linspace(equal_angles[0], equal_angles[-1], 200)  # 360 puntos para una curva suave
                        fitted_curve = ssm_model(theta, row["Amplitude"], row["Displacement"], row["Elevation"])
                        plt.plot(theta, fitted_curve,
                                color=color, linestyle='--', linewidth=2, # Línea punteada para la curva continua
                                label=f'Fitted Curve - {row["Value"]}' if differentiation_column else 'Fitted Curve')

                        # 3. Graficar los puntos discretos ajustados sobre la curva
                        plt.plot(equal_angles, fitted_values,
                                color=color, 
                                linestyle='',           # <-- Sin línea, solo puntos
                                marker='o',
                                markerfacecolor='none', # <-- Centro transparente
                                markersize=6,           # <-- Mismo tamaño que en el otro gráfico
                                zorder=3)

                # --- CONFIGURACIÓN DEL EJE X SEGÚN EL TIPO DE GRÁFICO ---
                if graph_type == "SSM Fitting (sinusoidal)":
                    # Forzamos a que el eje X muestre los ángulos pero con el texto de las emociones
                    plt.xticks(equal_angles, emotions, rotation=45, ha='right')
                    plt.xlim(-15, 335) # Un pequeño margen para que no se corten los extremos
                else:
                    # Comportamiento normal para el gráfico de líneas categórico
                    plt.xticks(rotation=45, ha='right')
                    
                plt.grid(True, linestyle='--', alpha=0.7)
                
            
            elif graph_type == "Radar Plot" and self.data_types == "emotions":
                # Si hay más de 7 filas, calculamos las medianas para agrupar los datos
                if len(plot_df) > self.MAX_RADAR_PLOT_ROWS:
                    # Aviso visual al usuario mediante un messagebox
                    messagebox.showinfo(
                        "Visualization Information", 
                        f"The dataset has more than {self.MAX_RADAR_PLOT_ROWS} records.\n\n"
                        "In order to ensure the readability of the Radar Plot, the median will be automatically calculated and displayed."
                    )
                    
                    if differentiation_column is not None:
                        # Agrupamos por la columna elegida y calculamos la mediana de las preguntas PAQ
                        PAQs_cols = [f"PAQ{i}" for i in range(1, 9)]
                        radar_df = plot_df.groupby(differentiation_column, observed=False)[PAQs_cols].median().reset_index()
                    else:
                        # Si no hay columna de diferenciación, calculamos la mediana global
                        PAQs_cols = [f"PAQ{i}" for i in range(1, 9)]
                        radar_df = plot_df[PAQs_cols].median().to_frame().T
                        radar_df["Value"] = "Global Median"
                        differentiation_column = "Value"
                else:
                    # Si tiene 7 o menos registros, usamos el plot_df original con todos los datos individuales
                    radar_df = plot_df.copy()

                # Revertimos de formato PAQ (PAQ1, PAQ2...) a los nombres de las emociones (Pleasant, Vibrant...)
                radar_df = self.revert_from_PAQ(radar_df)
                
                # Renderizamos el gráfico usando la función nativa de soundscapy
                sspy.paq_radar_plot(radar_df, title=title_label, index=differentiation_column)

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


            else:
                messagebox.showerror("Error", "Unsupported graph type selected.")

            
            if self.data_types == "emotions" \
                and hasattr(self, 'draw_median_var') \
                and self.draw_median_var.get() \
                and graph_type not in ["Radar Plot", "Classic Boxplot", "SSM Fitting (lines)", "SSM Fitting (sinusoidal)", "Personalized Boxplot", "Personalized Scatter"]:

                self.draw_median(plot_df, differentiation_column)

            if graph_type not in ["Radar Plot", "Classic Boxplot", "SSM Fitting (lines)", "SSM Fitting (sinusoidal)", "Personalized Boxplot", "Personalized Scatter"]:
                self.draw_diagonals()

            # Get current axes safely and apply aspect ratio only to simple plots
            if graph_type not in ["Radar Plot", "Classic Boxplot", "SSM Fitting (lines)", "SSM Fitting (sinusoidal)", "Personalized Boxplot", "Personalized Scatter"]:
                try:
                    fig = plt.gcf()
                    axes = fig.get_axes()
                    
                    if len(axes) == 1:
                        # Single axis - safe to set aspect equal
                        ax = plt.gca()
                        ax.set_aspect('equal')
                    else:
                        print("Info: Skipping aspect ratio for jointplot to maintain proper alignment")
                except Exception as e:
                    print(f"Warning: Could not set aspect ratio: {e}")

            if graph_type not in ["Personalized Boxplot", "Personalized Scatter"]:
                # Only show legend if there are labeled elements to display
                try:
                    fig = plt.gcf()
                    ax = plt.gca()
                    
                    # Check if there are any labeled elements (handles and labels)
                    handles, labels = ax.get_legend_handles_labels()
                    
                    if handles and labels:
                        # There are elements with labels, show the legend
                        legend = plt.legend(loc='best', title=differentiation_column if differentiation_column else None)
                        renderer = fig.canvas.get_renderer() if hasattr(fig.canvas, 'get_renderer') else None

                        if renderer:
                            try:
                                legend_bbox = legend.get_window_extent(renderer)
                                plot_bbox = ax.get_window_extent(renderer)
                                
                                # Calculate overlap ratio - fix the intersection call
                                if legend_bbox and plot_bbox:
                                    # Convert to the same coordinate system if needed
                                    legend_bounds = legend_bbox.bounds  # (x0, y0, width, height)
                                    plot_bounds = plot_bbox.bounds      # (x0, y0, width, height)
                                    
                                    # Calculate intersection manually
                                    x_left = max(legend_bounds[0], plot_bounds[0])
                                    y_bottom = max(legend_bounds[1], plot_bounds[1])
                                    x_right = min(legend_bounds[0] + legend_bounds[2], plot_bounds[0] + plot_bounds[2])
                                    y_top = min(legend_bounds[1] + legend_bounds[3], plot_bounds[1] + plot_bounds[3])
                                    
                                    if x_right > x_left and y_top > y_bottom:
                                        # There is an intersection
                                        intersection_area = (x_right - x_left) * (y_top - y_bottom)
                                        legend_area = legend_bounds[2] * legend_bounds[3]
                                        overlap_ratio = intersection_area / legend_area if legend_area > 0 else 0
                                        
                                        # If more than 30% of legend overlaps with plot area, move outside
                                        if overlap_ratio > 0.3:
                                            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title=differentiation_column if differentiation_column else None)
                                            print("Info: Moved legend outside due to overlap")
                                    # If no intersection, legend is fine where it is
                            except Exception as bbox_error:
                                print(f"Warning: Could not calculate bbox intersection: {bbox_error}")
                                # Fallback to outside placement
                                plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title=differentiation_column if differentiation_column else None)
                        else:
                            # Fallback: if we can't get renderer, place outside
                            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title=differentiation_column if differentiation_column else None)
                            print("Warning: Could not get renderer for legend placement.")
                        
                except Exception as e:
                    # If anything fails, use simple outside placement
                    try:
                        fig = plt.gcf()
                        ax = plt.gca()
                        handles, labels = ax.get_legend_handles_labels()
                        if handles and labels:
                            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title=differentiation_column if differentiation_column else None)
                            print(f"Warning: Could not place legend optimally, placed outside instead: {e}")
                    except:
                        pass  # Just don't show legend if everything fails
                
                plt.tick_params(axis='both', labelsize=7)
                plt.tight_layout()
                plt.show()
            
        except Exception as e:
            print(f"Error drawing graph: {e}")
            messagebox.showerror("Error", f"Could not draw graph:\n{e}")

    def plot_personalized_boxplot(self, differentiation_column=None):
        """Plot a customized Seaborn boxplot based on user-selected X and Y columns.

        Args:
            differentiation_column (str | None, optional): Column name used for hue categorization. Defaults to None.
        """
        x_column = self.x_axis_selector.get() if hasattr(self, 'x_axis_selector') else None
        y_column = self.y_axis_selector.get() if hasattr(self, 'y_axis_selector') else None

        if x_column not in self.df.columns or y_column not in self.df.columns:
            messagebox.showerror("Error", "Both X and Y axis columns must be selected and valid.")
            return

        if x_column == y_column:
            messagebox.showerror("Error", "X and Y axis columns must be different.")
            return

        # Create a copy of the DataFrame for plotting to avoid modifying the original
        plot_df = self.df.copy()
        # Get unique values from x_column and sort them
        x_order = sorted(plot_df[x_column].dropna().unique())

        
        sns.boxplot(
            x=x_column,
            y=y_column,
            data=plot_df,
            order=x_order,  # This will sort the x-axis values
            hue=differentiation_column,
            gap=0.1,
            medianprops=dict(color='black', linewidth=2.5)
        )
        plt.xticks(rotation=45)
        title_label = self.title_entry.get() if hasattr(self, 'title_entry') else "Filtered Data Visualization"
        plt.title(title_label)

        if differentiation_column is not None:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title=differentiation_column)


        plt.tight_layout()
        plt.show()

    def plot_custom_scatter(self, differentiation_column=None):
        """Plot a customized bivariate scatter plot based on user selections.

        Args:
            differentiation_column (str | None, optional): Column name used for hue categorization. Defaults to None.
        """
        x_column = self.custom_x_selector.get() if hasattr(self, 'custom_x_selector') else None
        y_column = self.custom_y_selector.get() if hasattr(self, 'custom_y_selector') else None

        if x_column not in self.df.columns or y_column not in self.df.columns:
            messagebox.showerror("Error", "Both X and Y axis columns must be selected and valid.")
            return

        # Creamos la figura de matplotlib
        plt.figure(figsize=(10, 6))
        
        # Copia para evitar modificar los datos originales
        plot_df = self.df.copy()

        # Dibujamos usando seaborn scatterplot
        sns.scatterplot(
            x=x_column,
            y=y_column,
            data=plot_df,
            hue=differentiation_column,
            palette="deep" if differentiation_column else None,
            alpha=0.8,
            edgecolor="w",
            s=80
        )

        # Configuración de etiquetas y título
        title_label = self.title_entry.get() if hasattr(self, 'title_entry') else "Scatter Plot"
        plt.title(title_label, fontsize=14, fontweight='bold')
        plt.xlabel(x_column, fontsize=12)
        plt.ylabel(y_column, fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.5)

        # Si hay leyenda de diferenciación, la movemos fuera para que no moleste
        if differentiation_column is not None:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title=differentiation_column)

        plt.tight_layout()
        plt.show()

    def revert_from_PAQ(self, data):
        """Revert PAQ codes (PAQ1-PAQ8) back to their corresponding emotion names.

        Args:
            data (pd.DataFrame | pd.Series): Data containing PAQ ID headers or indices.

        Returns:
            pd.DataFrame | pd.Series: Renamed dataset copy with natural emotion labels.
        """
                
        # Check if it's a DataFrame or Series and handle accordingly
        if isinstance(data, pd.DataFrame):
            data = data.copy()
            data.rename(columns=PAQ_DICT_REVERT, inplace=True)
        elif isinstance(data, pd.Series):
            data = data.copy()
            data.rename(index=PAQ_DICT_REVERT, inplace=True)
        
        return data
        
    def show_iqr(self):
        """Calculate and display the Interquartile Range (IQR) table in a modal dialog."""
        if not hasattr(self, 'df') or self.df.empty:
            messagebox.showerror("Error", "No data to calculate IQR. Please filter the data first.")
            return

        differentiation_column = self.differentiation_selector.get() if hasattr(self, 'differentiation_selector') else None
        if differentiation_column not in self.df.columns:
            differentiation_column = None

        IQR = pd.DataFrame(columns=["Value"])

        if differentiation_column is None:
            sorted_values = [""] 
        else:
            unique_values = self.df[differentiation_column].dropna().unique()
            sorted_values = sorted(unique_values)
        
        for value in sorted_values:
            # Filter the DataFrame by the current value in the differentiation column
            if differentiation_column is not None:
                value_df = self.df[self.df[differentiation_column] == value]
            else:
                value_df = self.df
            
            PAQs_value = sspy.surveys.return_paqs(value_df)
            Q3_value = PAQs_value.quantile(0.75)
            Q1_value = PAQs_value.quantile(0.25)
            IQR_value = Q3_value - Q1_value
            IQR_value = pd.DataFrame(IQR_value).T

            IQR_value = self.revert_from_PAQ(IQR_value)

            IQR = pd.concat([IQR, IQR_value], ignore_index=True)
            IQR.at[IQR.index[-1], 'Value'] = value  # Add the value of the differentiation column

        # Capitalize the columns
        IQR.columns = [emotion.capitalize() for emotion in IQR.columns]
            
        
        # Popup        
        popup = ctk.CTkToplevel()
        popup.title("IQR Values")
        popup.geometry("650x450")

        frame = ctk.CTkFrame(popup, corner_radius=15)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        title = ctk.CTkLabel(frame, text="IQR Values for each Emotion", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(15, 5))

        # Create an inner frame to center the table and keep it compact
        inner_table_frame = ctk.CTkFrame(frame, fg_color="transparent")
        inner_table_frame.pack(pady=10, expand=True)

        # Header
        emotions = ["Pleasant", "Vibrant", "Eventful", "Chaotic", "Annoying", "Monotonous", "Uneventful", "Calm"]
        for idx, emotion in enumerate(emotions, start=1):
            ctk.CTkLabel(inner_table_frame, text=emotion.capitalize(), font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=idx, padx=5, pady=4, sticky="w")

        for idy in range(1, len(sorted_values) + 1):
            ctk.CTkLabel(inner_table_frame, text=sorted_values[idy - 1], font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=idy, column=0, padx=5, pady=4, sticky="w")
            for idx, emotion in enumerate(emotions, start=1):
                value = IQR.at[IQR.index[idy - 1], emotion]
                ctk.CTkLabel(inner_table_frame, text=f"{value:.0f}", font=ctk.CTkFont(size=13), anchor="e").grid(row=idy, column=idx, padx=10, pady=2, sticky="e")
        
        # Buttons frame to place them in the same row
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.pack(pady=(10, 15))
        
        ctk.CTkButton(buttons_frame, text="Exit", command=popup.destroy).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Save IQR Values", command=lambda: self.save_df_to_file(IQR, default_name=self.file_name + "_filtered_IQR")).pack(side="left", padx=5)

    def save_df_to_file(self, df, default_name=None):
        """Export a pandas DataFrame or Series to a file via a native save file dialog.

        Args:
            df (pd.DataFrame | pd.Series): The data structure to export.
            default_name (str | None, optional): Suggested default filename without extension. Defaults to None.
        """
        filetypes = [
            ("Excel files", "*.xls *.xlsx"),
            ("CSV/TSV files", "*.csv *.tsv"),
            ("OpenDocument Spreadsheet", "*.ods"),
        ]
        filepath = filedialog.asksaveasfilename(
            title="Save Data",
            filetypes=filetypes,
            defaultextension=".xlsx",  # Default extension
            initialfile=default_name + ".xlsx" if default_name else None,
        )
        if not filepath:
            # User cancelled the save dialog
            return
        
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

    def obtain_median(self):
        """Calculate the median coordinates for each subset defined by the differentiation column.

        Returns:
            pd.DataFrame | None: DataFrame containing median coordinates and PAQ values, or None if no data.
        """
        if not hasattr(self, 'df') or self.df.empty:
            messagebox.showerror("Error", "No data to calculate median. Please filter the data first.")
            return
    
        differentiation_column = self.differentiation_selector.get() if hasattr(self, 'differentiation_selector') else None
        if differentiation_column not in self.df.columns:
            differentiation_column = None

        median = pd.DataFrame(columns=["Value"])


        if differentiation_column is None:
            sorted_values = [""] 
        else:
            unique_values = self.df[differentiation_column].dropna().unique()
            sorted_values = sorted(unique_values)

        for value in sorted_values:
            if differentiation_column is None:
                value_df = self.df
            else:
                value_df = self.df[self.df[differentiation_column] == value]
            PAQs_value = sspy.surveys.return_paqs(value_df)
            median_value = PAQs_value.median()
            median_value = pd.DataFrame(median_value).T

            median = pd.concat([median, median_value], ignore_index=True)
            median.at[median.index[-1], "Value"] = value  # Set the differentiation column value

        
        median = sspy.surveys.add_iso_coords(median)
        return median

    def show_median(self):
        """Calculate and display median coordinates in a modal dialog."""
        median = self.obtain_median()
        

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

        # Header
        ctk.CTkLabel(inner_table_frame, text="ISOPleasant", font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=1, padx=5, pady=4)
        ctk.CTkLabel(inner_table_frame, text="ISOEventful", font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=2, padx=5, pady=4)
        
        # Rows
        for idx, (value, pleasant, eventful) in enumerate(zip(median["Value"], median["ISOPleasant"], median["ISOEventful"]), start=1):
            value_label    = ctk.CTkLabel(inner_table_frame, text=str(value),        font=ctk.CTkFont(size=13), anchor="center")
            pleasant_label = ctk.CTkLabel(inner_table_frame, text=f"{pleasant:.4f}", font=ctk.CTkFont(size=13), anchor="center")
            eventful_label = ctk.CTkLabel(inner_table_frame, text=f"{eventful:.4f}", font=ctk.CTkFont(size=13), anchor="center")
            value_label.grid(row=idx, column=0, padx=10, pady=2, sticky="w")
            pleasant_label.grid(row=idx, column=1, padx=10, pady=2, sticky="e")
            eventful_label.grid(row=idx, column=2, padx=10, pady=2, sticky="e")

        # Buttons frame to place them in the same row
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.pack(pady=(10, 15))

        median = self.revert_from_PAQ(median)
        median.columns = [col.capitalize() for col in median.columns]  # Capitalize the column names
        
        ctk.CTkButton(buttons_frame, text="Exit", command=popup.destroy).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Save Median Values", command=lambda: self.save_df_to_file(median, default_name=self.file_name + "_filtered_median")).pack(side="left", padx=5)


    def draw_median(self, plot_df, differentiation_column=None):
        """Overlay median coordinate points onto the active matplotlib axes.

        Args:
            plot_df (pd.DataFrame): The filtered dataset.
            differentiation_column (str | None, optional): Categorical hue grouping variable. Defaults to None.
        """
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
            y = median["ISOEventful"].values[0]
            x = median["ISOPleasant"].values[0]

            # Add the median point to the plot
            # Check if we're in a jointplot context (has multiple subplots)
            fig = plt.gcf()
            axes = fig.get_axes()
            
            main_ax = axes[0]
            main_ax.scatter(x, y, color=color, s=160, edgecolor='black', linewidth=2, zorder=10, alpha=0.9)

            # Add label to the point itself
            # Solo añade el texto si hay columna de diferenciación Y la casilla está marcada
            show_labels = getattr(self, 'draw_median_labels_var', None)
            if differentiation_column is not None and (show_labels is None or show_labels.get()):
                main_ax.text(x, y, str(value), color='black', fontsize=6, fontweight='bold', ha='center', va='center', zorder=10)

    
    def obtain_ssm_metrics(self):
        """Calculate the Soundscape Standard Model (SSM) metrics on the dataset's medians.

        Returns:
            pd.DataFrame | None: Merged dataset of medians and SSM metrics, or None if calculation fails.
        """
        median = self.obtain_median()
        SSM_metrics = sspy.surveys.processing.ssm_metrics(median)

        # Fixing bugs in sspy "ssm_metrics" function
        SSM_metrics["elevation"] = SSM_metrics["elevation"] + SSM_metrics["displacement"]
        SSM_metrics.drop(columns=["displacement"], inplace=True)

        SSM_metrics.rename(columns={"angle": "displacement"}, inplace=True)



        # Check. Equal number of rows?
        if len(SSM_metrics) != len(median):
            messagebox.showerror("Error", "SSM metrics and median have different number of rows.")
            return
        
        # Merge the two DataFrames on their indices
        merged_df = pd.merge(median, SSM_metrics, left_index=True, right_index=True, suffixes=('_median', '_ssm'))

        return merged_df

    
    def show_ssm_metrics(self):
        """Calculate and display SSM metrics table in a modal dialog."""
        merged_df = self.obtain_ssm_metrics()
        

        # Popup        
        popup = ctk.CTkToplevel()
        popup.title("SSM Metrics")
        popup.geometry("400x400")

        frame = ctk.CTkFrame(popup, corner_radius=15)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        title = ctk.CTkLabel(frame, text="SSM Cosine Fitting Metrics", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(15, 5))

        # Create an inner frame to center the table and keep it compact
        inner_table_frame = ctk.CTkFrame(frame, fg_color="transparent")
        inner_table_frame.pack(pady=10, expand=True)

        # Header
        ctk.CTkLabel(inner_table_frame, text="Amplitude", font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=1, padx=5, pady=4)
        ctk.CTkLabel(inner_table_frame, text="Elevation", font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=2, padx=5, pady=4)
        ctk.CTkLabel(inner_table_frame, text="Displacement", font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=3, padx=5, pady=4)
        ctk.CTkLabel(inner_table_frame, text="R^2", font=ctk.CTkFont(size=14, weight="bold"), anchor="center").grid(row=0, column=4, padx=5, pady=4)
        
        # Rows
        for idx, (value, amplitude, elevation, displacement, r_squared) in enumerate(zip(merged_df["Value"], merged_df["amplitude"], merged_df["elevation"], merged_df["displacement"], merged_df["r_squared"]), start=1):
            value_label        = ctk.CTkLabel(inner_table_frame, text=str(value),        font=ctk.CTkFont(size=13), anchor="center")
            amplitude_label    = ctk.CTkLabel(inner_table_frame, text=f"{amplitude:.2f}", font=ctk.CTkFont(size=13), anchor="center")
            elevation_label    = ctk.CTkLabel(inner_table_frame, text=f"{elevation:.2f}", font=ctk.CTkFont(size=13), anchor="center")
            displacement_label = ctk.CTkLabel(inner_table_frame, text=f"{displacement:.2f}", font=ctk.CTkFont(size=13), anchor="center")
            r_squared_label    = ctk.CTkLabel(inner_table_frame, text=f"{r_squared:.4f}", font=ctk.CTkFont(size=13), anchor="center")
            value_label.grid(row=idx, column=0, padx=10, pady=2, sticky="w")
            amplitude_label.grid(row=idx, column=1, padx=10, pady=2, sticky="e")
            elevation_label.grid(row=idx, column=2, padx=10, pady=2, sticky="e")
            displacement_label.grid(row=idx, column=3, padx=10, pady=2, sticky="e")
            r_squared_label.grid(row=idx, column=4, padx=10, pady=2, sticky="e")

        # Buttons frame to place them in the same row
        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.pack(pady=(10, 15))

        merged_df = self.revert_from_PAQ(merged_df)
        merged_df.columns = [col.capitalize() for col in merged_df.columns]  # Capitalize the column names
        
        ctk.CTkButton(buttons_frame, text="Exit", command=popup.destroy).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="Save SSM Metrics", command=lambda: self.save_df_to_file(merged_df, default_name=self.file_name + "_filtered_ssm_metrics")).pack(side="left", padx=5)
        

    def draw_diagonals(self):
        """Draw ISO 12913-3 reference diagonal quadrant lines and emotion quadrant labels on the active plot."""
        fig = plt.gcf()
        axes = fig.get_axes()
        
        ax = axes[0]

        # Get current limits
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        
        ax.plot([x_min, x_max], [y_min, y_max], color='gray', linestyle='--', linewidth=1, alpha=0.7)
        ax.plot([x_min, x_max], [y_max, y_min], color='gray', linestyle='--', linewidth=1, alpha=0.7)

        # Definir estilo común para las etiquetas
        label_style = dict(
            fontsize=9, 
            fontstyle='italic', 
            color='dimgray', 
            ha='center', 
            va='center',
            alpha=0.8
        )

        # Añadir las etiquetas en las coordenadas correspondientes
        loc = 0.75
        ax.text(loc, loc, '(vibrant)', **label_style)
        ax.text(-loc, loc, '(chaotic)', **label_style)
        ax.text(-loc, -loc, '(monotonous)', **label_style)
        ax.text(loc, -loc, '(calm)', **label_style)
        

