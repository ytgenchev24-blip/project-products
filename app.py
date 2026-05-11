import easyocr
import streamlit as st
if uploaded_file is not None:

    try:
        image = Image.open(uploaded_file).convert("RGB")

        st.image(image, caption="Качено изображение", use_container_width=True)

        img_array = np.array(image)

        with st.spinner("Разпознаване на текст от изображението..."):
            results = reader.readtext(img_array, detail=0)

        extracted_text = " ".join(results)
        extracted_text_lower = extracted_text.lower()

        # Clean OCR text
        extracted_text_lower = re.sub(r'[^a-zA-Zа-яА-Я0-9 ]', ' ', extracted_text_lower)
        extracted_text_lower = re.sub(r'\s+', ' ', extracted_text_lower)

        st.subheader("📄 Разпознат текст")
        st.text_area(
            "Разпознати съставки",
            extracted_text,
            height=220
        )

        # ---------------------------------------------------
        # ТЪРСЕНЕ НА ВРЕДНИ СЪСТАВКИ
        # ---------------------------------------------------

        found_ingredients = []

        for ingredient, description in harmful_ingredients.items():

            # Проверка за E-номера
            if ingredient.startswith("e"):

                pattern = rf'{re.escape(ingredient)}'

                if re.search(pattern, extracted_text_lower):
                    found_ingredients.append((ingredient.upper(), description))

            # Проверка за текстови съставки
            else:

                if ingredient in extracted_text_lower:
                    found_ingredients.append((ingredient, description))

        # Премахване на дублиращи се резултати
        unique_found = list(set(found_ingredients))

        # ---------------------------------------------------
        # RESULTS
        # ---------------------------------------------------

        st.subheader("⚠️ Открити съставки")

        if unique_found:

            for ingredient, description in unique_found:
                st.warning(f"{ingredient} → {description}")

        else:
            st.success("Не са открити известни вредни съставки.")

    except Exception as e:
        st.error(f"Грешка при обработка на изображението: {e}")

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------

st.markdown("---")
st.caption("Това приложение е само с образователна цел.")
