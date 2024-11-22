--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_recxhon_1_usd(date, date, integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_recxhon_1_usd(
	date_from date,
	date_to date,
	  company_id integer,
	by_date character varying)
	RETURNS TABLE(move_id integer, renta numeric, retencion numeric)  AS
	$BODY$
	BEGIN
	RETURN QUERY  
  	SELECT am.id as move_id,
	sum(
		CASE
			WHEN aat.record_fees::text = '1'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS renta,
	sum(
		CASE
			WHEN aat.record_fees::text = '2'::text THEN aml.tax_amount_me
			ELSE 0::numeric
		END) AS retencion
   FROM account_move_line aml
	LEFT JOIN account_account_tag_account_move_line_rel rel ON rel.account_move_line_id = aml.id
	LEFT JOIN account_account_tag aat ON aat.id = rel.account_account_tag_id
	LEFT JOIN account_move am on am.id = aml.move_id
	LEFT JOIN account_journal aj ON aj.id = am.journal_id
	
	LEFT JOIN (SELECT  aml.account_id,
				aml.partner_id,
				aml.type_document_id,
				aml.nro_comp,
				max(am.date) as fecha_pago 
				FROM account_move_line aml
				LEFT JOIN account_move am ON am.id = aml.move_id
				LEFT JOIN account_account aa ON aa.id = aml.account_id
				WHERE  
					am.state='posted' 
				AND aml.debit<>0
				AND aa.account_type='liability_payable'
				AND am.company_id=$3
				AND am.state='posted'
				GROUP BY aml.account_id,aml.partner_id,aml.type_document_id,aml.nro_comp
			)pagos ON concat(am.l10n_latam_document_type_id,am.partner_id,am.nro_comp)=concat(pagos.type_document_id,pagos.partner_id,pagos.nro_comp)

	WHERE aj.register_sunat = '3' AND  am.state::text = 'posted'::text AND aml.account_id IS NOT NULL 
	AND ((CASE WHEN $4 = 'date' THEN am.date WHEN $4 = 'invoice_date_due' THEN am.invoice_date_due WHEN $4 = 'payment_date' THEN pagos.fecha_pago END) BETWEEN $1 and $2) AND am.company_id = $3
	AND rel.account_account_tag_id IS NOT NULL
  GROUP BY am.id;
 END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_recxhon_1_1_usd(date, date, integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_recxhon_1_1_usd(
	  date_from date,
	date_to date,
	  company_id integer,
	by_date character varying)
	RETURNS TABLE(periodo integer, libro character varying,voucher character varying, fecha_doc date, fecha_e date, fecha_p date, td character varying,
	serie character varying,numero character varying,tdp character varying,docp character varying,apellido_p character varying,apellido_m character varying,namep character varying,
	divisa character varying, tipo_c numeric, renta numeric, retencion numeric, neto_p numeric,
	periodo_p character varying, is_not_home character varying, c_d_imp character varying, am_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT CASE
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
	ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
	END AS periodo,
	aj.code AS libro,
	am.vou_number AS voucher,
	am.date AS fecha_doc,
	am.invoice_date AS fecha_e,
	am.invoice_date_due AS fecha_p,
	ec1.code AS td,
	CASE
		WHEN split_part(am.nro_comp::text, '-'::text, 2) <> ''::text THEN split_part(am.nro_comp::text, '-'::text, 1)::character varying
		ELSE ''::character varying
	END AS serie,
	CASE
		WHEN split_part(am.nro_comp::text, '-'::text, 2) <> ''::text THEN split_part(am.nro_comp::text, '-'::text, 2)::character varying
		ELSE split_part(am.nro_comp::text, '-'::text, 1)::character varying
	END AS numero,
	lit.l10n_pe_vat_code AS tdp,
	rp.vat AS docp,
	rp.last_name AS apellido_p,
	rp.m_last_name AS apellido_m,
	rp.name_p AS namep,
	rc.name AS divisa,
	am.currency_rate AS tipo_c,
	rh.renta,
	rh.retencion,
	rh.renta + rh.retencion AS neto_p,
	to_char(am.invoice_date_due::timestamp with time zone, 'yyyymm'::text)::character varying AS periodo_p,
	CASE
		WHEN rp.is_not_home IS NULL OR rp.is_not_home = false THEN '1'::character varying
		ELSE '2'::character varying
	END AS is_not_home,
	rp.c_d_imp,
	am.id AS am_id
	FROM account_move am
	LEFT JOIN account_journal aj ON aj.id = am.journal_id
	LEFT JOIN res_partner rp ON rp.id = am.partner_id
	LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
	LEFT JOIN l10n_latam_document_type ec1 ON ec1.id = am.l10n_latam_document_type_id
	LEFT JOIN ( SELECT a2.type_document_id,
		  a2.date,
		  a2.nro_comprobante,
		  a2.amount_currency,
		  a2.amount,
		  a2.bas_amount,
		  a2.tax_amount,
		  a2.id,
		  a2.move_id
		  FROM doc_rela_pri a1
			LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = am.id
	LEFT JOIN l10n_latam_document_type eic1 ON eic1.id = dr.type_document_id
	LEFT JOIN get_recxhon_1_usd($1,$2,$3,$4) rh ON rh.move_id = am.id
	LEFT JOIN res_currency rc ON rc.id = am.currency_id
	LEFT JOIN (SELECT  aml.account_id,
				aml.partner_id,
				aml.type_document_id,
				aml.nro_comp,
				max(am.date) as fecha_pago 
				FROM account_move_line aml
				LEFT JOIN account_move am ON am.id = aml.move_id
				LEFT JOIN account_account aa ON aa.id = aml.account_id
				WHERE  
					am.state='posted' 
				AND aml.debit<>0
				AND aa.account_type='liability_payable'
				AND am.company_id=$3
				AND am.state='posted'
				GROUP BY aml.account_id,aml.partner_id,aml.type_document_id,aml.nro_comp
			)pagos ON concat(am.l10n_latam_document_type_id,am.partner_id,am.nro_comp)=concat(pagos.type_document_id,pagos.partner_id,pagos.nro_comp)
	WHERE aj.register_sunat = '3' AND am.state::text = 'posted'::text AND aj.type = 'purchase'
	AND ((CASE WHEN $4 = 'date' THEN am.date WHEN $4 = 'invoice_date_due' THEN am.invoice_date_due WHEN $4 = 'payment_date' THEN pagos.fecha_pago END) BETWEEN $1 and $2) AND am.company_id = $3
  ORDER BY to_char(am.date::timestamp with time zone, 'yyyymm'::text), aj.code, am.vou_number;
 END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
