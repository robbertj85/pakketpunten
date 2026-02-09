"""
Generate a professional PDF report for municipality statistics analysis.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def load_analysis_data():
    """Load the analysis results from JSON."""
    data_file = Path(__file__).parent.parent / "output" / "municipality_statistics_data.json"

    if not data_file.exists():
        print("ERROR: Analysis data not found. Please run municipality_statistics_analysis.py first.")
        sys.exit(1)

    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_correlation_chart(data, output_path):
    """Create correlation bar chart."""
    correlations = data['correlations']

    variables = ['Inwoners', 'Oppervlakte (km²)', 'Bevolkingsdichtheid']
    values = [
        correlations['population']['correlation'],
        correlations['area_km2']['correlation'],
        correlations['population_density']['correlation']
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors_list = ['#2ecc71' if v > 0.5 else '#f39c12' if v > 0.3 else '#e74c3c' for v in values]

    bars = ax.barh(variables, values, color=colors_list, edgecolor='black', linewidth=1.5)

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        ax.text(val + 0.02, i, f'{val:.4f}', va='center', fontsize=10, fontweight='bold')

    ax.set_xlabel('Pearson Correlatie Coëfficiënt', fontsize=12, fontweight='bold')
    ax.set_title('Correlatie met Aantal Pakketpunten', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(-0.1, 1.0)
    ax.axvline(x=0, color='black', linewidth=0.8)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def create_scatter_plot(data, output_path):
    """Create actual vs predicted scatter plot."""
    df = pd.DataFrame(data['municipalities'])

    fig, ax = plt.subplots(figsize=(10, 8))

    # Scatter plot
    ax.scatter(df['predicted_parcel_points'], df['parcel_points'],
              alpha=0.6, s=80, edgecolors='black', linewidth=0.5, color='#3498db')

    # Perfect prediction line
    min_val = min(df['predicted_parcel_points'].min(), df['parcel_points'].min())
    max_val = max(df['predicted_parcel_points'].max(), df['parcel_points'].max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfecte voorspelling')

    ax.set_xlabel('Voorspeld Aantal Pakketpunten', fontsize=12, fontweight='bold')
    ax.set_ylabel('Werkelijk Aantal Pakketpunten', fontsize=12, fontweight='bold')
    ax.set_title('Voorspeld vs Werkelijk Aantal Pakketpunten', fontsize=14, fontweight='bold', pad=20)
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    # Add R² score
    r2 = data['regression_model']['r2_score']
    ax.text(0.05, 0.95, f'R² = {r2:.4f}', transform=ax.transAxes,
           fontsize=12, fontweight='bold', verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def create_distribution_chart(data, output_path):
    """Create distribution histogram."""
    df = pd.DataFrame(data['municipalities'])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Population distribution
    ax1.hist(df['parcel_points'], bins=30, color='#3498db', edgecolor='black', alpha=0.7)
    ax1.set_xlabel('Aantal Pakketpunten', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Aantal Gemeenten', fontsize=11, fontweight='bold')
    ax1.set_title('Verdeling Pakketpunten', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.axvline(df['parcel_points'].mean(), color='red', linestyle='--', linewidth=2, label=f'Gemiddelde: {df["parcel_points"].mean():.1f}')
    ax1.legend()

    # Error distribution
    ax2.hist(df['prediction_error_pct'], bins=30, color='#e74c3c', edgecolor='black', alpha=0.7)
    ax2.set_xlabel('Voorspellingsfout (%)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Aantal Gemeenten', fontsize=11, fontweight='bold')
    ax2.set_title('Verdeling Voorspellingsfouten', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    ax2.axvline(0, color='green', linestyle='--', linewidth=2, label='Perfecte voorspelling')
    ax2.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def generate_pdf_report(data):
    """Generate the complete PDF report."""

    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    pdf_path = output_dir / "municipality_statistics_report.pdf"

    # Generate charts
    print("Generating charts...")
    chart_dir = output_dir / "charts"
    chart_dir.mkdir(exist_ok=True)

    correlation_chart = chart_dir / "correlation.png"
    scatter_chart = chart_dir / "scatter.png"
    distribution_chart = chart_dir / "distribution.png"

    create_correlation_chart(data, correlation_chart)
    create_scatter_plot(data, scatter_chart)
    create_distribution_chart(data, distribution_chart)

    # Create PDF
    print("Creating PDF document...")
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                           topMargin=1.5*cm, bottomMargin=1.5*cm,
                           leftMargin=2*cm, rightMargin=2*cm)

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2980b9'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )

    # Cover Page
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("Statistische Analyse", title_style))
    story.append(Paragraph("Pakketpunten Dekking", title_style))
    story.append(Paragraph("Nederlandse Gemeenten", title_style))
    story.append(Spacer(1, 2*cm))

    summary = data['summary']
    cover_info = f"""
    <para align=center fontSize=12>
    <b>Analysedatum:</b> {datetime.now().strftime('%d %B %Y')}<br/>
    <b>Gemeenten geanalyseerd:</b> {summary['total_municipalities']}<br/>
    <b>Totaal pakketpunten:</b> {summary['total_parcel_points']:,}<br/>
    <b>R² Score:</b> {data['regression_model']['r2_score']:.1%}
    </para>
    """
    story.append(Paragraph(cover_info, body_style))
    story.append(PageBreak())

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading1_style))

    exec_summary = f"""
    Deze analyse onderzoekt de relatie tussen gemeentekenmerken (inwonersaantal en oppervlakte)
    en het aantal pakketpunten in {summary['total_municipalities']} Nederlandse gemeenten.
    In totaal zijn {summary['total_parcel_points']:,} pakketpunten geanalyseerd.
    <br/><br/>
    <b>Belangrijkste bevindingen:</b>
    <br/>
    • Het aantal inwoners vertoont een <b>sterke positieve correlatie</b> (r = {data['correlations']['population']['correlation']:.3f})
    met het aantal pakketpunten
    <br/>
    • De oppervlakte van de gemeente heeft een <b>zwakke positieve correlatie</b> (r = {data['correlations']['area_km2']['correlation']:.3f})
    <br/>
    • Het lineaire regressiemodel verklaart <b>{data['regression_model']['r2_score']:.1%}</b> van de variantie
    <br/>
    • Gemiddeld zijn er <b>{summary['avg_per_1000_people']:.2f}</b> pakketpunten per 1.000 inwoners
    <br/>
    • Voor elke 1.000 extra inwoners worden ongeveer <b>{data['regression_model']['coefficients']['population']*1000:.2f}</b>
    extra pakketpunten voorspeld
    """
    story.append(Paragraph(exec_summary, body_style))
    story.append(Spacer(1, 0.5*cm))

    # Summary Statistics Table
    story.append(Paragraph("Samenvattende Statistieken", heading2_style))

    summary_data = [
        ['Statistiek', 'Waarde'],
        ['Totaal gemeenten', f"{summary['total_municipalities']}"],
        ['Totaal pakketpunten', f"{summary['total_parcel_points']:,}"],
        ['Gemiddeld per gemeente', f"{summary['avg_parcel_points']:.1f}"],
        ['Per 1.000 inwoners', f"{summary['avg_per_1000_people']:.2f}"],
    ]

    summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
    ]))
    story.append(summary_table)
    story.append(PageBreak())

    # Correlation Analysis
    story.append(Paragraph("Correlatie Analyse", heading1_style))
    story.append(Paragraph(
        "De onderstaande grafiek toont de Pearson correlatie coëfficiënten tussen gemeentekenmerken "
        "en het aantal pakketpunten. Een waarde van 1 betekent perfecte positieve correlatie.",
        body_style
    ))
    story.append(Spacer(1, 0.5*cm))

    img = Image(str(correlation_chart), width=15*cm, height=9*cm)
    story.append(img)

    # Correlation interpretation
    corr_interp = """
    <b>Interpretatie:</b><br/>
    • <b>Inwoners</b>: Sterke positieve correlatie - gemeenten met meer inwoners hebben doorgaans meer pakketpunten<br/>
    • <b>Oppervlakte</b>: Zwakke positieve correlatie - grotere gemeenten hebben iets meer pakketpunten<br/>
    • <b>Bevolkingsdichtheid</b>: Matige correlatie - dichter bevolkte gebieden hebben meer pakketpunten
    """
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(corr_interp, body_style))
    story.append(PageBreak())

    # Regression Model
    story.append(Paragraph("Lineair Regressiemodel", heading1_style))

    model = data['regression_model']
    model_desc = f"""
    Het lineaire regressiemodel voorspelt het aantal pakketpunten op basis van het aantal inwoners en de oppervlakte:
    <br/><br/>
    <b>Pakketpunten = {model['coefficients']['intercept']:.2f} +
    {model['coefficients']['population']:.6f} × Inwoners +
    {model['coefficients']['area_km2']:.6f} × Oppervlakte (km²)</b>
    <br/><br/>
    <b>Model Prestaties:</b><br/>
    • R² Score: <b>{model['r2_score']:.4f}</b> ({model['r2_score']:.1%} variantie verklaard)<br/>
    • Mean Absolute Error (MAE): <b>{model['mae']:.2f}</b> pakketpunten<br/>
    • Root Mean Squared Error (RMSE): <b>{model['rmse']:.2f}</b> pakketpunten
    """
    story.append(Paragraph(model_desc, body_style))
    story.append(Spacer(1, 0.5*cm))

    img2 = Image(str(scatter_chart), width=14*cm, height=11.2*cm)
    story.append(img2)
    story.append(PageBreak())

    # Distribution Analysis
    story.append(Paragraph("Verdelingsanalyse", heading1_style))
    story.append(Paragraph(
        "De onderstaande grafieken tonen de verdeling van pakketpunten over gemeenten "
        "en de nauwkeurigheid van het voorspellingsmodel.",
        body_style
    ))
    story.append(Spacer(1, 0.5*cm))

    img3 = Image(str(distribution_chart), width=16*cm, height=5.7*cm)
    story.append(img3)
    story.append(Spacer(1, 0.5*cm))

    # Top Performers
    story.append(Paragraph("Top 10 Overperformers", heading2_style))
    story.append(Paragraph(
        "Gemeenten met significant meer pakketpunten dan voorspeld door het model:",
        body_style
    ))

    df = pd.DataFrame(data['municipalities'])
    top_over = df.nlargest(10, 'prediction_error')

    over_data = [['Gemeente', 'Werkelijk', 'Voorspeld', 'Verschil', 'Afwijking %']]
    for _, row in top_over.iterrows():
        over_data.append([
            row['gemeente'][:25],
            f"{int(row['parcel_points'])}",
            f"{row['predicted_parcel_points']:.1f}",
            f"+{row['prediction_error']:.1f}",
            f"+{row['prediction_error_pct']:.1f}%"
        ])

    over_table = Table(over_data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    over_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f8f5')]),
    ]))
    story.append(over_table)
    story.append(Spacer(1, 1*cm))

    # Bottom Performers
    story.append(Paragraph("Top 10 Underperformers", heading2_style))
    story.append(Paragraph(
        "Gemeenten met significant minder pakketpunten dan voorspeld door het model:",
        body_style
    ))

    top_under = df.nsmallest(10, 'prediction_error')

    under_data = [['Gemeente', 'Werkelijk', 'Voorspeld', 'Verschil', 'Afwijking %']]
    for _, row in top_under.iterrows():
        under_data.append([
            row['gemeente'][:25],
            f"{int(row['parcel_points'])}",
            f"{row['predicted_parcel_points']:.1f}",
            f"{row['prediction_error']:.1f}",
            f"{row['prediction_error_pct']:.1f}%"
        ])

    under_table = Table(under_data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    under_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fadbd8')]),
    ]))
    story.append(under_table)
    story.append(PageBreak())

    # Conclusions
    story.append(Paragraph("Conclusies en Aanbevelingen", heading1_style))

    conclusions = """
    <b>Belangrijkste Conclusies:</b><br/><br/>

    1. <b>Inwonersaantal is de belangrijkste voorspeller</b><br/>
       Met een correlatie van {pop_corr:.3f} is het aantal inwoners veruit de beste voorspeller voor
       het aantal pakketpunten in een gemeente. Dit suggereert dat pakketpunt-aanbieders primair
       focussen op bevolkingsomvang.<br/><br/>

    2. <b>Geografische spreiding speelt een beperkte rol</b><br/>
       De zwakke correlatie met oppervlakte ({area_corr:.3f}) suggereert dat geografische spreiding
       minder belangrijk is dan inwonersaantal. Grotere gemeenten hebben niet proportioneel meer pakketpunten.<br/><br/>

    3. <b>Significante verschillen tussen gemeenten</b><br/>
       Sommige gemeenten presteren aanzienlijk beter (bijv. Dijk en Waard, +74%) of slechter
       (bijv. Almere, -3937%) dan voorspeld. Dit duidt op lokale factoren die niet door het model
       worden gevangen.<br/><br/>

    <b>Mogelijke Verklaringen voor Afwijkingen:</b><br/>
    • Stedelijkheidsgraad en winkelconcentratie<br/>
    • Aanwezigheid van regionale distributiecentra<br/>
    • Lokaal beleid en ruimtelijke ordening<br/>
    • Concurrentie tussen pakketpunt-aanbieders<br/>
    • Kwaliteit van bestaande infrastructuur<br/><br/>

    <b>Aanbevelingen voor Verder Onderzoek:</b><br/>
    • Opnemen van stedelijkheidsgraad als variabele<br/>
    • Analyseren van geografische clustering<br/>
    • Onderzoeken van tijdstrends in pakketpunt-ontwikkeling<br/>
    • Vergelijken met andere Europese landen
    """.format(
        pop_corr=data['correlations']['population']['correlation'],
        area_corr=data['correlations']['area_km2']['correlation']
    )
    story.append(Paragraph(conclusions, body_style))

    # Build PDF
    doc.build(story)

    return pdf_path


def main():
    """Main function."""
    print("Loading analysis data...")
    data = load_analysis_data()

    print("Generating PDF report...")
    pdf_path = generate_pdf_report(data)

    print(f"\n✓ PDF report generated successfully!")
    print(f"  Location: {pdf_path}")
    print(f"  File size: {pdf_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
