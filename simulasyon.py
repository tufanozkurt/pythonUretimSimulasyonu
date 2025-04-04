import streamlit as st
import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt

# Streamlit arayüzü
st.title("🏭 Demir-Çelik Üretim Simülasyonu")

st.sidebar.header("🔧 Parametreler")
urun_sayisi = st.sidebar.slider("Ürün Sayısı", 5, 50, 20)
isci_sayisi = st.sidebar.slider("İşçi Sayısı", 1, 10, 4)
fire_ihtimali = st.sidebar.slider("Fire Oranı", 0.0, 0.5, 0.05, step=0.01)
ariza_ihtimali = st.sidebar.slider("Arıza İhtimali", 0.0, 0.5, 0.1, step=0.01)
fire_maliyeti = st.sidebar.number_input("Fire Başına Maliyet (TL)", 100, 5000, 500, step=100)
ariza_maliyeti = st.sidebar.number_input("Arıza Başına Maliyet (TL)", 100, 5000, 1000, step=100)

# Simülasyon verisi
rapor = []

class Istasyon:
    def __init__(self, env, name, capacity):
        self.name = name
        self.resource = simpy.Resource(env, capacity=capacity)
        self.env = env
        self.ariza_sayisi = 0
        self.fire_sayisi = 0

    def islem_yap(self, süre):
        if random.random() < ariza_ihtimali:
            ariza_suresi = random.randint(10, 30)
            self.ariza_sayisi += 1
            yield self.env.timeout(ariza_suresi)
        yield self.env.timeout(süre)
        if random.random() < fire_ihtimali:
            self.fire_sayisi += 1
            raise Exception("Fire")

def üretim(env, urun_id, kesim, isitma, haddeleme, isciler):
    with isciler.request() as req:
        yield req
        try:
            with kesim.resource.request() as r1:
                yield r1
                yield from kesim.islem_yap(30)
            with isitma.resource.request() as r2:
                yield r2
                yield from isitma.islem_yap(100)
            with haddeleme.resource.request() as r3:
                yield r3
                yield from haddeleme.islem_yap(50)
            rapor.append((urun_id, env.now, "Üretildi"))
        except:
            rapor.append((urun_id, env.now, "Fire"))

# Simülasyonu başlat
if st.button("Simülasyonu Başlat"):
    random.seed(42)
    env = simpy.Environment()
    kesim = Istasyon(env, "Kesim", 1)
    isitma = Istasyon(env, "Isıtma", 2)
    haddeleme = Istasyon(env, "Haddeleme", 1)
    isciler = simpy.Resource(env, capacity=isci_sayisi)

    for i in range(urun_sayisi):
        env.process(üretim(env, i+1, kesim, isitma, haddeleme, isciler))
        env.timeout(random.randint(1, 5))

    env.run(until=2000)

    # Raporlama
    df = pd.DataFrame(rapor, columns=["Ürün ID", "Zaman", "Durum"])
    st.subheader("📊 Üretim Sonuçları")
    st.dataframe(df)

    fire_toplam = kesim.fire_sayisi + isitma.fire_sayisi + haddeleme.fire_sayisi
    ariza_toplam = kesim.ariza_sayisi + isitma.ariza_sayisi + haddeleme.ariza_sayisi

    toplam_maliyet = fire_toplam * fire_maliyeti + ariza_toplam * ariza_maliyeti

    st.markdown(f"**♻️ Toplam Fire:** {fire_toplam}")
    st.markdown(f"**⛔ Toplam Arıza:** {ariza_toplam}")
    st.markdown(f"**💸 Toplam Maliyet:** {toplam_maliyet:,} TL")

    st.subheader("📈 Durum Grafiği")
    fig, ax = plt.subplots()
    df["Durum"].value_counts().plot(kind="bar", ax=ax, color=["green", "red"])
    st.pyplot(fig)

    st.success("Simülasyon tamamlandı ✅")
