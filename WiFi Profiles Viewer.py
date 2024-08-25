import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext

def save_to_file(ssid, profile_info):
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])

    if file_path:
        with open(file_path, 'a') as file:
            file.write(f"SSID: {ssid}\n")
            file.write(profile_info)

def save_all_to_file(profiles):
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])

    if file_path:
        with open(file_path, 'w') as file:
            for ssid, profile_info in profiles.items():
                file.write(f"SSID: {ssid}\n")
                file.write(profile_info)

def main():
    # Run the netsh command to get the list of WLAN profiles
    command_output = subprocess.check_output('netsh wlan show profiles', shell=True, universal_newlines=True)

    # Split the output into lines
    lines = command_output.split('\n')

    # Create the Tkinter window
    root = tk.Tk()
    root.wm_state('zoomed')
    root.title("WiFi Profiles Viewer")

    # Dictionary to store SSID and corresponding profile_info
    profiles = {}

    # Add a "Save All" button to save all profiles to a single file
    save_all_button = tk.Button(root, text="Save All", command=lambda: save_all_to_file(profiles), bg="#00FFFF")
    save_all_button.pack(side=tk.TOP, pady=10)  # Place the button at the top

    # Create a ScrolledText widget to display results
    text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=48, font=("Arial", 12))
    text_widget.pack()

    # Iterate through the lines, skipping the first 9 lines
    for line in lines[9:]:
        # Split each line into tokens using ':' as the delimiter
        tokens = line.split(':')

        # Extract the first two tokens
        if len(tokens) >= 2:
            profile_name = tokens[0].strip()
            ssid = tokens[1].strip()

            # Check if the SSID is not empty
            if ssid:
                text_widget.insert(tk.END, f"SSID: {ssid}\n")

                try:
                    # Run the netsh command to show the key for the current profile
                    profile_output = subprocess.check_output(f'netsh wlan show profiles name="{ssid}" key=clear', shell=True, universal_newlines=True)

                    # Display the profile information
                    text_widget.insert(tk.END, profile_output)

                    profiles[ssid] = profile_output  # Store in the dictionary

                except subprocess.CalledProcessError as e:
                    text_widget.insert(tk.END, f"Erro ao obter informações do perfil {ssid}.\n")
                    continue

    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
