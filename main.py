import os
from time import sleep
import datetime as dt
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import exceptions
import re
import pygame
import tkinter as tk
from tkinter import messagebox

SITE = "https://arxiv.org/"
DEFAULT_SOURCE_PATH = '/Users/username/Downloads'
DESTINATION_PATH = '/Users/username/Desktop/test'
MONTHS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
}
WEEKDAYS = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun"
}


def play_sound():
    pygame.init()
    pygame.mixer.init()

    try:
        sound = pygame.mixer.Sound("y2228.wav")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))
    except pygame.error as e:
        print(f"Error playing sound: {e}")
    finally:
        pygame.mixer.quit()
        pygame.quit()


# check if there is any illegal characters
def sanitize_filename(filename):
    illegal_characters = r'[\/:*?"<>|]'
    sanitized_filename = re.sub(illegal_characters, ' ', filename)
    return sanitized_filename


today = dt.datetime.today()
year = today.year
mon = MONTHS[today.month]
day = today.day
weekday = WEEKDAYS[today.weekday()]
date_for_archive = f"{weekday}, {day} {mon} {year}"

options = webdriver.ChromeOptions()
options.add_experimental_option('prefs', {
    "download.prompt_for_download": False,  # To auto download the file
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True  # It will not show PDF directly in chrome
})
browser = webdriver.Chrome(options=options)
browser.minimize_window()
browser.get(SITE)

optics = browser.find_element(By.ID, "physics.optics")
optics.click()
# to see if today's paper has been updated
try:
    h3_today = browser.find_element(By.XPATH, f"//h3[contains(text(),'{date_for_archive}')]")
except exceptions.NoSuchElementException:
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Error", "Not updated yet.")
    root.destroy()
else:
    dl_element = h3_today.find_element(By.XPATH, "following-sibling::*")
    dt_elements = dl_element.find_elements(By.XPATH, './/dt')

    # prepare to rename files
    rename_dict = {}
    for dt_element in dt_elements:
        title_a = dt_element.find_element(By.XPATH, './/span/a[@title="Abstract"]')
        old_title = title_a.text
        old_title = old_title[len('arXiv:'):]
        dd_element = dt_element.find_element(By.XPATH, "following-sibling::*")
        title_div = dd_element.find_element(By.XPATH, './/div/div[1]')
        title = title_div.text
        title = sanitize_filename(title)
        rename_dict[old_title] = title

    pdf_download_btns = dl_element.find_elements(By.XPATH, './/a[text()="pdf"]')
    for pdf_download in pdf_download_btns:
        pdf_download.click()
        sleep(1)
    sleep(60)

    # rename the file and move it to new directory
    new_folder_name = sanitize_filename(str(today))  # name of new folder
    new_folder_path = os.path.join(DESTINATION_PATH, new_folder_name)

    # use os.makedirs() to create a new folder（if not exist）
    os.makedirs(new_folder_path, exist_ok=True)

    for old_name, new_name in rename_dict.items():
        downloading = True
        while downloading:
            try:
                source_path = os.path.join(DEFAULT_SOURCE_PATH, f'{old_name}.pdf')
            except FileNotFoundError:
                sleep(5)
            else:
                downloading = False
                destination_path = os.path.join(new_folder_path, f'{new_name}.pdf')
                shutil.move(source_path, destination_path)
                sleep(5)
                # check if all works have been done
                file_list = os.listdir(new_folder_path)
                if len(file_list) == len(rename_dict):
                    play_sound()
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showinfo("Finish", "Download finished.")
                    root.destroy()
                    browser.quit()
