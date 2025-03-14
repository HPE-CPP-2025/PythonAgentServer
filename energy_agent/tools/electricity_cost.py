from langchain_core.tools import tool

@tool
def calculate_electricity_cost(energy_kwh: float, tariff_inr: float = 8.0):
    """
    Calculate electricity cost based on energy usage.

    :param energy_kwh: Energy consumed in kWh
    :param tariff_inr: Electricity tariff in INR per kWh (default is 8.0 INR/kWh)
    :return: Total cost in INR
    """
    if energy_kwh < 0:
        return {"error": "Energy consumption cannot be negative."}

    total_cost = energy_kwh * tariff_inr
    return {
        "energy_kwh": energy_kwh,
        "tariff_inr_per_kwh": tariff_inr,
        "total_cost_inr": total_cost
    }
