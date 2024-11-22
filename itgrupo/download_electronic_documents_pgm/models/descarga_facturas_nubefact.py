from odoo import models, fields, api
import requests
import os
import base64
import zipfile
import tempfile
class AccountMove(models.Model):
    _inherit = ['account.move']

    def download_invoices(self):
        selected_urls = [rec.l10n_pe_edi_pdf_file_link for rec in self]  # Obtener todas las URLs de impresión de las facturas seleccionadas
        selected_urls_xml = [rec.l10n_pe_edi_xml_file_link for rec in self]
        selected_urls_cdr = [rec.l10n_pe_edi_cdr_file_link for rec in self]
        selected_urls_cdr_void = [rec.l10n_pe_edi_cdr_void_file_link for rec in self]
        selected_urls_1 = [rec.ref for rec in self]
        if not selected_urls:
            print("No se han seleccionado facturas.")
            return
        # Crea un directorio temporal para almacenar los archivos descargados
        temp_dir = tempfile.mkdtemp()
        for url,url1,url_xml,url_cdr,url_crd_void in zip(selected_urls,selected_urls_1,selected_urls_xml,selected_urls_cdr,selected_urls_cdr_void):  # Iterar sobre las URLs y las facturas simultáneamente
            # Realiza una solicitud GET a la URL de la factura
            try:
                response = requests.get(url)
                # Verifica si la solicitud fue exitosa
                if response.status_code == 200:
                    # Obtén el nombre del archivo de la URL
                    file_name_ref = url1.split('/')[-1]
                    ref_value_1 = 'FACTURA'
                    ref_value = '.pdf'  # Asegúrate de que el nombre del campo "ref" sea correcto
                    file_name = f"{ref_value_1}-{file_name_ref}{ref_value}"
                    file_path = os.path.join(temp_dir, file_name)
                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                    print(f"Factura descargada: {file_name}")
                else:
                    print(f"Error al descargar la factura de la URL: {url}")
            except Exception as e:
                print(f"No se encontró el archivo CDR en la URL: {url}")
                print(f"Excepción: {e}")
            try:
                response_xml = requests.get(url_xml)
                if response_xml.status_code == 200:
                    # Obtener el nombre del archivo XML de la URL
                    ref_value = 'XML'
                    file_name_xml = f"{ref_value}-{file_name_ref}.xml"  # Utilizar una extensión de archivo .xml
                    file_path_xml = os.path.join(temp_dir, file_name_xml)
                    with open(file_path_xml, 'wb') as file_xml:
                        file_xml.write(response_xml.content)
                    print(f"Factura XML descargada: {file_name_xml}")
                else:
                    print(f"Error al descargar la factura XML de la URL: {url_xml}")
            except Exception as e:
                print(f"No se encontró el archivo CDR en la URL: {url_xml}")
                print(f"Excepción: {e}")

            try:
                response_cdr = requests.get(url_cdr)
                if response_cdr.status_code == 200:
                    # Obtener el nombre del archivo XML de la URL
                    ref_value = 'CDR'
                    file_name_cdr = f"{ref_value}-{file_name_ref}.xml"  # Utilizar una extensión de archivo .xml
                    file_path_cdr = os.path.join(temp_dir, file_name_cdr)
                    with open(file_path_cdr, 'wb') as file_cdr:
                        file_cdr.write(response_cdr.content)
                    print(f"Factura XML descargada: {file_name_cdr}")
                else:
                    print(f"Error al descargar la factura XML de la URL: {url_cdr}")
            except Exception as e:
                print(f"No se encontró el archivo CDR en la URL: {url_cdr}")
                print(f"Excepción: {e}")
            try:
                response_cdr = requests.get(url_crd_void)
                if response_cdr.status_code == 200:
                    # Obtener el nombre del archivo XML de la URL
                    ref_value = 'CDR-BAJA'
                    file_name_cdr = f"{ref_value}-{file_name_ref}.xml"  # Utilizar una extensión de archivo .xml
                    file_path_cdr = os.path.join(temp_dir, file_name_cdr)
                    with open(file_path_cdr, 'wb') as file_cdr:
                        file_cdr.write(response_cdr.content)
                    print(f"Factura XML descargada: {file_name_cdr}")
                else:
                    print(f"Error al descargar la factura XML de la URL: {url_crd_void}")
            except Exception as e:
                print(f"No se encontró el archivo CDR en la URL: {url_crd_void}")
                print(f"Excepción: {e}")
        # Ruta y nombre del archivo ZIP de salida
        zip_file_path = '/home/odoo/tmp/facturas.zip'
        # Crea un archivo ZIP con los archivos descargados
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            # Agrega los archivos descargados al archivo ZIP
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, arcname=file)
        f = open(zip_file_path, 'rb')
        return self.env['popup.it'].get_file('Documentos-Electrónicos.zip', base64.encodebytes(b''.join(f.readlines())))

