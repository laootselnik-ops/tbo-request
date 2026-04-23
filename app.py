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
        df = pd.read_csv(DATABASE_URL)
        df = df.dropna(how='all')
        df['БИН/ИИН'] = df['БИН/ИИН'].ffill()
        df['Наименование'] = df['Наименование'].ffill()
        df['БИН/ИИН'] = df['БИН/ИИН'].astype(str).str.replace('.0', '', regex=False).str.strip()
        return df
    except Exception as e:
        st.error(f"Ошибка базы: {e}")
        return None

df = load_data()

st.title("🚛 Заявка на вывоз ТБО")
st.info("Инструкция: Введите БИН вашей компании, выберите нужные адреса из списка и укажите дату вывоза.")

if df is not None:
    # Поле БИН
    st.markdown("### 1. Идентификация")
    bin_input = st.text_input(
        "Введите БИН организации (12 цифр)", 
        placeholder="Например: 961140000659",
        help="БИН указан в вашем договоре на вывоз ТБО."
    )

    if bin_input:
        search_bin = bin_input.strip()
        client_data = df[df['БИН/ИИН'] == search_bin]

        if not client_data.empty:
            org_name = client_data['Наименование'].iloc[0]
            st.success(f"✅ Организация найдена: **{org_name}**")
            
            # Поле Адреса
            st.markdown("### 2. Выбор точек вывоза")
            all_addresses = client_data['Адрес'].unique().tolist()
            selected_addresses = st.multiselect(
                "Нажмите сюда и выберите адрес(а), откуда нужно забрать мусор:",
                options=all_addresses,
                default=[],  # УБРАН АВТОВЫБОР
                help="Можно выбрать сразу несколько адресов, если у вашей компании их много."
            )

            if not selected_addresses:
                st.warning("⚠️ Обязательно выберите хотя бы один адрес из списка выше, чтобы продолжить.")
            else:
                st.divider()
                
                # Поле Даты
                st.markdown("### 3. Дата и количество")
                tomorrow = datetime.now() + timedelta(days=1)
                order_date = st.date_input(
                    "На какой день планируем вывоз?", 
                    min_value=tomorrow,
                    help="Заявки принимаются минимум за день до фактического выезда. На 'сегодня' заказать нельзя."
                )
                
                container_data = {}
                for addr in selected_addresses:
                    contract = client_data[client_data['Адрес'] == addr]['№ и дата договора'].iloc[0]
                    st.write(f"---")
                    st.markdown(f"📍 **Точка:** {addr}")
                    st.caption(f"Договор: {contract}")
                    
                    container_data[addr] = st.number_input(
                        f"Сколько контейнеров забираем по этому адресу?", 
                        min_value=1, 
                        value=1, 
                        key=addr,
                        help="Укажите количество полных баков, которые нужно опорожнить."
                    )

                st.markdown("### 4. Дополнительно")
                comment = st.text_area(
                    "Комментарий для водителя (необязательно)", 
                    placeholder="Например: Номер телефона ответственного на месте или код от ворот.",
                    help="Любая информация, которая поможет водителю быстрее найти ваши контейнеры."
                )

                if st.button("ОТПРАВИТЬ ВСЕ ЗАЯВКИ"):
                    success_count = 0
                    with st.spinner('Связь с базой данных...'):
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
                        st.success(f"✅ Готово! Отправлено заявок: {success_count}. Ожидайте спецтехнику в указанный день.")
        else:
            st.error("❌ БИН не найден. Пожалуйста, убедитесь, что ввели 12 цифр правильно. Если всё верно, значит вашей компании нет в базе госзакупок.")

st.sidebar.markdown("### 💡 Памятка пользователю")
st.sidebar.write("""
1. Сначала БИН.
2. Потом Адрес (выберите из выпадающего списка).
3. Укажите дату (только на завтра и далее).
4. Нажмите синюю кнопку внизу.
""")
