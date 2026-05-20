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

        self.configurar_base_de_datos()
        self.cargar_estilos()
        self.configurar_validadores()
        self.conectar_senales()

        # Carga inicial de datos
        self.actualizar_tabla()

        if hasattr(self.ui, 'cb_filtro_tipo'):
            self.ui.cb_filtro_tipo.clear()
            self.ui.cb_filtro_tipo.addItems(["Todos", "Cliente", "Empleado"])
        self.actualizar_tabla()

        # Ajuste de tabla Usuarios
        header_usuarios = self.ui.table_customer.horizontalHeader()
        header_usuarios.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

    def cargar_estilos(self) -> None:
        ruta_script = os.path.dirname(os.path.abspath(__file__))
        ruta_qss = os.path.join(ruta_script, "styles", "estilos.qss")

        if os.path.exists(ruta_qss):
            with open(ruta_qss, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"Ojo: No se ha encontrado el archivo de estilos en {ruta_qss}")

    def configurar_base_de_datos(self):
        try:
            ruta_base = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(ruta_base, "data", "bd.db")
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conexion = sqlite3.connect(self.db_path)


            self.conexion.execute('''
                CREATE TABLE IF NOT EXISTS Usuarios (
                    IDUsuario INTEGER PRIMARY KEY AUTOINCREMENT,
                    Nombre TEXT NOT NULL,
                    NIF_CIF TEXT,
                    Dirección TEXT,
                    Email TEXT NOT NULL,
                    Móvil TEXT,
                    Tipo TEXT NOT NULL
                )
            ''')
            self.conexion.commit()
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Error BBDD", str(e))

    def configurar_validadores(self) -> None:
        reg_nif = QtCore.QRegularExpression(r"^[0-9]{0,8}[A-Za-z]?$")
        self.ui.le_dni.setValidator(QtGui.QRegularExpressionValidator(reg_nif))
        reg_movil = QtCore.QRegularExpression(r"^[67][0-9]{0,8}$")
        self.ui.le_phone.setValidator(QtGui.QRegularExpressionValidator(reg_movil))

    def conectar_senales(self) -> None:
        self.ui.le_dni.textChanged.connect(self.validar_nif_visual)
        self.ui.le_phone.textChanged.connect(self.validar_movil_visual)

        # Botones CRUD Usuarios
        self.ui.btn_save_cust.clicked.connect(self.addUsuario)
        self.ui.btn_del_cust.clicked.connect(self.delUsuario)
        self.ui.btn_modify_cust.clicked.connect(self.modifUsuario)
        self.ui.btn_clear.clicked.connect(self.limpiar_campos)

        # Cargar datos al hacer clic en la tabla
        self.ui.table_customer.itemClicked.connect(self.selUsuario)
        if hasattr(self.ui, 'cb_filtro_tipo'):
            self.ui.cb_filtro_tipo.currentTextChanged.connect(self.actualizar_tabla)


    def validar_nif_visual(self):
        nif = self.ui.le_dni.text().upper()
        letras = "TRWAGMYFPDXBNJZSQVHLCKE"
        if len(nif) == 9 and nif[:8].isdigit() and nif[8].isalpha():
            if nif[8] == letras[int(nif[:8]) % 23]:
                self.ui.le_dni.setStyleSheet("background-color: #d4edda; color: black;")
            else:
                self.ui.le_dni.setStyleSheet("background-color: #f8d7da; color: black;")
        else:
            self.ui.le_dni.setStyleSheet("")

    def validar_movil_visual(self):
        if len(self.ui.le_phone.text()) == 9:
            self.ui.le_phone.setStyleSheet("background-color: #d4edda; color: black;")
        else:
            self.ui.le_phone.setStyleSheet("")


    def validacion_basica(self):
        """Cumple el requisito de: Nombre obligatorio, Email obligatorio, Tipo obligatorio"""
        nombre = self.ui.le_name.text().strip()
        email = self.ui.le_email.text().strip()

        if not nombre:
            QtWidgets.QMessageBox.warning(self, "Aviso", "El campo Nombre es obligatorio.")
            return False
        if not email:
            QtWidgets.QMessageBox.warning(self, "Aviso", "El campo Email es obligatorio.")
            return False
        if not self.ui.rb_electronic.isChecked() and not self.ui.rb_paper.isChecked():
            QtWidgets.QMessageBox.warning(self, "Aviso", "Debe seleccionar el Tipo (Cliente o Empleado).")
            return False
        return True

    def actualizar_tabla(self) -> None:
        """Renderizado dinámico de datos"""
        query = 'SELECT IDUsuario, Nombre, NIF_CIF, Dirección, Email, Móvil, Tipo FROM Usuarios'
        if hasattr(self.ui, 'cb_filtro_tipo'):
            filtro = self.ui.cb_filtro_tipo.currentText()
            if filtro == "Cliente":
                query += " WHERE Tipo = 'Cliente'"
            elif filtro == "Empleado":
                query += " WHERE Tipo = 'Empleado'"
        try:
            cursor = self.conexion.cursor()
            cursor.execute(query)
            usuarios = cursor.fetchall()

            self.ui.table_customer.setColumnCount(6)
            self.ui.table_customer.setHorizontalHeaderLabels(
                ["Nombre", "NIF/CIF", "Dirección", "Email", "Móvil", "Tipo"])
            self.ui.table_customer.setRowCount(0)

            for r_idx, r_data in enumerate(usuarios):
                self.ui.table_customer.insertRow(r_idx)
                for c_idx in range(1, len(r_data)):
                    val = r_data[c_idx]
                    item = QtWidgets.QTableWidgetItem(str(val) if val is not None else "")
                    if c_idx == 1:
                        item.setData(QtCore.Qt.ItemDataRole.UserRole, r_data[0])
                    self.ui.table_customer.setItem(r_idx, c_idx - 1, item)
        except sqlite3.Error as e:
            print(f"Error cargando tabla: {e}")

    def selUsuario(self) -> None:
        """Carga datos de la lista en el formulario"""
        fila = self.ui.table_customer.currentRow()
        if fila == -1: return

        def get_t(col):
            it = self.ui.table_customer.item(fila, col)
            return it.text() if it else ""

        self.ui.le_name.setText(get_t(0))
        self.ui.le_dni.setText(get_t(1))
        self.ui.le_address.setText(get_t(2))
        self.ui.le_email.setText(get_t(3))
        self.ui.le_phone.setText(get_t(4))

        tipo = get_t(5)
        if tipo == "Empleado":
            self.ui.rb_paper.setChecked(True)
        else:
            self.ui.rb_electronic.setChecked(True)

    def addUsuario(self):
        """Añade un usuario tras validar"""
        if not self.validacion_basica(): return
        tipo = "Empleado" if self.ui.rb_paper.isChecked() else "Cliente"
        try:
            self.conexion.execute(
                'INSERT INTO Usuarios (Nombre, NIF_CIF, Dirección, Email, Móvil, Tipo) VALUES (?,?,?,?,?,?)',
                (self.ui.le_name.text(), self.ui.le_dni.text(), self.ui.le_address.text(), self.ui.le_email.text(),
                 self.ui.le_phone.text(), tipo))
            self.conexion.commit()
            self.actualizar_tabla()
            self.limpiar_campos()
            QtWidgets.QMessageBox.information(self, "Éxito", "Usuario añadido correctamente.")
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def delUsuario(self):
        """Elimina usando delete"""
        fila = self.ui.table_customer.currentRow()
        if fila == -1:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Seleccione un usuario para eliminar.")
            return

        respuesta = QtWidgets.QMessageBox.question(self, "Confirmar", "¿Seguro que desea eliminar este usuario?",
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if respuesta == QtWidgets.QMessageBox.StandardButton.Yes:
            id_u = self.ui.table_customer.item(fila, 0).data(QtCore.Qt.ItemDataRole.UserRole)
            self.conexion.execute("DELETE FROM Usuarios WHERE IDUsuario = ?", (id_u,))
            self.conexion.commit()
            self.actualizar_tabla()
            self.limpiar_campos()

    def modifUsuario(self):
        """Modifica un usuario"""
        fila = self.ui.table_customer.currentRow()
        if fila == -1:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Seleccione un usuario para modificar.")
            return

        if not self.validacion_basica(): return

        id_u = self.ui.table_customer.item(fila, 0).data(QtCore.Qt.ItemDataRole.UserRole)
        tipo = "Empleado" if self.ui.rb_paper.isChecked() else "Cliente"
        try:
            self.conexion.execute(
                'UPDATE Usuarios SET Nombre=?, NIF_CIF=?, Dirección=?, Email=?, Móvil=?, Tipo=? WHERE IDUsuario=?',
                (self.ui.le_name.text(), self.ui.le_dni.text(), self.ui.le_address.text(), self.ui.le_email.text(),
                 self.ui.le_phone.text(), tipo, id_u))
            self.conexion.commit()
            self.actualizar_tabla()
            self.limpiar_campos()
            QtWidgets.QMessageBox.information(self, "Éxito", "Usuario modificado correctamente.")
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def limpiar_campos(self):
        for w in [self.ui.le_name, self.ui.le_dni, self.ui.le_address, self.ui.le_email, self.ui.le_phone]:
            w.clear()
            w.setStyleSheet("")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MiVentana()
    window.show()
    sys.exit(app.exec())