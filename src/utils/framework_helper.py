import logging
import textwrap
from PyQt6.QtCore import QObject, pyqtSignal
import PyQt6.QtCore as QtCore


class GuiLogger(QObject, logging.Handler):
    '''Ein Logger, der Log-Nachrichten an eine Qt-Signal sendet.'''
    logger_signal = pyqtSignal(str, int, str)
    
    def __init__(self) -> None:
        QObject.__init__(self)
        logging.Handler.__init__(self)
        self.flushOnClose = False  # <-- wichtig! Damit beim Schließen keine Logs mehr geschrieben werden und es zu Referenzfehlern kommt
        
    def emit(self, record) -> None:
        log_entry = self.format(record)
        self.logger_signal.emit(log_entry, record.levelno, record.levelname)
        
    def close(self) -> None:
        super().close()


class WrappingFormatter(logging.Formatter):
    '''Ein Formatter, der Log-Nachrichten in mehrere Zeilen umbrechen kann.
    Dies ist nützlich, wenn die Log-Nachrichten zu lang sind, um in eine einzelne Zeile zu passen.
    Die nächste Zeile fängt wieder unter der ersten Message Zeile an, um den Log-Eintrag lesbar zu halten.'''
    def __init__(self, fmt, datefmt=None, width=120):
        super().__init__(fmt, datefmt=datefmt)
        self.width = width
        # Ein Basis‑Formatter, der nur Header+Message (ohne Tracebacks) liefert
        self._base = logging.Formatter(fmt, datefmt)
        
    def format(self, record):
        # 1) Erzeuge den vollständigen Log‑String mit Exception (falls vorhanden)
        full = super().format(record)
        # 2) Erzeuge nur Header+Message (ohne Traceback)
        no_exc = self._base.format(record)
        msg = record.getMessage()
        # 3) Trenne Prefix (Header) und Body (Message + ggf. Traceback)
        idx = no_exc.find(msg)
        prefix = no_exc[:idx]
        body = full[len(prefix):]  # alles ab Message inklusive Traceback
        
        # 4) Wrap jede Zeile im Body einzeln
        wrapped = []
        for line in body.splitlines():
            # textwrap.wrap bricht in einzelne Segmente <= width
            parts = textwrap.wrap(line, width=self.width) or ['']
            for i, part in enumerate(parts):
                if i == 0:
                    wrapped.append(prefix + part)
                else:
                    wrapped.append(' ' * len(prefix) + part)
                    
        return "\n".join(wrapped)


class NoScrollFilter(QtCore.QObject):
    """Event-Filter, um das Maus-Scrollen in QComboBoxen zu verhindern. 
    Da sich sonst Einstellungen ungewollt verändern können"""
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.Wheel:
            return True
        return super().eventFilter(obj, event)
