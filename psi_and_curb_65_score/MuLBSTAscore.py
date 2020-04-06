class MuLBSTAscore:
    mortalityRates = [0.47, 0.87, 1.18, 1.60, 2.17, 2.92, 3.93, 5.27, 7.03, 9.33, 12.27, 15.99, 20.56, 26.03, 32.36, 39.42, 46.95, 54.61, 62.07, 68.99]
    def __init__(self, patient_data):
        self.data = patient_data
        print('mulb',list(self.data))

    def compute(self):
        self.data[['Multilobe infiltrate']] *= 5
        self.data[['Absolute lymphocyte count <=0.8 x 10^9/L', 'Bacterial infection']] *= 4
        self.data[['Acute smoker']] *= 3
        self.data[['Quit smoking', 'Hypertension', 'Age >=60']] *= 2

        self.data['MuLBSTA Score'] = self.data.sum(axis=1)
        self.data['90-day mortality'] = self.data.apply(self.riskAssess, axis = 1)

        return self.data['MuLBSTA Score'], self.data['90-day mortality']

    def riskAssess(self, row):
        print(row['MuLBSTA Score'])
        if row['MuLBSTA Score'] >= 20:
            return '>68.99'

        return str(self.mortalityRates[row['MuLBSTA Score']])
