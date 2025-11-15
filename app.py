# weather.py
import tkinter as tk
from tkinter import messagebox
import requests
from requests.exceptions import RequestException
import threading
import socket
import sys

# -----------------------
# CONFIG
# -----------------------
API_KEY = "04ee28ffa230c290908a1bb39f46b280"  # your API key
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT = 10  # seconds

# -----------------------
# Helper functions
# -----------------------
def get_weather_from_api(city: str):
    """Try to fetch weather from OpenWeather. Returns tuple (success_bool, data_or_error_message)."""
    url = f"{BASE_URL}?q={city}&appid={API_KEY}&units=metric"
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        try:
            body = resp.json()
        except ValueError:
            body = {"message": resp.text}

        if resp.status_code == 200:
            return True, body
        else:
            # Return API error message
            msg = body.get("message", f"HTTP {resp.status_code}")
            return False, f"API Error ({resp.status_code}): {msg}"
    except RequestException as e:
        # Network-related errors (DNS, timeout, connection refused, etc.)
        return False, f"Network error: {e}"

def make_mock_data(city: str):
    """Return a predictable mock response so UI still shows something."""
    return {
        "name": city.title(),
        "main": {"temp": 25.0, "humidity": 60},
        "weather": [{"description": "clear sky"}]
    }

# -----------------------
# GUI logic
# -----------------------
def update_result_text(text: str):
    """Safely update label text from any thread."""
    weather_label.config(text=text)

def format_weather_text(data: dict, note: str = ""):
    try:
        name = data.get("name", "Unknown")
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"].title()
        lines = [
            f"City: {name}",
            f"Temperature: {temp}°C",
            f"Humidity: {humidity}%",
            f"Weather: {description}",
        ]
        if note:
            lines.append("")  # blank line
            lines.append(note)
        return "\n".join(lines)
    except Exception as e:
        return f"Error parsing weather data: {e}"

def fetch_and_display(city: str):
    """Background thread worker: fetch weather and update UI."""
    city = city.strip()
    if not city:
        root.after(0, lambda: messagebox.showinfo("Info", "Please enter a city name."))
        return

    # Try API
    success, payload = get_weather_from_api(city)

    if success:
        text = format_weather_text(payload)
        # update UI on main thread
        root.after(0, lambda: update_result_text(text))
        print(f"[INFO] Weather fetched for {city}")
    else:
        # Print detailed error to terminal for debugging
        print(f"[ERROR] Could not fetch weather: {payload}", file=sys.stderr)

        # If it's a network/DNS issue (socket.gaierror or mention of name resolution), show mock
        low = str(payload).lower()
        if "getaddrinfo" in low or "name resolution" in low or "network error" in low or "failed to establish a new connection" in low:
            mock = make_mock_data(city)
            text = format_weather_text(mock, note="(Showing mock data because network/DNS error occurred.)")
            root.after(0, lambda: update_result_text(text))
            root.after(0, lambda: messagebox.showwarning("Network/DNS issue", f"Network/DNS error occurred.\nSee terminal for details.\nA mock result is shown in the UI."))
        else:
            # Show API error message to user
            root.after(0, lambda: update_result_text(f"Error: {payload}"))

def on_get_weather_clicked():
    city = city_entry.get()
    # start background thread
    thr = threading.Thread(target=fetch_and_display, args=(city,), daemon=True)
    thr.start()

def on_quit():
    root.destroy()

def on_test_dns():
    """Quick DNS test printed to terminal and shown in a small popup summary."""
    try:
        ip = socket.gethostbyname('api.openweathermap.org')
        msg = f"Resolved api.openweathermap.org → {ip}"
        print("[DNS TEST] " + msg)
        messagebox.showinfo("DNS Test", msg)
    except Exception as e:
        msg = f"DNS resolution failed: {e}"
        print("[DNS TEST] " + msg, file=sys.stderr)
        messagebox.showerror("DNS Test", msg)

# -----------------------
# Build GUI
# -----------------------
root = tk.Tk()
root.title("Weather App")
root.geometry("380x300")
root.resizable(False, False)

frame = tk.Frame(root, padx=12, pady=12)
frame.pack(fill="both", expand=True)

tk.Label(frame, text="Enter City Name:", anchor="w").pack(fill="x")
city_entry = tk.Entry(frame)
city_entry.pack(fill="x", pady=(4, 10))
city_entry.insert(0, "Bengaluru")  # default value

btn_frame = tk.Frame(frame)
btn_frame.pack(fill="x", pady=(0,10))

tk.Button(btn_frame, text="Get Weather", command=on_get_weather_clicked).pack(side="left", padx=(0,6))
tk.Button(btn_frame, text="Test DNS", command=on_test_dns).pack(side="left", padx=(0,6))
tk.Button(btn_frame, text="Quit", command=on_quit).pack(side="right")

weather_label = tk.Label(frame, text="Press 'Get Weather' to fetch data.", justify="left", anchor="nw", bd=1, relief="groove", padx=6, pady=6, wraplength=340)
weather_label.pack(fill="both", expand=True)

# Run the app
root.mainloop()
