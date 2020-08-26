SELECT EQ_EQUIP_NO as equip_id,
DESCRIPTION as description,
ASSET_TYPE as asset_type,
PROCST_PROC_STATUS as proc_status,
PRI_SHOP_PRIORITY as priority_code,
DEPT_DEPT_CODE as dept_code,
YEAR as year,
MANUFACTURER as manufacturer,
MODEL as model,
METER_1_TYPE as meter_1_type,
METER_2_TYPE as meter_2_type,
DATE_ADDED as date_added,
IN_SERVICE_DATE date_in_service,
RETIRE_DATE as date_retired,
SALE_DATE as date_purchased
FROM EMSDBA.EQ_MAIN