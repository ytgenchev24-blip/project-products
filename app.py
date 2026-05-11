import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import re

# -----------------------------------
# PAGE
# -----------------------------------

st.set_page_config(
    page_title="Скенер за храни",
    page_icon="🍔"
)

st.title("🍔 Скенер за вредни съставки")

st.write(
    "Качи снимка на етикет и приложението ще открие вредни съставки."
)

# -----------------------------------
# OCR
# -----------------------------------

@st.cache_resource
def load_reader():
    return easyocr.Reader(['bg', 'en'], gpu=False)

reader = load_reader()

# -----------------------------------
# ВРЕДНИ СЪСТАВКИ
# -----------------------------------

harmful_ingredients = {

    "e102": "Тартразин",
    "e110": "Sunset Yellow",
    "e122": "Азорубин",
    "e124": "Понсо 4R",
    "e129": "Allura Red",
    "e171": "Титанов диоксид",
    "e211": "Натриев бензоат",
    "e220": "Серен диоксид",
    "e249": "Калиев нитрит",
    "e250": "Натриев нитрит",
    "e251": "Натриев нитрат",
    "e252": "Калиев нитрат",
    "e320": "BHA",
    "e321": "BHT",
    "e407": "Карагенан",
    "e433": "Полисорбат 80",
    "e450": "Дифосфати",
    "e451": "Трифосфати",
    "e621": "MSG",
    "e627": "Динатриев гуанилат",
    "e631": "Динатриев инозинат",
    "e950": "Ацесулфам K",
    "e951": "Аспартам",
    "e952": "Цикламат",
    "e954": "Захарин",
    "e955": "Сукралоза",

    "палмово масло": "Палмово масло",
    "palm oil": "Палмово масло",

    "hydrogenated oil": "Хидрогенирано масло",

    "trans fat": "Транс мазнини",

    "high fructose corn syrup": "Глюкозо-фруктозен сироп",

    "msg": "Мононатриев глутамат",

    "artificial flavor": "Изкуствени аромати",

    "preservatives": "Консерванти"
}

# -----------------------------------
# UPLOAD
# -----------------------------------

uploaded_file = st.file_uploader(
    "Качи снимка",
    type=["jpg", "jpeg", "png"]
)

# -----------------------------------
# OCR PROCESS
# -----------------------------------

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    st.image(image, use_container_width=True)

    img_array = np.array(image)

    with st.spinner("Сканиране..."):

        results = reader.readtext(
            img_array,
            detail=0
        )

    extracted_text = " ".join(results)

    extracted_text = extracted_text.lower()

    extracted_text = re.sub(
        r'[^a-zA-Zа-яА-Я0-9 ]',
        ' ',
        extracted_text
    )

    st.subheader("📄 Разпознат текст")

    st.text_area(
        "",
        extracted_text,
        height=220
    )

    found = []

    for ingredient, description in harmful_ingredients.items():

        pattern = rf'\\b{re.escape(ingredient)}\\b'

        if re.search(pattern, extracted_text):

            found.append(
                (ingredient.upper(), description)
            )

    found = list(set(found))

    st.subheader("⚠️ Открити съставки")

    if found:

        for ingredient, description in found:

            st.warning(
                f"{ingredient} → {description}"
            )

    else:

        st.success(
            "Не са открити опасни съставки."
        )
