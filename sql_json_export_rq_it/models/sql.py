from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import os
import base64
from datetime import datetime


class SqlExportJson(models.Model):
    _inherit = 'sql.export'
    _description = 'Sql Export'

    file_format = fields.Selection(
        selection_add=[("json", "JSON")],
        ondelete={"json": "cascade"}
	  )


class SqlFileWizard(models.TransientModel):
    _inherit = 'sql.file.wizard'

    def export_sql(self):
        self.ensure_one()
        sql_export = self.sql_export_id

        # Manage Params
        variable_dict = {}
        if sql_export.field_ids:
              for field in sql_export.field_ids:
                  if field.ttype == "many2one":
                      variable_dict[field.name] = self[field.name].id
                  elif field.ttype == "many2many":
                      variable_dict[field.name] = tuple(self[field.name].ids)
                  else:
                      variable_dict[field.name] = self[field.name]
        if "%(company_id)s" in sql_export.query:
            company_id = self.env.company.id
            variable_dict["company_id"] = company_id
        if "%(user_id)s" in sql_export.query:
            user_id = self.env.user.id
            variable_dict["user_id"] = user_id

        # Call different method depending on file_type since the logic will be
        # different
        if sql_export.file_format == "json":
            query = sql_export.query
            # quiero ejecutar la query
            self._cr.execute(query)
            # obtengo los nombres de las columnas
            columns = [col.name for col in self._cr.description]
            # obtengo los datos
            data = self._cr.fetchall()

			      # creo un diccionario con los datos
            data_dict = {}
            for i, row in enumerate(data):
                data_dict[i] = {}
                for j, col in enumerate(columns):
                    # Convertir el valor datetime a una cadena
                    if isinstance(row[j], datetime):
                        data_dict[i][col] = row[j].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        data_dict[i][col] = row[j]

			# convierto el diccionario a json
            data_json = json.dumps(data_dict, indent=4)
			# Crear un archivo de texto
            file_name = "%s.txt" % sql_export.name
            with open(file_name, 'w') as file:
				# Escribir el contenido JSON en el archivo de texto
                file.write(data_json)

            # with open(file_name, 'r') as text_file:
            with open(file_name, 'rb') as binary_file:
                 binary_data = binary_file.read()

            self.write({
                'binary_file': base64.b64encode(binary_data),
                'file_name': file_name,
            })

            os.remove(file_name)

            return {
				'view_mode': 'form',
				'res_model': 'sql.file.wizard',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': self.env.context,
                'nodestroy': True,
            }

        method_name = "%s_get_data_from_query" % sql_export.file_format
        data = getattr(sql_export, method_name)(variable_dict)
        extension = sql_export._get_file_extension()
        self.write(
            {
                "binary_file": data,
                "file_name": "%(name)s.%(extension)s"
                % {"name": sql_export.name, "extension": extension},
            }
        )
        return {
            "view_mode": "form",
            "res_model": "sql.file.wizard",
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": self.env.context,
            "nodestroy": True,
        }
