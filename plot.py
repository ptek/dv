#!/usr/bin/env python3

import argparse
import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

def read_exported_dexcom_values(file_path):
    """
    Read the DexCom csv export file
    """
    return pl.read_csv(file_path)

def clean_data(df):
    """
    Clean the empty values
    """

    # return empty data frame if the input is empty
    if df.is_empty():
        return df

    # Select only the timestamp and glucose value columns
    df = df.select(['Timestamp (YYYY-MM-DDThh:mm:ss)', 'Glucose Value (mg/dL)'])

    # Replace "Low" with 0 and drop rows with missing or non-numerical values
    df = df.with_columns([
        pl.col('Glucose Value (mg/dL)').replace("Low", 30).cast(pl.Int32, strict=False)
    ]).drop_nulls()

    # Replace negative values with null and drop them
    df = df.with_columns([
        pl.when(pl.col("Glucose Value (mg/dL)") < 0)
         .then(None)
         .otherwise(pl.col("Glucose Value (mg/dL)")) # keep original value
         .name.keep()
    ]).drop_nulls()


    # Convert timestamp to datetime
    df = df.with_columns([
        pl.col('Timestamp (YYYY-MM-DDThh:mm:ss)').str.strptime(pl.Datetime, format='%Y-%m-%dT%H:%M:%S', strict=False)
    ]).drop_nulls()

    return df

def calculate_hourly_stats(df):
    """
    Calculate the mean, 25th percentile, and 75th percentile glucose values for each hour.
    """

    # return empty data frame if the input is empty
    if df.is_empty():
        return df

    # Extract hour from the timestamp
    df = df.with_columns([
        pl.col('Timestamp (YYYY-MM-DDThh:mm:ss)').dt.hour().alias('Hour')
    ])

    hourly_stats = df.group_by('Hour').agg([
        pl.mean('Glucose Value (mg/dL)').alias('Mean Glucose Value'),
        pl.col('Glucose Value (mg/dL)').quantile(0.05).alias('5th Percentile'),
        pl.col('Glucose Value (mg/dL)').quantile(0.25).alias('25th Percentile'),
        pl.col('Glucose Value (mg/dL)').quantile(0.75).alias('75th Percentile'),
        pl.col('Glucose Value (mg/dL)').quantile(0.95).alias('95th Percentile')
    ]).sort('Hour')

    print(hourly_stats)

    return hourly_stats

def plot_hourly_stats(hourly_stats):
    """
    Plot the hourly mean, 25th percentile, and 75th percentile glucose values with a smooth line.
    """
    # Convert to pandas DataFrame for plotting
    hourly_stats_pd = hourly_stats.to_pandas()

    # Generate smooth x-values
    x = hourly_stats_pd['Hour']
    x_smooth = np.linspace(x.min(), x.max(), 300)

    # Interpolate y-values for smooth lines
    y_mean_smooth = make_interp_spline(x, hourly_stats_pd['Mean Glucose Value'])(x_smooth)
    y_5th_smooth = make_interp_spline(x, hourly_stats_pd['5th Percentile'])(x_smooth)
    y_25th_smooth = make_interp_spline(x, hourly_stats_pd['25th Percentile'])(x_smooth)
    y_75th_smooth = make_interp_spline(x, hourly_stats_pd['75th Percentile'])(x_smooth)
    y_95th_smooth = make_interp_spline(x, hourly_stats_pd['95th Percentile'])(x_smooth)

    # Plot the smooth lines
    plt.plot(x_smooth, y_mean_smooth, label='Mean Glucose Value')
    plt.plot(x_smooth, y_5th_smooth, label='5th Percentile')
    plt.plot(x_smooth, y_25th_smooth, label='25th Percentile')
    plt.plot(x_smooth, y_75th_smooth, label='75th Percentile')
    plt.plot(x_smooth, y_95th_smooth, label='95th Percentile')

    # Fill the areas between the percentiles
    plt.fill_between(x_smooth, 80, 200, color='lightgreen', alpha=0.3, label='Target Range')
    plt.fill_between(x_smooth, y_5th_smooth, y_95th_smooth, color='lightgray', alpha=0.5, label='5th-95th Percentile')
    plt.fill_between(x_smooth, y_25th_smooth, y_75th_smooth, color='gray', alpha=0.5, label='25th-75th Percentile')

    plt.xlabel('Hour of the Day')
    plt.ylabel('Glucose Value (mg/dL)')
    plt.title('Hourly Glucose Levels (95%, 75%, Mean, 25%, 5%)')
    plt.grid(True)
    plt.xticks(range(0, 24))
    # plt.legend()
    plt.savefig('plot.png')

def main():
    parser = argparse.ArgumentParser(description='Plot hourly glucose levels from a CSV file.')
    parser.add_argument('file_path', type=str, help='Path to the CSV file')
    args = parser.parse_args()

    df = read_exported_dexcom_values(args.file_path)
    df = clean_data(df)
    hourly_stats = calculate_hourly_stats(df)
    plot_hourly_stats(hourly_stats)

if __name__ == "__main__":
    main()
