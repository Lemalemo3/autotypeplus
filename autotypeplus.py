import sys
import os
import time
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QDialog, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QSpinBox, QCheckBox, QMessageBox, QShortcut, 
                             QWidget, QSystemTrayIcon, QMenu, QStyle)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QKeySequence, QGuiApplication, QIcon, QPixmap
from pynput import keyboard
from pynput.keyboard import Controller, Key
from pynput.mouse import Listener as MouseListener

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class TypingThread(QThread):
    """Thread to handle the actual typing simulation"""
    typing_finished = pyqtSignal()
    typing_error = pyqtSignal(str)
    
    def __init__(self, text, delay, parent=None):
        super().__init__(parent)
        self.text = text
        self.delay = delay
        self.keyboard = Controller()
        self._is_running = True
        
    def stop(self):
        self._is_running = False
        
    def run(self):
        try:
            for char in self.text:
                if not self._is_running:
                    break
                    
                if char == '\n':
                    self.keyboard.press(Key.enter)
                    self.keyboard.release(Key.enter)
                elif char == '\t':
                    self.keyboard.press(Key.tab)
                    self.keyboard.release(Key.tab)
                elif char == ' ':
                    self.keyboard.press(Key.space)
                    self.keyboard.release(Key.space)
                else:
                    # Handle uppercase and special characters
                    if char.isupper():
                        self.keyboard.press(Key.shift)
                        self.keyboard.press(char.lower())
                        self.keyboard.release(char.lower())
                        self.keyboard.release(Key.shift)
                    else:
                        self.keyboard.press(char)
                        self.keyboard.release(char)
                
                time.sleep(self.delay)
                
            self.typing_finished.emit()
        except Exception as e:
            self.typing_error.emit(str(e))

class GlobalHotkeyListener(QThread):
    """Thread to listen for global hotkeys"""
    start_triggered = pyqtSignal()     # F9 - start typing
    stop_triggered = pyqtSignal()      # F11 - stop typing
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True
        
    def stop(self):
        self._is_running = False
        
    def run(self):
        def on_press(key):
            try:
                # F9 - Start typing
                if key == keyboard.Key.f9:
                    self.start_triggered.emit()
                    
                # F11 - Stop typing
                elif key == keyboard.Key.f11:
                    self.stop_triggered.emit()
            except:
                pass
                
        with keyboard.Listener(on_press=on_press) as listener:
            while self._is_running:
                time.sleep(0.1)
            listener.stop()

class MouseClickListener(QThread):
    """Thread to detect mouse clicks to stop typing"""
    mouse_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True
        
    def stop(self):
        self._is_running = False
        
    def run(self):
        def on_click(x, y, button, pressed):
            if pressed:
                self.mouse_clicked.emit()
                
        with MouseListener(on_click=on_click) as listener:
            while self._is_running:
                time.sleep(0.1)
            listener.stop()

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto-Typer")
        self.setMinimumSize(500, 400)
        
        # Set window icon
        icon_path = get_resource_path("favicon.png")
        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
            self.setWindowIcon(self.app_icon)
        else:
            # Fallback to a default icon
            self.app_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
            self.setWindowIcon(self.app_icon)
        
        # Central widget
        central_widget = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Paste your text below, then press F9 to start typing")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        central_widget.addWidget(self.status_label)
        
        # Text input - always visible
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Paste your text here...")
        central_widget.addWidget(self.text_edit)
        
        # Settings
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("Speed (ms/char):"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 1000)
        self.speed_spin.setValue(50)
        self.speed_spin.setSuffix(" ms")
        settings_layout.addWidget(self.speed_spin)
        
        settings_layout.addStretch()
        
        # Auto-close checkbox
        self.auto_close = QCheckBox("Close after typing")
        self.auto_close.setChecked(True)
        settings_layout.addWidget(self.auto_close)
        
        central_widget.addLayout(settings_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.text_edit.clear)
        button_layout.addWidget(self.clear_button)
        
        self.paste_button = QPushButton("Paste from Clipboard")
        self.paste_button.clicked.connect(self.paste_from_clipboard)
        button_layout.addWidget(self.paste_button)
        
        button_layout.addStretch()
        
        self.start_button = QPushButton("Start Typing (F9)")
        self.start_button.clicked.connect(self.start_typing_from_ui)
        self.start_button.setDefault(True)
        button_layout.addWidget(self.start_button)
        
        central_widget.addLayout(button_layout)
        
        # Container widget
        container = QWidget()
        container.setLayout(central_widget)
        self.setCentralWidget(container)
        
        # Initialize components
        self.typing_thread = None
        self.hotkey_listener = None
        self.mouse_listener = None
        self.tray_icon = None
        
        # Start listeners
        self.start_hotkey_listener()
        self.start_mouse_listener()
        
        # Setup system tray
        self.setup_tray()
        
        # Auto-load clipboard content on startup
        self.paste_from_clipboard()
        
    def setup_tray(self):
        """Setup the system tray icon"""
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self.app_icon, self)
        self.tray_icon.setToolTip("Auto-Typer")
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show Window")
        show_action.triggered.connect(self.show_window)
        
        start_action = tray_menu.addAction("Start Typing (F9)")
        start_action.triggered.connect(self.start_typing_from_ui)
        
        stop_action = tray_menu.addAction("Stop Typing (F11)")
        stop_action.triggered.connect(self.stop_typing)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Handle tray icon activation (click to show window)
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # Show tray icon
        self.tray_icon.show()
        
    def on_tray_activated(self, reason):
        """Handle tray icon clicks"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click - toggle window visibility
            if self.isVisible():
                self.hide()
            else:
                self.show_window()
        
    def show_window(self):
        """Show and focus the main window"""
        self.show()
        self.raise_()
        self.activateWindow()
        
    def quit_app(self):
        """Quit the application"""
        self.close()
        
    def paste_from_clipboard(self):
        """Paste the current clipboard content into the text area"""
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text()
        
        if text and text.strip():
            self.text_edit.setPlainText(text)
            self.status_label.setText("Clipboard content loaded. Press F9 to start typing.")
        else:
            self.status_label.setText("Clipboard is empty. Paste your text below, then press F9 to start typing.")
        
    def start_hotkey_listener(self):
        """Start the global hotkey listener"""
        self.hotkey_listener = GlobalHotkeyListener(self)
        self.hotkey_listener.start_triggered.connect(self.start_typing_from_hotkey)
        self.hotkey_listener.stop_triggered.connect(self.stop_typing)
        self.hotkey_listener.start()
        
    def start_mouse_listener(self):
        """Start the mouse click listener"""
        self.mouse_listener = MouseClickListener(self)
        self.mouse_listener.mouse_clicked.connect(self.on_mouse_click)
        self.mouse_listener.start()
        
    def on_mouse_click(self):
        """Handle mouse clicks - stop typing if active"""
        if self.typing_thread and self.typing_thread.isRunning():
            self.stop_typing()
            self.status_label.setText("Typing stopped (mouse click detected). Press F9 to start again.")
        
    def start_typing_from_ui(self):
        """Start typing from the button click"""
        self.start_typing()
        
    def start_typing_from_hotkey(self):
        """Start typing from the F9 hotkey"""
        self.start_typing()
        
    def start_typing(self):
        """Start the typing simulation"""
        # Don't start if already typing
        if self.typing_thread and self.typing_thread.isRunning():
            return
            
        text = self.text_edit.toPlainText().strip()
        if not text:
            self.status_label.setText("Please paste some text first.")
            return
            
        delay = self.speed_spin.value() / 1000.0
        auto_close = self.auto_close.isChecked()
        
        # Update status
        self.status_label.setText("Typing... (Press F11 to stop)")
        
        # Create and start typing thread
        self.typing_thread = TypingThread(text, delay, self)
        self.typing_thread.typing_finished.connect(lambda: self.on_typing_finished(auto_close))
        self.typing_thread.typing_error.connect(self.on_typing_error)
        self.typing_thread.start()
        
    def stop_typing(self):
        """Stop the current typing operation"""
        if self.typing_thread and self.typing_thread.isRunning():
            self.typing_thread.stop()
            self.status_label.setText("Typing stopped. Press F9 to start again.")
            
    def on_typing_finished(self, auto_close):
        """Handle typing completion"""
        self.status_label.setText("Typing complete! Press F9 to start again.")
        
        if auto_close:
            QTimer.singleShot(1000, self.close)
            
    def on_typing_error(self, error_message):
        """Handle typing errors"""
        self.status_label.setText("Error occurred during typing.")
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        
    def closeEvent(self, event):
        """Handle close event - minimize to tray instead of quitting"""
        # If auto_close was triggered, actually quit
        if hasattr(self, '_auto_closing') and self._auto_closing:
            self.cleanup()
            event.accept()
            return
            
        # Otherwise, minimize to tray
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Auto-Typer",
            "Still running in the system tray. Right-click the icon to quit.",
            QSystemTrayIcon.Information,
            2000
        )
        
    def cleanup(self):
        """Clean up all resources"""
        # Stop hotkey listener
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener.wait()
            
        # Stop mouse listener
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener.wait()
            
        # Stop typing thread
        if self.typing_thread and self.typing_thread.isRunning():
            self.typing_thread.stop()
            self.typing_thread.wait()
            
        # Remove tray icon
        if self.tray_icon:
            self.tray_icon.hide()
            
    def quit_app(self):
        """Actually quit the application"""
        self._auto_closing = True
        self.cleanup()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    
    # Set application icon for taskbar
    icon_path = get_resource_path("favicon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
