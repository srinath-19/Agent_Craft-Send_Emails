from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool
import sendgrid
import os
from sendgrid.helpers.mail import Mail, Email, To, Content
import asyncio
import json
import time
from pathlib import Path
from uuid import uuid4

load_dotenv(override=True)

DEBUG_LOG_PATH = Path(__file__).with_name("debug-41cf6c.log")
DEBUG_SESSION_ID = "41cf6c"

# region agent log
def debug_log(run_id: str, hypothesis_id: str, location: str, message: str, data: dict):
    payload = {
        "sessionId": DEBUG_SESSION_ID,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
        "id": f"log_{uuid4().hex}",
    }
    with DEBUG_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload) + "\n")
# endregion

instructions1 = "You are a sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write professional, serious cold emails."

instructions2 = "You are a humorous, engaging sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write witty, engaging cold emails that are likely to get a response."

instructions3 = "You are a busy sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write concise, to the point cold emails."

sales_agent1 = Agent(
        name="Professional Sales Agent",
        instructions=instructions1,
        model="gpt-4o-mini"
)

sales_agent2 = Agent(
        name="Engaging Sales Agent",
        instructions=instructions2,
        model="gpt-4o-mini"
)

sales_agent3 = Agent(
        name="Busy Sales Agent",
        instructions=instructions3,
        model="gpt-4o-mini"
)

@function_tool
def send_email(body: str):
    """ Send out an email with the given body to all sales prospects """
    run_id = uuid4().hex
    # region agent log
    debug_log(run_id, "H4", "agents_SDR.py:58", "send_email called", {"body_length": len(body)})
    # endregion
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("srinath.m1902@gmail.com")  # Change to your verified sender
    to_email = To("srinath.m1902@gmail.com")  # Change to your recipient
    content = Content("text/plain", body)
    mail = Mail(from_email, to_email, "Sales email", content).get()
    response = sg.client.mail.send.post(request_body=mail)
    # region agent log
    debug_log(run_id, "H4", "agents_SDR.py:65", "send_email completed", {"status_code": getattr(response, "status_code", None)})
    # endregion
    return {"status": "success"}

tool_description = "Write a cold sales email"

tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=tool_description)
tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description=tool_description)
tool3 = sales_agent3.as_tool(tool_name="sales_agent3", tool_description=tool_description)

tools = [tool1, tool2, tool3, send_email]

instructions = """
You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_agent tools.
 
Follow these steps carefully:
1. Generate Drafts: Use all three sales_agent tools to generate three different email drafts. Do not proceed until all three drafts are ready.
 
2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of which one is most effective.
 
3. Use the send_email tool to send the best email (and only the best email) to the user.
 
Crucial Rules:
- You must use the sales agent tools to generate the drafts — do not write them yourself.
- You must send ONE email using the send_email tool — never more than one.
"""


sales_manager = Agent(name="Sales Manager", instructions=instructions, tools=tools, model="gpt-4o-mini")

message = "Send a cold sales email addressed to 'Dear CEO' srinath"

async def main():
    run_id = uuid4().hex
    # region agent log
    debug_log(
        run_id,
        "H2",
        "agents_SDR.py:93",
        "main starting",
        {
            "has_openai_key": bool(os.environ.get("OPENAI_API_KEY")),
            "has_sendgrid_key": bool(os.environ.get("SENDGRID_API_KEY")),
            "message_length": len(message),
        },
    )
    # endregion
    with trace("Sales manager"):
        # region agent log
        debug_log(run_id, "H1", "agents_SDR.py:105", "before Runner.run", {"manager_tools": len(tools)})
        # endregion
        result = await Runner.run(sales_manager, message)
    # region agent log
    debug_log(
        run_id,
        "H3",
        "agents_SDR.py:109",
        "Runner.run completed",
        {
            "result_type": type(result).__name__,
            "has_final_output": hasattr(result, "final_output"),
        },
    )
    # endregion
    print(result.final_output if hasattr(result, "final_output") else result)


if __name__ == "__main__":
    asyncio.run(main())