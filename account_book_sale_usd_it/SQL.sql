DROP FUNCTION IF EXISTS public.get_ventas_1_1_usd(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_ventas_1_1_usd(
	date_from date,
	date_to date,
	company_id integer)
RETURNS TABLE(periodo integer, fecha_cont date,libro character varying, voucher character varying, fecha_e date, fecha_v date,
	td character varying, serie character varying, anio character varying, numero character varying, tdp character varying, docp character varying,
	namep character varying, exp numeric, venta_g numeric, inaf numeric, exo numeric, isc_v numeric, otros_v numeric, igv_v numeric, icbper numeric,
	total numeric, name character varying, currency_rate numeric, fecha_det date, comp_det character varying, f_doc_m date,
	td_doc_m character varying, serie_m character varying, numero_m character varying, glosa character varying, estado_ple character varying, am_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT CASE
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
		WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
		ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
		END AS periodo,
			am.date AS fecha_cont,
			aj.code AS libro,
			am.vou_number AS voucher,
			am.invoice_date AS fecha_e,
			am.invoice_date_due AS fecha_v,
			ec1.code AS td,
			CASE
				WHEN split_part(am.nro_comp, '-', 2) <> '' THEN split_part(am.nro_comp, '-', 1)::character varying
				ELSE ''
			END
			AS serie,
			CASE
				WHEN ec1.code = '50' THEN to_char(am.invoice_date , 'yyyy')::character varying
				ELSE NULL
			END AS anio,
			CASE
				WHEN split_part(am.nro_comp, '-', 2) <> '' THEN split_part(am.nro_comp, '-', 2)::character varying
				ELSE split_part(am.nro_comp, '-', 1)::character varying
			END
			AS numero,
			lit.l10n_pe_vat_code AS tdp,
			rp.vat AS docp,
			rp.name AS namep,
			coalesce(mv.exp_me,0) as exp,
			coalesce(mv.venta_g_me,0) as venta_g,
			coalesce(mv.inaf_me,0) as inaf,
			coalesce(mv.exo_me,0) as exo,
			coalesce(mv.isc_v_me,0) as isc_v,
			coalesce(mv.otros_v_me,0) as otros_v,
			coalesce(mv.igv_v_me,0) as igv_v,
			coalesce(mv.icbper_me,0) as icbper,
			(coalesce(mv.exp_me,0) + coalesce(mv.venta_g_me,0) + coalesce(mv.inaf_me,0) + coalesce(mv.exo_me,0) + coalesce(mv.isc_v_me,0) + 
			coalesce(mv.otros_v_me,0) + coalesce(mv.igv_v_me,0) + coalesce(mv.icbper_me,0)) AS total,
			rc.name,
			am.currency_rate,
			am.l10n_pe_detraction_date AS fecha_det,
			am.l10n_pe_detraction_number AS comp_det,
			dr.date AS f_doc_m,
			eic1.code AS td_doc_m,
			CASE
				WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 1)::character varying
				ELSE null
			END
			AS serie_m,
			CASE
				WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 2)::character varying
				ELSE split_part(dr.nro_comprobante, '-', 1)::character varying
			END
			AS numero_m,
			am.glosa,
			am.campo_34_sale AS estado_ple,
			am.id::integer as am_id
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
			 LEFT JOIN get_ventas_1($1,$2,$3) mv ON mv.move_id = am.id
			 LEFT JOIN res_currency rc ON rc.id = am.currency_id
		  WHERE aj.register_sunat::text = '2'::text AND am.state::text = 'posted'::text
		  AND (am.date::date BETWEEN $1 and $2) AND am.company_id = $3
		  ORDER BY ("left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6)), aj.code, am.vou_number;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;