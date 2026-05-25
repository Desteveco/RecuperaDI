from datetime import datetime
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtPrintSupport import QPrinter


def generar_pdf_usuarios(parent):
    try:
        ruta_archivo, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent, "Guardar Informe PDF", "Listado_Usuarios.pdf", "Archivos PDF (*.pdf)"
        )

        if not ruta_archivo:
            return

        cursor = parent.conexion.cursor()
        cursor.execute('SELECT Nombre, Email, Móvil, Tipo FROM Usuarios ORDER BY Nombre ASC')
        usuarios = cursor.fetchall()

        # 3. Fecha actual
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")

        # 4. Diseño HTML nativo
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ text-align: center; color: #333; }}
                .fecha {{ text-align: right; font-style: italic; color: #555; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #dddddd; padding: 8px; text-align: left; }}
                th {{ background-color: #0d6efd; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>LISTADO DE USUARIOS</h1>
            <div class="fecha">Fecha de Impresión: {fecha_actual}</div>

            <table>
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Email</th>
                        <th>Móvil</th>
                        <th>Tipo</th>
                    </tr>
                </thead>
                <tbody>
        """

        for u in usuarios:
            html += f"""
                    <tr>
                        <td>{u[0]}</td>
                        <td>{u[1]}</td>
                        <td>{u[2] if u[2] else ''}</td>
                        <td>{u[3]}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        # 5. Configurar el motor PDF de PyQt6
        documento = QtGui.QTextDocument()
        documento.setHtml(html)

        impresora = QPrinter(QPrinter.PrinterMode.HighResolution)
        impresora.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        impresora.setOutputFileName(ruta_archivo)

        # Imprimir al archivo
        documento.print(impresora)

        QtWidgets.QMessageBox.information(parent, "Éxito", "Informe PDF de Usuarios generado correctamente.")

    except Exception as e:
        # Hacemos un print para que, si vuelve a fallar, nos diga el motivo exacto en la terminal
        print(f"Error detallado: {e}")
        QtWidgets.QMessageBox.critical(parent, "Error", f"No se pudo generar el PDF:\n{e}")


def generar_pdf_tareas(parent):
    try:
        ruta_archivo, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent, "Guardar Informe PDF", "Listado_Tareas.pdf", "Archivos PDF (*.pdf)"
        )
        if not ruta_archivo:
            return
        # 2. Consultar la base de datos usando LEFT JOIN para evitar tareas fantasma
        cursor = parent.conexion.cursor()
        query = """
                SELECT T.IDTarea, 
                       IFNULL(C.Nombre, 'Usuario Borrado'), 
                       IFNULL(E.Nombre, 'Usuario Borrado'), 
                       T.Servicio, T.HorasTrabajadas, T.PrecioHora, T.Estado 
                FROM Tareas T 
                LEFT JOIN Usuarios C ON T.IDCliente = C.IDUsuario 
                LEFT JOIN Usuarios E ON T.IDEmpleado = E.IDUsuario
                ORDER BY T.IDTarea ASC
            """
        cursor.execute(query)
        tareas = cursor.fetchall()
        # CHIVATO: Esto imprimirá en la terminal de PyCharm/VSCode cuántas tareas detecta
        print(f"--- DEBUG: Se van a imprimir {len(tareas)} tareas en el PDF ---")
        if len(tareas) == 0:
            QtWidgets.QMessageBox.warning(parent, "Aviso",
                                          "No hay tareas registradas en la base de datos para imprimir.")
            return

        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ text-align: center; color: #333; }}
                .fecha {{ text-align: right; font-style: italic; color: #555; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 12px; }}
                th, td {{ border: 1px solid #dddddd; padding: 8px; text-align: left; }}
                th {{ background-color: #0d6efd; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .total {{ font-weight: bold; color: #198754; }}
            </style>
        </head>
        <body>
            <h1>LISTADO DE TAREAS</h1>
            <div class="fecha">Fecha de Impresión: {fecha_actual}</div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Cliente</th>
                        <th>Empleado</th>
                        <th>Servicio</th>
                        <th>Horas</th>
                        <th>Precio/h</th>
                        <th>Estado</th>
                        <th>Total (€)</th>
                    </tr>
                </thead>
                <tbody>
        """
        for t in tareas:
            id_t, cliente, empleado, servicio, horas_str, precio, estado = t
            total_calculado = 0.0
            if horas_str and precio:
                try:
                    h, m = map(int, horas_str.split(':'))
                    horas_decimales = h + (m / 60.0)
                    total_calculado = round(horas_decimales * float(precio), 2)
                except ValueError:
                    total_calculado = 0.0
            html += f"""
                    <tr>
                        <td>{id_t}</td>
                        <td>{cliente}</td>
                        <td>{empleado}</td>
                        <td>{servicio}</td>
                        <td>{horas_str}</td>
                        <td>{precio} €</td>
                        <td>{estado}</td>
                        <td class="total">{total_calculado} €</td>
                    </tr>
            """
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        documento = QtGui.QTextDocument()
        documento.setHtml(html)
        impresora = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        impresora.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        impresora.setOutputFileName(ruta_archivo)
        layout = impresora.pageLayout()
        layout.setOrientation(QtGui.QPageLayout.Orientation.Landscape)
        impresora.setPageLayout(layout)
        documento.print(impresora)
        QtWidgets.QMessageBox.information(parent, "Éxito", "Informe PDF de Tareas generado correctamente.")
    except Exception as e:
        print(f"Error detallado: {e}")
        QtWidgets.QMessageBox.critical(parent, "Error", f"No se pudo generar el PDF:\n{e}")