import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# Настройки ссылок
DATABASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgFy7gYL5tdh_SOEmkhLpM0gEPWjJJmgmHXrsxRIzdSnIiSieeTvTBE0QvD5cxLVnt5BqKe5H-dGUN/pub?output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxLomEDTnfQT8l1SQ2QkDagfZ1oqz4L0JWiccR_HNKCHwbzaRjk-n2PxO36iX5bnVwl/exec"

st.set_page_config(page_title="Заявка ТБО (Multi)", page_icon="🚛")

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(DATABASE_URL)
        # Магия для объединенных ячеек: заполняем пустые БИНы значениями сверху
        df['БИН/ИИН'] = df['БИН/ИИН'].fillna(method='ffill')
        df['Наименование'] = df['Наименование'].fillna(method='ffill')
        
        df['БИН/ИИН'] = df['БИН/ИИН'].astype(str).str.replace('.0', '', regex=False).str.strip()
        return df
    except Exception as e:
        st.error(f"Ошибка базы: {e}")
        return None

df = load_data()

st.title("🚛 Заявка на вывоз ТБО")

if df is not None:
    bin_input = st.text_input("Введите БИН организации")

    if bin_input:
        client_data = df[df['БИН/ИИН'] == bin_input.strip()]

        if not client_data.empty:
            org_name = client_data['Наименование'].iloc[0]
            st.success(f"✅ Организация: {org_name}")
            
            # ВЫБОР НЕСКОЛЬКИХ АДРЕСОВ
            all_addresses = client_data['Адрес'].unique().tolist()
            selected_addresses = st.multiselect(
                "Выберите один или несколько адресов для вывоза:",
                options=all_addresses,
                default=[all_addresses[0]] # По умолчанию выбран первый
            )

            if selected_addresses:
                st.divider()
                
                # Общие параметры
                tomorrow = datetime.now() + timedelta(days=1)
                order_date = st.date_input("Дата вывоза", min_value=tomorrow)
                
                # Для каждого выбранного адреса можно указать кол-во контейнеров
                container_data = {}
                st.write("### Детали по каждой точке:")
                for addr in selected_addresses:
                    container_data[addr] = st.number_input(f"Контейнеров для: {addr}", min_value=1, value=1, key=addr)

                comment = st.text_area("Общий комментарий")

                if st.button("ОТПРАВИТЬ ВСЕ ЗАЯВКИ"):
                    success_count = 0
                    for addr in selected_addresses:
                        payload = {
                            "Дата подачи": datetime.now().strftime("%d.%m.%Y %H:%M"),
                            "БИН": bin_input,
                            "Компания": org_name,
                            "Адрес": addr,
                            "Желаемая дата": order_date.strftime("%d.%m.%Y"),
                            "Кол-во": str(container_data[addr]),
                            "Комментарий": comment
                        }
                        
                        try:
                            res = requests.post(SCRIPT_URL, json=payload, timeout=10)
                            if res.status_code == 200:
                                success_count += 1
                        except:
                            st.error(f"Ошибка при отправке на адрес: {addr}")

                    if success_count == len(selected_addresses):
                        st.balloons()
                        st.success(f"✅ Успешно отправлено заявок: {success_count}")
            else:
                st.warning("Выберите хотя бы один адрес.")
        else:
            st.error("БИН не найден.")
