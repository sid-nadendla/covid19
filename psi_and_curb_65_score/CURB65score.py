import numpy as numpy
import pandas as pd

class CURB65score:
    def __init__(self, patient_data):
        self.data = patient_data

    def compute_curb(self):
        self.data['CURB-65 Score'] = self.data.sum(axis=1)
        self.data['Risk/Disposition'] = self.data.apply(self.riskAssess, axis = 1)

        return self.data['CURB-65 Score'], self.data['Risk/Disposition']

    def riskAssess(self, row):
        if row['CURB-65 Score'] == 0 or row['CURB-65 Score'] == 1:
            val = '1.5% mortality/Outpatient care'
        elif row['CURB-65 Score'] == 2:
            val = '9.2% mortality/Inpatient vs. observation admission'
        else:
            val = '22% mortality/Inpatient with ICU admission'

        return val
