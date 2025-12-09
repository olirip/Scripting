# Cloudinary Error Report Processor

This script processes Cloudinary error reports from Excel (.xlsx) format and converts them into a structured JSON format for easier analysis.

## Structure

The output JSON has the following nested structure:

```json
{
  "referrer": {
    "user_agent": {
      "code": {
        "error": [
          "request1",
          "request2",
          ...
        ]
      }
    }
  }
}
```

### Key Features

- **Referrer**: First level key. If empty or "-", it's replaced with "none"
- **User Agent**: Second level key
- **Code**: Third level key (HTTP status code)
- **Error**: Fourth level key. The prefix "Resource not found - " is automatically removed if present
- **Request**: Array of request URLs that match the above criteria

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install openpyxl
```

## Usage

1. Place your Excel error report in the same directory as the script
2. Update the filename in `process_errors.py` if needed (currently: "Cloudinary error report decembre.xlsx")
3. Run the script:

```bash
source venv/bin/activate  # If not already activated
python process_errors.py
```

4. The script will generate `cloudinary_errors.json` in the same directory

## Example Output

```json
{
  "none": {
    "Java/17.0.12": {
      "304": {
        "retailers/RSWI_17847/POS-wechat-image-3": [
          "/rolex-prod/image/upload/f_auto,q_auto/d_retailers:a_generic:imagewechat-3.jpg/retailers/RSWI_17847/POS-wechat-image-3"
        ]
      }
    }
  },
  "https://www.example.com": {
    "Mozilla/5.0": {
      "404": {
        "images/missing.jpg": [
          "/path/to/missing.jpg"
        ]
      }
    }
  }
}
```

## Statistics

The script will display:
- Number of rows processed
- Total unique referrers
- Total requests

This helps verify that all data was correctly imported.
