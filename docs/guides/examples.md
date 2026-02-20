# Example Workflows

Real-world examples of using the Automox MCP server with AI assistants.

## Device Health Summary

Get a quick snapshot of your device health:

```
Ask: "What can you tell me about the health of my devices in Automox?"
```

The MCP server returns a comprehensive summary including:
- Overall fleet health (total devices, compliance rate)
- Device status breakdown (ready, not ready, needs reboot, refreshing)
- Patching status (devices with pending patches, devices needing attention)
- Check-in recency analysis (last 24 hours, 7 days, 30 days, 30+ days)
- Key observations and suggested next steps

## Reboot a Device

Simple yet effective device management:

```
Ask: "Can you reboot the device 'Testing box' in Automox?"
```

The AI assistant will:
1. Search for devices matching the hostname
2. Present matching devices if there are multiple
3. Execute the reboot command once confirmed
4. Optionally verify the reboot was successful by checking device uptime

## Create and Update Policies

Create a patch policy to keep Firefox up to date:

```
Ask: "Can you create a patch policy that keeps Firefox up to date?
     Make sure to include 'henry' somewhere in the name of the patch policy
     and target the devices in the 'MCP testing' group."
```

The MCP server will:
1. Look up the server group by name
2. Create a patch policy with auto-patching enabled
3. Configure the schedule (weekdays at 2 AM by default)
4. Set up user notifications
5. Display the created policy configuration

Update policy schedules:

```
Ask: "Can you update the 'Auto-Patch Firefox - henry' policy to only run on weekdays?"
```

The AI will update the schedule from weekend to weekdays automatically.

## Check the Audit Log

Review user activity in your Automox console:

```
Ask: "What did Mark Hansen do in our Automox console last week?"
```

The MCP server will:
1. Query the audit trail for each day in the specified date range
2. Summarize all activities by day
3. Provide totals and highlight key actions (policy changes, device operations, user management)
4. Identify patterns like policy cleanup or reorganization activities

## Report Generation

Generate comprehensive reports (works best with Claude Desktop for PDF export):

```
Ask: "Generate a comprehensive report on our policy health and device status"
```

The AI can:
- Gather data from multiple endpoints
- Compile statistics and trends
- Format the information into a readable report
- Export to PDF format (when using Claude Desktop)

> **Note:** Report generation may take several minutes depending on organization size. Using a lighter model like Haiku can speed this up, though with potential trade-offs in detail.

## Search for Devices

Find devices by various criteria:

```
Ask: "Find all devices with 'prod' in the hostname"
Ask: "Which devices haven't checked in for over 30 days?"
Ask: "Show me all devices with critical patches pending"
```

## Webhook Management

Set up webhooks for event notifications:

```
Ask: "Create a webhook to notify Slack when a device fails a policy"
Ask: "List all configured webhooks"
Ask: "Test the 'Policy Alerts' webhook"
```

## Server Group Operations

Manage device groups:

```
Ask: "Create a new server group called 'Finance Department'"
Ask: "Move the device 'FINANCE-PC01' to the Finance Department group"
Ask: "List all server groups and their device counts"
```
