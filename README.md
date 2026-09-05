# Data Cleaning — Financial Transactions Dataset

A Python script that cleans, standardizes, and enriches a messy financial transactions dataset (`Database.csv`) using `pandas`. It handles inconsistent formatting, missing values, mixed currencies, ambiguous dates, outliers, and duplicate/garbled text fields, then prints an automatic summary report.

## What it does

The script (`desafio.py`) reads `Database.csv` and applies a sequence of cleaning steps:

- **General cleanup**: strips whitespace from column names and all text (string) columns; drops fully empty rows and duplicate rows.
- **CPF (Brazilian tax ID)**: fills missing values with `"Não informado"`, strips all non-digit characters, and re-formats valid 11-digit CPFs into the standard `000.000.000-00` pattern.
- **Transaction dates**: normalizes separators (`.` → `-`) and parses dates with the correct day/month order based on currency (`USD` uses month-first, others use day-first), then standardizes everything to `YYYY-MM-DD`.
- **Transaction amounts**: strips stray characters, removes thousands separators, converts the decimal comma to a decimal point, and converts every amount into BRL using a fixed exchange-rate table (`USD`, `EUR`, `GBP` → `BRL`).
- **Outliers**: detects outliers in `Valor_Transacao` using the IQR method and replaces them with the column's median.
- **Transaction type**: lowercases and maps free-text/typo'd values (e.g. `"pix"`, `"ted"`, `"pgto"`, `"dep"`, `"saque"`) into standardized categories (`PIX`, `Transferência`, `Pagamento`, `Depósito`, `Saque`); fills missing values with the mode.
- **Transaction status**: lowercases and maps variants (e.g. `"aprov"`, `"recus"`, `"pend"`) into `Aprovada`, `Recusada`, or `Pendente`.
- **Client name**: removes underscores and non-letter characters, collapses extra spaces, applies title case, and removes duplicated consecutive words.
- **Installments (`Num_Parcelas`)**: extracts the numeric value from free-text entries (e.g. `"6 parcelas"` → `6`), defaulting to `1` when missing.
- **Service fee (`Taxa_Servico`)**: coerces to numeric, takes the absolute value, fills missing values with the mean, and casts to integer.
- **Final amount (`Valor_Final`)**: recalculates it as `Valor_Transacao + Taxa_Servico` whenever it's missing or inconsistent (lower than the transaction amount).
- **Export**: saves the cleaned dataset back to `Database.csv`.
- **Summary report**: builds a formatted text report (in Portuguese) with overall totals, value statistics, status/type/category breakdowns, top clients, most-used banks, and a few automatic insights (top client by volume, dominant bank, approval rate).

## Dataset

`Database.csv` contains simulated financial transaction records with the following columns:

| Column | Description |
|---|---|
| `Codigo_Transacao` | Transaction ID |
| `CPF_Cliente` | Client's Brazilian tax ID (CPF) |
| `Nome_Cliente` | Client name |
| `Data_Transacao` | Transaction date |
| `Moeda` | Currency (`BRL`, `USD`, `EUR`, `GBP`) |
| `Valor_Transacao` | Transaction amount |
| `Tipo_Transacao` | Transaction type (PIX, transfer, payment, deposit, withdrawal) |
| `Status_Transacao` | Transaction status (approved, refused, pending) |
| `Categoria` | Spending category |
| `Banco` | Bank name |
| `Num_Parcelas` | Number of installments |
| `Taxa_Servico` | Service fee |
| `Valor_Final` | Final amount (transaction + fee) |

## Requirements

- Python 3.8+
- [pandas](https://pandas.pydata.org/)

Install the dependency with:

```bash
pip install pandas
```

## Usage

Make sure `Database.csv` is in the same directory as `desafio.py`, then run:

```bash
python desafio.py
```

The script will overwrite `Database.csv` with the cleaned data and generate a summary report (`resumo`) covering totals, value statistics, and key insights from the cleaned dataset.

## Notes

- The exchange rates used to convert `USD`, `EUR`, and `GBP` into `BRL` are hardcoded in the script and should be updated to reflect current rates if needed.
- The script modifies `Database.csv` in place — keep a backup of the original file if you want to preserve the raw data.
