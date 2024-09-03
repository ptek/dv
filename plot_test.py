import pytest
import polars as pl
from polars.testing import assert_frame_equal
from datetime import datetime

from plot import calculate_hourly_stats, clean_data

TIME_COL_NAME = 'Timestamp (YYYY-MM-DDThh:mm:ss)'
VALUE_COL_NAME = 'Glucose Value (mg/dL)'
SCHEMA_CLEAN = {TIME_COL_NAME: pl.Datetime(time_zone=None), VALUE_COL_NAME: pl.Int32}
SCHEMA_COMPUTED = {"Hour": pl.Int8, "Mean Glucose Value": pl.Float64, "5th Percentile": pl.Float64, "25th Percentile": pl.Float64, "75th Percentile": pl.Float64, "95th Percentile": pl.Float64}


def test_empty_data_frame_will_not_break():
    assert_frame_equal(clean_data(pl.DataFrame()), pl.DataFrame())


def test_non_empty_row_is_retained():
    input = pl.DataFrame({
        TIME_COL_NAME: ["0001-01-01T00:00:00"],
        VALUE_COL_NAME: ["100"]
    })

    actual = clean_data(input)

    expected = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")],
        VALUE_COL_NAME: [100]
    }, SCHEMA_CLEAN)
    assert_frame_equal(actual, expected)


def test_low_value_is_replaced_with_30():
    input = pl.DataFrame({
        TIME_COL_NAME: ["0001-01-01T00:00:00"],
        VALUE_COL_NAME: ["Low"]
    })

    actual = clean_data(input)

    expected = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")],
        VALUE_COL_NAME: [30]
    }, SCHEMA_CLEAN)
    assert_frame_equal(actual, expected)


def test_empty_time_row_is_removed():
    input = pl.DataFrame({
        TIME_COL_NAME: ["", " ", None],
        VALUE_COL_NAME: ["100", "100", "100"]
    })

    actual = clean_data(input)
    expected = pl.DataFrame([], SCHEMA_CLEAN)
    assert_frame_equal(actual, expected)


def test_empty_value_row_is_removed():
    input = pl.DataFrame({
        TIME_COL_NAME: ["0001-01-01T00:00:00", "0001-01-01T00:00:00", "0001-01-01T00:00:00"],
        VALUE_COL_NAME: ["", " ", None]
    })

    actual = clean_data(input)
    expected = pl.DataFrame([], SCHEMA_CLEAN)
    assert_frame_equal(actual, expected)


def test_non_parseable_time_row_is_removed():
    input = pl.DataFrame({
        TIME_COL_NAME: ["UNPARSEABLE TIMESTAMP"],
        VALUE_COL_NAME: ["100"]
    })

    actual = clean_data(input)
    expected = pl.DataFrame([], SCHEMA_CLEAN)
    assert_frame_equal(actual, expected)


def test_non_parseable_value_row_is_removed():
    input = pl.DataFrame({
        TIME_COL_NAME: ["0001-01-01T00:00:00"],
        VALUE_COL_NAME: ["UNPARSEABLE VALUE"]
    })

    actual = clean_data(input)
    expected = pl.DataFrame([], SCHEMA_CLEAN)
    assert_frame_equal(actual, expected)


def test_negative_value_row_is_removed():
    input = pl.DataFrame({
        TIME_COL_NAME: ["0001-01-01T00:00:00"],
        VALUE_COL_NAME: ["-100"]
    })

    actual = clean_data(input)
    expected = pl.DataFrame([], SCHEMA_CLEAN)
    assert_frame_equal(actual, expected)


def test_additional_column_is_removed():
    input = pl.DataFrame({
        "EXTRA_COLUMN": ["EXTRA_DATA"],
        TIME_COL_NAME: ["0001-01-01T00:00:00"],
        VALUE_COL_NAME: ["-100"]
    })

    actual = clean_data(input)
    expected = pl.DataFrame([], SCHEMA_CLEAN)
    assert_frame_equal(actual, expected)


def test_hourly_calculation_of_empty_dataframe_is_empty():
    input = pl.DataFrame()

    actual = calculate_hourly_stats(input)
    expected = pl.DataFrame()
    assert_frame_equal(actual, expected)


def test_hourly_computation_for_one_value():
    input = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")],
        VALUE_COL_NAME: [100]
    }, SCHEMA_CLEAN)

    actual = calculate_hourly_stats(input)

    expected = pl.DataFrame({
        "Hour": [0],
        "Mean Glucose Value": [100.0],
        "5th Percentile": [100.0],
        "25th Percentile": [100.0],
        "75th Percentile": [100.0],
        "95th Percentile": [100.0],
    }, SCHEMA_COMPUTED)
    assert_frame_equal(actual, expected)

def test_5th_percentile_value():
    input = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")] * 100,
        VALUE_COL_NAME: [100]*95 + [0]*5
    }, SCHEMA_CLEAN)

    actual = calculate_hourly_stats(input)

    expected = pl.DataFrame({
        "Hour": [0],
        "Mean Glucose Value": [95.0],
        "5th Percentile": [100.0],
        "25th Percentile": [100.0],
        "75th Percentile": [100.0],
        "95th Percentile": [100.0],
    }, SCHEMA_COMPUTED)
    assert_frame_equal(actual, expected)

def test_5th_percentile_value_flip():
    input = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")] * 100,
        VALUE_COL_NAME: [100]*94 + [0]*6
    }, SCHEMA_CLEAN)

    actual = calculate_hourly_stats(input)

    expected = pl.DataFrame({
        "Hour": [0],
        "Mean Glucose Value": [94.0],
        "5th Percentile": [0.0],
        "25th Percentile": [100.0],
        "75th Percentile": [100.0],
        "95th Percentile": [100.0],
    }, SCHEMA_COMPUTED)
    assert_frame_equal(actual, expected)


def test_25th_percentile_value():
    input = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")] * 100,
        VALUE_COL_NAME: [100]*75 + [0]*25
    }, SCHEMA_CLEAN)

    actual = calculate_hourly_stats(input)

    expected = pl.DataFrame({
        "Hour": [0],
        "Mean Glucose Value": [75.0],
        "5th Percentile": [0.0],
        "25th Percentile": [100.0],
        "75th Percentile": [100.0],
        "95th Percentile": [100.0],
    }, SCHEMA_COMPUTED)
    assert_frame_equal(actual, expected)


def test_25th_percentile_value_flip():
    input = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")] * 100,
        VALUE_COL_NAME: [100]*74 + [0]*26
    }, SCHEMA_CLEAN)

    actual = calculate_hourly_stats(input)

    expected = pl.DataFrame({
        "Hour": [0],
        "Mean Glucose Value": [74.0],
        "5th Percentile": [0.0],
        "25th Percentile": [0.0],
        "75th Percentile": [100.0],
        "95th Percentile": [100.0],
    }, SCHEMA_COMPUTED)
    assert_frame_equal(actual, expected)


def test_75th_percentile_value():
    input = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")] * 100,
        VALUE_COL_NAME: [100]*26 + [0]*74
    }, SCHEMA_CLEAN)

    actual = calculate_hourly_stats(input)

    expected = pl.DataFrame({
        "Hour": [0],
        "Mean Glucose Value": [26.0],
        "5th Percentile": [0.0],
        "25th Percentile": [0.0],
        "75th Percentile": [100.0],
        "95th Percentile": [100.0],
    }, SCHEMA_COMPUTED)
    assert_frame_equal(actual, expected)


def test_75th_percentile_value_flip():
    input = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")] * 100,
        VALUE_COL_NAME: [100]*24 + [0]*76
    }, SCHEMA_CLEAN)

    actual = calculate_hourly_stats(input)

    expected = pl.DataFrame({
        "Hour": [0],
        "Mean Glucose Value": [24.0],
        "5th Percentile": [0.0],
        "25th Percentile": [0.0],
        "75th Percentile": [0.0],
        "95th Percentile": [100.0],
    }, SCHEMA_COMPUTED)
    assert_frame_equal(actual, expected)

def test_95th_percentile_value():
    input = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")] * 100,
        VALUE_COL_NAME: [100]*6 + [0]*94
    }, SCHEMA_CLEAN)

    actual = calculate_hourly_stats(input)

    expected = pl.DataFrame({
        "Hour": [0],
        "Mean Glucose Value": [6.0],
        "5th Percentile": [0.0],
        "25th Percentile": [0.0],
        "75th Percentile": [0.0],
        "95th Percentile": [100.0],
    }, SCHEMA_COMPUTED)
    assert_frame_equal(actual, expected)


def test_95th_percentile_value_flip():
    input = pl.DataFrame({
        TIME_COL_NAME: [t("0001-01-01T00:00:00")] * 100,
        VALUE_COL_NAME: [100]*5 + [0]*95
    }, SCHEMA_CLEAN)

    actual = calculate_hourly_stats(input)

    expected = pl.DataFrame({
        "Hour": [0],
        "Mean Glucose Value": [5.0],
        "5th Percentile": [0.0],
        "25th Percentile": [0.0],
        "75th Percentile": [0.0],
        "95th Percentile": [0.0],
    }, SCHEMA_COMPUTED)
    assert_frame_equal(actual, expected)

# ====================
# These are test helper functions

def t(datetime_string):
    return datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S')
