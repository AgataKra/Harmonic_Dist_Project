from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class InteractivePlot:
    def __init__(self, fig, canvas, toolbar):
        self.fig = fig
        self.canvas = canvas
        self.toolbar = toolbar
        self.default_limits = []

    def capture_default_view(self):
        self.default_limits = []
        for axis in self.fig.axes:
            self.default_limits.append((axis, axis.get_xlim(), axis.get_ylim()))
        self.toolbar.update()

    def reset_view(self):
        for axis, x_limits, y_limits in self.default_limits:
            axis.set_xlim(x_limits)
            axis.set_ylim(y_limits)
        self.canvas.draw_idle()


def place_figure(frame, fig):
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)
    toolbar_frame = ttk.Frame(frame)
    toolbar_frame.grid(row=0, column=0, sticky="ew")
    canvas = FigureCanvasTkAgg(fig, master=frame)
    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame, pack_toolbar=False)
    toolbar.update()
    toolbar.grid(row=0, column=0, sticky="w")
    reset_button = ttk.Button(
        toolbar_frame,
        text="Reset view",
        command=lambda: interactive_plot.reset_view(),
    )
    reset_button.grid(row=0, column=1, sticky="w", padx=(8, 0))
    canvas.draw()
    canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")
    interactive_plot = InteractivePlot(fig, canvas, toolbar)
    interactive_plot.capture_default_view()
    return interactive_plot
