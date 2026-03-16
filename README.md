# Google Cloud Hackathon 19

## Overview

A personalized learning platform that acts as a software development tutor. Users create profiles with their interests and educational background, then engage in a guided learning experience:

1. **Assessment**: Chat-based conversation to understand learning goals and current knowledge level
2. **Curriculum Generation**: AI-powered roadmap with structured learning steps tailored to the user's goals
3. **Content & Resources**: Curated links, overviews, and learning materials for each step
4. **Reinforcement**: Auto-generated quizzes to assess understanding and identify knowledge gaps
5. **Adaptive Learning**: Quiz results guide next steps—either revision of weak areas or progression to new material

## Spec

All feature development starts with a spec. Before writing code, a spec must exist and be approved.

- Specs live in [`specs/`](specs/)
- Each spec follows the template in [`specs/_template.md`](specs/_template.md)
- A spec must include: problem statement, proposed solution, acceptance criteria, and out-of-scope items


# Prerequisites

## Install dependencies
```
uv sync
```

## Running locally

```bash
uv run fastapi dev learning_platform/main.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.


## Run adk 
```
uv run adk web src     
```

# Deploy adk 

Change AGENT_FOLDER_NAME to the name of the folder containing your agent definition. 
```
cd src
```
```
export PROJECT_ID="qwiklabs-asl-03-35787841388f"
export LOCATION_ID="europe-west1"
export AGENT_FOLDER_NAME="example_learning_agent"

uv run adk deploy agent_engine \
  --project=$PROJECT_ID \
  --region=$LOCATION_ID \
  --display_name="My First Agent" \
  --otel_to_cloud \
  $AGENT_FOLDER_NAME
```
