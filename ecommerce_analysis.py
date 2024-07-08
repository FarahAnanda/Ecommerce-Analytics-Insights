# Loading libraries
import numpy as np
import pandas as pd
from datetime import date,datetime

import seaborn as sns
import matplotlib.pyplot as plt

# Load the datasets
orders = pd.read_csv("orders.csv")
product_supplier = pd.read_csv("product_supplier.csv")

# Join the datasets on 'Product ID'
merged_data = pd.merge(orders, product_supplier, on='Product ID', how='left')

# Cleaning the data by :
# Removing the inconsistency in Customer Status
merged_data['Customer Status'] = merged_data['Customer Status'].str.capitalize()

# Dropping data with missing value (if any)
print(merged_data.isnull().sum()) # Check missing values, and there's none.

# Drop duplicates data (if any)
print(merged_data['Order ID'].value_counts()) # Check duplicates, and there's none.

# Calculate profit percentage
merged_data['unit_price'] = merged_data['Total Retail Price for This Order'] / merged_data['Quantity Ordered']

grouped_median = merged_data.groupby('Product Category')[['unit_price', 'Cost Price Per Unit']].median()
grouped_median['profit_percentage'] = ((grouped_median['unit_price'] - grouped_median['Cost Price Per Unit']) / grouped_median['Cost Price Per Unit']) * 100

# Find top 5 highest profit percentage
top_5_categories = grouped_median['profit_percentage'].nlargest(5)

# Plotting bar chart
plt.figure(figsize=(10, 8))
ax = sns.barplot(x=top_5_categories.index, y=top_5_categories.values, hue=top_5_categories.index, palette="Set2", err_kws={'color': 'black', 'linewidth': 0}, capsize=0, legend=False)

# Adding labels to the bars
for p in ax.patches:
    ax.annotate(f'{p.get_height():.2f}%', (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', xytext=(0, 10), textcoords='offset points')

plt.title('Product Categories with Highest Profit Percentage')
plt.xlabel('Product Category')
plt.ylabel('Profit Percentage (%)')
plt.xticks(rotation=0)
plt.grid(False)
plt.show()

# Convert 'Date Order was placed' to datetime
merged_data['Date Order was placed'] = pd.to_datetime(merged_data['Date Order was placed'], format='%d-%b-%y')

# Calculate profit
merged_data['Profit'] = merged_data['Total Retail Price for This Order'] - merged_data['Cost Price Per Unit']

# Group by year and month
merged_data['Year'] = merged_data['Date Order was placed'].dt.year
merged_data['Month'] = merged_data['Date Order was placed'].dt.month
monthly_profit = merged_data.groupby(['Year', 'Month'])['Profit'].sum().reset_index()

# Plotting line chart
plt.figure(figsize=(10, 6))
sns.lineplot(data=monthly_profit, x='Month', y='Profit', hue='Year', palette=sns.color_palette("ch:s=-.2,r=.6", as_cmap=True), linewidth=2.5)
plt.title('Monthly Profit Over Years')
plt.xlabel('Month')
plt.ylabel('Profit')
plt.legend(title='Year')
plt.grid(False)
plt.show()

# Plotting scatter plots
plt.figure(figsize=(12, 6))

# Scatter plot for cost price vs profit
plt.subplot(1, 2, 1)
sns.scatterplot(data=merged_data, x='Cost Price Per Unit', y='Profit')
plt.xlabel('Cost Price Per Unit')
plt.ylabel('Profit')
plt.grid(False)

# Scatter plot for cost price vs quantity ordered
plt.subplot(1, 2, 2)
sns.scatterplot(data=merged_data, x='unit_price', y='Quantity Ordered')
plt.xlabel('Unit Price')
plt.ylabel('Quantity Ordered')
plt.grid(False)

plt.tight_layout()
plt.show()

# Filter the data for the latest year
latest_year = merged_data['Year'].max()
latest_year_data = merged_data[merged_data['Year'] == latest_year]

# Group by product category and sum the quantity ordered for each category
category_quantity = latest_year_data.groupby('Product Category')['Quantity Ordered'].sum()

# Sort the categories based on the total quantity ordered
category_quantity_sorted = category_quantity.sort_values(ascending=False)

# Select the top 3 categories
top_3_categories = category_quantity_sorted.head(3)

# Plotting bar chart using seaborn with hue
plt.figure(figsize=(8, 6))
ax = sns.barplot(x=top_3_categories.index, y=top_3_categories.values, hue=top_3_categories.index, palette="rocket", dodge=False, legend=False)
plt.title('Most Favorite Products in {}'.format(latest_year))
plt.xlabel('Product Category')
plt.ylabel('Quantity Ordered')
plt.xticks(rotation=0)
plt.grid(False)

# Add labels to the bars
for p in ax.patches:
    ax.annotate('{:.0f}'.format(p.get_height()), (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', fontsize=10, color='black', xytext=(0, 5), textcoords='offset points')

plt.show()

# Convert 'Delivery Date' to datetime
merged_data['Delivery Date'] = pd.to_datetime(merged_data['Delivery Date'], format='%d-%b-%y')

# Calculate order to delivery length
merged_data['delivery_time'] = (merged_data['Delivery Date'] - merged_data['Date Order was placed']).dt.days
latest_year_data = merged_data[merged_data['Year'] == latest_year]

# Calculate median and maximum order-to-delivery length
delivery_stats = latest_year_data.groupby(pd.Grouper(key='Date Order was placed', freq='M'))['delivery_time'].agg(['median', 'max'])
delivery_stats['median'] = delivery_stats['median'].round(1)

delivery_stats['Month'] = delivery_stats.index.strftime('%-m')
delivery_stats.set_index('Month', inplace=True)
delivery_stats.columns = ['order_to_delivery_length', 'the_longest_order_to_delivery_length']

print("The order-to-delivery length of every month in the latest year:")
print(delivery_stats)

# Filter orders for the latest 3 months
latest_months = merged_data.groupby(merged_data['Date Order was placed'].dt.to_period('M'))['Order ID'].count().reset_index()
latest_3_months = latest_months.nlargest(3, columns='Date Order was placed')
latest_3_months = latest_3_months['Date Order was placed']

latest_orders = merged_data[merged_data['Date Order was placed'].dt.to_period('M').isin(latest_3_months)]

# Filter active loyal customers
active_orders = latest_orders.groupby('Customer ID').filter(lambda x: x['Order ID'].nunique() > 3)

total_loyal_customers = len(active_orders['Customer ID'].unique())
print("Total active loyal customers:", total_loyal_customers)

loyal_customers = active_orders.groupby('Customer ID').size().reset_index()
loyal_customers.columns = ['Customer ID', 'Order Count']

print("Customer ID of active loyal customer:")
loyal_customers[['Customer ID']]

def apply_multiplier(status):
  if status == 'Silver':
    return 1
  elif status == 'Gold':
    return 2
  elif status == 'Platinum':
    return 3

tier = active_orders
unique_customer_count = active_orders['Customer ID'].nunique()

tier['Proportion'] = tier['Customer Status'].apply(apply_multiplier)

tier = tier.groupby(['Customer ID', 'Customer Status'])['Proportion'].max().reset_index()

tier_sorted = tier.sort_values(by = ['Customer ID', 'Proportion'], ascending=[True, False])
tier_status = tier_sorted.drop_duplicates(subset = 'Customer ID', keep = 'first')
tier_status = tier_status.groupby(['Customer ID', 'Customer Status'])['Proportion'].count().reset_index()

# Pie chart
plt.figure(figsize=(8, 8))
tier_status['Customer Status'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=sns.color_palette("vlag"), labels=None)
plt.title('Proportion of Status Among Loyal Customers')
plt.ylabel('')
plt.legend(labels=tier_status['Customer Status'].value_counts().index, loc='upper right')
plt.axis('equal')
plt.show()
