import pandas as pd


def generate_latex_table(excel_file_path):
    """
    Reads an Excel file containing analysis results, calculates accuracies for
    Exverus and Autoverus, and generates a LaTeX formatted table for Overleaf.

    Args:
    excel_file_path (str): The file path for the input Excel file.
                         It is assumed that the last two columns of the file
                         are the verification results (1 for success, 0 for failure)
                         for Exverus and Autoverus, respectively.
    """
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file_path)
    except FileNotFoundError:
        print(
            f"Error: File '{excel_file_path}' not found. Please ensure the filename is correct and the file is in the same directory as the script."
        )
        return

    # Clean up leading/trailing whitespace from column names
    df.columns = df.columns.str.strip()

    # Get the names of the last two columns
    exverus_col_name = df.columns[-2]
    autoverus_col_name = df.columns[-1]

    print(f"Detected Exverus results column: '{exverus_col_name}'")
    print(f"Detected Autoverus results column: '{autoverus_col_name}'")

    # Define the six obfuscation sub-strategies and their corresponding category columns
    sub_strategies = {
        "meaningless_identifier_names": "meaningless_identifier_names_category",
        "dead_junk_variables": "dead_junk_variables_category",
        "instruction_substitution": "instruction_substitution_category",
        "dead_code_insertion": "dead_code_insertion_category",
        "opaque_predicates": "opaque_predicates_category",
        "redundant_conditional_branches": "redundant_conditional_branches_category",
    }

    # Dictionary to store the calculation results
    results = {}

    # Iterate over each sub-strategy to calculate accuracies
    for strategy, category_col in sub_strategies.items():
        # Filter for rows where this obfuscation strategy was applied
        # Use .str.strip() and .str.lower() for robustness
        applied_df = df[df[strategy].str.strip().str.lower() == "yes"]

        if not applied_df.empty:
            # Calculate accuracies for Exverus and Autoverus (as the mean of the 0/1 columns)
            exverus_accuracy = applied_df[exverus_col_name].mean()
            autoverus_accuracy = applied_df[autoverus_col_name].mean()

            # Get the main obfuscation category from the first row of the filtered data
            category = applied_df[category_col].iloc[0].strip()

            if category not in results:
                results[category] = []

            # Format the sub-strategy name for display in the table
            pretty_name = strategy.replace("_", " ").title()

            # Store the results
            results[category].append(
                {
                    "sub_strategy": pretty_name,
                    "exverus_accuracy": exverus_accuracy,
                    "autoverus_accuracy": autoverus_accuracy,
                }
            )

    # --- Generate LaTeX Table ---

    # Define the display order for the main categories
    category_order = [
        "Layout Obfuscation",
        "Data Obfuscation",
        "Control Flow Obfuscation",
    ]

    latex_string = []
    latex_string.append("\\begin{table}[h!]")
    latex_string.append("\\centering")
    latex_string.append(
        "\\caption{Accuracy comparison between Exverus and Autoverus under different obfuscation strategies}"
    )
    latex_string.append("\\label{tab:accuracy_comparison}")
    latex_string.append("\\begin{tabular}{r|r|ll}")
    latex_string.append("\\toprule")
    latex_string.append(" &  & \\textbf{Exverus} & \\textbf{Autoverus} \\\\")
    latex_string.append("\\midrule")

    for category in category_order:
        if category in results:
            sub_results = results[category]
            num_sub_results = len(sub_results)

            # Use multirow to merge cells for the main category
            latex_string.append(
                f"\\multirow{{{num_sub_results}}}{{*}}{{\\bf {category}}}"
            )

            for i, res in enumerate(sub_results):
                # For rows after the first in a category, leave the category column blank
                line_prefix = "& " if i == 0 else " & "

                # Format as percentage and escape the '%' character for LaTeX
                exverus_acc_percent = f"{res['exverus_accuracy']:.2%}".replace(
                    "%", r"\%"
                )
                autoverus_acc_percent = f"{res['autoverus_accuracy']:.2%}".replace(
                    "%", r"\%"
                )

                latex_string.append(
                    f"{line_prefix}{res['sub_strategy']} & {exverus_acc_percent} & {autoverus_acc_percent} \\\\"
                )

            # Add a midrule after each main category section (except for the last one)
            if category != category_order[-1]:
                latex_string.append("\\midrule")

    latex_string.append("\\bottomrule")
    latex_string.append("\\end{tabular}")
    latex_string.append("\\end{table}")

    # Join the list into a single string and print the result
    final_latex_code = "\n".join(latex_string)
    print("\n" + "=" * 20 + " LaTeX Table Code " + "=" * 20 + "\n")
    print(final_latex_code)
    print("\n" + "=" * 58)


if __name__ == "__main__":
    # --- User Configuration ---
    # Please replace 'your_analysis_results.xlsx' with your Excel file name
    EXCEL_FILENAME = "your_analysis_results.xlsx"

    # Run the main function
    generate_latex_table(EXCEL_FILENAME)
