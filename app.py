import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
DATABASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgFy7gYL5tdh_SOEmkhLpM0gEPWjJJmgmHXrsxRIzdSnIiSieeTvTBE0QvD5cxLVnt5BqKe5H-dGUN/pub?output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxLomEDTnfQT8l1SQ2QkDagfZ1oqz4L0JWiccR_HNKCHwbzaRjk-n2PxO36iX5bnVwl/exec"

st.set_page_config(page_title="Заявка ТБО", page_icon="🚛")

@st.cache_data(ttl=600)
def load_data():
    try:
        # Читаем таблицу
        df = pd.read_csv(DATABASE_URL)
        
        # 1. Удаляем полностью пустые строки, если они есть (например, в начале таблицы)
        df = df.dropna(how='all')
        
        # 2. Исправленная магия для объединенных ячеек (НОВЫЙ СИНТАКСИС)
        df['БИН/ИИН'] = df['БИН/ИИН'].ffill()
        df['Наименование'] = df['Наименование'].ffill()
        
        # 3. Очистка БИН
        df['БИН/ИИН'] = df['БИН/ИИН'].astype(str).str.replace('.0', '', regex=False).str.strip()
        return df
    except Exception as e:
        st.error(f"Ошибка базы: {e}")
        return None

df = load_data()

st.title("🚛 Заявка на вывоз ТБО")

if df is not None:
    bin_input = st.text_input("Введите БИН организации", placeholder="12 цифр")

    if bin_input:
        # Поиск по БИН
        search_bin = bin_input.strip()
        client_data = df[df['БИН/ИИН'] == search_bin]

        if not client_data.empty:
            org_name = client_data['Наименование'].iloc[0]
            st.success(f"✅ Организация: **{org_name}**")
            
            # Выбор адресов (мультивыбор)
            all_addresses = client_data['Адрес'].unique().tolist()
            selected_addresses = st.multiselect(
                "Выберите адрес(а) для вывоза:",
                options=all_addresses,
                default=[all_addresses[0]]
            )

            if selected_addresses:
                st.divider()
                
                # Общие параметры даты
                tomorrow = datetime.now() + timedelta(days=1)
                order_date = st.date_input("Дата вывоза (минимум завтра)", min_value=tomorrow)
                
                # Параметры по каждой точке
                container_data = {}
                st.write("### Детали по каждой точке:")
                for addr in selected_addresses:
                    # Ищем № договора для конкретного адреса
                    contract = client_data[client_data['Адрес'] == addr]['№ и дата договора'].iloc[0]
                    st.caption(f"📍 {addr} (Договор: {contract})")
                    container_data[addr] = st.number_input(f"Кол-во контейнеров", min_value=1, value=1, key=addr)

                comment = st.text_area("Дополнительный комментарий к заявке")

                if st.button("ОТПРАВИТЬ ВСЕ ЗАЯВКИ"):
                    success_count = 0
                    with st.spinner('Отправка данных...'):
                        for addr in selected_addresses:
                            payload = {
                                "Дата подачи": datetime.now().strftime("%d.%m.%Y %H:%M"),
                                "БИН": search_bin,
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
                                st.error(f"Не удалось отправить заявку для адреса: {addr}")

                    if success_count == len(selected_addresses):
                        st.balloons()
                        st.success(f"✅ Успешно отправлено заявок: {success_count}")
            else:
                st.warning("Пожалуйста, выберите хотя бы один адрес.")
        else:
            st.error("БИН не найден в базе. Проверьте правильность ввода.")

st.sidebar.markdown("---")
st.sidebar.caption("Приложение для автоматизации заявок на вывоз ТБО")
