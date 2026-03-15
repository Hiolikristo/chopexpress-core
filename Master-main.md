# ChopExpress Core

ChopExpress is a fairness-driven logistics platform designed to rebuild the economics of gig-delivery systems.

Most delivery platforms optimize for platform profit while pushing risk and cost onto drivers and restaurants.  
ChopExpress introduces a transparent system that calculates real economic delivery costs and distributes value fairly across the marketplace.

## Core Principles

• Fair driver compensation based on **economic miles (actual + return miles)**  
• Transparent order value breakdown  
• Built-in protection reserves for **tax, maintenance, and insurance**  
• Non-coercive dispatch logic (drivers choose orders without penalty pressure)  
• Zone-aware routing and deadhead compensation  
• Simulation-first platform testing before real-world deployment

## Core Engines

The platform is composed of several modular engines:

- `order_value_breakdown_engine.py`
- `fair_offer_engine.py`
- `dispatch_offer_engine.py`
- `driver_ms_engine.py`
- `insurance_support_engine.py`
- `fairness_engine.py`

## Simulation Framework

ChopExpress uses simulation testing before live deployment:

- market simulation
- merchant delay modeling
- zone heatmaps
- DoorDash comparison analytics
- driver behavior simulation

## Goal

Create a logistics platform where **drivers, merchants, and customers all understand how the economics work**, ensuring sustainable delivery markets rather than extractive gig systems.

---

This repository contains the **core economic and dispatch architecture** for the ChopExpress platform.
