class PSIscore:
    def __init__(self, patient_data):
        self.data = patient_data
        print('hi', list(self.data))

    def compute_psi(self):
        self.data[['Nursing home resident', 'CHF history', 'Cerebrovascular disease history', 'Renal disease history',
                    'Pulse >=125 beats/min', 'Glucose >=250 mg/dL or >=14 mmol/L', 'Hematocrit <30%', 'Partial pressure of oxygen <60 mmHg or <8 kPa',
                    'Pleural effusion on x-ray']] *= 10

        self.data[['Liver disease history', 'Altered mental status', 'Respiratory rate >=30 breaths/min',
            'Systolic blood pressure <90 mmHg', 'BUN >=30 mg/dL or >=11 mmol/L', 'Sodium <130 mmol/L']] *= 20

        self.data[['pH <7.35', 'Neoplastic disease']] *= 30

        self.data['Temperature <35C (95F) or >39.9C (103.8F)'] *= 15

        self.data['Sex'] *= -10

        self.data['PSI Score'] = self.data.sum(axis=1)
        self.data['Risk/Disposition'] = self.data.apply(self.riskAssess, axis = 1)

        return self.data['PSI Score'], self.data['Risk/Disposition']

    def riskAssess(self, row):
        if row['PSI Score'] <= 70:
            val = 'Low/Outpatient care'
        elif row['PSI Score'] > 70 and row['PSI Score'] <= 90:
            val = 'Low/Outpatient vs. Observation admission'
        elif row['PSI Score'] > 90 and row['PSI Score'] <= 130:
            val = 'Moderate/Inpatient Admission'
        else:
            val = 'High/Inpatient Admission'

        return val
