from tkinter import *
from tkinter import ttk
from bs4 import BeautifulSoup
import requests
import requests.exceptions
import urllib.parse
from collections import deque
import re

class ScraperGUI:
    def __init__(self, master):
        self.master = master
        master.title("Web Scraper")
        self.progress_var = DoubleVar()
        
        self.url_label = ttk.Label(master, text="Insira o URL de destino a ser verificado [https://example.com]")
        self.url_label.grid(row=0, column=0, padx=5, pady=5, sticky=W)
        
        self.url_entry = ttk.Entry(master, width=80)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)
        
        self.scrape_button = ttk.Button(master, text="Scrape", command=self.scrape)
        self.scrape_button.grid(row=0, column=2, padx=5, pady=5, sticky=W)        

        self.emails_label = ttk.Label(master, text="Emails encontrados")
        self.emails_label.grid(row=1, column=0, padx=5, pady=5, sticky=W)
        
        self.emails_listbox = Listbox(master, width=160, height=40)
        self.emails_listbox.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=W)
        
        self.progressbar = ttk.Progressbar(master, orient=HORIZONTAL, length=300, mode='determinate', variable=self.progress_var)
        self.progressbar.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky=W)
        self.progressbar.grid_remove()
        
        self.copy_button = ttk.Button(master, text="Copiar resultados", command=self.copy_results)
        self.copy_button.grid(row=3, column=2, padx=5, pady=5, sticky=E)

    def copy_results(self):
        results = "\n".join(self.emails_listbox.get(0, END))
        self.master.clipboard_clear()
        self.master.clipboard_append(results)    


    def scrape(self):
        self.progressbar.grid()
        self.progress_var.set(0)
        
        user_url = self.url_entry.get()
        urls = deque([user_url])
        scrapped_urls = set()
        emails = set()
        count = 0
        
        while len(urls):
            count += 1
            if count == 100:
                break
            url = urls.popleft()
            scrapped_urls.add(url)
            parts = urllib.parse.urlsplit(url)
            base_url = '{0.scheme}://{0.netloc}'.format(parts)
            path = url[:url.rfind('/')+1] if '/' in parts.path else url
            
            try:
                response = requests.get(url)
            except(requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
                continue
                
            new_emails = set(re.findall(r'[a-z0-9\. \-+_]+@[a-z0-9\. \-+_]+\.[a-z]+', response.text, re.I))
            emails.update(new_emails)
            
            soup = BeautifulSoup(response.text, features="html.parser")
            
            for anchor in soup.find_all("a"):
                link = anchor.attrs['href'] if 'href' in anchor.attrs else ''
                if link.startswith('/'):
                    link = base_url + link
                elif not link.startswith('http'):
                    link = path + link
                if not link in urls and not link in scrapped_urls:
                    urls.append(link)
            
            progress_percent = min(100, count)  # limita o valor máximo para 100
            self.progress_var.set(progress_percent)
            self.master.update_idletasks()

        self.emails_listbox.delete(0, END)
        for mail in emails:
            self.emails_listbox.insert(END, mail)

root = Tk()
root.wm_state('zoomed')
scraper_gui = ScraperGUI(root)
root.mainloop()
