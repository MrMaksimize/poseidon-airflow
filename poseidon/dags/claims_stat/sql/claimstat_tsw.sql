SELECT ORGANIZATION_DESC, CLAIM_NUMBER, ADRESS1, ZIP_CODE, CITY, CLAIMANT_TYPE_DESC, CLAIMANT_REFERENCE2_CODE, "CLAIMANT_REFERENCE2_Desc", INCIDENT_DESC, 
INCIDENT_DATE, ADJUSTING_LOC_RECEIVED_DATE, ADD_DATE, CLOSED_DATE, CLAIMANT_STATUS_DESC,
PAID_BI, PAID_PD, PAID_EXPENSE, PAID_TOTAL, 
INCURRED_BI, INCURRED_PD, INCURRED_EXPENSE, INCURRED_TOTAL
FROM CLAIMSTAT.CLAIMSTAT
WHERE ORGANIZATION_DESC = 'Storm Water-211612' OR ORGANIZATION_DESC = 'Street-211611'
AND INCIDENT_DATE >=  date '2008-07-01' 
ORDER BY INCIDENT_DATE DESC