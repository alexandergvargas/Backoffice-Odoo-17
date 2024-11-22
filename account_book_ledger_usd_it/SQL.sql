DROP FUNCTION IF EXISTS public.get_mayorg_usd(date, date, integer,integer[]) CASCADE;

CREATE OR REPLACE FUNCTION public.get_mayorg_usd(
	date_from date,
	date_to date,
	company_id integer,
  account_ids integer[])
	RETURNS TABLE(periodo integer, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, 
	haber numeric, balance numeric, saldo numeric, moneda character varying, 
	tc numeric, cta_analitica character varying, glosa character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, 
	nro_comprobante character varying, fecha_doc date, fecha_ven date, account_id integer, move_id integer, move_line_id integer) AS
	$BODY$
	BEGIN
	RETURN QUERY 
select 
CASE
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '0101'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '00')::integer
	WHEN am.is_opening_close = true AND to_char(am.date::timestamp with time zone, 'mmdd'::text) = '1231'::text THEN (to_char(am.date::timestamp with time zone, 'yyyy'::text) || '13')::integer
	ELSE to_char(am.date::timestamp with time zone, 'yyyymm'::text)::integer
END AS periodo,
T.fecha,
aj.code as libro,
am.vou_number AS voucher,
aa.code as cuenta,
T.debit as debe,
T.credit as haber,
T.balance,
sum(coalesce(T.balance,0)) OVER (partition by T.account_id order by T.account_id,T.fecha,T.move_line_id) as saldo,
rc.name as moneda,
aml.tc,
null::character varying AS cta_analitica,
--ana.name as cta_analitica,
am.glosa,
llit.l10n_pe_vat_code as td_partner,
rp.vat as doc_partner,
rp.name as partner,
lldt.code as td_sunat,
aml.nro_comp as nro_comprobante,
am.invoice_date AS fecha_doc,
aml.date_maturity AS fecha_ven,
T.account_id,
T.move_id,
T.move_line_id from (
select
null as move_id,
0 as move_line_id,
date_from as fecha, 
aml.account_id,
sum(case when rc.name = 'USD' then (case when aml.amount_currency> 0 then aml.amount_currency else 0 end) else round(case when convert_currency(aml.currency_id,1,aml.amount_currency,(case when am.move_type = 'entry' then am.date else am.invoice_date end),aml.company_id)>0 then convert_currency(aml.currency_id,1,aml.amount_currency,(case when am.move_type = 'entry' then am.date else am.invoice_date end),aml.company_id) else 0 end,2) end) AS debit,
sum(case when rc.name = 'USD' then (case when aml.amount_currency< 0 then abs(aml.amount_currency) else 0 end) else round(case when convert_currency(aml.currency_id,1,aml.amount_currency,(case when am.move_type = 'entry' then am.date else am.invoice_date end),aml.company_id)<0 then abs(convert_currency(aml.currency_id,1,aml.amount_currency,(case when am.move_type = 'entry' then am.date else am.invoice_date end),aml.company_id)) else 0 end,2) end) AS credit,
sum(case when rc.name = 'USD' then (aml.amount_currency) else round(convert_currency(aml.currency_id,1,aml.amount_currency,(case when am.move_type = 'entry' then am.date else am.invoice_date end),aml.company_id),2) end) AS balance
from account_move_line aml
left join account_move am on am.id=aml.move_id
left join res_currency rc on rc.id = aml.currency_id
where (am.date between (EXTRACT (YEAR FROM date_from)::character varying ||'/01/01')::date and date_from - 1)   
and  am.state='posted'
--and aml.display_type is null
and aml.account_id = ANY($4)
and am.company_id=$3
group by aml.account_id 
union all
select 
am.id as move_id,
aml.id as move_line_id,
am.date as fecha,
aml.account_id,
case when rc.name = 'USD' then (case when aml.amount_currency> 0 then aml.amount_currency else 0 end) else round(case when convert_currency(aml.currency_id,1,aml.amount_currency,(case when am.move_type = 'entry' then am.date else am.invoice_date end),aml.company_id)>0 then convert_currency(aml.currency_id,1,aml.amount_currency,(case when am.move_type = 'entry' then am.date else am.invoice_date end),aml.company_id) else 0 end,2) end AS debit,
case when rc.name = 'USD' then (case when aml.amount_currency< 0 then abs(aml.amount_currency) else 0 end) else round(case when convert_currency(aml.currency_id,1,aml.amount_currency,(case when am.move_type = 'entry' then am.date else am.invoice_date end),aml.company_id)<0 then abs(convert_currency(aml.currency_id,1,aml.amount_currency,(case when am.move_type = 'entry' then am.date else am.invoice_date end),aml.company_id)) else 0 end,2) end AS credit,
case when rc.name = 'USD' then (aml.amount_currency) else round(convert_currency(aml.currency_id,1,aml.amount_currency,(case when am.move_type = 'entry' then am.date else am.invoice_date end),aml.company_id),2) end AS balance
from account_move_line aml
left join account_move am on am.id=aml.move_id
left join res_currency rc on rc.id = aml.currency_id
where (am.date between date_from and date_to)
and  am.state='posted'
--and aml.display_type is null
and aml.account_id = ANY($4)
and am.company_id=$3
)T
LEFT JOIN account_move_line aml ON T.move_line_id = aml.id
LEFT JOIN account_move am ON T.move_id = am.id
LEFT JOIN account_journal aj ON aj.id = am.journal_id
LEFT JOIN account_account aa ON aa.id = T.account_id
LEFT JOIN res_currency rc ON rc.id = aml.currency_id
--CUENTA ANALITICA EN PRUEBA
--LEFT JOIN account_analytic_account ana ON ana.id = aml.analytic_account_id
LEFT JOIN res_partner rp ON rp.id = aml.partner_id
LEFT JOIN l10n_latam_identification_type llit ON llit.id = rp.l10n_latam_identification_type_id
LEFT JOIN l10n_latam_document_type lldt ON lldt.id = aml.type_document_id
order by T.account_id,T.fecha,T.move_line_id;
END;
	$BODY$
	LANGUAGE plpgsql VOLATILE
	COST 100
	ROWS 1000;
------------------------------------------------------------------------------------------------------------------------------------------------------------------