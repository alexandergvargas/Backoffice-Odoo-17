DROP FUNCTION IF EXISTS get_saldos_cc(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION get_saldos_cc(date_from DATE, date_to DATE, company_id INTEGER) 
RETURNS TABLE (
    id INT,
    date DATE,
    partner_id INT,
    account_id INT,
    type_document_id INT,
    nro_comp VARCHAR,
    debit NUMERIC,
    credit NUMERIC,
    balancemn NUMERIC,
    balanceme NUMERIC,
    type VARCHAR
) 
AS $$
BEGIN
    RETURN QUERY
    (
        SELECT a1.id, a2.date, a1.partner_id, a1.account_id, a1.type_document_id, a1.nro_comp,
            a1.debit::numeric, a1.credit::numeric, a1.balance::numeric AS balancemn,
            (CASE WHEN a3.currency_id is null or a3.currency_id = (SELECT rc.currency_id FROM res_company rc WHERE rc.id = $3) 
                THEN 0 ELSE a1.amount_currency END)::numeric AS balanceme,
            'move'::character varying as type
        FROM account_move_line a1
        LEFT JOIN account_move a2 ON a2.id = a1.move_id
        LEFT JOIN account_account a3 ON a3.id = a1.account_id
        WHERE (a2.date BETWEEN $1 AND $2) AND a2.state = 'posted'
            AND a3.is_document_an = TRUE 
            AND a1.company_id = $3
    )
    UNION ALL
    (
        SELECT b1.id, b2.date, b1.partner_id, b1.account_id, b1.type_document_id, b1.nro_comp,
            b1.debit::numeric, b1.credit::numeric, (b1.debit - b1.credit)::numeric AS balancemn, 
			(CASE WHEN b3.currency_id is null or b3.currency_id = (SELECT rc.currency_id FROM res_company rc WHERE rc.id = $3) THEN 0 ELSE  b1.amount_currency end)::numeric AS balanceme,
            'cta_cte'::character varying as type
        FROM account_cta_cte_si b1
        LEFT JOIN account_cta_cte b2 ON b2.id = b1.main_id	
        LEFT JOIN account_account b3 ON b3.id = b1.account_id
        WHERE (b2.date BETWEEN $1 AND $2) AND b2.state = 'posted'
            AND b3.is_document_an = TRUE 
            AND b2.company_id = $3
    )
    ORDER BY partner_id, account_id, date, type_document_id, nro_comp, id;
END;
$$ LANGUAGE plpgsql;

------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS get_origenes_cc(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION get_origenes_cc(date_from DATE, date_to DATE, company_id INT)
RETURNS TABLE (
    account_type VARCHAR,
    partner_id INT,
    account_id INT,
    type_document_id INT,
    nro_comp VARCHAR,
    periodo TEXT,
    date DATE,
    invoice_date_it DATE,
    date_maturity DATE,
    glosa VARCHAR,
    name VARCHAR,
    invoice_user_id INT,
    journal_id INT,
    linea INT,
    cabecera INT,
    type VARCHAR
)
AS $$
BEGIN
    RETURN QUERY (
        SELECT aa.account_type,
	        T.partner_id,
            T.account_id,
            T.type_document_id,
            T.nro_comp,
            periodo_de_fecha(am.date,am.is_opening_close)::text as periodo,
            am.date,
            aml.invoice_date_it,
            aml.date_maturity,
            am.glosa,
            aml.name,
            am.invoice_user_id,
            am.journal_id,
            T.linea,
            aml.move_id as cabecera,
            T.type
	    FROM(SELECT 
            a1.partner_id,
            a1.account_id,
            a1.type_document_id,
            a1.nro_comp,
            min(a1.id) as linea,
            'move'::character varying as type
        FROM 
            account_move_line a1
        LEFT JOIN account_move a2 ON a2.id = a1.move_id
        WHERE a1.cta_cte_origen = true 
            AND (a2.date BETWEEN $1 AND $2)
            AND a2.state = 'posted' 
            AND a2.company_id = $3
            GROUP BY a1.partner_id, a1.account_id, a1.type_document_id, a1.nro_comp)T
        LEFT JOIN account_account aa ON aa.id = T.account_id
        LEFT JOIN account_move_line aml ON aml.id = T.linea
        LEFT JOIN account_move am on am.id = aml.move_id
    )
    UNION ALL
    (
        SELECT 
            b3.account_type,
            b1.partner_id,
            b1.account_id,
            b1.type_document_id,
            b1.nro_comp,
			periodo_de_fecha(b2.date,(b2.type_register = 'origin')::boolean)::text as periodo,
            b2.date,
            b1.invoice_date as invoice_date_it,
            b1.date_maturity,
            b1.glosa,
            NULL as name,
            b1.invoice_user_id,
            b1.journal_id,
            b1.id as linea,
            b2.id as cabecera,
            'cta_cte'::character varying as type
        FROM 
            account_cta_cte_si b1
        LEFT JOIN 
            account_cta_cte b2 ON b2.id = b1.main_id
        LEFT JOIN 
            account_account b3 ON b3.id = b1.account_id
        WHERE 
            b2.type_register = 'origin' 
            AND (b2.date BETWEEN $1 AND $2) 
            AND b2.state = 'posted' 
            AND b2.company_id = $3
    )
    ORDER BY 
        partner_id, account_id, date, type_document_id, nro_comp, linea;
END;
$$ LANGUAGE plpgsql;

------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS get_saldos(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION get_saldos(date_from DATE, date_to DATE, id_company INTEGER) 
RETURNS TABLE (
    id bigint, 
    periodo text, 
    fecha_con date, 
    libro character varying, 
    voucher character varying, 
    td_partner character varying, 
	doc_partner character varying,
    partner character varying, 
    td_sunat character varying, 
    nro_comprobante character varying, 
    fecha_doc date, 
	fecha_ven date, 
    cuenta character varying, 
    moneda character varying, 
    monto_ini_mn numeric, 
    monto_ini_me numeric, 
    debe numeric, 
    haber numeric, 
    saldo_mn numeric, 
    saldo_me numeric,
    journal_id integer, 
    account_id integer, 
    partner_id integer, 
    move_id integer, 
    move_line_id integer, 
    type character varying
) 
AS $$
BEGIN
    RETURN QUERY
	SELECT row_number() OVER () AS id,t.* from 
    (SELECT origin.periodo,
	origin.date as fecha_con,
	aj.code as libro,
	(case when origin.type = 'move' then am.vou_number else cta_cte.name end) as voucher,
    lit.l10n_pe_vat_code as td_partner,
    rp.vat as doc_partner,
    rp.name as partner,
    ec1.code as td_sunat,
    s.nro_comp as nro_comprobante,
    origin.invoice_date_it as fecha_doc,
    origin.date_maturity as fecha_ven,
    aa.code as cuenta,
    rc.name as moneda,
    0::numeric as monto_ini_mn,
    0::numeric as monto_ini_me,
    s.debe,
    s.haber,
    s.saldo_mn,
    s.saldo_me,
    origin.journal_id,
    s.account_id,
    s.partner_id,
    origin.cabecera as move_id,
    origin.linea as move_line_id,
    origin.type 
	FROM  
    (SELECT c1.partner_id, c1.account_id, c1.type_document_id, c1.nro_comp,
           SUM(c1.debit) AS debe, SUM(c1.credit) AS haber, 
           SUM(c1.balancemn) AS saldo_mn, SUM(c1.balanceme) AS saldo_me
    FROM get_saldos_cc($1, $2, $3) c1
    GROUP BY c1.partner_id, c1.account_id, c1.type_document_id, c1.nro_comp)s
	LEFT JOIN get_origenes_cc($1, $2, $3) origin ON origin.partner_id = s.partner_id and origin.type_document_id = s.type_document_id and origin.nro_comp = s.nro_comp and origin.account_id = s.account_id
	LEFT JOIN account_move am on am.id = origin.cabecera
	LEFT JOIN account_cta_cte cta_cte on cta_cte.id = origin.cabecera
    LEFT JOIN res_partner rp on rp.id = s.partner_id
    LEFT JOIN l10n_latam_identification_type lit on lit.id=rp.l10n_latam_identification_type_id
    LEFT JOIN l10n_latam_document_type ec1 on ec1.id=s.type_document_id
    LEFT JOIN account_account aa on aa.id=s.account_id
    left join res_currency rc on rc.id=coalesce(aa.currency_id,(SELECT rc.currency_id FROM res_company rc WHERE rc.id = $3))
    LEFT JOIN account_journal aj on aj.id = origin.journal_id)t;
END;
$$ LANGUAGE plpgsql;

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldo_detalle(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldo_detalle(
	date_from date,
	date_to date,
	company_id integer)
	RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying,td_partner character varying, 
    doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, 
    fecha_ven date, cuenta character varying, moneda character varying, debe numeric, haber numeric,balance numeric,importe_me numeric, 
    saldo numeric, saldo_me numeric, partner_id integer, account_id integer, register_id integer, type character varying) AS
	$BODY$
	BEGIN
	RETURN QUERY 
    SELECT periodo_de_fecha(s.date,case when s.type = 'move' then am.is_opening_close else (cta_cte.type_register = 'origin')::boolean end)::character varying as periodo,
	s.date as fecha,
	aj.code as libro,
	(case when s.type = 'move' then am.vou_number else cta_cte.name end) as voucher,
    lit.l10n_pe_vat_code as td_partner,
    rp.vat as doc_partner,
    rp.name as partner,
    ec1.code as td_sunat,
    s.nro_comp as nro_comprobante,
    origin.invoice_date_it as fecha_doc,
    origin.date_maturity as fecha_ven,
    aa.code as cuenta,
    rc.name as moneda,
    s.debe,
    s.haber,
    s.balance,
    s.importe_me,
    sum(s.balance) OVER (partition by s.partner_id, s.account_id,ec1.code, s.nro_comp order by s.partner_id, s.account_id,ec1.code, s.nro_comp, s.date, s.id ) as saldo,
    sum(s.importe_me) OVER (partition by s.partner_id, s.account_id,ec1.code, s.nro_comp order by s.partner_id, s.account_id,ec1.code, s.nro_comp, s.date, s.id ) as saldo_me,
    s.partner_id,
    s.account_id,
    s.id as register_id,
    origin.type 
	FROM  
    (SELECT c1.id, c1.type, c1.partner_id, c1.account_id, c1.type_document_id, c1.nro_comp,
           c1.debit AS debe, c1.credit AS haber, 
           c1.balancemn AS balance, c1.balanceme AS importe_me,
           c1.date
    FROM get_saldos_cc($1, $2, $3) c1)s
	LEFT JOIN get_origenes_cc($1, $2, $3) origin ON (origin.partner_id = s.partner_id and origin.type_document_id = s.type_document_id and origin.nro_comp = s.nro_comp and origin.account_id = s.account_id)
	LEFT JOIN account_move_line aml on aml.id = s.id
	LEFT JOIN account_cta_cte_si ccl on ccl.id = s.id
    LEFT JOIN account_move am on am.id = aml.move_id
	LEFT JOIN account_cta_cte cta_cte on cta_cte.id = ccl.main_id
    LEFT JOIN res_partner rp on rp.id = s.partner_id
    LEFT JOIN l10n_latam_identification_type lit on lit.id=rp.l10n_latam_identification_type_id
    LEFT JOIN l10n_latam_document_type ec1 on ec1.id=s.type_document_id
    LEFT JOIN account_account aa on aa.id=s.account_id
    left join res_currency rc on rc.id=coalesce(aa.currency_id,(SELECT rc.currency_id FROM res_company rc WHERE rc.id = $3))
    LEFT JOIN account_journal aj on aj.id = (case when s.type = 'move' then am.journal_id else ccl.journal_id end)
    order by s.partner_id, s.account_id,ec1.code, s.nro_comp, s.date, s.id;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_global(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_global(
    periodo_apertura character varying,
    periodo character varying,
    company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
    RETURN QUERY   
    SELECT a1.account_id,
        sum(a1.debe) AS debe,
        sum(a1.haber) AS haber,
        sum(coalesce(a1.balance,0)) AS saldomn,
        sum(coalesce(a1.importe_me,0)) AS saldome
        FROM get_diariog((select date_start from account_period where code = $1::character varying limit 1),(select date_end from account_period where code = $2::character varying  limit 1),$3) a1
        LEFT JOIN account_account a2 ON a2.id = a1.account_id
        --LEFT JOIN res_currency a4 on a4.id = a2.currency_id
        WHERE a2.currency_id is not null AND
        a2.dif_cambio_type = 'global' AND (a1.periodo::integer between $1::integer and $2::integer)
        GROUP BY a1.account_id;
END;
$BODY$;
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_global_2(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_global_2(
	periodo_apertura character varying,
	periodo character varying,
	company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
 SELECT
    b1.account_id,
    b1.debe,
    b1.haber,
    b1.saldomn,
    b1.saldome,
    b3.group_balance,
        CASE
            WHEN b3.group_balance::text = ANY (ARRAY['B1'::character varying, 'B2'::character varying]::text[]) THEN ( SELECT edcl.compra
               FROM exchange_diff_config_line edcl
                 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
                 LEFT JOIN account_period ap ON ap.id = edcl.period_id
              WHERE edc.company_id = $3 AND ap.code::text = $2::text and edcl.currency_id = b2.currency_id)
            ELSE ( SELECT edcl.venta
               FROM exchange_diff_config_line edcl
                 LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
                 LEFT JOIN account_period ap ON ap.id = edcl.period_id
              WHERE edc.company_id = $3 AND ap.code::text = $2::text and edcl.currency_id = b2.currency_id)
        END AS tc
   FROM get_saldos_me_global($1,$2,$3) b1
     LEFT JOIN account_account b2 ON b2.id = b1.account_id
     LEFT JOIN account_type_it b3 ON b3.id = b2.account_type_it_id;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_global_final(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_global_final(
	fiscal_year character varying,
	periodo character varying,
	company_id integer)
    RETURNS TABLE(account_id integer, debe numeric, haber numeric, saldomn numeric, saldome numeric, group_balance character varying, tc numeric, saldo_act numeric, diferencia numeric, difference_account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	SELECT *,
	round(coalesce(vst.tc,0) * vst.saldome,2) AS saldo_act,
	vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) AS diferencia,
	CASE 
	WHEN vst.saldomn < round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN vst.saldomn > round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) > (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) < (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3) END AS difference_account_id
	FROM get_saldos_me_global_2($1||'00',$2,$3) vst;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_documento(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento(
	periodo_apertura character varying,
	periodo character varying,
	company_id integer)
    RETURNS TABLE(partner_id integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric, type_document_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY   
	select a1.partner_id,
	a1.account_id,
	a1.td_sunat,
	a1.nro_comprobante,
	sum(a1.debe) debe,
	sum(a1.haber) haber,
	sum(coalesce(a1.balance,0))as saldomn,
	sum(coalesce(a1.importe_me,0)) as saldome,
	aml.type_document_id
	from get_diariog((select date_start from account_period where code = $1::character varying limit 1),(select date_end from account_period where code = $2::character varying  limit 1),$3) a1
	left join account_account a2 on a2.id=a1.account_id
	left join account_type_it a3 on a3.id=a2.account_type_it_id
	--left join res_currency a4 on a4.id = a2.currency_id
	left join account_move_line aml on aml.id = a1.move_line_id
	where 
	a2.dif_cambio_type = 'doc' and
	a2.currency_id is not null and
	(a1.periodo::int between $1::int and $2::int)
	group by a1.partner_id,a1.account_id,a1.td_sunat,a1.nro_comprobante, aml.type_document_id
	having (sum(a1.balance)+sum(a1.importe_me)) <> 0;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_documento_2(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento_2(
	periodo_apertura character varying,
	periodo character varying,
	company_id integer)
    RETURNS TABLE(partner_id integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric, type_document_id integer, group_balance character varying, tc numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
select b1.partner_id,
b1.account_id,
b1.td_sunat,
b1.nro_comprobante,
b1.debe,
b1.haber,
b1.saldomn,
b1.saldome,
b1.type_document_id,
b3.group_balance,
CASE
	WHEN b3.group_balance::text = ANY (ARRAY['B1'::character varying, 'B2'::character varying]::text[]) THEN ( SELECT edcl.compra
		FROM exchange_diff_config_line edcl
			LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
			LEFT JOIN account_period ap ON ap.id = edcl.period_id
		WHERE edc.company_id = $3 AND ap.code::text = $2::text and edcl.currency_id = b2.currency_id)
	ELSE ( SELECT edcl.venta
		FROM exchange_diff_config_line edcl
			LEFT JOIN exchange_diff_config edc ON edc.id = edcl.line_id
			LEFT JOIN account_period ap ON ap.id = edcl.period_id
		WHERE edc.company_id = $3 AND ap.code::text = $2::text and edcl.currency_id = b2.currency_id)
END AS tc
from get_saldos_me_documento($1,$2,$3) b1
LEFT JOIN account_account b2 ON b2.id = b1.account_id
LEFT JOIN account_type_it b3 ON b3.id = b2.account_type_it_id;
END;
$BODY$;

----------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_saldos_me_documento_final(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos_me_documento_final(
	fiscal_year character varying,
	periodo character varying,
	company_id integer)
    RETURNS TABLE(partner_id integer, account_id integer, td_sunat character varying, nro_comprobante character varying, debe numeric, haber numeric, saldomn numeric, saldome numeric, type_document_id integer, group_balance character varying, tc numeric, saldo_act numeric, diferencia numeric, difference_account_id integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	SELECT *,
	round(coalesce(vst.tc,0) * vst.saldome,2) AS saldo_act,
	vst.saldomn - round(coalesce(vst.tc,0) * vst.saldome,2) AS diferencia,
	CASE 
	WHEN vst.saldomn < round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN vst.saldomn > round(vst.tc * vst.saldome,2) AND vst.group_balance IN ('B1','B2') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) > (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.profit_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3)
	WHEN (-1 * vst.saldomn) < (-1 * round(vst.tc * vst.saldome,2)) AND vst.group_balance IN ('B3','B4','B5') THEN (SELECT edc.loss_account_id FROM exchange_diff_config edc WHERE edc.company_id = $3) END AS difference_account_id
	FROM get_saldos_me_documento_2($1||'00',$2,$3) vst;
END;
$BODY$;
-------------------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_maturity_analysis(date, date, integer, character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.get_maturity_analysis(
	first_date date,
	end_date date,
	company_id integer,
	type character varying)
    RETURNS TABLE(fecha_emi date, fecha_ven date, cuenta character varying, divisa character varying, tdp character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, saldo_mn numeric, saldo_me numeric, partner_id integer, cero_treinta numeric, treinta1_sesenta numeric, sesenta1_noventa numeric, noventa1_ciento20 numeric, ciento21_ciento50 numeric, ciento51_ciento80 numeric, ciento81_mas numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN
	RETURN QUERY  
	select 
	b1.fecha_emi,
	b1.fecha_ven,
	b1.cuenta,
	b1.divisa,
	b1.tdp,
	b1.doc_partner,
	b1.partner,
	b1.td_sunat,
	b1.nro_comprobante,
	b1.saldo_mn,
	b1.saldo_me,
	b1.partner_id,
	case when b1.atraso between 0 and 30 then b1.saldo_mn else 0 end as cero_treinta,
	case when b1.atraso between 31 and 60 then b1.saldo_mn else 0 end as treinta1_sesenta,
	case when b1.atraso between 61 and 90 then b1.saldo_mn else 0 end as sesenta1_noventa,
	case when b1.atraso between 91 and 120 then b1.saldo_mn else 0 end as noventa1_ciento20,
	case when b1.atraso between 121 and 150 then b1.saldo_mn else 0 end as ciento21_ciento50,
	case when b1.atraso between 151 and 180 then b1.saldo_mn else 0 end as ciento51_ciento80,
	case when b1.atraso >180 then b1.saldo_mn else 0 end as ciento81_mas 
	from
	(
	select 
	case when a1.fecha_doc::date is null then a1.fecha_con::date else a1.fecha_doc::date end as fecha_emi,
	a1.fecha_ven as fecha_ven,
	a1.cuenta as cuenta,
	case when a3.name is not null then a3.name else 'PEN' end as divisa,
	a1.td_partner as tdp,
	a1.doc_partner as doc_partner,
	a1.partner,
	a1.td_sunat,
	a1.nro_comprobante,
	case when  a2.account_type='asset_receivable' then a1.saldo_mn else -a1.saldo_mn end as saldo_mn,
	case when  a2.account_type='asset_receivable' then a1.saldo_me else -a1.saldo_me end as saldo_me,
	case when a1.fecha_ven is not null then $2 - a1.fecha_ven else 0 end as atraso,
	a1.account_id,
	a2.account_type,
	a1.partner_id
	from 
	get_saldos($1,$2,$3) a1
	left join account_account a2 on a2.id=a1.account_id
	left join res_currency a3 on a3.id=a2.currency_id
	where a1.nro_comprobante is not null and a1.saldo_mn <> 0
	)b1
	where b1.account_type = $4;
END;
$BODY$;