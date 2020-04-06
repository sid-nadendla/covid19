from psi_and_curb_65_score.PSIscore import PSIscore
from psi_and_curb_65_score.CURB65score import CURB65score
from psi_and_curb_65_score.MuLBSTAscore import MuLBSTAscore

import pandas as pd
import sys
import os

class FinalResults:
    def __init__(self):
        pass

    def generateReport(self,patient_data):
        # patient_data = pd.read_csv(filename)
        
        data_copy = patient_data.copy()
        data_copy['Sex'] = data_copy['Sex'].apply({0:'Male', 1:'Female'}.get)

        #Computing PSI score and risk.
        psiObj = PSIscore(data_copy.loc[:, 'Age':'Temperature <35C (95F) or >39.9C (103.8F)'])
        psi_score, psi_risk = psiObj.compute_psi()

        #Computing CURB-65 score and risk.
        curbscore = CURB65score(pd.DataFrame(list(zip(data_copy['Confusion'], data_copy['BUN > 19 mg/dL (> 7 mmol/L)'], data_copy['Respiratory Rate >= 30'], data_copy['Systolic BP < 90 mmHg or Diastolic BP <= 60 mmHg'], data_copy['Age >= 65']))))
        curb_score, curb_risk = curbscore.compute_curb()

        #Computining MuLBSTA score and mortality rate.
        mulbscore = MuLBSTAscore(data_copy.loc[:, 'Multilobe infiltrate':'Age >=60'])
        mulb_score, mortality = mulbscore.compute()

        finalReport = pd.DataFrame(list(zip(patient_data['Patient ID'], psi_score, psi_risk, curb_score, curb_risk, mulb_score, mortality)), columns = ['Patient ID', 'PSI Score', 'PSI Risk/Disposition', 'CURB-65 Score', 'CURB-65 Risk/Disposition', 'MuLBSTA Score', 'Mortality %'])
        # reportFileName = filename.replace(".csv",'')+'_report.csv'
        # finalReport.to_csv(reportFileName)

        # return reportFileName
        return finalReport


