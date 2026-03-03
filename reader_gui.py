import sys
import json
import os

# --- Path Handling for PyInstaller ---
def get_app_dir():
    if getattr(sys, 'frozen', False):
        # If running as an EXE, use the directory of the EXE
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()
CONFIG_FILE = os.path.join(APP_DIR, "reader_config.json")
# -------------------------------------

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextBrowser, QListWidget, QListWidgetItem,
                             QPushButton, QFileDialog, QSlider, QLabel, QFrame,
                             QComboBox, QFontDialog, QColorDialog, QLineEdit,
                             QSpinBox, QSplitter, QProgressBar, QMessageBox,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QPalette, QShortcut, QKeySequence
from parser import NovelParser
from downloader import NovelDownloader

class ReaderConfig:
    def __init__(self):
        self.font_family = "Microsoft YaHei"
        self.font_size = 18
        self.line_spacing = 150 # percent
        self.bg_color = "#f4f4f4"
        self.text_color = "#333333"
        self.last_file = ""
        self.last_chapter = 0
        self.books = {} # file_path: {last_chapter: 0, title: ""}
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.__dict__.update(data)
            except:
                pass

    def save(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, ensure_ascii=False, indent=4)

    def update_book(self, file_path, chapter_idx):
        if file_path not in self.books:
            self.books[file_path] = {"title": os.path.basename(file_path), "last_chapter": 0}
        self.books[file_path]["last_chapter"] = chapter_idx
        self.last_file = file_path
        self.last_chapter = chapter_idx
        self.save()

# --- Worker for Downloading ---
class DownloadWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, book_info):
        super().__init__()
        self.book_info = book_info
        self.downloader = NovelDownloader()

    def run(self):
        try:
            def callback(current, total, status):
                self.progress.emit(current, total, status)
            
            final_path = self.downloader.start_download(self.book_info, callback)
            if final_path:
                self.finished.emit(final_path)
            else:
                self.error.emit("下载失败，未找到目录")
        except Exception as e:
            self.error.emit(str(e))

# --- Search Dialog ---
class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("搜索并下载小说")
        self.resize(600, 450)
        self.layout = QVBoxLayout(self)
        
        # Search Box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入小说名称...")
        self.search_input.returnPressed.connect(self.search)
        self.btn_search = QPushButton("搜索")
        self.btn_search.clicked.connect(self.search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        self.layout.addLayout(search_layout)
        
        # Results Table
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["书名", "作者", "链接"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.layout.addWidget(self.results_table)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_download = QPushButton("下载选中小说")
        self.btn_download.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_download)
        btn_layout.addWidget(self.btn_cancel)
        self.layout.addLayout(btn_layout)
        
        self.downloader = NovelDownloader()

    def search(self):
        name = self.search_input.text().strip()
        if not name: return
        
        self.btn_search.setEnabled(False)
        self.btn_search.setText("搜索中...")
        QApplication.processEvents()
        
        results = self.downloader.search_novel(name)
        self.results_table.setRowCount(0)
        for r in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(r['title']))
            self.results_table.setItem(row, 1, QTableWidgetItem(r['author']))
            self.results_table.setItem(row, 2, QTableWidgetItem(r['url']))
        
        self.btn_search.setEnabled(True)
        self.btn_search.setText("搜索")
        
        if not results:
            QMessageBox.information(self, "搜索结果", "未找到相关小说，请尝试更换书名关键词")

    def get_selected_book(self):
        row = self.results_table.currentRow()
        if row >= 0:
            return {
                'title': self.results_table.item(row, 0).text(),
                'author': self.results_table.item(row, 1).text(),
                'url': self.results_table.item(row, 2).text()
            }
        return None

# --- Main Reader Window ---
class NovelReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ReaderConfig()
        
        # Auto-add the downloaded novel if it exists in the same directory
        default_novel_name = "蛊真人_全文.txt"
        default_novel_path = os.path.join(APP_DIR, default_novel_name)
        if os.path.exists(default_novel_path):
            abs_path = os.path.abspath(default_novel_path)
            if abs_path not in self.config.books:
                self.config.books[abs_path] = {"title": "蛊真人", "last_chapter": 0}
                self.config.save()

        self.parser = None
        self.init_ui()
        
        if self.config.last_file and os.path.exists(self.config.last_file):
            self.load_novel(self.config.last_file)
            self.jump_to_chapter(self.config.last_chapter)

    def init_ui(self):
        self.setWindowTitle("极简小说阅读器")
        self.resize(1100, 850)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter for sidebar and content
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel (Shelf + Chapters)
        self.left_panel = QFrame()
        self.left_panel.setFixedWidth(280)
        left_layout = QVBoxLayout(self.left_panel)
        
        # Shelf Section
        left_layout.addWidget(QLabel("<b>书架</b>"))
        
        self.btn_search_online = QPushButton("在线搜索下载")
        self.btn_search_online.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        self.btn_search_online.clicked.connect(self.open_search_dialog)
        left_layout.addWidget(self.btn_search_online)
        
        self.download_progress = QProgressBar()
        self.download_progress.hide()
        left_layout.addWidget(self.download_progress)
        self.lbl_download_status = QLabel("")
        self.lbl_download_status.hide()
        self.lbl_download_status.setWordWrap(True)
        left_layout.addWidget(self.lbl_download_status)

        self.shelf_list = QListWidget()
        self.shelf_list.setFixedHeight(200)
        self.shelf_list.itemClicked.connect(self.on_shelf_clicked)
        left_layout.addWidget(self.shelf_list)
        self.update_shelf()

        # Chapter Section
        left_layout.addWidget(QLabel("<b>目录</b>"))
        self.btn_open = QPushButton("打开本地 TXT")
        self.btn_open.clicked.connect(self.open_file_dialog)
        left_layout.addWidget(self.btn_open)
        
        # Chapter Jump Input
        jump_layout = QHBoxLayout()
        self.jump_input = QLineEdit()
        self.jump_input.setPlaceholderText("输入章节数跳转...")
        self.jump_input.returnPressed.connect(self.jump_by_input)
        self.btn_jump = QPushButton("跳转")
        self.btn_jump.clicked.connect(self.jump_by_input)
        jump_layout.addWidget(self.jump_input)
        jump_layout.addWidget(self.btn_jump)
        left_layout.addLayout(jump_layout)
        
        self.chapter_list = QListWidget()
        self.chapter_list.itemClicked.connect(self.on_chapter_clicked)
        left_layout.addWidget(self.chapter_list)
        
        # Main Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Header for current chapter title
        self.lbl_current_chapter = QLabel("未加载章节")
        self.lbl_current_chapter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_current_chapter.setFixedHeight(40)
        self.lbl_current_chapter.setStyleSheet("font-weight: bold; border-bottom: 1px solid #ddd;")
        content_layout.addWidget(self.lbl_current_chapter)
        
        self.text_display = QTextBrowser()
        self.text_display.setOpenExternalLinks(True)
        self.update_text_style()
        content_layout.addWidget(self.text_display)
        
        # Bottom Control
        control_layout = QHBoxLayout()
        self.btn_prev = QPushButton("上一章")
        self.btn_prev.clicked.connect(self.prev_chapter)
        self.lbl_progress = QLabel("进度: 0/0")
        self.btn_next = QPushButton("下一章")
        self.btn_next.clicked.connect(self.next_chapter)
        
        control_layout.addWidget(self.btn_prev)
        control_layout.addWidget(self.lbl_progress)
        control_layout.addWidget(self.btn_next)
        
        # Appearance Controls
        control_layout.addStretch()
        
        # Line Spacing Control
        control_layout.addWidget(QLabel("行间距:"))
        self.spacing_box = QSpinBox()
        self.spacing_box.setRange(100, 300)
        self.spacing_box.setSingleStep(10)
        self.spacing_box.setValue(self.config.line_spacing)
        self.spacing_box.valueChanged.connect(self.change_line_spacing)
        control_layout.addWidget(self.spacing_box)
        
        self.btn_font_plus = QPushButton("A+")
        self.btn_font_plus.setFixedWidth(40)
        self.btn_font_plus.clicked.connect(lambda: self.change_font_size(2))
        self.btn_font_minus = QPushButton("A-")
        self.btn_font_minus.setFixedWidth(40)
        self.btn_font_minus.clicked.connect(lambda: self.change_font_size(-2))
        
        self.btn_theme = QPushButton("护眼/夜间")
        self.btn_theme.clicked.connect(self.toggle_theme)
        
        control_layout.addWidget(self.btn_font_minus)
        control_layout.addWidget(self.btn_font_plus)
        control_layout.addWidget(self.btn_theme)
        
        self.btn_sidebar = QPushButton("隐藏侧栏")
        self.btn_sidebar.clicked.connect(self.toggle_sidebar)
        control_layout.addWidget(self.btn_sidebar)
        
        self.btn_fullscreen = QPushButton("全屏 (F11)")
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        control_layout.addWidget(self.btn_fullscreen)
        
        content_layout.addLayout(control_layout)
        
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(content_area)
        self.splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.splitter)
        
        # Shortcuts
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.prev_chapter)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.next_chapter)
        QShortcut(QKeySequence(Qt.Key.Key_Up), self, lambda: self.text_display.verticalScrollBar().setValue(
            self.text_display.verticalScrollBar().value() - 50))
        QShortcut(QKeySequence(Qt.Key.Key_Down), self, lambda: self.text_display.verticalScrollBar().setValue(
            self.text_display.verticalScrollBar().value() + 50))
        QShortcut(QKeySequence(Qt.Key.Key_F11), self, self.toggle_fullscreen)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.exit_fullscreen)

    def update_shelf(self):
        self.shelf_list.clear()
        for path, info in self.config.books.items():
            if os.path.exists(path):
                self.shelf_list.addItem(info['title'])

    def on_shelf_clicked(self, item):
        title = item.text()
        for path, info in self.config.books.items():
            if info['title'] == title:
                self.load_novel(path)
                # Ensure we jump to the correct last chapter saved for this specific book
                last_ch = info.get('last_chapter', 0)
                self.jump_to_chapter(last_ch)
                break

    def change_font_size(self, delta):
        self.config.font_size += delta
        self.config.font_size = max(8, min(72, self.config.font_size))
        # update_text_style now handles everything including jump_to_chapter
        self.update_text_style()
        self.config.save()

    def change_line_spacing(self, value):
        self.config.line_spacing = value
        self.update_text_style()
        self.config.save()

    def jump_by_input(self):
        text = self.jump_input.text().strip()
        if not text:
            return
        try:
            # Support 1-based input for users
            idx = int(text) - 1
            if self.parser and 0 <= idx < len(self.parser.chapters):
                self.jump_to_chapter(idx)
                self.jump_input.clear()
        except ValueError:
            pass

    def toggle_theme(self):
        if self.config.bg_color == "#f4f4f4":
            # Eye protection
            self.config.bg_color = "#c7edcc"
            self.config.text_color = "#000000"
        elif self.config.bg_color == "#c7edcc":
            # Night
            self.config.bg_color = "#1a1a1a"
            self.config.text_color = "#cccccc"
        else:
            # Default
            self.config.bg_color = "#f4f4f4"
            self.config.text_color = "#333333"
        self.update_text_style()
        self.config.save()

    def update_text_style(self):
        # 1. Update the widget's base appearance (padding, border, etc.)
        style = f"""
            QTextBrowser {{
                background-color: {self.config.bg_color};
                padding: 40px;
                border: none;
            }}
        """
        self.text_display.setStyleSheet(style)
        
        # Update top header style
        header_style = f"""
            QLabel {{
                background-color: {self.config.bg_color};
                color: {self.config.text_color};
                font-weight: bold;
                font-size: 12pt;
                border-bottom: 1px solid {"#444" if self.config.bg_color == "#1a1a1a" else "#ddd"};
            }}
        """
        self.lbl_current_chapter.setStyleSheet(header_style)
        
        # 2. Update the default stylesheet for the HTML document (font, color, line height)
        # This is the most reliable way in Qt to apply global styles to HTML content
        doc_style = f"""
            body {{
                background-color: {self.config.bg_color};
                color: {self.config.text_color};
                font-family: '{self.config.font_family}';
                font-size: {self.config.font_size}pt;
            }}
            h1 {{
                text-align: center;
                font-weight: bold;
                margin-bottom: 1.5em;
                color: {self.config.text_color};
            }}
            p {{
                line-height: {self.config.line_spacing}%;
                text-indent: 2em;
                margin-bottom: 1em;
            }}
        """
        self.text_display.document().setDefaultStyleSheet(doc_style)
        
        # 3. Re-render the current chapter to apply the new default style
        if self.parser and self.config.last_chapter >= 0:
            self.jump_to_chapter(self.config.last_chapter)

    def toggle_sidebar(self):
        visible = not self.left_panel.isVisible()
        self.left_panel.setVisible(visible)
        self.btn_sidebar.setText("显示侧栏" if not visible else "隐藏侧栏")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.exit_fullscreen()
        else:
            self.showFullScreen()
            self.left_panel.hide()
            self.btn_sidebar.setText("显示侧栏")

    def exit_fullscreen(self):
        self.showNormal()
        self.left_panel.show()
        self.btn_sidebar.setText("隐藏侧栏")

    def open_search_dialog(self):
        dialog = SearchDialog(self)
        if dialog.exec():
            book_info = dialog.get_selected_book()
            if book_info:
                self.start_download(book_info)

    def start_download(self, book_info):
        self.btn_search_online.setEnabled(False)
        self.btn_search_online.setText("正在准备下载...")
        self.download_progress.show()
        self.download_progress.setValue(0)
        self.lbl_download_status.show()
        self.lbl_download_status.setText(f"准备下载: {book_info['title']}")
        
        self.worker = DownloadWorker(book_info)
        self.worker.progress.connect(self.on_download_progress)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_download_error)
        self.worker.start()

    def on_download_progress(self, current, total, status):
        self.download_progress.setMaximum(total)
        self.download_progress.setValue(current)
        self.lbl_download_status.setText(status)

    def on_download_finished(self, file_path):
        self.btn_search_online.setEnabled(True)
        self.btn_search_online.setText("在线搜索下载")
        self.download_progress.hide()
        self.lbl_download_status.hide()
        
        QMessageBox.information(self, "下载完成", f"小说已下载并合并完成：\n{os.path.basename(file_path)}")
        
        # Add to shelf and load
        abs_path = os.path.abspath(file_path)
        if abs_path not in self.config.books:
            self.config.books[abs_path] = {"title": os.path.basename(file_path).replace(".txt", ""), "last_chapter": 0}
            self.config.save()
            self.update_shelf()
        
        self.load_novel(abs_path)

    def on_download_error(self, error_msg):
        self.btn_search_online.setEnabled(True)
        self.btn_search_online.setText("在线搜索下载")
        self.download_progress.hide()
        self.lbl_download_status.setText(f"下载出错: {error_msg}")
        QMessageBox.warning(self, "下载失败", f"下载过程中出现错误：\n{error_msg}")

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择小说", "", "TXT Files (*.txt);;All Files (*)")
        if file_path:
            self.load_novel(file_path)
            self.update_shelf()

    def load_novel(self, file_path):
        # Create cache dir if it doesn't exist
        cache_dir = os.path.join(APP_DIR, ".reader_cache")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        self.parser = NovelParser(file_path, cache_dir=cache_dir)
        chapters = self.parser.parse()
        
        self.chapter_list.clear()
        for ch in chapters:
            self.chapter_list.addItem(ch['title'])
            
        if file_path not in self.config.books:
             self.config.books[file_path] = {"title": os.path.basename(file_path), "last_chapter": 0}
        
        self.config.last_file = file_path
        self.config.save()
        self.setWindowTitle(f"阅读器 - {os.path.basename(file_path)}")
        
        # Load the book's progress
        last_ch = self.config.books[file_path].get('last_chapter', 0)
        self.jump_to_chapter(last_ch)

    def on_chapter_clicked(self, item):
        idx = self.chapter_list.row(item)
        self.jump_to_chapter(idx)

    def jump_to_chapter(self, index):
        if self.parser and 0 <= index < len(self.parser.chapters):
            content = self.parser.get_chapter_content(index)
            lines = content.split('\n')
            import html
            
            # Separate title and content
            title = ""
            body_lines = []
            
            # Find the first non-empty line as title
            found_title = False
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if not found_title:
                    title = line
                    found_title = True
                else:
                    body_lines.append(line)
            
            # Format title and body without redundant inline styles
            # The styles are now managed by setDefaultStyleSheet
            formatted_title = f"<h1>{html.escape(title)}</h1>"
            
            formatted_body = []
            for line in body_lines:
                safe_line = html.escape(line)
                formatted_body.append(f"<p>{safe_line}</p>")
            
            html_content = formatted_title + "".join(formatted_body)
            # Use a clean container; styles will be applied by default CSS
            self.text_display.setHtml(f"<html><body>{html_content}</body></html>")
            self.text_display.verticalScrollBar().setValue(0)
            
            # Update top header
            self.lbl_current_chapter.setText(title if title else "无标题章节")
            
            self.config.update_book(self.config.last_file, index)
            self.lbl_progress.setText(f"进度: {index + 1}/{len(self.parser.chapters)}")
            self.chapter_list.setCurrentRow(index)
            
            # Find in shelf and select
            for i in range(self.shelf_list.count()):
                if self.shelf_list.item(i).text() == self.config.books.get(self.config.last_file, {}).get('title', ''):
                    self.shelf_list.setCurrentRow(i)
                    break

    def prev_chapter(self):
        if self.config.last_chapter > 0:
            self.jump_to_chapter(self.config.last_chapter - 1)

    def next_chapter(self):
        if self.parser and self.config.last_chapter < len(self.parser.chapters) - 1:
            self.jump_to_chapter(self.config.last_chapter + 1)

    def closeEvent(self, event):
        self.config.save()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    reader = NovelReader()
    reader.show()
    sys.exit(app.exec())
