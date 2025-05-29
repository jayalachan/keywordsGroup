import streamlit as st
import pandas as pd
import re
from io import BytesIO

# -------------------------------
# CARGAR LISTA DE CIUDADES DESDE CSV
# -------------------------------

@st.cache_resource
def load_cities():
    try:
        cities_df = pd.read_csv("all cities.csv")
        city_set = set(cities_df.iloc[:, 0].str.lower().str.strip())
        return city_set
    except Exception as e:
        st.error(f"Error loading city data: {e}")
        return set()

KNOWN_CITIES = load_cities()

# -------------------------------
# PREPROCESAMIENTO Y REGLAS DE CLASIFICACIÓN
# -------------------------------

# Lista de países conocidos
KNOWN_COUNTRIES = {
    "afghanistan", "albania", "algeria", "argentina", "australia", "austria", "bahamas", "bahrain",
    "bangladesh", "barbados", "belgium", "belize", "brazil", "canada", "chile", "china", "colombia", "costa rica",
    "cuba", "denmark", "dominican republic", "ecuador", "egypt", "el salvador", "finland", "france", "germany",
    "greece", "guatemala", "honduras", "iceland", "india", "indonesia", "ireland", "israel", "italy", "jamaica",
    "japan", "jordan", "kenya", "kuwait", "korea", "north korea", "south korea", "lebanon", "malaysia", "mexico", 
    "morocco", "netherlands", "new zealand","nicaragua", "nigeria", "norway", "panama", "peru", "philippines", 
    "portugal", "qatar", "russia","saudi arabia", "singapore", "south africa", "south korea", "spain", "sweden", 
    "switzerland", "thailand","turkey", "ukraine", "united arab emirates", "united kingdom", "united states", "uruguay", 
    "venezuela","vietnam", "zambia", "zimbabwe", "usa", "us", "america","AF", "AL", "DZ", "AR", "AU", "AT", "BS", "BH", "BD", 
    "BB", "BE", "BZ", "BR", "CA", "CL", "CN", "CO", "CR","CU", "DK", "DO", "EC", "EG", "SV", "FI", "FR", "DE", "GR", 
    "GT", "HN", "IS", "IN", "ID", "IE", "IL", "IT","JM", "JP", "JO", "KE", "KW", "LB", "MY", "MX", "MA", "NL", "NZ", 
    "NI", "NG", "NO", "PA", "PE", "PH", "PT","QA", "RU", "SA", "SG", "ZA", "KR", "ES", "SE", "CH", "TH", "TR", "UA", 
    "AE", "GB", "US", "UY", "VE", "VN","ZM", "ZW", "turks", "caicos", "trinidad and tobago", "sri lanka", "havana", 
    "salvador", "poland"
}

# Lista de marcas
BRANDED_KEYWORDS = {kw.lower() for kw in [
    "AM Resorts", "ANA", "Aegean", "Aer Lingus", "Aeroitalia", "Aeromexico", "Afriqiyah Airways",
    "Air Albania", "Air Arabia", "Air Astana", "Air Austral", "Air Canada", "Air Caraïbes",
    "Air Côte d'Ivoire", "Air Europa", "Air France", "Air India Express", "Air Moana", "Air Montenegro",
    "Air New Zealand", "Air Niugini", "Air Senegal", "Air Serbia", "Air Seychelles", "Airlink",
    "Alaska Airlines", "Allegiant", "American Airlines", "American Airlines Vacations", "AA", "Arajet",
    "Austrian Airlines", "Avianca", "Azul Airlines", "Azul Viagens", "Azul", "BeOnd", "Blue Islands",
    "Breeze Airways", "Breeze", "Cape Air", "Caribbean Airlines", "Cathay Pacific", "China Airlines",
    "Condor", "Copa Airlines", "Cyprus Airways", "DAN AIR", "Dohop", "Eastern Airlines", "Eastern Airways",
    "El Al", "Emetebe", "Emirates", "Ethiopian Airlines", "Etihad", "EVA Airways", "Fiji Airways",
    "Firefly", "Flair Airlines", "Fly Lili", "Frontier", "Garuda Indonesia", "Georgian Airways",
    "GOL Airlines", "Greater Bay Airlines", "Hong Kong Express", "Iberojet", "Icelandair",
    "Japan Airlines", "Japan Airlines Domestic", "JA", "Jazeera Airways", "Jeju Air", "JetBlue",
    "JetSMART", "JSX", "Kenya Airways", "KLM", "Korean Air", "Kuwait Airways", "Level", "Lifemiles",
    "Loganair", "Nok Air", "Norse Atlantic Airways", "Oman Air", "Olympic Air", "Pacific Coastal Airlines",
    "Philippine Airlines", "PLAY Airlines", "Porter Airlines", "Rex Airlines", "Royal Air Maroc",
    "Royal Brunei Airlines", "RwandAir", "Safarilink", "Saudia", "Scoot", "Shangri-La",
    "Singapore Airlines", "SKS Airways", "SKY express", "Sky Airline", "SKYhigh Dominicana", "SKY",
    "South African Airlines", "Spirit", "Spirit Vacations", "Sri Lankan", "Star Alliance",
    "STARLUX Airlines", "Sun Country", "Sun Country Vacations", "TAG Airlines", "Tap Portugal",
    "Tarom Airlines", "Tennis Australia", "Thai Airways", "Thai Smile", "Tropic Air",
    "Turkish Airlines", "United", "United Airlines Packages", "United Airlines", "UA",
    "Vientam Airlines", "Viva Aerobus", "Virgin Atlantic", "Virgin Atlantic Packages",
    "Virgin Australia", "Vistara", "Volaris", "Vueling", "Winair", "Wingo", "Wizz Air", "YaVas"
]}



def preprocess_keyword(keyword):
    """Clean and standardize the keyword text"""
    keyword = str(keyword)  # 🔁 aseguramos que siempre sea string
    keyword = re.sub(r'\bflight\b', 'flights', keyword, flags=re.IGNORECASE)
    keyword = keyword.lower()
    keyword = re.sub(r'\s+', ' ', keyword)
    keyword = re.sub(r'[^a-z0-9\s]', '', keyword)
    return keyword.strip()


def classify_location(location):
    location = location.strip().lower()
    
    if location in KNOWN_COUNTRIES:  # ✅ Verificar primero si es país
        return "country"
    elif location in KNOWN_CITIES:
        return "city"
    return "unknown"


def contains_branded_keyword(text):
    """Check if the text contains any branded keywords"""
    if pd.isnull(text):
        return False  # No hay texto, no puede ser branded
    try:
        text_lower = str(text).lower()
        return any(re.search(rf'\b{re.escape(brand)}\b', text_lower) for brand in BRANDED_KEYWORDS)
    except Exception:
        return False  # En caso de error inesperado, tratamos como no branded

def classify_keyword(keyword):
    """Classify keywords using rule-based approach"""
    keyword_clean = preprocess_keyword(keyword)

    # Branded keyword
    if contains_branded_keyword(keyword):
        return "Branded"

    # ORDEN CORREGIDO: Patrones específicos primero
    
    # Pattern: "flights to DEST from ORIG"
    match = re.match(r'^flights to ([a-z\s]+) from ([a-z\s]+)$', keyword_clean)
    if match:
        destination = match.group(1).strip()
        origin = match.group(2).strip()
        origin_type = classify_location(origin)
        destination_type = classify_location(destination)
        if "unknown" in [origin_type, destination_type]:
            return "Unknown"
        return f"{origin_type.title()} to {destination_type.title()} - Flights from OR to DN"

    # Pattern: "flights from X to Y"
    match = re.match(r'^flights from ([a-z\s]+) to ([a-z\s]+)$', keyword_clean)
    if match:
        origin = match.group(1).strip()
        destination = match.group(2).strip()
        origin_type = classify_location(origin)
        destination_type = classify_location(destination)
        if "unknown" in [origin_type, destination_type]:
            return "Unknown"
        return f"{origin_type.title()} to {destination_type.title()} - Flights from OR to DN"

    # Pattern: "flights to X" - MOVER ANTES QUE "X to Y"
    match = re.match(r'^flights to ([a-z\s]+)$', keyword_clean)
    if match:
        destination = match.group(1).strip()
        location_type = classify_location(destination)
        return f"To {location_type.title()} - Flights to DN" if location_type != "unknown" else "Unknown"

    # Pattern: "flights from X" - MOVER ANTES QUE "X to Y"
    match = re.match(r'^flights from ([a-z\s]+)$', keyword_clean)
    if match:
        origin = match.group(1).strip()
        location_type = classify_location(origin)
        return f"From {location_type.title()} - Flights from OR" if location_type != "unknown" else "Unknown"

    # Pattern: "X to Y flights"
    match = re.match(r'^([a-z\s]+) to ([a-z\s]+) flights$', keyword_clean)
    if match:
        origin = match.group(1).strip()
        destination = match.group(2).strip()
        origin_type = classify_location(origin)
        destination_type = classify_location(destination)
        if "unknown" in [origin_type, destination_type]:
            return "Unknown"
        return f"{origin_type.title()} to {destination_type.title()} - Flights from OR to DN"

    # Pattern: "X flights"
    match = re.match(r'^([a-z\s]+) flights$', keyword_clean)
    if match:
        location = match.group(1).strip()
        location_type = classify_location(location)
        return f"To {location_type.title()} - Flights to DN" if location_type != "unknown" else "Unknown"

    # Pattern: "X to Y" - MOVER AL FINAL para que sea el menos específico
    match = re.match(r'^([a-z\s]+) to ([a-z\s]+)$', keyword_clean)
    if match:
        origin = match.group(1).strip()
        destination = match.group(2).strip()
        
        # FILTRO ADICIONAL: Rechazar si el origen contiene palabras no-geográficas
        non_geographic_words = {'flights', 'cheap', 'direct', 'nonstop', 'round', 'trip', 'tickets', 'deals'}
        if any(word in origin.lower().split() for word in non_geographic_words):
            return "Unknown"
            
        origin_type = classify_location(origin)
        destination_type = classify_location(destination)
        if "unknown" in [origin_type, destination_type]:
            return "Unknown"
        return f"{origin_type.title()} to {destination_type.title()} - Flights from OR to DN"

    return "Unknown"



# -------------------------------
# INTERFAZ STREAMLIT
# -------------------------------

st.title("Flight Keyword Classifier")
st.write("This application classifies flight-related keywords using a rule-based approach.")

option = st.radio("How would you like to enter the keywords?", ["Enter manually", "Upload Excel file"])

keywords = []

if option == "Enter manually":
    text_input = st.text_area("Write one or more keywords, one per line")
    if st.button("Classify"):
        keywords = [line.strip() for line in text_input.split("\n") if line.strip()]
elif option == "Upload Excel file":
    file = st.file_uploader("Upload an Excel file with a 'Keyword' column", type=["xlsx"])
    if file is not None:
        df_input = pd.read_excel(file)
        if "Keyword" in df_input.columns:
            keywords = df_input["Keyword"].tolist()
        else:
            st.error("The file must contain a column named 'Keyword'.")

if keywords:
    # Show a progress bar during classification
    progress_bar = st.progress(0)
    results = []
    
    for i, keyword in enumerate(keywords):
        results.append({
            "Keyword": keyword,
            "Classification": classify_keyword(keyword)
        })
        progress_bar.progress((i + 1) / len(keywords))
    
    results_df = pd.DataFrame(results)
    st.success(f"Classified {len(keywords)} keywords!")
    
    # Display results
    st.write("Results:")
    st.dataframe(results_df)
    
    # Add statistics
    st.write("### Classification Statistics")
    classification_counts = results_df["Classification"].value_counts()
    st.bar_chart(classification_counts)
    
    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Results")
        return output.getvalue()

    st.download_button(
        label="📥 Download results in Excel",
        data=convert_df_to_excel(results_df),
        file_name="keyword_classification.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )