------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_diariog_usd(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_diariog_usd(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(periodo integer, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, haber numeric, balance numeric, moneda character varying, 
	tc numeric, glosa character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, 
	nro_comprobante character varying, fecha_doc date, fecha_ven date, col_reg character varying, monto_reg numeric, medio_pago character varying, ple_diario character varying, ple_compras character varying,
	ple_ventas character varying, move_id integer, move_line_id integer, account_id integer, partner_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
	SELECT
	CASE
		WHEN a1.is_opening_close = true AND to_char(a1.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(a1.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
		WHEN a1.is_opening_close = true AND to_char(a1.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(a1.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
		ELSE to_char(a1.date::timestamp with time zone, 'yyyymm'::text)::integer
	END AS periodo,
	a1.date AS fecha,
	a3.code AS libro,
	a1.vou_number AS voucher,
	a4.code AS cuenta,
	case when a5.name = 'USD' then (case when a2.amount_currency> 0 then a2.amount_currency else 0 end) else round(case when convert_currency(a2.currency_id,1,a2.amount_currency,(case when a1.move_type = 'entry' then a1.date else a1.invoice_date end),a2.company_id)>0 then convert_currency(a2.currency_id,1,a2.amount_currency,(case when a1.move_type = 'entry' then a1.date else a1.invoice_date end),a2.company_id) else 0 end,2) end AS debe,
	case when a5.name = 'USD' then (case when a2.amount_currency< 0 then abs(a2.amount_currency) else 0 end) else round(case when convert_currency(a2.currency_id,1,a2.amount_currency,(case when a1.move_type = 'entry' then a1.date else a1.invoice_date end),a2.company_id)<0 then abs(convert_currency(a2.currency_id,1,a2.amount_currency,(case when a1.move_type = 'entry' then a1.date else a1.invoice_date end),a2.company_id)) else 0 end,2) end AS haber,
	case when a5.name = 'USD' then (a2.amount_currency) else round(convert_currency(a2.currency_id,1,a2.amount_currency,(case when a1.move_type = 'entry' then a1.date else a1.invoice_date end),a2.company_id),2) end AS balance,
	CASE
		WHEN a2.currency_id IS NULL THEN 'PEN'::character varying
		ELSE a5.name
	END AS moneda,
	coalesce(case when a2.tc = 0 then 1 else a2.tc end,1) as tc,
	a1.glosa,
	a7.l10n_pe_vat_code AS td_partner,
	a6.vat AS doc_partner,
	a6.name AS partner,
	a8.code AS td_sunat,
	REPLACE(a2.nro_comp,'/','-')::character varying AS nro_comprobante,
	a1.invoice_date AS fecha_doc,
	a2.date_maturity AS fecha_ven,
	(a10.name->>'es_PE'::character varying)::character varying AS col_reg,
	a2.tax_amount_it::numeric AS monto_reg,
	a12.code AS medio_pago,
	a1.ple_state AS ple_diario,
	a1.campo_41_purchase AS ple_compras,
	a1.campo_34_sale AS ple_ventas,
	a1.id AS move_id,
	a2.id AS move_line_id,
	a2.account_id,
	a2.partner_id
	FROM account_move a1
		LEFT JOIN account_move_line a2 ON a2.move_id = a1.id
		LEFT JOIN account_journal a3 ON a3.id = a1.journal_id
		LEFT JOIN account_account a4 ON a4.id = a2.account_id
		LEFT JOIN res_currency a5 ON a5.id = a2.currency_id
		LEFT JOIN res_partner a6 ON a6.id = a2.partner_id
		LEFT JOIN l10n_latam_identification_type a7 ON a7.id = a6.l10n_latam_identification_type_id
		LEFT JOIN l10n_latam_document_type a8 ON a8.id = a2.type_document_id
		LEFT JOIN account_account_tag_account_move_line_rel a9 ON a9.account_move_line_id = a2.id
		LEFT JOIN account_account_tag a10 ON a10.id = a9.account_account_tag_id
		LEFT JOIN einvoice_catalog_payment a12 ON a12.id = a1.td_payment_id
	WHERE a1.state::text = 'posted'::text 
	AND a2.account_id IS NOT NULL AND (a1.date::date BETWEEN $1 and $2) AND a1.company_id = $3
	ORDER BY (date_part('month'::text, a1.date)), a3.code, a1.vou_number, a2.debit DESC, a4.code;
	END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
--------------------------------------------------------------------------------------------------------------------------