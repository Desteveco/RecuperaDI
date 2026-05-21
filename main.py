import sys
import os
import sqlite3
from PyQt6 import QtCore, QtGui, QtWidgets


from window import Ui_MainWindow
from menuActions import generar_pdf_usuarios


class MiVentana(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setFixedSize(1024, 768)

        self.configurar_base_de_datos()
        self.cargar_estilos()
        self.configurar_validadores()
        self.conectar_senales()

        # Carga inicial de datos
        self.actualizar_tabla()
        # Inicializar combos de tareas
        self.actualizar_combos_tareas()

        if hasattr(self.ui, 'cb_filtro_tipo'):
            self.ui.cb_filtro_tipo.clear()
            self.ui.cb_filtro_tipo.addItems(["Todos", "Cliente", "Empleado"])
        self.actualizar_tabla()

        # Menú Informes
        if hasattr(self.ui, 'actionListado_Usuarios'):
            self.ui.actionListado_Usuarios.triggered.connect(lambda: generar_pdf_usuarios(self))
        # Ajuste de tabla Usuarios
        header_usuarios = self.ui.table_customer.horizontalHeader()
        header_usuarios.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)


        # AÑADE ESTO: Ajuste de tabla Tareas al 100%
        header_tareas = self.ui.table_product.horizontalHeader()
        header_tareas.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

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
            # Creación tabla Tareas
            self.conexion.execute('''
                            CREATE TABLE IF NOT EXISTS Tareas (
                                IDTarea INTEGER PRIMARY KEY AUTOINCREMENT,
                                IDCliente INTEGER NOT NULL,
                                IDEmpleado INTEGER NOT NULL,
                                Servicio TEXT,
                                HorasTrabajadas TEXT,
                                PrecioHora REAL,
                                Estado TEXT,
                                FOREIGN KEY(IDCliente) REFERENCES Usuarios(IDUsuario),
                                FOREIGN KEY(IDEmpleado) REFERENCES Usuarios(IDUsuario)
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

        # Señales y Filtros de Tareas
        if hasattr(self.ui, 'btn_save_task'):
            self.ui.btn_save_task.clicked.connect(self.addTarea)
            self.ui.btn_modify_task.clicked.connect(self.modifTarea)
            self.ui.btn_del_task.clicked.connect(self.delTarea)
            self.ui.btn_clear_task.clicked.connect(self.limpiar_campos_tarea)
            self.ui.table_product.itemClicked.connect(self.selTarea)

            self.ui.cb_cliente.currentIndexChanged.connect(self.actualizar_tabla_tareas)
            self.ui.cb_empleado.currentIndexChanged.connect(self.actualizar_tabla_tareas)


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
            self.actualizar_combos_tareas()
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
            self.actualizar_combos_tareas()
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
            self.actualizar_combos_tareas()
            self.limpiar_campos()
            QtWidgets.QMessageBox.information(self, "Éxito", "Usuario modificado correctamente.")
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def limpiar_campos(self):
        for w in [self.ui.le_name, self.ui.le_dni, self.ui.le_address, self.ui.le_email, self.ui.le_phone]:
            w.clear()
            w.setStyleSheet("")

        # ==========================
        # LÓGICA TAREAS
        # ==========================
    def actualizar_combos_tareas(self):
        """Carga clientes y empleados desde la BD"""
        if not hasattr(self.ui, 'cb_cliente'): return
        try:
            cursor = self.conexion.cursor()
            self.ui.cb_cliente.blockSignals(True)
            self.ui.cb_empleado.blockSignals(True)
            self.ui.cb_cliente.clear()
            self.ui.cb_empleado.clear()
            # Opción vacía para poder ver toda la tabla sin filtros
            self.ui.cb_cliente.addItem("--- Todos / Seleccionar ---", None)
            self.ui.cb_empleado.addItem("--- Todos / Seleccionar ---", None)
            cursor.execute("SELECT IDUsuario, Nombre FROM Usuarios WHERE Tipo='Cliente'")
            for cli in cursor.fetchall():
                self.ui.cb_cliente.addItem(cli[1], cli[0])
            cursor.execute("SELECT IDUsuario, Nombre FROM Usuarios WHERE Tipo='Empleado'")
            for emp in cursor.fetchall():
                self.ui.cb_empleado.addItem(emp[1], emp[0])
            self.ui.cb_cliente.blockSignals(False)
            self.ui.cb_empleado.blockSignals(False)
            self.actualizar_tabla_tareas()
        except sqlite3.Error as e:
            print(e)
    def actualizar_tabla_tareas(self):
        """Renderizado de tabla y filtrado dinámico"""
        if not hasattr(self.ui, 'cb_cliente'): return
        query = """
            SELECT T.IDTarea, C.Nombre, E.Nombre, T.Servicio, T.HorasTrabajadas, T.PrecioHora, T.Estado 
            FROM Tareas T 
            JOIN Usuarios C ON T.IDCliente = C.IDUsuario 
            JOIN Usuarios E ON T.IDEmpleado = E.IDUsuario
        """
        filtros, params = [], []
        id_cli = self.ui.cb_cliente.currentData()
        if id_cli:
            filtros.append("T.IDCliente = ?")
            params.append(id_cli)
        id_emp = self.ui.cb_empleado.currentData()
        if id_emp:
            filtros.append("T.IDEmpleado = ?")
            params.append(id_emp)
        if filtros:
            query += " WHERE " + " AND ".join(filtros)
        try:
            cursor = self.conexion.cursor()
            cursor.execute(query, params)
            tareas = cursor.fetchall()
            self.ui.table_product.setColumnCount(6)
            self.ui.table_product.setHorizontalHeaderLabels(
                ["Cliente", "Empleado", "Servicio", "Horas", "Precio/h", "Estado"])
            self.ui.table_product.setRowCount(0)
            for r_idx, r_data in enumerate(tareas):
                self.ui.table_product.insertRow(r_idx)
                for c_idx in range(1, len(r_data)):
                    val = r_data[c_idx]
                    item = QtWidgets.QTableWidgetItem(str(val) if val is not None else "")
                    if c_idx == 1:
                        item.setData(QtCore.Qt.ItemDataRole.UserRole, r_data[0])
                    self.ui.table_product.setItem(r_idx, c_idx - 1, item)
        except sqlite3.Error as e:
            print(e)
    def selTarea(self):
        """Cargar formulario bloqueando señales y guardando el ID en memoria"""
        fila = self.ui.table_product.currentRow()
        if fila == -1: return

        # ¡NUEVO!: Guardamos el ID de la tarea en la memoria de la clase
        self.tarea_seleccionada = self.ui.table_product.item(fila, 0).data(QtCore.Qt.ItemDataRole.UserRole)

        self.ui.cb_cliente.blockSignals(True)
        self.ui.cb_empleado.blockSignals(True)

        self.ui.cb_cliente.setCurrentText(self.ui.table_product.item(fila, 0).text())
        self.ui.cb_empleado.setCurrentText(self.ui.table_product.item(fila, 1).text())

        self.ui.cb_cliente.blockSignals(False)
        self.ui.cb_empleado.blockSignals(False)

        self.ui.le_servicio.setText(self.ui.table_product.item(fila, 2).text())
        horas = self.ui.table_product.item(fila, 3).text()
        if horas:
            self.ui.te_horas.setTime(QtCore.QTime.fromString(horas, "HH:mm"))
        precio = self.ui.table_product.item(fila, 4).text()
        if precio:
            self.ui.sp_precio.setValue(float(precio))
        self.ui.cb_estado.setCurrentText(self.ui.table_product.item(fila, 5).text())
    def validacion_tareas(self):
        if not self.ui.cb_cliente.currentData():
            QtWidgets.QMessageBox.warning(self, "Aviso", "Seleccione un Cliente.")
            return False
        if not self.ui.cb_empleado.currentData():
            QtWidgets.QMessageBox.warning(self, "Aviso", "Seleccione un Empleado.")
            return False
        if self.ui.sp_precio.value() <= 0:
            QtWidgets.QMessageBox.warning(self, "Aviso", "El precio debe ser mayor a 0.")
            return False
        return True

    def addTarea(self):
        if not self.validacion_tareas(): return
        try:
            # Leemos los valores uno a uno para detectar dónde falla si hay un error
            id_cli = self.ui.cb_cliente.currentData()
            id_emp = self.ui.cb_empleado.currentData()
            servicio = self.ui.le_servicio.text()
            horas = self.ui.te_horas.time().toString("HH:mm")
            precio = self.ui.sp_precio.value()
            estado = self.ui.cb_estado.currentText()

            self.conexion.execute(
                "INSERT INTO Tareas (IDCliente, IDEmpleado, Servicio, HorasTrabajadas, PrecioHora, Estado) VALUES (?,?,?,?,?,?)",
                (id_cli, id_emp, servicio, horas, precio, estado)
            )
            self.conexion.commit()

            # Recargamos la tabla y limpiamos
            self.actualizar_tabla_tareas()
            self.limpiar_campos_tarea()

            QtWidgets.QMessageBox.information(self, "Éxito", "Tarea añadida correctamente.")

        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Error de Base de Datos", str(e))
        except Exception as e:
            # Esto evita el crash 0xC0000409 y te dice exactamente qué está fallando
            print(f"Fallo en Python: {e}")
            QtWidgets.QMessageBox.critical(self, "Error de Código",
                                           f"Asegúrate de que te_horas es QTimeEdit y sp_precio es QDoubleSpinBox en Qt Designer.\nError: {e}")

    def modifTarea(self):
        # ¡NUEVO!: Verificamos la memoria en lugar de la fila de la tabla
        if not hasattr(self, 'tarea_seleccionada') or self.tarea_seleccionada is None:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Seleccione una tarea de la tabla para modificarla.")
            return

        if not self.validacion_tareas(): return

        try:
            self.conexion.execute(
                "UPDATE Tareas SET IDCliente=?, IDEmpleado=?, Servicio=?, HorasTrabajadas=?, PrecioHora=?, Estado=? WHERE IDTarea=?",
                (self.ui.cb_cliente.currentData(), self.ui.cb_empleado.currentData(), self.ui.le_servicio.text(),
                 self.ui.te_horas.time().toString("HH:mm"), self.ui.sp_precio.value(), self.ui.cb_estado.currentText(),
                 self.tarea_seleccionada)
            )
            self.conexion.commit()
            self.limpiar_campos_tarea()
            self.actualizar_tabla_tareas()
            QtWidgets.QMessageBox.information(self, "Éxito", "Tarea modificada.")
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def delTarea(self):
        # ¡NUEVO!: Verificamos la memoria en lugar de la fila de la tabla
        if not hasattr(self, 'tarea_seleccionada') or self.tarea_seleccionada is None:
            QtWidgets.QMessageBox.warning(self, "Aviso", "Seleccione una tarea de la tabla para eliminarla.")
            return

        respuesta = QtWidgets.QMessageBox.question(self, "Confirmar", "¿Eliminar tarea?",
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        if respuesta == QtWidgets.QMessageBox.StandardButton.Yes:
            self.conexion.execute("DELETE FROM Tareas WHERE IDTarea = ?", (self.tarea_seleccionada,))
            self.conexion.commit()
            self.limpiar_campos_tarea()
            self.actualizar_tabla_tareas()

    def limpiar_campos_tarea(self):
        # ¡NUEVO!: Borramos la memoria
        self.tarea_seleccionada = None

        self.ui.cb_cliente.setCurrentIndex(0)
        self.ui.cb_empleado.setCurrentIndex(0)
        self.ui.le_servicio.clear()
        self.ui.te_horas.setTime(QtCore.QTime(0, 0))
        self.ui.sp_precio.setValue(0.0)
        self.ui.cb_estado.setCurrentIndex(0)
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MiVentana()
    window.show()
    sys.exit(app.exec())