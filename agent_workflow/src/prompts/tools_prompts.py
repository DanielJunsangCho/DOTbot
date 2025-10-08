"""Tool prompt templates for  integration."""

# Gmail tools prompt for insertion into agent system prompts
GMAIL_TOOLS_PROMPT = """
1. fetch_emails_tool(email_address, minutes_since) - Fetch recent emails from Gmail
2. send_email_tool(email_id, response_text, email_address, additional_recipients) - Send a reply to an email thread
3. check_calendar_tool(dates) - Check Google Calendar availability for specific dates
4. schedule_meeting_tool(attendees, title, start_time, end_time, organizer_email, timezone) - Schedule a meeting and send invites
5. triage_email(ignore, notify, respond) - Triage emails into one of three categories
6. Done - E-mail has been sent
"""

URL_TOOLS_PROMPT = """
1. url_handler(url) - Get the HTML text from a specific URL page
"""

CSV_TOOLS_PROMPT = """
1. write_to_csv(data, filename) - If data exists, it will be a list of dictionaries, where each dict is a row in the CSV. Write 
    each row to the CSV "filename".
"""