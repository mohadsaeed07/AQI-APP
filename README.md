# Real-Time Air Quality (AQI) Tracker

This is an end-to-end DevOps project that tracks air quality. I took a Python web app, split it into two containerized microservices, deployed it onto a local Kubernetes cluster, and automated everything with a GitHub Actions CI/CD pipeline.

![CI/CD Status](https://github.com/mohadsaeed07/AQI-APP/actions/workflows/ci-cd.yaml/badge.svg)

---

## What Does the App Do?

You enter any city name (like Islamabad or Lahore) in the dashboard, and the app shows:
- Current Air Quality Index (AQI score from 0 to 500)
- Safety category (Good, Moderate, Poor, or Dangerous)
- Map location and pollutant breakdown (PM2.5, NO2, CO, etc.)
- A 5-day air quality forecast chart

---

## How It Works (Architecture)

Instead of running everything in one script, I split the project into two microservices:

1. Frontend (`frontend.py`):** A Streamlit dashboard that users interact with.
2. Backend (`main.py`):** A FastAPI server that fetches data from OpenWeatherMap, calculates AQI ratings, and serves data to the frontend.
