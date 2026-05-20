import sys
import os
import sqlite3
from PyQt6 import QtCore, QtGui, QtWidgets


from window import Ui_MainWindow


class MiVentana(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MiVentana()
    window.show()
    sys.exit(app.exec())