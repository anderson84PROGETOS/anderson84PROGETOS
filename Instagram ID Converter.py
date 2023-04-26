import tkinter as tk
import instaloader


# Função para converter nome de usuário em ID de usuário
def username_to_userid():
    username = username_entry.get()
    L = instaloader.Instaloader()
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        result_label.config(text=f'User ID: {profile.userid}')
    except:
        result_label.config(text='User not found!')

# Função para converter ID de usuário em nome de usuário
def userid_to_username():
    userid = userid_entry.get()
    L = instaloader.Instaloader()
    try:
        profile = instaloader.Profile.from_id(L.context, int(userid))
        result_label.config(text=f'Username: {profile.username}')
    except:
        result_label.config(text='User not found!')

# Cria a interface gráfica
root = tk.Tk()
root.geometry('400x500')
root.title('Instagram ID Converter')

# Cria um campo de entrada para o nome de usuário
username_entry = tk.Entry(root, width=30)
username_entry.pack(pady=10)

# Cria um botão para converter o nome de usuário em ID de usuário
convert_button = tk.Button(root, text='Convert to ID', command=username_to_userid)
convert_button.pack(pady=10)

# Adiciona mais espaço entre os botões
tk.Label(root, text='').pack()

# Cria um campo de entrada para o ID de usuário
userid_entry = tk.Entry(root, width=30)
userid_entry.pack(pady=10)

# Cria um botão para converter o ID de usuário em nome de usuário
convert_button2 = tk.Button(root, text='Convert to Username', command=userid_to_username)
convert_button2.pack(pady=10)
# Adiciona mais espaço entre os botões
tk.Label(root, text='').pack()

# Cria uma label para exibir o resultado
result_label = tk.Label(root, text='')
result_label.pack(pady=10)

# copiar o resultado
def copy_to_clipboard():
    root.clipboard_clear()
    root.clipboard_append(result_label.cget('text'))

# Adiciona mais espaço entre os botões
tk.Label(root, text='').pack()
tk.Label(root, text='').pack()
tk.Label(root, text='').pack()
tk.Label(root, text='').pack()
tk.Label(root, text='').pack()
tk.Label(root, text='').pack()

copy_button = tk.Button(root, text='click copy result', command=copy_to_clipboard)
copy_button.pack(pady=10)

root.mainloop()
