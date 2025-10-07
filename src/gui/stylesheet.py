"""
HTSSigma2 Dark Theme Stylesheet
Für PyQt6 optimiert - Dark Mode mit Cyan-Akzenten
Konfigurierbare Variablen für einfache Anpassung
"""

# =============================================================================
# FARBPALETTE & KONFIGURATION
# =============================================================================

# Hauptfarben
PRIMARY_BG = "#232730"          # Hauptfenster-Hintergrund
PANEL_BG = "#262a32"            # Panel/GroupBox-Hintergrund
WIDGET_BG = "#2c313a"           # Input-Fields/Buttons
BORDER_COLOR = "#33383f"        # Standard-Rahmenfarbe
ACCENT_COLOR = "#00bcd4"        # Akzentfarbe (Cyan)

# Textfarben
TEXT_PRIMARY = "#f5f6fa"        # Standard-Schrift hell
TEXT_DISABLED = "#7b7f8a"       # Deaktivierte Elemente
TEXT_READONLY = "#9ea3ae"       # ReadOnly-Felder

# Tab-Farben
TAB_INACTIVE = "#242933"        # Inaktive Tabs
TAB_ACTIVE = "#31363b"          # Aktiver Tab
TAB_HOVER = "#3a4750"           # Hover Tab

# Button-Farben
BTN_NORMAL = "#2c313a"          # Standard Button
BTN_HOVER = "#00bcd4"           # Button Hover
BTN_PRESSED = "#3a4750"         # Button gedrückt
BTN_DISABLED = "#23272f"        # Button deaktiviert
BTN_CANCEL = "#e53935"          # Cancel/Stop Button (rot)
BTN_CANCEL_PRESSED = "#b71c1c"  # Cancel gedrückt
BTN_START = "#4caf50"           # Start/Go Button (grün)
BTN_START_PRESSED = "#2e7d32"   # Start gedrückt

# Scrollbar-Farben
SCROLLBAR_BG = "#23272f"        # Scrollbar Hintergrund
SCROLLBAR_HANDLE = "#393e46"    # Scrollbar Handle
SCROLLBAR_HOVER = "#00bcd4"     # Scrollbar Hover

# Spezielle Hintergründe
INPUT_FOCUS_BG = "#242933"      # Input-Field bei Fokus
SELECTION_BG = "#00bcd4"        # Auswahl-Hintergrund
SELECTION_TEXT = "#23272f"      # Auswahl-Text
ALTERNATE_ROW = "#2c313a"       # Abwechselnde Tabellenzeilen

# Schriftarten & Größen
FONT_FAMILY = "'Arial'"    # Hauptschrift
FONT_SIZE_LARGE = "12pt"              # Große Schrift (z.B. für Überschriften)
FONT_SIZE_NORMAL = "11pt"              # Standard-Schriftgröße
FONT_SIZE_SMALL = "10pt"               # Kleine Schrift (Buttons)
FONT_SIZE_TINY = "9pt"              # Mini-Schrift (Checkboxen)
FONT_SIZE_HEADER = "11pt"              # Header-Schrift
FONT_FAMILY_MONO = "'Consolas'"        # Monospace für Logs

# =============================================================================
# STYLESHEET TEMPLATE
# =============================================================================

STYLE_TEMPLATE = f"""
/* --------------------------- */
/*        GLOBAL STYLES        */
/* --------------------------- */

QWidget {{
    background-color: {PRIMARY_BG};
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL};
}}

/* --------------------------- */
/*        TAB WIDGETS          */
/* --------------------------- */

QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    background: {TAB_INACTIVE};
    border-radius: 5px;
    padding: 3px;
}}
QTabBar::tab {{
    background: {TAB_INACTIVE};
    color: {TEXT_PRIMARY};
    min-width: 100px;
    min-height: 30px;
    padding: 6px 20px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {TAB_ACTIVE};
    color: {ACCENT_COLOR};
    font-weight: bold;
}}
QTabBar::tab:hover {{
    background: {TAB_HOVER};
}}

/* --------------------------- */
/*        GROUPBOX             */
/* --------------------------- */

QGroupBox {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 5px;
    margin-top: 22px;
    font-weight: bold;
    font-size: {FONT_SIZE_HEADER};
    background: {PANEL_BG};
}}
QGroupBox:title {{
    subcontrol-origin: margin;
    subcontrol-position: top center;
    color: {ACCENT_COLOR};
    padding: 0px;
    margin-top: 0px;
    background: {PRIMARY_BG};
}}

/* --------------------------- */
/*           FRAME             */
/* --------------------------- */

QFrame {{
    border: 1px solid {PRIMARY_BG};
    background: {PRIMARY_BG};
}}

QFrame#tempSetGraph_frame,
QFrame#frame_sample,
QFrame#frameSetpoint,
QFrame#frameTempTime,
QFrame#Ttime_graph_frame,
QFrame#current_graph_frame,
QFrame#voltage_graph_frame,
QFrame#UnegUposTime_graph_frame,
QFrame#UnegUpos_graph_frame,
QFrame#data_graph_frame,
QFrame#iv_sweep_frame {{
    background: {PANEL_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 5px;
}}


QFrame#tempSetGraph_frame {{
    margin-top: 40px;
}}

QFrame#smp_frame {{
    background: {PANEL_BG};
}}
    

/* --------------------------- */
/*          LABELS             */
/* --------------------------- */

QLabel {{
    color: {TEXT_PRIMARY};
    font-size: {FONT_SIZE_NORMAL};
    background-color: {PANEL_BG};
    border: 1px solitd {PANEL_BG};
}}
QLabel:disabled {{
    color: {TEXT_DISABLED};
}}

QLabel#logo_icon {{
    background: {PRIMARY_BG};
}}

QLabel#sample_icon {{
    background: {PANEL_BG}
}}


/* --------------------------- */
/*     INPUT FIELDS            */
/* --------------------------- */

QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {WIDGET_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 2px;
    padding: 2px 7px;
    selection-background-color: {SELECTION_BG};
    selection-color: {SELECTION_TEXT};
}}

QTextEdit#plainLog {{
    font-family: {FONT_FAMILY_MONO};
    font-size: {FONT_SIZE_NORMAL};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1.5px solid {ACCENT_COLOR};
    background: {INPUT_FOCUS_BG};
}}
QLineEdit[readOnly="true"], QTextEdit[readOnly="true"], QPlainTextEdit[readOnly="true"] {{
    background: {PRIMARY_BG};
    color: {TEXT_READONLY};
}}

QLineEdit#contr_setpoint,
QLineEdit#calc_factor {{
    font-size: {FONT_SIZE_LARGE};
    font-weight: bold;
}}

QLineEdit#stabiholdtime {{
    font-size: 8pt;
}}

/* --------------------------- */
/*          BUTTONS            */
/* --------------------------- */

QPushButton {{
    background: {BTN_NORMAL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 5px;
    padding: 7px 18px;
    font-weight: 500;
    font-size: {FONT_SIZE_SMALL};
}}
QPushButton:hover {{
    background: {BTN_HOVER};
    color: {SELECTION_TEXT};
}}
QPushButton:pressed {{
    background: {BTN_PRESSED};
    color: {ACCENT_COLOR};
}}
QPushButton:disabled {{
    background: {BTN_DISABLED};
    color: {TEXT_DISABLED};
    border: 1px solid {TAB_INACTIVE};
}}
QPushButton#btnCancelProcess,
QPushButton#btnCancelProcess:hover {{
    background: {BTN_CANCEL};
    color: #fff;
    border: 1px solid #ab2323;
}}
QPushButton#btnCancelProcess:pressed {{
    background: {BTN_CANCEL_PRESSED};
}}

/* Stop Measurement Button - dezent rot */
QPushButton#stop_meas_btn {{
    background: {BTN_NORMAL};
    color: {BTN_CANCEL};
    border: 1.5px solid {BTN_CANCEL};
    border-radius: 5px;
    padding: 7px 18px;
    font-weight: 500;
    font-size: {FONT_SIZE_SMALL};
}}
QPushButton#stop_meas_btn:hover {{
    background: {BTN_CANCEL};
    color: #fff;
    border: 1.5px solid {BTN_CANCEL};
}}
QPushButton#stop_meas_btn:pressed {{
    background: {BTN_CANCEL_PRESSED};
    color: #fff;
    border: 1.5px solid {BTN_CANCEL_PRESSED};
}}

/* Start Measurement Button - dezent grün */
QPushButton#start_meas_btn {{
    background: {BTN_NORMAL};
    color: {BTN_START};
    border: 1.5px solid {BTN_START};
    border-radius: 5px;
    padding: 7px 18px;
    font-weight: 500;
    font-size: {FONT_SIZE_SMALL};
}}
QPushButton#start_meas_btn:hover {{
    background: {BTN_START};
    color: #fff;
    border: 1.5px solid {BTN_START};
}}
QPushButton#start_meas_btn:pressed {{
    background: {BTN_START_PRESSED};
    color: #fff;
    border: 1.5px solid {BTN_START_PRESSED};
}}

/* --------------------------- */
/*        COMBO BOX            */
/* --------------------------- */

QComboBox {{
    background: {WIDGET_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px 12px 4px 6px;
}}
QComboBox:focus {{
    border: 1.5px solid {ACCENT_COLOR};
    background: {PRIMARY_BG};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 2px;
    border-left: 1px solid {TAB_INACTIVE};
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    background: {PRIMARY_BG};
}}
QComboBox QAbstractItemView {{
    background: {PRIMARY_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {ACCENT_COLOR};
    selection-background-color: {SELECTION_BG};
    selection-color: {SELECTION_TEXT};
}}
QComboBox::hover {{
    border: 1.5px solid {ACCENT_COLOR};
}}

/* --------------------------- */
/*   CHECKBOX & RADIOBUTTON    */
/* --------------------------- */

QCheckBox, QRadioButton {{
    color: {TEXT_PRIMARY};
    font-size: {FONT_SIZE_TINY};
    padding: 5px 10;
    background-color: {PANEL_BG};
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
}}
QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {{
    border: 1.5px solid {BORDER_COLOR};
    background: {PRIMARY_BG};
    border-radius: 3px;
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    border: 1.5px solid {ACCENT_COLOR};
    background: {ACCENT_COLOR};
    border-radius: 3px;
}}

/* --------------------------- */
/*        SCROLLBARS           */
/* --------------------------- */

QScrollBar:vertical, QScrollBar:horizontal {{
    background: {SCROLLBAR_BG};
    border-radius: 4px;
    width: 12px;
    margin: 0px;
}}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: {SCROLLBAR_HANDLE};
    border-radius: 4px;
    min-height: 22px;
    min-width: 22px;
}}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background: {SCROLLBAR_HOVER};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    background: none;
    border: none;
    height: 0px;
    width: 0px;
}}

/* --------------------------- */
/*    PROGRESS BAR             */
/* --------------------------- */

QProgressBar {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    text-align: center;
    background: {PRIMARY_BG};
    color: {TEXT_PRIMARY};
    font-size: {FONT_SIZE_NORMAL};
}}
QProgressBar::chunk {{
    background: {ACCENT_COLOR};
    border-radius: 4px;
}}

/* --------------------------- */
/*         TOOLTIP             */
/* --------------------------- */

QToolTip {{
    background: {WIDGET_BG};
    color: #fff;
    border: 1.5px solid {ACCENT_COLOR};
    border-radius: 4px;
    font-size: {FONT_SIZE_SMALL};
    padding: 6px;
}}

/* --------------------------- */
/*      LISTS & TABLES         */
/* --------------------------- */

QListView, QTableView, QTreeView {{
    background: {PRIMARY_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    alternate-background-color: {ALTERNATE_ROW};
    selection-background-color: {SELECTION_BG};
    selection-color: {SELECTION_TEXT};
    font-size: {FONT_SIZE_TINY};
}}
QHeaderView::section {{
    background: {TAB_INACTIVE};
    color: {ACCENT_COLOR};
    border: 1px solid {BORDER_COLOR};
    font-weight: bold;
    font-size: {FONT_SIZE_HEADER};
    padding: 6px 0;
}}

/* --------------------------- */
/*   LED-artige QLabel (rund)  */
/* --------------------------- */

QLabel[styleSheet*="border-radius"] {{
    border: 2px solid {TAB_INACTIVE};
}}

/* --------------------------- */
/*          SPLITTER           */
/* --------------------------- */

QSplitter::handle {{
    background: {SCROLLBAR_HANDLE};
    border-radius: 4px;
}}
"""


# =============================================================================
# CONVENIENCE FUNKTIONEN
# =============================================================================

def get_dark_stylesheet():
    """
    Gibt das HTSSigma2 Dark Theme Stylesheet zurück.
    
    Returns:
        str: Komplettes Stylesheet als String
    """
    return STYLE_TEMPLATE


def apply_dark_theme(app_or_widget):
    """
    Wendet das Dark Theme auf eine QApplication oder QWidget an.
    
    Args:
        app_or_widget: QApplication oder QWidget Instanz
    """
    app_or_widget.setStyleSheet(STYLE_TEMPLATE)
