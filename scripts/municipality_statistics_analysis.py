"""
Municipality Statistics Analysis Script

This script performs correlation and linear regression analysis to predict
the expected number of parcel points based on:
- Number of inhabitants
- Area (km²)

It generates a comprehensive report with:
- Correlation coefficients
- Linear regression model
- Predictions vs actual values
- Municipality rankings
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


def load_municipalities_data():
    """Load municipality population data."""
    municipalities_file = Path(__file__).parent.parent / "webapp" / "public" / "municipalities.json"

    with open(municipalities_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Convert to dict keyed by slug, excluding "Nederland"
    municipalities = {}
    for muni in data:
        if muni['slug'] != 'nederland':
            municipalities[muni['slug']] = {
                'name': muni['name'],
                'population': muni.get('population', 0),
                'province': muni.get('province', ''),
                'slug': muni['slug']
            }

    return municipalities


def load_parcel_point_counts():
    """Load parcel point counts by reading all GeoJSON files."""
    data_dir = Path(__file__).parent.parent / "webapp" / "public" / "data"

    counts = {}
    geojson_files = list(data_dir.glob("*.geojson"))

    print(f"  Scanning {len(geojson_files)} GeoJSON files...")

    for geojson_file in geojson_files:
        slug = geojson_file.stem

        # Skip nederland and boundary files
        if slug == 'nederland' or slug.startswith('provincie-'):
            continue

        try:
            with open(geojson_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Count pakketpunt features
            pakketpunt_count = sum(
                1 for feature in data.get('features', [])
                if feature.get('properties', {}).get('type') == 'pakketpunt'
            )

            # Get gemeente name from metadata or first feature
            gemeente_name = data.get('metadata', {}).get('gemeente', '')
            if not gemeente_name and data.get('features'):
                # Try to infer from slug
                gemeente_name = slug.replace('-', ' ').title()

            counts[slug] = {
                'gemeente': gemeente_name,
                'count': pakketpunt_count
            }

        except Exception as e:
            print(f"  Warning: Could not read {geojson_file.name}: {e}")
            continue

    return counts


def load_cbs_area_data():
    """Load CBS area data from cached file."""
    area_file = Path(__file__).parent.parent / "data" / "cbs_municipality_areas.json"

    if not area_file.exists():
        print(f"ERROR: CBS area data not found at {area_file}")
        print("Please run: python scripts/fetch_cbs_municipality_data.py")
        return {}

    with open(area_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def normalize_name(name):
    """Normalize municipality name for matching."""
    # Handle special cases and common variations
    name_map = {
        'Den Haag': ['Den Haag', "'s-Gravenhage", 's-Gravenhage', "'s-Gravenhage (gemeente)"],
        "'s-Gravenhage": ['Den Haag', "'s-Gravenhage", 's-Gravenhage', "'s-Gravenhage (gemeente)"],
        's-Gravenhage': ['Den Haag', "'s-Gravenhage", 's-Gravenhage', "'s-Gravenhage (gemeente)"],
        'Súdwest-Fryslân': ['Súdwest-Fryslân', 'Sudwest-Fryslân', 'SudWest Fryslan'],
        'Sudwest-Fryslân': ['Súdwest-Fryslân', 'Sudwest-Fryslân', 'SudWest Fryslan'],
        's-Hertogenbosch': ["'s-Hertogenbosch", 's-Hertogenbosch', 'Den Bosch'],
        "'s-Hertogenbosch": ["'s-Hertogenbosch", 's-Hertogenbosch', 'Den Bosch'],
        'Beek': ['Beek', 'Beek (L.)'],
        'Groningen': ['Groningen', 'Groningen (gemeente)'],
        'Hengelo': ['Hengelo', 'Hengelo (O.)'],
        'Laren': ['Laren', 'Laren (NH.)'],
        'Middelburg': ['Middelburg', 'Middelburg (Z.)'],
        'Nuenen': ['Nuenen', 'Nuenen, Gerwen en Nederwetten', 'Nuenen c.a.'],
        'Rijswijk': ['Rijswijk', 'Rijswijk (ZH.)'],
        'Stein': ['Stein', 'Stein (L.)'],
        'Utrecht': ['Utrecht', 'Utrecht (gemeente)'],
    }

    if name in name_map:
        return name_map[name]

    # Also try with/without "(gemeente)" suffix and stripped parentheses
    variants = [name]
    if '(' in name:
        base_name = name.split('(')[0].strip()
        variants.append(base_name)

    # Try adding "(gemeente)" suffix
    variants.append(f"{name} (gemeente)")

    return variants


def match_area_data(municipalities, cbs_area_data):
    """Match CBS area data to municipalities."""

    matched = {}
    unmatched = []

    # Create a case-insensitive lookup for CBS data
    cbs_lookup = {name.lower(): data for name, data in cbs_area_data.items()}

    for slug, muni_data in municipalities.items():
        muni_name = muni_data['name']
        area_km2 = None

        # Try exact match first
        if muni_name in cbs_area_data:
            area_km2 = cbs_area_data[muni_name]['area_km2']
        else:
            # Try case-insensitive match
            if muni_name.lower() in cbs_lookup:
                area_km2 = cbs_lookup[muni_name.lower()]['area_km2']
            else:
                # Try normalized names
                for variant in normalize_name(muni_name):
                    if variant in cbs_area_data:
                        area_km2 = cbs_area_data[variant]['area_km2']
                        break
                    elif variant.lower() in cbs_lookup:
                        area_km2 = cbs_lookup[variant.lower()]['area_km2']
                        break

        if area_km2 is not None:
            matched[slug] = area_km2
        else:
            unmatched.append(muni_name)

    if unmatched:
        print(f"\n  Warning: Could not match area data for {len(unmatched)} municipalities:")
        for name in sorted(unmatched)[:15]:
            print(f"    - {name}")
        if len(unmatched) > 15:
            print(f"    ... and {len(unmatched) - 15} more")

    return matched


def combine_data(municipalities, parcel_counts, area_data):
    """Combine all data sources into a single dataframe."""

    combined = []
    skipped = {'no_parcel_data': 0, 'zero_parcel_points': 0, 'no_area_data': 0}

    for slug, muni_data in municipalities.items():
        if slug not in parcel_counts:
            skipped['no_parcel_data'] += 1
            continue  # Skip municipalities without parcel data

        # Skip municipalities with 0 parcel points
        parcel_point_count = parcel_counts[slug]['count']
        if parcel_point_count == 0:
            skipped['zero_parcel_points'] += 1
            continue

        if slug not in area_data:
            skipped['no_area_data'] += 1
            continue  # Skip municipalities without area data

        combined.append({
            'gemeente': muni_data['name'],
            'slug': slug,
            'province': muni_data['province'],
            'population': muni_data['population'],
            'area_km2': area_data[slug],
            'parcel_points': parcel_point_count
        })

    df = pd.DataFrame(combined)

    # Calculate additional metrics
    df['population_density'] = df['population'] / df['area_km2']
    df['parcel_points_per_1000_people'] = (df['parcel_points'] / df['population']) * 1000
    df['parcel_points_per_km2'] = df['parcel_points'] / df['area_km2']

    # Print skip summary
    print(f"\n  Skipped municipalities:")
    print(f"    - No parcel data file: {skipped['no_parcel_data']}")
    print(f"    - Zero parcel points: {skipped['zero_parcel_points']}")
    print(f"    - No area data: {skipped['no_area_data']}")

    return df


def calculate_correlations(df):
    """Calculate correlation coefficients."""

    correlations = {}

    # Parcel points vs population
    corr_pop, pval_pop = stats.pearsonr(df['population'], df['parcel_points'])
    correlations['population'] = {
        'correlation': corr_pop,
        'p_value': pval_pop
    }

    # Parcel points vs area
    corr_area, pval_area = stats.pearsonr(df['area_km2'], df['parcel_points'])
    correlations['area_km2'] = {
        'correlation': corr_area,
        'p_value': pval_area
    }

    # Parcel points vs population density
    corr_density, pval_density = stats.pearsonr(df['population_density'], df['parcel_points'])
    correlations['population_density'] = {
        'correlation': corr_density,
        'p_value': pval_density
    }

    return correlations


def build_linear_regression_model(df):
    """Build linear regression model using population and area as predictors."""

    # Prepare features (X) and target (y)
    X = df[['population', 'area_km2']].values
    y = df['parcel_points'].values

    # Build model
    model = LinearRegression()
    model.fit(X, y)

    # Make predictions
    y_pred = model.predict(X)

    # Calculate metrics
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))

    # Add predictions to dataframe
    df['predicted_parcel_points'] = y_pred
    df['prediction_error'] = df['parcel_points'] - df['predicted_parcel_points']
    df['prediction_error_pct'] = (df['prediction_error'] / df['parcel_points']) * 100

    return {
        'model': model,
        'r2_score': r2,
        'mae': mae,
        'rmse': rmse,
        'coefficients': {
            'population': model.coef_[0],
            'area_km2': model.coef_[1],
            'intercept': model.intercept_
        }
    }


def generate_report(df, correlations, regression_results):
    """Generate a comprehensive analysis report."""

    report = []
    report.append("=" * 80)
    report.append("MUNICIPALITY PARCEL POINTS STATISTICAL ANALYSIS")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total municipalities analyzed: {len(df)}")
    report.append("")

    # Summary statistics
    report.append("-" * 80)
    report.append("SUMMARY STATISTICS")
    report.append("-" * 80)
    report.append(f"Total parcel points: {df['parcel_points'].sum():,.0f}")
    report.append(f"Average parcel points per municipality: {df['parcel_points'].mean():.1f}")
    report.append(f"Median parcel points per municipality: {df['parcel_points'].median():.1f}")
    report.append(f"Std deviation: {df['parcel_points'].std():.1f}")
    report.append("")
    report.append(f"Average parcel points per 1,000 people: {df['parcel_points_per_1000_people'].mean():.2f}")
    report.append(f"Average parcel points per km²: {df['parcel_points_per_km2'].mean():.2f}")
    report.append("")

    # Correlation analysis
    report.append("-" * 80)
    report.append("CORRELATION ANALYSIS")
    report.append("-" * 80)
    report.append("Pearson correlation coefficients (with parcel points):")
    report.append("")

    for variable, data in correlations.items():
        corr = data['correlation']
        pval = data['p_value']
        strength = "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"
        direction = "positive" if corr > 0 else "negative"

        report.append(f"  {variable.replace('_', ' ').title()}:")
        report.append(f"    Correlation: {corr:+.4f} ({strength} {direction})")
        report.append(f"    P-value: {pval:.6f} {'***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else ''}")
        report.append("")

    # Linear regression
    report.append("-" * 80)
    report.append("LINEAR REGRESSION MODEL")
    report.append("-" * 80)
    report.append("Model: Parcel Points = α + β₁(Population) + β₂(Area km²)")
    report.append("")
    report.append(f"  Intercept (α): {regression_results['coefficients']['intercept']:.4f}")
    report.append(f"  Population coefficient (β₁): {regression_results['coefficients']['population']:.6f}")
    report.append(f"  Area coefficient (β₂): {regression_results['coefficients']['area_km2']:.6f}")
    report.append("")
    report.append("Model Performance:")
    report.append(f"  R² Score: {regression_results['r2_score']:.4f} ({regression_results['r2_score']*100:.1f}% variance explained)")
    report.append(f"  Mean Absolute Error: {regression_results['mae']:.2f} parcel points")
    report.append(f"  Root Mean Squared Error: {regression_results['rmse']:.2f} parcel points")
    report.append("")

    # Interpretation
    report.append("-" * 80)
    report.append("INTERPRETATION")
    report.append("-" * 80)

    pop_coef = regression_results['coefficients']['population']
    area_coef = regression_results['coefficients']['area_km2']

    report.append(f"For every 1,000 additional inhabitants: ~{pop_coef*1000:.2f} additional parcel points expected")
    report.append(f"For every 1 km² additional area: ~{area_coef:.2f} additional parcel points expected")
    report.append("")

    # Top/bottom performers
    df_sorted_error = df.sort_values('prediction_error', ascending=False)

    report.append("-" * 80)
    report.append("TOP 10 OVERPERFORMING MUNICIPALITIES")
    report.append("-" * 80)
    report.append("(More parcel points than predicted)")
    report.append("")
    report.append(f"{'Municipality':<25} {'Actual':>8} {'Predicted':>10} {'Difference':>11} {'Error %':>9}")
    report.append("-" * 80)

    for _, row in df_sorted_error.head(10).iterrows():
        report.append(f"{row['gemeente']:<25} {row['parcel_points']:>8.0f} {row['predicted_parcel_points']:>10.1f} "
                     f"{row['prediction_error']:>11.1f} {row['prediction_error_pct']:>8.1f}%")

    report.append("")
    report.append("-" * 80)
    report.append("TOP 10 UNDERPERFORMING MUNICIPALITIES")
    report.append("-" * 80)
    report.append("(Fewer parcel points than predicted)")
    report.append("")
    report.append(f"{'Municipality':<25} {'Actual':>8} {'Predicted':>10} {'Difference':>11} {'Error %':>9}")
    report.append("-" * 80)

    for _, row in df_sorted_error.tail(10).iterrows():
        report.append(f"{row['gemeente']:<25} {row['parcel_points']:>8.0f} {row['predicted_parcel_points']:>10.1f} "
                     f"{row['prediction_error']:>11.1f} {row['prediction_error_pct']:>8.1f}%")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)


def main():
    """Main analysis function."""

    print("Loading data...")

    # Load data from all sources
    municipalities = load_municipalities_data()
    print(f"  Loaded {len(municipalities)} municipalities")

    parcel_counts = load_parcel_point_counts()
    print(f"  Loaded parcel point data for {len(parcel_counts)} municipalities")

    cbs_area_data = load_cbs_area_data()
    print(f"  Loaded CBS area data for {len(cbs_area_data)} municipalities")

    if not cbs_area_data:
        print("\nPlease run: python scripts/fetch_cbs_municipality_data.py")
        sys.exit(1)

    # Match area data
    print("\nMatching area data to municipalities...")
    area_data = match_area_data(municipalities, cbs_area_data)
    print(f"  Successfully matched {len(area_data)} municipalities")

    # Combine all data
    print("\nCombining data...")
    df = combine_data(municipalities, parcel_counts, area_data)
    print(f"  Combined data for {len(df)} municipalities")

    if len(df) < 10:
        print("\nERROR: Not enough data for statistical analysis")
        sys.exit(1)

    # Calculate correlations
    print("\nCalculating correlations...")
    correlations = calculate_correlations(df)

    # Build regression model
    print("Building linear regression model...")
    regression_results = build_linear_regression_model(df)

    # Generate report
    print("\nGenerating report...")
    report = generate_report(df, correlations, regression_results)

    # Print report
    print("\n")
    print(report)

    # Save report
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    report_file = output_dir / "municipality_statistics_analysis.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")

    # Save detailed data
    data_file = output_dir / "municipality_statistics_data.json"
    output_data = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_municipalities': len(df),
            'total_parcel_points': int(df['parcel_points'].sum()),
            'avg_parcel_points': float(df['parcel_points'].mean()),
            'avg_per_1000_people': float(df['parcel_points_per_1000_people'].mean())
        },
        'correlations': {
            key: {
                'correlation': float(val['correlation']),
                'p_value': float(val['p_value'])
            }
            for key, val in correlations.items()
        },
        'regression_model': {
            'r2_score': float(regression_results['r2_score']),
            'mae': float(regression_results['mae']),
            'rmse': float(regression_results['rmse']),
            'coefficients': {
                key: float(val)
                for key, val in regression_results['coefficients'].items()
            }
        },
        'municipalities': df.to_dict('records')
    }

    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Detailed data saved to: {data_file}")

    # Save CSV for easy import
    csv_file = output_dir / "municipality_statistics_data.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"CSV data saved to: {csv_file}")

    print("\n✓ Analysis complete!")


if __name__ == "__main__":
    main()
