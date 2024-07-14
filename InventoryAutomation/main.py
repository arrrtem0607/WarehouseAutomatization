import pandas as pd
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os
import logging
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageTk

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Определение специальных штрихкодов для действий
EXPORT_DATA_BARCODE = "EXPORT123"
CLEAR_DATA_BARCODE = "CLEAR123"


# Функция для создания и отображения штрихкодов
def create_barcode(data, filename):
    barcode = Code128(data, writer=ImageWriter())
    barcode.save(filename)


def display_barcodes():
    export_image = Image.open("export_barcode.png")
    clear_image = Image.open("clear_barcode.png")
    export_photo = ImageTk.PhotoImage(export_image)
    clear_photo = ImageTk.PhotoImage(clear_image)

    export_label = ttk.Label(frame, image=export_photo)
    export_label.image = export_photo
    export_label.grid(row=3, column=0, pady=10)

    clear_label = ttk.Label(frame, image=clear_photo)
    clear_label.image = clear_photo
    clear_label.grid(row=3, column=1, pady=10)


# Функция для добавления товара в таблицу и обновления DataFrame
def add_item(barcode, name, quantity):
    global df
    logging.debug(f"Adding item: {barcode}, {name}, {quantity}")
    if barcode in df['Штрихкод'].values:
        df.loc[df['Штрихкод'] == barcode, 'Количество'] += quantity
    else:
        new_row = pd.DataFrame({'Штрихкод': [barcode], 'Название товара': [name], 'Количество': [quantity]})
        df = pd.concat([df, new_row], ignore_index=True)
    update_table()


def update_table():
    for row in tree.get_children():
        tree.delete(row)
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))
    logging.debug("Table updated")


def request_product_name(barcode):
    logging.debug(f"Requesting product name for barcode: {barcode}")
    name = simpledialog.askstring("Название товара", "Введите название товара для нового штрихкода:")
    if name:
        add_item(barcode, name, 1)
        new_product = pd.DataFrame({'Штрихкод': [barcode], 'Название товара': [name]})
        global products
        products = pd.concat([products, new_product], ignore_index=True)
        products.to_csv('products.csv', index=False)
    barcode_var.set('')
    root.after(100, lambda: barcode_entry.focus())


def scan_barcode(event=None):
    barcode = barcode_var.get().strip()
    logging.debug(f"Scanned barcode: {barcode}")
    if barcode:
        if barcode == EXPORT_DATA_BARCODE:
            export_data()
        elif barcode == CLEAR_DATA_BARCODE:
            clear_data()
        elif barcode in products['Штрихкод'].values:
            add_item(barcode, products.loc[products['Штрихкод'] == barcode, 'Название товара'].values[0], 1)
        else:
            root.after(100, request_product_name, barcode)  # Используем after для вызова диалога
        barcode_var.set('')
        root.after(100, lambda: barcode_entry.focus())


def export_data():
    df.to_csv('inventory.csv', index=False)
    messagebox.showinfo("Экспорт данных", "Данные успешно экспортированы в файл inventory.csv")
    logging.debug("Data exported")
    root.after(100, lambda: barcode_entry.focus())


def load_data():
    global df, products
    if os.path.exists('inventory.csv'):
        df = pd.read_csv('inventory.csv')
        update_table()
    if os.path.exists('products.csv'):
        products = pd.read_csv('products.csv')
    else:
        products = pd.DataFrame(columns=['Штрихкод', 'Название товара'])
    logging.debug("Data loaded")


def on_closing():
    df.to_csv('inventory.csv', index=False)
    root.destroy()
    logging.debug("Application closed")


def clear_data():
    global df
    if messagebox.askokcancel("Очистка данных",
                              "Вы уверены, что хотите начать новую инвентаризацию? Все текущие данные будут удалены."):
        df = pd.DataFrame(columns=['Штрихкод', 'Название товара', 'Количество'])
        update_table()
        messagebox.showinfo("Очистка данных",
                            "Данные текущей инвентаризации очищены. Вы можете начать новую инвентаризацию.")
        logging.debug("Data cleared")
        root.after(100, lambda: barcode_entry.focus())


# Создаем или загружаем DataFrame для инвентаризации и продуктов
df = pd.DataFrame(columns=['Штрихкод', 'Название товара', 'Количество'])
products = pd.DataFrame(columns=['Штрихкод', 'Название товара'])

# Интерфейс пользователя
root = tk.Tk()
root.title("Инвентаризация склада")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

barcode_label = ttk.Label(frame, text="Сканируйте штрихкод:")
barcode_label.grid(row=0, column=0, sticky=tk.W)
barcode_var = tk.StringVar()
barcode_entry = ttk.Entry(frame, textvariable=barcode_var)
barcode_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
barcode_entry.bind("<Return>", scan_barcode)
barcode_entry.focus()

columns = ["Штрихкод", "Название товара", "Количество"]
tree = ttk.Treeview(frame, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
tree.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

export_button = ttk.Button(frame, text="Экспорт данных", command=export_data)
export_button.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

clear_button = ttk.Button(frame, text="Новая инвентаризация", command=clear_data)
clear_button.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

# Создаем штрихкоды для действий
create_barcode(EXPORT_DATA_BARCODE, "export_barcode")
create_barcode(CLEAR_DATA_BARCODE, "clear_barcode")

# Отображаем штрихкоды на экране
display_barcodes()

load_data()

root.protocol("WM_DELETE_WINDOW", on_closing)

update_table()

root.mainloop()
