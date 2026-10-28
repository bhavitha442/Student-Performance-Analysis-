"""
visualizations.py
====================================================================
Data Visualization Module using Matplotlib
Generates clean, presentation-ready charts for performance metrics.
====================================================================
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for web servers
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


def _create_empty_figure(message: str = "No Data Available to Display") -> plt.Figure:
    """Helper to return a clean placeholder figure when datasets are empty."""
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=13, color="#6c757d", weight="bold")
    ax.axis("off")
    fig.tight_layout()
    return fig


def plot_subject_averages(subject_summary_df: pd.DataFrame) -> plt.Figure:
    """
    Bar chart showing Subject-wise Average Marks vs Subject Maximum Marks.
    """
    if subject_summary_df.empty or "Subject" not in subject_summary_df.columns:
        return _create_empty_figure("No Subject Data Available")

    df = subject_summary_df.copy()
    subjects = df["Subject"].tolist()
    averages = df["Average Marks"].tolist()
    max_marks = df["Max Marks"].tolist()

    x = np.arange(len(subjects))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 4.5))
    rects1 = ax.bar(x - width/2, averages, width, label="Average Marks", color="#1f77b4")
    rects2 = ax.bar(x + width/2, max_marks, width, label="Max Marks", color="#aec7e8", alpha=0.7)

    ax.set_ylabel("Marks", fontsize=11, weight="bold")
    ax.set_title("Subject-wise Average Marks vs Maximum Marks", fontsize=13, weight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(subjects, rotation=15, ha="right", fontsize=10)
    ax.legend(frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    # Add numeric labels on top of bars
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h:.1f}",
                    xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9, weight="bold")

    fig.tight_layout()
    return fig


def plot_subject_pass_percentage(subject_summary_df: pd.DataFrame) -> plt.Figure:
    """
    Bar chart showing Pass Percentage for each subject with color-coded benchmark.
    """
    if subject_summary_df.empty or "Subject" not in subject_summary_df.columns:
        return _create_empty_figure("No Subject Data Available")

    df = subject_summary_df.copy()
    subjects = df["Subject"].tolist()
    pass_pcts = df["Pass %"].tolist()

    # Color bars: Green for >= 75%, Orange for >= 50%, Red for < 50%
    colors = []
    for p in pass_pcts:
        if p >= 75.0:
            colors.append("#2ca02c")
        elif p >= 50.0:
            colors.append("#ff7f0e")
        else:
            colors.append("#d62728")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(subjects, pass_pcts, color=colors, width=0.45, edgecolor="#333333", linewidth=0.5)

    ax.set_ylabel("Pass Percentage (%)", fontsize=11, weight="bold")
    ax.set_ylim(0, 105)
    ax.set_title("Subject-wise Pass Percentage", fontsize=13, weight="bold", pad=12)
    ax.axhline(50, color="red", linestyle=":", linewidth=1.2, label="50% Support Benchmark")
    ax.set_xticklabels(subjects, rotation=15, ha="right", fontsize=10)
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9, weight="bold")

    fig.tight_layout()
    return fig


def plot_student_marks_comparison(student_marks: List[Dict[str, Any]], student_name: str) -> plt.Figure:
    """
    Individual student report chart:
    Compares marks obtained vs pass marks vs max marks across subjects.
    """
    if not student_marks:
        return _create_empty_figure(f"No Marks Recorded for {student_name}")

    subjects = [m["subject_name"] for m in student_marks]
    obtained = [float(m["marks_obtained"]) for m in student_marks]
    pass_m = [float(m["pass_marks"]) for m in student_marks]
    max_m = [float(m["max_marks"]) for m in student_marks]

    x = np.arange(len(subjects))
    width = 0.28

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    r1 = ax.bar(x - width, obtained, width, label="Marks Obtained", color="#1f77b4")
    r2 = ax.bar(x, pass_m, width, label="Pass Marks", color="#ff7f0e", alpha=0.85)
    r3 = ax.bar(x + width, max_m, width, label="Max Marks", color="#2ca02c", alpha=0.6)

    ax.set_ylabel("Marks", fontsize=11, weight="bold")
    ax.set_title(f"Performance Breakdown: {student_name}", fontsize=13, weight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(subjects, rotation=15, ha="right", fontsize=10)
    ax.legend(frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for r in r1:
        h = r.get_height()
        ax.annotate(f"{h:.0f}",
                    xy=(r.get_x() + r.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, weight="bold")

    fig.tight_layout()
    return fig


def plot_marks_distribution(summary_df: pd.DataFrame) -> plt.Figure:
    """
    Histogram and Grade Distribution chart of student percentages.
    """
    if summary_df.empty or "Percentage" not in summary_df.columns:
        return _create_empty_figure("No Performance Data Available")

    valid_pcts = pd.to_numeric(summary_df["Percentage"], errors="coerce").dropna()
    if valid_pcts.empty:
        return _create_empty_figure("No Numeric Marks Available for Distribution")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

    # 1. Percentage Distribution Histogram
    bins = [0, 50, 60, 70, 80, 90, 100]
    ax1.hist(valid_pcts, bins=bins, color="#3498db", edgecolor="#2c3e50", alpha=0.85, rwidth=0.9)
    ax1.set_xlabel("Percentage Range (%)", fontsize=10, weight="bold")
    ax1.set_ylabel("Number of Students", fontsize=10, weight="bold")
    ax1.set_title("Student Percentage Distribution", fontsize=11, weight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # 2. Grade Distribution Bar Chart
    grades_order = ["A", "B", "C", "D", "E", "F"]
    grade_counts = summary_df["Grade"].value_counts().reindex(grades_order, fill_value=0)
    colors = ["#2ecc71", "#27ae60", "#f1c40f", "#e67e22", "#e74c3c", "#c0392b"]

    ax2.bar(grades_order, grade_counts, color=colors, edgecolor="#333333", linewidth=0.6, width=0.55)
    ax2.set_xlabel("Letter Grade", fontsize=10, weight="bold")
    ax2.set_ylabel("Student Count", fontsize=10, weight="bold")
    ax2.set_title("Grade Breakdown (A to F)", fontsize=11, weight="bold")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    for i, count in enumerate(grade_counts):
        if count > 0:
            ax2.annotate(str(count), xy=(i, count), xytext=(0, 2),
                         textcoords="offset points", ha="center", va="bottom",
                         fontsize=9, weight="bold")

    fig.tight_layout()
    return fig


def plot_section_performance(section_summary_df: pd.DataFrame) -> plt.Figure:
    """
    Bar chart comparing Average Percentage and Pass Rate by Section.
    """
    if section_summary_df.empty or "Section" not in section_summary_df.columns:
        return _create_empty_figure("No Section Data Available")

    df = section_summary_df.copy()
    sections = df["Section"].tolist()
    avg_pct = df["Average %"].tolist()
    pass_rates = df["Pass Rate %"].tolist()

    x = np.arange(len(sections))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    r1 = ax.bar(x - width/2, avg_pct, width, label="Average %", color="#9b59b6")
    r2 = ax.bar(x + width/2, pass_rates, width, label="Pass Rate %", color="#1abc9c")

    ax.set_ylabel("Percentage (%)", fontsize=11, weight="bold")
    ax.set_title("Section-wise Comparison: Average % vs Pass Rate", fontsize=12, weight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Section {s}" for s in sections], fontsize=10)
    ax.set_ylim(0, 105)
    ax.legend(frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for r in r1:
        h = r.get_height()
        ax.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, weight="bold")

    for r in r2:
        h = r.get_height()
        ax.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, weight="bold")

    fig.tight_layout()
    return fig
