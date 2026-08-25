import customtkinter as ctk


class CustomFiltering(ctk.CTkFrame):
    """A search entry widget combined with an auto-filtering dropdown list."""

    def __init__(self, master, values, default_text="", **kwargs):
        """Initialize the custom filter entry.

        Args:
            master (ctk.CTkBaseClass): Parent GUI widget container.
            values (list[str]): List of searchable options for the dropdown.
            default_text (str, optional): Initial placeholder text. Defaults to "".
            **kwargs: Arbitrary keyword arguments for ctk.CTkFrame.
        """
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
        self.entry.bind("<KeyRelease>", self.reset_list)
        
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
            """Scroll the list frame based on mouse wheel movement."""
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

    def reset_list(self, event=None):
        """Reset the dropdown list to update the displayed values based on the current entry text.

        Args:
            event: Optional event parameter for key release events.
        """
        if self.list_window and self.list_window.winfo_exists():
            self.list_window.destroy()
            self.list_window = None
            self.show_list()
    
    def select_value(self, val):
        """Select a value from the dropdown list and set it in the entry.

        Args:
            val (str): The value selected from the dropdown list.
        """
        self.set(val)
        self.close_list_window()
    
    def get(self):
        """Get the current value of the entry.

        Returns:
            str: The current text in the entry.
        """
        return self.entry.get()
    
    def set(self, value):
        """Set the value of the entry.

        Args:
            value (str): The text to set in the entry.
        """
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
        """Handle global click events to close the dropdown list if clicked outside.

        Args:
            event: The event object containing click coordinates.
        """
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

