> ## Documentation Index
> Fetch the complete documentation index at: https://docs.base.org/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> For the current source of truth, read https://docs.base.org/llms.txt and connect the Base docs MCP server at https://docs.base.org/mcp.

# Dynamic Upgrades

> An Ethereum smart contract stores upgrade timestamps for Base nodes, allowing forks to activate at the scheduled time with no client restart.

> [!NOTE]
>
> This change runs in metrics-only mode on Mainnet while data is collected to validate that upgrades work smoothly.

## Motivation

Today, every hardfork activation requires a new node release with hard-coded timestamps. Operators must upgrade their binaries before each fork, and any missed release risks falling out of consensus. Decoupling upgrade timestamps from client releases reduces the number of releases operators need to run and shortens the coordination window for activating new forks.

## What Changed

The EL and CL each run an upgrade-signal poller that reads the onchain contract over L1 RPC, saves the schedule into the client's activation overrides, and applies them wherever the schedule is used. Forks activate at the scheduled time with no restart.

## Migration

This change is included in the Cobalt node release, so no action is required for node operators.
