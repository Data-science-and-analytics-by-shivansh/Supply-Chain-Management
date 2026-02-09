import pandas as pd
import matplotlib.pyplot as plt
from pulp import LpMinimize, LpProblem, LpVariable, lpSum, value

# Load data
df = pd.read_csv('data/lpi_dataset.csv')

# Clean (assume no nulls for simplicity)
df = df.dropna()

# KPIs
on_time_rate = (df['Timeliness'] > 3.5).mean() * 100
print(f"On-Time Delivery Rate: {on_time_rate}%")

# Trends
yearly_timeliness = df.groupby('Year')['Timeliness'].mean()
yearly_timeliness.plot(title='Delivery Timeliness Trends')
plt.savefig('outputs/timeliness_trends.png')

# What-If Optimization (Minimize costs with constraints)
# Assume costs based on scores; e.g., low score = high cost
countries = df['Country_Name'].unique()[:5]  # Sample
prob = LpProblem("SupplyChainOpt", LpMinimize)
x = {c: LpVariable(f"x_{c}", lowBound=0) for c in countries}  # Allocation
costs = {c: 100 / df[df['Country_Name'] == c]['LPI_Score'].mean() for c in countries}  # Inverse score as cost

prob += lpSum([costs[c] * x[c] for c in countries])  # Minimize total cost
prob += lpSum([x[c] for c in countries]) == 100  # Total allocation 100%
for c in countries:
    prob += x[c] <= 30  # Max per supplier

prob.solve()
print("Optimized Allocations:")
for c in countries:
    print(f"{c}: {value(x[c])}")

# Save results
df.to_csv('outputs/optimized_data.csv', index=False)
