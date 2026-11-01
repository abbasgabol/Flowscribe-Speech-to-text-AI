"""Lightweight native desktop presentation; no web runtime or extra UI dependencies."""
import tkinter as tk
from tkinter import ttk
from app_paths import FROZEN

BG = '#f5f4ef'
INK = '#203c35'
MUTED = '#67766f'
ACCENT = '#245c48'


def build(app, choices):
    root = app.root
    root.geometry('880x720')
    root.minsize(760, 660)
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background=BG, foreground=INK, font=('Segoe UI', 10))
    style.configure('TFrame', background=BG)
    style.configure('TLabel', background=BG)
    style.configure('Muted.TLabel', foreground=MUTED)
    style.configure('Title.TLabel', font=('Segoe UI Semibold', 25))
    style.configure('Section.TLabel', font=('Segoe UI Semibold', 13))
    style.configure('TButton', padding=(14, 9), background='#e6eae2', borderwidth=0)
    style.map('TButton', background=[('active', '#d8e2d6')])
    style.configure('Accent.TButton', background=ACCENT, foreground='white', padding=(22, 12))
    style.map('Accent.TButton', background=[('disabled', '#d7ddd5'), ('active', '#184735')],
              foreground=[('disabled', '#748276')])
    style.configure('TCheckbutton', padding=(0, 7))
    style.configure('TCombobox', padding=7, fieldbackground='white', arrowsize=16)
    style.configure('TNotebook', borderwidth=0)
    style.configure('Nav.TButton', background=BG, padding=(18, 9))
    style.configure('Selected.Nav.TButton', background='#e2e9db', foreground=ACCENT, padding=(18, 9))
    style.configure('TNotebook.Tab', padding=(20, 11), background='#e9ebe3')
    style.map('TNotebook.Tab', background=[('selected', BG)], foreground=[('selected', ACCENT)])
    style.configure('Treeview', background='white', fieldbackground='white', rowheight=32, borderwidth=0)
    style.configure('Treeview.Heading', font=('Segoe UI Semibold', 10), padding=8)

    shell = ttk.Frame(root, padding=(28, 22))
    shell.pack(fill='both', expand=True)
    header = ttk.Frame(shell)
    header.pack(fill='x')
    ttk.Label(header, text='Local Dictation', style='Title.TLabel').pack(side='left')
    tk.Label(header, text='●  ON YOUR DEVICE', bg='#e3ebdd', fg=ACCENT,
             font=('Segoe UI Semibold', 9), padx=12, pady=7).pack(side='right')
    ttk.Label(shell, text='A little less typing. A little more flow.', style='Muted.TLabel').pack(anchor='w', pady=(2, 20))

    nav = ttk.Frame(shell)
    nav.pack(fill='x', pady=(0, 4))
    pages = ttk.Frame(shell)
    pages.pack(fill='both', expand=True)
    dictate = ttk.Frame(pages, padding=(0, 18, 0, 0))
    settings = ttk.Frame(pages, padding=(12, 18))
    def select_page(page):
        for panel in (dictate, settings):
            panel.pack_forget()
        page.pack(fill='both', expand=True)
        dictate_nav.configure(style='Selected.Nav.TButton' if page is dictate else 'Nav.TButton')
        settings_nav.configure(style='Selected.Nav.TButton' if page is settings else 'Nav.TButton')
    dictate_nav = ttk.Button(nav, text='Dictate', command=lambda: select_page(dictate))
    dictate_nav.pack(side='left', padx=(0, 8))
    settings_nav = ttk.Button(nav, text='Preferences', command=lambda: select_page(settings))
    settings_nav.pack(side='left')
    select_page(dictate)

    hero = tk.Frame(dictate, bg=INK, padx=22, pady=18)
    hero.pack(fill='x', pady=(0, 16))
    tk.Label(hero, text='Your words, wherever you work.', bg=INK, fg='#f7f7ef',
             font=('Segoe UI Semibold', 17)).pack(anchor='w')
    keys = tk.Frame(hero, bg=INK)
    keys.pack(anchor='w', pady=(12, 0))
    for key in ('Win', '+', 'Alt'):
        tk.Label(keys, text=key, bg=('#36544a' if key != '+' else INK), fg='white',
                 font=('Segoe UI Semibold', 11), padx=10, pady=5).pack(side='left', padx=(0, 6))
    tk.Label(keys, text='Hold to talk. Release to insert.   Esc to cancel.', bg=INK,
             fg='#d4dfd5', font=('Segoe UI', 10)).pack(side='left', padx=6)

    ttk.Label(dictate, textvariable=app.status, wraplength=740, style='Muted.TLabel').pack(anchor='w', pady=(0, 10))
    row = ttk.Frame(dictate)
    row.pack(fill='x', pady=(0, 10))
    ttk.Label(row, text='Your transcript', style='Section.TLabel').pack(side='left')
    ttk.Button(row, text='Original', command=app.show_original).pack(side='right', padx=(8, 0))
    ttk.Button(row, text='Copy text', command=app.copy).pack(side='right')
    editor = tk.Frame(dictate, bg='#dce1d6', padx=1, pady=1)
    editor.pack(fill='both', expand=True)
    app.output = tk.Text(editor, height=5, wrap='word', font=('Segoe UI', 12), bg='#ffffff',
                         fg=INK, insertbackground=ACCENT, selectbackground='#d9e8d4',
                         relief='flat', borderwidth=0, padx=16, pady=14, undo=True)
    scrollbar = ttk.Scrollbar(editor, command=app.output.yview)
    scrollbar.pack(side='right', fill='y')
    app.output.configure(yscrollcommand=scrollbar.set)
    app.output.pack(fill='both', expand=True)
    actions = ttk.Frame(dictate)
    actions.pack(fill='x', pady=(14, 0))
    app.button = ttk.Button(actions, text='Start recording', style='Accent.TButton', command=lambda: app.toggle(None))
    app.button.pack(side='left')
    ttk.Label(actions, text='Button recording stays in this preview.', style='Muted.TLabel').pack(side='left', padx=16)

    ttk.Label(settings, text='Make it feel like you', style='Section.TLabel').pack(anchor='w', pady=(0, 5))
    ttk.Label(settings, text='Everything below is processed on your computer.', style='Muted.TLabel').pack(anchor='w', pady=(0, 18))
    ttk.Label(settings, text='Speech model').pack(anchor='w')
    app.model_choice = tk.StringVar(value=next(label for label, name in choices.items() if name == app.current_model))
    app.model_selector = ttk.Combobox(settings, textvariable=app.model_choice, values=list(choices), state='disabled', width=34)
    app.model_selector.pack(anchor='w', pady=(6, 4))
    app.model_selector.bind('<<ComboboxSelected>>', app.switch_model)
    model_help = 'Add Accuracy by running the installer again.' if FROZEN else 'Install the optional Accuracy model with setup_accuracy.bat.'
    ttk.Label(settings, text='Lightweight uses less memory. Accuracy takes more time.\n' + model_help, style='Muted.TLabel').pack(anchor='w', pady=(0, 16))
    for label, variable in [('Insert at the cursor when using Win + Alt', app.insert),
                            ('Refine punctuation', app.punctuation_enabled),
                            ('Apply my saved corrections', app.personalization_enabled),
                            ('Add a space between dictations', app.add_space)]:
        ttk.Checkbutton(settings, text=label, variable=variable).pack(anchor='w')
    ttk.Button(settings, text='Manage personal dictionary', command=app.open_dictionary).pack(anchor='w', pady=14)
    ttk.Label(settings, text='Only corrections you save are remembered. Audio stays in memory.', style='Muted.TLabel').pack(anchor='w')

    footer = ttk.Frame(shell)
    footer.pack(fill='x', pady=(18, 0))
    ttk.Label(footer, textvariable=app.memory_label, style='Muted.TLabel', font=('Segoe UI', 9)).pack(side='left')
    ttk.Button(footer, text='Quit', command=app.close).pack(side='right', padx=(8, 0))
    ttk.Button(footer, text='Hide to tray', command=root.withdraw).pack(side='right')

    def sync_state():
        if app.closed:
            return
        app.button.configure(state='disabled' if app.busy else 'normal')
        root.after(150, sync_state)
    sync_state()
