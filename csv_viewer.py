import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from datetime import datetime
import numpy as np
import shutil
import os
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CSVViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Metrics Viewer")
        self.root.geometry("1000x600")
        self.temp_csv = None

        try:
            # Ensure Data directory exists
            if not os.path.exists('Data'):
                raise FileNotFoundError("Data directory not found")

            original_csv = os.path.join('Data', 'network_metrics.csv')
            if not os.path.exists(original_csv):
                raise FileNotFoundError(f"CSV file not found: {original_csv}")

            # Create a temporary copy of the CSV file
            self.temp_csv = self.create_temp_copy()
            logger.debug(f"Temporary file created at: {self.temp_csv}")
            
            # Load the CSV data from the temporary copy
            self.df = pd.read_csv(self.temp_csv)
            # Convert timestamp to datetime
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            messagebox.showerror("Error", f"Failed to initialize: {str(e)}")
            self.root.destroy()
            return

        # Create the main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create metric selection dropdown
        self.metric_var = tk.StringVar(value='download')
        metrics = ['download', 'upload', 'ping']
        self.metric_select = ttk.Combobox(
            self.main_frame, 
            textvariable=self.metric_var,
            values=metrics,
            state='readonly'
        )
        self.metric_select.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.metric_select.bind('<<ComboboxSelected>>', self.update_graph)

        # Add refresh button
        self.refresh_button = ttk.Button(
            self.main_frame,
            text="Refresh Data",
            command=self.refresh_data
        )
        self.refresh_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.E)

        # Create the figure and canvas
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        # Create a frame for the toolbar to prevent geometry manager conflicts
        self.toolbar_frame = ttk.Frame(self.main_frame)
        self.toolbar_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
        
        # Add the navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)

        # Add statistics label
        self.stats_label = ttk.Label(self.main_frame, text="", wraplength=900)
        self.stats_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        # Store the current annotation to remove it later
        self.current_annotation = None
        
        # Connect the hover event instead of click
        self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        # Connect scroll event for zooming
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

        # Bind cleanup to window closing
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)

        # Initial plot
        self.update_graph()

    def create_temp_copy(self):
        """Create a temporary copy of the CSV file."""
        try:
            original_csv = os.path.join('Data', 'network_metrics.csv')
            if not os.path.exists(original_csv):
                raise FileNotFoundError(f"Original CSV file not found: {original_csv}")
            
            # Create a unique temporary file name
            temp_file = tempfile.NamedTemporaryFile(
                prefix='network_metrics_',
                suffix='.csv',
                delete=False
            )
            temp_csv = temp_file.name
            temp_file.close()  # Close the file so we can copy to it
            
            logger.debug(f"Copying {original_csv} to {temp_csv}")
            shutil.copy2(original_csv, temp_csv)
            
            return temp_csv
        except Exception as e:
            logger.error(f"Error in create_temp_copy: {str(e)}")
            raise Exception(f"Failed to create temporary copy: {str(e)}")

    def refresh_data(self):
        """Refresh the data by creating a new temporary copy and updating the graph."""
        try:
            logger.debug("Starting data refresh")
            
            # Create a new temporary copy
            new_temp_csv = self.create_temp_copy()
            logger.debug(f"Created new temporary file: {new_temp_csv}")
            
            # Remove the old temporary file
            if self.temp_csv and os.path.exists(self.temp_csv):
                try:
                    os.remove(self.temp_csv)
                    logger.debug(f"Removed old temporary file: {self.temp_csv}")
                except Exception as e:
                    logger.warning(f"Failed to remove old temp file: {str(e)}")
            
            # Update the temporary file reference
            self.temp_csv = new_temp_csv
            
            # Reload the data
            self.df = pd.read_csv(self.temp_csv)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            
            # Update the graph
            self.update_graph()
            
            logger.debug("Data refresh completed successfully")
            messagebox.showinfo("Success", "Data refreshed successfully!")
        except Exception as e:
            logger.error(f"Error in refresh_data: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")

    def cleanup(self):
        """Clean up temporary files before closing."""
        try:
            if self.temp_csv and os.path.exists(self.temp_csv):
                os.remove(self.temp_csv)
                logger.debug(f"Cleaned up temporary file: {self.temp_csv}")
        except Exception as e:
            logger.warning(f"Cleanup error: {str(e)}")
        finally:
            self.root.destroy()

    def on_scroll(self, event):
        if not event.inaxes:
            return
            
        # Get the current x and y axis limits
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        
        # Get the cursor position
        xdata = event.xdata
        ydata = event.ydata
        
        if event.button == 'up':
            scale_factor = 0.9  # Zoom in
        else:
            scale_factor = 1.1  # Zoom out
            
        # Set the new limits
        self.ax.set_xlim([xdata - (xdata - cur_xlim[0]) * scale_factor,
                         xdata + (cur_xlim[1] - xdata) * scale_factor])
        self.ax.set_ylim([ydata - (ydata - cur_ylim[0]) * scale_factor,
                         ydata + (cur_ylim[1] - ydata) * scale_factor])
        
        self.canvas.draw()

    def on_hover(self, event):
        if event.inaxes != self.ax:
            if self.current_annotation:  # Remove annotation when mouse leaves the plot
                self.current_annotation.remove()
                self.current_annotation = None
                self.canvas.draw()
            return

        metric = self.metric_var.get()
        x_data = self.df['timestamp'].values
        y_data = self.df[metric].values

        # Find the nearest point
        x_hover = event.xdata
        distances = np.abs(mdates.date2num(x_data) - x_hover)
        nearest_idx = np.argmin(distances)

        # Remove previous annotation if it exists
        if self.current_annotation:
            self.current_annotation.remove()

        # Create new annotation
        timestamp = pd.Timestamp(x_data[nearest_idx]).to_pydatetime()
        value = y_data[nearest_idx]
        unit = 'Mbps' if metric in ['download', 'upload'] else 'ms'
        annotation_text = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")}\n{metric}: {value:.2f} {unit}'

        # Get the display coordinates of the data point
        display_coords = self.ax.transData.transform((mdates.date2num(timestamp), value))
        
        # Get the figure boundaries
        bbox = self.ax.get_window_extent()
        
        # Calculate offset based on position in the figure
        x_offset = 10
        y_offset = 10
        
        # Adjust offsets if near the right edge
        if display_coords[0] > bbox.x1 - 150:  # 150 pixels from right edge
            x_offset = -160  # Move annotation to the left of the point
            
        # Adjust offsets if near the top edge
        if display_coords[1] > bbox.y1 - 50:  # 50 pixels from top edge
            y_offset = -50  # Move annotation below the point
        
        self.current_annotation = self.ax.annotate(
            annotation_text,
            xy=(timestamp, value),
            xytext=(x_offset, y_offset),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=1.0),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )

        self.canvas.draw()

    def update_graph(self, event=None):
        self.ax.clear()
        metric = self.metric_var.get()
        
        # Plot the data
        self.ax.plot(self.df['timestamp'], self.df[metric], marker='o')
        
        # Customize the plot
        self.ax.set_title(f'{metric.capitalize()} Over Time')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel(f'{metric.capitalize()} {"(Mbps)" if metric in ["download", "upload"] else "(ms)"}')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Adjust layout to prevent label cutoff
        self.fig.tight_layout()
        
        # Reset the current annotation
        self.current_annotation = None
        
        # Update the canvas
        self.canvas.draw()

        # Update statistics
        stats = self.calculate_statistics(metric)
        self.stats_label.config(text=stats)

    def calculate_statistics(self, metric):
        data = self.df[metric]
        stats = f"""
        Statistics for {metric}:
        Average: {data.mean():.2f} {'Mbps' if metric in ['download', 'upload'] else 'ms'}
        Maximum: {data.max():.2f} {'Mbps' if metric in ['download', 'upload'] else 'ms'}
        Minimum: {data.min():.2f} {'Mbps' if metric in ['download', 'upload'] else 'ms'}
        Standard Deviation: {data.std():.2f}
        """
        return stats

def main():
    root = tk.Tk()
    app = CSVViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
