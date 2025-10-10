from django import forms

ZIMBABWE_CITIES_AND_TOWNS = [
    ("Harare", "Harare"),
    ("Bulawayo", "Bulawayo"),
    ("Chitungwiza", "Chitungwiza"),
    ("Mutare", "Mutare"),
    ("Gweru", "Gweru"),
    ("Kwekwe", "Kwekwe"),
    ("Kadoma", "Kadoma"),
    ("Masvingo", "Masvingo"),
    ("Chinhoyi", "Chinhoyi"),
    ("Marondera", "Marondera"),
    ("Bindura", "Bindura"),
    ("Zvishavane", "Zvishavane"),
    ("Victoria Falls", "Victoria Falls"),
    ("Hwange", "Hwange"),
    ("Rusape", "Rusape"),
    ("Beitbridge", "Beitbridge"),
    ("Kariba", "Kariba"),
    ("Chipinge", "Chipinge"),
    ("Shurugwi", "Shurugwi"),
    ("Redcliff", "Redcliff"),
    ("Norton", "Norton"),
    ("Gokwe", "Gokwe"),
    ("Plumtree", "Plumtree"),
    ("Mvurwi", "Mvurwi"),
    ("Mazowe", "Mazowe"),
    ("Chegutu", "Chegutu"),
    ("Karoi", "Karoi"),
    ("Murewa", "Murewa"),
    ("Mhangura", "Mhangura"),
    ("Banket", "Banket"),
    ("Concession", "Concession"),
    ("Nyanga", "Nyanga"),
    ("Chirundu", "Chirundu"),
    ("Chiredzi", "Chiredzi"),
    ("Gwanda", "Gwanda"),
    ("Filabusi", "Filabusi"),
    ("Lupane", "Lupane"),
    ("Nkayi", "Nkayi"),
    ("Tsholotsho", "Tsholotsho"),
    ("Binga", "Binga"),
    ("Dete", "Dete"),
]

class ProductForm(forms.Form):
    location = forms.ChoiceField(
        choices=ZIMBABWE_CITIES_AND_TOWNS,
        label="Delivery Location"
    )

