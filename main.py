import tkinter as tk
from dostoevsky.tokenization import RegexTokenizer
from dostoevsky.models import FastTextSocialNetworkModel
from tkinter import * 
from tkinter import messagebox
from tkinter import ttk
import requests
import json
import re
from bs4 import BeautifulSoup
from transformers import pipeline

# Инициализация модели для генерации ключевых слов
nlp = pipeline("text2text-generation", model="t5-base")


root = Tk()

# Функция оценки тональности текста

def analyze_sentiments():
    labelOutputTone.delete(1.0, tk.END)
    messages = labelInputTone.get("1.0", "end").strip().split("\n")
    
    tokenizer = RegexTokenizer()
    model = FastTextSocialNetworkModel(tokenizer=tokenizer)

    results = model.predict(messages, k=2)
    for message, sentiment in zip(messages, results):
        labelOutputTone.insert("end", f"{message} -> {sentiment}\n")

# Функция поиска по форумам
def forum_search():
    link = linkInput.get()
    words = wordsInput.get()

    # Загружаем список слов из файла пользователя
    # with open('words.txt', 'r') as f:
    #     words = [word.strip() for word in f.readlines()]

    # Отправляем запрос на форум и получаем HTML-код страницы
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим все сообщения на форуме
    messages = soup.find_all('article', {'class': 'message'})

    # Открываем файл для записи результатов
    with open('forum_search_results.txt', 'w') as f:
        found_links = []
        for message in messages:
            # Проверяем, содержит ли сообщение какое-либо из слов
            for word in words:
                if word in message.text:
                    # Если слово найдено, сохраняем ссылку на сообщение
                    message_link = message.find('a', {'class': 'message-attribution-gadget'})['href']
                    found_links.append(message_link)
                    break
        if found_links:
            labelOutput.config(text="\n".join(found_links))
            f.write("\n".join(found_links))
        else:
            labelOutput.config(text="Ничего не найдено.")
            f.write("Ничего не найдено.") 

    status_label.config(text="Поиск выполнен успешно!")


# Функция преобразования ссылки в числовое значение

def convert_group_link_to_id(vk_group_link, access_token):
    # Извлекаем название группы из ссылки
    match = re.search(r'vk.com/([\w\.]+)', vk_group_link)
    group_name = match.group(1)
    
    # Получаем ID группы по ее названию
    params = {
        'group_id': group_name,
        'access_token': access_token,
        'v': '5.131'
    }
    response = requests.get('https://api.vk.com/method/groups.getById', params=params)
    group_info = json.loads(response.text)['response'][0]
    
    # Возвращаем ID группы в числовом формате
    return str(group_info['id'])


# Функция поиска по vk.com
def vk_search():

    # API vk.com
    access_token = '' # ключ доступа, полученный при регистрации приложения

    # Получение введенных пользователем данных

    linkKeywordVk = linkKeywordVkInput.get()
    vk_group_link = linkPostVkInput.get()
          
    # Вызов функции преобразования ссылки в числовое значение

    vk_group_id = convert_group_link_to_id(vk_group_link, access_token)
    linkResultVk = '-' + vk_group_id

    # Выполнение поиска

    keywords =  linkKeywordVk # ключевые слова для поиска
    count = 10 # количество результатов для вывода
    api_version = '5.131' # версия API Vk

    group_id = linkResultVk # id группы, в которой будем искать посты (- перед числом указывает, что это отрицательное число)

    url = 'https://api.vk.com/method/wall.search?owner_id={}&query={}&count={}&access_token={}&v={}'.format(group_id, keywords, count, access_token, api_version)

    response = requests.get(url)
    result = json.loads(response.text)

    filename = 'vk_search_result.txt'  # название файла, в который будут сохранены результаты
    with open(filename, 'w') as file:  # создаем файл и открываем его для записи
        if 'items' in result['response']:
            for item in result['response']['items']:
                link = 'https://vk.com/wall{}_{}\n'.format(item['owner_id'], item['id'])
                file.write(link)  # записываем ссылку на пост в файл
        else:
            print('Ошибка при выполнении запроса: ', result)
    links = open('vk_search_result.txt','r')
    labelOutput3.config(text="\n".join(links))
    status_label1.config(text="Поиск выполнен успешно!")

# Создаем функцию для поиска пользователя
def search_user():
    usernames = username_entry.get().split(",")
    platforms = platform_entry.get().split(",")
    proxy = proxy_entry.get()
    results = ""
    for username in map(str.strip, usernames):
        for platform in map(str.strip, platforms):
            url = platform.format(username)
            try:
                proxies = {"http": proxy, "https": proxy} if proxy else None
                response = requests.get(url, proxies=proxies)
                if response.status_code == 200:
                    if 'telegram' in platform:
                        data = response.json()
                        if data['ok'] and data['result']['type'] == 'supergroup':
                            results += f"Найден пользователь {username} в {platform}\n"
                        else:
                            results += f"Пользователь {username} не найден в {platform}\n"
                    else:
                        results += f"Найден пользователь {username} в {platform}\n"
                else:
                    results += f"Пользователь {username} не найден в {platform}\n"
            except requests.exceptions.RequestException as e:
                results += f"Не удалось подключиться к {platform} ({e})\n"
    # Сохраняем результаты в файл и выводим их в Label
    with open('Nickname_results.txt', "w") as f:
        f.write(results)
    label_results.config(text=results.strip())


# Функция для генерации ключевых слов и вывода результатов
def generate_keywords():
    # Выполнение генерации ключевых слов
    aiKeys = aiGenerateTextInput.get()
    keywords = nlp(aiKeys, max_length=50, min_length=10, num_return_sequences=1)
    # Очистка поля вывода и вывод результата
    labelOutputAi.delete(1.0, tk.END)
    labelOutputAi.configure(state=tk.NORMAL)
    labelOutputAi.insert(tk.END, keywords[0]['generated_text'])
    labelOutputAi.configure(state=tk.DISABLED)

# Настройки окна 
root ['bg'] = '#fafafa'
root. title("Flipper v1.4")
root.geometry ('710x600')
root.resizable(width=False, height=False)
root.attributes("-fullscreen", False)
# -*-

# Настройка вкладок
tab_control = ttk.Notebook(root)  
tab1 = ttk.Frame(tab_control)  
tab2 = ttk.Frame(tab_control)  
tab3 = ttk.Frame(tab_control) 
tab4 = ttk.Frame(tab_control) 
tab5 = ttk.Frame(tab_control) 
tab_control.add(tab1, text='Поиск по форумам')  
tab_control.add(tab2, text='Поиск по vk.com')  
tab_control.add(tab3, text='Аналитика') 
tab_control.add(tab4, text='Генерация данных') 
tab_control.add(tab5, text='Тональность') 

# Настройка параметров первой вкладки

lbl1 = Label(tab1)  
lbl1.grid(column=0, row=0)  

# Настройка параметров второй вкладки

lbl2 = Label(tab2)  
lbl2.grid(column=0, row=0)  
tab_control.pack(expand=1, fill='both')  

# Настройка параметров третьей вкладки

lbl3 = Label(tab3)  
lbl3.grid(column=0, row=0)  
tab_control.pack(expand=1, fill='both')  

# Настройка параметров четвертой вкладки

lbl4 = Label(tab4)  
lbl4.grid(column=0, row=0)  
tab_control.pack(expand=1, fill='both')  

# Настройка параметров пятой вкладки

lbl5 = Label(tab5)  
lbl5.grid(column=0, row=0)  
tab_control.pack(expand=1, fill='both')  


# Настройка элементов
# Поиск по форумам
frame1 = Frame(lbl1)
frame1.pack(fill='both', pady=10)
lwords = Label(frame1, text='Ключевые слова:', font=('Arial', 16))
lwords.pack(side=LEFT)
wordsInput = Entry(frame1, bg='white', width=52)
wordsInput.pack(side=RIGHT, padx=10)
frame = Frame(lbl1)
frame.pack(fill='both', pady=10)
lbfs = Label(frame, text='Ссылка на форум:', font=('Arial', 16))
lbfs.pack(side=LEFT)
linkInput = Entry(frame, bg='white', width=36)
linkInput.pack(side=LEFT, padx=10)
btnFirst = Button(frame, text='Поиск', bg='yellow', command=forum_search, width=10)
btnFirst.pack(side=RIGHT, padx=9)
status_label = Label(lbl1, padx=100, text='', anchor='w', justify='center')
status_label.pack(fill='x')
title = Label(lbl1, text='Результаты поиска:', justify='left', font=('Arial', 16))
title.pack(pady=10)
frame2 = Frame(lbl1)
frame2.pack(fill='both', pady=10)
canvas = Canvas(frame2)
canvas.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar = Scrollbar(frame2, command=canvas.yview)
scrollbar.pack(side=RIGHT, fill=Y)
canvas.config(yscrollcommand=scrollbar.set)
canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
labelOutput = Label(canvas, padx=100, font=('Arial', 14), justify='center', anchor='nw', height=50)
labelOutput.pack(fill='both', expand=True)
canvas.create_window((0,0), window=labelOutput, anchor="nw")
title = Label(lbl1, justify='left', text='Данное ПО позволяет выполнить поиск по ключевым словам\nна указанномпользователем форуме.\nДля начала работы введите ссылку в поле "Ссылка:"\nи нажмите кнопку "Поиск".\nКак только ПО закончит работу, вы увидите\nв поле "Результаты:"список постов,\nсодержащих указанное ключевое слово.\nВ случае ошибок в работе ПО обращаться в Telegram - @ricardosql', font=('Arial', 16))
title.pack()


# Поиск по vk.com
frame2 = Frame(lbl2)
frame2.pack(fill='both', pady=10)
linkKeywordVkText  = Label(frame2, text='Ключевые слова:', font=('Arial', 16))
linkKeywordVkText.pack(side=LEFT)
linkKeywordVkInput = Entry(frame2, bg='white', width=48)
linkKeywordVkInput.pack(side=LEFT, padx=57)
frame3 = Frame(lbl2)
frame3.pack(fill='both', pady=10)
lbfsVk = Label(frame3, text='Ссылка на сообщество:', font=('Arial', 16))
lbfsVk.pack(side=LEFT)
linkPostVkInput = Entry(frame3, bg='white', width=32)
linkPostVkInput.pack(side=LEFT, padx=7)
btnS = Button(frame3, text='Поиск', bg='yellow', command=vk_search, width=10)
btnS.pack(side=LEFT, padx=16)
status_label1 = Label(lbl2, padx=260, text='', anchor='w', justify='center')
status_label1.pack(fill='x')
titleV = Label(lbl2, text='Результаты поиска:', justify='left', font=('Arial', 16))
titleV.pack(pady=10)
frame4 = Frame(lbl2)
frame4.pack(fill='both', pady=10)
labelOutput3 = Label(frame4, padx=220, font=('Arial', 14), justify='center', anchor='nw', height=14)
labelOutput3.pack(fill='both', expand=True)
titleVK = Label(lbl2, justify='left', text='Данное ПО позволяет выполнить поиск по ключевым словам в указанном\nпользователем сообществе vk.com. Для начала работы введите ссылку в поле\n"Ссылка:" и нажмите кнопку "Поиск". Как только ПО закончит работу, вы\nувидите в поле "Результаты:"список постов и комментариев,\nсодержащих указанное ключевое слово.\nВ случае ошибок в работе ПО обращаться в Telegram - @ricardosql', font=('Arial', 16))
titleVK.pack(pady=10)

# Аналитика
username_frame = Frame(lbl3)
username_frame.pack(side=TOP, fill=BOTH)
username_label = Label(username_frame, text="Введите никнеймы (через запятую):")
username_label.pack(side=LEFT)
username_entry = Entry(username_frame, width=45)
username_entry.pack(side=LEFT, expand=YES, fill=X)

# Поле для ввода списка ресурсов
platform_frame = Frame(lbl3)
platform_frame.pack(side=TOP, fill=X)
platform_label = Label(platform_frame, text="Введите список ресурсов (через запятую):")
platform_label.pack(side=LEFT)
platform_entry = Entry(platform_frame, width=22)
platform_entry.pack(side=LEFT, expand=YES, fill=X)

# Поле для ввода прокси
proxy_frame = Frame(lbl3)
proxy_frame.pack(side=TOP, fill=X)
proxy_label = Label(proxy_frame, text="Введите прокси (если не требуется, оставьте пустым):")
proxy_label.pack(side=LEFT)
proxy_entry = Entry(proxy_frame)
proxy_entry.pack(side=LEFT, expand=YES, fill=X)

# Поле для выбора пола
proxy_gender_frame = Frame(lbl3)
proxy_gender_frame.pack(side=TOP, fill=X)

# Радиокнопки выбора ппараметров
gender_label = Label(proxy_gender_frame, text="Выберите предполагаемый пол объекта поиска:")
gender_label.pack(side=LEFT)
gender_var = StringVar()
male_radio = Radiobutton(proxy_gender_frame, text="Мужской", variable=gender_var, value="male")
male_radio.pack(side=LEFT)
female_radio = Radiobutton(proxy_gender_frame, text="Женский", variable=gender_var, value="female")
female_radio.pack(side=LEFT)

# Кнопки и Label для отображения результатов
search_button = Button(lbl3, text="Поиск", command=search_user)
search_button.pack()
titleA = Label(lbl3, text='Результаты поиска:', justify='left', font=('Arial', 16))
titleA.pack(pady=1)
frame5 = Frame(lbl3)
frame5.pack(fill='both', pady=2)
canvas = Canvas(frame5)
canvas.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar = Scrollbar(frame5, command=canvas.yview)
scrollbar.pack(side=RIGHT, fill=Y)
canvas.config(yscrollcommand=scrollbar.set)
canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
label_results = Label(canvas, padx=100, font=('Arial', 14), justify='left', anchor='nw')
label_results.pack(fill='both', expand=True)
canvas.create_window((0,0), window=label_results, anchor="nw")
titleA = Label(lbl3, justify='left', text='Данное ПО позволяет выполнить поиск по никнейму в указанных социальных сетях\nи мессенджерах.Для начала работы введите через запятую никнеймы.Затем введите\nчерез запятую список ресурсов в формате "https://t.me/{}". Если необходимо\nвыполнить поиск по запрещенным на территории РФ ресурсам,то введите прокси\nв формате "IP:PORT" Нажмите кнопку "Поиск".В поле "Результаты:" будет\nобозначение о наличии страницы пользователя в указанном ресурсе.\n В поле выбора параметров укажите предполагаемый пол.\n Результаты также сохраняются в файл. В случае ошибок в работе ПО\nобращаться в Telegram - @ricardosql', font=('Arial', 16))
titleA.pack()

# Генерация данных
frame5 = Frame(lbl4)
frame5.pack(fill='both', pady=10)
aiGenerateText  = Label(frame5, text='Введите текст:', font=('Arial', 16))
aiGenerateText.pack(side=LEFT)
aiGenerateTextInput = Entry(frame5, bg='white', width=40)
aiGenerateTextInput.pack(side=LEFT, padx=18)
btnAi = Button(frame5, text='Генерировать', bg='yellow', command=generate_keywords, width=10)
btnAi.pack()
titleAi = Label(lbl4, text='Результаты:', justify='left', font=('Arial', 16))
titleAi.pack(pady=10)
frame6 = Frame(lbl4)
frame6.pack(fill='both', pady=10)
labelOutputAi = Text(frame6, font=('Arial', 14), height=20)
labelOutputAi.pack(fill='both', expand=True, pady=10)
titleAi = Label(lbl4, justify='left', text='Данное ПО позволяет выполнить генерацию новых слов и выражений\nна основе введенных. Для начала работы введите текст в поле\n"Введите текст:" и нажмите кнопку "Генерировать". Как только ПО закончит работу, вы\nувидите в поле "Результаты:"список сгенерированных слов.\nВ случае ошибок в работе ПО обращаться в Telegram - @ricardosql', font=('Arial', 16))
titleAi.pack()

# Тональность
frame7 = Frame(lbl5)
frame7.pack(fill='both', pady=10)
toneGenerateText  = Label(frame7, text='Введите текст:', font=('Arial', 16))
toneGenerateText.pack()
labelInputTone = Text(frame7, font=('Arial', 14), height=8)
labelInputTone.pack(fill='both', expand=True, pady=5)
btnTone = Button(frame7, text='Анализировать', bg='yellow', command=analyze_sentiments, width=10)
btnTone.pack(pady=10)
titleTone = Label(lbl5, text='Результаты:', justify='left', font=('Arial', 16))
titleTone.pack(pady=10)
frame8 = Frame(lbl5)
frame8.pack(fill='both', pady=5)
labelOutputTone = Text(frame8, font=('Arial', 14), height=8)
labelOutputTone.pack(fill='both', expand=True, pady=5)
titleTone = Label(lbl5, justify='left', text='Данное ПО позволяет выполнить анализ тональности слов и выражений\nна основе введенных. Для начала работы введите текст в поле\n"Введите текст:" и нажмите кнопку "Анализировать". Как только ПО закончит работу,\nвы увидите в поле "Результаты:"оценку тональности введенных данных.\nВ случае ошибок в работе ПО обращаться в Telegram - @ricardosql', font=('Arial', 16))
titleTone.pack()

# Окно вывода программы
icon = PhotoImage(file = "media/favicon.png")
root.iconphoto(False, icon)
root.mainloop()