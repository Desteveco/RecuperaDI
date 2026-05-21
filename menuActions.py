from datetime import datetime
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtPrintSupport import QPrinter


def generar_pdf_usuarios(parent):
    try:
        # 1. Cuadro de diálogo para elegir dónde guardar
        ruta_archivo, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent, "Guardar Informe PDF", "Listado_Usuarios.pdf", "Archivos PDF (*.pdf)"
        )

        if not ruta_archivo:
            return  # El usuario canceló

        # 2. Obtener datos de la BD a través de la conexión de la ventana principal
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