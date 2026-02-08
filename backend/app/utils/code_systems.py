# LOINC codes for key observations
LOINC_BMI = "39156-5"
LOINC_BODY_WEIGHT = "29463-7"
LOINC_BODY_HEIGHT = "8302-2"
LOINC_BP_PANEL = "85354-9"
LOINC_BP_SYSTOLIC = "8480-6"
LOINC_BP_DIASTOLIC = "8462-4"

# SNOMED codes for bariatric eligibility comorbidities
SNOMED_HYPERTENSION_CODES = {
    "59621000",   # Essential hypertension
    "38341003",   # Hypertensive disorder
}

SNOMED_TYPE2_DIABETES_CODES = {
    "44054006",        # Diabetes mellitus type 2
    "127013003",       # Disorder of kidney due to diabetes mellitus
    "90781000119102",  # Microalbuminuria due to type 2 diabetes mellitus
    "157141000119108", # Proteinuria due to type 2 diabetes mellitus
    "422034002",       # Retinopathy due to type 2 diabetes mellitus
    "368581000119106", # Neuropathy due to type 2 diabetes mellitus
    "1551000119108",   # Nonproliferative diabetic retinopathy due to T2DM
    "97331000119101",  # Macular edema and retinopathy due to T2DM
    "1501000119109",   # Proliferative diabetic retinopathy due to T2DM
}

# SNOMED codes for evidence of prior weight-loss attempts
SNOMED_WEIGHT_LOSS_CODES = {
    "228557008",  # Cognitive and behavioral therapy
    "408919008",  # Psychosocial care
    "229095001",  # Exercise class
    "409066002",  # Education, guidance and counseling
}

# SNOMED codes for psychological evaluation evidence
SNOMED_PSYCH_EVAL_CODES = {
    "385892002",  # Mental health screening
    "408919008",  # Psychosocial care
    "228557008",  # Cognitive and behavioral therapy
}
