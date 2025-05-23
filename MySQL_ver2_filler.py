import math
import pandas as pd
import pymysql
import re

def create_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='10082005',
            database='sys',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Ошибка подключения к MySQL: {e}")
        return None

def to_bool(val):
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val):
            return None
        return val == 1.0
    if isinstance(val, int):
        return val == 1
    val_str = str(val).strip().lower()
    if val_str in ("true", "1", "yes", "да"):
        return True
    if val_str in ("false", "0", "no", "нет"):
        return False
    return None

def to_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

def to_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def extract_model(run_id):
    if not run_id:
        return None
    match = re.search(r'-(\w+)$', run_id)
    return match.group(1) if match else None

ICD_DICTIONARY = {
    'Q85.0': 'Нейрофиброматоз I типа',
    'E70.0': 'Фенилкетонурия',
    'E84.0': 'Кистозный фиброз с легочными проявлениями',
    'G11.3': 'Мозжечковая атаксия с нарушением репарации ДНК',
    'Q87.2': 'Синдромы врождённых аномалий конечностей',
    'Q87.3': 'Синдромы избыточного роста на ранних этапах'
}

def fill_reference_tables(connection, df):
    cursor = connection.cursor()
    try:
        genders = [(1, 'XY', 'Мужской'), (2, 'XX', 'Женский')]
        for gender_id, name, synonim in genders:
            cursor.execute("INSERT IGNORE INTO Gender (ID, Name, Synonims) VALUES (%s, %s, %s)", (gender_id, name, synonim))

        if 'Тип секвенирования' in df.columns:
            for i, seq_type in enumerate(df['Тип секвенирования'].dropna().unique(), 1):
                cursor.execute("INSERT IGNORE INTO SequencingType (UniqueID, Name) VALUES (%s, %s)", (i, seq_type))

        if 'Проект' in df.columns:
            projects = df[['Проект', 'Партнер']].drop_duplicates()
            for i, row in projects.iterrows():
                if row['Проект']:
                    cursor.execute("INSERT IGNORE INTO Projects (ID, Name, Partner) VALUES (%s, %s, %s)", (i + 1, row['Проект'], row.get('Партнер')))

        if 'Предполагаемый диагноз' in df.columns:
            for diagnosis in df['Предполагаемый диагноз'].dropna().unique():
                name = ICD_DICTIONARY.get(diagnosis, diagnosis)
                cursor.execute("INSERT IGNORE INTO ICD (ID, Name) VALUES (%s, %s)", (diagnosis, name))

        connection.commit()
    except pymysql.MySQLError as e:
        print(f"Ошибка при заполнении справочных таблиц: {e}")
        connection.rollback()
    finally:
        cursor.close()

def fill_main_tables(connection, df):
    cursor = connection.cursor()
    patient_ids = {}

    try:
        # === Families ===
        if 'Семья' in df.columns and 'Близкородственный брак' in df.columns:
            df['Близкородственный брак'] = df['Близкородственный брак'].apply(to_bool)
            df_clean = df.dropna(subset=['Близкородственный брак'])
            family_data = df_clean.groupby('Семья')['Близкородственный брак'].first().reset_index()
            for _, row in family_data.iterrows():
                family_id = to_int(row['Семья'])
                inbreeding = row['Близкородственный брак']
                if family_id is not None:
                    cursor.execute("INSERT IGNORE INTO Families (ID, Inbreeding) VALUES (%s, %s)", (family_id, inbreeding))

        # === Runs ===
        for _, row in df.iterrows():
            run_name = row.get('Номер запуска')
            if run_name:
                model = extract_model(run_name)
                cursor.execute("SELECT 1 FROM Runs WHERE Name = %s", (run_name,))
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT IGNORE INTO Runs (Name, SequencingData, Plan, Model) VALUES (%s, %s, %s, %s)",
                        (run_name, row.get('Дата секвенирования'), None, model)
                    )

        # === Patients ===
        if all(col in df.columns for col in ['Фамилия', 'Имя', 'Пол']):
            for _, row in df.iterrows():
                surname = row['Фамилия']
                name = row['Имя']
                if not surname or not name:
                    continue
                patronymic = row.get('Отчество')
                gender_code = str(row.get('Пол')).upper()[:2]
                cursor.execute("SELECT ID FROM Gender WHERE Name = %s", (gender_code,))
                gender_result = cursor.fetchone()
                gender_id = gender_result["ID"] if gender_result else None
                family_id = to_int(row.get('Семья'))

                cursor.execute(
                    """INSERT INTO Patients 
                       (Surname, Name, SecondName, Sex, Phenotype, FamilyID, FamilyRelation, 
                        Birthday, Diagnosis, MedCardNumber) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        surname, name, patronymic, gender_id,
                        row.get('Фенотип'), family_id,
                        row.get('Степень родства'), row.get('Дата рождения'),
                        row.get('Предполагаемый диагноз'), row.get('Номер карты')
                    )
                )

                # Сохраняем ID по УИН1
                uin1 = to_int(row.get('УИН1'))
                if uin1:
                    # Получаем ID пациента по имени и фамилии только что вставленного
                    cursor.execute("SELECT PatientID FROM Patients WHERE Surname=%s AND Name=%s ORDER BY PatientID DESC LIMIT 1", (surname, name))
                    result = cursor.fetchone()
                    if result:
                        patient_ids[uin1] = result["PatientID"]

        # === Samples ===
        for _, row in df.iterrows():
            uin1 = to_int(row.get('УИН1'))
            if uin1:
                patient_id = patient_ids.get(uin1)
                project_id = None
                if row.get('Проект'):
                    cursor.execute("""
                        SELECT ID 
                        FROM Projects 
                        WHERE Name = %s AND Partner = %s
                    """, (row.get('Проект'), row.get('Партнер')))
                    result = cursor.fetchone()
                    project_id = result["ID"] if result else None

                cursor.execute(
                    """INSERT IGNORE INTO Samples 
                       (UIN1, UIN2, Patient, Project, Run, Deadline, AcquiringDate) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        uin1,
                        row.get('УИН2'),
                        patient_id,
                        project_id,
                        row.get('Номер запуска'),
                        row.get('Дедлайн'),
                        row.get('Дата поступления')
                    )
                )

        # === Plans + обновление Runs.Plan ===
        for _, row in df.iterrows():
            uin1 = to_int(row.get('УИН1'))
            if uin1 and row.get('Тип секвенирования'):
                cursor.execute("SELECT UniqueID FROM SequencingType WHERE Name = %s", (row['Тип секвенирования'],))
                result = cursor.fetchone()
                sequencing_id = result["UniqueID"] if result else None
                cursor.execute(
                    "INSERT IGNORE INTO Plans (UniquelID, Sample, SequencingType) VALUES (%s, %s, %s)",
                    (uin1, uin1, sequencing_id)
                )
                run_name = row.get('Номер запуска')
                if run_name:
                    cursor.execute("UPDATE Runs SET Plan = %s WHERE Name = %s", (uin1, run_name))

        # === Analysis ===
        for _, row in df.iterrows():
            uin1 = to_int(row.get('УИН1'))
            if uin1 and row.get('Дата анализа'):
                cursor.execute("SELECT 1 FROM Plans WHERE UniquelID = %s", (uin1,))
                if cursor.fetchone():
                    cursor.execute(
                        """INSERT IGNORE INTO Analysis
                           (ID, Plan, AnalysisDate, Filepath, Pipeline, Reference,
                            ResultGiven, Coverage, MeanDepth, NumberReads, Uniformity)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            uin1, uin1,
                            row.get('Дата анализа'),
                            row.get('Путь к файлам'),
                            row.get('Пайплайн анализа'),
                            row.get('Референсный геном'),
                            to_bool(row.get('Выданы результаты партнерам')),
                            to_float(row.get('Покрытие')),
                            to_float(row.get('Средняя глубина покрытия')),
                            to_int(row.get('Количество прочтений')),
                            to_float(row.get('Униформность'))
                        )
                    )

        connection.commit()
    except pymysql.MySQLError as e:
        print(f"Ошибка при заполнении таблиц: {e}")
        connection.rollback()
    finally:
        cursor.close()

if __name__ == "__main__":
    connection = create_connection()
    if connection is None:
        print("❌ Ошибка подключения к БД")
        exit(1)

    df = pd.read_csv('/home/alor/VisualStudioCode/pythoncode/SQL_LAB/MySQLData.csv', encoding='utf-8')
    df = df.where(pd.notnull(df), None)

    try:
        fill_reference_tables(connection, df)
        fill_main_tables(connection, df)
        print("✅ Данные успешно загружены в базу данных.")
    except pymysql.MySQLError as e:
        print(f"❌ Ошибка при загрузке данных: {e}")
        connection.rollback()
    finally:
        connection.close()
