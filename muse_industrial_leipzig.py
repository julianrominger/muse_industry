#!/usr/bin/env python
# coding: utf-8

# In[1]:


from pyomo import *
from math import sqrt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# In[2]:


directory = "data/"
#Allgemeine Kosten
#Kosten Gas
c_gas = 31.5

##Externe Stromkosten
eeg_umlage=67.9
eeg_faktor_kwk1=0
eeg_faktor_kwk2=0.6
#Arbeitspreis pro MWh
netz_ap=5.3
#Leistungspreis pro MW
netz_lp=91900
stromsteuer=15
kwk_bonus=23.2
wartung_kwk=16 # 16€ pro Bh
konzessionsabgabe=1.1
kwkg_umlage=3.45
par19_umlage=3.7
absch_umlage=0.11
umlagen_entgelte_extern = (netz_ap+stromsteuer+konzessionsabgabe+kwkg_umlage+par19_umlage+absch_umlage+eeg_umlage)
cost_rueck = 10
cost_res_buffer = 40
cost_lastspitze = netz_lp

#Peak Shaving
peak_init = 20
peak = peak_init

#Stunden in den Regelleistung geboten werden kann
rl_vzr = 4*4

#Vermarktungszeitraum Arbitrage
arb_vzr = 24*4

#Durchschnittlicher Strompreis
price_avg = 35

# SRL Abrufe

#Einlesen von Strompreisen
file = directory+"Abrufwlichkeit_15-17.csv"
afrr_abruf = pd.read_csv(file, sep = ",", decimal =".", usecols =["energy_price","NEG","POS"])

afrr_abruf=afrr_abruf.set_index(afrr_abruf["energy_price"])
afrr_abruf=afrr_abruf.drop(["energy_price"], axis = 1)

# Kraft-Wärme-Kopplungsanlagen

gaspreis_bonus_kwk = 5.5
c_gas_kwk = c_gas - gaspreis_bonus_kwk

#KWK1,2
nennleistung_kwk1 = 3.047*1.03
nennleistung_kwk2 = 3.356
nennleistung_kwk1_gas = 6.809
nennleistung_kwk2_gas = 8.246
nennleistung_kwk1_therm = 2.877*1.02
nennleistung_kwk2_therm = 3.227
teillast_kwk1 = 1.524
teillast_kwk2 = 1.66
teillast_kwk1_gas = 3.809
teillast_kwk2_gas = 4.466
teillast_kwk1_therm = 1.79
teillast_kwk2_therm = 1.92

#Wirkungsgrade und Stromkennzahl für Teillast und Nennleistung
wirkungsgrad_elektr_kwk1_nl= nennleistung_kwk1/nennleistung_kwk1_gas
wirkungsgrad_therm_kwk1_nl=nennleistung_kwk1_therm/nennleistung_kwk1_gas
wirkungsgrad_elektr_kwk2_nl=nennleistung_kwk2/nennleistung_kwk2_gas
wirkungsgrad_therm_kwk2_nl=nennleistung_kwk2_therm/nennleistung_kwk2_gas
stromkennzahl_kwk1_nl = round(wirkungsgrad_elektr_kwk1_nl/wirkungsgrad_therm_kwk1_nl,2)
stromkennzahl_kwk2_nl = round(wirkungsgrad_elektr_kwk2_nl/wirkungsgrad_therm_kwk2_nl,2)
wirkungsgrad_elektr_kwk1_tl= teillast_kwk1/teillast_kwk1_gas
wirkungsgrad_therm_kwk1_tl=teillast_kwk1_therm/teillast_kwk1_gas
wirkungsgrad_elektr_kwk2_tl=teillast_kwk2/teillast_kwk2_gas
wirkungsgrad_therm_kwk2_tl=teillast_kwk2_therm/teillast_kwk2_gas
stromkennzahl_kwk1_tl = round(wirkungsgrad_elektr_kwk1_tl/wirkungsgrad_therm_kwk1_tl,2)
stromkennzahl_kwk2_tl = round(wirkungsgrad_elektr_kwk2_tl/wirkungsgrad_therm_kwk2_tl,2)

#Kosten pro Erzeugung 1 MWh Wärme und Strom 
varcos_kwk1_nl=round(c_gas_kwk/wirkungsgrad_elektr_kwk1_nl+eeg_umlage*eeg_faktor_kwk1,2)
varcos_kwk2_nl=round(c_gas_kwk/wirkungsgrad_elektr_kwk2_nl+eeg_umlage*eeg_faktor_kwk2-kwk_bonus,2)
varcos_kwk1_tl=round(c_gas_kwk/wirkungsgrad_elektr_kwk1_tl+eeg_umlage*eeg_faktor_kwk1,2)
varcos_kwk2_tl=round(c_gas_kwk/wirkungsgrad_elektr_kwk2_tl+eeg_umlage*eeg_faktor_kwk2-kwk_bonus,2)
cos_lin_kwk1 =(nennleistung_kwk1_gas-teillast_kwk1_gas)*c_gas_kwk/(nennleistung_kwk1-teillast_kwk1)+eeg_umlage*eeg_faktor_kwk1#varcos_kwk1_nl/varcos_kwk1_tl 
cos_lin_kwk2 =(nennleistung_kwk2_gas-teillast_kwk2_gas)*c_gas_kwk/(nennleistung_kwk2-teillast_kwk2)+eeg_umlage*eeg_faktor_kwk2-kwk_bonus
###Teillastverhalten simulieren!!!!

#Stromkennzahlfaktoren
f1_kwk1 = (nennleistung_kwk1+nennleistung_kwk1_therm)/nennleistung_kwk1_gas*(1/wirkungsgrad_elektr_kwk1_tl-((1/wirkungsgrad_elektr_kwk1_nl)-(1/wirkungsgrad_elektr_kwk1_tl))/((teillast_kwk1/nennleistung_kwk1)-1))-1
f1_kwk2 = (nennleistung_kwk2+nennleistung_kwk2_therm)/nennleistung_kwk2_gas*(1/wirkungsgrad_elektr_kwk2_tl-((1/wirkungsgrad_elektr_kwk2_nl)-(1/wirkungsgrad_elektr_kwk2_tl))/((teillast_kwk1/nennleistung_kwk2)-1))-1
f2_kwk1 = (nennleistung_kwk1+nennleistung_kwk1_therm)/nennleistung_kwk1_gas*((1/wirkungsgrad_elektr_kwk1_nl)-(1/wirkungsgrad_elektr_kwk1_tl))/((1/nennleistung_kwk1)-(1/teillast_kwk1))
f2_kwk2 = (nennleistung_kwk2+nennleistung_kwk2_therm)/nennleistung_kwk2_gas*((1/wirkungsgrad_elektr_kwk2_nl)-(1/wirkungsgrad_elektr_kwk2_tl))/((1/nennleistung_kwk2)-(1/teillast_kwk2))

#Mindestbetrieb/ -stillstand KWKs
kwk_min_betrieb = 4*1 #1 Stunde
kwk_min_stillstand = 4*1 #1 Stunde

#Anfahrkosten
cos_anfahr = 1
cos_ausschalt = 1

#Maximale Starts pro Woche
kwk_maxstarts = 300/52

#Wartungskosten
cos_wartung = wartung_kwk

#Rückkühler
leistung_rueckkuehler = 3

#Präqualifizierte PRL Leistung
kwk_fcr1 = 1/3*(nennleistung_kwk1-teillast_kwk1)
kwk_fcr2 = 1/3*(nennleistung_kwk2-teillast_kwk2)

#Präqualifizierte SRL Leistung
kwk_afrr1 = nennleistung_kwk1-teillast_kwk1
kwk_afrr2 = nennleistung_kwk2-teillast_kwk2

#Abrufwahrscheinlichkeiten
kwk_afrr_ep_neg1 = 340 #siehe Excel
kwk_afrr_ep_pos1 = 43 #Mindestpreis von 35€ angenommen (siehe Maximum Veröffentlichung)
kwk_afrr_ep_neg2 = 340 #siehe Excel
kwk_afrr_ep_pos2 = 56 #Mindestpreis von 35€ angenommen (siehe Maximum Veröffentlichung)
abrufwlichkeit_neg1 = afrr_abruf["NEG"][kwk_afrr_ep_neg1]
abrufwlichkeit_pos1 = afrr_abruf["POS"][kwk_afrr_ep_pos1]
abrufwlichkeit_neg2 = afrr_abruf["NEG"][kwk_afrr_ep_neg2]
abrufwlichkeit_pos2 = afrr_abruf["POS"][kwk_afrr_ep_pos2]

kwk1_total = varcos_kwk1_tl*1*teillast_kwk1+ cos_lin_kwk1*(nennleistung_kwk1-teillast_kwk1) + cos_wartung
kwk2_total = varcos_kwk2_tl*1*teillast_kwk2+ cos_lin_kwk2*(nennleistung_kwk2 - teillast_kwk2) + cos_wartung

#Erstellung Kenndaten KWK
##INSERT: FCR per KWK and FRR per KWK
kwk = pd.DataFrame({"kwk": [1, 2], 
                    "varcos_tl": [varcos_kwk1_tl, varcos_kwk2_tl],
                    "cos_lin": [cos_lin_kwk1, cos_lin_kwk2],
                    "cap": [nennleistung_kwk1, nennleistung_kwk2],
                    "floor": [teillast_kwk1, teillast_kwk2], 
                    "f1": [f1_kwk1, f1_kwk2],
                    "f2": [f2_kwk1, f2_kwk2],
                    "kwk_fcr":[kwk_fcr1,kwk_fcr2],
                    "kwk_afrr":[kwk_afrr1,kwk_afrr2],
                    "cos_wartung":[wartung_kwk, wartung_kwk],
                    "kwk_afrr_prob_neg":[abrufwlichkeit_neg1, abrufwlichkeit_neg2],
                    "kwk_afrr_prob_pos":[abrufwlichkeit_pos1, abrufwlichkeit_pos2],
                    "kwk_afrr_ep_neg":[kwk_afrr_ep_neg1, kwk_afrr_ep_neg2],
                    "kwk_afrr_ep_pos":[kwk_afrr_ep_pos1, kwk_afrr_ep_pos2]})
kwk.index = np.arange(1, len(kwk)+1)
#kwk.to_csv("kwk_data.csv", index_label = "kwk", sep=",", header = True)
kwk.to_csv(directory + "kwk_varcos_tl.csv", columns =["varcos_tl"], index_label = "kwk")
kwk.to_csv(directory + "kwk_cos_lin.csv", columns =["cos_lin"], index_label = "kwk")
kwk.to_csv(directory + "kwk_cap.csv", columns =["cap"], index_label = "kwk")
kwk.to_csv(directory + "kwk_floor.csv", columns =["floor"], index_label = "kwk")
kwk.to_csv(directory + "kwk_f1.csv", columns =["f1"], index_label = "kwk")
kwk.to_csv(directory + "kwk_f2.csv", columns =["f2"], index_label = "kwk")
kwk.to_csv(directory + "kwk_fcr.csv", columns =["kwk_fcr"], index_label = "kwk")
kwk.to_csv(directory + "kwk_afrr.csv", columns =["kwk_afrr"], index_label = "kwk")
kwk.to_csv(directory + "kwk_afrr_prob_neg.csv", columns =["kwk_afrr_prob_neg"], index_label = "kwk")
kwk.to_csv(directory + "kwk_afrr_prob_pos.csv", columns =["kwk_afrr_prob_pos"], index_label = "kwk")
kwk.to_csv(directory + "kwk_afrr_ep_neg.csv", columns =["kwk_afrr_ep_neg"], index_label = "kwk")
kwk.to_csv(directory + "kwk_afrr_ep_pos.csv", columns =["kwk_afrr_ep_pos"], index_label = "kwk")

# Gaskessel

#Nennleistung Wärme
nennleistung_kessel1 = 9.726
nennleistung_kessel2 = 14.435
nennleistung_kessel3 = 16.577
nennleistung_kessel4 = 18.093
nennleistung_schwach = 2
#Nennleistung Gas
nennleistung_kessel1_gas = 11.610
nennleistung_kessel2_gas = 16.564
nennleistung_kessel3_gas = 18.962
nennleistung_kessel4_gas = 20.443
nennleistung_schwach_gas = 4
#Teillast Wärme
teillast_kessel1 = 1.086
teillast_kessel2 = 1.879
teillast_kessel3 = 2.362
teillast_kessel4 = 2.522
teillast_schwach = 0
#Teillast Gas
teillast_kessel1_gas = 1.227
teillast_kessel2_gas = 2.111
teillast_kessel3_gas = 2.663
teillast_kessel4_gas = 2.829
teillast_schwach_gas = 0
#Wirkungsgrade
wirkungsgrad_kessel1_nl=nennleistung_kessel1/nennleistung_kessel1_gas
wirkungsgrad_kessel1_tl=teillast_kessel1/teillast_kessel1_gas
wirkungsgrad_kessel2_nl=nennleistung_kessel2/nennleistung_kessel2_gas
wirkungsgrad_kessel2_tl=teillast_kessel2/teillast_kessel2_gas
wirkungsgrad_kessel3_nl=nennleistung_kessel3/nennleistung_kessel3_gas
wirkungsgrad_kessel3_tl=teillast_kessel3/teillast_kessel3_gas
wirkungsgrad_kessel4_nl=nennleistung_kessel4/nennleistung_kessel4_gas
wirkungsgrad_kessel4_tl=teillast_kessel4/teillast_kessel4_gas
wirkungsgrad_schwach_nl=nennleistung_schwach/nennleistung_schwach_gas
wirkungsgrad_schwach_tl=wirkungsgrad_schwach_nl

### Teillastverhalten simulieren!
#Kosten Nennleistung
varcost_kessel1_nl = c_gas/wirkungsgrad_kessel1_nl
varcost_kessel2_nl = c_gas/wirkungsgrad_kessel2_nl
varcost_kessel3_nl = c_gas/wirkungsgrad_kessel3_nl
varcost_kessel4_nl = c_gas/wirkungsgrad_kessel4_nl
varcost_schwach_nl = c_gas/wirkungsgrad_schwach_nl

#Kosten Teillastleistung
varcost_kessel1_tl = c_gas/wirkungsgrad_kessel1_tl
varcost_kessel2_tl = c_gas/wirkungsgrad_kessel2_tl
varcost_kessel3_tl = c_gas/wirkungsgrad_kessel3_tl
varcost_kessel4_tl = c_gas/wirkungsgrad_kessel4_tl
varcost_schwach_tl = c_gas/wirkungsgrad_schwach_tl

#Lineare Kosten
cos_lin_kessel1 = (nennleistung_kessel1_gas-teillast_kessel1_gas)*c_gas/(nennleistung_kessel1-teillast_kessel1)
cos_lin_kessel2 = (nennleistung_kessel2_gas-teillast_kessel2_gas)*c_gas/(nennleistung_kessel2-teillast_kessel2)
cos_lin_kessel3 = (nennleistung_kessel3_gas-teillast_kessel3_gas)*c_gas/(nennleistung_kessel3-teillast_kessel3)
cos_lin_kessel4 = (nennleistung_kessel4_gas-teillast_kessel4_gas)*c_gas/(nennleistung_kessel4-teillast_kessel4)
cos_lin_schwach = (nennleistung_schwach_gas-teillast_schwach_gas)*c_gas/(nennleistung_schwach-teillast_schwach)

#Wartungskosten pro Bh
cos_wartung_kessel = 12

kessel1_total = varcost_kessel1_tl*1*teillast_kessel1+ cos_lin_kessel1*(nennleistung_kessel1-teillast_kessel1) + cos_wartung_kessel

#Erstellung Kenndaten Kessel
kessel = pd.DataFrame({"kessel": [1, 2, 3, 4, 5], 
                       "cos_lin_kessel": [cos_lin_kessel1, cos_lin_kessel2, cos_lin_kessel3, cos_lin_kessel4, cos_lin_schwach],
                       "cos_kessel_tl": [varcost_kessel1_tl, varcost_kessel2_tl, varcost_kessel3_tl, varcost_kessel4_tl, varcost_schwach_tl], 
                       "cap_kessel": [nennleistung_kessel1, nennleistung_kessel2, nennleistung_kessel3, nennleistung_kessel4, nennleistung_schwach],
                       "floor_kessel": [teillast_kessel1, teillast_kessel2, teillast_kessel3, teillast_kessel4, teillast_schwach]})
kessel.index = np.arange(1, len(kessel)+1)
kessel.to_csv("kessel_data.csv", index_label = "kessel", sep=",", header = True)
kessel.to_csv(directory +"cos_lin_kessel.csv", columns =["cos_lin_kessel"], index_label = "kessel")
kessel.to_csv(directory +"cos_kessel_tl.csv", columns =["cos_kessel_tl"], index_label = "kessel")
kessel.to_csv(directory +"cap_kessel.csv", columns =["cap_kessel"], index_label = "kessel")
kessel.to_csv(directory +"floor_kessel.csv", columns =["floor_kessel"], index_label = "kessel")

# Lüftungsanlagen (RLT-Anlagen)

#RLT
#Betrieb Sommermonate > 30°
geb30_nl = 3.375
geb50_nl = 4.671
geb8x_nl = 0.837 + 1.350
#Betrieb Winter < 10°
geb30_wb = 0.512*geb30_nl
geb50_wb = 0.512*geb50_nl
geb8x_wb = 0.512*geb8x_nl
#Niedrigster möglicher Arbeitspunkt für Flexibilitätsvermarktung
geb30_tl = 0.4*geb30_nl
geb50_tl = 0.4*geb50_nl
geb8x_tl = 0.4*geb8x_nl
rlt_cos = 250


#Abrufwahrscheinlichkeit maximal 5% der Zeit
rlt_afrr_prob_neg = 2/(7*24)
rlt_afrr_prob_pos = 2/(7*24)

#Arbeitspreis für gewünschte Abrufwahrscheinlichkeit
rlt_afrr_ep_neg= 272#afrr_abruf[afrr_abruf["NEG"]<rlt_afrr_prob_neg].index.values.astype(int)[0]
rlt_afrr_ep_pos= 210#afrr_abruf[afrr_abruf["POS"]<rlt_afrr_prob_pos].index.values.astype(int)[0]

rlt_dsm_max_betrieb =4*4 #Maximallänge von 2 Stunde für DSM Maßnahmen
rlt_dsm_min_pause = 2*4 #Minimalpause von 2 Stunde zwischen DSM Maßnahmen

#Erstellung Kenndaten RLT, INSERT FCR per HVAC and FRR per HVAC
rlt = pd.DataFrame({"rlt": [1, 2, 3],
                    "cap_rlt": [geb30_nl, geb50_nl, geb8x_nl],
                    "winter_rlt": [geb30_wb, geb50_wb, geb8x_wb],
                    "floor_rlt": [geb30_tl, geb50_tl, geb8x_tl],
                    "rlt_afrr_prob_neg": [rlt_afrr_prob_neg,rlt_afrr_prob_neg,rlt_afrr_prob_neg],
                    "rlt_afrr_prob_pos": [rlt_afrr_prob_pos,rlt_afrr_prob_pos,rlt_afrr_prob_pos],
                    "rlt_afrr_ep_neg": [rlt_afrr_ep_neg,rlt_afrr_ep_neg,rlt_afrr_ep_neg],
                    "rlt_afrr_ep_pos": [rlt_afrr_ep_pos,rlt_afrr_ep_pos,rlt_afrr_ep_pos]})
rlt["rlt_fcr"] = rlt["cap_rlt"]*0.2
rlt.index = np.arange(1, len(rlt)+1)
rlt.to_csv("rlt_data.csv", index_label = "rlt", sep=",", header = True)
rlt.to_csv(directory +"cap_rlt.csv", columns =["cap_rlt"], index_label = "rlt")
rlt.to_csv(directory +"winter_rlt.csv", columns =["winter_rlt"], index_label = "rlt")
rlt.to_csv(directory +"floor_rlt.csv", columns =["floor_rlt"], index_label = "rlt")
rlt.to_csv(directory +"rlt_fcr.csv", columns =["rlt_fcr"], index_label = "rlt")
rlt.to_csv(directory +"rlt_afrr_prob_neg.csv", columns =["rlt_afrr_prob_neg"], index_label = "rlt")
rlt.to_csv(directory +"rlt_afrr_prob_pos.csv", columns =["rlt_afrr_prob_pos"], index_label = "rlt")
rlt.to_csv(directory +"rlt_afrr_ep_neg.csv", columns =["rlt_afrr_prob_neg"], index_label = "rlt")
rlt.to_csv(directory +"rlt_afrr_ep_pos.csv", columns =["rlt_afrr_prob_pos"], index_label = "rlt")

# Notstromersatzanlage

cos_verbrauch = 0.66 #€/L
heizwert = 10 #kWh/L
effizienz = 0.4 #Effizienz der Heizölverbrennung
#Notstromersatzanlage
nea1_nl = 3.3 #Effizienz der Anlage
nea2_nl = 3.3 #Effizienz der Anlage
nea1_cos = cos_verbrauch/heizwert*1000/effizienz
nea2_cos = cos_verbrauch/heizwert*1000/effizienz+0.01 #Kosten erhöht um Prioritäten zu setzen. 
nea_afrr1 = nea1_nl
nea_afrr2 = nea2_nl
nea_starts = 4*24*1 # Maximal 1 Start pro 24h
nea_min_betrieb = 4*1 #1 Stunde Maximalbetrieb pro Tag
kap_oel = 15000*heizwert/1000*effizienz #Kapazität Speicher in L

#Abrufwahrscheinlichkeit POS ca. 100h pro Jahr. Negativ volle Abrufwahrscheinilchkeit
nea_afrr_prob_pos = 100/8760

#Arbeitspreis für gewünschte Abrufwahrscheinlichkeit
nea_afrr_ep_neg= 285
nea_afrr_ep_pos= afrr_abruf[afrr_abruf["POS"]<nea_afrr_prob_pos].index.values.astype(int)[0]

nea_afrr_prob_neg = afrr_abruf["NEG"][nea_afrr_ep_neg]

cos_wartung_nea = 40
#Laufzeit begrenzt auf 300h pro Jahr

#Erstellung Kenndaten Kessel, insert FRR per NEA
nea = pd.DataFrame({"nea": [1, 2], 
                    "cos_nea": [nea1_cos,nea2_cos], 
                    "cap_nea": [nea1_nl,nea2_nl],
                    "nea_afrr": [nea_afrr1,nea_afrr2], 
                    "nea_afrr_prob_pos":[nea_afrr_prob_pos,nea_afrr_prob_pos],
                    "nea_afrr_prob_neg":[nea_afrr_prob_neg,nea_afrr_prob_neg], 
                    "nea_afrr_ep_pos":[nea_afrr_ep_pos,nea_afrr_ep_pos],
                    "nea_afrr_ep_neg":[nea_afrr_ep_neg,nea_afrr_ep_neg]})                       
nea.index = np.arange(1, len(nea)+1)
nea.to_csv("nea_data.csv", index_label = "nea", sep=",", header = True)
nea.to_csv(directory +"cos_nea.csv", columns =["cos_nea"], index_label = "nea")
nea.to_csv(directory +"cap_nea.csv", columns =["cap_nea"], index_label = "nea")
nea.to_csv(directory +"nea_afrr.csv", columns =["nea_afrr"], index_label = "nea")
nea.to_csv(directory +"nea_afrr_prob_pos.csv", columns =["nea_afrr_prob_pos"], index_label = "nea")
nea.to_csv(directory +"nea_afrr_prob_neg.csv", columns =["nea_afrr_prob_neg"], index_label = "nea")
nea.to_csv(directory +"nea_afrr_ep_pos.csv", columns =["nea_afrr_ep_pos"], index_label = "nea")
nea.to_csv(directory +"nea_afrr_ep_neg.csv", columns =["nea_afrr_ep_neg"], index_label = "nea")

# Batteriespeicher

#Speicher
battery_num = 4
fcr_cap_power_rating = 1.5
kap_speicher1=2.8
kap_speicher2=2.8
kap_speicher3=2.8
kap_speicher4=2.8
max_leistung1=kap_speicher1/fcr_cap_power_rating*1.25
max_leistung2=kap_speicher2/fcr_cap_power_rating*1.25
max_leistung3=kap_speicher3/fcr_cap_power_rating*1.25
max_leistung4=kap_speicher4/fcr_cap_power_rating*1.25
varcost_batt1 = 0
varcost_batt2 = 0
varcost_batt3 = 0
varcost_batt4 = 0
temp_wg_batt = 2/30/96
bel_wg_batt1 = 0.9
entl_wg_batt1 = 0.9
temp_wg_batt1 = temp_wg_batt
bel_wg_batt2 = 0.9
entl_wg_batt2 = 0.9
temp_wg_batt2 = temp_wg_batt
bel_wg_batt3 = 0.9
entl_wg_batt3 = 0.9
temp_wg_batt3 = temp_wg_batt
bel_wg_batt4 = 0.9
entl_wg_batt4 = 0.9
temp_wg_batt4 = temp_wg_batt
fcr_1 = kap_speicher1/fcr_cap_power_rating
fcr_2 = kap_speicher2/fcr_cap_power_rating
fcr_3 = kap_speicher3/fcr_cap_power_rating
fcr_4 = kap_speicher4/fcr_cap_power_rating

#kap_speicher = 0 #15
#max_leistung_speicher = 0 #12.5

#PRL Batterie
prl_soc_einfluss = -0.009023706/fcr_1
kosten_prl = 0.125673



#Erstellung Kenndaten Batterie, insert FCR per Battery
batterie = pd.DataFrame({"Batterie": [1, 2, 3, 4], 
                         "cos_batt": [varcost_batt1, varcost_batt2, varcost_batt3, varcost_batt4], 
                         "bel_wg_batt": [bel_wg_batt1, bel_wg_batt2, bel_wg_batt3, bel_wg_batt4],
                         "entl_wg_batt": [entl_wg_batt1, entl_wg_batt2, entl_wg_batt3, entl_wg_batt4],
                         "temp_wg_batt": [temp_wg_batt1, temp_wg_batt2, temp_wg_batt3, temp_wg_batt4],
                         "fcr_power":[fcr_1,fcr_2,fcr_3,fcr_4],
                         "max_power":[max_leistung1, max_leistung2, max_leistung3, max_leistung4],
                         "cap":[kap_speicher1, kap_speicher2, kap_speicher3, kap_speicher4]})
batterie.index = np.arange(1, len(batterie)+1)
batterie.to_csv("batterie_data.csv", index_label = "batterie", sep=",", header = True)
batterie.to_csv(directory +"cos_batt.csv", columns =["cos_batt"], index_label = "batterie")
batterie.to_csv(directory +"bel_wg_batt.csv", columns =["bel_wg_batt"], index_label = "batterie")
batterie.to_csv(directory +"entl_wg_batt.csv", columns =["entl_wg_batt"], index_label = "batterie")
batterie.to_csv(directory +"temp_wg_batt.csv", columns =["temp_wg_batt"], index_label = "batterie")
batterie.to_csv(directory +"fcr_power.csv", columns =["fcr_power"], index_label = "batterie")
batterie.to_csv(directory +"max_power.csv", columns =["max_power"], index_label = "batterie")
batterie.to_csv(directory +"cap.csv", columns =["cap"], index_label = "batterie")

# Wärmespeicher und Wärmenetzwerk

#Speicher
heat_storage_liter = 0 #50000
heat_storage = heat_storage_liter*1*4200*(90-75)*2.77778e-10 #Kapazität in MWh von Mauser
hs_cha_eff = 0.8
hs_discha_eff = 0.8 
hs_self_discharge = 0.999479166666667
#Self discharge due to https://www.mdpi.com/1996-1073/8/1/172/pdf
#Speicherdichte 63.8 kWh / m3 @ ∆T = 55K

#Wärmenetzwerk
heating_network_eff = 0.9 # Masatin 

# P2H

#Speicher
p2h = 0.4 #elektrische Wirkleistung
p2h_wirkungsgrad = 0.95

p2h_afrr_ep_neg= 340
p2h_afrr_ep_pos= 34

p2h_afrr_prob_neg=afrr_abruf["NEG"][p2h_afrr_ep_neg]
p2h_afrr_prob_pos=afrr_abruf["POS"][p2h_afrr_ep_pos]

cos_p2h_wartung = 40

# Kältemaschine

#Kältemaschine
cap_cooler = 7.2
#elektrische MWh, die der Eisspeicher umfasst
#COP = 3 
#Eisspeicher = 120m3
#Phasenumwandlung von Wasser (fest-flüssig): 0,06 MWh (therm.) /m³
# eisspeicher = 0#120*0.06/3
cooler_dsm_max_betrieb =2*4 #Maximallänge von 1 Stunde für DSM Maßnahmen

cooler = pd.DataFrame({"cooler": [1], 
                       "cap_cooler": [cap_cooler]})
cooler.to_csv(directory +"cap_cooler.csv", columns =["cap_cooler"], index_label = "cooler")


# In[3]:


# Dateien laden

from datetime import timezone as tz
#Einlesen von Bedarfen und Windeinspeisung
file1 = directory + "EndogeneDaten_aufbereitet.csv"
#daten_waerme=pd.read_excel(filename)
dateparse = lambda x: pd.datetime.strptime(x, "%d.%m.%Y %H:%M")
daten_waerme = pd.read_csv(file1, sep = ";", dtype= {"Wärmebedarf" : np.float64}, parse_dates = {"Timestamp": ["Datum"] },date_parser=dateparse, index_col = "Timestamp", decimal =",")

file2 = directory + "EndogeneDaten.csv"
#daten_strom=pd.read_excel(filename2)
daten_strom = pd.read_csv(file2, sep = ";", dtype= {"Strombedarf" : np.float64}, parse_dates = {"Timestamp": ["Datum"] },date_parser=dateparse, index_col = "Timestamp",decimal =",")
daten_strom=daten_strom.drop_duplicates()

file3 = directory +"Wind.csv"
#daten_strom=pd.read_excel(filename2)
wind = pd.read_csv(file3, sep = ";", dtype= {"Windstromerzeugung" : np.float64}, parse_dates = {"Timestamp": ["Datum"] },date_parser=dateparse, index_col = "Timestamp", decimal =",")
wind[wind["Windstromerzeugung"]<0] = 0

#Einlesen von Temperaturwerten
file4 = directory + "temperature.csv"
temperature = pd.read_csv(file4, sep = ";", dtype= {"Temperature" : np.float64}, parse_dates = {"Timestamp": ["Datum"] },date_parser=dateparse, index_col = "Timestamp", decimal =",")

#Einlesen Schichtpläne 
file5 = directory+"Schichtplan.csv"
schichtplan = pd.read_csv(file5, sep = ";", dtype= {"KB" : np.float64, "MO" : np.float64, "VZ" : np.float64}, parse_dates = {"Timestamp": ["Datum"] },date_parser=dateparse, index_col = "Timestamp", decimal =",")

# #Einlesen von Daten der Kältemaschine
file6= directory+"kaeltemaschine.csv"
kaelte = pd.read_csv(file6, sep = ";", dtype= {"Power" : np.float64}, parse_dates = {"Timestamp": ["DateTime"] },date_parser=dateparse, index_col = "Timestamp", decimal =",")

# #Einlesen von Daten von EVs
dateparse = lambda x: pd.datetime.strptime(x, "%d.%m.%Y %H:%M")
file8 = directory+"2018_leipzig.csv"
bev = pd.read_csv(file8, sep = ";", date_parser=dateparse, decimal =",", parse_dates = ["time_p","time_unp","time_finish"])

#Einlesen von Strompreisen
dateparse = lambda x: pd.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
file7 = directory+"Day-Ahead-Auktion.csv"
strompreis = pd.read_csv(file7, sep = ",", decimal =".", dtype= {"Prices" : np.float64}, parse_dates = {"Timestamp": ["DateTime"] },date_parser=dateparse, index_col = "Timestamp", usecols =["DateTime","Prices"])

#Einlesen von PRL-Preisen
dateparse = lambda x: pd.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
file8 = directory+"PRL.csv"
fcr_prices = pd.read_csv(file8, sep = ",", decimal =".", dtype= {"price" : np.float64}, parse_dates = {"Timestamp": ["date_from"]},date_parser=dateparse, index_col = "Timestamp", usecols =["date_from","price"])

#Einlesen von NEG_SRL Preisen
dateparse = lambda x: pd.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
file9 = directory+"NEG_SRL.csv"
frr_pos_prices = pd.read_csv(file9, sep = ",", decimal =".", dtype= {"price" : np.float64}, parse_dates = {"Timestamp": ["date_from"]},date_parser=dateparse, index_col = "Timestamp", usecols =["date_from","price"])

#Einlesen von POS_SRL Preisen
dateparse = lambda x: pd.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
file10 = directory+"POS_SRL.csv"
frr_neg_prices = pd.read_csv(file10, sep = ",", decimal =".", dtype= {"price" : np.float64}, parse_dates = {"Timestamp": ["date_from"]},date_parser=dateparse, index_col = "Timestamp", usecols =["date_from","price"])

#Einlesen von Erlösen auf dem kurzfristigen Strommarkt
dateparse = lambda x: pd.datetime.strptime(x, "%d.%m.%Y")
file11 = directory+"Arbitrage_Bat_1.4_3.125.csv"
arb_rev_bat = pd.read_csv(file11, sep = ";", decimal =",", dtype= {"Revenue" : np.float64} ,date_parser=dateparse, index_col = "Timestamp", usecols =["Timestamp","Revenue"])

from datetime import datetime, timedelta
bev["time_p"]= bev["time_p"]- timedelta(days=(365-1))
bev["time_unp"]= bev["time_unp"]- timedelta(days=(365-1))
bev["time_finish"]= bev["time_finish"]- timedelta(days=(365-1))
#Round plug time to lower quarter hour and unplug and finish time to higher quarter hour
bev["time_p_round"]= (bev["time_p"]- timedelta(minutes=15/2)).dt.round("15min")  
bev["time_unp_round"]= (bev["time_unp"]+ timedelta(minutes=15/2)).dt.round("15min")  
bev["time_finish_round"]= (bev["time_finish"]+ timedelta(minutes=15/2)).dt.round("15min")  
bev["time_idle [h]"] = pd.to_numeric(bev["time_unp_round"]-bev["time_finish_round"])/(10**9)/3600 #Idle time in hours
bev["time_idle [15m]"] = round(bev["time_idle [h]"]*4,0)
bev["time_plug [h]"] = pd.to_numeric(bev["time_unp_round"]-bev["time_p_round"])/(10**9)/3600 #Plug time in hours
bev["time_plug [15m]"] = round(bev["time_plug [h]"]*4,0)
bev["time_charge [h]"] = pd.to_numeric(bev["time_finish_round"]-bev["time_p_round"])/(10**9)/3600 #charge time in hours
bev["time_charge [15m]"] = round(bev["time_charge [h]"]*4,0)
bev["power"]=(bev["soc_unp"]-bev["soc_p"])*bev["c_battery_size_max"]/100/1000/bev["time_charge [h]"]/0.9
bev = bev[bev["time_plug [h]"]>1]
bev = bev[bev["time_idle [h]"]>=0.5]
bev = bev[bev["power"]>1]
bev = bev.fillna(0)

# date_lower_bound = "2017-11-20"
# date_upper_bound = "2017-12-10"
# mask=(bev["time_p_round"]>= date_lower_bound) & (bev["time_unp_round"] < date_upper_bound)
# ev = bev.loc[mask]
# ev["time_p"]= ev["time_p"]+ timedelta(days=21+365-1)
# ev["time_unp"]= ev["time_unp"]+ timedelta(days=21+365-1)
# ev["time_finish"]= ev["time_finish"]+ timedelta(days=21+365-1)
# ev.to_csv("test.csv")
# bev = pd.concat([bev,ev], ignore_index=True)


# # Definition Optimierungsmodell

# In[ ]:


from pyomo.environ import *
from pyomo.opt import SolverFactory

#Definition of abstract Model
model = AbstractModel()

#Sets of the abstract model
model.t = Set(dimen = 1) #time periods
model.kwk = Set(dimen = 1) #KWK
model.kessel = Set(dimen = 1) #Kessel
model.rlt = Set(dimen = 1) #RLT-Anlagen
model.batterie = Set(dimen = 1)# Batteriepartitionen
model.nea = Set(dimen = 1) #Notstromersatzanlage
model.ev = Set(dimen = 1) #EV charges

#RangeSets of the abstract model
model.nea_minb= RangeSet(0, nea_min_betrieb-1) #Maximalbetrieb NEA
model.kwk_minb= RangeSet(0, kwk_min_betrieb-1) #Mindestbetriebszeit KWK-Anlagen
model.kwk_mins= RangeSet(0, kwk_min_stillstand-1) #Mindestbetriebszeit KWK-Anlagen
model.rlt_dsm_mins= RangeSet(0, rlt_dsm_min_pause-1) #Mindestbetriebszeit KWK-Anlagen
model.rlt_dsm_maxb= RangeSet(0, rlt_dsm_max_betrieb-1) #Maximallänge DSM RLT-Anlagen
model.rl_vz = RangeSet(0, rl_vzr-1)
model.arb_vz = RangeSet(0, arb_vzr-1)
model.cooler_dsm_maxb= RangeSet(0, cooler_dsm_max_betrieb-1) #Maximallänge DSM Kältemaschine

#Parameters of the model
#KWK
model.cos_lin = Param(model.kwk) #marginal cost of generating units
model.varcos_tl = Param(model.kwk) #cost of generating units at part load
model.cos_wartung = Param(model.kwk) # Wartungskosten
model.cap = Param(model.kwk) #capacity of generating units
model.floor = Param(model.kwk) # Part load of generating units
model.f1 = Param(model.kwk) #Stromkennzahl KWKs Teillast
model.f2 = Param(model.kwk) #Stromkennzahl KWKs Nennleistung
model.kwk_fcr = Param(model.kwk) #Präqualifizierte Leistung PRL
model.kwk_afrr = Param(model.kwk) #Präqualifizierte Leistung SRL
model.kwk_afrr_prob_neg = Param(model.kwk) #Abrufwahrscheinlichkeit
model.kwk_afrr_prob_pos = Param(model.kwk) #Abrufwahrscheinlichkeit
model.kwk_afrr_ep_neg = Param(model.kwk) #Arbeitspreis
model.kwk_afrr_ep_pos = Param(model.kwk) #Arbeitspreis

#Kessel
model.cos_lin_kessel = Param(model.kessel) #Linear cost development 
model.cos_kessel_tl = Param(model.kessel) #marginal costs of Kessel at partial production
model.cap_kessel = Param(model.kessel) #capacity of generating units
model.floor_kessel = Param(model.kessel) # Part load of generating units

#NEA
model.cos_nea = Param(model.nea) #marginal costs of NEA
model.cap_nea = Param(model.nea) #capacity of NEA
model.nea_afrr = Param(model.nea) #Präqualifizierte Leistung SRL NEA
model.nea_afrr_prob_neg = Param(model.nea) #Abrufwahrscheinlichkeit
model.nea_afrr_prob_pos = Param(model.nea) #Abrufwahrscheinlichkeit
model.nea_afrr_ep_neg = Param(model.nea) #Arbeitspreis
model.nea_afrr_ep_pos = Param(model.nea) #Arbeitspreis

#HVAC
model.cap_rlt = Param(model.rlt) #max operation point rlt (depending on temperature)
model.floor_rlt = Param(model.rlt) #min operation point rlt
model.winter_rlt = Param(model.rlt) # operation point winter rlt (depending on temperature)
model.rlt_onoff= Param(model.t, model.rlt) #ON/OFF of HVACs
model.rlt_fcr = Param(model.rlt)
model.rlt_afrr_prob_neg = Param(model.rlt) #Abrufwahrscheinlichkeit
model.rlt_afrr_prob_pos = Param(model.rlt) #Abrufwahrscheinlichkeit
model.rlt_afrr_ep_neg = Param(model.rlt) #Arbeitspreis
model.rlt_afrr_ep_pos = Param(model.rlt) #Arbeitspreis

#Batterie
model.cos_batt = Param(model.batterie) #charging efficiency
model.bel_wg_batt = Param(model.batterie) #charging efficiency
model.entl_wg_batt = Param(model.batterie) #discharchging efficiency
model.temp_wg_batt = Param(model.batterie) #Temporal discharge
model.fcr_power = Param(model.batterie) #FCR power
model.max_power = Param(model.batterie) #Max power
model.cap_batterie = Param(model.batterie) #Kapazität
model.arb_rev_bat = Param(model.t)

#Cooler
model.op_cooler=Param(model.t)

#P2H
model.p2h_afrr_call_prob = Param() #Abrufwahrscheinlichkeit

#EV
model.ev_flex = Param(model.ev)
model.charge_length = Param(model.ev)
model.ev_max_power = Param(model.ev)
model.ev_min_power = Param(model.ev)
model.ev_power_plan = Param(model.t, model.ev)
model.ev_energy = Param(model.ev)
model.charge_start_energy = Param(model.ev)
model.charge_finish_energy = Param(model.ev)
model.charge_start = Param(model.ev)
model.charge_plug = Param(model.t, model.ev)
model.fcr_ev = Param(model.ev)
model.bel_wg_ev = Param(model.ev) #charging efficiency
model.entl_wg_ev = Param(model.ev) #discharchging efficiency
model.batt_size_ev = Param(model.ev) #discharchging efficiency

#Other
model.dem_power = Param(model.t) #demand level
model.wind = Param(model.t) #Wind
model.dem_heat = Param(model.t) #heat level
model.power_price = Param(model.t) #Electricity Price (Day-Ahead)
model.fcr_price = Param(model.t) # Power Price FCR
model.frr_neg_price = Param(model.t) # Power Price FRR NEG
model.frr_pos_price = Param(model.t) # Power Price FRR POS
model.temperature = Param(model.t) #Temperaturdaten
model.strombezugskosten = Var(model.t) #Strombezug Commodity
model.peak = Param(initialize=peak)

#Variables of the abstract model
#KWK Variablen
model.power_gen = Var(model.kwk, model.t, domain=NonNegativeReals, initialize=0) #power generation level KWK
model.heat_gen = Var(model.kwk, model.t, domain=NonNegativeReals, initialize=0) #heat generation level KWK
model.gen_onoff= Var(model.kwk, model.t, domain=Binary, initialize=0) #ON/OFF of generating units
model.neg_flex_kwk = Var(model.kwk, model.t, domain=NonNegativeReals, initialize=0) #Negative Flexibilität KWK
model.pos_flex_kwk = Var(model.kwk, model.t, domain=NonNegativeReals, initialize=0) #Positive Flexibilität KWK
model.gen_anf= Var(model.kwk, model.t, domain = Binary, initialize=0) #Anfahrzeit oder nicht
model.gen_auss= Var(model.kwk, model.t, domain=Binary, initialize=0) #Ausschaltzeit oder nicht

#Kessel
model.heat_prod = Var(model.kessel, model.t, domain=NonNegativeReals, initialize=0) #heat production level
model.prod_onoff = Var(model.kessel, model.t, domain=Binary, initialize=0) #ON/OFF of producing units

#NEA
model.nea_gen = Var(model.nea, model.t, domain=NonNegativeReals, initialize=0) #power generation level NEA
model.neg_flex_nea = Var(model.nea, model.t, domain=NonNegativeReals, initialize=0) #Negative Flexibilität NEA
model.pos_flex_nea = Var(model.nea, model.t, domain=NonNegativeReals, initialize=0) #Positive Flexibilität NEA
model.nea_onoff = Var(model.nea, model.t, domain=Binary, initialize=0) #ON/OFF of NEA
model.gen_anf_nea= Var(model.nea, model.t, domain=Binary, initialize=0) #Anfahrzeit oder nicht
# model.oel_speicher = Var(model.t, bounds=(0, kap_oel), initialize = 0) # Speicher
model.nea_onoff_pos_afrr = Var(model.nea, model.t, domain=Binary, initialize=0) #ON/OFF Positive Sekundärregelleistung NEA
model.nea_onoff_neg_afrr = Var(model.nea, model.t, domain=Binary, initialize=0) #ON/OFF Negative Sekundärregelleistung NEA

#HVAC
model.neg_flex_rlt = Var(model.rlt, model.t, domain=NonNegativeReals, initialize=0) #Negative Flexibilität RLT
model.pos_flex_rlt = Var(model.rlt, model.t, domain=NonNegativeReals, initialize=0) #Positive Flexibilität RLT
model.op_rlt = Var(model.rlt, model.t, initialize = 0) # Operation point of HVACs
model.rlt_dsm_pos = Var(model.rlt, model.t, domain=NonNegativeReals, initialize=0) #POS Demand Side Management by HVACS
model.rlt_dsm_neg = Var(model.rlt, model.t, domain=NonNegativeReals, initialize=0) #NEG Demand Side Management by HVACS
model.rlt_dsm_pos_onoff= Var(model.rlt, model.t, domain=Binary, initialize=0) #DSM Usage of HVAC systems POS
model.rlt_dsm_neg_onoff= Var(model.rlt, model.t, domain=Binary, initialize=0) #DSM Usage of HVAC systems NEG
model.rlt_dsm_anf= Var(model.rlt, model.t, domain=Binary, initialize=0) #DSM Anfahren oder nicht

#Cooler
model.neg_flex_cooler = Var(model.t, domain=NonNegativeReals, initialize=0) #Negative Flexibilität Cooler
model.pos_flex_cooler = Var(model.t, domain=NonNegativeReals, initialize=0) #Positive Flexibilität Cooler
model.cooler_dsm_pos = Var(model.t, domain=NonNegativeReals, initialize=0) #POS Demand Side Management by Cooler
model.cooler_dsm_neg = Var(model.t, domain=NonNegativeReals, initialize=0) #NEG Demand Side Management by Cooler
model.cooler_dsm_pos_onoff= Var(model.t, domain=Binary, initialize=0) #DSM Usage of Cooler POS
model.cooler_dsm_neg_onoff= Var(model.t, domain=Binary, initialize=0) #DSM Usage of Cooler NEG

#Recooler
model.rueckk = Var(model.t, domain = NonNegativeReals, bounds=(0,leistung_rueckkuehler), initialize=0) # Rückkühler

#Allgemein
model.grid_power_feed_in = Var(model.t, domain=NonNegativeReals, initialize=0) #Strombezug
model.grid_power_feed_back = Var(model.t, domain=NonNegativeReals, initialize=0) #Rückspeisung
model.renewable = Var(model.t, domain=NonNegativeReals, initialize=0)
model.conventional = Var(model.t, domain=NonNegativeReals, initialize=0)
model.res_buffer = Var(model.t, domain=NonNegativeReals, initialize=0)

#Batterie
model.entladen = Var(model.batterie, model.t, domain = NonNegativeReals, initialize = 0)# Anpassen auf model.batt
model.beladen = Var(model.batterie, model.t, domain = NonNegativeReals, initialize = 0)# Anpassen auf model.batt
model.soc = Var(model.batterie, model.t, domain = NonNegativeReals, initialize = 0) # Speicher
model.netzentgelte= Var(domain = NonNegativeReals, initialize = 0)
model.batterie_fcr_onoff = Var(model.batterie, model.t, domain=Binary, initialize = 0) #Binäre Variable, die entscheidet ob eine Batterie PRL erbringt. 
model.batterie_LO = Var(model.batterie, model.t, domain=Binary, initialize = 0) #Binäre Variable, die entscheidet ob eine Batterie PRL erbringt.
model.fcr_anf = Var(model.batterie, model.t, domain=Integers, initialize = 0)
model.arb_on_off = Var(model.batterie, model.t, domain= Binary, initialize = 0)

#Wärmespeicher
model.heat_charge = Var(model.t, domain = NonNegativeReals, initialize = 0) #Füllen des Wärmespeichers
model.heat_discharge = Var(model.t, domain = NonNegativeReals, initialize = 0) #Leeren des Wärmespeichers
model.heat_store = Var(model.t, domain = NonNegativeReals,bounds = (0,heat_storage), initialize = 0) #Wärmespeicher
model.x_heat_charge = Var(model.t, domain = Binary, initialize = 0)
model.x_heat_discharge = Var(model.t, domain = Binary, initialize = 0)

#EVs
model.ev_dsm_pos_onoff= Var(model.ev, model.t, domain=Binary, initialize=0) #EV Usage of POS
model.ev_dsm_neg_onoff= Var(model.ev, model.t, domain=Binary, initialize=0) #EV Usage of NEG
model.ev_fcr_onoff = Var(model.ev, model.t, domain=Binary, initialize=0) #EV symm FCR
model.ev_soc = Var(model.ev, model.t, domain = NonNegativeReals, initialize = 0) # Speicher EV
model.ev_charge = Var(model.ev, model.t, domain = NonNegativeReals, initialize = 0) # Charge EV
model.ev_discharge = Var(model.ev, model.t, domain = NonNegativeReals, initialize = 0) # Discharge EV
model.ev_dsm_pos = Var(model.ev, model.t, domain = NonNegativeReals, initialize = 0) # Charge EV
model.ev_dsm_neg = Var(model.ev, model.t, domain = NonNegativeReals, initialize = 0) # Discharge EV

#P2H
model.p2h_demand = Var(model.t, domain=NonNegativeReals, bounds = (0,p2h), initialize=0) #Stromverbrauch P2H
model.p2h_prod = Var(model.t, domain=NonNegativeReals, bounds = (0,p2h/p2h_wirkungsgrad), initialize=0) #Wärmeproduktion P2H

#Flexerlöse
model.arb_rev = Var(model.t, domain = NonNegativeReals, initialize = 0)
model.fcr_rev = Var(model.t, domain = NonNegativeReals, initialize = 0)
model.frr_pos_rev = Var(model.t, domain = NonNegativeReals, initialize = 0)
model.frr_neg_rev = Var(model.t, domain = NonNegativeReals, initialize = 0)

#PRL/SRL
model.pos_fcr_kwk = Var(model.kwk, model.t, domain=NonNegativeReals, initialize=0) #PRL Leistung zum Zeitpunkt t
model.neg_fcr_kwk = Var(model.kwk, model.t, domain=NonNegativeReals, initialize=0) #PRL Leistung zum Zeitpunkt t
model.neg_afrr_kwk =  Var(model.kwk, model.t, domain=NonNegativeReals, initialize=0) #Negative SRL Leistung zum Zeitpunkt t
model.pos_afrr_kwk =  Var(model.kwk, model.t, domain=NonNegativeReals, initialize=0) #Positive SRL Leistung zum Zeitpunkt t
model.neg_afrr_nea =  Var(model.nea, model.t, domain=NonNegativeReals, initialize=0) #Negative SRL Leistung zum Zeitpunkt t
model.pos_afrr_nea =  Var(model.nea, model.t, domain=NonNegativeReals, initialize=0) #Positive SRL Leistung zum Zeitpunkt t
model.fcr_batterie = Var(model.batterie, model.t, domain=NonNegativeReals, initialize=0) #PRL Leistung Batterie zum Zeitpunkt t
model.pos_fcr_rlt = Var(model.rlt, model.t, domain=NonNegativeReals, initialize=0) #PRL Leistung HVAC zum Zeitpunkt t
model.neg_fcr_rlt = Var(model.rlt, model.t, domain=NonNegativeReals, initialize=0) #PRL Leistung HVAC zum Zeitpunkt t
model.pos_afrr_rlt = Var(model.rlt, model.t, domain=NonNegativeReals, initialize=0) #SRL Leistung HVAC zum Zeitpunkt t
model.neg_afrr_rlt = Var(model.rlt, model.t, domain=NonNegativeReals, initialize=0) #SRL Leistung HVAC zum Zeitpunkt t
model.neg_afrr_p2h =  Var(model.t, domain=NonNegativeReals, bounds = (0,p2h), initialize=0) #Negative SRL Leistung zum Zeitpunkt t P2H
model.pos_afrr_p2h =  Var(model.t, domain=NonNegativeReals, bounds = (0,p2h), initialize=0) #Positive SRL Leistung zum Zeitpunkt t P2H
model.pos_fcr_p2h =  Var(model.t, domain=NonNegativeReals, bounds = (0,p2h), initialize=0) #PRL Leistung zum Zeitpunkt t P2H
model.neg_fcr_p2h =  Var(model.t, domain=NonNegativeReals, bounds = (0,p2h), initialize=0) #PRL Leistung zum Zeitpunkt t P2H
model.ev_fcr = Var(model.ev, model.t, domain = NonNegativeReals, initialize=0) #EV FCR
model.pos_fcr_ev = Var(model.ev, model.t, domain = NonNegativeReals, initialize=0) #FCR positive 
model.neg_fcr_ev = Var(model.ev, model.t, domain = NonNegativeReals, initialize=0) #FCR negative

model.afrr_energy_rev_pos = Var(model.t, domain = NonNegativeReals , initialize = 0)
model.afrr_energy_rev_neg = Var(model.t, domain = NonNegativeReals, initialize = 0)
model.afrr_call_pos=Var(model.t, domain = NonNegativeReals, initialize = 0)
model.afrr_call_neg=Var(model.t, domain = NonNegativeReals, initialize = 0)

#Summe PRL/SRL
model.fcr = Var(model.t, domain=NonNegativeReals, initialize=0) #PRL Leistung zum Zeitpunkt t of the whole industrial plant
model.pos_afrr = Var(model.t, domain=NonNegativeReals, initialize=0) #PRL Leistung zum Zeitpunkt t of the whole industrial plant
model.neg_afrr = Var(model.t, domain=NonNegativeReals, initialize=0) #PRL Leistung zum Zeitpunkt t of the whole industrial plant

#Summe pro Technologie
model.fcr_kwk = Var(model.kwk, model.t, domain=NonNegativeReals, initialize=0) #PRL Leistung zum Zeitpunkt t
model.fcr_p2h = Var(model.t, domain=NonNegativeReals, bounds = (0,p2h), initialize=0) #PRL Leistung zum Zeitpunkt t P2H
model.fcr_rlt = Var(model.rlt, model.t, domain=NonNegativeReals, initialize=0) #PRL Leistung HVAC zum Zeitpunkt t

#Objective function of the abstract model
def obj_expression(model):
    return   model.netzentgelte*cost_lastspitze + \
               sum(sum(model.varcos_tl[kwk]*model.floor[kwk]*model.gen_onoff[kwk,t]/4
                     + model.cos_lin[kwk]*(model.power_gen[kwk,t]-model.floor[kwk])*model.gen_onoff[kwk,t]/4
                     + model.cos_lin[kwk]*(model.pos_afrr_kwk[kwk,t]*model.kwk_afrr_prob_pos[kwk]-model.neg_afrr_kwk[kwk,t]*model.kwk_afrr_prob_neg[kwk])*model.gen_onoff[kwk,t]/4
                     + cos_anfahr*model.gen_anf[kwk,t]
                     + cos_ausschalt*model.gen_auss[kwk,t]
                     + cos_wartung*model.gen_onoff[kwk,t]/4 for kwk in model.kwk)
                + sum(model.cos_kessel_tl[kessel]*model.floor_kessel[kessel]*model.prod_onoff[kessel,t]
                      + model.cos_lin_kessel[kessel]*(model.heat_prod[kessel,t]-model.floor_kessel[kessel]) 
                      + cos_wartung_kessel*model.prod_onoff[kessel,t] for kessel in model.kessel)/4 
                + sum(model.cos_nea[nea]*model.nea_gen[nea,t]/4
                      + model.cos_nea[nea]*(model.pos_afrr_nea[nea,t]/4*model.nea_afrr_prob_pos[nea]-model.neg_afrr_nea[nea,t]/4*model.nea_afrr_prob_neg[nea])
                      + cos_wartung_nea*model.nea_onoff[nea,t] for nea in model.nea)/4
                + sum(kosten_prl*model.fcr_batterie[batterie,t] for batterie in model.batterie)
                + sum(kosten_prl*model.ev_fcr[ev,t] for ev in model.ev)
                + model.grid_power_feed_in[t]*umlagen_entgelte_extern/4 
                + model.grid_power_feed_in[t]*model.power_price[t]/4
#                 + model.grid_power_feed_in[t]*price_avg/4
                + model.grid_power_feed_back[t]*(cost_rueck/4 - model.power_price[t]/4)
                + model.res_buffer[t]*cost_res_buffer/4
                + model.afrr_call_neg[t]*(umlagen_entgelte_extern)/4
                #- model.afrr_call_pos[t]*(umlagen_entgelte_extern)/4
                - model.frr_pos_rev[t]
                - model.frr_neg_rev[t]
                - model.fcr_rev[t]
                - model.arb_rev[t]
                 for t in model.t)
model.OBJ = Objective(rule=obj_expression)

#Power balance constraint
def power_balance_rule(model,t):
    return sum(model.power_gen[kwk,t] for kwk in model.kwk)     + model.wind[t]     + model.grid_power_feed_in[t]     + sum(model.nea_gen[nea,t]*model.nea_onoff[nea,t] for nea in model.nea)     + sum(model.rlt_dsm_pos[rlt,t] for rlt in model.rlt)     + model.cooler_dsm_pos[t]     + sum(model.entladen[batterie,t]*model.entl_wg_batt[batterie] for batterie in model.batterie)     + sum(model.ev_dsm_pos[ev,t]*model.entl_wg_ev[ev] for ev in model.ev)     == model.cooler_dsm_neg[t]     + sum(model.rlt_dsm_neg[rlt,t] for rlt in model.rlt)     + sum(model.ev_dsm_neg[ev,t]*(1/model.bel_wg_ev[ev]) for ev in model.ev)     + model.dem_power[t]     + model.p2h_demand[t]     + model.grid_power_feed_back[t]     + sum(model.beladen[batterie,t]*(1/model.bel_wg_batt[batterie]) for batterie in model.batterie) 
model.power_balance = Constraint(model.t,rule=power_balance_rule)

#Renewable Power
def renewable_rule(model,t):
    return model.wind[t]     == model.renewable[t]
model.renewable_balance = Constraint(model.t,rule=renewable_rule)

#Renewable Power
def conventional_rule(model,t):
    return sum(model.power_gen[kwk,t] for kwk in model.kwk)     + sum(model.nea_gen[nea,t]*model.nea_onoff[nea,t] for nea in model.nea)     == model.conventional[t]
model.conventional_balance = Constraint(model.t,rule=conventional_rule)

#Heat balance constraint
def heat_balance_rule(model,t):
    return sum(model.heat_gen[kwk,t] for kwk in model.kwk)    + sum(model.heat_prod[kessel,t] for kessel in model.kessel)   + model.p2h_prod[t]     + model.heat_discharge[t]*hs_discha_eff     == model.dem_heat[t]/heating_network_eff     + model.rueckk[t]     + model.heat_charge[t]/hs_cha_eff
model.heat_balance = Constraint(model.t,rule=heat_balance_rule)

# #Wärmespeicher
# #Speicherregel
# def hs_rule(model,t):
#     if t >= 1:
#         return model.heat_store[t] == model.heat_store[(t-1)]-model.heat_discharge[t-1]/4+model.heat_charge[t-1]/4
#     return Constraint.Skip
# model.hs_rule = Constraint(model.t, rule=hs_rule)

def strombezug_rule(model,t):
    return model.strombezugskosten[t]==model.grid_power_feed_in[t]*model.power_price[t]/4  - model.grid_power_feed_back[t]*model.power_price[t]/4     + model.grid_power_feed_in[t]*umlagen_entgelte_extern/4 + model.grid_power_feed_back[t]*cost_rueck/4     + model.res_buffer[t]*cost_res_buffer/4
model.strombezug = Constraint(model.t, rule=strombezug_rule)

#Speicherregel 2
def hs_rule2(model,t):
    if t==0:
        return model.heat_store[t] == heat_storage*0.5
    elif t==len(zeitreihen.index)-1:
        return model.heat_store[t] == heat_storage*0.5
    return model.heat_store[t] == model.heat_store[(t-1)]*hs_self_discharge-model.heat_discharge[t-1]/4+model.heat_charge[t-1]/4
model.hs_rule2 = Constraint(model.t, rule=hs_rule2)

#Wärmespeicher füllen
def hs_cha_rule(model,t):
    return model.heat_charge[t] <= model.x_heat_charge[t]*heat_storage
model.hs_cha_rule = Constraint(model.t, rule=hs_cha_rule)

#Wärmespeicher leeren
def hs_discha_rule(model,t):
    return model.heat_discharge[t] <= model.x_heat_discharge[t]*heat_storage
model.hs_discha_rule = Constraint(model.t, rule=hs_discha_rule)

#Wärmespeicher Managemant
def hs_cha_discha_rule(model,t):
    return model.x_heat_discharge[t]+model.x_heat_charge[t] <= 1
model.hs_cha_discha_rule = Constraint(model.t, rule=hs_cha_discha_rule)

#Rückkühler ausschließliche Nutzung für KWK1
def rk_kwk1_rule(model,t):
    return model.rueckk[t] <= leistung_rueckkuehler*model.gen_onoff[1,t]
model.rk_kwk1_rule = Constraint(model.t, rule=rk_kwk1_rule)

#KWK
#Power-heat balance constraint KWK
def power_heat_balance_kwk_rule(model,kwk,t):
    return model.heat_gen[kwk,t] - model.f1[kwk]*model.power_gen[kwk,t]     - model.f1[kwk]*(model.pos_afrr_kwk[kwk,t]*model.kwk_afrr_prob_pos[kwk]-model.neg_afrr_kwk[kwk,t]*model.kwk_afrr_prob_neg[kwk])     - model.f2[kwk]*model.gen_onoff[kwk,t] == 0
model.power_heat_balance_kwk = Constraint(model.kwk,model.t,rule=power_heat_balance_kwk_rule)

#Maxlast KWK
def max_gen_rule(model,kwk,t):
    return model.power_gen[kwk,t] <= model.cap[kwk]*model.gen_onoff[kwk,t]
model.max_gen = Constraint(model.kwk,model.t,rule=max_gen_rule)

#Teillast KWK
def min_gen_rule(model,kwk,t):
    return model.power_gen[kwk,t] >= model.floor[kwk]*model.gen_onoff[kwk,t]
model.min_gen = Constraint(model.kwk,model.t,rule=min_gen_rule)

#Anfahrbedingung KWK
def anfahr_rule(model,kwk,t):
    if t >= 1:
            return model.gen_anf[kwk,t] >= model.gen_onoff[kwk,t]-model.gen_onoff[kwk,t-1]
    return Constraint.Skip
model.anfahr_rule = Constraint(model.kwk, model.t, rule=anfahr_rule)

#Anfahrbedingung KWK
def ausschalt_rule(model,kwk,t):
    if t >= 1:
            return model.gen_auss[kwk,t] >= model.gen_onoff[kwk,t-1]-model.gen_onoff[kwk,t]
    return Constraint.Skip
model.ausschalt_rule = Constraint(model.kwk, model.t, rule=ausschalt_rule)

#Mindestbetriebszeit KWK 4*15min 
def mindestbetrieb_rule(model,kwk,t):
    if t <= len(zeitreihen.index)-kwk_min_betrieb and t>=1:
        return sum(model.gen_onoff[kwk,t+kwk_minb] for kwk_minb in model.kwk_minb)     >= model.gen_anf[kwk,t]*(kwk_min_betrieb)#*(model.gen_onoff[kwk,t]-model.gen_onoff[kwk,t-1])
    return Constraint.Skip
model.mb_rule = Constraint(model.kwk, model.t, rule = mindestbetrieb_rule)

#Mindeststillstandszeit KWK 4*15min 
def mindeststillstand_rule(model,kwk,t):
    if t <= len(zeitreihen.index)-kwk_min_stillstand and t>=1:
        return sum(model.gen_onoff[kwk,t+kwk_mins] for kwk_mins in model.kwk_mins)         <= (1-model.gen_auss[kwk,t])*(kwk_min_stillstand)#*(1+model.gen_onoff[kwk,t]-model.gen_onoff[kwk,t-1])
    return Constraint.Skip
model.ms_rule = Constraint(model.kwk, model.t, rule = mindeststillstand_rule)

#Maximale Anzahl an Starts
def max_start_rule(model,kwk,t):
    return sum(model.gen_anf[kwk,t] for t in model.t) <= kwk_maxstarts
model.max_start_rule = Constraint(model.kwk, model.t,rule=max_start_rule)

#Max NEG Flex
def max_neg_flex_kwk_rule(model,kwk,t):
    return model.neg_flex_kwk[kwk,t] == model.power_gen[kwk,t]-model.floor[kwk]*model.gen_onoff[kwk,t]
model.max_neg_flex_rule = Constraint(model.kwk, model.t,rule=max_neg_flex_kwk_rule)

#Max POS Flex
def max_pos_flex_kwk_rule(model,kwk,t):
    return model.pos_flex_kwk[kwk,t] == model.cap[kwk]*model.gen_onoff[kwk,t]-model.power_gen[kwk,t]
model.max_pos_flex_rule = Constraint(model.kwk, model.t,rule=max_pos_flex_kwk_rule)

#Negative aFRR KWK
def neg_afrr_kwk_rule(model,kwk,t):
    return model.neg_afrr_kwk[kwk,t]<=model.kwk_afrr[kwk]
model.neg_afrr_kwk_rule = Constraint(model.kwk, model.t, rule=neg_afrr_kwk_rule)

#Positive aFRR KWK
def pos_afrr_kwk_rule(model,kwk,t):
    return model.pos_afrr_kwk[kwk,t]<=model.kwk_afrr[kwk]
model.pos_afrr_kwk_rule = Constraint(model.kwk, model.t, rule=pos_afrr_kwk_rule)

#Positive aFRR KWK Kopplung an Rückkühler
def pos_afrr_kwk_rule_v2(model,kwk,t):
    return sum(model.pos_afrr_kwk[kwk,t] for kwk in model.kwk) + model.pos_afrr_p2h[t]<=leistung_rueckkuehler + sum(model.heat_prod[kessel,t] for kessel in model.kessel)  
model.pos_afrr_kwk_rule_v2 = Constraint(model.t, model.kwk, rule=pos_afrr_kwk_rule_v2)

#FCR KWK
def pos_fcr_kwk_rule(model,kwk,t):
    return model.pos_fcr_kwk[kwk,t]<=model.kwk_fcr[kwk]
model.pos_fcr_kwk_rule = Constraint(model.kwk, model.t, rule=pos_fcr_kwk_rule)

#FCR KWK
def neg_fcr_kwk_rule(model,kwk,t):
    return model.neg_fcr_kwk[kwk,t]<=model.kwk_fcr[kwk]
model.neg_fcr_kwk_rule = Constraint(model.kwk, model.t, rule=neg_fcr_kwk_rule)

#P2H
#Power-2-heat balance constraint
def power_to_heat_rule(model,t):
    return model.p2h_prod[t]/p2h_wirkungsgrad - model.p2h_demand[t]     - (model.neg_afrr_p2h[t]*p2h_afrr_prob_neg-model.pos_afrr_p2h[t]*p2h_afrr_prob_pos)     == 0
model.power_to_heat = Constraint(model.t,rule=power_to_heat_rule)

#Maxlast Kessel
def max_prod_rule(model,kessel,t):
    return model.heat_prod[kessel,t] <= model.prod_onoff[kessel,t]*model.cap_kessel[kessel]
model.max_prod = Constraint(model.kessel,model.t,rule=max_prod_rule)

#Teillast Kessel
def min_prod_rule(model,kessel,t):
    return model.heat_prod[kessel,t] >= model.prod_onoff[kessel,t]*model.floor_kessel[kessel]
model.min_prod = Constraint(model.kessel,model.t,rule=min_prod_rule)

#Lüftungsanlage
#Arbeitspunkt abhängig von der Temperatur 
def rlt_op_rule(model,rlt,t): 
    if model.temperature[t] < 10:
        return model.op_rlt[rlt,t]==model.winter_rlt[rlt]*model.rlt_onoff[t,rlt]
    elif model.temperature[t] > 30:
        return model.op_rlt[rlt,t]==model.cap_rlt[rlt]*model.rlt_onoff[t,rlt]
    else:
        return model.op_rlt[rlt,t]==(model.winter_rlt[rlt]+(model.temperature[t]-10)/(30-10)*(model.cap_rlt[rlt]-model.winter_rlt[rlt]))*model.rlt_onoff[t,rlt]
model.rlt_op = Constraint(model.rlt, model.t, rule = rlt_op_rule)

#Max NEG Flex
def max_neg_flex_rlt_rule(model,rlt,t):
    return model.neg_flex_rlt[rlt,t] == model.cap_rlt[rlt]*model.rlt_onoff[t,rlt]-model.op_rlt[rlt,t]
model.max_neg_flex_rlt = Constraint(model.rlt, model.t,rule=max_neg_flex_rlt_rule)

#Max POS Flex
def max_pos_flex_rlt_rule(model,rlt,t):
    return model.pos_flex_rlt[rlt,t] == model.op_rlt[rlt,t]-model.floor_rlt[rlt]*model.rlt_onoff[t,rlt]
model.max_pos_flex_rlt = Constraint(model.rlt, model.t,rule=max_pos_flex_rlt_rule)

def rlt_pos_dsm_milp_rule(model,rlt,t):
    return model.rlt_dsm_pos[rlt,t] <= model.rlt_dsm_pos_onoff[rlt,t]*model.cap_rlt[rlt]
model.rlt_pos_dsm_milp = Constraint(model.rlt, model.t,rule=rlt_pos_dsm_milp_rule)

def rlt_neg_dsm_milp_rule(model,rlt,t):
    return model.rlt_dsm_neg[rlt,t] <= model.rlt_dsm_neg_onoff[rlt,t]*model.cap_rlt[rlt]
model.rlt_neg_dsm_milp = Constraint(model.rlt, model.t,rule=rlt_neg_dsm_milp_rule)

#Exklusive Nutzung DSM POS/NEG by HVACs
def rlt_dsm_exclusion_rule(model,rlt,t):
    return model.rlt_dsm_neg_onoff[rlt,t] + model.rlt_dsm_pos_onoff[rlt,t] <= 1
model.rlt_dsm_exclusion = Constraint(model.rlt, model.t,rule=rlt_dsm_exclusion_rule)

#Ausgleichender Nutzen DSM
def maximalbetrieb_rlt_dsm_rule(model,rlt,t):
    if t <= (len(zeitreihen.index)-rlt_dsm_max_betrieb) and t%rlt_dsm_max_betrieb==0:
        return sum(model.rlt_dsm_pos[rlt,t+rlt_dsm_maxb] for rlt_dsm_maxb in model.rlt_dsm_maxb) == sum(model.rlt_dsm_neg[rlt,t+rlt_dsm_maxb]*0.95 for rlt_dsm_maxb in model.rlt_dsm_maxb)
    else:
        return model.rlt_dsm_pos[rlt,t] == 0
model.maxb_rlt_dsm = Constraint(model.rlt, model.t, rule = maximalbetrieb_rlt_dsm_rule)

# #Mindeststillstandszeit DSM RLT 4*15min 
# def dsm_pos_pause_rule(model,rlt,t):
#     if t <= len(zeitreihen.index)-rlt_dsm_min_pause and t>=1:
#         return sum(model.rlt_dsm_pos_onoff[rlt,t+rlt_dsm_mins] for rlt_mins in model.rlt_dsm_mins) \
#         <= (1-rlt_dsm_pos_onoff[rlt,t-1]-rlt_dsm_pos_onoff[rlt,t])*(rlt_dsm_min_pause)
#     return Constraint.Skip
# model.dsm_pause_rule = Constraint(model.rlt, model.t, rule = dsm_pos_pause_rule)

# #Mindeststillstandszeit DSM RLT 4*15min 
# def dsm_neg_pause_rule(model,rlt,t):
#     if t <= len(zeitreihen.index)-rlt_dsm_min_pause and t>=1:
#         return sum(model.rlt_dsm_pos_onoff[rlt,t+rlt_dsm_mins] for rlt_mins in model.rlt_dsm_mins) \
#         <= (1-rlt_dsm_pos_onoff[rlt,t-1]-rlt_dsm_pos_onoff[rlt,t])*(rlt_dsm_min_pause)
#     return Constraint.Skip
# model.dsm_pause_rule = Constraint(model.rlt, model.t, rule = dsm_neg_pause_rule)

##Kältemaschine
#Maximale Abrufzeit von bestimmter Energiemenge
#Aufteilung Flexibilität HVACs
#Max NEG Flex
def max_neg_flex_cooler_rule(model,t):
    return model.neg_flex_cooler[t] == cap_cooler-model.op_cooler[t]
model.max_neg_flex_cooler = Constraint(model.t,rule=max_neg_flex_cooler_rule)

#Max POS Flex
def max_pos_flex_cooler_rule(model,t):
    return model.pos_flex_cooler[t] == model.op_cooler[t]
model.max_pos_flex_cooler = Constraint(model.t,rule=max_pos_flex_cooler_rule)

def cooler_pos_dsm_rule(model,t):
    return model.cooler_dsm_pos[t]<=model.pos_flex_cooler[t]*10/max(model.temperature[t],10)#model.cooler_dsm_pos_onoff[t]*0.2*cap_cooler*10/max(model.temperature[t],10)
model.cooler_pos_dsm = Constraint(model.t,rule=cooler_pos_dsm_rule)

def cooler_neg_dsm_rule(model,t):
    return model.cooler_dsm_neg[t]<=model.neg_flex_cooler[t]*10/max(model.temperature[t],10)#model.cooler_dsm_neg_onoff[t]*0.2*cap_cooler*10/max(model.temperature[t],10)
model.cooler_neg_dsm = Constraint(model.t,rule=cooler_neg_dsm_rule)

# #Exklusive Nutzung DSM POS/NEG by Coolers
# def cooler_dsm_exclusion(model,t):
#     return model.cooler_dsm_pos_onoff[t] + model.cooler_dsm_neg_onoff[t] <= 1
# model.cooler_dsm_exclusion = Constraint(model.t,rule=cooler_dsm_exclusion)

#Ausgleichender Nutzen Cooler
def maximalbetrieb_cooler_dsm_rule(model,t):
    if t <= (len(zeitreihen.index)-cooler_dsm_max_betrieb) and t%cooler_dsm_max_betrieb==0:
        return sum(model.cooler_dsm_pos[t+cooler_dsm_maxb] for cooler_dsm_maxb in model.cooler_dsm_maxb) == sum(model.cooler_dsm_neg[t+cooler_dsm_maxb]*0.9 for cooler_dsm_maxb in model.cooler_dsm_maxb)
    else:
        return model.cooler_dsm_pos[t] == 0
model.maxb_cooler_dsm = Constraint(model.t, rule = maximalbetrieb_cooler_dsm_rule)

# #Eisspeicher
# def boundaries_eisspeicher_rule(model,t):
#     if t >= 1 and t <= len(zeitreihen.index)-1:
#         return model.eisspeicher[t] == model.eisspeicher[t-1]*0.95+model.cooler_dsm_neg[t]/4-model.cooler_dsm_pos[t]/4
#     else:
#         return model.eisspeicher[t] == 0
# model.boundaries_eisspeicher = Constraint(model.t, rule=boundaries_eisspeicher_rule)

##EV - done
def ev_power_rule(model,ev,t):
    return model.ev_charge[ev,t]-model.ev_discharge[ev,t] == model.ev_power_plan[t,ev] + model.ev_dsm_neg[ev,t]     - model.ev_dsm_pos[ev,t]
model.ev_power_rule = Constraint(model.ev, model.t, rule = ev_power_rule)

#Positives DSM - done
def ev_pos_dsm_rule(model,ev,t):
    return model.ev_dsm_pos[ev,t] <= (model.ev_max_power[ev]-model.ev_min_power[ev])*model.ev_dsm_pos_onoff[ev,t]
model.ev_pos_dsm_rule = Constraint(model.ev, model.t, rule = ev_pos_dsm_rule)

#Negatives DSM - done
def ev_neg_dsm_rule(model,ev,t):
    return model.ev_dsm_neg[ev,t] <= (model.ev_max_power[ev]-model.ev_min_power[ev])*model.ev_dsm_neg_onoff[ev,t]
model.ev_neg_dsm_rule = Constraint(model.ev, model.t, rule = ev_neg_dsm_rule)

#Auschließendes DSM und FCR 
def ev_bin_dsm_rule(model,ev,t):
    return model.ev_dsm_neg_onoff[ev,t] + model.ev_dsm_pos_onoff[ev,t] + model.ev_fcr_onoff[ev,t] <= 1
model.ev_bin_dsm_rule = Constraint(model.ev, model.t, rule = ev_bin_dsm_rule)

#Charge EV - done
def ev_charge_rule(model,ev,t):
#     if t == int(model.charge_start[ev]+model.charge_length[ev]):
#         return model.ev_charge[ev,t] == 0
#     else:
    return model.ev_charge[ev,t] <= model.ev_max_power[ev]*model.charge_plug[t,ev]
model.ev_charge_rule = Constraint(model.ev, model.t, rule = ev_charge_rule)

#Discharge EV - done
def ev_discharge_rule(model,ev,t):
#     if t == int(model.charge_start[ev]+model.charge_length[ev]):
#         return model.ev_discharge[ev,t] == 0
#     else:
    return model.ev_discharge[ev,t] <= -model.ev_min_power[ev]*model.charge_plug[t,ev]
model.ev_discharge_rule = Constraint(model.ev, model.t, rule = ev_discharge_rule)

#EV SOC - done
def ev_soc_rule(model,ev,t):
    if t >= 1:
        return model.ev_soc[ev,t] == model.ev_soc[ev,(t-1)] + model.ev_charge[ev,(t-1)]/4*model.bel_wg_ev[ev]     -model.ev_discharge[ev,(t-1)]/4/model.entl_wg_ev[ev]
    return Constraint.Skip
model.ev_soc_rule = Constraint(model.ev, model.t, rule=ev_soc_rule)

#EV SOC -done 
def min_max_soc_rule(model,ev,t):
    if t <= int(model.charge_start[ev]):
        return model.ev_soc[ev,t] == model.charge_start_energy[ev]
    elif t > int(model.charge_start[ev]+model.charge_length[ev]):
        return model.ev_soc[ev,t] == model.charge_finish_energy[ev]
    return Constraint.Skip
model.min_max_soc_rule = Constraint(model.ev, model.t, rule=min_max_soc_rule)

# #Upper SOC bound - done
# def upper_ev_soc_rule(model,ev,t):
#     return model.ev_soc[ev,t] <= model.batt_size_ev[ev]
# model.upper_ev_soc_rule = Constraint(model.ev, model.t, rule=upper_ev_soc_rule)

def fcr_lower_soc_rule(model,ev,t):
    if t >= int(model.charge_start[ev]) and t < int(model.charge_start[ev]+model.charge_length[ev]):
        return model.ev_soc[ev,t] >= model.ev_fcr_onoff[ev,t]*1/3*model.batt_size_ev[ev]
    return Constraint.Skip
model.fcr_lower_soc_rule = Constraint(model.ev, model.t, rule=fcr_lower_soc_rule)

def fcr_upper_soc_rule(model,ev,t):
    if t >= int(model.charge_start[ev]) and t < int(model.charge_start[ev]+model.charge_length[ev]):
        return model.ev_soc[ev,t] <= model.ev_fcr_onoff[ev,t]*2/3*model.batt_size_ev[ev] + (1-model.ev_fcr_onoff[ev,t])*model.batt_size_ev[ev]
    return Constraint.Skip
model.fcr_upper_soc_rule = Constraint(model.ev, model.t, rule=fcr_upper_soc_rule)

def fcr_ev_rule(model,ev,t):
    return model.ev_fcr[ev,t] <= model.ev_fcr_onoff[ev,t]*model.fcr_ev[ev]*model.charge_plug[t,ev]
model.fcr_ev_rule = Constraint(model.ev, model.t, rule=fcr_ev_rule)

def pos_fcr_ev_rule(model,ev,t):
    return model.ev_fcr[ev,t] == model.pos_fcr_ev[ev,t]
model.pos_fcr_ev_rule = Constraint(model.ev, model.t, rule=pos_fcr_ev_rule)

def neg_fcr_ev_rule(model,ev,t):
    return model.ev_fcr[ev,t] == model.neg_fcr_ev[ev,t]
model.neg_fcr_ev_rule = Constraint(model.ev, model.t, rule=neg_fcr_ev_rule)

# #Positive Flex
# def ev_pos_flex_rule(model,ev,t):
#     return model.pos_fcr_ev[ev,t] \
#     <= (model.ev_charge[ev,t] -model.ev_discharge[ev,t] - model.ev_min_power[ev])*model.charge_plug[t,ev]
# model.ev_pos_flex_rule = Constraint(model.ev, model.t, rule = ev_pos_flex_rule)

# #Negative Flex
# def ev_neg_flex_rule(model,ev,t):
#     return model.neg_fcr_ev[ev,t] \
#     <= (model.ev_max_power[ev] - model.ev_charge[ev,t] - model.ev_discharge[ev,t])*model.charge_plug[t,ev]
# model.ev_neg_flex_rule = Constraint(model.ev, model.t, rule = ev_neg_flex_rule)

##NEA
#Maxlast NEA #Ungleichheit setzen für kontinuierliche Regelung
def max_gen_nea_rule(model,nea,t):
    return model.nea_gen[nea,t] == model.cap_nea[nea]*model.nea_onoff[nea,t]
model.max_gen_nea = Constraint(model.nea,model.t,rule=max_gen_nea_rule)

# NEG Flex NEA
def max_neg_flex_nea_rule(model,nea,t):
    return model.neg_afrr_nea[nea,t] == model.nea_gen[nea,t]*model.nea_onoff_neg_afrr[nea,t]
model.max_neg_flex_nea = Constraint(model.nea, model.t,rule=max_neg_flex_nea_rule)

# POS Flex NEA
def max_pos_flex_nea_rule(model,nea,t):
    return model.pos_afrr_nea[nea,t] == (model.cap_nea[nea]-model.nea_gen[nea,t])*model.nea_onoff_neg_afrr[nea,t]
model.max_pos_flex_nea = Constraint(model.nea, model.t,rule=max_pos_flex_nea_rule)

# #Negative Flexibilität #Ungleichheit setzen für kontinuierliche Regelung
# def neg_flex_nea_rule(model,nea,t):
#     return model.neg_afrr_nea[nea,t] == model.neg_flex_nea[nea,t]*model.nea_onoff_neg_afrr[nea,t]
# model.neg_flex_nea_rule = Constraint(model.nea, model.t, rule=neg_flex_nea_rule)

# #Positive Flexibilität #Ungleichheit setzen für kontinuierliche Regelung
# def pos_flex_nea_rule(model,nea,t):
#     return model.pos_afrr_nea[nea,t] == model.pos_flex_nea[nea,t]*model.nea_onoff_pos_afrr[nea,t]
# model.pos_flex_nea_rule = Constraint(model.nea, model.t, rule=neg_flex_nea_rule)

#Negative aFRR NEA 
def neg_afrr_nea_rule(model,nea,t):
    return model.neg_afrr_nea[nea,t]<=model.nea_afrr[nea]
model.neg_afrr_nea_rule = Constraint(model.nea, model.t, rule=neg_afrr_nea_rule)

#Positive aFRR NEA 
def pos_afrr_nea_rule(model,nea,t):
    return model.pos_afrr_nea[nea,t]<=model.nea_afrr[nea]
model.pos_afrr_nea_rule = Constraint(model.nea, model.t, rule=pos_afrr_nea_rule)

#Mindestbetriebszeit NEA 4*15min 
def mindestbetrieb_nea_rule(model,nea,t):
    if t <= len(zeitreihen.index)-nea_min_betrieb and t>=1:
        return sum(model.nea_onoff[nea,t+nea_minb] for nea_minb in model.nea_minb)     >= (nea_min_betrieb)*(model.nea_onoff[nea,t]-model.nea_onoff[nea,t-1])
    return Constraint.Skip
model.mb_nea_rule = Constraint(model.nea, model.t, rule = mindestbetrieb_nea_rule)

# #Oelspeicher
# def speicher_rule(model,nea,t):
#     if t >= 1 and t <= len(zeitreihen.index)-1:
#         return model.oel_speicher[t] == model.oel_speicher[(t-1)] \
#         -sum(model.nea_gen[nea,t]/4 for nea in model.nea) \
#         -sum(model.pos_afrr_nea[nea,t]/4*model.nea_afrr_prob_pos[nea]-model.neg_afrr_nea[nea,t]/4*model.nea_afrr_prob_neg[nea] for nea in model.nea)
#     return Constraint.Skip
# model.speicher_rule = Constraint(model.nea, model.t, rule=speicher_rule)

def einsatzzeit(model,nea,t):
    return sum(model.nea_onoff[nea,t] for t in model.t) <= 4#*5.5
model.einsatzzeit = Constraint(model.nea, model.t, rule = einsatzzeit)


# #Wöchentlicher Betankungsvorgang 
# def fill_rule(model,t):
#     if t % 672*2 == 0: 
#         return model.oel_speicher[t] == kap_oel
#     return Constraint.Skip
# model.fill_rule = Constraint(model.t, rule=fill_rule)

##Batterie
#Speicher SOC
def soc_rule(model,batterie,t):
    if t >= 1:
        return model.soc[batterie,t] == model.soc[batterie,(t-1)]         -model.soc[batterie,(t-1)]*model.temp_wg_batt[batterie]*model.batterie_LO[batterie,t]         -model.batterie_LO[batterie,t]*model.entladen[batterie,t]/4         +model.batterie_LO[batterie,t]*model.beladen[batterie,t]/4 
    return Constraint.Skip
model.soc_rule = Constraint(model.batterie, model.t, rule=soc_rule)

#Charging Power Battery
def charge_rule(model,batterie,t):
    if t ==0:
        return model.beladen[batterie,t] == 0
    else:
        return model.beladen[batterie,t] <=  model.max_power[batterie]*model.batterie_LO[batterie,t]
model.charge_rule = Constraint(model.batterie, model.t, rule=charge_rule)

#Discharging Power Battery
def discharge_rule(model,batterie,t):
    if t == 0: 
        return model.entladen[batterie,t] == 0
    else:
        return model.entladen[batterie,t] <= model.max_power[batterie]*model.batterie_LO[batterie,t]
model.discharge_rule = Constraint(model.batterie, model.t, rule=discharge_rule)

#FCR Power Battery
def fcr_battery_rule(model,batterie,t):
    return model.fcr_batterie[batterie,t] <= model.fcr_power[batterie]*model.batterie_fcr_onoff[batterie,t]
model.fcr_battery_rule = Constraint(model.batterie, model.t, rule=fcr_battery_rule)

#Kein Value Stacking
def battery_fcr_exclusion(model,batterie,t):
    return model.batterie_fcr_onoff[batterie,t] + model.batterie_LO[batterie,t] + model.arb_on_off[batterie,t] <= 1
model.battery_fcr_exclusion = Constraint(model.batterie, model.t,rule=battery_fcr_exclusion)

def max_soc_rule(model,batterie,t):
    if t >= 1 and t <= len(zeitreihen.index)-1:
        return model.soc[batterie,t] <= model.batterie_fcr_onoff[batterie,t]*2/3*model.cap_batterie[batterie]    + (1-model.batterie_fcr_onoff[batterie,t])*model.cap_batterie[batterie]
    return Constraint.Skip
model.max_soc_rule = Constraint(model.batterie, model.t, rule=max_soc_rule)

def min_soc_rule(model,batterie,t):
    if t >= 1 and t < len(zeitreihen.index)-1:
        return model.soc[batterie,t] >= model.batterie_fcr_onoff[batterie,t]*1/3*model.cap_batterie[batterie]
    elif t == len(zeitreihen.index)-1:
        return model.soc[batterie,t] >= model.cap_batterie[batterie]*0.5
    elif t== 0:
        return model.soc[batterie,t] == model.cap_batterie[batterie]*0.5
    return Constraint.Skip
model.min_soc_rule = Constraint(model.batterie, model.t, rule=min_soc_rule)

#Arbitrage Mindestvermarktung
def arb_mindestvm_rule(model,t, batterie,arb_vz):
    if t < len(zeitreihen.index)-1 and t%arb_vzr==0:
        return model.arb_on_off[batterie, t] == model.arb_on_off[batterie, t+arb_vz]
    return Constraint.Skip
model.arb_mindestvm_rule = Constraint(model.t, model.batterie, model.arb_vz, rule = arb_mindestvm_rule)

#Peak Shaving
def ps_rule(model,t):
    return model.grid_power_feed_in[t]-peak <= model.netzentgelte
model.ps_rule = Constraint(model.t, rule=ps_rule) 

#Renewable Power
def res_buffer_rule(model,t):
    return model.grid_power_feed_back[t]- model.conventional[t] <= model.res_buffer[t]
model.res_buffer_balance = Constraint(model.t,rule=res_buffer_rule)
    
#FRR
def pos_afrr_balance_rule(model,t):
    return sum(model.pos_afrr_kwk[kwk,t] for kwk in model.kwk)     + sum(model.pos_afrr_nea[nea,t] for nea in model.nea)     + model.pos_afrr_p2h[t]     + sum(model.pos_afrr_rlt[rlt,t] for rlt in model.rlt)     ==     model.pos_afrr[t]
model.pos_afrr_balance = Constraint(model.t,rule=pos_afrr_balance_rule)

def neg_afrr_balance_rule(model,t):
    return sum(model.neg_afrr_kwk[kwk,t] for kwk in model.kwk)     + sum(model.neg_afrr_nea[nea,t] for nea in model.nea)     + model.neg_afrr_p2h[t]     + sum(model.neg_afrr_rlt[rlt,t] for rlt in model.rlt)     ==     model.neg_afrr[t]
model.neg_afrr_balance = Constraint(model.t,rule=neg_afrr_balance_rule)

def afrr_call_prob_pos_rule(model, t):
    return sum(model.pos_afrr_kwk[kwk,t]/4*model.kwk_afrr_prob_pos[kwk]*model.kwk_afrr_ep_pos[kwk] for kwk in model.kwk)     + sum(model.pos_afrr_nea[nea,t]/4*model.nea_afrr_prob_pos[nea]*model.nea_afrr_ep_pos[nea] for nea in model.nea)     + sum(model.pos_afrr_rlt[rlt,t]/4*model.rlt_afrr_prob_pos[rlt]*model.rlt_afrr_ep_pos[rlt] for rlt in model.rlt)     + model.pos_afrr_p2h[t]/4*p2h_afrr_prob_pos*p2h_afrr_ep_pos     == model.afrr_energy_rev_pos[t]
model.afrr_call_prob_pos_rule = Constraint(model.t,rule=afrr_call_prob_pos_rule)

def afrr_call_prob_neg_rule(model, t):
    return sum(model.neg_afrr_kwk[kwk,t]/4*model.kwk_afrr_prob_neg[kwk]*model.kwk_afrr_ep_neg[kwk] for kwk in model.kwk)     + sum(model.neg_afrr_nea[nea,t]/4*model.nea_afrr_prob_neg[nea]*model.nea_afrr_ep_neg[nea] for nea in model.nea)     + sum(model.neg_afrr_rlt[rlt,t]/4*model.rlt_afrr_prob_neg[rlt]*model.rlt_afrr_ep_neg[rlt] for rlt in model.rlt)     + model.neg_afrr_p2h[t]/4*p2h_afrr_prob_neg*p2h_afrr_ep_neg     == model.afrr_energy_rev_neg[t]
model.afrr_call_prob_neg_rule = Constraint(model.t,rule=afrr_call_prob_neg_rule)

def afrr_call_pos_rule(model, t):
    return sum(model.pos_afrr_kwk[kwk,t]*model.kwk_afrr_prob_pos[kwk] for kwk in model.kwk)     + sum(model.pos_afrr_nea[nea,t]*model.nea_afrr_prob_pos[nea] for nea in model.nea)     + sum(model.pos_afrr_rlt[rlt,t]*model.rlt_afrr_prob_pos[rlt] for rlt in model.rlt)     + model.pos_afrr_p2h[t]*p2h_afrr_prob_pos    == model.afrr_call_pos[t]
model.afrr_call_pos_rule = Constraint(model.t,rule=afrr_call_pos_rule)

def afrr_call_neg_rule(model, t):
    return sum(model.neg_afrr_kwk[kwk,t]*model.kwk_afrr_prob_neg[kwk] for kwk in model.kwk)     + sum(model.neg_afrr_nea[nea,t]*model.nea_afrr_prob_neg[nea] for nea in model.nea)     + sum(model.neg_afrr_rlt[rlt,t]*model.rlt_afrr_prob_neg[rlt] for rlt in model.rlt)     + model.neg_afrr_p2h[t]*p2h_afrr_prob_neg    == model.afrr_call_neg[t]
model.afrr_call_neg_rule = Constraint(model.t,rule=afrr_call_neg_rule)

#Arbitrage
def arb_rule(model,t):
    return sum(model.arb_on_off[batterie,t]*model.arb_rev_bat[t] for batterie in model.batterie)     ==     model.arb_rev[t]
model.arb_rule = Constraint(model.t,rule=arb_rule)

#Flexibility revenues
def fcr_rev_rule(model,t):
    return model.fcr_price[t]*model.fcr[t]     ==     model.fcr_rev[t]
model.fcr_rev_rule = Constraint(model.t,rule=fcr_rev_rule)

def frr_pos_rev_rule(model,t):
    return model.frr_pos_price[t]*model.pos_afrr[t]     + model.afrr_energy_rev_pos[t]     ==     model.frr_pos_rev[t]
model.frr_pos_rev_rule = Constraint(model.t,rule=frr_pos_rev_rule)

def frr_neg_rev_rule(model,t):
    return model.frr_neg_price[t]*model.neg_afrr[t]     + model.afrr_energy_rev_neg[t]     ==     model.frr_neg_rev[t]
model.frr_neg_rev_rule = Constraint(model.t,rule=frr_neg_rev_rule)

###FCR symmetric combination

# #Positive Flexibilität
# def pos_flex_kwk_rule(model,kwk,t):
#     return model.pos_afrr_kwk[kwk,t]+model.pos_fcr_kwk[kwk,t]<=model.pos_flex_kwk[kwk,t]
# model.pos_flex_kwk_rule = Constraint(model.kwk, model.t, rule=pos_flex_kwk_rule)

# #Negative Flexibilität
# def neg_flex_kwk_rule(model,kwk,t):
#     return model.neg_afrr_kwk[kwk,t]+model.neg_fcr_kwk[kwk,t]<=model.neg_flex_kwk[kwk,t]
# model.neg_flex_kwk_rule = Constraint(model.kwk, model.t, rule=neg_flex_kwk_rule)

# #FCR RLT
# def pos_fcr_rlt_rule(model,rlt,t):
#     return model.pos_fcr_rlt[rlt,t]<=model.rlt_fcr[rlt]
# model.pos_fcr_rlt_milp = Constraint(model.rlt, model.t, rule=pos_fcr_rlt_rule)

# #FCR RLT
# def neg_fcr_rlt_rule(model,rlt,t):
#     return model.neg_fcr_rlt[rlt,t]<=model.rlt_fcr[rlt]
# model.neg_fcr_rlt_milp = Constraint(model.rlt, model.t, rule=neg_fcr_rlt_rule)

# #Aufteilung Flexibilität HVACs
# def max_rlt_pos_dsm_rule(model,rlt,t):
#     return model.rlt_dsm_pos[rlt,t]+model.pos_fcr_rlt[rlt,t] + model.pos_afrr_rlt[rlt,t] <= model.pos_flex_rlt[rlt,t]
# model.max_rlt_pos_dsm = Constraint(model.rlt, model.t,rule=max_rlt_pos_dsm_rule)

# #Aufteilung Flexibilität HVACs
# def max_rlt_neg_dsm_rule(model,rlt,t):
#     return model.rlt_dsm_neg[rlt,t]+model.neg_fcr_rlt[rlt,t] + model.neg_afrr_rlt[rlt,t] <= model.neg_flex_rlt[rlt,t]
# model.max_rlt_neg_dsm = Constraint(model.rlt, model.t,rule=max_rlt_neg_dsm_rule)

# def fcr_balance_rule(model,t):
#     return sum(model.pos_fcr_kwk[kwk,t] for kwk in model.kwk) \
#     + sum(model.pos_fcr_rlt[rlt,t] for rlt in model.rlt) \
#     + model.pos_fcr_p2h[t] \
#     + sum(model.pos_fcr_ev[ev,t] for ev in model.ev) \
#     == \
#     sum(model.neg_fcr_kwk[kwk,t] for kwk in model.kwk) \
#     + sum(model.neg_fcr_rlt[rlt,t] for rlt in model.rlt) \
#     + model.neg_fcr_p2h[t]
#     + sum(model.neg_fcr_ev[ev,t] for ev in model.ev)
# model.fcr_balance = Constraint(model.t,rule=fcr_balance_rule)

# def fcr_total_balance_rule(model,t):
#     return sum(model.pos_fcr_kwk[kwk,t] for kwk in model.kwk) \
#     + sum(model.pos_fcr_rlt[rlt,t] for rlt in model.rlt) \
#     + model.pos_fcr_p2h[t] \
#     + sum(model.fcr_batterie[batterie,t] for batterie in model.batterie) \
#     + sum(model.pos_fcr_ev[ev,t] for ev in model.ev) \
#     == \
#     model.fcr[t]
# model.fcr_total_balance = Constraint(model.t,rule=fcr_total_balance_rule)

# #Positive Flexibilität P2H
# def pos_flex_p2h_rule(model,t):
#     return model.pos_afrr_p2h[t]+model.pos_fcr_p2h[t]<=model.p2h_demand[t]
# model.pos_flex_p2h_rule = Constraint(model.t, rule=pos_flex_p2h_rule)

# #Negative Flexibilität P2H
# def neg_flex_p2h_rule(model,t):
#     return model.neg_afrr_p2h[t]+model.neg_fcr_p2h[t]<=p2h-model.p2h_demand[t]
# model.neg_flex_p2h_rule = Constraint(model.t, rule=neg_flex_p2h_rule)

# #Positive Flexibilität Cooler
# def max_cooler_pos_dsm_rule(model,t):
#     return model.cooler_dsm_pos[t] <= model.pos_flex_cooler[t]
# model.max_cooler_pos_dsm = Constraint(model.t,rule=max_cooler_pos_dsm_rule)

# #Negative Flexibilität Cooler
# def max_cooler_neg_dsm_rule(model,t):
#     return model.cooler_dsm_neg[t] <= model.neg_flex_cooler[t]
# model.max_cooler_neg_dsm = Constraint(model.t,rule=max_cooler_neg_dsm_rule)

### Vermarktungszeit 4h gemeinsam
# def fcr_mindestvm_rule(model,t,rl_vz):
#     if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
#         return model.fcr[t] == model.fcr[t+rl_vz]
#     return Constraint.Skip
# model.fcr_mindestvm_rule = Constraint(model.t, model.rl_vz, rule = fcr_mindestvm_rule)

# def neg_afrr_mindestvm_rule(model,t,rl_vz):
#     if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
#         return model.neg_afrr[t] == model.neg_afrr[t+rl_vz]
#     return Constraint.Skip
# model.neg_afrr_mindestvm_rule = Constraint(model.t, model.rl_vz, rule = neg_afrr_mindestvm_rule)

# def pos_afrr_mindestvm_rule(model,t,rl_vz):
#     if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
#         return model.pos_afrr[t] == model.pos_afrr[t+rl_vz]
#     return Constraint.Skip
# model.pos_afrr_mindestvm_rule = Constraint(model.t, model.rl_vz, rule = pos_afrr_mindestvm_rule)

# # ####### FCR Symmetrisch individuell

def fcr_total_balance_rule(model,t):
    return sum(model.fcr_kwk[kwk,t] for kwk in model.kwk)     + sum(model.fcr_rlt[rlt,t] for rlt in model.rlt)     + model.fcr_p2h[t]     + sum(model.fcr_batterie[batterie,t] for batterie in model.batterie) +sum(model.ev_fcr[ev,t] for ev in model.ev)   ==     model.fcr[t]
model.fcr_total_balance = Constraint(model.t,rule=fcr_total_balance_rule)

#Positive Flexibilität
def pos_flex_kwk_rule(model,kwk,t):
    return model.pos_afrr_kwk[kwk,t]+model.fcr_kwk[kwk,t]<=model.pos_flex_kwk[kwk,t]
model.pos_flex_kwk_rule = Constraint(model.kwk, model.t, rule=pos_flex_kwk_rule)

#Negative Flexibilität
def neg_flex_kwk_rule(model,kwk,t):
    return model.neg_afrr_kwk[kwk,t]+model.fcr_kwk[kwk,t]<=model.neg_flex_kwk[kwk,t]
model.neg_flex_kwk_rule = Constraint(model.kwk, model.t, rule=neg_flex_kwk_rule)

#FCR KWK
def fcr_kwk_rule(model,kwk,t):
    return model.fcr_kwk[kwk,t]<=model.kwk_fcr[kwk]
model.fcr_kwk_rule = Constraint(model.kwk, model.t, rule=fcr_kwk_rule)

#Aufteilung Flexibilität HVACs
def max_rlt_pos_dsm_rule(model,rlt,t):
    return model.rlt_dsm_pos[rlt,t]+model.fcr_rlt[rlt,t]+model.pos_afrr_rlt[rlt,t] <= model.pos_flex_rlt[rlt,t]
model.max_rlt_pos_dsm = Constraint(model.rlt, model.t,rule=max_rlt_pos_dsm_rule)

#Aufteilung Flexibilität HVACs
def max_rlt_neg_dsm_rule(model,rlt,t):
    return model.rlt_dsm_neg[rlt,t]+model.fcr_rlt[rlt,t]+model.neg_afrr_rlt[rlt,t] <= model.neg_flex_rlt[rlt,t]
model.max_rlt_neg_dsm = Constraint(model.rlt, model.t,rule=max_rlt_neg_dsm_rule)

#FCR RLT
def fcr_rlt_rule(model,rlt,t):
    return model.fcr_rlt[rlt,t]<=model.rlt_fcr[rlt]
model.fcr_rlt_milp = Constraint(model.rlt, model.t, rule=fcr_rlt_rule)

#Positive Flexibilität
def pos_flex_p2h_rule(model,t):
    return model.pos_afrr_p2h[t]+model.fcr_p2h[t]<=model.p2h_demand[t]
model.pos_flex_p2h_rule = Constraint(model.t, rule=pos_flex_p2h_rule)

#Negative Flexibilität
def neg_flex_p2h_rule(model,t):
    return model.neg_afrr_p2h[t]+model.fcr_p2h[t]<=p2h-model.p2h_demand[t]
model.neg_flex_p2h_rule = Constraint(model.t, rule=neg_flex_p2h_rule)

####### Vermarktungszeit 4h individuell

#Vermarktungszeit FCR Batterie 
def battery_fcr_mindestvm_rule(model,batterie,t, rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.fcr_batterie[batterie,t] == model.fcr_batterie[batterie,t+rl_vz]
    return Constraint.Skip
model.battery_fcr_mindestvm_rule = Constraint(model.batterie, model.t, model.rl_vz, rule = battery_fcr_mindestvm_rule)

#Vermarktungszeit KWK FCR 
def kwk_fcr_mindestvm_rule(model,kwk,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.fcr_kwk[kwk,t] == model.fcr_kwk[kwk,t+rl_vz]
    return Constraint.Skip
model.kwk_fcr_mindestvm_rule = Constraint(model.kwk, model.t, model.rl_vz, rule = kwk_fcr_mindestvm_rule)

#Vermarktungszeit KWK POS FRR 
def kwk_FRR_POS_mindestvm_rule(model,kwk,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.pos_afrr_kwk[kwk,t] == model.pos_afrr_kwk[kwk,t+rl_vz]
    return Constraint.Skip
model.kwk_FRR_POS_mindestvm_rule = Constraint(model.kwk, model.t, model.rl_vz, rule = kwk_FRR_POS_mindestvm_rule)

#Vermarktungszeit KWK NEG FRR 
def kwk_FRR_NEG_mindestvm_rule(model,kwk,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.neg_afrr_kwk[kwk,t] == model.neg_afrr_kwk[kwk,t+rl_vz]
    return Constraint.Skip
model.kwk_FRR_NEG_mindestvm_rule = Constraint(model.kwk, model.t, model.rl_vz, rule = kwk_FRR_NEG_mindestvm_rule)

#Vermarktungszeit RLT POS FRR 
def rlt_FRR_POS_mindestvm_rule(model,rlt,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.pos_afrr_rlt[rlt,t] == model.pos_afrr_rlt[rlt,t+rl_vz]
    return Constraint.Skip
model.rlt_FRR_POS_mindestvm_rule = Constraint(model.rlt, model.t, model.rl_vz, rule = rlt_FRR_POS_mindestvm_rule)

#Vermarktungszeit NEA POS FRR 
def nea_FRR_POS_mindestvm_rule(model,nea,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.pos_afrr_nea[nea,t] == model.pos_afrr_nea[nea,t+rl_vz]
    return Constraint.Skip
model.nea_FRR_POS_mindestvm_rule = Constraint(model.nea, model.t, model.rl_vz, rule = nea_FRR_POS_mindestvm_rule)

#Vermarktungszeit NEA NEG FRR 
def nea_FRR_NEG_mindestvm_rule(model,nea,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.neg_afrr_nea[nea,t] == model.neg_afrr_nea[nea,t+rl_vz]
    return Constraint.Skip
model.nea_FRR_NEG_mindestvm_rule = Constraint(model.nea, model.t, model.rl_vz, rule = nea_FRR_NEG_mindestvm_rule)

#Vermarktungszeit RLT NEG FRR 
def rlt_FRR_NEG_mindestvm_rule(model,rlt,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.neg_afrr_rlt[rlt,t] == model.neg_afrr_rlt[rlt,t+rl_vz]
    return Constraint.Skip
model.rlt_FRR_NEG_mindestvm_rule = Constraint(model.rlt, model.t, model.rl_vz, rule = rlt_FRR_NEG_mindestvm_rule)

#Vermarktungszeit RLT FCR 
def rlt_fcr_mindestvm_rule(model,rlt,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.fcr_rlt[rlt,t] == model.fcr_rlt[rlt,t+rl_vz]
    return Constraint.Skip
model.rlt_fcr_mindestvm_rule = Constraint(model.rlt, model.t, model.rl_vz, rule = rlt_fcr_mindestvm_rule)

#Vermarktungszeit P2H FCR 
def p2h_fcr_mindestvm_rule(model,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.fcr_p2h[t] == model.fcr_p2h[t+rl_vz]
    return Constraint.Skip
model.p2h_fcr_mindestvm_rule = Constraint(model.t, model.rl_vz, rule = p2h_fcr_mindestvm_rule)

#Vermarktungszeit P2H POS FRR 
def p2h_FRR_POS_mindestvm_rule(model,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.pos_afrr_p2h[t] == model.pos_afrr_p2h[t+rl_vz]
    return Constraint.Skip
model.p2h_FRR_POS_mindestvm_rule = Constraint(model.t, model.rl_vz, rule = p2h_FRR_POS_mindestvm_rule)

#Vermarktungszeit P2H NEG FRR 
def p2h_FRR_NEG_mindestvm_rule(model,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.neg_afrr_p2h[t] == model.neg_afrr_p2h[t+rl_vz]
    return Constraint.Skip
model.p2h_FRR_NEG_mindestvm_rule = Constraint(model.t, model.rl_vz, rule = p2h_FRR_NEG_mindestvm_rule)

#Vermarktungszeit EV FCR 
def ev_fcr_mindestvm_rule(model,ev,t,rl_vz):
    if t <= len(zeitreihen.index)-rl_vzr and t%rl_vzr==0:
        return model.ev_fcr[ev,t] == model.ev_fcr[ev,t+rl_vz]
    return Constraint.Skip
model.ev_fcr_mindestvm_rule = Constraint(model.ev, model.t, model.rl_vz, rule = ev_fcr_mindestvm_rule)


# # Definition Optimierungszeitraum

# In[ ]:


import datetime
#Datum, für die Optimierung durchgeführt wird
date_lower_bound_start = "2017-01-01"

header = ["OBJ", "PRL", "FRR+", "FRR-","INT", "FRR+ Energieerloese", "FRR- Energieerloese", "PRL Leistung", "FRR+ Leistung", "FRR- Leistung", "INT Leistung Batterie",            "FCR Leistung Batterie", "FCR Batterie", "INT Batterie", "LO Batterie",        "FCR+ KWK", "FCR- KWK", "FRR+ KWK", "FRR- KWK", "FRR+ NEA", "FRR- NEA", "FCR+ RLT", "FCR- RLT", "FRR+ RLT",                   "FRR- RLT","FCR+ P2H", "FCR- P2H", "FRR+ P2H", "FRR- P2H", "FCR EV",           "Netzentgelte", "Lastspitze", "Maximaler Strombedarf", "Strombezugskosten","Menge Peak",           "Ausspeisung", "Ausspeisung RE",           "Status", "Time"]
results_total = pd.DataFrame(columns = header)

for z in range(365):
    date_lower_bound = pd.to_datetime(date_lower_bound_start) + z*timedelta(days = 1)
    date_upper_bound = date_lower_bound + timedelta(days = 1)

    #For new optimization
    ev2=bev[(bev["time_p_round"]>= date_lower_bound) & (bev["time_unp_round"] < date_upper_bound)]
    if date_lower_bound == pd.to_datetime("2017-10-29"):
            ev2 = ev2.drop(ev2.index[2:3])
    if z == 42:
        ev2 = ev2[1:30]
    
    a = pd.to_datetime(date_lower_bound)
    b = pd.to_datetime(date_upper_bound)
    c = b-a
    index = pd.date_range(start = a, end = b, freq = "15Min", tz = "UTC")

    df_power = pd.DataFrame(index=index, columns = range(np.shape(ev2)[0]))
    df_plug = pd.DataFrame(index=index, columns = range(np.shape(ev2)[0]))
    df_power.index = pd.DatetimeIndex([i.astimezone(tz.utc) for i in df_power.index])
    df_power = df_power.tz_localize(None)
    df_plug.index = pd.DatetimeIndex([i.astimezone(tz.utc) for i in df_plug.index])
    df_plug = df_plug.tz_localize(None)

    series_flex = pd.Series(index = range(np.shape(ev2)[0]))
    series_max_power = pd.Series(index = range(np.shape(ev2)[0]))
    series_min_power = pd.Series(index = range(np.shape(ev2)[0]))
    series_charge_length = pd.Series(index = range(np.shape(ev2)[0]))
    series_energy = pd.Series(index = range(np.shape(ev2)[0]))
    series_start_energy = pd.Series(index = range(np.shape(ev2)[0]))
    series_finish_energy = pd.Series(index = range(np.shape(ev2)[0]))
    series_ev_fcr = pd.Series(index = range(np.shape(ev2)[0]))
    series_charge_start = pd.Series(index = range(np.shape(ev2)[0]))
    series_charge_eff = pd.Series(index = range(np.shape(ev2)[0]))
    series_discharge_eff = pd.Series(index = range(np.shape(ev2)[0]))
    series_batt_size = pd.Series(index = range(np.shape(ev2)[0]))



    for i in range(np.shape(ev2)[0]):
        a = ev2.iloc[i]["time_p_round"]
        ab = ev2.iloc[i]["time_finish_round"]
        b = ev2.iloc[i]["time_unp_round"]
        c = ev2.iloc[i]["power"]/1000
        d = ev2.iloc[i]["time_idle [15m]"]
        e = ev2.iloc[i]["time_plug [15m]"]
        f = ev2.iloc[i]["c_battery_size_max"]/1000/1000
        g = ev2.iloc[i]["soc_p"]*ev2.iloc[i]["c_battery_size_max"]/100/1000/1000
        h = min(c,f/1.5)
        j = (ev2.iloc[i]["time_p_round"]-pd.to_datetime(date_lower_bound)).days*96 + (ev2.iloc[i]["time_p_round"]-pd.to_datetime(date_lower_bound)).seconds/3600*4
        k = ev2.iloc[i]["soc_unp"]*ev2.iloc[i]["c_battery_size_max"]/100/1000/1000
        l = ev2.iloc[i]["c_battery_size_max"]/1000/1000

        df_power[i].loc[a:ab] = (k-g)/0.9/(((ab-a).seconds)/60/60+0.25)
        df_plug[i].loc[a:b] = 1
        series_flex.loc[i]= int(d)
        series_max_power.loc[i]= (k-g)/0.9/(((ab-a).seconds)/60/60+0.25)
        series_min_power.loc[i]= -(k-g)/0.9/(((ab-a).seconds)/60/60+0.25)
        series_charge_length.loc[i] = e
        series_energy.loc[i] = f
        series_start_energy.loc[i] = g
        series_ev_fcr.loc[i] = h
        series_charge_start.loc[i] = j
        series_finish_energy.loc[i] = k
        series_charge_eff.loc[i] =0.9
        series_discharge_eff.loc[i] =0.9
        series_batt_size.loc[i] = l

    df_power = df_power.fillna(value =0)
    df_plug = df_plug.fillna(value =0)
    series_flex = series_flex.rename("ev_flex")
    series_max_power = series_max_power.rename("ev_max_power")
    series_min_power = series_min_power.rename("ev_min_power")
    series_charge_length = series_charge_length.rename("charge_length")
    series_energy = series_energy.rename("ev_energy")
    series_start_energy = series_start_energy.rename("charge_start_energy")
    series_finish_energy = series_finish_energy.rename("charge_finish_energy")
    series_ev_fcr = series_ev_fcr.rename("fcr_ev")
    series_charge_start= series_charge_start.rename("charge_start")
    series_charge_eff = series_charge_eff.rename("bel_wg_ev")
    series_discharge_eff = series_discharge_eff.rename("entl_wg_ev")
    series_batt_size = series_batt_size.rename("batt_size")


    zeitreihen = pd.DataFrame(index=index)
    zeitreihen=zeitreihen[:-1]
    zeitreihen.index = pd.DatetimeIndex([i.astimezone(tz.utc) for i in zeitreihen.index])
    zeitreihen = zeitreihen.tz_localize(None)
    zeitreihen = zeitreihen.join(daten_strom/1000*4, how="left")
    zeitreihen = zeitreihen.join(daten_waerme, how="left")
    zeitreihen = zeitreihen.join(wind/1000*4, how="left")
    zeitreihen = zeitreihen.join(strompreis, how="left")
    zeitreihen = zeitreihen.join(temperature, how="left")
    zeitreihen = zeitreihen.join(kaelte/1000, how="left")
    zeitreihen = zeitreihen.join(schichtplan, how="left")
    zeitreihen = zeitreihen.join(fcr_prices/(4*4)*0.8, how="left") #20% Abschlag für PRL-Vermarktung
    zeitreihen = zeitreihen.join(frr_neg_prices/(4*4)*0.8, how="left", lsuffix = "SRL_POS") #20% Abschlag für PRL-Vermarktung
    zeitreihen = zeitreihen.join(frr_pos_prices/(4*4)*0.8, how="left", rsuffix="SRL_NEG")
    zeitreihen = zeitreihen.join(arb_rev_bat/(24*4)*0.8, how="left") #20% Abschlag für Handelsgebühr, Auto-Trading, 30% Abschlag für Wirkungsgradberechnung
    zeitreihen.columns= ["dem_power", "dem_heat", "wind", "power_price", "temperature","kaelte", "KB","MO","VZ",
                         "fcr_price", "frr_neg_prices", "frr_pos_prices", "arb_rev_bat"]
    zeitreihen = zeitreihen.join(df_power, how="left")
    zeitreihen=zeitreihen.fillna(method="ffill")
    zeitreihen=zeitreihen.fillna(method="bfill")
    zeitreihen=zeitreihen.fillna(0)
    zeitreihen= zeitreihen[:96]
    zeitreihen3= zeitreihen.drop(columns =range(np.shape(ev2)[0]))
    zeitreihen3 = zeitreihen3.join(df_plug, how="left")
    zeitreihen2 = zeitreihen.set_index([np.arange(len(zeitreihen.index))])
    zeitreihen3 = zeitreihen3.set_index([np.arange(len(zeitreihen.index))])
    price_avg=np.mean(zeitreihen["power_price"])

    directory = ""
    zeitreihen2.to_csv(directory +"dem_power_data.csv", columns =["dem_power"], index_label = "t")
    zeitreihen2.to_csv(directory +"dem_heat_data.csv", columns =["dem_heat"], index_label = "t")
    zeitreihen2.to_csv(directory +"wind_data.csv", columns =["wind"], index_label = "t")
    zeitreihen2.to_csv(directory +"power_price_data.csv", columns =["power_price"], index_label = "t")
    zeitreihen2.to_csv(directory +"temp_data.csv", columns =["temperature"], index_label = "t")
    zeitreihen2.to_csv(directory +"kaelte_data.csv", columns =["kaelte"], index_label = "t")
    zeitreihen2.to_csv(directory +"schicht_data.csv", columns =["KB","MO","VZ"], index_label = "t", header = [1,2,3])
    zeitreihen2.to_csv(directory +"fcr_price_data.csv", columns =["fcr_price"], index_label = "t")
    zeitreihen2.to_csv(directory +"frr_neg_price_data.csv", columns =["frr_neg_prices"], index_label = "t")
    zeitreihen2.to_csv(directory +"frr_pos_price_data.csv", columns =["frr_pos_prices"], index_label = "t")
    zeitreihen2.to_csv(directory +"arb_rev_bat.csv", columns =["arb_rev_bat"], index_label = "t")
    zeitreihen2.to_csv(directory +"EV.csv", columns =range(np.shape(ev2)[0]), index_label = "t")
    zeitreihen3.to_csv(directory +"charge_plug.csv", columns =range(np.shape(ev2)[0]), index_label = "t")
    series_flex.to_csv(directory +"EV_flex.csv", index_label = "ev", header = True)
    series_max_power.to_csv(directory +"EV_max_power.csv", index_label = "ev", header = True)
    series_min_power.to_csv(directory +"EV_min_power.csv", index_label = "ev", header = True)
    series_charge_length.to_csv(directory +"EV_charge_length.csv", index_label = "ev", header = True)
    series_energy.to_csv(directory +"EV_energy.csv", index_label = "ev", header = True)
    series_start_energy.to_csv(directory +"charge_start_energy.csv", index_label = "ev", header = True)
    series_finish_energy.to_csv(directory +"charge_finish_energy.csv", index_label = "ev", header = True)
    series_ev_fcr.to_csv(directory +"ev_fcr.csv", index_label = "ev", header = True)
    series_charge_start.to_csv(directory +"charge_start.csv", index_label = "ev", header = True)
    series_charge_eff.to_csv(directory +"charge_efficiency.csv", index_label = "ev", header = True)
    series_discharge_eff.to_csv(directory +"discharge_efficiency.csv", index_label = "ev", header = True)
    series_batt_size.to_csv(directory +"batt_size.csv", index_label = "ev", header = True)

    #Solver definiert - auch glpk möglich
    opt = SolverFactory("gurobi")
    opt.options["timelimit"] = 600
    opt.options["mipgap"] = 0.0000001
    opt.options["Threads"] = 28
    # opt.options["LogToConsole"]=1
    # opt.options["DualReductions"]=0


    #DataPortal geöffnet
    data = DataPortal() 

    #Read all the data from different files
    #Sonstiges
    data.load(filename="dem_power_data.csv",format="set", set="t")
    data.load(filename="dem_power_data.csv",index="t", param="dem_power")
    data.load(filename="dem_heat_data.csv",format="set", set="t")
    data.load(filename="dem_heat_data.csv",index="t", param="dem_heat")
    data.load(filename="wind_data.csv",format="set", set="t")
    data.load(filename="wind_data.csv",index="t", param="wind")
    data.load(filename="power_price_data.csv",format="set", set="t")
    data.load(filename="power_price_data.csv",index="t", param="power_price")
    data.load(filename="temp_data.csv",format="set", set="t")
    data.load(filename="temp_data.csv",index="t", param="temperature")

    #Regelleistung
    data.load(filename="fcr_price_data.csv",format="set", set="t")
    data.load(filename="fcr_price_data.csv",index="t", param="fcr_price")
    data.load(filename="frr_neg_price_data.csv",format="set", set="t")
    data.load(filename="frr_neg_price_data.csv",index="t", param="frr_neg_price")
    data.load(filename="frr_pos_price_data.csv",format="set", set="t")
    data.load(filename="frr_pos_price_data.csv",index="t", param="frr_pos_price")

    #KWK
    data.load(filename="kwk_cos_lin.csv",format="set", set="kwk")
    data.load(filename="kwk_cos_lin.csv",index="kwk",param="cos_lin")
    data.load(filename="kwk_varcos_tl.csv",format="set", set="kwk")
    data.load(filename="kwk_varcos_tl.csv",index="kwk",param="varcos_tl")
    data.load(filename="kwk_cap.csv",format="set", set="kwk")
    data.load(filename="kwk_cap.csv",index="kwk",param="cap")
    data.load(filename="kwk_floor.csv",format="set", set="kwk")
    data.load(filename="kwk_floor.csv",index="kwk",param="floor")
    data.load(filename="kwk_f1.csv",format="set", set="kwk")
    data.load(filename="kwk_f1.csv",index="kwk",param="f1")
    data.load(filename="kwk_f2.csv",format="set", set="kwk")
    data.load(filename="kwk_f2.csv",index="kwk",param="f2")
    data.load(filename="kwk_fcr.csv",format="set", set="kwk")
    data.load(filename="kwk_fcr.csv",index="kwk",param="kwk_fcr")
    data.load(filename="kwk_afrr.csv",format="set", set="kwk")
    data.load(filename="kwk_afrr.csv",index="kwk",param="kwk_afrr")
    data.load(filename="kwk_afrr_prob_neg.csv",format="set", set="kwk")
    data.load(filename="kwk_afrr_prob_neg.csv",index="kwk",param="kwk_afrr_prob_neg")
    data.load(filename="kwk_afrr_prob_pos.csv",format="set", set="kwk")
    data.load(filename="kwk_afrr_prob_pos.csv",index="kwk",param="kwk_afrr_prob_pos")
    data.load(filename="kwk_afrr_ep_neg.csv",format="set", set="kwk")
    data.load(filename="kwk_afrr_ep_neg.csv",index="kwk",param="kwk_afrr_ep_neg")
    data.load(filename="kwk_afrr_ep_pos.csv",format="set", set="kwk")
    data.load(filename="kwk_afrr_ep_pos.csv",index="kwk",param="kwk_afrr_ep_pos")


    #Kessel
    data.load(filename="cos_lin_kessel.csv",format="set", set="kessel")
    data.load(filename="cos_lin_kessel.csv",index="kessel",param="cos_lin_kessel")
    data.load(filename="cos_kessel_tl.csv",format="set", set="kessel")
    data.load(filename="cos_kessel_tl.csv",index="kessel",param="cos_kessel_tl")
    data.load(filename="floor_kessel.csv",format="set", set="kessel")
    data.load(filename="floor_kessel.csv",index="kessel",param="floor_kessel")
    data.load(filename="cap_kessel.csv",format="set", set="kessel")
    data.load(filename="cap_kessel.csv",index="kessel",param="cap_kessel")

    #Batterie
    data.load(filename="cos_batt.csv",format="set", set="batterie")
    data.load(filename="cos_batt.csv",index="batterie",param="cos_batterie")
    data.load(filename="bel_wg_batt.csv",format="set", set="batterie")
    data.load(filename="bel_wg_batt.csv",index="batterie", param="bel_wg_batt")
    data.load(filename="entl_wg_batt.csv",format="set", set="batterie")
    data.load(filename="entl_wg_batt.csv",index="batterie", param="entl_wg_batt")
    data.load(filename="temp_wg_batt.csv",format="set", set="batterie")
    data.load(filename="temp_wg_batt.csv",index="batterie", param="temp_wg_batt")
    data.load(filename="fcr_power.csv",format="set", set="batterie")
    data.load(filename="fcr_power.csv",index="batterie", param="fcr_power")
    data.load(filename="max_power.csv",format="set", set="batterie")
    data.load(filename="max_power.csv",index="batterie", param="max_power")
    data.load(filename="cap.csv",format="set", set="batterie")
    data.load(filename="cap.csv",index="batterie", param="cap_batterie")
    data.load(filename="arb_rev_bat.csv",format="set", set="t")
    data.load(filename="arb_rev_bat.csv",index="t", param="arb_rev_bat")

    #HVAC
    data.load(filename="floor_rlt.csv",format="set", set="rlt")
    data.load(filename="floor_rlt.csv",index="rlt",param="floor_rlt")
    data.load(filename="winter_rlt.csv",format="set", set="rlt")
    data.load(filename="winter_rlt.csv",index="rlt",param="winter_rlt")
    data.load(filename="cap_rlt.csv",format="set", set="rlt")
    data.load(filename="cap_rlt.csv",index="rlt",param="cap_rlt")
    data.load(filename="rlt_afrr_prob_neg.csv",format="set", set="rlt")
    data.load(filename="rlt_afrr_prob_neg.csv",index="rlt",param="rlt_afrr_prob_neg")
    data.load(filename="rlt_afrr_prob_pos.csv",format="set", set="rlt")
    data.load(filename="rlt_afrr_prob_pos.csv",index="rlt",param="rlt_afrr_prob_pos")
    data.load(filename="rlt_afrr_ep_neg.csv",format="set", set="rlt")
    data.load(filename="rlt_afrr_ep_neg.csv",index="rlt",param="rlt_afrr_ep_neg")
    data.load(filename="rlt_afrr_ep_pos.csv",format="set", set="rlt")
    data.load(filename="rlt_afrr_ep_pos.csv",index="rlt",param="rlt_afrr_ep_pos")
    data.load(filename="rlt_fcr.csv",format="set", set="rlt")
    data.load(filename="rlt_fcr.csv",index="rlt",param="rlt_fcr")
    data.load(filename="schicht_data.csv",param = "rlt_onoff",format="array")

    #NEA
    data.load(filename="cos_nea.csv",format="set", set="nea")
    data.load(filename="cos_nea.csv",index="nea",param="cos_nea")
    data.load(filename="cap_nea.csv",format="set", set="nea")
    data.load(filename="cap_nea.csv",index="nea",param="cap_nea")
    data.load(filename="nea_afrr.csv",format="set", set="nea")
    data.load(filename="nea_afrr.csv",index="nea",param="nea_afrr")
    data.load(filename="nea_afrr_prob_neg.csv",format="set", set="nea")
    data.load(filename="nea_afrr_prob_neg.csv",index="nea",param="nea_afrr_prob_neg")
    data.load(filename="nea_afrr_prob_pos.csv",format="set", set="nea")
    data.load(filename="nea_afrr_prob_pos.csv",index="nea",param="nea_afrr_prob_pos")
    data.load(filename="nea_afrr_ep_neg.csv",format="set", set="nea")
    data.load(filename="nea_afrr_ep_neg.csv",index="nea",param="nea_afrr_ep_neg")
    data.load(filename="nea_afrr_ep_pos.csv",format="set", set="nea")
    data.load(filename="nea_afrr_ep_pos.csv",index="nea",param="nea_afrr_ep_pos")

    #Cooler
    data.load(filename="kaelte_data.csv",format="set", set="t")
    data.load(filename="kaelte_data.csv",index="t", param="op_cooler")
    data.load(filename="cap_cooler.csv",format="set", set="cooler")
    data.load(filename="cap_cooler.csv",index="cooler",param="cap_cooler")

    if np.shape(ev2)[0] >0:
        #EV
        data.load(filename="EV_max_power.csv",format="set", set="ev")
        data.load(filename="EV_max_power.csv",index="ev", param="ev_max_power")
        data.load(filename="EV_min_power.csv",format="set", set="ev")
        data.load(filename="EV_min_power.csv",index="ev", param="ev_min_power")
        data.load(filename="EV.csv",format="array", param="ev_power_plan")
        #data.load(filename="charge_start.csv",format="array", param="charge_start")
        data.load(filename="charge_plug.csv",format="array", param="charge_plug")
        data.load(filename="EV_flex.csv",format="set", set="ev")
        data.load(filename="EV_flex.csv",index="ev", param="ev_flex")
        data.load(filename="EV_charge_length.csv",format="set", set="ev")
        data.load(filename="EV_charge_length.csv",index="ev", param="charge_length")
        data.load(filename="EV_energy.csv",format="set", set="ev")
        data.load(filename="EV_energy.csv",index="ev", param="ev_energy")
        data.load(filename="charge_start_energy.csv",format="set", set="ev")
        data.load(filename="charge_start_energy.csv",index="ev", param="charge_start_energy")
        data.load(filename="charge_finish_energy.csv",format="set", set="ev")
        data.load(filename="charge_finish_energy.csv",index="ev", param="charge_finish_energy")
        data.load(filename="ev_fcr.csv",format="set", set="ev")
        data.load(filename="ev_fcr.csv",index="ev", param="fcr_ev")
        data.load(filename="charge_start.csv",format="set", set="ev")
        data.load(filename="charge_start.csv",index="ev", param="charge_start")
        data.load(filename="charge_efficiency.csv",format="set", set="ev")
        data.load(filename="charge_efficiency.csv",index="ev", param="bel_wg_ev")
        data.load(filename="discharge_efficiency.csv",format="set", set="ev")
        data.load(filename="discharge_efficiency.csv",index="ev", param="entl_wg_ev")
        data.load(filename="batt_size.csv",format="set", set="ev")
        data.load(filename="batt_size.csv",index="ev", param="batt_size_ev")

    #model.pprint()

    #Create an instance  
    instance = model.create_instance(data)

    #Display all the info of the instance
    #instance.pprint()

    #Solve the optimization problem
    results_solve = opt.solve(instance) 
    print(results_solve)
    #instance.display()  

    print(z)
    
    directory = "2017_Scenario1/" 
    
    peak = instance.netzentgelte.value+peak
     
    
    # Flexerlöse
    f = open(directory + "results_flex"+str(peak_init)+ ".csv", "w")
    f.write("Date"+", ")
    f.write(str(date_lower_bound))
    f.write("\n")
    f.write("OBJ"+", ")
    f.write(str(instance.OBJ()))
    f.write("\n")
    f.write("PRL Erloese"+", ")
    f.write(str(sum(instance.fcr_rev[:].value)))
    f.write("\n")
    f.write("FRR+ Erloese"+", ")
    f.write(str(sum(instance.frr_pos_rev[:].value)))
    f.write("\n")
    f.write("FRR- Erloese"+", ")
    f.write(str(sum(instance.frr_neg_rev[:].value)))
    f.write("\n")
    
    f.write("INT Erloese"+", ")
    f.write(str(sum(instance.arb_rev[:].value)))
    f.write("\n")
    
    f.write("FRR+ Arbeitserloese"+", ")
    f.write(str(sum(instance.afrr_energy_rev_pos[:].value)))
    f.write("\n")
    f.write("FRR- Arbeitserloese"+", ")
    f.write(str(sum(instance.afrr_energy_rev_neg[:].value)))
    f.write("\n")

    
    t = len(zeitreihen.index)
    f.write("FCR Leistung"+", ")
    f.write(str(sum(instance.fcr[:].value)/t))
    f.write("\n")


    f.write("FRR+ Leistung"+", ")
    f.write(str(sum(instance.pos_afrr[:].value)/t))
    f.write("\n")
    f.write("FRR- Leistung"+", ")
    f.write(str(sum(instance.neg_afrr[:].value)/t))
    f.write("\n")

    
    #Batterie
    f.write("INT Leistung Batterie"+", ")
    f.write(str(sum(instance.arb_on_off[:,:].value)/t/4*10))
    f.write("\n")
    f.write("FCR Leistung Batterie"+", ")
    f.write(str(sum(instance.fcr_batterie[:,:].value)/t/4))
    f.write("\n")
    f.write("Summe FCR Batterie"+", ")
    f.write(str(sum(instance.batterie_fcr_onoff[:,:].value)))
    f.write("\n")
    f.write("Summe INT Batterie"+", ")
    f.write(str(sum(instance.arb_on_off[:,:].value)))
    f.write("\n")
    f.write("Summe Lokale Optimierung Batterie"+", ")
    f.write(str(sum(instance.batterie_LO[:,:].value)))
    f.write("\n")

     #KWK
    f.write("POS FCR KWK"+", ")
    f.write(str(sum(instance.fcr_kwk[:,:].value)/t))
    f.write("\n")
    f.write("NEG FCR KWK"+", ")
    f.write(str(sum(instance.fcr_kwk[:,:].value)/t))
    f.write("\n")
    f.write("POS FRR KWK"+", ")
    f.write(str(sum(instance.pos_afrr_kwk[:,:].value)/t))
    f.write("\n")
    f.write("NEG FRR KWK"+", ")
    f.write(str(sum(instance.neg_afrr_kwk[:,:].value)/t))
    f.write("\n")
    
    #NEA
    f.write("POS FRR NEA"+", ")
    f.write(str(sum(instance.pos_afrr_nea[:,:].value)/t))
    f.write("\n")
    f.write("NEG FRR NEA"+", ")
    f.write(str(sum(instance.neg_afrr_nea[:,:].value)/t))
    f.write("\n")
    
    #RLT
    f.write("POS FCR RLT"+", ")
    f.write(str(sum(instance.fcr_rlt[:,:].value)/t))
    f.write("\n")
    f.write("NEG FCR RLT"+", ")
    f.write(str(sum(instance.fcr_rlt[:,:].value)/t))
    f.write("\n")
    f.write("POS FRR RLT"+", ")
    f.write(str(sum(instance.pos_afrr_rlt[:,:].value)/t))
    f.write("\n")
    f.write("NEG FRR RLT"+", ")
    f.write(str(sum(instance.neg_afrr_rlt[:,:].value)/t))
    f.write("\n")
    
    #P2H
    f.write("POS FCR P2H"+", ")
    f.write(str(sum(instance.fcr_p2h[:].value)/t))
    f.write("\n")
    f.write("NEG FCR P2h"+", ")
    f.write(str(sum(instance.fcr_p2h[:].value)/t))
    f.write("\n")
    f.write("POS FRR P2H"+", ")
    f.write(str(sum(instance.pos_afrr_p2h[:].value)/t))
    f.write("\n")
    f.write("NEG FRR P2H"+", ")
    f.write(str(sum(instance.neg_afrr_p2h[:].value)/t))
    f.write("\n")
            
    #EV
    f.write("FCR EV"+", ")
    f.write(str(sum(instance.ev_fcr[:,:].value)/t))
    f.write("\n")
    
    
    f.write("Netzentgelte"+", ")
    f.write(str(instance.netzentgelte.value*cost_lastspitze))
    f.write("\n")
    f.write("Lastspitze"+", ")
    f.write(str(max(instance.grid_power_feed_in[:].value)))
    f.write("\n")
    f.write("Max Strombedarf"+", ")
    f.write(str(max(instance.dem_power[:])))
    f.write("\n")
    f.write("Strombezugskosten"+", ")
    f.write(str(sum(instance.strombezugskosten[:].value)))
    f.write("\n")
    f.write("Menge Peak"+", ")
    f.write(str(instance.netzentgelte.value))
    f.write("\n")
    
    f.write("Ausspeisung"+", ")
    f.write(str(sum(instance.grid_power_feed_back[:].value)))
    f.write("\n")
    f.write("Ausspeisung RE"+", ")
    f.write(str(sum(instance.res_buffer[:].value)))
    f.write("\n")

    f.write("Status"+", ")
    f.write(str(results_solve.Solver[0]["Status"]))
    f.write("\n")
    f.write("Time"+", ")
    f.write(str(results_solve.Solver[0]["Time"]))
    f.write("\n")
    
    f.close()


    results = pd.read_csv(directory + "results_flex"+str(peak_init)+ ".csv",  sep = ",", error_bad_lines=False)
    results=results.T
    results=results[-1:]
    results.columns = header


    
    results_total = pd.concat([results_total, results])
    results_total.to_csv(directory + "results"+str(peak_init)+ ".csv")
    
results_total

