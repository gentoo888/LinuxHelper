import tkinter as tk

class PreferencesScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Preferences", font=("Arial", 20)).pack(pady=20)

        self.visual_var = tk.StringVar(value="")
        self.usage_var = tk.StringVar(value="")

        tk.Label(self, text="Is visual design important?").pack()
        # The buttons are at the left side. 
        tk.Radiobutton(self, text="Yes", value="yes", variable=self.visual_var).pack(anchor="w")
        tk.Radiobutton(self, text="No",  value="no",  variable=self.visual_var).pack(anchor="w")

        tk.Label(self, text="Primary use case:").pack(pady=(10,0))
        usage_options = ["gaming", "office", "development"]
        tk.OptionMenu(self, self.usage_var, *usage_options).pack()

        self.warn = tk.Label(self, fg="red")
        self.warn.pack(pady=10)

        tk.Button(
            self,
            text="Next",
            font=("Arial", 14),
            command=self._on_next
        ).pack(pady=20)

    def _on_next(self):
        v = self.visual_var.get()
        u = self.usage_var.get()
        if v not in ("yes","no") or u == "":
            self.warn.config(text="Please select both visual preference and usage.")
            return
        self.controller.state["visual"] = v
        self.controller.state["usage"]  = u
        self.controller.show_frame("RecommendationScreen")

