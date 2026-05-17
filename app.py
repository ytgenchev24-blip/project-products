import streamlit as st
import cv2
import numpy as np
import easyocr
import re

# 1. База данни с Е-номера
E_NUMBERS = {
    "E102": {"name": "Тартразин", "status": "вреден", "reason": "Алерген, може да причини хиперактивност при деца."},
    "E122": {"name": "Азорубин", "status": "вреден", "reason": "Забранен в някои страни, съмнения за канцерогенност."},
    "E211": {"name": "Натриев бензоат", "status": "вреден", "reason": "Консервант. В комбинация с Витамин Ц образува бензен (канцероген)."},
    "E250": {"name": "Натриев нитрит", "status": "вреден", "reason": "Използва се в колбаси. Може да образува нитрозамини."},
    "E621": {"name": "Мононатриев глутамат", "status": "вреден", "reason": "Повреди на вкусовите рецептори, главоболие."},
    "E950": {"name": "Ацесулфам К", "status": "вреден", "reason": "Изкуствен подсладител. Натоварва черния дроб."},
    "E951": {"name": "Аспартам", "status": "вреден", "reason": "Изкуствен подсладител. Свързва се с главоболие и неврологични проблеми."},
    "E952": {"name": "Цикламат", "status": "вреден", "reason": "Изкуствен подсладител, забранен в САЩ поради риск за здравето."},
    "E100": {"name": "Куркумин", "status": "полезен", "reason": "Естествени противовъзпалителни свойства."},
    "E160a": {"name": "Каротини", "status": "полезен", "reason": "Провитамин А. Мощен антиоксидант."},
    "E300": {"name": "Аскорбинова киселина", "status": "полезен", "reason": "Чист Витамин Ц. Антиоксидант."},
    "E322": {"name": "Лецитин", "status": "полезен", "reason": "Полезен за мозъка и черния дроб."},
    "E440": {"name": "Пектин", "status": "полезен", "reason": "Естествени фибри. Помага на храносмилането."}
}

# 2. РАЗШИРЕНА база данни за съставки (BG и EN)
INGREDIENTS = {
    # --- ВРЕДНИ СЪСТАВКИ ---
    "ЗАХАР": {"status": "вреден", "reason": "Високо съдържание на рафинирана захар. Риск от диабет и затлъстяване.", "match": ["ЗАХАР", "SUGAR"]},
    "ПАЛМОВО МАСЛО": {"status": "вреден", "reason": "Наситени мазнини. Повишават лошия холестерол и риска от инфаркт.", "match": ["ПАЛМОВО", "PALM OIL", "PALM FAT"]},
    "ГЛЮКОЗО-ФРУКТОЗЕН СИРОП": {"status": "вреден", "reason": "Евтин и опасен подсладител. Натоварва черния дроб директно.", "match": ["ГЛЮКОЗО", "ФРУКТОЗЕН", "FRUCTOSE SYRUP", "GLUCOSE-FRUCTOSE"]},
    "МАРГАРИН / ХИДРОГЕНИРАНИ МАЗНИНИ": {"status": "вреден", "reason": "Трансмазнини, които причиняват тежки възпаления в съдовете.", "match": ["МАРГАРИН", "MARGARINE", "ХИДРОГЕНИРАНИ", "HYDROGENATED"]},
    "ИНСТАНТНО КАФЕ НА ПРАХ (3в1)": {"status": "вреден", "reason": "Пълно с химикали, палмова мазнина и захар вместо истинско кафе.", "match": ["ЗАБЕЛИТЕЛ", "CREAMER"]},
    "НИТРИТНА СОЛ": {"status": "вреден", "reason": "Токсичен химикал, използван за запазване на червения цвят в месото.", "match": ["НИТРИТНА", "NITRITE"]},
    "КАРАГЕНАН": {"status": "вреден", "reason": "Сгъстител, който често причинява язви и сериозни стомашни проблеми.", "match": ["КАРАГЕНАН", "CARRAGEENAN"]},

    # --- СЪСТАВКИ С ВНИМАНИЕ (УМЕРЕНО) ---
    "СОЛ": {"status": "внимание", "reason": "Високи количества сол водят до хипертония и задържане на вода.", "match": ["СОЛ", "SALT"]},
    "ГЛУТЕН": {"status": "внимание", "reason": "Силен алерген. Проблемен за хора с непоносимост или цолиакия.", "match": ["ГЛУТЕН", "GLUTEN"]},
    "ПШЕНИЧНО БРАШНО бяло": {"status": "внимание", "reason": "Бърз въглехидрат с висок гликемичен индекс. Бързо огладняване.", "match": ["ПШЕНИЧНО БРАШНО", "WHEAT FLOUR"]},
    "СОЕВ ПРОТЕИН / СОЯ": {"status": "внимание", "reason": "Често е ГМО продукт и може да повлияе на хормоналния баланс.", "match": ["СОЯ", "СОЕВ", "SOY", "SOYA"]},
    "СУРОВАТКА / ЛАКТОЗА": {"status": "внимание", "reason": "Млечна захар. Чест причинител на подуване и газове.", "match": ["СУРОВАТКА", "ЛАКТОЗА", "WHEY", "LACTOSE"]},

    # --- ПОЛЕЗНИ СЪСТАВКИ ---
    "ОДЕСНИ ЯДКИ": {"status": "полезен", "reason": "Сложни въглехидрати и бета-глюкани за здрава сърдечна система.", "match": ["ОВЕС", "OAT", "OATS"]},
    "ПЪЛНОЗЪРНЕСТО БРАШНО": {"status": "полезен", "reason": "Богато на естествени фибри, магнезий и витамини от група B.", "match": ["ПЪЛНОЗЪРНЕСТО", "WHOLE GRAIN", "WHOLEWHEAT"]},
    "ЗЕХТИН (Extra Virgin)": {"status": "полезен", "reason": "Здравословни мазнини (олеинова киселина), чистят съдовете.", "match": ["ЗЕХТИН", "OLIVE OIL"]},
    "МЕД": {"status": "полезен", "reason": "Натурален антибиотик и антиоксидант. По-добра алтернатива на захарта.", "match": ["МЕД", "HONEY"]},
    "ЧИЯ": {"status": "полезен", "reason": "Растителен източник №1 на Омега-3 мастни киселини.", "match": ["ЧИЯ", "CHIA"]},
    "ЛЕНЕНО СЕМЕ": {"status": "полезен", "reason": "Подобрява перисталтиката и балансира хормоните.", "match": ["ЛЕНЕНО", "FLAXSEED"]},
    "БАДЕМ / ОРЕХ / ЛЕШНИК": {"status": "полезен", "reason": "Полезни ядки, богати на мазнини за мозъка и витамин Е.", "match": ["БАДЕМ", "ОРЕХ", "ЛЕШНИК", "ALMOND", "WALNUT", "HAZELNUT"]},
    "КАКАО": {"status": "полезен", "reason": "Натуралното какао подобрява настроението и е пълно с антиоксиданти.", "match": ["КАКАО", "COCOA", "CACAO"]},
    "ПРОБИОТИК / ЗАКВАСКА": {"status": "полезен", "reason": "Живи бактерии, които подсилват имунитета и стомашната флора.", "match": ["ЗАКВАСКА", "CULTURE", "PROBIOTIC"]}
}

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['bg', 'en'])

reader = load_ocr()

st.title("🍎 Макси Скенер за Храни & Съставки")
st.write("Качете снимка на етикета. Приложението сканира за десетки вредни и полезни съставки.")

uploaded_file = st.file_uploader("Изберете снимка на етикет...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)
    
    st.image(image, channels="BGR", caption="Качена снимка", use_container_width=True)
    
    with st.spinner("Четене и дълбок анализ на текста..."):
        results = reader.readtext(image, detail=0)
        full_text = " ".join(results).upper()
        
    st.subheader("📝 Разпознат текст:")
    st.write(full_text)
    
    has_harmful = False
    has_warning = False
    has_healthy = False
    
    st.subheader("🔍 Подробен анализ на състава:")
    
    # --- ЧАСТ 1: Е-номера ---
    found_codes = re.findall(r'E\s*\d{3}[A-Z]?', full_text)
    cleaned_codes = list(set([code.replace(" ", "") for code in found_codes]))
    
    if cleaned_codes:
        st.write(f"**Открити Е-номера:** {', '.join(cleaned_codes)}")
        for code in cleaned_codes:
            if code in E_NUMBERS:
                info = E_NUMBERS[code]
                if info["status"] == "вреден":
                    st.error(f"🚨 **{code} ({info['name']})** - ВРЕДЕН: {info['reason']}")
                    has_harmful = True
                else:
                    st.success(f"✅ **{code} ({info['name']})** - ПОЛЕЗЕН: {info['reason']}")
                    has_healthy = True
            else:
                st.warning(f"⚠️ **{code}** - Намерено Е-число, което липсва в базата данни.")

    # --- ЧАСТ 2: Съставки ---
    found_ingredients = False
    for ing_name, details in INGREDIENTS.items():
        if any(keyword in full_text for keyword in details["match"]):
            found_ingredients = True
            if details["status"] == "вреден":
                st.error(f"🚨 **{ing_name}** - ВРЕДНА СЪСТАВКА: {details['reason']}")
                has_harmful = True
            elif details["status"] == "внимание":
                st.warning(f"⚠️ **{ing_name}** - Консумирай с ВНИМАНИЕ: {details['reason']}")
                has_warning = True
            else:
                st.success(f"✅ **{ing_name}** - ПОЛЕЗНА СЪСТАВКА: {details['reason']}")
                has_healthy = True
                
    if not cleaned_codes and not found_ingredients:
        st.info("Текстът не съдържа познати Е-номера или специфични съставки от базата данни.")

    # --- ЧАСТ 3: Крайна комплексна оценка ---
    st.subheader("📊 Генерално заключение:")
    if has_harmful:
        st.error("❌ **Продуктът е ВРЕДЕН!** Съдържа съставки, криещи риск за здравето при честа употреба.")
    elif has_warning and not has_healthy:
        st.warning("⚠️ **Внимавайте с количеството.** Продуктът съдържа предимно рафинирани съставки или потенциални алергени.")
    elif has_healthy and not has_warning:
        st.success("🍏 **Продуктът е МНОГО ПОЛЕЗЕН!** Съдържа чисти суперхрани и полезни суровини.")
