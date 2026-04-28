"""
MCP Data Processing Service
Handles MCP server communication and data processing
"""
import json
import logging
import os
from typing import Dict, List, Any, Tuple
from datetime import datetime

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.financials import (
    Account, Asset, Liability, Holding,
    Transaction, CreditReport, EPF, MCPRawData
)
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# Development mode flag
USE_SAMPLE_DATA = settings.USE_SAMPLE_MCP_DATA

# --- MCP Response Parsing ---


def parse_mcp_response(mcp_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the complex MCP JSON response and extract structured data.
    Returns a dictionary with parsed assets, liabilities, accounts, and holdings.
    """
    try:
        # Extract the JSON string from the response
        text_content = mcp_response["result"]["content"][0]["text"]
        data = json.loads(text_content)

        parsed_data = {
            "net_worth": parse_net_worth(data),
            "assets": parse_assets(data),
            "liabilities": parse_liabilities(data),
            "accounts": parse_accounts(data),
            "mutual_funds": parse_mutual_funds(data)
        }

        return parsed_data

    except (KeyError, json.JSONDecodeError, IndexError) as e:
        raise ValueError(f"Failed to parse MCP response: {str(e)}") from e


def parse_net_worth(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract net worth information."""
    networth = data.get("netWorthResponse", {})
    return {
        "total_net_worth": float(networth.get("totalNetWorthValue", {}).get("units", 0)),
        "currency": networth.get("totalNetWorthValue", {}).get("currencyCode", "INR")
    }


def parse_assets(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract asset values from net worth response."""
    networth = data.get("netWorthResponse", {})
    asset_values = networth.get("assetValues", [])

    assets = []
    for asset in asset_values:
        assets.append({
            "asset_type": asset["netWorthAttribute"],
            "value": float(asset["value"]["units"]),
            "currency": asset["value"]["currencyCode"]
        })

    return assets


def parse_liabilities(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract liability values from net worth response."""
    networth = data.get("netWorthResponse", {})
    liability_values = networth.get("liabilityValues", [])

    liabilities = []
    for liability in liability_values:
        liabilities.append({
            "liability_type": liability["netWorthAttribute"],
            "value": float(liability["value"]["units"]),
            "currency": liability["value"]["currencyCode"]
        })

    return liabilities


def parse_accounts(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract account details and their summaries."""
    account_map = data.get("accountDetailsBulkResponse",
                           {}).get("accountDetailsMap", {})

    accounts = []
    for acc_id, acc_data in account_map.items():
        acc_details = acc_data.get("accountDetails", {})

        account = {
            "external_id": acc_id,
            "masked_account_number": acc_details.get("maskedAccountNumber"),
            "account_type": acc_details.get("accInstrumentType"),
            "institution_name": acc_details.get("fipMeta", {}).get("displayName"),
            "institution_id": acc_details.get("fipId"),
            "ifsc_code": acc_details.get("ifscCode"),
            "holdings": parse_account_holdings(acc_data)
        }

        # Add account-specific summary data
        if "depositSummary" in acc_data:
            deposit = acc_data["depositSummary"]
            account["current_balance"] = float(
                deposit.get("currentBalance", {}).get("units", 0))
            account["balance_date"] = deposit.get("balanceDate")
            account["account_status"] = deposit.get("depositAccountStatus")

        accounts.append(account)

    return accounts


def parse_account_holdings(acc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract holdings information from account data."""
    holdings = []

    # Check different types of summaries for holdings
    summary_types = ["equitySummary", "etfSummary",
                     "reitSummary", "invitSummary"]

    for summary_type in summary_types:
        summary = acc_data.get(summary_type)
        if summary and "holdingsInfo" in summary:
            for holding in summary["holdingsInfo"]:
                holding_data = {
                    "holding_type": summary_type.replace("Summary", "").upper(),
                    "isin": holding.get("isin"),
                    "issuer_name": holding.get("issuerName"),
                    "description": holding.get("isinDescription"),
                    "units": float(holding.get("units", holding.get("totalNumberUnits", 0))),
                    "current_value": 0  # Will be calculated from price * units
                }

                # Extract price information
                price_info = holding.get("lastTradedPrice") or holding.get(
                    "nav") or holding.get("lastClosingRate")
                if price_info:
                    price = float(price_info.get("units", 0)) + \
                        float(price_info.get("nanos", 0)) / 1000000000
                    holding_data["unit_price"] = price
                    holding_data["current_value"] = price * \
                        holding_data["units"]

                holdings.append(holding_data)

    return holdings


def parse_mutual_funds(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract mutual fund scheme analytics."""
    mf_data = data.get("mfSchemeAnalytics", {})
    scheme_analytics = mf_data.get("schemeAnalytics", [])

    mutual_funds = []
    for scheme in scheme_analytics:
        scheme_detail = scheme.get("schemeDetail", {})
        analytics = scheme.get("enrichedAnalytics", {}).get(
            "analytics", {}).get("schemeDetails", {})

        mf_info = {
            "amc": scheme_detail.get("amc"),
            "scheme_name": scheme_detail.get("nameData", {}).get("longName"),
            "plan_type": scheme_detail.get("planType"),
            "option_type": scheme_detail.get("optionType"),
            "asset_class": scheme_detail.get("assetClass"),
            "isin_number": scheme_detail.get("isinNumber"),
            "category": scheme_detail.get("categoryName"),
            "risk_level": scheme_detail.get("fundhouseDefinedRiskLevel"),
            "nav": float(scheme_detail.get("nav", {}).get("units", 0)),
            "current_value": float(analytics.get("currentValue", {}).get("units", 0)),
            "invested_value": float(analytics.get("investedValue", {}).get("units", 0)),
            "units": float(analytics.get("units", 0)),
            "xirr": analytics.get("XIRR", 0),
            "absolute_returns": float(analytics.get("absoluteReturns", {}).get("units", 0)),
            "unrealised_returns": float(analytics.get("unrealisedReturns", {}).get("units", 0))
        }

        mutual_funds.append(mf_info)

    return mutual_funds

# --- MCP Data Ingestion ---


class MCPDatabaseIngest:
    """Service to ingest parsed MCP data into the database."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def ingest_all_data(self, parsed_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Ingest all parsed MCP data into the database.
        Returns a summary of records created.
        """
        summary = {
            "assets": 0,
            "liabilities": 0,
            "accounts": 0,
            "holdings": 0,
            "mutual_funds": 0
        }

        try:
            # Ingest assets
            if "assets" in parsed_data:
                summary["assets"] = self._ingest_assets(parsed_data["assets"])

            # Ingest liabilities
            if "liabilities" in parsed_data:
                summary["liabilities"] = self._ingest_liabilities(
                    parsed_data["liabilities"])

            # Ingest accounts (includes holdings)
            if "accounts" in parsed_data:
                account_count, holding_count = self._ingest_accounts(
                    parsed_data["accounts"])
                summary["accounts"] = account_count
                summary["holdings"] = holding_count

            # TODO: Add mutual fund ingestion when MF model is ready
            # if "mutual_funds" in parsed_data:
            #     summary["mutual_funds"] = self._ingest_mutual_funds(parsed_data["mutual_funds"])

            self.db.commit()
            logger.info(
                f"Successfully ingested MCP data for user {self.user_id}: {summary}")
            return summary

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(
                f"Database error during MCP ingestion for user {self.user_id}: {str(e)}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Unexpected error during MCP ingestion for user {self.user_id}: {str(e)}")
            raise

    def _ingest_assets(self, assets_data: List[Dict[str, Any]]) -> int:
        """Ingest asset data into the database."""
        count = 0
        for asset_data in assets_data:
            asset = Asset(
                user_id=self.user_id,
                asset_type=asset_data["asset_type"],
                value=asset_data["value"]
                # Add other fields as needed based on your Asset model
            )
            self.db.add(asset)
            count += 1
        return count

    def _ingest_liabilities(self, liabilities_data: List[Dict[str, Any]]) -> int:
        """Ingest liability data into the database."""
        count = 0
        for liability_data in liabilities_data:
            liability = Liability(
                user_id=self.user_id,
                liability_type=liability_data["liability_type"],
                value=liability_data["value"]
                # Add other fields as needed based on your Liability model
            )
            self.db.add(liability)
            count += 1
        return count

    def _ingest_accounts(self, accounts_data: List[Dict[str, Any]]) -> tuple[int, int]:
        """
        Ingest account and holdings data into the database.
        Returns (account_count, holdings_count).
        """
        account_count = 0
        holdings_count = 0

        for account_data in accounts_data:
            # Create account
            account = Account(
                user_id=self.user_id,
                account_type=account_data["account_type"],
                account_number=account_data["masked_account_number"],
                institution=account_data["institution_name"]
                # Add other fields as needed based on your Account model
            )
            self.db.add(account)
            self.db.flush()  # Get the account_id for holdings
            account_count += 1

            # Create holdings for this account
            if "holdings" in account_data:
                for holding_data in account_data["holdings"]:
                    holding = Holding(
                        account_id=account.account_id,
                        holding_type=holding_data["holding_type"],
                        quantity=holding_data["units"],
                        value=holding_data["current_value"]
                        # Add other fields as needed based on your Holding model
                    )
                    self.db.add(holding)
                    holdings_count += 1

        return account_count, holdings_count

    # TODO: Implement when MutualFund model is created
    # def _ingest_mutual_funds(self, mf_data: List[Dict[str, Any]]) -> int:
    #     """Ingest mutual fund data into the database."""
    #     count = 0
    #     for mf in mf_data:
    #         mutual_fund = MutualFund(
    #             user_id=self.user_id,
    #             scheme_name=mf["scheme_name"],
    #             amc=mf["amc"],
    #             current_value=mf["current_value"],
    #             invested_value=mf["invested_value"],
    #             units=mf["units"]
    #             # Add other fields
    #         )
    #         self.db.add(mutual_fund)
    #         count += 1
    #     return count


def ingest_mcp_data(user_id: int, parsed_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Convenience function to ingest MCP data for a user.

    Args:
        user_id: The user ID to associate the data with
        parsed_data: The parsed MCP response data

    Returns:
        Summary of records created
    """
    with MCPDatabaseIngest(user_id) as ingest_service:
        return ingest_service.ingest_all_data(parsed_data)

# --- MCP Processor ---


def process_mcp_response(mcp_response: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    try:
        parsed_data = parse_mcp_response(mcp_response)
        with MCPDatabaseIngest(user_id) as db_ingest:
            ingestion_summary = db_ingest.ingest_all_data(parsed_data)
        result = {
            "status": "success",
            "user_id": user_id,
            "parsed_data_summary": {
                "net_worth": parsed_data.get("net_worth", {}),
                "assets_count": len(parsed_data.get("assets", [])),
                "liabilities_count": len(parsed_data.get("liabilities", [])),
                "accounts_count": len(parsed_data.get("accounts", [])),
                "mutual_funds_count": len(parsed_data.get("mutual_funds", []))
            },
            "database_summary": ingestion_summary
        }
        logger.info(
            f"Successfully processed MCP response for user {user_id}: {result}")
        return result
    except (ValueError, KeyError, TypeError) as e:
        error_msg = f"Failed to process MCP response for user {user_id}: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "user_id": user_id, "error": error_msg}

# --- Transaction Parsers ---


# --- MCP Client Service ---

def load_sample_data(tool_name: str) -> Dict[str, Any]:
    """Load sample MCP response from JSON files for testing"""
    # Map tool names to sample file names
    file_map = {
        "fetch_net_worth": "fetch_net_worth.json",
        "fetch_bank_transactions": "fetch_bank_transactions.json",
        "fetch_stock_transactions": "fetch_stock_transactions.json",
        "fetch_mf_transactions": "fetch_mf_transactions.json",
        "fetch_epf_details": "fetch_epf_details.json",
        "fetch_credit_report": "fetch_credit_report.json",
    }

    # Get the tool name from params if tool_name is "tools/call"
    filename = file_map.get(tool_name, "fetch_net_worth.json")
    filepath = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), "data", filename)

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Wrap in MCP response format
        return {
            "jsonrpc": "2.0",
            "id": "1",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(data)
                    }
                ]
            }
        }
    except FileNotFoundError:
        logger.error(f"Sample data file not found: {filepath}")
        raise Exception(f"Sample data file not found: {filename}")
    except Exception as e:
        logger.error(f"Error loading sample data: {str(e)}")
        raise


def call_mcp_server(session_id: str, tool_name: str = "tools/call", tool_arguments: Dict[str, Any] = {"name": "fetch_net_worth", "arguments": {}}) -> Dict[str, Any]:
    """Call the MCP server with given parameters, or use sample data in development mode"""
    import requests

    # Development mode: use sample data
    if USE_SAMPLE_DATA:
        logger.info(
            f"🧪 DEV MODE: Using sample data instead of calling MCP server")
        tool_to_call = tool_arguments.get(
            "name", "fetch_net_worth") if tool_name == "tools/call" else tool_name
        return load_sample_data(tool_to_call)

    # Production mode: call actual MCP server
    try:
        mcp_url = f"{settings.FI_MCP_BASE_URL}/mcp/stream"
        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": tool_name,
            "params": tool_arguments
        }
        headers = {
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id
        }

        logger.info(
            f"Calling MCP server: {mcp_url} with session {session_id[:10]}...")
        response = requests.post(
            mcp_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        mcp_response = response.json()

        if "login_required" in str(mcp_response):
            return {
                "status": "login_required",
                "message": "Please complete login first",
                "response": mcp_response
            }

        return mcp_response
    except requests.RequestException as e:
        raise Exception(f"Failed to call MCP server: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to process MCP request: {str(e)}")


def process_mcp_data_service(session_id: str, user_id: int, tool_name: str = "tools/call", tool_arguments: Dict[str, Any] = {"name": "fetch_net_worth", "arguments": {}}) -> Dict[str, Any]:
    """Complete service to handle MCP data processing"""
    try:
        # Call MCP server
        mcp_response = call_mcp_server(session_id, tool_name, tool_arguments)

        # If login required, return early
        if mcp_response.get("status") == "login_required":
            return mcp_response

        # Process and ingest the response
        result = process_mcp_response(mcp_response, user_id)
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "user_id": user_id
        }


# --- Transaction Parsers ---

def parse_bank_transactions(json_data: dict) -> List[Transaction]:
    """Parse bank transactions from MCP JSON data."""
    transactions = []
    for bank in json_data.get('bankTransactions', []):
        bank_name = bank.get('bank')
        for txn in bank.get('txns', []):
            transaction = Transaction(
                amount=float(txn[0]),
                description=txn[1],
                date=datetime.strptime(txn[2], "%Y-%m-%d"),
                transaction_type=str(txn[3]),
                # txn[4] is transactionMode, txn[5] is currentBalance
            )
            transactions.append(transaction)
    return transactions


def parse_mf_transactions(json_data: dict) -> List[Transaction]:
    """Parse mutual fund transactions from MCP JSON data."""
    transactions = []
    for mf in json_data.get('mfTransactions', []):
        isin = mf.get('isin')
        scheme_name = mf.get('schemeName')
        for txn in mf.get('txns', []):
            transaction = Transaction(
                transaction_type=str(txn[0]),
                date=datetime.strptime(txn[1], "%Y-%m-%d"),
                amount=float(txn[4]),
                description=f"MF {scheme_name} ({isin})"
            )
            transactions.append(transaction)
    return transactions


def parse_stock_transactions(json_data: dict) -> List[Transaction]:
    """Parse stock transactions from MCP JSON data."""
    transactions = []
    for stock in json_data.get('stockTransactions', []):
        isin = stock.get('isin')
        for txn in stock.get('txns', []):
            transaction_type = str(txn[0])
            date = datetime.strptime(txn[1], "%Y-%m-%d")
            quantity = float(txn[2])
            nav_value = float(txn[3]) if len(txn) > 3 else None
            description = f"Stock {isin}"
            transaction = Transaction(
                transaction_type=transaction_type,
                date=date,
                amount=nav_value if nav_value is not None else quantity,
                description=description
            )
            transactions.append(transaction)
    return transactions


def parse_credit_report(json_data: dict) -> List[CreditReport]:
    """Parse credit report data from MCP JSON."""
    reports = []
    for report in json_data.get('creditReports', []):
        cr_data = report.get('creditReportData', {})
        score = int(cr_data.get('score', {}).get('bureauScore', 0))
        report_date = cr_data.get('creditProfileHeader', {}).get('reportDate')
        if report_date:
            report_date = datetime.strptime(report_date, "%Y%m%d")
        reports.append(CreditReport(
            score=score,
            report_date=report_date
        ))
    return reports


def parse_epf_details(json_data: dict) -> List[EPF]:
    """Parse EPF details from MCP JSON data."""
    epfs = []
    for uan in json_data.get('uanAccounts', []):
        raw = uan.get('rawDetails', {})
        for est in raw.get('est_details', []):
            pf_balance = est.get('pf_balance', {})
            net_balance = float(pf_balance.get('net_balance', 0))
            epf = EPF(
                balance=net_balance
            )
            epfs.append(epf)
    return epfs


def archive_raw_mcp_data(user_id: int, raw_json: dict) -> MCPRawData:
    """Archive raw MCP data for historical purposes."""
    return MCPRawData(user_id=user_id, received_at=datetime.utcnow(), data=raw_json)


def ingest_bank_transactions(json_data: dict, user_id: int):
    """
    Parse bank transactions from MCP JSON and save them to the database.
    """
    transactions = parse_bank_transactions(json_data)
    db = SessionLocal()
    try:
        for txn in transactions:
            txn.user_id = user_id
            db.add(txn)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
