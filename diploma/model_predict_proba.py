import joblib
import json
import pandas as pd
import random
import lightgbm as lgb

from diploma_project import parse_args


def get_proba(dataframe: pd.DataFrame):
    proba = model.predict(dataframe)
    return proba


def generate_param_with_prefix(dataframe, pref):
    cols = []
    for column in dataframe.columns:
        if pref in column:
            dataframe[column].iloc[0] = random.random()
            cols.append(dataframe[column].iloc[0])
            max_ = max(cols)

    for column in dataframe.columns:
        if pref in column:
            if dataframe[column].iloc[0] == max_:
                dataframe[column].iloc[0] = 1
            else:
                dataframe[column].iloc[0] = 0

    return dataframe


args = parse_args()

with open(args.config_file, encoding='UTF-8') as config_file:
    config = json.load(config_file)

generate_parameters = joblib.load('model_parameters_dict.pkl')

# прочитаем все параметры, которые пойдут в модель (пикл уже обучен, мы просто будем передовать строку в модель)
parameters_model = config['model_parameters']
line_for_predict = pd.DataFrame(columns=parameters_model, index=[0])
# подставляю данные из имитационной модели
line_for_predict['DAYS_BIRTH'].iloc[0] = generate_parameters['age_client']
line_for_predict['AMT_ANNUITY_x'].iloc[0] = generate_parameters['full_loan_credit']
line_for_predict['AMT_CREDIT_x'].iloc[0] = generate_parameters['loan_credit']
line_for_predict['AMT_CREDIT_SUM'].iloc[0] = generate_parameters['loan_credit']
line_for_predict['AMT_INCOME_TOTAL'].iloc[0] = generate_parameters['income_sum_client']
line_for_predict['CODE_GENDER_F'].iloc[0] = 1 if generate_parameters['gender_client']=='woman' else 0
line_for_predict['DAYS_CREDIT_ENDDATE'].iloc[0] = generate_parameters['time_credit']

# теперь будем подставлять значения туда, где речь идет о признаках с одинаковым префиксом
pref1 = 'CHANNEL_TYPE'
pref2 = 'CREDIT_TYPE'
pref3 = 'FLAG_DOCUMENT'
pref4 = 'NAME_CASH_LOAN_PURPOSE'
pref5 = 'NAME_CLIENT_TYPE'
pref6 = 'NAME_CONTRACT_STATUS'
pref7 = 'NAME_EDUCATION_TYPE'
pref8 = 'NAME_FAMILY_STATUS'
pref9 = 'NAME_GOODS_CATEGORY'
pref10 = 'NAME_HOUSING_TYPE'
pref11 = 'NAME_PAYMENT_TYPE'
pref12 = 'NAME_SELLER_INDUSTRY'
pref13 = 'NAME_TYPE_SUITE_x'
pref14 = 'OCCUPATION_TYPE'
pref15 = 'ORGANIZATION_TYPE'
pref16 = 'PRODUCT_COMBINATION'
pref17 = 'WALLSMATERIAL_MODE'
pref18 = 'WEEKDAY_APPR_PROCESS_START'

line_for_predict = generate_param_with_prefix(line_for_predict, pref1)
line_for_predict = generate_param_with_prefix(line_for_predict, pref2)
line_for_predict = generate_param_with_prefix(line_for_predict, pref3)
line_for_predict = generate_param_with_prefix(line_for_predict, pref4)
line_for_predict = generate_param_with_prefix(line_for_predict, pref5)
line_for_predict = generate_param_with_prefix(line_for_predict, pref6)
line_for_predict = generate_param_with_prefix(line_for_predict, pref7)
line_for_predict = generate_param_with_prefix(line_for_predict, pref8)
line_for_predict = generate_param_with_prefix(line_for_predict, pref9)
line_for_predict = generate_param_with_prefix(line_for_predict, pref10)
line_for_predict = generate_param_with_prefix(line_for_predict, pref11)
line_for_predict = generate_param_with_prefix(line_for_predict, pref12)
line_for_predict = generate_param_with_prefix(line_for_predict, pref13)
line_for_predict = generate_param_with_prefix(line_for_predict, pref14)
line_for_predict = generate_param_with_prefix(line_for_predict, pref15)
line_for_predict = generate_param_with_prefix(line_for_predict, pref16)
line_for_predict = generate_param_with_prefix(line_for_predict, pref17)
line_for_predict = generate_param_with_prefix(line_for_predict, pref18)

# здесь будем формировать признаки, где в названии встречается AVG, MEDI, MODE
for column in line_for_predict.columns:
    if ('AVG' in column)|('MEDI' in column)|('MODE' in column):
        line_for_predict[column].iloc[0] = random.random()

# print(line_for_predict)
line_for_predict.fillna(0, inplace=True)  # временная мера, чтобы проверить работу модели

model = joblib.load('update_model.pkl')

proba = get_proba(line_for_predict)
print(proba)

# joblib.dump(proba, 'proba.pkl')
