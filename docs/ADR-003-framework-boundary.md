# ADR-003: Why the control plane does not depend on LangChain or another agent framework

Status: accepted

Date: 2026-10-04

## The decision

Keep routing, admission and tenant policy independent of an application orchestration
framework. The provider interface accepts a prompt and an output limit and returns a
completion with usage. A framework can call this platform; it does not own its policy.

## Why this boundary matters

I want to be able to replace an application workflow without changing the rules for
who can use a model, in which region, and against which budget. Those rules also have
to hold during fallback. If they live inside individual chains or agent workflows,
every application becomes another place to implement and audit infrastructure policy.

This is a scope decision, not a judgment that LangChain is unsuitable software.
The current project has no retrieval workflow, tool loop or conversation state that
would justify adopting an application framework. Introducing one would enlarge the
dependency surface without resolving the admission and ownership problems being tested.

## What this costs

A narrow adapter means writing and maintaining provider-specific translation ourselves.
It also means declining vendor features until their semantics fit the platform's
contract. The current prompt/completion interface does not cover streaming, tool calls
or multimodal payloads; adding those requires explicit limits and cancellation behavior,
not just forwarding arbitrary SDK arguments.

We give up ready-made application integrations and workflow abstractions. That is a
reasonable trade here because mockable policy and failure paths are the deliverable.

## When I would use a framework

For an application with retrieval, tools, conversation state or a multi-step agent
workflow, a framework may remove useful amounts of application plumbing. It could sit
above this API while admission and routing remain enforced here. For a single-purpose
prototype without shared platform requirements, a separate control-plane service might
itself be unnecessary.

Revisit the adapter contract when a concrete client needs richer inference semantics.
Keep application state out of the infrastructure policy modules even then.
