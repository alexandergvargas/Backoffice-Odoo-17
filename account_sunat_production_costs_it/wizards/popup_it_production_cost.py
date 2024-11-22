# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PopupITProductionCost(models.TransientModel):
	_name = 'popup.it.production.cost'
	_description = 'Popup IT Production Cost'

	name = fields.Char()
	output_name_1 = fields.Char(string='Nombre del Archivo 1')
	output_file_1 = fields.Binary(string=u'REGISTRO DE COSTOS - ESTADO DE COSTO DE VENTAS ANUAL',readonly=True,filename="output_name_1")
	output_name_2 = fields.Char(string='Nombre del Archivo 2')
	output_file_2 = fields.Binary(string='REGISTRO DE COSTOS - ELEMENTOS DEL COSTO MENSUAL',readonly=True,filename="output_name_2")
	output_name_3 = fields.Char(string='Nombre del Archivo 3')
	output_file_3 = fields.Binary(string='REGISTRO DE COSTOS - ESTADO DE COSTO DE PRODUCCION VALORIZADO ANUAL',readonly=True,filename="output_name_3")
	output_name_4 = fields.Char(string='Nombre del Archivo 4')
	output_file_4 = fields.Binary(string='REGISTRO DE COSTOS - CENTRO DE COSTOS',readonly=True,filename="output_name_4")

	def get_file(self,output_name_1,output_file_1,
					output_name_2,output_file_2,
					output_name_3,output_file_3,
					output_name_4,output_file_4):
		wizard = self.create({'output_name_1':output_name_1,'output_file_1':output_file_1,
							'output_name_2':output_name_2,'output_file_2':output_file_2,
							'output_name_3':output_name_3,'output_file_3':output_file_3,
							'output_name_4':output_name_4,'output_file_4':output_file_4})
		return {
			"type":"ir.actions.act_window",
			"res_model":"popup.it.production.cost",
			"views":[[self.env.ref('account_sunat_production_costs_it.popup_it_production_cost_form').id,"form"]],
			"res_id":wizard.id,
			"target":"new",
		}