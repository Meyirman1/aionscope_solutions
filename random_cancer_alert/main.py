import random

def generate_cancer_alert():
  patient_ids = ["001","002","003","004","005"]
  cancer_symptoms = ["unexplained weight loss" , "fatigue that doesn't go away with rest", "night sweats or fever", "skin changes"]

  cancer_symptom = random.choice(cancer_symptoms)
  patient_id = random.choice(patient_ids)


  message = f"Our patient №{patient_id} has '{cancer_symptom}' which is the symptom of the Cancer"
  return message

print(generate_cancer_alert())
