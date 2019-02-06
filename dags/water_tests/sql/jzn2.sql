-- Select 2nd part of analysis - ecoli linke with view 1
-- (SAMPLE_DATE, SOURCE, SAMPLE_ID, L_ANALYTE, L_VALUE, F_ANALYTE, F_VALUE, F_FIELD_RECORD)
SELECT DISTINCT
s.SAMPLE_DATE as SAMPLE_DATE, 
s.SOURCE as SOURCE, 
s.sample_id as SAMPLE_ID, 
r.analyte as L_ANALYTE, 
r.qualifier as L_VALUE, 
f.analyte as F_ANALYTE,
' '||f.qualifier||' '||f.value AS F_VALUE,
f.field_record as F_FIELD_RECORD
FROM
WPL.SAMPLE s, WPL.FIELD_DATA f, WPL.RESULT r, WPL.XR_SOURCE xrs
WHERE s.sample_id=r.sample_id
AND test_number=1
AND test_type='SAMP'
AND r.analyte in ('E_COLI')
AND r.reportable=1
AND f.analyte in ('CL2_RES_TOTAL')
AND s.Source in (SELECT DISTINCT SOURCE FROM WPL.XR_SOURCE WHERE SOURCE_NAME = 'SYS' AND VALID='Y')
AND SAMPLE_DATE BETWEEN '$ds' AND '$de'
AND s.sample_id=r.sample_id
AND s.field_record=f.field_record
AND xrs.source=s.source