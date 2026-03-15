import os
import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = "sim/output/dd_comparison_results.csv"
OUTPUT_DIR = "sim/analytics"


def generate_charts():

    if not os.path.exists(INPUT_FILE):
        print("Comparison results file not found.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = pd.read_csv(INPUT_FILE)

    if "metric" not in df.columns or "value" not in df.columns:
        print("CSV format not recognized.")
        return

    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.dropna(subset=["value"])

    if df.empty:
        print("No numeric values available.")
        return

    metrics = df["metric"].unique()

    for metric in metrics:

        subset = df[df["metric"] == metric]

        plt.figure()

        plt.bar(subset["section"], subset["value"])

        plt.title(metric)
        plt.xlabel("System")
        plt.ylabel(metric)

        plt.xticks(rotation=25)

        output_file = f"{OUTPUT_DIR}/{metric.replace(' ','_')}.png"

        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()

        print(f"Chart created: {output_file}")


if __name__ == "__main__":

    print("\nGenerating analytics charts...\n")

    generate_charts()

    print("\nAnalytics generation complete\n")