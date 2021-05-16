import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Combobox
from diploma_project import parse_args
import pandas as pd
from random import *
import json
import joblib
import math
from scipy.stats import variation
from numpy import asarray


class Client:
    def __init__(self, gender: str, config_file):
        self.config = config_file
        self.gender = gender
        self.age = 0.0
        self.law = ''
        self.law_params = {}
        self.key = ''
        self.income_sum = 0.0
        self.loan_law_parameters = {}
        self.loan = 0.0
        self.law_loan = ''
        self.rate = 0.0
        self.time = 0
        self.coef_solvency = 0.0
        self.rate_down = self.rate_up = 0.0
        self.time_down = self.time_up = 0
        self.solvency = 0.0
        self.max_enable_loan_sum = 0.0
        self.month_pay = 0.0
        self.full_loan = 0.0
        self.loan_down = 0.0
        self.loan_up = 0.0

    def generate_age(self, down_limit: int, up_limit: int):
        assert (down_limit >= 20.0) & (up_limit <= 70.0), 'invalid age'  # check age
        assert up_limit > down_limit, 'down limit age more up limit age'
        self.age = (up_limit - down_limit) * random() + down_limit

    def income(self, law: str):
        r = ''
        self.law = law
        for key_ in KEYS:
            if (self.age > self.config['age'][key_]['down']) & (self.age < self.config['age'][key_]['up']):
                r = key_
        self.key = self.key + r
        assert (self.law == 'uniform') | (self.law == 'exponential'), "invalid law"
        self.law_params = config['income'][self.gender][self.key][self.law]
        try:
            self.income_sum = (self.law_params['b'] - self.law_params['a']) * random() + self.law_params['a']
            assert self.law_params['lambda'] > 0, 'invalid parameter'
            self.income_sum = random.expovariate(lambd=self.law_params['lambda'])
        except KeyError:
            pass
        if self.income_sum == 0.0:
            print('invalid parameters for generation income sum')

    def generate_credit(self, key, law_loan: str):
        self.law_loan = law_loan
        self.loan_law_parameters = config['loan_amount'][self.gender][key][self.law_loan]
        try:
            self.loan = (self.loan_law_parameters['b'] - self.loan_law_parameters['a']) * random() + \
                        self.loan_law_parameters['a']
            assert self.loan_law_parameters['lambda'] > 0, 'invalid parameter'
            self.loan = random.expovariate(lambd=self.loan_law_parameters['lambda'])
        except KeyError:
            pass
        if self.loan == 0.0:
            print('invalid parameters for generation loan credit')
        if self.loan > 3000000.0:
            self.loan = 3000000.0
    def get_credit_params(self):
        self.rate_down = self.rate_up = self.time_up = self.time_down = 0
        assert (self.loan >= 45000.0) & (self.loan <= 3000000.0), 'invalid loan sum'
        if (self.loan >= 45000.0) & (self.loan <= 300000.0):
            self.loan_down = 45000.0
            self.loan_up = 300000.0
            self.rate_down = 13.9
            self.rate_up = 19.9
            self.time_down = 3
            self.time_up = 12
        elif (self.loan > 300000.0) & (self.loan <= 1000000.0):
            self.loan_down = 300000.0
            self.loan_up = 1000000.0
            self.rate_down = 12.9
            self.rate_up = 16.9
            self.time_down = 13
            self.time_up = 36
        elif (self.loan > 1000000.0) & (self.loan <= 3000000.0):
            self.loan_down = 1000000.0
            self.loan_up = 3000000.0
            self.rate_down = self.rate_up = 12.9
            self.time_down = 37
            self.time_up = 60

        self.rate = (self.rate_up - self.rate_down) * random() + self.rate_down
        self.time = int((self.time_up - self.time_down) * random() + self.time_down)
        month_rate = self.rate / 1200
        # ежемесячный платеж
        self.month_pay = self.loan * (month_rate + month_rate / ((1 + month_rate) ** self.time - 1))
        # полная сумма кредита
        self.full_loan = self.time * self.loan * (month_rate * (1 + month_rate) ** self.time) / ((1 + month_rate) ** self.time - 1)

    def check_solvency(self, income_sum, rate, time, loan):
        """
         проверка платежеспособности клиента
         """
        self.income_sum = income_sum
        self.rate = rate
        self.time = time
        self.loan = loan
        if self.income_sum < 32500.0:
            self.coef_solvency = 0.3
        elif (self.income_sum >= 32500.0) & (self.income_sum < 65000.0):
            self.coef_solvency = 0.4
        elif (self.income_sum >= 65000.0) & (self.income_sum < 130000.0):
            self.coef_solvency = 0.5
        elif self.income_sum >= 130000.0:
            self.coef_solvency = 0.6
        self.solvency = self.income_sum * self.coef_solvency * self.time

        self.max_enable_loan_sum = (self.solvency * 2400) / (1 + self.rate * (self.time + 1))
        assert self.max_enable_loan_sum >= self.loan, 'credit is unable'

def count_noreturn(pay, prob_base):
    """
    расчет размера месячного невозврата, эту функцию будем вызывать в main столько раз, сколько месяцев мы
    сгенерировали
    """
    month_pay = pay
    no_return_sum = 0
    month_prob = random()
    if month_prob < prob_base:  # пока задаем дефолт, следующий шаг - прикрепить модель
        coef_no_return = random()
        no_return_sum = coef_no_return * month_pay
    else:
        pass
    return month_prob, no_return_sum


def generate_params_from_combobox():
    # сюда будем писать данные из комбобоксов
    # нужно будет аккуратно находить колонку с соответсвующим постфиксом и писать в него 1, а все остальные заполнять 0
    # получаем инфомацию из Combobox
    columns = config['model_parameters']
    combo_values = [education.get(), occupation.get(), family_status.get(), income_type.get()]
    columns_for_1 = []
    columns_for_0 = []
    # префиксы из изначальноо датафрейма, которорые относятся к нашим combobox
    prefix_combobox = ['NAME_EDUCATION_TYPE', 'OCCUPATION_TYPE', 'NAME_FAMILY_STATUS', 'NAME_INCOME_TYPE']
    for i in range(len(prefix_combobox)):
        if (prefix_combobox[i]+'_'+combo_values[i].replace(' ', '_')) in columns:
            columns_for_1.append(prefix_combobox[i]+'_'+combo_values[i].replace(' ', '_'))
        else:
            columns_for_0.append(prefix_combobox[i]+'_'+combo_values[i].replace(' ', '_'))
    return columns_for_1, columns_for_0


def get_document_flag_values():
    documents_dict = {} # значения из этого словаря пойдут в модель в качестве flag_documents_x
    bools = [bool1, bool2, bool3, bool4, bool5, bool6, bool7, bool8, bool9, bool10, bool11, bool12, bool13]
    documents = ['FLAG_DOCUMENT_3', 'FLAG_DOCUMENT_5', 'FLAG_DOCUMENT_6', 'FLAG_DOCUMENT_8', 'FLAG_DOCUMENT_9',
                 'FLAG_DOCUMENT_11', 'FLAG_DOCUMENT_13', 'FLAG_DOCUMENT_14', 'FLAG_DOCUMENT_16', 'FLAG_DOCUMENT_17',
                 'FLAG_DOCUMENT_18', 'FLAG_DOCUMENT_19', 'FLAG_DOCUMENT_20']
    for i in range(13):
        if bools[i].get() == 0:
            documents_dict[documents[i]] = 0
        else:
            documents_dict[documents[i]] = 1
    return documents_dict



def generate_param_with_prefix(dataframe, pref):
    cols = []
    for column in dataframe.columns:
        if pref in column:
            dataframe[column].iloc[0] = random()
            cols.append(dataframe[column].iloc[0])
            max_ = max(cols)

    for column in dataframe.columns:
        if pref in column:
            if dataframe[column].iloc[0] == max_:
                dataframe[column].iloc[0] = 1
            else:
                dataframe[column].iloc[0] = 0
    return dataframe


def get_proba(parameters_dict):
    # generate_parameters = joblib.load('model_parameters_dict.pkl')
    generate_parameters = parameters_dict
    # print(generate_parameters)
    parameters_model = config['model_parameters']
    line_for_predict = pd.DataFrame(columns=parameters_model, index=[0])
    # подставляю данные из имитационной модели
    line_for_predict['DAYS_BIRTH'].iloc[0] = generate_parameters['age_client']
    line_for_predict['AMT_ANNUITY_x'].iloc[0] = generate_parameters['full_loan_credit']
    line_for_predict['AMT_CREDIT_x'].iloc[0] = generate_parameters['loan_credit']
    line_for_predict['AMT_CREDIT_SUM'].iloc[0] = generate_parameters['loan_credit']
    line_for_predict['AMT_INCOME_TOTAL'].iloc[0] = generate_parameters['income_sum_client']
    line_for_predict['CODE_GENDER_F'].iloc[0] = 1 if generate_parameters['gender_client'] == 'woman' else 0
    line_for_predict['DAYS_CREDIT_ENDDATE'].iloc[0] = generate_parameters['time_credit']

    prefix_list = ['CHANNEL_TYPE', 'CREDIT_TYPE', 'NAME_CASH_LOAN_PURPOSE', 'NAME_CLIENT_TYPE',
                  'NAME_CONTRACT_STATUS', 'NAME_GOODS_CATEGORY',
                  'NAME_HOUSING_TYPE', 'NAME_PAYMENT_TYPE', 'NAME_SELLER_INDUSTRY', 'NAME_TYPE_SUITE_x',
                   'ORGANIZATION_TYPE', 'PRODUCT_COMBINATION',
                  'WEEKDAY_APPR_PROCESS_START', 'NAME_PRODUCT_TYPE', 'NAME_PORTFOLIO',
                   'NAME_YIELD_GROUP', 'FONDKAPREMONT_MODE_not specified', 'HOUSETYPE_MODE']

    for prefix in prefix_list:
        line_for_predict = generate_param_with_prefix(line_for_predict, prefix)

    # в этой версии уточняется значение колонок с помщью комбобокс
    cols1, cols0 = generate_params_from_combobox()
    for col in cols1:
        line_for_predict[col].iloc[0] = 1
    for col in cols0:
        line_for_predict[col].iloc[0] = 0

    # в этой части записываем переменные из checkbox
    # TODO: как это красивее записать
    document_flags = get_document_flag_values()
    line_for_predict['FLAG_DOCUMENT_3'].iloc[0] = document_flags['FLAG_DOCUMENT_3']
    line_for_predict['FLAG_DOCUMENT_5'].iloc[0] = document_flags['FLAG_DOCUMENT_5']
    line_for_predict['FLAG_DOCUMENT_6'].iloc[0] = document_flags['FLAG_DOCUMENT_6']
    line_for_predict['FLAG_DOCUMENT_8'].iloc[0] = document_flags['FLAG_DOCUMENT_8']
    line_for_predict['FLAG_DOCUMENT_9'].iloc[0] = document_flags['FLAG_DOCUMENT_9']
    line_for_predict['FLAG_DOCUMENT_11'].iloc[0] = document_flags['FLAG_DOCUMENT_11']
    line_for_predict['FLAG_DOCUMENT_13'].iloc[0] = document_flags['FLAG_DOCUMENT_13']
    line_for_predict['FLAG_DOCUMENT_14'].iloc[0] = document_flags['FLAG_DOCUMENT_14']
    line_for_predict['FLAG_DOCUMENT_16'].iloc[0] = document_flags['FLAG_DOCUMENT_16']
    line_for_predict['FLAG_DOCUMENT_17'].iloc[0] = document_flags['FLAG_DOCUMENT_17']
    line_for_predict['FLAG_DOCUMENT_18'].iloc[0] = document_flags['FLAG_DOCUMENT_18']
    line_for_predict['FLAG_DOCUMENT_19'].iloc[0] = document_flags['FLAG_DOCUMENT_19']
    line_for_predict['FLAG_DOCUMENT_20'].iloc[0] = document_flags['FLAG_DOCUMENT_20']

    # здесь будем формировать признаки, где в названии встречается AVG, MEDI, MODE
    for column in line_for_predict.columns:
        if ('AVG' in column) | ('MEDI' in column) | ('MODE' in column):
            line_for_predict[column].iloc[0] = random()

    # теперь добавим информацию из внешних источников
    line_for_predict['EXT_SOURCE_1'].iloc[0] = (0.9444195 - 0.014568) * random() + 0.014568
    line_for_predict['EXT_SOURCE_2'].iloc[0] = (0.8549997 - 0.000001) * random() + 0.000001
    line_for_predict['EXT_SOURCE_3'].iloc[0] = (0.8939761 - 0.000527) * random() + 0.000527

    # теперь еще несколько дополнительных факторов
    line_for_predict['FLAG_EMAIL'].iloc[0] = generate_parameters['email_flag'] # из окна с данными
    line_for_predict['FLAG_OWN_CAR'].iloc[0] = generate_parameters['car_flag']# из окна с данными
    line_for_predict['OWN_CAR_AGE'].iloc[0] = generate_parameters['car_age']  # из окна с данными
    line_for_predict['FLAG_OWN_REALTY'].iloc[0] = 1 if random() > 0.5 else 0 # из окна с данными
    line_for_predict['FLAG_PHONE'].iloc[0] = generate_parameters['telephone_flag'] # из окна с данными
    line_for_predict['FLAG_WORK_PHONE'].iloc[0] = 1 if random() > 0.5 else 0 # из окна с данными

    # у нас еще есть информация про дни
    line_for_predict['DAYS_CREDIT'].iloc[0] = generate_parameters['time_credit'] * 30
    line_for_predict['DAYS_DECISION'].iloc[0] = (14 - 1) * random() + 1
    line_for_predict['DAYS_EMPLOYED'].iloc[0] = generate_parameters['employed']
    line_for_predict['DAYS_ID_PUBLISH'].iloc[0] = line_for_predict['DAYS_BIRTH'].iloc[0] - 20 \
        if line_for_predict['DAYS_BIRTH'].iloc[0] < 45 else line_for_predict['DAYS_BIRTH'].iloc[0] - 45
    line_for_predict['DAYS_REGISTRATION'].iloc[0] = (line_for_predict['DAYS_BIRTH'].iloc[0]) * random()
    line_for_predict['DAYS_LAST_PHONE_CHANGE'].iloc[0] = (10 - 0) * random() * 365
    line_for_predict['DAYS_TERMINATION'].iloc[0] = ((3 - 0) * random()) * 365
    line_for_predict['DAYS_CREDIT_UPDATE'].iloc[0] = (14 - 1) * random() + 1
    line_for_predict['DAYS_FIRST_DUE'].iloc[0] = (14 - 1) * random() + 1
    line_for_predict['REGION_POPULATION_RELATIVE'].iloc[0] = (0.072508 - 0.00029) * random() + 0.00029
    line_for_predict['AMT_GOODS_PRICE_x'].iloc[0] = line_for_predict['AMT_CREDIT_x'].iloc[0] * 0.9
    line_for_predict['CNT_PAYMENT'].iloc[0] = int(84 * random())
    line_for_predict['AMT_APPLICATION'].iloc[0] = 5850000 * random() # сумма предыдущего займа
    line_for_predict['NFLAG_INSURED_ON_APPROVAL'].iloc[0] = 1 if random() > 0.5 else 0
    line_for_predict['NFLAG_LAST_APPL_IN_DAY'].iloc[0] = 1 if random() > 0.5 else 0

    line_for_predict['REG_CITY_NOT_LIVE_CITY'].iloc[0] = 1 if random() > 0.5 else 0
    line_for_predict['REG_CITY_NOT_WORK_CITY'].iloc[0] = 1 if random() > 0.5 else 0
    line_for_predict['REG_REGION_NOT_LIVE_REGION'].iloc[0] = 1 if random() > 0.5 else 0
    line_for_predict['REG_REGION_NOT_WORK_REGION'].iloc[0] = 1 if random() > 0.5 else 0
    line_for_predict['LIVE_CITY_NOT_WORK_CITY'].iloc[0] = 1 if random() > 0.5 else 0
    line_for_predict['LIVE_REGION_NOT_WORK_REGION'].iloc[0] = 1 if random() > 0.5 else 0

    line_for_predict['REGION_RATING_CLIENT'].iloc[0] = int((3 - 1) * random() + 1)
    line_for_predict['REGION_RATING_CLIENT_W_CITY'].iloc[0] = int((3 - 1) * random() + 1)
    line_for_predict['HOUR_APPR_PROCESS_START_x'].iloc[0] = int((23 - 0) * random() + 0)
    line_for_predict['CNT_FAM_MEMBERS'].iloc[0] = generate_parameters['family_numbers']
    line_for_predict['CNT_CHILDREN'].iloc[0] = generate_parameters['children']

    line_for_predict['SELLERPLACE_AREA'].iloc[0] = 1000000 * random() if random() > 0.5 else -1

    line_for_predict['CREDIT_ACTIVE_Active'].iloc[0] = 1
    line_for_predict['CREDIT_ACTIVE_Closed'].iloc[0] = 0

    line_for_predict.fillna(1, inplace=True)  # временная мера, чтобы проверить работу модели

    model = joblib.load('update_model.pkl')

    proba = model.predict(line_for_predict)
    return proba


def create_key(age):
    age_d = int(age // 10)
    age_u = int(age // 10) + 1
    key = str(age_d*10)+'_'+str(age_u*10)
    return key

def programm_exit():
    root.destroy()


if __name__ == "__main__":
    args = parse_args()

    with open(args.config_file, encoding='UTF-8') as config_file:
        config = json.load(config_file)
    KEYS = list(config['age'].keys())

    root = tk.Tk() # родительское окно
    var1 = tk.IntVar()  # выбор пола
    var2 = tk.IntVar()  # проверка наличия почты
    var3 = tk.IntVar()  # проверка наличия телефона
    var4 = tk.IntVar()  # проверка наличия авто

    bool1 = tk.BooleanVar()  # флаг для документа 3
    bool2 = tk.BooleanVar()  # флаг для документа 5
    bool3 = tk.BooleanVar()  # флаг для документа 6
    bool4 = tk.BooleanVar()  # флаг для документа 8
    bool5 = tk.BooleanVar()  # флаг для документа 9
    bool6 = tk.BooleanVar()  # флаг для документа 11
    bool7 = tk.BooleanVar()  # флаг для документа 13
    bool8 = tk.BooleanVar()  # флаг для документа 14
    bool9 = tk.BooleanVar()  # флаг для документа 16
    bool10 = tk.BooleanVar()  # флаг для документа 17
    bool11 = tk.BooleanVar()  # флаг для документа 18
    bool12 = tk.BooleanVar()  # флаг для документа 19
    bool13 = tk.BooleanVar()  # флаг для документа 20

    age_down = age_up = emploeyd_years = family_numbers = children = 0.0
    root.title('Lukyanova Anastasia')

    # Первое окно - описание клиента (верхняя половина) (его же будем считать родительским окном)
    # Клиент
    tk.Label(text="Приветствуем вас в системе CreditL.", font='Broadway', width=30, anchor='s').grid(row=0, columnspan=4)
    tk.Label(text="Шаг 1. Создание клиента", font='Broadway', anchor='w', width=25).grid(column=0, row=1)
    tk.Label(text="Задайте возраст", font='Broadway', anchor='w', width=20).grid(column=0, row=2)
    tk.Label(text='Пол клиента', font='Broadway', anchor='w', width=20).grid(column=0, row=3)
    tk.Label(text='Уровень образования', font='Broadway', anchor='w', width=20).grid(column=0, row=4)
    tk.Label(text='Профессия клиента', font='Broadway', anchor='w', width=20).grid(column=0, row=5)
    tk.Label(text='Семейное положение', font='Broadway', anchor='w', width=20).grid(column=2, row=4)
    tk.Label(text='Тип дохода', font='Broadway', anchor='w', width=20).grid(column=2, row=5)
    tk.Label(text='Текущий стаж', font='Broadway', anchor='w', width=20).grid(column=0, row=6)
    tk.Label(text='Количество членов семьи', font='Broadway', width=20, anchor='w').grid(column=0, row=8)
    tk.Label(text='из них детей', font='Broadway', width=20).grid(column=2, row=8)
    tk.Label(text='Почта', font='Broadway', width=20, anchor='w').grid(column=0,row=9)
    tk.Label(text='Телефон', font='Broadway', width=20, anchor='w').grid(column=3, row=9)
    tk.Label(text='Машина', font='Broadway', width=20, anchor='w').grid(column=0, row=10)
    tk.Label(text='Возраст авто', font='Broadway', width=20, anchor='w').grid(column=3, row=10)
    tk.Label(text='Отметьте документы, предоставленные клиентом', width=40, anchor='w').grid(row=11, columnspan=2)

    e1 = tk.Entry(root, width=20, font='Broadway')
    e1.grid(column=1, row=2) # возраст (нижняя граница)
    e3 = tk.Entry(root, width=20, font='Broadway')
    e3.grid(column=1, row=6) # рабочий стаж
    e4 = tk.Entry(root, width=20, font='Broadway')
    e4.grid(column=1, row=8) # размер семьи
    e5 = tk.Entry(root, width=20, font='Broadway')
    e5.grid(column=3, row=8) # количество детей
    e6 = tk.Entry(root, width=20, font='Broadway')
    e6.grid(column=4, row=10) # возраст авто в случае его наличия

    v1 = tk.Radiobutton(text="Женский", font='Broadway', variable=var1, value=0, anchor='w').grid(row=3, column=1)
    v2 = tk.Radiobutton(text="Мужской", font='Broadway', variable=var1, value=1, anchor='w').grid(row=3, column=2)
    v3 = tk.Radiobutton(text='Yes', font='Broadway', variable=var2, value=0, anchor='w').grid(row=9, column=1)
    v4 = tk.Radiobutton(text='No', font="Broadway", variable=var2, value=1, anchor='w').grid(row=9, column=2)
    v5 = tk.Radiobutton(text='Yes', font='Broadway', variable=var3, value=0, anchor='w').grid(row=9, column=4)
    v6 = tk.Radiobutton(text='No', font="Broadway", variable=var3, value=1, anchor='w').grid(row=9, column=5)
    v7 = tk.Radiobutton(text='Yes', font='Broadway', variable=var4, value=0, anchor='w').grid(row=10, column=1)
    v8 = tk.Radiobutton(text='No', font='Broadway', variable=var4, value=1, anchor='w').grid(row=10, column=2)

    c1 = tk.Checkbutton(root, text="Document 3", variable=bool1, onvalue=1, offvalue=0, anchor='w').grid(row=12,
                                                                                                         column=0)
    c2 = tk.Checkbutton(root, text="Document 5", variable=bool2, onvalue=1, offvalue=0, anchor='w').grid(row=12,
                                                                                                         column=1)
    c3 = tk.Checkbutton(root, text="Document 6", variable=bool3, onvalue=1, offvalue=0, anchor='w').grid(row=12,
                                                                                                         column=2)
    c4 = tk.Checkbutton(root, text="Document 8", variable=bool4, onvalue=1, offvalue=0, anchor='w').grid(row=12,
                                                                                                         column=3)
    c5 = tk.Checkbutton(root, text="Document 9", variable=bool5, onvalue=1, offvalue=0, anchor='w').grid(row=13,
                                                                                                         column=0)
    c6 = tk.Checkbutton(root, text="Document 11", variable=bool6, onvalue=1, offvalue=0, anchor='w').grid(row=13,
                                                                                                         column=1)
    c7 = tk.Checkbutton(root, text="Document 13", variable=bool7, onvalue=1, offvalue=0, anchor='w').grid(row=13,
                                                                                                         column=2)
    c8 = tk.Checkbutton(root, text="Document 14", variable=bool8, onvalue=1, offvalue=0, anchor='w').grid(row=13,
                                                                                                         column=3)
    c9 = tk.Checkbutton(root, text="Document 16", variable=bool9, onvalue=1, offvalue=0, anchor='w').grid(row=14,
                                                                                                         column=0)
    c10 = tk.Checkbutton(root, text="Document 17", variable=bool10, onvalue=1, offvalue=0, anchor='w').grid(row=14,
                                                                                                         column=1)
    c11 = tk.Checkbutton(root, text="Document 18", variable=bool11, onvalue=1, offvalue=0, anchor='w').grid(row=14,
                                                                                                         column=2)
    c12 = tk.Checkbutton(root, text="Document 19", variable=bool12, onvalue=1, offvalue=0, anchor='w').grid(row=14,
                                                                                                         column=3)
    c13 = tk.Checkbutton(root, text="Document 20", variable=bool13, onvalue=1, offvalue=0, anchor='w').grid(row=14,
                                                                                                         column=4)

    education = Combobox(root, font='Broadway', width=20)  # для выбора уровня образования
    occupation = Combobox(root, font='Broadway', width=20) # профессия
    family_status = Combobox(root, font='Broadway', width=20) # семейное положение
    income_type = Combobox(root, font='Broadway', width=20) # тип дохода

    education['values'] = ('Secondary / secondary special', 'Higher education', 'Incomplete higher', 'Lower secondary',
                           'Academic degree')
    occupation['values'] = ('Laborers', 'Core staff', 'Accountants', 'Managers', 'Drivers', 'Sales staff',
                            'Cleaning staff', 'Cooking staff', 'Private service staff', 'Medicine staff',
                            'Security staff', 'High skill tech staff', 'Waiters/barmen staff', 'Low-skill Laborers',
                            'Realty agents', 'Secretaries', 'IT staff','HR staff')
    family_status['values'] = ('Single / not married', 'Married', 'Civil marriage', 'Widow', 'Separated', 'Unknown')
    income_type['values'] = ('Working', 'State servant', 'Commercial associate', 'Pensioner', 'Unemployed', 'Student',
                             'Businessman', 'Maternity leave')
    education.grid(column=1, row=4)
    occupation.grid(column=1, row=5)
    family_status.grid(column=3, row=4)
    income_type.grid(column=3, row=5)

    # 2 окно - формирование кредитной заявки
    var1_cr = tk.IntVar() # выбор закона распределения для дохода
    var2_cr = tk.IntVar() # выбор типа кредитной заявки
    var3_cr = tk.IntVar() # выбор закона распределения для суммы кредита

    credit_window = tk.Toplevel(root)
    credit_window.title('Заявка на кредит')
    tk.Label(credit_window, text='Доход клиента', font='Broadway', width=30, anchor='w').grid(row=0, column=0)
    tk.Label(credit_window, text='Формирование заявки', font='Broadway', width=30, anchor='s').grid(row=2, columnspan=4)
    tk.Label(credit_window, text='Тип кредита', font='Broadway', width=30, anchor='w').grid(row=3, column=0)
    tk.Label(credit_window, text='Закон распределения для кредита', font='Broadway', width=30, anchor='w').grid(row=4, column=0)
    tk.Label(credit_window, text='Кредит: нижняя граница', font='Broadway', width=30, anchor='w').grid(row=5, column=0)
    tk.Label(credit_window, text='верхняя граница', font='Broadway', width=30, anchor='w').grid(row=5, column=2)
    tk.Label(credit_window, text='Лямбда для суммы кредита', font='Broadway', width=30, anchor='w').grid(row=6, column=0)
    tk.Label(credit_window, text='Процентная ставка: min', font='Broadway', width=30, anchor='w').grid(row=7, column=0)
    tk.Label(credit_window, text='max', font='Broadway', width=30, anchor='w').grid(row=7, column=2)
    tk.Label(credit_window, text='Кол-во месяцев: min', font='Broadway', width=30, anchor='w').grid(row=8, column=0)
    tk.Label(credit_window, text='max', font='Broadway', width=30, anchor='w').grid(row=8, column=2)
    tk.Label(credit_window, text='Количество иммитационных экспериментов', font='Broadway', width=40, anchor='e')\
        .grid(row=9, column=1, columnspan=2)
    tk.Label(credit_window, text='Критический порог для невозврата', width=40, anchor='e', font='Broadway')\
        .grid(row=10, column=1, columnspan=2)

    e1_cr = tk.Entry(credit_window, width=20, font='Broadway')
    e1_cr.grid(row=0, column=3) # доход клиента
    e1_norm_down = tk.Entry(credit_window, width=20, font='Broadway')
    e1_norm_down.grid(row=1, column=0) # нижняя граница равномерного закона распределения (для дохода)
    e1_norm_up = tk.Entry(credit_window, width=20, font='Broadway')
    e1_norm_up.grid(row=1, column=1)  # верхняя граница равномерного закона распределения (для дохода)
    e1_norm_exp = tk.Entry(credit_window, width=20, font='Broadway')
    e1_norm_exp.grid(row=1, column=2)  # параметр лямбда для показательного закона распределения (для дохода)
    e2_cr = tk.Entry(credit_window, width=20, font='Broadway')
    e2_cr.grid(row=5, column=1) # нижняя граница кредита (равномерный закон распределения)
    e3_cr = tk.Entry(credit_window, width=20, font='Broadway')
    e3_cr.grid(row=5, column=3) # верхняя граница кредита (равномерный закон распределения)
    e2_3_exp = tk.Entry(credit_window, width=20, font='Broadway')
    e2_3_exp.grid(row=6, column=1) # параметр лямбда для суммы кредита
    e4_cr = tk.Entry(credit_window, width=20, font='Broadway')
    e4_cr.grid(row=7, column=1) # нижняя граница процентной ставки
    e5_cr = tk.Entry(credit_window, width=20, font='Broadway')
    e5_cr.grid(row=7, column=3) # верхняя граница процентной ставки
    e6_cr = tk.Entry(credit_window, width=20, font='Broadway')
    e6_cr.grid(row=8, column=1) # нижняя граница продолжительности кредита в месяцах
    e7_cr = tk.Entry(credit_window, width=20, font='Broadway')
    e7_cr.grid(row=8, column=3) # верхняя граница продолжительности кредита в месяцах
    e8_cr = tk.Entry(credit_window, width=20, font='Broadway')
    e8_cr.grid(row=9, column=3) # количество иммитационных экспериментов
    e9_cr = tk.Entry(credit_window, width=20, font='Broadway')
    e9_cr.grid(row=10, column=3) # порог для невозврата (в процентной доле)

    v1_cr = tk.Radiobutton(credit_window, text='Равномерный', font='Broadway', variable=var1_cr, value=0, anchor='w')
    v1_cr.grid(row=0, column=1)
    v2_cr = tk.Radiobutton(credit_window, text='Показательный', font='Broadway', variable=var1_cr, value=1, anchor='w')
    v2_cr.grid(row=0, column=2)
    v3_cr = tk.Radiobutton(credit_window, text='Натуральный кредит', font='Broadway', variable=var2_cr, value=0, anchor='w')
    v3_cr.grid(row=3, column=1)
    v4_cr = tk.Radiobutton(credit_window, text='Овердрафт', font='Broadway', variable=var2_cr, value=1, anchor='w')
    v4_cr.grid(row=3, column=2)
    v5_cr = tk.Radiobutton(credit_window, text='Равномерный закон', font='Broadway', variable=var3_cr, value=0, anchor='w')
    v5_cr.grid(row=4, column=1)
    v6_cr = tk.Radiobutton(credit_window, text='Равномерный закон', font='Broadway', variable=var3_cr, value=1, anchor = 'w')
    v6_cr.grid(row=4, column=2)

    # 3 окно - окно с метриками
    metrics_window = tk.Toplevel(root)
    metrics_window.title('CreditL. Результаты расчета')
    tk.Label(metrics_window, text='Количество имитационных экспериментов', width=40, font='Broadway', anchor='w').grid(row=0,
                                                                                                              column=0)
    tk.Label(metrics_window, text='Результаты экспериментов', width=40, font='Broadway', anchor='s').grid(row=1)
    tk.Label(metrics_window, text='Средний ожидаемый полный возврат', width=40, font='Broadway', anchor='w').grid(row=2, column=0)
    tk.Label(metrics_window, text='Средний ожидаемый невозврат', width=40, font='Broadway', anchor='w').grid(row=3, column=0)
    tk.Label(metrics_window, text='Отношение невозврата к возврату', width=40, font='Broadway', anchor='w').grid(row=4, column=0)
    tk.Label(metrics_window, text='Средняя базовая вероятность невозврата', width=40, font='Broadway', anchor='w')\
        .grid(row=5, column=0)
    tk.Label(metrics_window, text='Вероятность превышения невозвратом порога', width=40, font='Broadway', anchor='w')\
        .grid(row=6, column=0)
    tk.Label(metrics_window, text='Коэффициент вариации для невозврата', width=40, font='Broadway', anchor='w')\
        .grid(row=7, column=0)

    e1_metr = tk.Entry(metrics_window, width=20, font='Broadway')
    e1_metr.grid(row=0, column=1) # кол-во экспериментов
    e2_metr = tk.Entry(metrics_window, width=20, font='Broadway')
    e2_metr.grid(row=2, column=1) # средняя полная сумма кредита или полный ожидаемый возврат
    e3_metr = tk.Entry(metrics_window, width=20, font='Broadway')
    e3_metr.grid(row=3, column=1) # средний невозврат
    e4_metr = tk.Entry(metrics_window, width=20, font='Broadway')
    e4_metr.grid(row=4, column=1) # доля невозвратов
    e5_metr = tk.Entry(metrics_window, width=20, font='Broadway')
    e5_metr.grid(row=5, column=1) # Средняя базовая вероятность невозврата
    e6_metr = tk.Entry(metrics_window, width=20, font='Broadway')
    e6_metr.grid(row=6, column=1) # вероятность превышения невозвратом порога
    e7_metr = tk.Entry(metrics_window, width=20, font='Broadway')
    e7_metr.grid(row=7, column=1) # коэффициент вариации

    def get_data_and_count_metrics():
        if var1.get() == 0:
            gender = 'woman'
        elif var1.get() == 1:
            gender = 'man'
        if var2.get() == 0:
            mail = 1
        elif var2.get() == 1:
            mail = 0
        if var3.get() == 0:
            telephone = 1
        elif var3.get() == 1:
            telephone = 0
        client = Client(gender, config)
        client.age = float(e1.get())
        age = '{:2.2f}'.format(float(client.age))
        if var4.get() == 0:
            car = 1
        if var4.get() == 1: # выбран флаг об отсутсвиии машины у клиента
            car = 0
            e6.delete(0, tk.END)
            e6.insert(0,str(0))

        if not e1_cr.get():
            if var1_cr.get() == 0:
                law = 'uniform'
                income_sum = (float(e1_norm_up.get()) - float(e1_norm_down.get())) * random() + float(e1_norm_down.get())
                e1_cr.delete(0, tk.END)
                e1_cr.insert(0, income_sum)
                client.income(law)
            if var1_cr.get() == 1:
                law = 'exponential'
                lymbda = float(e1_norm_exp.get())
                income_sum = -math.log(random()) / lymbda
                e1_cr.delete(0, tk.END)
                e1_cr.insert(0, income_sum)
                client.income(law)
        else:
            income_sum = float(e1_cr.get())
            e1_cr.delete(0, tk.END)
            e1_cr.insert(0, income_sum)

        # получаем информацию о сотруднике: стаж, кол-во членов семьи и детей
        employed_years ='{:2.2f}'.format(float(e3.get())) #рабочий стаж
        family_count = int(e4.get())
        children_count = int(e5.get())
        car_age = '{:2.2f}'.format(float(e6.get()))
        income_sum_client = float(e1_cr.get())
        experiments = int(e8_cr.get())
        # формируем словарь с параметрами (в этой части те, которые не меняются (берем из первого окна и доход из второго)
        # те, что сейчас занулены, будут подставляться  в цикле
        model_parameters_dict = {'age_client': float(age),
                                 'gender_client': gender,
                                 'income_sum_client': income_sum_client,
                                 'solvency_credit': 0.0,
                                 'loan_credit': 0.0,
                                 'rate_credit': 0.0,
                                 'time_credit': 0,
                                 'month_pay_credit': 0.0,
                                 'full_loan_credit': 0.0,
                                 'employed': float(employed_years),
                                 'family_numbers': family_count,
                                 'children': children_count,
                                 'email_flag': mail,
                                 'telephone_flag': telephone,
                                 'car_flag': car,
                                 'car_age': float(car_age)
                                 }
        sum_no_return = 0.0
        sum_base_proba = 0.0
        sum_full_loan_from_list = 0.0
        count_no_return_cases = 0  # количество невозвратов
        more_porog = []
        full_loan_sum_list = []
        base_proba_list = []
        no_return_list = []
        for _ in range(experiments):
            if (not e2_cr.get()) & (not e3_cr.get()):
                client.generate_credit(create_key(float(age)), 'uniform')
                client.get_credit_params()
                e2_cr.delete(0, tk.END)
                e2_cr.insert(0, client.loan_down)
                e3_cr.delete(0, tk.END)
                e3_cr.insert(0, client.loan_up)
                e4_cr.delete(0, tk.END)
                e4_cr.insert(0, client.rate_down)
                e5_cr.delete(0, tk.END)
                e5_cr.insert(0, client.rate_up)
                e6_cr.delete(0, tk.END)
                e6_cr.insert(0, client.time_down)
                e7_cr.delete(0, tk.END)
                e7_cr.insert(0, client.time_up)
            if e2_cr.get() and e3_cr.get():
                client.loan = (float(e3_cr.get()) - float(e2_cr.get())) * random() + float(e2_cr.get())
                client.get_credit_params()
                e4_cr.delete(0, tk.END)
                e4_cr.insert(0, client.rate_down)
                e5_cr.delete(0, tk.END)
                e5_cr.insert(0, client.rate_up)
                e6_cr.delete(0, tk.END)
                e6_cr.insert(0, client.time_down)
                e7_cr.delete(0, tk.END)
                e7_cr.insert(0, client.time_up)

            model_parameters_dict['solvency_credit'] = client.solvency
            model_parameters_dict['loan_credit'] = client.loan
            model_parameters_dict['rate_credit'] = client.rate
            model_parameters_dict['time_credit'] = client.time
            model_parameters_dict['month_pay_credit'] = client.month_pay
            model_parameters_dict['full_loan_credit'] = client.full_loan

            base_proba = get_proba(model_parameters_dict)
            base_proba_list.append(base_proba[0])

            e1_metr.config(state='normal')
            e1_metr.delete(0, tk.END)
            e1_metr.insert(0, experiments)
            e1_metr.config(state='disabled')
            noret = count_noreturn(float(client.full_loan), base_proba)[1]
            no_return_list.append(noret)
            full_loan_sum_list.append(client.full_loan)

            if noret != 0:
                print(noret)
                count_no_return_cases += 1
                # if noret >= client.full_loan*float(e9_cr.get()):
                if noret >= float(e9_cr.get()):
                    more_porog.append(noret)
        sum_no_return += sum([i for i in no_return_list])
        sum_base_proba += sum([i for i in base_proba_list])
        sum_full_loan_from_list += sum([i for i in full_loan_sum_list])
        print(more_porog)

        full_loan = str('{:10.4f}'.format(sum_full_loan_from_list / experiments)) # размер среднего ожидаемого возврата
        noret_value = str('{:10.4f}'.format(sum_no_return / experiments))  # размер среднего невозврата
        noret_part_value = str('{:10.4f}'.format(sum_no_return / sum_full_loan_from_list))  # отношение невозврата к возврату
        mean_base_proba = str('{:10.4f}'.format(sum_base_proba / experiments))  # средняя базовая вероятность невозврата
        more_porog_count = str('{:10.4f}'.format(len(more_porog) / experiments))  # вероятность превышения невозвратом порога
        coef_variation = str('{:10.4f}'.format(variation(asarray(no_return_list)))) # коэффициент вариации


        e2_metr.delete(0, tk.END)
        e2_metr.insert(0, full_loan)
        e3_metr.delete(0, tk.END)
        e3_metr.insert(0, noret_value)
        e4_metr.delete(0, tk.END)
        e4_metr.insert(0, noret_part_value)
        e5_metr.delete(0, tk.END)
        e5_metr.insert(0, mean_base_proba)
        e6_metr.delete(0, tk.END)
        e6_metr.insert(0, more_porog_count)
        e7_metr.delete(0, tk.END)
        e7_metr.insert(0, coef_variation)


    button1 = tk.Button(credit_window, text="Рассчитать метрики", font='Broadway',
                        command=get_data_and_count_metrics,
                        state=tk.NORMAL)
    button1.grid(row=12, sticky='S', columnspan=4)  # сбор все информации про кредит и клиента, передача данных в модель

    button2 = tk.Button(metrics_window, text='Exit program', font='Broadway',
                        command=programm_exit, state=tk.NORMAL)
    button2.grid(row=10, sticky='S', columnspan=2)

    # запуск окна
    root.mainloop()

