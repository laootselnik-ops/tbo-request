import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Ссылка на твою опубликованную таблицу (формат CSV для прямого чтения)
DATABASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgFy7gYL5tdh_SOEmkhLpM0gEPWjJJmgmHXrsxRIzdSnIiSieeTvTBE0QvD5cxLVnt5BqKe5H-dGUN/pub?output=csv"

st.set_page_config(page_title="Заявка на вывоз ТБО", page_icon="🚛")

st.title("🚛 Форма заявки на вывоз ТБО")
st.write("Введите БИН вашей организации, чтобы подтянуть данные из договора.")

# Загрузка базы данных
@st.cache_data(ttl=600)
def load_data():
    try:
        # Читаем CSV напрямую из Google Sheets
        df = pd.read_csv(DATABASE_URL)
        # Очищаем БИН от лишних пробелов, если они есть
        df['БИН/ИИН'] = df['БИН/ИИН'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки базы: {e}")
        return None

df = load_data()

if df is not None:
    # Поле ввода БИН
    bin_input = st.text_input("БИН организации (12 цифр)", placeholder="Например: 961140000659")

    if bin_input:
        # Фильтруем данные по введенному БИНу
        client_data = df[df['БИН/ИИН'] == bin_input.strip()]

        if not client_data.empty:
            # 1. Проверка наименования
            org_name = client_data['Наименование'].iloc[0]
            st.success(f"✅ Организация: **{org_name}**")
            
            # 2. Выбор адреса (если их несколько на одном БИН)
            addresses = client_data['Адрес'].unique()
            selected_address = st.selectbox("Выберите адрес вывоза", addresses)
            
            # Показываем номер договора для уверенности
            contract = client_data[client_data['Адрес'] == selected_address]['№ и дата договора'].iloc[0]
            st.caption(f"Договор: {contract}")

            st.divider()

            # 3. Детали заявки
            col1, col2 = st.columns(2)
            
            with col1:
                # Ограничение даты: только со следующего дня
                tomorrow = datetime.now() + timedelta(days=1)
                order_date = st.date_input("Дата вывоза", min_value=tomorrow)
            
            with col2:
                container_count = st.number_input("Кол-во контейнеров", min_value=1, value=1)

            comment = st.text_area("Дополнительный комментарий (необязательно)")

            # 4. Кнопка отправки
            if st.button("Отправить заявку в работу"):
                # Формируем объект заявки
                order_payload = {
                    "Дата подачи": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "БИН": bin_input,
                    "Компания": org_name,
                    "Адрес": selected_address,
                    "Желаемая дата": order_date.strftime("%d.%m.%Y"),
                    "Кол-во": container_count,
                    "Комментарий": comment
                }
                
                # Здесь будет код для записи в "приемную" таблицу
                st.balloons()
                st.success("Спасибо! Ваша заявка принята.")
                st.info("Данные заявки:")
                st.json(order_payload)
        else:
            st.error("БИН не найден в базе. Пожалуйста, проверьте правильность ввода или свяжитесь с менеджером.")

st.sidebar.info("Система автоматизации вывоза ТБО. Выбор даты возможен только на следующий день и позже.")
