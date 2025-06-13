import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import ctypes
import ctypes.wintypes

if sys.platform == 'win32':
    from PyQt5 import QtWinExtras

def exclude_from_capture(hwnd):
    WDA_EXCLUDEFROMCAPTURE = 0x11
    ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class CodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QtGui.QFont("Consolas", 11))
        self.setStyleSheet("""
            QPlainTextEdit {
                padding: 10px;
                color: #fff;
                font-family: monospace;
                background: transparent;
            }
        """)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QtGui.QPainter(self.line_number_area)
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingGeometry(block).height()
        painter.setPen(QtGui.QColor(255, 255, 255))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(0, int(top), self.line_number_area.width() - 5, self.fontMetrics().height(), QtCore.Qt.AlignRight, str(block_number + 1))
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingGeometry(block).height()
            block_number += 1

class GlassTextWindow(QtWidgets.QMainWindow):
    DWMWA_CLOAK = 14

    def __init__(self):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.NoDropShadowWindowHint)
        self.setGeometry(100, 100, 800, 600)
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QtWidgets.QVBoxLayout(self.central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        self.title_bar = QtWidgets.QWidget()
        self.title_bar.setFixedHeight(30)
        title_layout = QtWidgets.QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QtWidgets.QLabel("GlassText")
        self.title_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 12pt; }")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        self.title_close_btn = QtWidgets.QPushButton("✕")
        self.title_close_btn.setFixedSize(30, 30)
        self.title_close_btn.setStyleSheet("QPushButton { background-color: transparent; color: white; font-weight: bold; border: none; font-size: 14pt; } QPushButton:hover { border-radius: 15px; }")
        self.title_close_btn.clicked.connect(self.close)
        title_layout.addWidget(self.title_close_btn)
        layout.addWidget(self.title_bar)
        self.editor = CodeEditor()
        layout.addWidget(self.editor)
        footer = QtWidgets.QLabel("GlassText v1.0 - Luigi Adducci    |    Atajos: Ctrl+M Mostrar/Ocultar, Esc Cerrar")
        footer.setStyleSheet("QLabel { color: rgba(255, 255, 255, 180); font-size: 9pt; }")
        footer.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(footer)
        self.central_widget.setStyleSheet("QWidget { background-color: transparent; } QPushButton { background-color: rgba(255, 255, 255, 150); border: 1px solid rgba(200, 200, 200, 100); padding: 5px 10px; color: #333; } QPushButton:hover { background-color: rgba(230, 230, 230, 200); }")
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        self.central_widget.setGraphicsEffect(shadow)
        if sys.platform == 'win32':
            try:
                QtWinExtras.QtWin.enableBlurBehindWindow(self)
            except:
                pass
            hwnd = int(self.winId())
            exclude_from_capture(hwnd)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, self.DWMWA_CLOAK, ctypes.byref(ctypes.c_bool(True)), ctypes.sizeof(ctypes.c_bool(True)))
        toggle = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+M"), self)
        toggle.setContext(QtCore.Qt.ApplicationShortcut)
        toggle.activated.connect(self.toggle_visibility)
        close = QtWidgets.QShortcut(QtGui.QKeySequence("Esc"), self)
        close.setContext(QtCore.Qt.ApplicationShortcut)
        close.activated.connect(self.close)

    def toggle_visibility(self):
        if self.isVisible() and not self.isMinimized():
            self.showMinimized()
        else:
            if self.isMinimized():
                self.showNormal()
            self.show()
            self.activateWindow()
            self.raise_()
            self.editor.setFocus()
            self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
            self.activateWindow()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor(255, 255, 255, 40))
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 80), 1)
        painter.setPen(pen)
        painter.drawRect(self.rect())

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()
        self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos') and self.old_pos is not None and self.drag_start_position.y() <= self.title_bar.height():
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'old_pos'):
            self.old_pos = None

class GlassTextApp(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setStyle("Fusion")
        self.setApplicationName("GlassText")
        self.setApplicationDisplayName("GlassText - Professional Note Taking")
        self.setApplicationVersion("1.0")
        dark_palette = QtGui.QPalette()
        dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(30, 30, 30, 200))
        dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        self.setPalette(dark_palette)
        self.window = GlassTextWindow()
        screen_geo = self.primaryScreen().availableGeometry()
        self.window.setGeometry(screen_geo.width() // 2 - 400, screen_geo.height() // 2 - 300, 800, 600)
        self.window.show()

if __name__ == '__main__':
    app = GlassTextApp(sys.argv)
    sys.exit(app.exec_())
