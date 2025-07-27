import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Pro Solar Light Calculator", layout="centered")
st.title("🔋 Pro Solar Light Runtime Calculator")

# === INPUTS ===
try:
    voltage_option = st.radio("Select Battery Voltage", options=[12.8, 25.6], format_func=lambda x: f"{int(x)}V System")
    system_voltage = float(voltage_option)

    load_power = st.number_input("LED Load Power (Full Brightness in Watts)", min_value=1.0, value=40.0)
    battery_capacity_wh = st.number_input("Battery Capacity (Wh)", min_value=1.0, value=480.0)
    solar_panel_wattage = st.number_input("Solar Panel Wattage (W)", min_value=1.0, value=120.0)

    solar_efficiency = 0.75
    sun_hours = 5
    solar_energy = solar_panel_wattage * sun_hours * solar_efficiency

    # === DIMMING PROFILE ===
    st.markdown("### 🌙 Dimming Profile (Customize Each Stage)")
    stage_data = []
    total_energy = 0

    for i in range(1, 5):
        st.markdown(f"**Stage {i}**")
        brightness = st.slider(f"Brightness (%) - Stage {i}", 0, 100, [100, 50, 30, 0][i-1], key=f"b{i}")
        duration = st.slider(f"Duration (hours) - Stage {i}", 0, 12, [4, 6, 6, 0][i-1], key=f"d{i}")
        if duration > 0 and brightness > 0:
            energy = load_power * (brightness / 100) * duration
            stage_data.append({
                'Stage': i,
                'Brightness (%)': brightness,
                'Duration (hrs)': duration,
                'Energy (Wh)': energy
            })
            total_energy += energy
        else:
            stage_data.append({
                'Stage': i,
                'Brightness (%)': brightness,
                'Duration (hrs)': duration,
                'Energy (Wh)': 0
            })

    # === BATTERY & SOLAR RESULTS ===
    energy_balance = solar_energy - total_energy
    battery_remaining = battery_capacity_wh - total_energy
    dod = 0.8
    required_battery_wh = total_energy / dod
    required_battery_ah = required_battery_wh / system_voltage

    # === RESULTS DISPLAY ===
    st.markdown("## 📊 Results Summary")
    st.write(f"🔋 **Total Night Load:** {total_energy:.2f} Wh")
    st.write(f"🔆 **Solar Recovery (5h @ 75%):** {solar_energy:.2f} Wh")
    st.write(f"⚖️ **Energy Balance (Solar - Load):** {energy_balance:.2f} Wh")
    st.write(f"🔋 **Battery Remaining After Night:** {battery_remaining:.2f} Wh")

    # === WARNINGS ===
    if battery_remaining < 0:
        st.error("❌ Battery is too small to support this load for the night!")
    elif battery_remaining < battery_capacity_wh * 0.2:
        st.warning("⚠️ Battery is nearly fully used.")
    else:
        st.success("✅ Battery capacity is sufficient.")

    if energy_balance < 0:
        st.error("❌ Solar panel is undersized! It won't recharge the battery daily.")
    elif energy_balance < 0.2 * total_energy:
        st.warning("⚠️ Solar just barely recharges the load.")
    else:
        st.info("✅ Solar panel can recharge the battery daily.")

    if total_energy > battery_capacity_wh * 0.9:
        st.warning("⚠️ Load is too high for the selected battery size.")

    # === SUGGESTED BATTERY ===
    st.markdown("### 🔋 Suggested Battery Size")
    st.write(f"📌 Required Battery: **{required_battery_wh:.2f} Wh**")
    st.write(f"📌 Or: **{required_battery_ah:.2f} Ah** @ {int(system_voltage)}V")

    # === BAR CHART ===
    st.markdown("## 📉 Energy Comparison")
    fig, ax = plt.subplots()
    ax.bar(["Night Load", "Solar Recovery"], [total_energy, solar_energy], color=["red", "green"])
    ax.set_ylabel("Energy (Wh)")
    st.pyplot(fig)

    # === SOC SIMULATION ===
    st.markdown("## 🔋 Battery SOC Simulation (24hr)")

    hourly_soc = []
    soc = 100
    hr_pointer = 0
    battery_wh = battery_capacity_wh

    for stage in stage_data:
        for _ in range(stage['Duration (hrs)']):
            consumption = load_power * (stage['Brightness (%)'] / 100)
            soc -= (consumption / battery_wh) * 100
            soc = max(soc, 0)
            hourly_soc.append(soc)
            hr_pointer += 1

    while hr_pointer < 16:
        hourly_soc.append(soc)
        hr_pointer += 1

    charge_per_hour = (solar_panel_wattage * solar_efficiency / battery_wh) * 100
    for _ in range(5):
        soc += charge_per_hour
        soc = min(soc, 100)
        hourly_soc.append(soc)
        hr_pointer += 1

    while hr_pointer < 24:
        hourly_soc.append(soc)
        hr_pointer += 1

    fig2, ax2 = plt.subplots()
    ax2.plot(range(24), hourly_soc, marker='o', color='blue')
    ax2.set_title("Battery SOC Simulation (24h)")
    ax2.set_xlabel("Hour")
    ax2.set_ylabel("SOC (%)")
    ax2.set_ylim(0, 100)
    ax2.grid(True)
    st.pyplot(fig2)

    # === CSV EXPORT ===
    st.markdown("## 📤 Export Data as CSV")

    df_stage = pd.DataFrame(stage_data)
    df_summary = pd.DataFrame({
        "Metric": [
            "LED Power (W)", "Battery Capacity (Wh)", "Solar Panel (W)", "Battery Voltage (V)",
            "Total Night Load (Wh)", "Solar Recovery (Wh)", "Energy Balance (Wh)",
            "Suggested Battery (Wh)", f"Suggested Battery (Ah) @ {int(system_voltage)}V"
        ],
        "Value": [
            load_power, battery_capacity_wh, solar_panel_wattage, system_voltage,
            total_energy, solar_energy, energy_balance,
            required_battery_wh, required_battery_ah
        ]
    })

    csv_stage = df_stage.to_csv(index=False)
    csv_summary = df_summary.to_csv(index=False)

    st.download_button("📥 Download Dimming Profile CSV", data=csv_stage, file_name="dimming_profile.csv", mime="text/csv")
    st.download_button("📥 Download Summary CSV", data=csv_summary, file_name="system_summary.csv", mime="text/csv")

except Exception as e:
    st.error(f"🚨 An unexpected error occurred: {e}")
