# StageTool API
![stagetool-architecture-diagram](https://github.com/Turku-BioImaging/stagetool-api/assets/11444749/b9daf7e0-fd13-4c40-889b-0a48767b9fe7)

REST API for StageTool, a convolutional deep neural network-based approach that facilitates the analysis of spermatogenesis in DAPI-stained mouse testis cross-sections.

StageTool API handles communication between StageTool Core and StageTool UI.

## Dev / Testing

Create a `.env` inside `./src` with the following keys

```
ENV=development // can be "production" or "staging"
DOCKER_IMAGE_NAME=ghcr.io/turku-bioimaging/stagetool-core
DOCKER_IMAGE_VERSION=0.1.0
```
