import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
# Твоя база данных (опубликована как CSV)
DATABASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgFy7gYL5tdh_SOEmkhLpM0gEPWjJJmgmHXrsxRIzdSnIiSieeTvTBE0QvD5cxLVnt5BqKe5H-dGUN/pub?output=csv"

# Твой Apps Script для приема заявок
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxLomEDTnfQT8l1SQ2QkDagfZ1oqz4L0JWiccR_HNKCHwbzaRjk-n2PxO36iX5bnVwl/exec"

st.set_page_config(page_title="Заявка на вывоз ТБО", page_icon="🚛", layout="centered")

# Кастомные стили для красоты
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚛 Заявка на вывоз ТБО")
st.write("Введите БИН организации для автоматического заполнения данных.")

# Загрузка данных из Google Таблицы
@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(DATABASE_URL)
        # Приводим БИН к строке и убираем лишнее
        df['БИН/ИИН'] = df['БИН/ИИН'].astype(str).str.replace('.0', '', regex=False).str.strip()
        return df
    except Exception as e:
        st.error(f"Ошибка подключения к базе: {e}")
        return None

df = load_data()

if df is not None:
    # Ввод БИН
    bin_input = st.text_input("БИН/ИИН организации", placeholder="Например: 961140000659")

    if bin_input:
        # Фильтруем базу
        client_data = df[df['БИН/ИИН'] == bin_input.strip()]

        if not client_data.empty:
            # Отображаем название компании
            org_name = client_data['Наименование'].iloc[0]
            st.success(f"✅ **Организация:** {org_name}")
            
            # Выбор адреса
            addresses = client_data['Адрес'].unique()
            selected_address = st.selectbox("Выберите адрес точки вывоза", addresses)
            
            # Инфо о договоре
            contract_info = client_data[client_data['Адрес'] == selected_address]['№ и дата договора'].iloc[0]
            st.info(f"Договор: {contract_info}")

            st.divider()
            
            # Поля для новой заявки
            col1, col2 = st.columns(2)
            with col1:
                tomorrow = datetime.now() + timedelta(days=1)
                order_date = st.date_input("Дата вывоза (минимум завтра)", min_value=tomorrow)
            with col2:
                container_count = st.number_input("Кол-во контейнеров", min_value=1, value=1, step=1)

            comment = st.text_area("Комментарий к заявке", placeholder="Например: код от шлагбаума или номер телефона на месте")

            if st.button("ОТПРАВИТЬ ЗАЯВКУ"):
                # Формируем данные
                payload = {
                    "Дата подачи": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "БИН": bin_input,
                    "Компания": org_name,
                    "Адрес": selected_address,
                    "Желаемая дата": order_date.strftime("%d.%m.%Y"),
                    "Кол-во": str(container_count),
                    "Комментарий": comment
                }
                
                with st.spinner('Отправка заявки...'):
                    try:
                        # Отправляем POST запрос в Google Apps Script
                        response = requests.post(SCRIPT_URL, json=payload, timeout=10)
                        
                        if response.status_code == 200:
                            st.balloons()
                            st.success("✅ Заявка успешно принята! Менеджер увидит её в системе.")
                        else:
                            st.error(f"Ошибка сервера (код {response.status_code}). Попробуйте позже.")
                    except Exception as e:
                        st.error(f"Ошибка при отправке: {e}")
        else:
            st.warning("⚠️ Организация с таким БИН не найдена в базе госконтрактов.")

st.sidebar.markdown("---")
st.sidebar.write("📍 **Техподдержка:**")
st.sidebar.write("При возникновении проблем с формой обратитесь в отдел автоматизации.")
