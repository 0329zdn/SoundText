#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
from pathlib import Path

# 添加当前目录和本地 site-packages 到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
local_site_packages = os.path.join(current_dir, 'python', 'Lib', 'site-packages')
if os.path.exists(local_site_packages):
    sys.path.insert(0, local_site_packages)

# 导入 tkinter
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    TK_AVAILABLE = True
except ImportError:
    print("错误: 无法导入 tkinter，请确保您的 Python 环境已安装 tkinter")
    TK_AVAILABLE = False

# 自动安装依赖
def install_dependencies():
    requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    if os.path.exists(requirements_file):
        print("检查依赖...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])

# 尝试导入核心依赖，如果失败则安装
try:
    from audio_analyzer import AudioAnalyzer
except ImportError:
    print("缺少依赖，正在安装...")
    install_dependencies()
    # 重新导入
    from audio_analyzer import AudioAnalyzer

class MusicToTxtApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 音视频转文字工具")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        self.root.configure(bg='#f0f0f0')
        
        # 设置主题样式
        self.setup_styles()
        
        # 全局变量
        self.file_path = ""
        self.file_paths = []  # 存储多个文件路径
        self.analyzer = AudioAnalyzer()
        self.is_processing = False
        self.last_saved_folder = os.path.expanduser("~/Documents")
        self.process_mode = "single"  # "single" 或 "batch"

        # 创建主框架
        main_container = tk.Frame(root, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_frame = tk.Frame(main_container, bg='#f0f0f0')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            title_frame, 
            text="🎵 音视频转文字工具", 
            font=('Microsoft YaHei', 24, 'bold'),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="支持 MP3, WAV, MP4, AVI 等多种格式",
            font=('Microsoft YaHei', 10),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        subtitle_label.pack(pady=(5, 0))

        # 文件选择区域
        file_card = tk.Frame(main_container, bg='white', relief=tk.FLAT, bd=0)
        file_card.pack(fill=tk.X, pady=10)
        file_card.configure(highlightbackground='#ddd', highlightthickness=1)
        
        file_header = tk.Frame(file_card, bg='#3498db', height=3)
        file_header.pack(fill=tk.X)
        file_header.pack_propagate(False)
        
        file_content = tk.Frame(file_card, bg='white', padx=15, pady=15)
        file_content.pack(fill=tk.X)
        
        file_title = tk.Label(file_content, text="📁 文件选择", font=('Microsoft YaHei', 12, 'bold'), bg='white', fg='#2c3e50')
        file_title.pack(anchor='w', pady=(0, 10))
        
        # 模式选择框架
        mode_frame = tk.Frame(file_content, bg='white')
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(mode_frame, text="处理模式:", font=('Microsoft YaHei', 10), bg='white', fg='#555').pack(side=tk.LEFT, padx=(0, 10))
        
        self.mode_var = tk.StringVar(value="single")
        single_radio = tk.Radiobutton(
            mode_frame, 
            text="单文件", 
            variable=self.mode_var, 
            value="single",
            command=self.on_mode_change,
            font=('Microsoft YaHei', 10),
            bg='white',
            activebackground='white'
        )
        single_radio.pack(side=tk.LEFT, padx=(0, 15))
        
        batch_radio = tk.Radiobutton(
            mode_frame, 
            text="批量处理", 
            variable=self.mode_var, 
            value="batch",
            command=self.on_mode_change,
            font=('Microsoft YaHei', 10),
            bg='white',
            activebackground='white'
        )
        batch_radio.pack(side=tk.LEFT)
        
        file_input_frame = tk.Frame(file_content, bg='white')
        file_input_frame.pack(fill=tk.X)
        
        self.file_entry = tk.Entry(
            file_input_frame, 
            font=('Microsoft YaHei', 10),
            relief=tk.FLAT,
            bg='#f8f9fa',
            highlightbackground='#ddd',
            highlightthickness=1
        )
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)

        self.browse_btn = ttk.Button(
            file_input_frame, 
            text="📂 浏览", 
            command=self.browse_file,
            style="Custom.TButton"
        )
        self.browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.batch_browse_btn = ttk.Button(
            file_input_frame, 
            text="📁 选择文件夹", 
            command=self.browse_folder,
            style="Custom.TButton"
        )
        self.batch_browse_btn.pack(side=tk.RIGHT)
        self.batch_browse_btn.pack_forget()  # 初始隐藏
        
        # 批量文件列表框
        self.file_listbox_frame = tk.Frame(file_content, bg='white')
        self.file_listbox_frame.pack(fill=tk.X, pady=(10, 0))
        self.file_listbox_frame.pack_forget()  # 初始隐藏
        
        tk.Label(self.file_listbox_frame, text="已选文件:", font=('Microsoft YaHei', 10), bg='white', fg='#555').pack(anchor='w', pady=(0, 5))
        
        listbox_container = tk.Frame(self.file_listbox_frame, bg='white', highlightbackground='#ddd', highlightthickness=1)
        listbox_container.pack(fill=tk.X)
        
        self.file_listbox = tk.Listbox(
            listbox_container,
            font=('Microsoft YaHei', 9),
            height=4,
            bg='#fafafa',
            fg='#333',
            selectbackground='#d4e6f1',
            activestyle='none'
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1, pady=1)
        
        listbox_scrollbar = ttk.Scrollbar(listbox_container, command=self.file_listbox.yview)
        listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=listbox_scrollbar.set)

        # 选项设置区域
        options_card = tk.Frame(main_container, bg='white', relief=tk.FLAT, bd=0)
        options_card.pack(fill=tk.X, pady=10)
        options_card.configure(highlightbackground='#ddd', highlightthickness=1)
        
        options_header = tk.Frame(options_card, bg='#2ecc71', height=3)
        options_header.pack(fill=tk.X)
        options_header.pack_propagate(False)
        
        options_content = tk.Frame(options_card, bg='white', padx=15, pady=15)
        options_content.pack(fill=tk.X)
        
        options_title = tk.Label(options_content, text="⚙️ 转写选项", font=('Microsoft YaHei', 12, 'bold'), bg='white', fg='#2c3e50')
        options_title.pack(anchor='w', pady=(0, 15))
        
        # 选项网格布局
        options_grid = tk.Frame(options_content, bg='white')
        options_grid.pack(fill=tk.X)
        
        # 语言选择
        lang_frame = tk.Frame(options_grid, bg='white')
        lang_frame.pack(side=tk.LEFT, padx=(0, 30))
        
        tk.Label(lang_frame, text="🌐 语言", font=('Microsoft YaHei', 10), bg='white', fg='#555').pack(anchor='w')
        self.language_var = tk.StringVar(value="auto")
        language_options = ["auto", "zh", "en", "ja", "ko", "fr", "de", "es"]
        language_combo = ttk.Combobox(
            lang_frame, 
            textvariable=self.language_var, 
            values=language_options, 
            width=12,
            font=('Microsoft YaHei', 10),
            state='readonly'
        )
        language_combo.pack(pady=(5, 0))
        
        # 模型大小
        model_frame = tk.Frame(options_grid, bg='white')
        model_frame.pack(side=tk.LEFT, padx=(0, 30))
        
        tk.Label(model_frame, text="🧠 模型", font=('Microsoft YaHei', 10), bg='white', fg='#555').pack(anchor='w')
        self.model_var = tk.StringVar(value="base")
        model_options = ["tiny", "base"]
        model_combo = ttk.Combobox(
            model_frame, 
            textvariable=self.model_var, 
            values=model_options, 
            width=12,
            font=('Microsoft YaHei', 10),
            state='readonly'
        )
        model_combo.pack(pady=(5, 0))
        
        # 设备选择
        device_frame = tk.Frame(options_grid, bg='white')
        device_frame.pack(side=tk.LEFT)
        
        tk.Label(device_frame, text="💻 设备", font=('Microsoft YaHei', 10), bg='white', fg='#555').pack(anchor='w')
        self.device_var = tk.StringVar(value="cpu")
        device_options = ["cpu", "cuda"]
        device_combo = ttk.Combobox(
            device_frame, 
            textvariable=self.device_var, 
            values=device_options, 
            width=12,
            font=('Microsoft YaHei', 10),
            state='readonly'
        )
        device_combo.pack(pady=(5, 0))

        # 操作按钮区域
        button_frame = tk.Frame(main_container, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=15)
        
        self.start_btn = ttk.Button(
            button_frame, 
            text="▶ 开始转写", 
            command=self.start_transcription,
            style="Custom.TButton"
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_btn = ttk.Button(
            button_frame, 
            text="⏹ 取消", 
            command=self.cancel_transcription,
            style="Custom.TButton",
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 保存按钮组
        save_button_frame = tk.Frame(button_frame, bg='#f0f0f0')
        save_button_frame.pack(side=tk.RIGHT)

        self.save_btn = ttk.Button(
            save_button_frame, 
            text="💾 保存结果", 
            command=self.save_result,
            style="Custom.TButton",
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.open_folder_btn = ttk.Button(
            save_button_frame,
            text="📂 打开文件夹",
            command=self.open_save_folder,
            style="Custom.TButton",
            state=tk.DISABLED
        )
        self.open_folder_btn.pack(side=tk.LEFT)

        # 进度条
        progress_frame = tk.Frame(main_container, bg='#f0f0f0')
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            mode='determinate',
            length=100
        )
        self.progress_bar.pack(fill=tk.X)
        
        # 状态标签
        self.status_label = tk.Label(
            progress_frame,
            text="就绪",
            font=('Microsoft YaHei', 9),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        self.status_label.pack(anchor='w', pady=(5, 0))

        # 内容区域（日志和结果）
        content_frame = tk.Frame(main_container, bg='#f0f0f0')
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # 日志区域
        log_card = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=0)
        log_card.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        log_card.configure(highlightbackground='#ddd', highlightthickness=1)
        
        log_header = tk.Frame(log_card, bg='#f39c12', height=3)
        log_header.pack(fill=tk.X)
        log_header.pack_propagate(False)
        
        log_content = tk.Frame(log_card, bg='white')
        log_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        log_title = tk.Label(log_content, text="📋 转写日志", font=('Microsoft YaHei', 11, 'bold'), bg='white', fg='#2c3e50')
        log_title.pack(anchor='w', pady=(0, 10))
        
        log_text_frame = tk.Frame(log_content, bg='white')
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_text_frame, 
            wrap=tk.WORD, 
            height=8,
            font=('Consolas', 9),
            relief=tk.FLAT,
            bg='#fafafa',
            fg='#333',
            highlightbackground='#e0e0e0',
            highlightthickness=1,
            padx=8,
            pady=8
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scrollbar = ttk.Scrollbar(log_text_frame, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # 结果区域
        result_card = tk.Frame(content_frame, bg='white', relief=tk.FLAT, bd=0)
        result_card.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        result_card.configure(highlightbackground='#ddd', highlightthickness=1)
        
        result_header = tk.Frame(result_card, bg='#9b59b6', height=3)
        result_header.pack(fill=tk.X)
        result_header.pack_propagate(False)
        
        result_content = tk.Frame(result_card, bg='white')
        result_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        result_title_frame = tk.Frame(result_content, bg='white')
        result_title_frame.pack(fill=tk.X, pady=(0, 10))
        
        result_title = tk.Label(result_title_frame, text="📝 转写结果", font=('Microsoft YaHei', 11, 'bold'), bg='white', fg='#2c3e50')
        result_title.pack(side=tk.LEFT)
        
        self.word_count_label = tk.Label(result_title_frame, text="", font=('Microsoft YaHei', 9), bg='white', fg='#7f8c8d')
        self.word_count_label.pack(side=tk.RIGHT)
        
        result_text_frame = tk.Frame(result_content, bg='white')
        result_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = tk.Text(
            result_text_frame, 
            wrap=tk.WORD,
            font=('Microsoft YaHei', 10),
            relief=tk.FLAT,
            bg='#fafafa',
            fg='#333',
            highlightbackground='#e0e0e0',
            highlightthickness=1,
            padx=8,
            pady=8
        )
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        result_scrollbar = ttk.Scrollbar(result_text_frame, command=self.result_text.yview)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=result_scrollbar.set)

    def setup_styles(self):
        """设置自定义样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 进度条样式
        style.configure(
            "Horizontal.TProgressbar",
            thickness=8,
            background='#27ae60',
            troughcolor='#ecf0f1',
            borderwidth=0
        )
        
        # 按钮样式
        style.configure(
            "Custom.TButton",
            font=('Microsoft YaHei', 10),
            foreground='white',
            background='#3498db',
            borderwidth=0,
            focuscolor='none',
            padding=(20, 8)
        )
        style.map(
            "Custom.TButton",
            background=[('active', '#2980b9'), ('!disabled', '#3498db')],
            foreground=[('disabled', 'white')]
        )

    def browse_file(self):
        file_types = [
            ("音视频文件", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac *.wma *.mp4 *.avi *.mov *.wmv *.mkv *.flv *.webm"),
            ("所有文件", "*.*")
        ]
        filename = filedialog.askopenfilename(title="选择文件", filetypes=file_types)
        if filename:
            self.file_path = filename
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
            self.log(f"已选择文件: {filename}")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            self.process_folder(folder)

    def process_folder(self, folder_path):
        """处理文件夹中的所有符合要求的文件"""
        supported_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma', 
                               '.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm'}
        
        self.file_paths = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_extensions:
                    self.file_paths.append(os.path.join(root, file))
        
        if not self.file_paths:
            messagebox.showwarning("提示", "该文件夹中没有找到支持的音视频文件")
            return
        
        # 更新列表框
        self.file_listbox.delete(0, tk.END)
        for path in self.file_paths:
            self.file_listbox.insert(tk.END, os.path.basename(path))
        
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, f"{folder_path} (共 {len(self.file_paths)} 个文件)")
        self.log(f"已从文件夹加载 {len(self.file_paths)} 个文件")

    def on_mode_change(self):
        """切换处理模式时的 UI 更新"""
        if self.mode_var.get() == "batch":
            self.batch_browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
            self.file_listbox_frame.pack(fill=tk.X, pady=(10, 0))
            self.browse_btn.pack_forget()
        else:
            self.batch_browse_btn.pack_forget()
            self.file_listbox_frame.pack_forget()
            self.browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
            self.file_paths = []
            self.file_listbox.delete(0, tk.END)
            self.file_entry.delete(0, tk.END)


    def log(self, message):
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def update_status(self, text, color='#7f8c8d'):
        self.status_label.config(text=text, fg=color)
        self.root.update()

    def start_transcription(self):
        if self.mode_var.get() == "batch":
            if not self.file_paths:
                messagebox.showerror("错误", "请选择要处理的文件夹")
                return
        else:
            if not self.file_path:
                messagebox.showerror("错误", "请选择要转写的文件")
                return

        if self.is_processing:
            return

        # 禁用按钮
        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.DISABLED)
        self.is_processing = True

        # 清空日志和结果
        self.log_text.delete(1.0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.word_count_label.config(text="")
        self.progress_var.set(0)
        self.update_status("正在转写...", '#f39c12')

        # 开始转写线程
        threading.Thread(target=self.transcribe_file, daemon=True).start()

    def transcribe_file(self):
        import time
        start_time = time.time()
        
        try:
            mode = self.mode_var.get()
            
            if mode == "batch":
                # 批量处理模式
                files_to_process = self.file_paths
                self.log(f"批量处理模式：共 {len(files_to_process)} 个文件")
            else:
                # 单文件处理模式
                files_to_process = [self.file_path]
                self.log(f"开始转写：{self.file_path}")
            
            self.log(f"语言：{self.language_var.get()}")
            self.log(f"模型：{self.model_var.get()}")
            self.log(f"设备：{self.device_var.get()}")
            self.log("🔄 正在转写中...")

            total_files = len(files_to_process)
            all_results = []
            
            for idx, file_path in enumerate(files_to_process):
                if not self.is_processing:
                    self.log("⚠️ 转写已取消")
                    break
                
                current_file_start = time.time()
                self.log(f"\n[{idx+1}/{total_files}] 处理：{os.path.basename(file_path)}")
                
                # 更新进度条
                progress = int((idx / total_files) * 100)
                self.progress_var.set(progress)
                self.root.update()

                # 分析文件类型
                file_ext = Path(file_path).suffix.lower().lstrip('.')
                video_extensions = {'mp4', 'avi', 'mov', 'wmv', 'mkv', 'flv', 'webm'}
                audio_extensions = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac', 'wma'}

                is_video = file_ext in video_extensions
                is_audio = file_ext in audio_extensions

                if not is_video and not is_audio:
                    self.log(f"⚠️ 跳过不支持的文件类型：{file_ext}")
                    continue

                # 执行转写
                try:
                    if is_video:
                        self.log("  正在从视频中提取音频并转写中...")
                        result = self.analyzer.analyze_audio_from_video(
                            video_path=file_path,
                            language=self.language_var.get() if self.language_var.get() != "auto" else None,
                            model_size=self.model_var.get(),
                            local_model_path=str(Path(__file__).parent / self.model_var.get()) if self.model_var.get() in ["tiny", "base"] else None,
                            device=self.device_var.get()
                        )
                    else:
                        self.log("  正在分析音频文件...")
                        result = self.analyzer.analyze_audio_file(
                            audio_path=file_path,
                            language=self.language_var.get() if self.language_var.get() != "auto" else None,
                            model_size=self.model_var.get(),
                            local_model_path=str(Path(__file__).parent / self.model_var.get()) if self.model_var.get() in ["tiny", "base"] else None,
                            device=self.device_var.get()
                        )

                    transcript = result.get('transcript', '')
                    all_results.append((file_path, transcript))
                    
                    elapsed = time.time() - current_file_start
                    self.log(f"  ✅ 完成，耗时：{elapsed:.1f} 秒")
                    
                except Exception as e:
                    self.log(f"  ❌ 处理失败：{str(e)}")
            
            # 显示所有结果
            if all_results:
                for file_path, transcript in all_results:
                    if mode == "batch":
                        self.result_text.insert(tk.END, f"\n{'='*50}\n")
                        self.result_text.insert(tk.END, f"文件：{os.path.basename(file_path)}\n")
                        self.result_text.insert(tk.END, f"{'='*50}\n")
                    self.result_text.insert(tk.END, transcript)
                    self.result_text.insert(tk.END, "\n")
                
                total_chars = sum(len(t) for _, t in all_results)
                self.word_count_label.config(text=f"{total_chars} 字符")
                
                elapsed_time = time.time() - start_time
                if elapsed_time < 60:
                    time_str = f"{elapsed_time:.1f} 秒"
                else:
                    minutes = int(elapsed_time // 60)
                    seconds = elapsed_time % 60
                    time_str = f"{minutes} 分 {seconds:.1f} 秒"
                
                self.log(f"\n✅ 全部转写完成，共 {total_chars} 字符，总耗时：{time_str}")

                # 更新进度条
                self.progress_var.set(100)
                self.update_status("转写完成", '#27ae60')

                # 启用保存按钮
                self.save_btn.config(state=tk.NORMAL)
                self.open_folder_btn.config(state=tk.NORMAL)
                self.last_saved_folder = os.path.expanduser("~/Documents")
            else:
                self.log("❌ 没有成功处理任何文件")
                self.update_status("转写失败", '#e74c3c')
                messagebox.showerror("错误", "转写失败：没有成功处理任何文件")

        except Exception as e:
            self.log(f"❌ 错误：{str(e)}")
            self.update_status("转写失败", '#e74c3c')
            messagebox.showerror("错误", f"转写失败：{str(e)}")
        finally:
            # 恢复按钮状态
            self.start_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.is_processing = False

    def _process_single_file(self, file_path):
        """处理单个文件并返回转写结果"""
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        video_extensions = {'mp4', 'avi', 'mov', 'wmv', 'mkv', 'flv', 'webm'}
        audio_extensions = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac', 'wma'}

        is_video = file_ext in video_extensions
        is_audio = file_ext in audio_extensions

        if not is_video and not is_audio:
            self.log(f"⚠️ 跳过不支持的文件类型：{file_ext}")
            return None

        try:
            if is_video:
                result = self.analyzer.analyze_audio_from_video(
                    video_path=file_path,
                    language=self.language_var.get() if self.language_var.get() != "auto" else None,
                    model_size=self.model_var.get(),
                    local_model_path=str(Path(__file__).parent / self.model_var.get()) if self.model_var.get() in ["tiny", "base"] else None,
                    device=self.device_var.get()
                )
            else:
                result = self.analyzer.analyze_audio_file(
                    audio_path=file_path,
                    language=self.language_var.get() if self.language_var.get() != "auto" else None,
                    model_size=self.model_var.get(),
                    local_model_path=str(Path(__file__).parent / self.model_var.get()) if self.model_var.get() in ["tiny", "base"] else None,
                    device=self.device_var.get()
                )
            return result.get('transcript', '')
        except Exception as e:
            self.log(f"❌ 处理失败 {os.path.basename(file_path)}: {str(e)}")
            return None

    def cancel_transcription(self):
        self.is_processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.update_status("已取消", '#e74c3c')
        self.log("⚠️ 转写已取消")

    def save_result(self):
        content = self.result_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showerror("错误", "没有可保存的内容")
            return

        file_types = [("文本文件", "*.txt"), ("所有文件", "*.*")]
        filename = filedialog.asksaveasfilename(
            title="保存结果", 
            filetypes=file_types, 
            defaultextension=".txt",
            initialfile="转写结果.txt",
            initialdir=self.last_saved_folder if hasattr(self, 'last_saved_folder') else os.path.expanduser("~/Documents")
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.last_saved_folder = os.path.dirname(os.path.abspath(filename))
                self.log(f"💾 结果已保存到: {filename}")
                messagebox.showinfo("成功", "结果保存成功！")
            except Exception as e:
                self.log(f"❌ 保存失败: {str(e)}")
                messagebox.showerror("错误", f"保存失败: {str(e)}")

    def open_save_folder(self):
        folder = getattr(self, 'last_saved_folder', os.path.expanduser("~/Documents"))
        if os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")
        else:
            messagebox.showerror("错误", "文件夹不存在")

if __name__ == "__main__":
    if not TK_AVAILABLE:
        print("错误: 无法导入 tkinter，请确保您的 Python 环境已安装 tkinter")
        print("请尝试使用系统 Python 运行此应用")
        input("按 Enter 键退出...")
        sys.exit(1)
    
    root = tk.Tk()
    app = MusicToTxtApp(root)
    root.mainloop()
