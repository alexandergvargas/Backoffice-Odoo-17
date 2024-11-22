--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_percepciones_usd(date, date, integer,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_percepciones_usd(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(periodo_con integer, periodo_percep integer, fecha_uso date, libro character varying, voucher character varying, tipo_per character varying, 
	ruc_agente character varying, partner character varying, tipo_comp character varying, serie_cp character varying, numero_cp character varying, 
	fecha_com_per date, percepcion numeric, t_comp character varying, serie_comp character varying, numero_comp character varying, 
	fecha_cp date, montof numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT CASE
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
		ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
	END AS periodo_con,
	to_char(am.perception_date::timestamp with time zone, 'yyyymm'::text)::integer AS periodo_percep,
	am.perception_date AS fecha_uso,
	aj.code as libro,
	am.vou_number as voucher,
	llit.l10n_pe_vat_code as tipo_per,
	rp.vat as ruc_agente,
	rp.name as partner,
	lldt.code AS tipo_comp,
	CASE
		WHEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2) <> ''::text THEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 1)::character varying
		ELSE ''::character varying
	END AS serie_cp,
	CASE
		WHEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2) <> ''::text THEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2)::character varying
		ELSE split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 1)::character varying
	END AS numero_cp,
	am.invoice_date AS fecha_com_per,
	aml.tax_amount_me AS percepcion,
	dir.t_comp,
	CASE
		WHEN split_part(dir.nro_comprobante::text, '-'::text, 2) <> ''::text THEN split_part(dir.nro_comprobante::text, '-'::text, 1)::character varying
		ELSE ''::character varying
	END AS serie_comp,
	CASE
		WHEN split_part(dir.nro_comprobante::text, '-'::text, 2) <> ''::text THEN split_part(dir.nro_comprobante::text, '-'::text, 2)::character varying
		ELSE split_part(dir.nro_comprobante::text, '-'::text, 1)::character varying
	END AS numero_comp,
	dir.date AS fecha_cp,

	CASE
		WHEN am.currency_id = $4 THEN dir.amount_currency
		ELSE dir.amount/am.currency_rate	  
	END AS montof  	
	FROM account_move_line aml
  	LEFT JOIN account_move am on am.id = aml.move_id
   	LEFT JOIN account_journal aj ON aj.id = am.journal_id
	LEFT JOIN res_partner rp ON rp.id = aml.partner_id
	LEFT JOIN l10n_latam_identification_type llit ON llit.id = rp.l10n_latam_identification_type_id
	LEFT JOIN l10n_latam_document_type lldt ON lldt.id = aml.type_document_id
	LEFT JOIN ( SELECT b2.code,
			b1.date,
			b1.nro_comprobante,
			b1.amount,
			b1.amount_currency,
			b2.code as t_comp,
			b1.move_id
		   	FROM doc_invoice_relac b1
			LEFT JOIN l10n_latam_document_type b2 ON b2.id = b1.type_document_id) dir ON dir.move_id = aml.move_id
	LEFT JOIN account_account_tag_account_move_line_rel rel ON rel.account_move_line_id = aml.id
  	WHERE rel.account_account_tag_id = (select prm.tax_account
										from account_main_parameter prm where prm.company_id = $3)
			and am.company_id = $3 and (am.perception_date::date between $1 and $2);
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_percepciones_sp_usd(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_percepciones_sp_usd(
	  date_from date,
	date_to date,
	  company_id integer)
	RETURNS TABLE(periodo_con integer, periodo_percep integer, fecha_uso date, libro character varying, voucher character varying, 
	tipo_per character varying, ruc_agente character varying, partner character varying, tipo_comp character varying, serie_cp character varying, 
	numero_cp character varying, fecha_com_per date, percepcion numeric) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	 SELECT
	CASE
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
		ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
	END AS periodo_con,
	to_char(am.perception_date::timestamp with time zone, 'yyyymm'::text)::integer AS periodo_percep,
	am.perception_date AS fecha_uso,
	aj.code as libro,
	am.vou_number as voucher,
	llit.l10n_pe_vat_code as tipo_per,
	rp.vat as ruc_agente,
	rp.name as partner,
	  lldt.code AS tipo_comp,
	CASE
		WHEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2) <> ''::text THEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 1)::character varying
		ELSE ''::character varying
	END AS serie_cp,
	CASE
		WHEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2) <> ''::text THEN split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 2)::character varying
		ELSE split_part(REPLACE(aml.nro_comp,'/','-')::text, '-'::text, 1)::character varying
	END AS numero_cp,
	am.invoice_date AS fecha_com_per,
	aml.tax_amount_me AS percepcion
	FROM account_move_line aml
	LEFT JOIN account_move am on am.id = aml.move_id
	LEFT JOIN account_journal aj ON aj.id = am.journal_id
	LEFT JOIN res_partner rp ON rp.id = aml.partner_id
	LEFT JOIN l10n_latam_identification_type llit ON llit.id = rp.l10n_latam_identification_type_id
	LEFT JOIN l10n_latam_document_type lldt ON lldt.id = aml.type_document_id
  	LEFT JOIN account_account_tag_account_move_line_rel rel ON rel.account_move_line_id = aml.id
  	WHERE rel.account_account_tag_id = (select prm.tax_account
						from account_main_parameter prm where prm.company_id = $3)
		and am.company_id = $3 and (am.perception_date::date between $1 and $2);
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------

