import tkinter as tk
from tkinter import messagebox
from core_logic import SeleniumApp
from datetime import datetime
from utils import setup_logger

logger = setup_logger()

def main():
    def on_submit():
        username = username_entry.get()
        password = password_entry.get()
        crawl_year = crawl_year_entry.get()
        crawl_month = crawl_month_entry.get()
        crawl_day = crawl_day_entry.get()

        # Check if any field is empty
        if not username or not password or not crawl_year or not crawl_month or not crawl_day:
            messagebox.showerror("Error", "All fields are required!")
            return

        # Validate the date
        try:
            crawluntil_time = datetime(year=int(crawl_year), month=int(crawl_month), day=int(crawl_day))
        except ValueError:
            messagebox.showerror("Error", "Invalid date! Please enter a valid date.")
            return

        messagebox.showinfo("Info", "You can hit Ctrl+C to safely terminate the program anytime. ")
        messagebox.showwarning("Warning", "Data will only be saved if the program has finished running. ")

        # Close the GUI after getting input
        root.destroy()

        # If all inputs are valid, proceed to run the crawler
        app = SeleniumApp(username, password, crawluntil_time)
        app.run()

    root = tk.Tk()
    root.title("Selenium Crawler GUI")

    tk.Label(root, text="Username:").grid(row=0, column=0)
    username_entry = tk.Entry(root)
    username_entry.grid(row=0, column=1)

    tk.Label(root, text="Password:").grid(row=1, column=0)
    password_entry = tk.Entry(root, show="*")
    password_entry.grid(row=1, column=1)

    tk.Label(root, text="Specify the target date to crawl until:").grid(row=2, column=0, columnspan=2, pady=(10, 0))

    tk.Label(root, text="Year(YYYY):").grid(row=3, column=0)
    crawl_year_entry = tk.Entry(root)
    crawl_year_entry.grid(row=3, column=1)

    tk.Label(root, text="Month(MM):").grid(row=4, column=0)
    crawl_month_entry = tk.Entry(root)
    crawl_month_entry.grid(row=4, column=1)

    tk.Label(root, text="Day(DD):").grid(row=5, column=0)
    crawl_day_entry = tk.Entry(root)
    crawl_day_entry.grid(row=5, column=1)

    submit_button = tk.Button(root, text="Run Crawler", command=on_submit)
    submit_button.grid(row=6, columnspan=2)

    root.mainloop()

if __name__ == "__main__":
    main()



