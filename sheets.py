"""
Google Sheets Manager
Handles all read/write operations with Google Sheets API v4
"""
import logging
from typing import List, Dict
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import GOOGLE_CREDENTIALS_FILE, SPREADSHEET_ID

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsManager:
    """Google Sheets API wrapper for business automation"""

    def __init__(self, credentials_file: str = None, spreadsheet_id: str = None):
        self.credentials_file = credentials_file or GOOGLE_CREDENTIALS_FILE
        self.spreadsheet_id = spreadsheet_id or SPREADSHEET_ID
        self._service = None

    @property
    def service(self):
        """Lazy-initialize the Sheets API service"""
        if self._service is None:
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=SCOPES
            )
            self._service = build("sheets", "v4", credentials=creds)
        return self._service

    def read_rows(self, sheet_name: str, range_str: str = "A:Z") -> List[List[str]]:
        """Read all rows from a sheet"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!{range_str}"
            ).execute()
            return result.get("values", [])
        except HttpError as e:
            logger.error(f"Error reading sheet '{sheet_name}': {e}")
            return []

    def get_leads(self, sheet_name: str = "Leads") -> List[Dict]:
        """
        Read leads from sheet, return as list of dicts.
        Expects headers in row 1: Name, Email, Company, Message, Status, Score, AI_Response
        """
        rows = self.read_rows(sheet_name)
        if not rows:
            return []

        headers = [h.strip().lower().replace(" ", "_") for h in rows[0]]
        leads = []
        for i, row in enumerate(rows[1:], start=2):
            # Pad row to match headers length
            padded = row + [""] * (len(headers) - len(row))
            lead = dict(zip(headers, padded))
            lead["_row_number"] = i  # Track row for updates
            leads.append(lead)
        return leads

    def get_unprocessed_leads(self, sheet_name: str = "Leads") -> List[Dict]:
        """Get leads where Status is empty (not yet processed)"""
        leads = self.get_leads(sheet_name)
        return [lead for lead in leads if not lead.get("status", "").strip()]

    def update_cell(self, sheet_name: str, cell: str, value: str):
        """Update a single cell"""
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!{cell}",
                valueInputOption="USER_ENTERED",
                body={"values": [[value]]}
            ).execute()
        except HttpError as e:
            logger.error(f"Error updating cell {cell}: {e}")

    def update_row(self, sheet_name: str, row_number: int, values: Dict[str, str], headers: List[str] = None):
        """Update specific columns in a row"""
        if headers is None:
            rows = self.read_rows(sheet_name, "1:1")
            headers = [h.strip().lower().replace(" ", "_") for h in rows[0]] if rows else []

        for col_name, value in values.items():
            if col_name in headers:
                col_index = headers.index(col_name)
                col_letter = self._col_letter(col_index)
                self.update_cell(sheet_name, f"{col_letter}{row_number}", str(value))

    def append_row(self, sheet_name: str, values: List[str]):
        """Append a row to the sheet"""
        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:Z",
                valueInputOption="USER_ENTERED",
                body={"values": [values]}
            ).execute()
        except HttpError as e:
            logger.error(f"Error appending row: {e}")

    def write_analytics(self, sheet_name: str, data: Dict):
        """Write analytics summary to a dedicated sheet"""
        rows = [
            ["Metric", "Value"],
            ["Total Leads", data.get("total", 0)],
            ["Processed", data.get("processed", 0)],
            ["Hot Leads (Score 8-10)", data.get("hot", 0)],
            ["Warm Leads (Score 5-7)", data.get("warm", 0)],
            ["Cold Leads (Score 1-4)", data.get("cold", 0)],
            ["Avg Score", f"{data.get('avg_score', 0):.1f}"],
            ["Last Updated", data.get("timestamp", "")],
        ]
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A1:B{len(rows)}",
                valueInputOption="USER_ENTERED",
                body={"values": rows}
            ).execute()
        except HttpError as e:
            logger.error(f"Error writing analytics: {e}")

    @staticmethod
    def _col_letter(index: int) -> str:
        """Convert 0-based column index to Excel-style letter (A, B, ..., Z, AA, AB, ...)"""
        result = ""
        while index >= 0:
            result = chr(65 + index % 26) + result
            index = index // 26 - 1
        return result

    def ensure_headers(self, sheet_name: str, headers: List[str]):
        """Ensure the first row has the correct headers"""
        existing = self.read_rows(sheet_name, "1:1")
        if not existing or not existing[0]:
            for i, h in enumerate(headers):
                col_letter = self._col_letter(i)
                self.update_cell(sheet_name, f"{col_letter}1", h)
            logger.info(f"Headers created in '{sheet_name}'")
