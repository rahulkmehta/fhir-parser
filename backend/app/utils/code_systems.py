# LOINC codes for key observations
LOINC_BMI = "39156-5"
LOINC_BODY_WEIGHT = "29463-7"
LOINC_BODY_HEIGHT = "8302-2"
LOINC_BP_PANEL = "85354-9"
LOINC_BP_SYSTOLIC = "8480-6"
LOINC_BP_DIASTOLIC = "8462-4"

# SNOMED codes for bariatric eligibility comorbidities
# Per NIH/CMS bariatric surgery guidelines, these are obesity-related
# comorbidities that qualify a patient with BMI 35-39.9.
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

SNOMED_ADDITIONAL_COMORBIDITY_CODES = {
    "237602007",   # Metabolic syndrome X
    "55822004",    # Hyperlipidemia
    "370992007",   # Dyslipidemia
    "239873007",   # Osteoarthritis of knee
    "396275006",   # Osteoarthritis (general)
    "78275009",    # Obstructive sleep apnea
    "73430006",    # Sleep apnea
    "39898005",    # Sleep disorder
    "235595009",   # Gastroesophageal reflux disease (GERD)
    "197315008",   # Non-alcoholic fatty liver disease (NAFLD)
    "442685003",   # Nonalcoholic steatohepatitis (NASH)
    "414545008",   # Ischemic heart disease
    "53741008",    # Coronary arteriosclerosis
    "68267002",    # Benign intracranial hypertension (pseudotumor cerebri)
    "237055002",   # Polycystic ovary syndrome (PCOS)
    "190966007",   # Obesity hypoventilation syndrome
}

# All comorbidity codes combined for eligibility checks
SNOMED_ALL_COMORBIDITY_CODES = (
    SNOMED_HYPERTENSION_CODES
    | SNOMED_TYPE2_DIABETES_CODES
    | SNOMED_ADDITIONAL_COMORBIDITY_CODES
)

# SNOMED codes for evidence of prior weight-loss attempts
# Includes dietary counseling, exercise/physical therapy, weight management,
# and behavioral interventions per OpenCodelists weight management reference set.
SNOMED_WEIGHT_LOSS_CODES = {
    # Behavioral / counseling
    "228557008",  # Cognitive and behavioral therapy
    "408919008",  # Psychosocial care
    "409066002",  # Education, guidance and counseling
    # Exercise / physical activity
    "229095001",  # Exercise class
    "229064008",  # Movement therapy
    "229065009",  # Exercise therapy
    "91251008",   # Physical therapy procedure
    "52052004",   # Rehabilitation therapy
    "304507003",  # Exercise education
    # Dietary counseling
    "11816003",   # Diet education
    "103699006",  # Referral to dietitian
    "424753004",  # Dietary management education, guidance, and counseling
    "266724001",  # Weight-reducing diet education
    "284352003",  # Obesity diet education
    "443288003",  # Lifestyle education regarding diet
    # Weight management programs
    "408289007",  # Refer to weight management program
    "388976009",  # Weight reduction regimen
    "718361005",  # Weight management program
    "386516004",  # Anticipatory guidance
}

# SNOMED codes for psychological evaluation evidence
# Includes psychiatric interviews, mental health assessments,
# depression/anxiety screenings, and behavioral evaluations.
SNOMED_PSYCH_EVAL_CODES = {
    "385892002",       # Mental health screening
    "408919008",       # Psychosocial care
    "228557008",       # Cognitive and behavioral therapy
    "10197000",        # Psychiatric interview and evaluation
    "79094001",        # Initial psychiatric interview with mental status
    "410223002",       # Mental health care assessment
    "391281002",       # Mental health assessment
    "171207006",       # Depression screening
    "454711000124102", # Depression screening using PHQ-2
    "715252007",       # Depression screening using PHQ-9
    "710841007",       # Assessment of anxiety
}
