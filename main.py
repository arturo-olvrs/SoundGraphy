import traceback
import sys
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import messagebox
from soundgraphy.gui import GUI

if __name__ == "__main__":
    app = None
    try:
        app = GUI()
        app.mainloop()
    except Exception as e:
        error_msg = f"ERROR DETECTED:\n\n{str(e)}\n\nTechnical details:\n{traceback.format_exc()}"
        try:
            root = ctk.CTk()
            root.withdraw()
            messagebox.showerror("ERROR DETECTED - Fatal Error", error_msg)
            root.destroy()
        except Exception:
            print(error_msg)
    finally:
        try:
            plt.close("all")
            if app:
                app.quit()
        except Exception:
            pass
        sys.exit(0)