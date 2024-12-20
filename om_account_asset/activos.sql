DROP FUNCTION IF EXISTS public.get_activos(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_activos(
    IN date_ini date,
    IN date_fin date,
    IN id_company integer)
  RETURNS TABLE(id bigint, code character varying, name character varying, mes integer, period character varying, cat_name character varying, cta_analitica jsonb , cta_activo character varying, cta_gasto character varying, cta_depreciacion character varying, valor_dep numeric, analytic_distribution jsonb , account_depreciation_expense_id integer, account_depreciation_id integer, line_depreciation_id integer) AS
$BODY$
BEGIN
	RETURN QUERY 
	select row_number() OVER () AS id,
	ass.code,
	ass.name,
	line.sequence as mes,
	to_char(line.depreciation_date::timestamp with time zone, 'mm/yyyy'::text)::character varying as period,
	cat.name as cat_name,
	ass.analytic_distribution as cta_analitica,
	ac_as.code as cta_activo,
	ac_ga.code as cta_gasto,
	ac_de.code as cta_depreciacion,
	line.amount as valor_dep,
	ass.analytic_distribution,
	cat.account_depreciation_expense_id,
	cat.account_depreciation_id,
	line.id as line_depreciation_id
	from account_asset_depreciation_line line
	left join account_asset_asset ass on ass.id = line.asset_id
	left join account_asset_category cat on ass.category_id = cat.id
	left join account_account ac_as on cat.account_asset_id = ac_as.id
	left join account_account ac_ga on cat.account_depreciation_expense_id = ac_ga.id
	left join account_account ac_de on cat.account_depreciation_id = ac_de.id
	where (line.depreciation_date::date between $1::date and $2::date) and ass.company_id = $3 and ass.state <> 'draft';
	--and (ass.f_baja is null or ass.f_baja > $1::date); POR ENCARGO DEL SR edward
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
-----------------------------------------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_activos_usd(date, date, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_activos_usd(
    IN date_ini date,
    IN date_fin date,
    IN id_company integer)
  RETURNS TABLE(id bigint, code character varying, name character varying, mes integer, period character varying, cat_name character varying, cta_analitica jsonb , cta_activo character varying, cta_gasto character varying, cta_depreciacion character varying, valor_dep numeric, analytic_distribution jsonb , account_depreciation_expense_id integer, account_depreciation_id integer, line_depreciation_id integer) AS
$BODY$
BEGIN
	RETURN QUERY 
	select row_number() OVER () AS id,
	ass.code,
	ass.name,
	line.sequence as mes,
	to_char(line.depreciation_date::timestamp with time zone, 'mm/yyyy'::text)::character varying as period,
	cat.name as cat_name,
	ass.analytic_distribution as cta_analitica,
	ac_as.code as cta_activo,
	ac_ga.code as cta_gasto,
	ac_de.code as cta_depreciacion,
	line.amount_me :: numeric as valor_dep,
	ass.analytic_distribution,
	cat.account_depreciation_expense_id,
	cat.account_depreciation_id,
	line.id as line_depreciation_id
	from account_asset_depreciation_line line
	left join account_asset_asset ass on ass.id = line.asset_id
	left join account_asset_category cat on ass.category_id = cat.id
	left join account_account ac_as on cat.account_asset_id = ac_as.id
	left join account_account ac_ga on cat.account_depreciation_expense_id = ac_ga.id
	left join account_account ac_de on cat.account_depreciation_id = ac_de.id
	where (line.depreciation_date::date between $1::date and $2::date) and ass.company_id = $3 and ass.state <> 'draft';
	--and (ass.f_baja is null or ass.f_baja > $1::date); POR ENCARGO DEL SR edward
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;