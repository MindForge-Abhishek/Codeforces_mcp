# Import FastMCP - this is the framework that turns our Python functions into MCP tools
# MCP (Model Context Protocol) is what lets Claude talk to external services
from mcp.server.fastmcp import FastMCP

# Import logging - this lets us print debug/info messages to the terminal
import logging

# Import json - we use this to convert Python dictionaries to JSON strings for responses
import json

# Import typing helpers - these let us say "this argument can be None" or "this returns a Dict"
from typing import Dict, Optional, Any

# Import urlencode - this converts a dictionary into a URL query string
# Example: {"handle": "_bakugo_", "count": 1} -> "handle=_bakugo_&count=1"
from urllib.parse import urlencode

# Import httpx - this is an async HTTP client (like requests but works with async/await)
import httpx

# Set up logging so we can see info and error messages in the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# This class handles all communication with the Codeforces public API
class CodeforcesAPI:
    # Base URL for all Codeforces API calls
    BASE_URL = "https://codeforces.com/api"

    def __init__(self):
        # Create an async HTTP client with a 30 second timeout
        # async means it won't block while waiting for the response
        self.client = httpx.AsyncClient(timeout=30.0)

    async def request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        # Build the full URL from base + endpoint
        # Example: "https://codeforces.com/api/user.status"
        url = f"{self.BASE_URL}/{endpoint}"

        if params:
            # Remove any params that are None (we don't want to send empty params)
            # Then convert the dict to a URL query string and attach it
            # Example: url becomes "https://codeforces.com/api/user.status?handle=_bakugo_&count=1"
            url += "?" + urlencode({k: v for k, v in params.items() if v is not None})

        try:
            # Make the GET request to Codeforces API
            response = await self.client.get(url)

            # If the response has an error status code (like 404, 500), raise an exception
            response.raise_for_status()

            # Convert the response body from JSON text to a Python dictionary
            data = response.json()

            # Codeforces API always returns {"status": "OK", "result": {...}} on success
            # If status is not OK, something went wrong on their end
            if data.get("status") != "OK":
                raise Exception(f"CF API Error: {data.get('comment', 'Unknown error')}")

            # Return just the "result" part - that's the actual data we need
            return data.get("result", {})

        except Exception as e:
            # Log the error to terminal so we can debug it
            logger.error(f"API request failed: {str(e)}")
            # Re-raise the exception so the calling tool can catch it and return an error message
            raise


# Create one shared instance of CodeforcesAPI that all tools will use
api = CodeforcesAPI()


def create_server():
    # Create the MCP server and give it a name
    # This name appears when Claude lists available tools
    server = FastMCP(name="codeforces-mcp-server")

    # ── TOOL: Get latest submissions for a user ──────────────────────────────
    # This is the main tool we use for logging - fetches your recent CF submissions
    @server.tool(
        name="get_user_submissions",
        description="Get recent submissions for a Codeforces user. Returns problem name, rating, tags, verdict, and contest ID."
    )
    async def get_user_submissions(
        handle: str,                        # Codeforces handle, e.g. "_bakugo_"
        from_index: Optional[int] = 1,      # Which submission to start from (1 = most recent)
        count: Optional[int] = 1            # How many submissions to return (default 1 = latest only)
    ) -> str:
        try:
            # Call the Codeforces user.status endpoint
            result = await api.request("user.status", {
                "handle": handle,
                "from": from_index,
                "count": count
            })
            # Convert the result to a nicely formatted JSON string and return it
            return json.dumps(result, indent=2)
        except Exception as e:
            # If anything goes wrong, return the error message as a string
            return f"Error fetching submissions: {str(e)}"

    # ── TOOL: Get user profile info ──────────────────────────────────────────
    # Returns rating, rank, name, etc. for a user
    @server.tool(
        name="get_user_info",
        description="Get profile information for a Codeforces user including current rating and rank."
    )
    async def get_user_info(handles: str) -> str:
        # handles can be one handle or multiple separated by semicolons
        # Example: "_bakugo_" or "_bakugo_;tourist"
        try:
            result = await api.request("user.info", {"handles": handles})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error fetching user info: {str(e)}"

    # ── TOOL: Get user rating history ────────────────────────────────────────
    # Returns rating changes after each contest the user participated in
    @server.tool(
        name="get_user_rating",
        description="Get the full rating history of a Codeforces user across all contests."
    )
    async def get_user_rating(handle: str) -> str:
        try:
            result = await api.request("user.rating", {"handle": handle})
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error fetching rating history: {str(e)}"

    # ── TOOL: Get contest standings ──────────────────────────────────────────
    # Useful for checking your rank after a contest
    @server.tool(
        name="get_contest_standings",
        description="Get standings for a specific Codeforces contest. Optionally filter by handle."
    )
    async def get_contest_standings(
        contest_id: int,                        # The contest ID number
        from_rank: Optional[int] = None,        # Starting rank to fetch from
        count: Optional[int] = None,            # How many rows to return
        handles: Optional[str] = None,          # Filter to specific handles (semicolon-separated)
        show_unofficial: bool = False           # Whether to include unofficial (practice) submissions
    ) -> str:
        try:
            result = await api.request("contest.standings", {
                "contestId": contest_id,
                "from": from_rank,
                "count": count,
                "handles": handles,
                "showUnofficial": "true" if show_unofficial else None
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error fetching contest standings: {str(e)}"

    # ── TOOL: Get contest submissions ────────────────────────────────────────
    # Returns all submissions made during a specific contest
    @server.tool(
        name="get_contest_status",
        description="Get all submissions made during a specific Codeforces contest."
    )
    async def get_contest_status(
        contest_id: int,
        handle: Optional[str] = None,           # Filter to one user's submissions
        from_index: Optional[int] = None,
        count: Optional[int] = None
    ) -> str:
        try:
            result = await api.request("contest.status", {
                "contestId": contest_id,
                "handle": handle,
                "from": from_index,
                "count": count
            })
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error fetching contest status: {str(e)}"

    # ── TOOL: Get list of all contests ───────────────────────────────────────
    @server.tool(
        name="get_contest_list",
        description="Get the list of all Codeforces contests (past and upcoming)."
    )
    async def get_contest_list(gym: bool = False) -> str:
        # gym=True returns gym contests, gym=False returns regular contests
        try:
            params = {"gym": "true" if gym else None}
            result = await api.request("contest.list", params)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error fetching contest list: {str(e)}"

    # Return the fully built server so main() can run it
    return server


def main():
    # Build the server with all tools registered
    server = create_server()

    logger.info("Starting Codeforces MCP server...")

    # Run the server using SSE (Server-Sent Events) transport
    # SSE is required for Claude to connect to this as a remote connector
    # stdio (the old transport) only works for local command-line tools
    # SSE means the server runs as an HTTP server that Claude can reach over the internet
    server.run(transport='sse', host ='0.0.0.0', port=8000)


# Standard Python entry point - only runs main() if this file is executed directly
# (not if it's imported by another file)
if __name__ == "__main__":
    main()