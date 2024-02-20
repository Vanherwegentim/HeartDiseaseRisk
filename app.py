import streamlit as st
import pandas as pd
import polars as pl
import numpy as np
import pickle
import sklearn
import plotly.graph_objs as go
import random
from helperfunctions import *

from streamlit_float import *

from openai import OpenAI


st.set_page_config(layout="wide")
float_init(theme=True, include_unstable_primary=False)

DATASET_PATH = "heart_2020_cleaned.csv"
LOG_MODEL_PATH = "logistic_regression.pkl"
#Gets random row from the dataset
total_rows= 319796
if "random_row_index" not in st.session_state:
    # If not, generate a new random row index and store it in the session state
    st.session_state.random_row_index = random.randint(0, total_rows - 1)

# Use the stored random row index to read the specific row from the CSV file
# This ensures the same row is used throughout the session
random_row_index = st.session_state.random_row_index
random_row = pd.read_csv(DATASET_PATH, skiprows=random_row_index, nrows=1)


BMI = random_row.iloc[0,1]
smokingcat = random_row.iloc[0,2]
alcohol = random_row.iloc[0,3]
strokecat = random_row.iloc[0,4]

diffwalk = random_row.iloc[0,7]
gender = random_row.iloc[0,8]
age = random_row.iloc[0,9]
diabeticcat = random_row.iloc[0,11]
genhealth = random_row.iloc[0,13]
sleeptime = random_row.iloc[0,14]


@st.cache_data(persist=True)
def load_dataset() -> pd.DataFrame:
    heart_df = pl.read_csv(DATASET_PATH)
    heart_df = heart_df.to_pandas()
    heart_df = pd.DataFrame(np.sort(heart_df.values, axis=0),
                            index=heart_df.index,
                            columns=heart_df.columns)
    return heart_df
def user_input_features() -> pd.DataFrame:
    col1, col2, col3 = col2cont.columns([1.5, 1,1])
    # race = col1cont.selectbox("Race", options=(race for race in heart.Race.unique()))
    sex = col1.selectbox("Sex", options=(sex for sex in heart.Sex.unique()),index=sex_to_numeric(gender) )
    age_cat = col1.selectbox("Age category",
                                   options=(age_cat for age_cat in heart.AgeCategory.unique()), index=age_to_numeric(age))
    bmi_cat = col1.selectbox("BMI category",
                                   options=(bmi_cat for bmi_cat in heart.BMICategory.unique()), index=BMI_to_numeric(BMI))
    sleep_time = col2.number_input("How many hours on average do you sleep?", 0, 24,value=int(sleeptime))
    gen_health = col1.selectbox("How can you define your general health?",
                                      options=(gen_health for gen_health in heart.GenHealth.unique()), index=gen_health_to_numeric(genhealth))
    # phys_health = col1cont.number_input("For how many days during the past 30 days was"
    #                                       " your physical health not good?", 0, 30, 0)
    # # ment_health = col1cont.number_input("For how many days during the past 30 days was"
    #                                       " your mental health not good?", 0, 30, 0)
    # phys_act = col1cont.selectbox("Have you played any sports (running, biking, etc.)"
    #                                 " in the past month?", options=("No", "Yes"))
    smoking = col3.selectbox("Have you smoked at least 100 cigarettes in"
                                   " your entire life (approx. 5 packs)?)",
                                   options=("No", "Yes"), index=smoking_to_numeric(smokingcat))
    alcohol_drink = col2.selectbox("Do you have more than 14 drinks of alcohol (men)"
                                         " or more than 7 (women) in a week?", options=("No", "Yes"), index=alcohol_to_numeric(alcohol))
    stroke = col2.selectbox("Have you ever had a stroke?", options=("No", "Yes"), index=stroke_to_numeric(strokecat))
    diff_walk = col3.selectbox("Do you have difficulty walking"
                                     " or climbing stairs?", options=("No", "Yes"), index=diffwalk_to_numeric(diffwalk))
    diabetic = col3.selectbox("Do you have diabetes?",
                                    options=(diabetic for diabetic in heart.Diabetic.unique()), index=diabetic_to_numeric(diabeticcat))
    # asthma = col3.selectbox("Do you have asthma?", options=("No", "Yes"))
    # kid_dis = col1cont.selectbox("Do you have kidney disease?", options=("No", "Yes"))
    # skin_canc = col1cont.selectbox("Do you have skin cancer?", options=("No", "Yes"))
    features = pd.DataFrame({
        "PhysicalHealth": ["0"],
        "MentalHealth": ["0"],
        "SleepTime": [sleep_time],
        "BMICategory": [bmi_cat],
        "Smoking": [smoking],
        "AlcoholDrinking": [alcohol_drink],
        "Stroke": [stroke],
        "DiffWalking": [diff_walk],
        "Sex": [sex],
        "AgeCategory": [age_cat],
        "Race": ["White"],
        "Diabetic": [diabetic],
        "PhysicalActivity": ["No"],
        "GenHealth": [gen_health],
        "Asthma": ["No"],
        "KidneyDisease": ["No"],
        "SkinCancer": ["No"]
    })
    return features
# st.set_page_config(
#     page_title="Heart Disease Prediction App",
#     page_icon="images/heart-fav.png"
# )
st.title("Heart Disease Prediction")

col1, col2, col3 = st.columns([3,3,3])
data = np.random.randn(10, 1)
# contcol1 = col1.container()
contcontcol1 = col1.container(border=True)
contcontcol1.subheader("Hello, Jane Doe")
contcontcol1.markdown("""
                  Welcome to your health dashboard. 
                  Here you can find all the information about your health.""")
contcol2 = col2.container(border=True)


col2.subheader("What If?")

col2cont =  col2.container(border=True)
#Prediction

heart = load_dataset()
col2topcont = col2cont.container()
col2topcont1, col2topcont2 = col2topcont.columns([1,1])
submit = col2topcont1.button("Predict")

input_df = user_input_features()
df = pd.concat([input_df, heart], axis=0)
df = df.drop(columns=["HeartDisease"])
cat_cols = ["BMICategory", "Smoking", "AlcoholDrinking", "Stroke", "DiffWalking",
            "Sex", "AgeCategory", "Race", "Diabetic", "PhysicalActivity",
            "GenHealth", "Asthma", "KidneyDisease", "SkinCancer"]
for cat_col in cat_cols:
    dummy_col = pd.get_dummies(df[cat_col], prefix=cat_col)
    df = pd.concat([df, dummy_col], axis=1)
    del df[cat_col]
df = df[:1]
df.fillna(0, inplace=True)
log_model = pickle.load(open(LOG_MODEL_PATH, "rb"))

prediction_prob = log_model.predict_proba(df)  

if "previous_state" not in st.session_state:
    st.session_state.previous_state = 0
if submit:      
    delta_calculated = round(round(prediction_prob[0][1] * 100, 2) - st.session_state.previous_state,2)
    col2topcont2.metric(label="Heart Disease Risk", value=str(round(prediction_prob[0][1] * 100, 2)) + " %", delta= str(delta_calculated) + " %", delta_color="inverse")
    st.session_state.previous_state = round(prediction_prob[0][1] * 100, 2)

#End Prediction

if "prediction" not in st.session_state:
    st.session_state.prediction = str(round(prediction_prob[0][1] * 100, 2))

contcol2.markdown("<p style='text-align: center;' > Your calculated risk is</p>", unsafe_allow_html=True)
contcol2.markdown("<h1 style='text-align:center;font-size:3rem; padding:0rem;'>" + st.session_state.prediction + "%</h1>", unsafe_allow_html=True)
contcol2.markdown("<p style='text-align: center;' >Considered quite high</p>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
        [data-testid=stSidebar] [data-testid=stImage]{
            text-align: center;
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True
)

# Using object notation
st.sidebar.image('pictures/stock_placeholder.jpg', width=100)
sidecont1, sidecont2, sidecont3 = st.sidebar.columns([3, 3, 3])
sidecont1 = st.sidebar.container(border=True)
sidecont2 = st.sidebar.container(border=True)
sidecont3 = st.sidebar.container(border=True)

sidecont1.markdown("<h2 style='text-align: center;' >BloodPressure </h2>", unsafe_allow_html=True)
sidecont1.markdown("<p style='text-align: center;' >120/80 <p>", unsafe_allow_html=True)
sidecont2.markdown("<h2 style='text-align: center;' >Cholesterol </h2>", unsafe_allow_html=True)
sidecont2.markdown("<p style='text-align: center;' >220 <p>", unsafe_allow_html=True)
sidecont3.markdown("<h2 style='text-align: center;' >Gender </h2>", unsafe_allow_html=True)
sidecont3.markdown("<p style='text-align: center;' >Female <p>", unsafe_allow_html=True)




with col1.container():
    st.subheader("Your results")

    # st.write("Your blood pressure is 120/80, which is abnormaly high")
    # data = np.random.randn(10, 1)
    # chart_data = pd.DataFrame(np.random.randn(20, 2), columns=["x", "y"])
    # st.line_chart(chart_data)

with col1.container(border=True):
    st.subheader("Cholesterol")
    st.markdown("<p>High cholesterol is a silent killer</p>", unsafe_allow_html=True)
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
    st.area_chart(chart_data)

smokingcontainer = col1.container(border=True)
col1col1, col1col2 = smokingcontainer.columns([1,1])

with col1col1.container():
    st.subheader("Smoking")
    st.markdown("<p>Smoking doubles your heart disease risk</p>", unsafe_allow_html=True)
with col1col2.container():
    st.markdown("<p style='text-align: center;' ></p>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;font-size:2rem; padding:0rem;'>50 %</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;' >of the current population smokes</p>", unsafe_allow_html=True)


    



# with col2.container():
#     st.subheader("Your Risk Over Time")
# with col2.container(border=True):
#     chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
#     st.bar_chart(chart_data)
# with col2.container(border=True):
#     st.subheader("Early symptoms of a heart attack")
#     st.markdown("<h4>Chest pain or discomfort </h4>", unsafe_allow_html=True)
#     st.markdown("Most heart attacks involve discomfort in the center or left side of the chest that lasts for more than a few minutes or that goes away and comes back. The discomfort can feel like uncomfortable pressure, squeezing, fullness, or pain.")
#     st.markdown("<h4>Feeling weak, light-headed, or faint</h4>", unsafe_allow_html=True)
#     st.markdown("<h4>Pain or discomfort in one or both arms or shoulders.</h4>", unsafe_allow_html=True)
#     st.markdown("<h4>Shortness of breath</h4>", unsafe_allow_html=True)



with col3.container(border=True):
    st.title("ChatGPT-like clone")

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
# def chat_content():
#     st.session_state['contents'].append(st.session_state.content)

# if 'contents' not in st.session_state:
#     st.session_state['contents'] = []
#     border = False
# else:
#     border = True

# with contcol3:
#     with st.container(border=border):
#         with st.container():
#             st.chat_input(key='content', on_submit=chat_content) 
#             button_b_pos = "0rem"
#             button_css = float_css_helper(width="2.2rem", bottom=button_b_pos, transition=0)
#             float_parent(css=button_css)
#         if content:=st.session_state.content:
#             with st.chat_message(name='robot'):
#                 for c in st.session_state.contents:
#                     st.write(c)
                    
