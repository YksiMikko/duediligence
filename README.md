# Due Diligence & Neuvotteluapuri 📊🤖

Tekoälypohjainen mikropalvelu ja päätöksenteon apuväline yrityskauppoihin, luottoriskien arviointiin ja kumppanineuvotteluihin.

---

## 🎯 Mistä on kyse?

Perinteiset talous- ja luottoriskiraportit tarjoavat kattavaa numeerista dataa, mutta käyttäjä jää usein yksin lukujen tulkinnan kanssa: *mitä nämä tunnusluvut tarkoittavat käytännössä, kun istutaan toimitusjohtajan kanssa neuvottelupöytään?*

Tämä ratkaisu siltaa kuilun historiallisen tilinpäätösdatan ja reaalimaailman päätöksenteon välillä. Se analysoi yrityksen talousluvut ja tuottaa automaattisesti:

1. **Riskikatsauksen & punaiset liput (Red Flags):** Tunnistaa piilevät epäsuhdat (esim. kasvava liikevaihto yhdistettynä heikkenevään käyttöpääomaan tai kuivuvaan kassaan).
2. **Kysymyspatterin johdolle:** 3–5 suoraa kysymystä toimitus- tai talousjohtajalle neuvottelutilanteeseen sekä suuntaviivat siitä, mitä vastauksissa kannattaa tarkkailla.
3. **Konkreettiset sopimusehtosuositukset:** Käytännön ehdotukset riskien hallintaan (esim. maksuajan lyhentäminen, vakuuksien vaatiminen tai lisäkauppahintaehdot / earn-out).

---

## 💡 Kaupallinen lisäarvo

* **Lisämyynti nykyisille palveluille (Upsell):** Voidaan liittää suoraan lisämoduuliksi valmiin talous- tai arvonmääritysraportin loppuun.
* **Konversion parantaminen (Freemium / Teaser):** Toimii kevyenä herätteenä yrityssivuilla ohjaamassa käyttäjiä laajemman analyysin pariin.
* **Saumaton käyttöönotto:** Hyödyntää suoraan yrityksen olemassa olevaa tunnuslukudataa – erillistä raskasta ulkoisen datan keruuta ei tarvita.

---

## 🛠️ Tekninen toteutus

* **Malli:** Google Gemini 2.5 Flash (`gemini-2.5-flash`)
* **Ohjaus:** Järjestelmäkehote (System Instruction) + Strukturoitu JSON Schema -tulostus
* **Käyttöliittymä:** Responsiivinen selainkäyttöliittymä (Streamlit)
* **Ketterä kehitys:** Rakennettu ja testattu nopeana prototyyppinä modernien AI-kehitystyökalujen avulla.

---

## 🚀 Käyttöönotto

### 1. Asenna riippuvuudet
```bash
pip install -r requirements.txt