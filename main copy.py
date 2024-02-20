import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pytube import YouTube
from PIL import ImageTk, Image
from io import BytesIO
import requests, threading, re, textwrap, webbrowser
import os


lista_links = []
lista_links_concluidos = []
pasta_destino = ""

def adicionar_link():
    link = entry_link.get()
    if link == "":
        mostrar_alerta("Insira um link para download.")
    else:
        try:
            video = YouTube(link)
            thumbnail = obter_thumbnail(link)
            lista_links.insert(0, {"titulo": video.title, "url": link, "thumbnail": thumbnail})
            atualizar_lista_links()
        except Exception:
            mostrar_alerta("Insira um link válido.")
            

def mostrar_alerta(msg):
    messagebox.showinfo("Alerta", msg)


def obter_thumbnail(link):
    video = YouTube(link)
    response = requests.get(video.thumbnail_url)
    thumbnail = Image.open(BytesIO(response.content))
    thumbnail = thumbnail.resize((70, 40), Image.LANCZOS)
    thumbnail = ImageTk.PhotoImage(thumbnail)
    return thumbnail

def excluir_link(index, frame):
    lista_links.pop(index)
    frame.destroy()
    atualizar_lista_links()

def selecionar_pasta_destino():
    global pasta_destino
    pasta_destino = filedialog.askdirectory()
    entry_caminho_salvar.delete(0, tk.END)
    entry_caminho_salvar.insert(0, pasta_destino)

def iniciar_download():
    thread_download = threading.Thread(target=download_links)
    thread_download.start()

def download_links():
    # Disable buttons during download
    botao_adicionar.config(state="disabled")
    botao_iniciar_download.config(state="disabled")
    botao_limpar_listas.config(state="disabled")

    
    links_pendentes = list(lista_links)  # Faz uma cópia da lista de links pendentes para evitar problemas durante o loop
    
    if(links_pendentes != []):
        for link in links_pendentes:
            video = YouTube(link['url'])
            titulo_video = video.title

            if entry_nome_arquivo.get():
                nome_arquivo = f"{entry_nome_arquivo.get()}_{titulo_video}" 
            else:
                nome_arquivo = f"{titulo_video}" 
            
            nome_arquivo = re.sub(r'[<>:"/\\|?*]', '', nome_arquivo)

            if escolha_saida.get() == 'Áudio':
                video.streams.filter(only_audio=True).first().download(output_path=pasta_destino, filename=nome_arquivo + ".mp3")

            elif escolha_saida.get() == 'Vídeo':
                # Escolher a stream de vídeo com resolução 720p, se disponível
                video_stream = video.streams.filter(res="720p", file_extension='mp4').first()
                if not video_stream:
                    # Se 720p não estiver disponível, escolher a melhor qualidade disponível
                    video_stream = video.streams.filter(progressive=True, file_extension='mp4').first()

                video_stream.download(output_path=pasta_destino, filename=nome_arquivo + ".mp4")

            lista_links_concluidos.append(link)
            lista_links.remove(link)
            janela.after(0, atualizar_lista_links)
    else: 
        mostrar_alerta("Adicione uma fila para fazer Download.")
    
    
    

    # Enable buttons after download
    botao_adicionar.config(state="normal")
    botao_iniciar_download.config(state="normal")
    botao_limpar_listas.config(state="normal")

def atualizar_lista_links():
    # Limpar os frames
    for widget in lista_pendentes_frame.winfo_children():
        widget.destroy()

    for widget in lista_concluidos_frame.winfo_children():
        widget.destroy()

    # Atualizar o frame "Download Pendente"
    for i, link in enumerate(lista_links):
        frame = tk.Frame(lista_pendentes_frame, bd=0, relief=tk.SOLID)
        frame.pack(anchor=tk.W, pady=0)

        thumbnail_label = tk.Label(frame, image=link['thumbnail'])
        thumbnail_label.image = link['thumbnail']
        thumbnail_label.pack(side=tk.LEFT)

        # Limitar o título em duas linhas e adicionar reticências
        wrapped_title = textwrap.shorten(link['titulo'], width=30, placeholder="...")
        title_label = tk.Label(frame, text=wrapped_title, padx=10, wraplength=280)
        title_label.pack(side=tk.LEFT)

        excluir_button = tk.Button(frame, text="Excluir", bg='#ce390a', fg="white", borderwidth=0,
                                   command=lambda i=i, frame=frame: excluir_link(i, frame))
        excluir_button.pack(side=tk.RIGHT, anchor='e')

    # Atualizar o frame "Download Concluído"
    for i, link in enumerate(lista_links_concluidos):
        frame = tk.Frame(lista_concluidos_frame, bd=0, relief=tk.SOLID)
        frame.pack(anchor=tk.W, pady=0)

        thumbnail_label = tk.Label(frame, image=link['thumbnail'])
        thumbnail_label.image = link['thumbnail']
        thumbnail_label.pack(side=tk.LEFT)

        # Limitar o título em duas linhas e adicionar reticências
        wrapped_title = textwrap.shorten(link['titulo'], width=30, placeholder="...")
        title_label = tk.Label(frame, text=wrapped_title, padx=10, wraplength=280)
        title_label.pack(side=tk.LEFT)

def show_full_title(event, title):
    event.widget['text'] = title

def hide_full_title(event):
    wrapped_title = textwrap.shorten(event.widget['text'], width=30, placeholder="...")
    event.widget['text'] = wrapped_title

def limpar_listas():
    resposta = messagebox.askyesno("Limpar Listas", "Tem certeza de que deseja limpar as listas?")
    if resposta:
        lista_links.clear()
        lista_links_concluidos.clear()
        atualizar_lista_links()

janela = tk.Tk()
janela.title("Youtube Capture")
janela.resizable(False, False)
janela.configure(bg='darkgray')
# Define o tamanho da janela
janela.geometry("600x420")
janela.attributes('-alpha', 1)



# Criar as abas
abas = ttk.Notebook(janela)
aba_pagina_inicial = ttk.Frame(abas)
aba_configuracoes = ttk.Frame(abas)
aba_sobre = ttk.Frame(abas)
abas.add(aba_pagina_inicial, text="Página Inicial")
abas.add(aba_configuracoes, text="Configurações")
abas.add(aba_sobre, text="Sobre")
abas.pack(expand=True, fill="both")

# Conteúdo da aba "Página Inicial"
frame_link = ttk.Frame(aba_pagina_inicial)
frame_link.pack(pady=10)

textplaceholder = "Insira o Link do Video aqui"

entry_link = tk.Entry(frame_link, width=70)
entry_link.insert(0, textplaceholder)
entry_link.configure(foreground='gray')  # Define a cor do texto para cinza

def on_entry_click(event):
    if entry_link.get() == textplaceholder:
        entry_link.delete(0, tk.END)  # Remove o texto atual
        entry_link.configure(foreground='black')  # Altera a cor do texto para preto

def on_focusout(event):
    if entry_link.get() == "":
        entry_link.insert(0, textplaceholder)
        entry_link.configure(foreground='gray')  # Altera a cor do texto para cinza

entry_link.bind('<FocusIn>', on_entry_click)
entry_link.bind('<FocusOut>', on_focusout)

entry_link.pack(side=tk.LEFT, padx=10)

frame_botoes = ttk.Frame(aba_pagina_inicial)
frame_botoes.pack(pady=10)

# Cria um estilo personalizado para o botão
style = ttk.Style()
style.configure("RoundedButton.TButton", borderwidth=0, relief="flat", foreground="white", bordercolor="white", borderradius=10)

def limpar_entry_link():
    entry_link.delete(0, tk.END)  # Remove o texto atual
    
botao_adicionar = tk.Button(frame_botoes, cursor="hand2", text="ADICIONAR", bg='#e23e0a', fg="#fff", borderwidth=0, font=("Arial", 10, 'bold'), command=lambda: [adicionar_link(), limpar_entry_link()], padx=10, pady=5, activebackground='#ff6f00', activeforeground='#fff')
botao_adicionar.pack(side=tk.LEFT, padx=10)

botao_iniciar_download = tk.Button(frame_botoes, cursor="hand2", text="INICIAR DOWNLOAD", bg='green', fg="#fff", borderwidth=0, font=("Arial", 10, 'bold'), command=iniciar_download, padx=10, pady=5, activebackground='#1b5e20', activeforeground='#fff')
botao_iniciar_download.pack(side=tk.LEFT, padx=10)

botao_limpar_listas = tk.Button(frame_botoes, cursor="hand2", text="LIMPAR LISTAS", bg='#222', fg="#fff", borderwidth=0, font=("Arial", 10, 'bold'), command=limpar_listas, padx=10, pady=5, activebackground='#424242', activeforeground='#fff')
botao_limpar_listas.pack(side=tk.LEFT, padx=10)

lista_pendentes_frame = ttk.Labelframe(aba_pagina_inicial, text="Download Pendente", width=300)
lista_pendentes_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

lista_concluidos_frame = ttk.Labelframe(aba_pagina_inicial, text="Download Concluído", width=300)
lista_concluidos_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

# Conteúdo da aba "Configurações"
frame_configuracoes = ttk.Frame(aba_configuracoes)
frame_configuracoes.pack(pady=10)

label_caminho_salvar = tk.Label(frame_configuracoes, text="Caminho de Salvamento:")
label_caminho_salvar.pack()


caminho_documentos = os.path.join(os.path.expanduser('~'), 'Music')

entry_caminho_salvar = tk.Entry(frame_configuracoes, width=50)
entry_caminho_salvar.insert(tk.END, caminho_documentos)  # Inserir "teste" como texto padrão
entry_caminho_salvar.pack()

botao_selecionar_pasta = tk.Button(frame_configuracoes, text="Selecionar Pasta", bg='#e23e0a', fg="#fff", borderwidth=0, font=("Arial", 10, 'bold'), command=selecionar_pasta_destino, padx=10, pady=5)
botao_selecionar_pasta.pack(padx=10, pady=10)


label_saida = tk.Label(frame_configuracoes, text="Saída:")
label_saida.pack()

escolha_saida = tk.StringVar(value="Áudio")

radio_audio = tk.Radiobutton(frame_configuracoes, text="Áudio", variable=escolha_saida, value="Áudio")
radio_audio.pack()

radio_video = tk.Radiobutton(frame_configuracoes, text="Vídeo", variable=escolha_saida, value="Vídeo")
radio_video.pack()

label_renomear = tk.Label(frame_configuracoes, text="Assinatura Arquivo:")
label_renomear.pack()

entry_nome_arquivo = tk.Entry(frame_configuracoes, width=50)
entry_nome_arquivo.pack()

# Conteúdo da aba "Sobre"
frame_sobre = ttk.Frame(aba_sobre)
frame_sobre.pack(pady=10)

label_insta = ttk.Label(frame_sobre, text="instagram.com/matias8523", cursor="hand2")
label_insta.pack()
label_insta.bind("<Button-1>", lambda event: webbrowser.open_new("https://instagram.com/matias8523"))

label_github = ttk.Label(frame_sobre, text="github.com/RafaelMendesMatias", cursor="hand2")
label_github.pack()
label_github.bind("<Button-1>", lambda event: webbrowser.open_new("https://github.com/RafaelMendesMatias"))


janela.mainloop()