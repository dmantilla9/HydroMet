# HydroMet

**Safe water. Smart weather. One system.**

HydroMet is a Python-based application that brings together **drinking water quality monitoring** and **local weather observations** for municipalities in France. It collects information from external data sources, stores structured records in Supabase (PostgreSQL), provides a Streamlit interface for managing locations and exploring reference data, and sends Telegram notifications when new water analyses become available.

## Project goals

HydroMet is designed to:

- **Track drinking water quality** using official water analysis reports, including sanitary conclusions, compliance indicators, and measured parameters.
- **Collect local weather observations** for configured municipalities.
- **Keep information organized over time** in a relational database so analyses and observations can be consulted independently of their sources.
- **Automate daily collection** with GitHub Actions.
- **Notify subscribers of new water analyses** without repeating notifications for records already processed.
- **Offer a simple management interface** for municipalities and water distribution networks.

## Data sources and technologies

| Component | Technology | Purpose |
| --- | --- | --- |
| Drinking water analyses | OROBNAT (French public health water information) | Retrieve water analysis reports |
| Weather observations | OpenWeatherMap | Retrieve current weather conditions by location |
| Geographic reference data | French public geographic datasets | Provide municipality information and INSEE identifiers |
| Database | Supabase / PostgreSQL | Persist water analyses, weather observations, application settings, and notification history |
| User interface | Streamlit | Manage locations and consult reference tables |
| Data processing | Python, Requests, Beautiful Soup, Pandas | Retrieve, interpret, and transform source data |
| Automation | GitHub Actions | Run scheduled ingestion and notification checks |
| Notifications | Telegram Bot API | Deliver updates about new water analyses |

## How HydroMet works

### 1. Configure the monitored municipalities

HydroMet maintains a list of municipalities in the `cities` table. Each location can include:

- Municipality name, postal code, and INSEE code.
- Geographic coordinates for weather queries.
- The corresponding drinking water network code.
- Time zone and an active/inactive flag.

Only **active municipalities** are included in the daily collection workflows. Water networks are represented separately in the `water_network` table.

### 2. Collect drinking water analyses

The water ingestion process:

1. Loads all active municipalities from Supabase.
2. Builds a search request for each municipality using its INSEE code and water network.
3. Requests the latest available report from OROBNAT.
4. Extracts report sections covering search criteria, general sampling information, sanitary compliance, and laboratory results.
5. Maps the extracted information into relational records.
6. Inserts or updates the corresponding records in PostgreSQL.

An analysis identifier combines the **sampling date** and the **municipality INSEE code**, in the form `DD-MM-YYYY-INSEE`. The ingestion process uses upserts so a subsequent run can process an existing identifier without creating an additional analysis record.

**Collection scope:** HydroMet retrieves the report available when a municipality is processed. It does **not** automatically backfill all previous analyses when a new municipality is added. As a result, a newly configured municipality starts with its currently available analysis, and subsequent reports are collected through future executions.

Each report can include bacteriological conformity, physicochemical conformity, quality-reference assessments, official sanitary conclusions, and measured values for parameters such as pH, nitrates, chlorine, and turbidity, when present in the source.

### 3. Collect weather observations

For each active municipality, HydroMet queries OpenWeatherMap using latitude and longitude. The weather ingestion process stores a timestamped observation containing available information such as:

- Current temperature, feels-like temperature, minimum and maximum temperature.
- Atmospheric pressure and humidity.
- Wind speed and direction.
- Cloud cover.
- Sunrise and sunset times.
- Location and observation timestamps.

The current implementation collects **weather observations**, rather than producing a multi-day forecast model.

### 4. Detect and notify new water analyses

HydroMet includes a separate notification process for water quality updates.

1. A PostgreSQL function, `get_pending_water_analyses_active`, identifies analyses associated with active municipalities that have not already been marked as notified or included in the notification baseline.
2. The Python notification script creates a readable Telegram message with the municipality, sampling date, sanitary conformity, official conclusions, and selected measured parameters.
3. The message is sent through the Telegram Bot API.
4. When Telegram confirms acceptance, HydroMet records the analysis and channel in `hydromet_notification_history`.

The notification history distinguishes **baseline** records (existing analyses excluded from new-alert delivery) from **sent** records. This allows the system to focus on newly detected reports instead of re-announcing older analyses.

If there are no pending analyses, the workflow finishes without sending a message.

## Application interface

The Streamlit application offers three main areas:

| Area | Description |
| --- | --- |
| Home (`app.py`) | Project introduction, account registration, sign-in, and password reset |
| Manage (`pages/1_Manage.py`) | Add municipalities and water distribution networks using dedicated forms |
| Consult (`pages/2_Consult.py`) | Search and browse municipality and water network tables; export results to CSV; view user information through an administrator-specific tab |

The interface is organized around managing reference data and exploring configured locations. Daily collection and notifications run independently through automated workflows.

## Data model

Water analysis information is divided into related tables rather than stored as one large record.

| Table | Responsibility |
| --- | --- |
| `cities` | Monitored municipalities and collection settings |
| `water_network` | Drinking water distribution networks |
| `fait_anl_criteres_recherche` | Main water analysis identifier, municipality, and network |
| `fait_anl_informations_generales` | Sampling date, sampling municipality, and distribution information |
| `fait_anl_conformite` | Sanitary conclusions and conformity indicators |
| `fait_anl_resultats_analyses` | Individual laboratory parameters, values, and quality thresholds |
| `weather_data` | Time-stamped weather observations |
| `hydromet_notification_history` | Telegram notification state by analysis and channel |
| `hydromet_telegram_topics` | Municipality-to-Telegram topic configuration data |
| `dim_geo_communes` | Reference information about French municipalities |
| `app_users` | Application user accounts |

The primary water analysis record is stored in `fait_anl_criteres_recherche`. General information and conformity use the same analysis identifier, while the results table stores multiple measured parameters for each analysis.

The current notification script sends messages to the configured Telegram chat. The database also contains topic configuration data that can support more granular destination routing.

## Scheduled execution

Two GitHub Actions workflows automate HydroMet.

### Daily data collection

**Workflow:** [`hydromet.yml`](.github/workflows/hydromet.yml)

- Scheduled daily at **05:00 UTC**.
- Runs the drinking water ETL first.
- Runs the weather ETL after the water job completes.
- Stores job logs as GitHub Actions artifacts.
- Also supports manual execution from the Actions tab.

### Water analysis notification check

**Workflow:** [`check_water_analysis.yml`](.github/workflows/check_water_analysis.yml)

- Configured for a daily check around **12:15 Europe/Paris**.
- Queries pending analyses through Supabase.
- Sends Telegram messages only when pending analyses exist.
- Supports manual execution.
- Includes a dry-run mode for reviewing messages without sending them.

The actual start time may vary depending on GitHub Actions scheduling.

## Repository structure

```text
HydroMet/
├── .github/workflows/
│   ├── hydromet.yml              # Daily water and weather ingestion
│   └── check_water_analysis.yml  # Water analysis notification checks
├── app.py                        # Streamlit entry point
├── pages/                        # Streamlit management and consultation pages
├── form/                         # Municipality and water network forms
├── hydro/
│   ├── cli.py                    # Water ETL command-line entry point
│   ├── etl_runner.py             # Per-municipality water ingestion
│   ├── http_client.py            # OROBNAT HTTP requests
│   ├── payloads.py               # Source request parameters
│   ├── parsing/                  # HTML extraction and normalization
│   └── tables/                   # Mapping to water analysis tables
├── weather/
│   └── fetch_weather.py          # Weather data ingestion
├── db/
│   ├── supabase_utils.py         # Database operations and notification helpers
│   └── seeds.sql                 # Example reference records
├── geo/
│   └── seed_communes.py          # Municipality reference data loader
├── scripts/
│   └── check_water_analysis.py   # Telegram notification runner
├── sql/
│   └── pending_analyses.sql      # Reference query for pending analyses
├── config.py                     # Environment-based configuration
└── requirements.txt              # Python dependencies
```

## Run locally

### Requirements

- Python **3.11** (the version used by GitHub Actions).
- Access to a configured Supabase project.
- Appropriate credentials and endpoint settings for the external services used.

### Install dependencies

```bash
git clone https://github.com/dmantilla9/HydroMet.git
cd HydroMet
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the virtual environment with `.venv\Scripts\activate` instead.

### Configure the environment

HydroMet reads its configuration from environment variables through `config.py`. Depending on which components are being run, variables include:

```dotenv
SUPABASE_URL=
SUPABASE_KEY=

API_KEY=
OPENWEATHER_URL=

BASE_OROBNAT=
URL_OROBNAT_GET=
URL_OROBNAT_POST=

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
HYDROMET_DRY_RUN=true
```

Additional variables used by specific features include `RESET_MASTER_KEY` and `CSV_URL`. The GitHub Actions workflows supply their own configured values.

### Launch the Streamlit app

```bash
streamlit run app.py
```

### Run the drinking water ETL

Process all active municipalities:

```bash
python -m hydro.cli --sleep 1.0 --limit 0
```

Process one municipality from the active-city list:

```bash
python -m hydro.cli --city-index 0
```

The water CLI also supports local HTML input for offline parsing and debugging.

### Run the weather ETL

```bash
python -m weather.fetch_weather
```

### Check water analyses for Telegram notifications

```bash
python -m scripts.check_water_analysis
```

Set `HYDROMET_DRY_RUN=true` to preview notification messages without sending them.

## Current behavior and scope

HydroMet currently provides:

- Configurable municipality-based water and weather collection.
- Structured storage of drinking water reports and laboratory results.
- Repeated daily execution without duplicating analysis identifiers.
- Historical accumulation of reports collected since municipalities began being monitored.
- Weather observation storage for configured locations.
- A Streamlit interface for account access, reference data management, and consultation.
- Telegram alerts for newly detected water analyses.
- Automated scheduled workflows and manual execution options.

**Not currently part of the collection workflow:** automatic recovery of all historical water analyses for a newly added municipality, multi-day weather forecasting, or automatic Telegram topic routing based on the topic mapping table.

## Project links

- **Repository:** https://github.com/dmantilla9/HydroMet
- **OROBNAT:** https://orobnat.sante.gouv.fr/
- **OpenWeatherMap:** https://openweathermap.org/
- **Supabase:** https://supabase.com/
- **Streamlit:** https://streamlit.io/

---

HydroMet brings water quality reports and weather observations into one automated data platform, helping monitor local conditions and stay informed when new drinking water analyses are published.
