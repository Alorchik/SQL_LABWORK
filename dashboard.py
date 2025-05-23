import streamlit as st
import pymysql
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.ticker import MaxNLocator
import seaborn as sns

def get_connection():
    return pymysql.connect(
            host='localhost',
            user='root',
            password='10082005',
            database='sys',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
    )

def load_analysis_data():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM Analysis;")
    rows = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(rows)
    return df
def load_families_data():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM Families;")
    rows = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(rows)
    return df
def load_samples_data():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM Samples;")
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)
def load_projects_data():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM Projects;")
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)
def load_seqtypes_data():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM SequencingType;")
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)
def load_plans_data():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM Plans;")
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)
def load_patients_data():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM Patients;")
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)
def load_runs_data():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM Runs;")
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)
def load_icd_data():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM ICD;")
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)
@st.cache_data
def load_data():
    data = {}
    data['analysis'] = load_analysis_data()
    data['families'] = load_families_data()
    data['samples'] = load_samples_data()
    data['projects'] = load_projects_data()
    data['seqtypes'] = load_seqtypes_data()
    data['plans'] = load_plans_data()
    data['patients'] = load_patients_data()
    data['runs'] = load_runs_data()
    data['icd'] = load_icd_data()
    # При желании другие таблицы можно грузить так (просто пример):
    # conn = get_connection()
    # data['patients'] = pd.read_sql("SELECT * FROM Patients;", conn)
    # data['samples'] = pd.read_sql("SELECT * FROM Samples;", conn)
    # conn.close()
    
    return data

def plot_histogram(df, column):
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6)) 
    ax.tick_params(axis='x', labelsize=7)  
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    ax.hist(df[column].dropna(), bins=30, color='skyblue', edgecolor='black')
    ax.set_title(f"Распределение {column}")
    ax.set_xlabel(column)
    ax.set_ylabel("Количество записей")
    st.pyplot(fig)

if __name__ == "__main__":
    st.title("Анализ данных из бд")
    st.title("")
    st.title("")
    st.title("1)Как распределены метрики качества секвенирования?")

    data = load_data()
    #Задание 1 
    df_analysis = data['analysis']
    # Построим гистограммы по нужным метрикам
    metrics = ['Coverage', 'MeanDepth', 'NumberReads', 'Uniformity']
    for metric in metrics:
        plot_histogram(df_analysis, metric)
    #Задание 2 
    st.title("2)Сколько результатов было выдано партнерам?")
 # Обработка как булевого поля: 1 — выдано, 0 — нет
    issued_count = df_analysis[df_analysis['ResultGiven'] == 1].shape[0]
    not_issued_count = df_analysis[df_analysis['ResultGiven'] == 0].shape[0]

    st.metric(label="Результатов выдано партнёрам", value=issued_count)

    # Данные для графика
    categories = ['Выдано', 'Не выдано']
    values = [issued_count, not_issued_count]
    colors = ['green', 'red']

    fig, ax = plt.subplots()
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    bars = ax.bar(categories, values, color=colors, edgecolor='white')

    ax.set_title("Распределение выдачи результатов", color='white')
    ax.set_ylabel("Количество", color='white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')

    # Подписи на столбцах
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    color='white', fontsize=8)

    st.pyplot(fig)
    #Задание 3
    df_families = data['families']

    # 1. Количество семей
    num_families = df_families['ID'].nunique()
    st.subheader("2) Сколько семей участвовало в исследовании?")
    st.metric(label="Количество семей", value=num_families)

    # 2. Доля близкородственных браков
    inbred_count = df_families[df_families['Inbreeding'] == 1].shape[0]
    total_families = df_families.shape[0]
    inbred_ratio = inbred_count / total_families if total_families else 0

    st.metric(label="Доля близкородственных браков", value=f"{inbred_ratio:.2%}")

    # 3. Визуализация: столбчатая диаграмма
    labels = ['Близкородственные', 'Обычные']
    values = [inbred_count, total_families - inbred_count]
    colors = ['red', 'green']

    fig, ax = plt.subplots()
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    bars = ax.bar(labels, values, color=colors, edgecolor='white')

    ax.set_title("Типы браков среди семей", color='white')
    ax.set_ylabel("Количество", color='white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.title.set_color('white')
    ax.yaxis.label.set_color('white')

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha='center', va='bottom',
                color='white', fontsize=8)

    st.pyplot(fig)
    #Задание 4 
    st.title("4) Соотношение типов исследований и вклад партнеров")
    df_samples = data['samples']
    df_projects = data['projects']
    df_seqtypes = data['seqtypes']

    # Получим данные из таблицы Plans
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT Sample, SequencingType FROM Plans;")
    df_plans = pd.DataFrame(cursor.fetchall())
    conn.close()

    # Объединение с проектами (полное, чтобы не терять строки)
    merged_df = df_samples.merge(df_projects[['ID', 'Partner']], left_on='Project', right_on='ID', suffixes=('', '_proj'), how='left')
    merged_df['Partner'] = merged_df['Partner'].fillna('Неизвестно')

    # Присоединяем планы секвенирования
    merged_df = merged_df.merge(df_plans, left_on='UIN1', right_on='Sample', how='left')

    # Присоединяем типы секвенирования
    merged_df = merged_df.merge(df_seqtypes, left_on='SequencingType', right_on='UniqueID', how='left')
    # Группировка
    group_df = merged_df.groupby(['Partner', 'Name']).size().reset_index(name='Count')

    # Построение графика
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    sns.set(style="darkgrid")
    sns.barplot(
        data=group_df,
        x='Partner',
        y='Count',
        hue='Name',
        palette='pastel',
        ax=ax
    )
    ax.set_title("Типы секвенирования у партнёров", fontsize=16, color='white')
    ax.set_xlabel("Партнёры", color='white')
    ax.set_ylabel("Количество заказов", color='white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.legend(title='Метод секвенирования', title_fontsize='13', fontsize='11')
    legend = ax.get_legend()
    frame = legend.get_frame()
    frame.set_facecolor('black')
    frame.set_edgecolor('white')
    for text in legend.get_texts():
        text.set_color('white')
    legend.get_title().set_color('white')
    st.pyplot(fig)
    #Задание 5 
    st.title("5) Какова доля просроченных анализов?")
    df_analysis = data['analysis']
    df_samples = data['samples']
    df_plans = data['plans']

    # Соединяем Analysis с Plans
    intermediate_df = df_analysis.merge(df_plans, left_on='Plan', right_on='UniquelID', how='inner')

    # Затем добавляем данные из Samples
    merged_df = intermediate_df.merge(df_samples, left_on='Sample', right_on='UIN1', how='inner')

    # Конвертируем даты в подходящий формат
    merged_df['AnalysisDate'] = pd.to_datetime(merged_df['AnalysisDate'])
    merged_df['Deadline'] = pd.to_datetime(merged_df['Deadline'])

    # Фильтруем просроченные анализы
    overdue_analyses = merged_df[merged_df['AnalysisDate'] > merged_df['Deadline']]

    # Рассчитываем статистику
    total_analyses = len(merged_df)
    overdue_count = len(overdue_analyses)
    overdue_percentage = (overdue_count / total_analyses) * 100

    # Представляем результат
    st.header("5) Какова доля просроченных анализов?")
    st.write(f"Общее число анализов: {total_analyses}")
    st.write(f"Количество просроченных анализов: {overdue_count}")
    st.write(f"Доля просроченных анализов: {overdue_percentage:.2f}%")

    # Построим график
    labels = ["В срок", "Просрочено"]
    sizes = [total_analyses - overdue_count, overdue_count]
    explode = (0, 0.1)  # Немного выделим сектор "Просрочено"
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', startangle=90, colors=["lightgreen", "salmon"])
    ax1.axis('equal')  # Равномерное масштабирование круга
    st.pyplot(fig1)
    #Задание 6 
    st.title("6) Сколько анализов было сделано в рамках каких проектов?")
    df_analysis = data['analysis']
    df_plans = data['plans']
    df_samples = data['samples']
    df_projects = data['projects']
        # Сначала объединяем Analysis с Plans
    intermediate_df = df_analysis.merge(df_plans, left_on='Plan', right_on='UniquelID', how='inner')

    # Затем объединяем полученный результат с Samples
    merged_df = intermediate_df.merge(df_samples, left_on='Sample', right_on='UIN1', how='inner')

    # Теперь добавляем данные из Projects
    final_df = merged_df.merge(df_projects, left_on='Project', right_on='ID', how='inner')

    # Агрегирование количества анализов по каждому проекту
    analyses_per_project = final_df.groupby('Name').size().reset_index(name='Count')

    # Установка индекса перед стилизацией
    nalyses_per_project = final_df.groupby('Name').size().reset_index(name='Count')

    # Выводим результаты
    st.table(analyses_per_project.reset_index(drop=True))

    # Визуализация
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=analyses_per_project, x='Name', y='Count', palette='pastel', ax=ax)
    ax.set_title("Количество анализов по проектам")
    ax.set_xlabel("Проект")
    ax.set_ylabel("Количество анализов")
    st.pyplot(fig)

    #Задание 7 
    st.title("7) Каков соотношение полов, распределение возраста в исследовании среди пробандов?")
    df_patients = data['patients']

    # Отфильтруем только пробандов
    probands = df_patients.query("FamilyRelation == 'пробанд'")

    # Преобразуем дату рождения в правильный формат (если не датетайм)
    probands['Birthday'] = pd.to_datetime(probands['Birthday'])

    # Пол пробандов
    sex_counts = probands['Sex'].value_counts().rename_axis('Пол').reset_index(name='Количество')

    # Возраст пробандов
    current_year = pd.Timestamp.now().year
    probands['Age'] = current_year - probands['Birthday'].dt.year

    # Выводим результаты без таблиц
    st.subheader("Соотношение полов среди пробандов")
    fig_sex, ax_sex = plt.subplots()
    sex_counts['Пол'] = sex_counts['Пол'].map({1: 'Мужской', 2: 'Женский'})  # Преобразуем числовые значения в текстовые
    sns.barplot(data=sex_counts, x='Пол', y='Количество', palette='pastel', ax=ax_sex)
    ax_sex.set_title("Соотношение полов среди пробандов")
    ax_sex.set_xlabel("Пол")
    ax_sex.set_ylabel("Количество пробандов")
    st.pyplot(fig_sex)

    # Гистограмма для возрастов
    st.subheader("Возрастное распределение среди пробандов")
    fig_age, ax_age = plt.subplots()
    sns.histplot(data=probands, x='Age', bins=18, kde=False, color='skyblue', ax=ax_age)
    ax_age.set_title("Возрастное распределение среди пробандов")
    ax_age.set_xlabel("Возраст")
    ax_age.set_ylabel("Количество пробандов")
    st.pyplot(fig_age)

    #Задание 8 
    st.title("8) Грубо оцените размер вставки (insert size) для каждого образца.")
    df_analysis = data['analysis']
    df_samples = data['samples']

    # Объединяем Analysis с Plans
    intermediate_df = df_analysis.merge(df_plans, left_on='Plan', right_on='UniquelID', how='inner')

    # Затем добавляем данные из Samples
    merged_df = intermediate_df.merge(df_samples, left_on='Sample', right_on='UIN1', how='inner')

    # Оценка размера вставки
    merged_df['InsertSize'] = (3 * 10**9 * merged_df['MeanDepth'] * merged_df['Coverage']) /( merged_df['NumberReads'] * 100 )

    # Создаём таблицу с нужными данными
    result_table = merged_df[['UIN1', 'NumberReads', 'MeanDepth', 'Coverage', 'InsertSize']]

    # Выводим таблицу с возможностью прокрутки и фильтрации
    st.dataframe(result_table, width=800, height=300)
    #Задание 9
    st.title("9) Оцените нагрузку приборов.")
    # Подсчёт количества запусков для каждой модели
    df_runs = data['runs']
    # Подсчёт количества запусков для каждой модели
    model_counts = df_runs['Model'].value_counts().reset_index()
    model_counts.columns = ['Model', 'Количество запусков']

    # Построение столбчатой диаграммы
    fig, ax = plt.subplots()
    sns.barplot(data=model_counts, x='Model', y='Количество запусков', palette='pastel', ax=ax)
    ax.set_title("Нагрузка приборов по количеству запусков")
    ax.set_xlabel("Модель прибора")
    ax.set_ylabel("Количество запусков")
    st.pyplot(fig)  
    #Задание 10
    st.title("10)Сколько пробандов, каким заболеванием болеет. Что это за заболевания?")
    # Загруженные данные
    df_patients = data['patients']
    df_icd = data['icd']

    # 10-е задание: Сколько пробандов, каким заболеванием болеет
    st.title("10) Сколько пробандов, каким заболеванием болеет")

    # Отфильтруем только пробандов
    probands = df_patients.query("FamilyRelation == 'пробанд'")

    # Объединяем данные с таблицей ICD для получения полных названий заболеваний
    merged_df = probands.merge(df_icd, left_on='Diagnosis', right_on='ID', how='left')
    # Подсчёт количества пробандов по заболеваниям
    disease_counts = merged_df['Name_y'].value_counts().reset_index()
    disease_counts.columns = ['Заболевание', 'Количество пробандов']

    # Построение столбчатой диаграммы
    fig, ax = plt.subplots()
    sns.barplot(data=disease_counts, x='Заболевание', y='Количество пробандов', palette='pastel', ax=ax)
    ax.set_title("Количество пробандов с каждым заболеванием")
    ax.set_xlabel("Заболевание")
    ax.set_ylabel("Количество пробандов")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
    st.pyplot(fig)